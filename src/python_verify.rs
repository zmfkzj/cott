use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use serde_json::{Value, json};

use crate::contract_test::execute_contract_tests;
use crate::hash::sha256_hex;
use crate::ir::CanonicalIr;
use crate::manifest::ProjectConfig;
use crate::project::ProjectPaths;
use crate::provenance::GenerationRecord;
use crate::python::artifact_plan::{PythonArtifactPlan, PythonCallableKind};
use crate::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxSpec, run};
use crate::version::{is_at_least, parse_version};

#[derive(Clone, Debug)]
pub struct VerificationEvidence {
    pub tools: Value,
    pub report: Value,
    pub dependencies: Value,
}

struct CandidateGenerationGuard {
    path: PathBuf,
    original: Vec<u8>,
    keep: bool,
}

impl Drop for CandidateGenerationGuard {
    fn drop(&mut self) {
        if !self.keep {
            let _ = fs::write(&self.path, &self.original);
        }
    }
}
fn supports_cpython_version(version: &str) -> bool {
    parse_version(version)
        .is_some_and(|(major, minor, patch)| (major, minor) == (3, 14) && patch >= 6)
}

fn basedpyright_version(output: &str) -> Option<&str> {
    let version_line = output.lines().next().unwrap_or_default();
    let version = version_line
        .strip_prefix("basedpyright ")
        .unwrap_or(version_line);
    is_at_least(version, (1, 39, 9)).then_some(version)
}

pub fn verify_python(
    config: &ProjectConfig,
    paths: &ProjectPaths,
    artifact_root: &Path,
    ir: &CanonicalIr,
    scope: Option<&BTreeSet<String>>,
) -> Result<VerificationEvidence, String> {
    let interpreter = executable(
        &paths.root,
        &config.python.interpreter,
        "Python interpreter",
    )?;
    let type_checker = executable(&paths.root, &config.python.type_checker, "BasedPyright")?;
    let scratch = scratch_directory()?;
    let result = verify_in_scratch(
        config,
        paths,
        artifact_root,
        ir,
        scope,
        &interpreter,
        &type_checker,
        &scratch,
    );
    let cleanup = fs::remove_dir_all(&scratch);
    match (result, cleanup) {
        (Err(error), _) => Err(error),
        (Ok(_), Err(error)) => Err(format!(
            "remove verification scratch {}: {error}",
            scratch.display()
        )),
        (Ok(evidence), Ok(())) => Ok(evidence),
    }
}

