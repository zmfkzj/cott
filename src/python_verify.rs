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
use crate::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxSpec, run};

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
    if python.get("implementation").and_then(Value::as_str) != Some("cpython")
        || python.get("version").and_then(Value::as_str) != Some("3.14.6")
    {
        return Err(format!(
            "Python target requires CPython 3.14.6, got {} {}",
            python
                .get("implementation")
                .and_then(Value::as_str)
                .unwrap_or("unknown"),
            python
                .get("version")
                .and_then(Value::as_str)
                .unwrap_or("unknown")
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
    let checker_version = String::from_utf8_lossy(&checker_probe.stdout)
        .trim()
        .to_owned();
    let checker_version_line = checker_version.lines().next().unwrap_or_default();
    if checker_version_line != "basedpyright 1.39.9" && checker_version_line != "1.39.9" {
        return Err(format!(
            "Python target requires BasedPyright 1.39.9, got `{checker_version}`"
        ));
    }

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
    let config_path = scratch.join("basedpyrightconfig.json");
    let checker_config = json!({
        "exclude": [generated_root.join("__pycache__")],
        "extraPaths": [generated_root],
        "include": [generated_root.join("_cott_impl")],
        "pythonPlatform": python_platform,
        "pythonVersion": "3.14",
        "reportInvalidTypeVarUse": "none",
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
    let implementation_symbols = generation
        .current
        .implementations
        .as_array()
        .ok_or("generation implementations must be an array")?
        .iter()
        .filter_map(|implementation| {
            Some((
                implementation.get("cott_symbol")?.as_str()?.to_owned(),
                implementation.clone(),
            ))
        })
        .collect::<BTreeMap<_, _>>();

    let signature_requests = ir
        .modules
        .iter()
        .flat_map(|module| {
            let module_name = module.module.as_string();
            let implementation_symbols = &implementation_symbols;
            serde_json::from_slice::<Value>(&module.bytes)
                .ok()
                .and_then(|value| value.get("declarations").and_then(Value::as_array).cloned())
                .unwrap_or_default()
                .into_iter()
                .filter(|declaration| {
                    declaration.get("kind").and_then(Value::as_str) == Some("function")
                        && declaration.get("public").and_then(Value::as_bool) == Some(true)
                })
                .filter_map(move |declaration| {
                    let symbol = declaration.get("name")?.as_str()?;
                    let name = symbol.rsplit('.').next()?;
                    let implementation = implementation_symbols.get(symbol)?;
                    let python_symbol = implementation.get("python_symbol")?.as_str()?;
                    let (_, implementation_function) = python_symbol.split_once(':')?;
                    let runtime_origin = Path::new(implementation.get("runtime_origin")?.as_str()?)
                        .strip_prefix(Path::new(&config.python.generated).file_name()?)
                        .ok()?;
                    Some(json!({
                        "content_hash": implementation.get("content_hash")?,
                        "function": name,
                        "implementation_function": implementation_function,
                        "module": module_name,
                        "project": config.project.name,
                        "runtime_path": runtime_origin,
                        "symbol": symbol,
                    }))
                })
        })
        .filter(|request| {
            scope.is_none_or(|scope| {
                request
                    .get("symbol")
                    .and_then(Value::as_str)
                    .is_some_and(|symbol| scope.contains(symbol))
            })
        })
        .collect::<Vec<_>>();
    let expected_signature_count = ir
        .modules
        .iter()
        .flat_map(|module| {
            serde_json::from_slice::<Value>(&module.bytes)
                .ok()
                .and_then(|value| value.get("declarations").and_then(Value::as_array).cloned())
                .unwrap_or_default()
        })
        .filter(|declaration| {
            declaration.get("kind").and_then(Value::as_str) == Some("function")
                && declaration.get("public").and_then(Value::as_bool) == Some(true)
                && scope.is_none_or(|scope| {
                    declaration
                        .get("name")
                        .and_then(Value::as_str)
                        .is_some_and(|symbol| scope.contains(symbol))
                })
        })
        .count();
    if signature_requests.len() != expected_signature_count {
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
        "basedpyright": tool_record(type_checker, "1.39.9")?,
        "compiler": tool_record(&compiler, env!("CARGO_PKG_VERSION"))?,
        "python": {
            "cache_tag": python["cache_tag"],
            "content_hash": hash_file(interpreter)?,
            "executable": interpreter,
            "implementation": "cpython",
            "machine": python["machine"],
            "os": python["os"],
            "platform": python["platform"],
            "version": "3.14.6",
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

    let signature_probe = process(
        interpreter,
        vec![
            "-c".to_owned(),
            "import importlib,inspect,json,sys,typing\nfrom cott_runtime import _cott_load\n\ndef shape(signature):\n return [(name,parameter.kind.name,parameter.default is inspect.Parameter.empty,repr(parameter.default)) for name,parameter in signature.parameters.items()]\n\ndef hint(value):\n if isinstance(value,typing.TypeVar):\n  return ('TypeVar',value.__name__,hint(value.__bound__),tuple(hint(item) for item in value.__constraints__))\n origin=typing.get_origin(value)\n if origin is not None:\n  return (origin,tuple(hint(item) for item in typing.get_args(value)))\n return value\n\nout={}\nfor item in json.loads(sys.argv[1]):\n facade=getattr(importlib.import_module(item['module']),item['function'])\n implementation=_cott_load(item['runtime_path'],item['content_hash'].removeprefix('sha256:'),item['implementation_function'],expected_project_name=item['project'])\n expected_signature=inspect.signature(facade)\n actual_signature=inspect.signature(implementation)\n expected_hints={name:hint(value) for name,value in typing.get_type_hints(facade,include_extras=True).items()}\n actual_hints={name:hint(value) for name,value in typing.get_type_hints(implementation,include_extras=True).items()}\n if shape(actual_signature) != shape(expected_signature) or actual_hints != expected_hints:\n  raise TypeError(f\"{item['symbol']} implementation signature {actual_signature} {actual_hints!r} != {expected_signature} {expected_hints!r}\")\n out[item['symbol']]={'implementation_module':implementation.__module__,'implementation_name':implementation.__name__,'module':facade.__module__,'name':facade.__name__,'signature':str(expected_signature)}\nprint(json.dumps(out,sort_keys=True,separators=(',',':')))".to_owned(),
            serde_json::to_string(&signature_requests).map_err(|error| error.to_string())?,
        ],
        &generated_root,
        scratch,
        &[artifact_root.to_path_buf()],
    )?;
    require_success("runtime signature probe", &signature_probe)?;
    let runtime_signatures: Value = serde_json::from_slice(&signature_probe.stdout)
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
            "checker": "BasedPyright 1.39.9",
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
    if let Some(environment) = external_program_environment(interpreter) {
        mounts.push(environment);
    }
    process(type_checker, arguments, cwd, scratch, &mounts)
}

fn external_program_environment(program: &Path) -> Option<PathBuf> {
    (!program.starts_with("/usr") && !program.starts_with("/bin") && !program.starts_with("/lib"))
        .then(|| program.parent()?.parent().map(Path::to_path_buf))
        .flatten()
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
    run(&SandboxSpec {
        program: program.to_path_buf(),
        arguments,
        cwd: cwd.to_path_buf(),
        environment: BTreeMap::from([
            ("HOME".to_owned(), scratch.display().to_string()),
            ("NO_COLOR".to_owned(), "1".to_owned()),
            ("PATH".to_owned(), "/usr/bin:/bin".to_owned()),
            ("PYTHONDONTWRITEBYTECODE".to_owned(), "1".to_owned()),
            ("PYTHONHASHSEED".to_owned(), "0".to_owned()),
            ("TMPDIR".to_owned(), scratch.display().to_string()),
        ]),
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
        &[artifact_root.to_path_buf()],
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
            let interpreter = root.join("toolchain/bin/python");
            let checker = root.join("project/.venv/bin/basedpyright");
            let scratch = root.join("scratch");
            fs::create_dir_all(interpreter.parent().expect("interpreter parent"))?;
            fs::create_dir_all(checker.parent().expect("checker parent"))?;
            fs::create_dir(&scratch)?;
            fs::copy(fs::canonicalize("/bin/sh")?, &interpreter)?;
            symlink(&interpreter, root.join("project/.venv/bin/python"))?;
            fs::write(
                &checker,
                format!(
                    "#!{}\nprintf 'basedpyright 1.39.9\\n'\n",
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
}