fn verify_in_scratch(
    config: &ProjectConfig,
    paths: &ProjectPaths,
    artifact_root: &Path,
    ir: &CanonicalIr,
    scope: Option<&BTreeSet<String>>,
    interpreter: &Path,
    type_checker: &Path,
    scratch: &Path,
) -> Result<VerificationEvidence, String> {
    let python_probe = process(
        interpreter,
        vec![
            "-c".to_owned(),
            "import json,platform,sys,sysconfig; print(json.dumps({'implementation':sys.implementation.name,'version':platform.python_version(),'cache_tag':sys.implementation.cache_tag,'os':sys.platform,'machine':platform.machine(),'platform':sysconfig.get_platform()},sort_keys=True,separators=(',',':')))".to_owned(),
        ],
        scratch,
        scratch,
        &[],
    )?;
    require_success("Python identity probe", &python_probe)?;
    let python: Value = serde_json::from_slice(&python_probe.stdout)
        .map_err(|error| format!("invalid Python identity probe output: {error}"))?;
    let python_version = python
        .get("version")
        .and_then(Value::as_str)
        .unwrap_or("unknown");
    if python.get("implementation").and_then(Value::as_str) != Some("cpython")
        || !supports_cpython_version(python_version)
    {
        return Err(format!(
            "Python target requires CPython >=3.14.6,<3.15, got {} {}",
            python
                .get("implementation")
                .and_then(Value::as_str)
                .unwrap_or("unknown"),
            python_version
        ));
    }

    let checker_probe = checker_process(
        type_checker,
        interpreter,
        vec!["--version".to_owned()],
        scratch,
        scratch,
        &[],
    )?;
    require_success("BasedPyright version probe", &checker_probe)?;
    let checker_output = String::from_utf8_lossy(&checker_probe.stdout);
    let Some(checker_version) = basedpyright_version(&checker_output) else {
        return Err(format!(
            "Python target requires BasedPyright >=1.39.9, got `{checker_output}`"
        ));
    };

    let managed_root = paths
        .generated_dir
        .parent()
        .ok_or("target.python.generated has no artifact root")?;
    let generated_root = artifact_root.join(
        paths
            .generated_dir
            .strip_prefix(managed_root)
            .map_err(|_| "generated Python path escaped artifact root")?,
    );
    let stubs_root = artifact_root.join(
        paths
            .stubs_dir
            .strip_prefix(managed_root)
            .map_err(|_| "stub path escaped artifact root")?,
    );
    let python_platform = match python.get("os").and_then(Value::as_str) {
        Some("darwin") => "Darwin",
        Some("win32") => "Windows",
        _ => "Linux",
    };
    let target_site_packages = external_program_environment(type_checker)
        .map(|environment| site_package_directories(&environment))
        .unwrap_or_default();
    let mut checker_extra_paths = vec![generated_root.clone()];
    checker_extra_paths.extend(target_site_packages.iter().cloned());
    let config_path = scratch.join("basedpyrightconfig.json");
    let checker_config = json!({
        "exclude": [generated_root.join("__pycache__")],
        "extraPaths": checker_extra_paths,
        "include": [generated_root.join("_cott_impl")],
        "pythonPlatform": python_platform,
        "pythonVersion": "3.14",
        "reportInvalidTypeVarUse": "none",
        "reportUnknownMemberType": "none",
        "reportPrivateUsage": "none",
        "reportUnusedFunction": "none",
        "stubPath": stubs_root,
        "typeCheckingMode": "strict",
    });
    fs::write(
        &config_path,
        serde_json::to_vec(&checker_config).map_err(|error| error.to_string())?,
    )
    .map_err(|error| {
        format!(
            "write BasedPyright config {}: {error}",
            config_path.display()
        )
    })?;
    let checker = checker_process(
        type_checker,
        interpreter,
        vec!["--project".to_owned(), config_path.display().to_string()],
        scratch,
        scratch,
        &[artifact_root.to_path_buf()],
    )?;
    require_success("BasedPyright", &checker)?;

    let generation = GenerationRecord::parse(
        &fs::read(artifact_root.join("generation.json"))
            .map_err(|error| format!("read staged generation record: {error}"))?,
    )
    .map_err(|error| format!("invalid staged generation record: {error}"))?;
    let plan = PythonArtifactPlan::from_ir(ir)
        .map_err(|error| format!("project canonical IR cannot be verified: {error}"))?;
    let callables = plan.callables();
    let callable_symbols = callables
        .iter()
        .map(|callable| (callable.cott_symbol.clone(), callable))
        .collect::<BTreeMap<_, _>>();
    let implementations = generation
        .current
        .implementations
        .as_array()
        .ok_or("generation implementations must be an array")?;
    let mut implementation_symbols = BTreeMap::new();
    for implementation in implementations {
        let symbol = implementation
            .get("cott_symbol")
            .and_then(Value::as_str)
            .ok_or("generation implementation is missing cott_symbol")?;
        if implementation_symbols
            .insert(symbol.to_owned(), implementation)
            .is_some()
        {
            return Err(format!(
                "generation record contains duplicate implementation `{symbol}`"
            ));
        }
    }
    for (symbol, implementation) in &implementation_symbols {
        let callable = callable_symbols.get(symbol).ok_or_else(|| {
            format!("generation record contains unknown implementation `{symbol}`")
        })?;
        let (kind, concrete, method) = match &callable.kind {
            PythonCallableKind::Function => ("function", Value::Null, Value::Null),
            PythonCallableKind::ImplMethod { concrete } => (
                "impl_method",
                Value::String(concrete.clone()),
                Value::String(callable.name.clone()),
            ),
        };
        if implementation.get("kind").and_then(Value::as_str) != Some(kind)
            || implementation.get("concrete") != Some(&concrete)
            || implementation.get("method") != Some(&method)
        {
            return Err(format!(
                "generation record has an invalid callable identity for `{symbol}`"
            ));
        }
    }
    let selected_callables = callables
        .iter()
        .filter(|callable| scope.is_none_or(|scope| scope.contains(&callable.cott_symbol)))
        .collect::<Vec<_>>();
    let signature_requests = selected_callables
        .iter()
        .map(|callable| {
            let implementation = implementation_symbols
                .get(&callable.cott_symbol)
                .ok_or_else(|| {
                    format!(
                        "generation record omitted a selected public implementation `{}`",
                        callable.cott_symbol
                    )
                })?;
            let python_symbol = implementation
                .get("python_symbol")
                .and_then(Value::as_str)
                .ok_or_else(|| {
                    format!(
                        "generation record implementation `{}` is missing python_symbol",
                        callable.cott_symbol
                    )
                })?;
            let (implementation_module, implementation_function) = python_symbol
                .split_once(':')
                .filter(|(module, function)| {
                    !module.is_empty() && !function.is_empty() && !function.contains(':')
                })
                .ok_or_else(|| {
                    format!(
                        "generation record implementation `{}` has an invalid python_symbol",
                        callable.cott_symbol
                    )
                })?;
            let runtime_origin = Path::new(
                implementation
                    .get("runtime_origin")
                    .and_then(Value::as_str)
                    .ok_or_else(|| {
                        format!(
                            "generation record implementation `{}` is missing runtime_origin",
                            callable.cott_symbol
                        )
                    })?,
            )
            .strip_prefix(
                Path::new(&config.python.generated)
                    .file_name()
                    .ok_or("target.python.generated has no directory name")?,
            )
            .map_err(|_| {
                format!(
                    "generation record implementation `{}` escaped generated Python root",
                    callable.cott_symbol
                )
            })?;
            let (facade, method) = match &callable.kind {
                PythonCallableKind::Function => (callable.name.as_str(), None),
                PythonCallableKind::ImplMethod { concrete } => {
                    let expected_path = Path::new("_cott_impl")
                        .join(callable.module.replace('.', "/"))
                        .join(concrete)
                        .join(format!("{}.py", callable.name));
                    let expected_source = Path::new(&config.python.source)
                        .join(&expected_path)
                        .to_string_lossy()
                        .replace('\\', "/");
                    let expected_runtime = Path::new(
                        Path::new(&config.python.generated)
                            .file_name()
                            .ok_or("target.python.generated has no directory name")?,
                    )
                    .join(&expected_path)
                    .to_string_lossy()
                    .replace('\\', "/");
                    let expected_module = format!(
                        "_cott_impl.{}.{}.{}",
                        callable.module, concrete, callable.name
                    );
                    let expected_function =
                        format!("_cott_impl_{}_{}", concrete, callable.name);
                    if runtime_origin != expected_path
                        || implementation
                            .get("source_origin")
                            .and_then(Value::as_str)
                            != Some(expected_source.as_str())
                        || implementation
                            .get("runtime_origin")
                            .and_then(Value::as_str)
                            != Some(expected_runtime.as_str())
                        || implementation_module != expected_module
                        || implementation_function != expected_function
                    {
                        return Err(format!(
                            "generation record has an invalid implementation method binding for `{}`",
                            callable.cott_symbol
                        ));
                    }
                    (concrete.as_str(), Some(callable.name.as_str()))
                }
            };
            Ok(json!({
                "content_hash": implementation.get("content_hash").ok_or_else(|| format!("generation record implementation `{}` is missing content_hash", callable.cott_symbol))?,
                "facade": facade,
                "implementation_function": implementation_function,
                "method": method,
                "module": callable.module,
                "project": config.project.name,
                "runtime_path": runtime_origin,
                "symbol": callable.cott_symbol,
            }))
        })
        .collect::<Result<Vec<_>, String>>()?;
    if signature_requests.len() != selected_callables.len() {
        return Err("generation record omitted a selected public implementation".to_owned());
    }
    let project_modules = ir
        .modules
        .iter()
        .map(|module| module.module.as_string())
        .flat_map(|module| [module.clone(), format!("{module}_types")])
        .collect::<BTreeSet<_>>();
    let dependencies = dependency_evidence(
        &config.project.name,
        paths,
        interpreter,
        &generated_root,
        artifact_root,
        scratch,
        &project_modules,
        &target_site_packages,
    )?;
    let runtime_probe = process(
        interpreter,
        vec![
            "-c".to_owned(),
            "import json,pathlib,platform,sys,sysconfig; value=(sys.implementation.name,platform.python_version(),sys.implementation.cache_tag,sys.platform,platform.machine(),sysconfig.get_platform(),str(pathlib.Path(sys.executable).resolve())); print(json.dumps(value,separators=(',',':')))"
                .to_owned(),
        ],
        scratch,
        scratch,
        &[],
    )?;
    require_success("runtime Python identity probe", &runtime_probe)?;
    let runtime_python: Vec<String> = serde_json::from_slice(&runtime_probe.stdout)
        .map_err(|error| format!("invalid runtime Python identity probe output: {error}"))?;
    if runtime_python.len() != 7 {
        return Err("runtime Python identity probe returned an invalid shape".to_owned());
    }
    let compiler =
        std::env::current_exe().map_err(|error| format!("resolve compiler executable: {error}"))?;
    let compiler = fs::canonicalize(&compiler)
        .map_err(|error| format!("canonicalize compiler executable: {error}"))?;
    let tools = json!({
        "basedpyright": tool_record(type_checker, checker_version)?,
        "compiler": tool_record(&compiler, env!("CARGO_PKG_VERSION"))?,
        "python": {
            "cache_tag": python["cache_tag"],
            "content_hash": hash_file(interpreter)?,
            "executable": interpreter,
            "implementation": "cpython",
            "machine": python["machine"],
            "os": python["os"],
            "platform": python["platform"],
            "version": python_version,
        },
        "runtime": {"abi": "1", "version": env!("CARGO_PKG_VERSION")},
    });
    let mut candidate_tools = tools.clone();
    candidate_tools["python"] = json!({
        "cache_tag": runtime_python[2],
        "content_hash": hash_file(Path::new(&runtime_python[6]))?,
        "executable": runtime_python[6],
        "implementation": runtime_python[0],
        "machine": runtime_python[4],
        "os": runtime_python[3],
        "platform": runtime_python[5],
        "version": runtime_python[1],
    });
    let mut candidate_guard =
        stage_candidate_generation(artifact_root, &candidate_tools, &dependencies)?;

    let mut signature_mounts = vec![artifact_root.to_path_buf()];
    signature_mounts.extend(target_site_packages.iter().cloned());
    let signature_probe = process(
        interpreter,
        vec![
            "-c".to_owned(),
            "import collections.abc,importlib,inspect,json,sys,typing\nfrom cott_runtime import _cott_load\n\ndef shape(signature):\n return [(name,parameter.kind.name,parameter.default is inspect.Parameter.empty,repr(parameter.default)) for name,parameter in signature.parameters.items()]\n\ndef hint(value):\n if isinstance(value,typing.TypeVar):\n  return ('TypeVar',hint(value.__bound__),tuple(hint(item) for item in value.__constraints__),value.__covariant__,value.__contravariant__)\n origin=typing.get_origin(value)\n if origin is not None:\n  return (origin,tuple(hint(item) for item in typing.get_args(value)))\n return value\n\ndef runtime_validation(value):\n if value is typing.Any or value is object:\n  return 'dynamic'\n origin=typing.get_origin(value)\n args=typing.get_args(value)\n if origin is typing.Annotated and any(type(item).__name__=='CottExternal' for item in args[1:]):\n  return 'static-only'\n if origin in (collections.abc.Iterator,collections.abc.Generator):\n  return 'outer-only'\n nested={runtime_validation(item) for item in args}\n return next((item for item in ('static-only','dynamic','outer-only') if item in nested),'deep')\n\nout={}\nfor item in json.loads(sys.argv[1]):\n facade=getattr(importlib.import_module(item['module']),item['facade'])\n if item['method'] is not None:\n  facade=getattr(facade,item['method'])\n implementation=_cott_load(item['runtime_path'],item['content_hash'].removeprefix('sha256:'),item['implementation_function'],expected_project_name=item['project'])\n expected_signature=inspect.signature(facade)\n actual_signature=inspect.signature(implementation)\n expected_hints={name:hint(value) for name,value in typing.get_type_hints(facade,include_extras=True).items()}\n actual_hints={name:hint(value) for name,value in typing.get_type_hints(implementation,include_extras=True).items()}\n if shape(actual_signature) != shape(expected_signature) or actual_hints != expected_hints:\n  raise TypeError(f\"{item['symbol']} implementation signature {actual_signature} {actual_hints!r} != {expected_signature} {expected_hints!r}\")\n out[item['symbol']]={'implementation_module':implementation.__module__,'implementation_name':implementation.__name__,'module':facade.__module__,'name':facade.__qualname__,'runtime_validation':{name:runtime_validation(value) for name,value in typing.get_type_hints(facade,include_extras=True).items()},'signature':str(expected_signature)}\nprint(json.dumps(out,sort_keys=True,separators=(',',':')))".to_owned(),
            serde_json::to_string(&signature_requests).map_err(|error| error.to_string())?,
        ],
        &generated_root,
        scratch,
        &signature_mounts,
    )?;
    require_success("runtime signature probe", &signature_probe)?;
    let runtime_signature_output = last_nonempty_line(&signature_probe.stdout)
        .ok_or("runtime signature probe produced no JSON")?;
    let runtime_signatures: Value = serde_json::from_slice(runtime_signature_output)
        .map_err(|error| format!("invalid runtime signature probe output: {error}"))?;
    if runtime_signatures
        .as_object()
        .map_or(0, serde_json::Map::len)
        != signature_requests.len()
    {
        return Err("runtime signature probe omitted a public function".to_owned());
    }

    let contract_report = execute_contract_tests(
        interpreter,
        &generated_root,
        &target_site_packages,
        ir,
        config.python.runtime_validation.clone(),
        scope,
    )?;
    candidate_guard.keep = true;
    let report = json!({
        "contract_tests": contract_report,
        "runtime_capability": {
            "grade": "runtime check",
            "sandbox": "bubblewrap",
            "status": "passed",
        },
        "static": {
            "checker": format!("BasedPyright {checker_version}"),
            "runtime_signatures": runtime_signatures,
            "grade": "static proof",
            "status": "passed",
        },
    });
    Ok(VerificationEvidence {
        tools,
        report,
        dependencies,
    })
}

fn stage_candidate_generation(
    artifact_root: &Path,
    tools: &Value,
    dependencies: &Value,
) -> Result<CandidateGenerationGuard, String> {
    let path = artifact_root.join("generation.json");
    let original =
        fs::read(&path).map_err(|error| format!("read staged generation record: {error}"))?;
    let mut record = GenerationRecord::parse(&original)
        .map_err(|error| format!("invalid staged generation record: {error}"))?;
    record.current.tools = tools.clone();
    record.current.dependencies = dependencies.clone();
    record.current.verified = true;
    record.current.verification = Value::Null;
    record
        .current
        .compute_generation_id()
        .map_err(|error| format!("compute candidate generation identity: {error}"))?;
    let bytes = record
        .canonical_bytes()
        .map_err(|error| format!("serialize candidate generation record: {error}"))?;
    fs::write(&path, bytes)
        .map_err(|error| format!("write candidate generation record: {error}"))?;
    Ok(CandidateGenerationGuard {
        path,
        original,
        keep: false,
    })
}

fn executable(root: &Path, configured: &str, label: &str) -> Result<PathBuf, String> {
    let configured = Path::new(configured);
    let path = if configured.is_absolute() {
        configured.to_path_buf()
    } else {
        root.join(configured)
    };
    let path = fs::canonicalize(&path)
        .map_err(|error| format!("resolve {label} {}: {error}", path.display()))?;
    let metadata = fs::metadata(&path)
        .map_err(|error| format!("inspect {label} {}: {error}", path.display()))?;
    if !metadata.is_file() || metadata.nlink() != 1 {
        return Err(format!(
            "{label} must be a regular single-link file: {}",
            path.display()
        ));
    }
    Ok(path)
}

fn tool_record(executable: &Path, version: &str) -> Result<Value, String> {
    Ok(json!({
        "content_hash": hash_file(executable)?,
        "executable": executable,
        "version": version,
    }))
}

fn hash_file(path: &Path) -> Result<String, String> {
    fs::read(path)
        .map(|bytes| format!("sha256:{}", sha256_hex(&bytes)))
        .map_err(|error| format!("hash executable {}: {error}", path.display()))
}

fn last_nonempty_line(output: &[u8]) -> Option<&[u8]> {
    output
        .rsplit(|byte| *byte == b'\n')
        .find(|line| !line.is_empty())
}

fn require_success(
    label: &str,
    completed: &crate::sandbox::CompletedProcess,
) -> Result<(), String> {
    if completed.status == Some(0) && completed.stderr.is_empty() {
        Ok(())
    } else {
        let stdout = String::from_utf8_lossy(&completed.stdout);
        let stderr = String::from_utf8_lossy(&completed.stderr);
        Err(format!(
            "{label} failed with status {:?}: {}{}{}",
            completed.status,
            stdout.trim(),
            if stdout.is_empty() || stderr.is_empty() {
                ""
            } else {
                "\n"
            },
            stderr.trim()
        ))
    }
}

fn checker_process(
    type_checker: &Path,
    interpreter: &Path,
    arguments: Vec<String>,
    cwd: &Path,
    scratch: &Path,
    read_only: &[PathBuf],
) -> Result<crate::sandbox::CompletedProcess, String> {
    let mut mounts = read_only.to_vec();
    for program in [interpreter, type_checker] {
        if let Some(environment) = external_program_environment(program) {
            mounts.push(environment);
        }
    }
    let python_launcher = fs::read(type_checker).ok().is_some_and(|source| {
        let line = source
            .split(|byte| *byte == b'\n')
            .next()
            .unwrap_or_default();
        line.starts_with(b"#!") && line.windows(6).any(|part| part == b"python")
    });
    if python_launcher {
        let environment = type_checker
            .parent()
            .and_then(Path::parent)
            .ok_or_else(|| {
                format!(
                    "type checker has no environment: {}",
                    type_checker.display()
                )
            })?;
        let mut checker_arguments = vec![
            "-c".to_owned(),
            "import pathlib,runpy,sys; checker=sys.argv[1]; environment=pathlib.Path(sys.argv[2]); sys.path[:0]=[str(path) for path in (environment/'lib').glob('python*/site-packages')]; sys.argv=[checker,*sys.argv[3:]]; runpy.run_path(checker,run_name='__main__')".to_owned(),
            type_checker.display().to_string(),
            environment.display().to_string(),
        ];
        checker_arguments.extend(arguments);
        process(interpreter, checker_arguments, cwd, scratch, &mounts)
    } else {
        process(type_checker, arguments, cwd, scratch, &mounts)
    }
}

fn external_program_environment(program: &Path) -> Option<PathBuf> {
    (!program.starts_with("/usr") && !program.starts_with("/bin") && !program.starts_with("/lib"))
        .then(|| program.parent()?.parent().map(Path::to_path_buf))
        .flatten()
}
fn site_package_directories(environment: &Path) -> Vec<PathBuf> {
    let Ok(entries) = fs::read_dir(environment.join("lib")) else {
        return Vec::new();
    };
    let mut paths = entries
        .filter_map(Result::ok)
        .map(|entry| entry.path().join("site-packages"))
        .filter(|path| path.is_dir())
        .collect::<Vec<_>>();
    paths.sort();
    paths
}

fn process(
    program: &Path,
    arguments: Vec<String>,
    cwd: &Path,
    scratch: &Path,
    read_only: &[PathBuf],
) -> Result<crate::sandbox::CompletedProcess, String> {
    let mut mounts = read_only.to_vec();
    if let Some(environment) = external_program_environment(program) {
        mounts.push(environment);
    }
    let mut environment = BTreeMap::from([
        ("HOME".to_owned(), scratch.display().to_string()),
        ("NO_COLOR".to_owned(), "1".to_owned()),
        ("PATH".to_owned(), "/usr/bin:/bin".to_owned()),
        ("PYTHONDONTWRITEBYTECODE".to_owned(), "1".to_owned()),
        ("PYTHONHASHSEED".to_owned(), "0".to_owned()),
        ("TMPDIR".to_owned(), scratch.display().to_string()),
    ]);
    let site_packages = read_only
        .iter()
        .filter(|path| path.file_name().is_some_and(|name| name == "site-packages"))
        .collect::<Vec<_>>();
    if !site_packages.is_empty() {
        let python_path = std::env::join_paths(site_packages)
            .map_err(|error| format!("construct sandbox PYTHONPATH: {error}"))?;
        environment.insert(
            "PYTHONPATH".to_owned(),
            python_path.to_string_lossy().into_owned(),
        );
    }
    run(&SandboxSpec {
        program: program.to_path_buf(),
        arguments,
        cwd: cwd.to_path_buf(),
        environment,
        stdin: Vec::new(),
        binds: BindMounts {
            read_only: mounts,
            writable: vec![scratch.to_path_buf()],
        },
        network: NetworkAccess::Disabled,
        limits: ResourceLimits {
            cpu_time: Duration::from_secs(120),
            address_space_bytes: 16 * 1024 * 1024 * 1024,
            process_count: 64,
            open_files: 256,
            file_size_bytes: 128 * 1024 * 1024,
            wall_time: Duration::from_secs(120),
            stream_limit_bytes: 16 * 1024 * 1024,
            writable_bytes: 128 * 1024 * 1024,
        },
    })
    .map_err(|error| error.to_string())
}

fn scratch_directory() -> Result<PathBuf, String> {
    static NEXT: AtomicU64 = AtomicU64::new(0);
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| error.to_string())?
        .as_nanos();
    let path = std::env::temp_dir().join(format!(
        "cott-python-verify-{}-{nonce}-{}",
        std::process::id(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&path)
        .map_err(|error| format!("create verification scratch {}: {error}", path.display()))?;
    Ok(path)
}

fn dependency_evidence(
    project_name: &str,
    paths: &ProjectPaths,
    interpreter: &Path,
    generated_root: &Path,
    artifact_root: &Path,
    scratch: &Path,
    project_modules: &BTreeSet<String>,
    site_packages: &[PathBuf],
) -> Result<Value, String> {
    let metadata_path = paths.python_source_dir.join("pyproject.toml");
    let metadata: toml::Value =
        toml::from_str(&fs::read_to_string(&metadata_path).map_err(|error| {
            format!("read target metadata {}: {error}", metadata_path.display())
        })?)
        .map_err(|error| {
            format!(
                "invalid target metadata {}: {error}",
                metadata_path.display()
            )
        })?;
    let declared_dependencies = metadata
        .get("project")
        .and_then(|project| project.get("dependencies"))
        .and_then(toml::Value::as_array)
        .ok_or_else(|| {
            format!(
                "target metadata {} has no project.dependencies array",
                metadata_path.display()
            )
        })?
        .iter()
        .map(|requirement| {
            requirement
                .as_str()
                .and_then(requirement_name)
                .ok_or_else(|| {
                    "target project contains an unsupported dependency requirement".to_owned()
                })
        })
        .collect::<Result<BTreeSet<_>, _>>()?;
    let (mut dependencies, lock_index) = if let Some(path) = &paths.lockfile {
        let bytes =
            fs::read(path).map_err(|error| format!("read lockfile {}: {error}", path.display()))?;
        let lock: toml::Value = toml::from_str(
            std::str::from_utf8(&bytes)
                .map_err(|_| format!("lockfile {} is not UTF-8", path.display()))?,
        )
        .map_err(|error| format!("invalid uv lockfile {}: {error}", path.display()))?;
        let lock_hash = format!("sha256:{}", sha256_hex(&bytes));
        let packages = lock
            .get("package")
            .and_then(toml::Value::as_array)
            .ok_or_else(|| format!("lockfile {} has no package array", path.display()))?;
        let normalize_name = |name: &str| name.to_ascii_lowercase().replace('_', "-");
        let dependency_names = |package: &toml::Value| {
            package
                .get("dependencies")
                .and_then(toml::Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(|dependency| {
                    dependency
                        .get("name")
                        .and_then(toml::Value::as_str)
                        .map(&normalize_name)
                })
                .collect::<Vec<_>>()
        };
        let project_package = packages.iter().find(|package| {
            package
                .get("name")
                .and_then(toml::Value::as_str)
                .is_some_and(|name| normalize_name(name) == project_name)
        });
        if project_package.is_none() && !packages.is_empty() {
            return Err(format!(
                "lockfile {} omits project package `{project_name}`",
                path.display()
            ));
        }
        let locked_direct_dependencies = project_package
            .map(&dependency_names)
            .unwrap_or_default()
            .into_iter()
            .collect::<BTreeSet<_>>();
        if locked_direct_dependencies != declared_dependencies {
            return Err(format!(
                "target project dependencies do not match frozen root metadata in {}",
                path.display()
            ));
        }
        let mut pending = project_package.map(&dependency_names).unwrap_or_default();
        let mut selected = BTreeSet::new();
        while let Some(name) = pending.pop() {
            if !selected.insert(name.clone()) {
                continue;
            }
            for package in packages.iter().filter(|package| {
                package
                    .get("name")
                    .and_then(toml::Value::as_str)
                    .is_some_and(|candidate| normalize_name(candidate) == name)
            }) {
                pending.extend(dependency_names(package));
            }
        }
        let project_name = normalize_name(project_name);
        let mut values = Vec::new();
        for package in packages {
            let name = package
                .get("name")
                .and_then(toml::Value::as_str)
                .ok_or("locked package has no name")?
                .to_ascii_lowercase()
                .replace('_', "-");
            if name == project_name {
                continue;
            }
            if !selected.contains(&name) {
                continue;
            }
            let version = package
                .get("version")
                .and_then(toml::Value::as_str)
                .ok_or_else(|| format!("locked package `{name}` has no version"))?
                .to_owned();
            if package
                .get("source")
                .and_then(toml::Value::as_table)
                .and_then(|source| source.get("registry"))
                .and_then(toml::Value::as_str)
                .is_none()
            {
                return Err(format!(
                    "locked package `{name}` is not a non-editable registry dependency"
                ));
            }
            let mut artifacts = package
                .get("wheels")
                .and_then(toml::Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(|wheel| wheel.get("hash").and_then(toml::Value::as_str))
                .map(str::to_owned)
                .collect::<Vec<_>>();
            if let Some(hash) = package
                .get("sdist")
                .and_then(|value| value.get("hash"))
                .and_then(toml::Value::as_str)
            {
                artifacts.push(hash.to_owned());
            }
            artifacts.sort();
            artifacts.dedup();
            if artifacts.is_empty()
                || artifacts.iter().any(|hash| {
                    let Some(hash) = hash.strip_prefix("sha256:") else {
                        return true;
                    };
                    hash.len() != 64 || !hash.bytes().all(|byte| byte.is_ascii_hexdigit())
                })
            {
                return Err(format!(
                    "locked package `{name}` lacks complete SHA-256 archive provenance"
                ));
            }
            values.push(json!({
                "artifacts": artifacts,
                "lock_hash": lock_hash,
                "name": name,
                "version": version,
            }));
        }
        values.sort_by(|left, right| left["name"].as_str().cmp(&right["name"].as_str()));
        let index = values
            .iter()
            .filter_map(|value| {
                Some((
                    value.get("name")?.as_str()?.to_owned(),
                    value.get("version")?.as_str()?.to_owned(),
                ))
            })
            .collect::<BTreeMap<_, _>>();
        (values, index)
    } else {
        (Vec::new(), BTreeMap::new())
    };
    let mut dependency_mounts = vec![artifact_root.to_path_buf()];
    dependency_mounts.extend(site_packages.iter().cloned());
    let probe = process(
        interpreter,
        vec![
            "-c".to_owned(),
            r#"import ast,hashlib,importlib.metadata as md,json,pathlib,sys
root=pathlib.Path(sys.argv[1])
locked=json.loads(sys.argv[2])
project_modules=set(json.loads(sys.argv[3]))
imports=set()
for path in sorted((root/"_cott_impl").rglob("*.py")):
 tree=ast.parse(path.read_bytes(),filename=str(path))
 for node in ast.walk(tree):
  if isinstance(node,ast.Import):
   imports.update(alias.name for alias in node.names)
  elif isinstance(node,ast.ImportFrom) and node.level==0 and node.module:
   imports.add(node.module)
imports={name.split(".",1)[0] for name in imports if name not in project_modules}
imports-=set(sys.stdlib_module_names)|{"cott_runtime","_cott_impl"}
owners=md.packages_distributions()
imported_by={}
for package in sorted(imports):
 distributions=owners.get(package,[])
 if len(distributions)!=1:
  raise RuntimeError(f"external import {package!r} belongs to {len(distributions)} installed distributions")
 name=distributions[0].lower().replace("_","-")
 if name not in locked:
  raise RuntimeError(f"external import {package!r} resolves to unlocked distribution {name!r}")
 imported_by.setdefault(name,[]).append(package)
result={}
for locked_name,locked_version in sorted(locked.items()):
 if locked_name not in imported_by:
  continue
 distribution=md.distribution(locked_name)
 name=distribution.metadata["Name"].lower().replace("_","-")
 version=distribution.version
 if name!=locked_name or version!=locked_version:
  raise RuntimeError(f"locked distribution {locked_name}=={locked_version} resolved to {name}=={version}")
 metadata=distribution.read_text("METADATA")
 if metadata is None:
  raise RuntimeError(f"installed distribution {name!r} has no METADATA")
 files=[]
 roots=sorted(set(imported_by.get(name,[])))
 for relative in distribution.files or ():
  rel=relative.as_posix()
  if not any(rel==root+".py" or rel==root+"/__init__.py" or ("/" not in rel and rel.startswith(root+".") and (rel.endswith(".so") or rel.endswith(".pyd"))) for root in roots):
   continue
  path=pathlib.Path(distribution.locate_file(relative))
  if path.is_symlink():
   raise RuntimeError(f"installed distribution {name!r} contains symlink {path}")
  if path.is_file():
   files.append({"content_hash":"sha256:"+hashlib.sha256(path.read_bytes()).hexdigest(),"path":rel})
 if not files:
  raise RuntimeError(f"installed distribution {name!r} has no regular files")
 result[name]={"imports":sorted(imported_by.get(name,[])),"metadata_hash":"sha256:"+hashlib.sha256(metadata.encode()).hexdigest(),"origins":sorted(files,key=lambda item:(item["path"],item["content_hash"])),"version":version}
print(json.dumps(result,sort_keys=True,separators=(",",":")))"#
                .to_owned(),
            generated_root.display().to_string(),
            serde_json::to_string(&lock_index).map_err(|error| error.to_string())?,
            serde_json::to_string(project_modules).map_err(|error| error.to_string())?,
        ],
        generated_root,
        scratch,
        &dependency_mounts,
    )?;
    require_success("dependency provenance probe", &probe)?;
    let installed: BTreeMap<String, Value> = serde_json::from_slice(&probe.stdout)
        .map_err(|error| format!("invalid dependency provenance output: {error}"))?;
    dependencies.retain(|dependency| {
        dependency
            .get("name")
            .and_then(Value::as_str)
            .is_some_and(|name| installed.contains_key(name))
    });
    for dependency in &mut dependencies {
        let name = dependency
            .get("name")
            .and_then(Value::as_str)
            .ok_or("dependency provenance omitted a name")?;
        let evidence = installed
            .get(name)
            .ok_or_else(|| format!("installed dependency provenance omitted `{name}`"))?;
        dependency
            .as_object_mut()
            .expect("dependency is an object")
            .insert("installed".to_owned(), evidence.clone());
    }
    Ok(Value::Array(dependencies))
}

fn requirement_name(requirement: &str) -> Option<String> {
    let requirement = requirement.trim();
    let end = requirement
        .char_indices()
        .find_map(|(index, character)| {
            (!character.is_ascii_alphanumeric() && !matches!(character, '-' | '_' | '.'))
                .then_some(index)
        })
        .unwrap_or(requirement.len());
    let name = requirement[..end]
        .to_ascii_lowercase()
        .replace(['_', '.'], "-");
    (!name.is_empty() && !requirement.contains('@')).then_some(name)
}

#[cfg(test)]
mod tests {
    use std::os::unix::fs::{PermissionsExt, symlink};

    use super::*;

    #[test]
    fn checker_process_mounts_external_shebang_interpreter() {
        let root = scratch_directory().expect("fixture root");
        let outcome = (|| {
            let interpreter = fs::canonicalize("/usr/bin/python3")?;
            let checker = root.join("project/.venv/bin/basedpyright");
            let scratch = root.join("scratch");
            fs::create_dir_all(checker.parent().expect("checker parent"))?;
            fs::create_dir(&scratch)?;
            symlink(&interpreter, root.join("project/.venv/bin/python"))?;
            fs::write(
                &checker,
                format!(
                    "#!{}\nprint('basedpyright 1.39.9')\n",
                    root.join("project/.venv/bin/python").display()
                ),
            )?;
            fs::set_permissions(&checker, fs::Permissions::from_mode(0o755))?;
            let completed = checker_process(
                &checker,
                &interpreter,
                vec!["--version".to_owned()],
                &scratch,
                &scratch,
                &[],
            )
            .map_err(std::io::Error::other)?;
            Ok::<_, std::io::Error>(completed)
        })();
        let cleanup = fs::remove_dir_all(&root);
        let completed = outcome.expect("checker process");
        cleanup.expect("remove fixture root");
        assert_eq!(
            completed.status,
            Some(0),
            "{}",
            String::from_utf8_lossy(&completed.stderr)
        );
        assert_eq!(completed.stdout, b"basedpyright 1.39.9\n");
        assert!(completed.stderr.is_empty());
    }
    #[test]
    fn discovers_target_site_packages_deterministically() {
        let root = scratch_directory().expect("fixture root");
        let second = root.join("lib/python3.15/site-packages");
        let first = root.join("lib/python3.14/site-packages");
        fs::create_dir_all(&second).expect("second site-packages");
        fs::create_dir_all(&first).expect("first site-packages");
        assert_eq!(
            site_package_directories(&root),
            vec![first.clone(), second.clone()]
        );
        fs::remove_dir_all(root).expect("remove fixture root");
    }
    #[test]
    fn process_exposes_mounted_site_packages_to_python() {
        let root = scratch_directory().expect("fixture root");
        let outcome = (|| {
            let scratch = root.join("scratch");
            let site_packages = root.join("lib/python3.14/site-packages");
            fs::create_dir(&scratch)?;
            fs::create_dir_all(&site_packages)?;
            fs::write(
                site_packages.join("dependency_fixture.py"),
                "VALUE = 'available'\n",
            )?;
            process(
                &fs::canonicalize("/usr/bin/python3")?,
                vec![
                    "-c".to_owned(),
                    "import dependency_fixture; print(dependency_fixture.VALUE)".to_owned(),
                ],
                &scratch,
                &scratch,
                &[site_packages],
            )
            .map_err(std::io::Error::other)
        })();
        let cleanup = fs::remove_dir_all(&root);
        let completed = outcome.expect("Python process");
        cleanup.expect("remove fixture root");
        assert_eq!(
            completed.status,
            Some(0),
            "{}",
            String::from_utf8_lossy(&completed.stderr)
        );
        assert_eq!(completed.stdout, b"available\n");
    }

    #[test]
    fn selects_probe_json_after_dependency_logs() {
        assert_eq!(
            last_nonempty_line(b"dependency warning\n{\"ok\":true}\n"),
            Some(b"{\"ok\":true}".as_slice())
        );
    }

    #[test]
    fn accepts_supported_python_and_basedpyright_versions() {
        assert!(supports_cpython_version("3.14.6"));
        assert!(supports_cpython_version("3.14.7"));
        assert!(!supports_cpython_version("3.14.5"));
        assert!(!supports_cpython_version("3.15.0"));
        assert_eq!(basedpyright_version("basedpyright 1.40.0"), Some("1.40.0"));
        assert_eq!(basedpyright_version("1.39.9"), Some("1.39.9"));
        assert_eq!(basedpyright_version("basedpyright 1.39.8"), None);
    }
}
