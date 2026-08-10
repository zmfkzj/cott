use std::collections::{BTreeMap, BTreeSet, HashSet};
use std::fs;
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};

use crate::hash::sha256_hex;
use crate::manifest::ProjectConfig;
use crate::project::ProjectPaths;
use crate::provenance::GenerationRecord;
use crate::python::artifact_plan::PythonArtifactPlan;

/// A validated implementation binding and its byte identity.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ResolvedBinding {
    pub module: String,
    pub function: String,
    pub implementation_module: String,
    pub implementation_function: String,
    pub owner: BindingOwner,
    pub source: PathBuf,
    pub generated_relative: PathBuf,
    pub bytes: Vec<u8>,
    pub sha256: String,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BindingOwner {
    Manifest,
    Agent,
}

/// A stable diagnostic for one expected implementation binding.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BindingDiagnostic {
    pub path: PathBuf,
    pub message: String,
}

/// Resolution separates absent durable sources from invalid sources so
/// `generate` can supply only truly unresolved functions to an agent.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ImplementationResolution {
    pub resolved: Vec<ResolvedBinding>,
    pub unresolved: Vec<UnresolvedBinding>,
    pub stale: Vec<PathBuf>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct UnresolvedBinding {
    pub module: String,
    pub function: String,
    pub source: PathBuf,
}

/// Resolves every canonical planned function to the corresponding Python implementation.
pub fn resolve_bindings(
    config: &ProjectConfig,
    paths: &ProjectPaths,
    plan: &PythonArtifactPlan,
) -> Result<Vec<ResolvedBinding>, Vec<BindingDiagnostic>> {
    let resolution = resolve_implementations(config, paths, plan)?;
    if resolution.unresolved.is_empty() {
        Ok(resolution.resolved)
    } else {
        Err(resolution
            .unresolved
            .into_iter()
            .map(|binding| BindingDiagnostic {
                path: binding.source,
                message: "missing implementation binding".to_owned(),
            })
            .collect())
    }
}

pub fn resolve_implementations(
    config: &ProjectConfig,
    paths: &ProjectPaths,
    plan: &PythonArtifactPlan,
) -> Result<ImplementationResolution, Vec<BindingDiagnostic>> {
    let callables = plan
        .callable_functions()
        .into_iter()
        .filter(|callable| {
            callable
                .declaration
                .get("public")
                .and_then(serde_json::Value::as_bool)
                .unwrap_or(false)
        })
        .map(|callable| (callable.function.clone(), callable))
        .collect::<BTreeMap<_, _>>();
    let mut diagnostics = Vec::new();
    for symbol in config.python.implementations.keys() {
        if !callables.contains_key(symbol) {
            diagnostics.push(BindingDiagnostic {
                path: paths.manifest.clone(),
                message: format!(
                    "implementation binding key `{symbol}` does not name a public function"
                ),
            });
        }
    }
    if !diagnostics.is_empty() {
        return Err(diagnostics);
    }

    let local_imports = local_import_roots(config, plan);
    let generated_type_modules = generated_type_modules(plan);
    let allowed_facade_imports = allowed_facade_imports(plan);
    let locked_imports = match locked_import_roots(paths, &config.project.name) {
        Ok(imports) => imports,
        Err(message) => {
            return Err(vec![BindingDiagnostic {
                path: paths
                    .lockfile
                    .clone()
                    .unwrap_or_else(|| paths.manifest.clone()),
                message,
            }]);
        }
    };
    let recorded_agents = match recorded_agent_sources(paths) {
        Ok(recorded) => recorded,
        Err(message) => {
            return Err(vec![BindingDiagnostic {
                path: paths
                    .generated_dir
                    .parent()
                    .unwrap_or(&paths.generated_dir)
                    .join("generation.json"),
                message,
            }]);
        }
    };
    let mut resolved = Vec::new();
    let mut unresolved = Vec::new();
    let mut expected_agent_files = BTreeSet::new();
    for (symbol, callable) in callables {
        let function = symbol.rsplit('.').next().unwrap_or(&symbol).to_owned();
        if json_contains_opaque(&callable.declaration)
            && !config.python.implementations.contains_key(&symbol)
        {
            diagnostics.push(BindingDiagnostic {
                path: paths.manifest.clone(),
                message: format!(
                    "Opaque boundary function `{symbol}` requires a manifest implementation binding"
                ),
            });
            continue;
        }
        let Some(segments) = module_segments(&callable.module) else {
            diagnostics.push(BindingDiagnostic {
                path: paths.python_source_dir.clone(),
                message: format!("invalid canonical module path `{}`", callable.module),
            });
            continue;
        };
        let mut agent_source = paths.python_source_dir.join("_cott_impl");
        for segment in segments {
            agent_source.push(segment);
        }
        agent_source.push(format!("{function}.py"));
        let generated_relative = agent_source
            .strip_prefix(&paths.python_source_dir)
            .expect("canonical implementation is rooted at Python source")
            .to_path_buf();
        expected_agent_files.insert(agent_source.clone());

        let (source, implementation_module, implementation_function, owner) = if let Some(target) =
            config.python.implementations.get(&symbol)
        {
            match manifest_target(
                paths,
                target,
                &local_imports,
                &generated_type_modules,
                &locked_imports,
            ) {
                Ok((source, module, function)) => {
                    (source, module, function, BindingOwner::Manifest)
                }
                Err(message) => {
                    diagnostics.push(BindingDiagnostic {
                        path: paths.manifest.clone(),
                        message: format!(
                            "invalid implementation binding `{symbol}` = `{target}`: {message}"
                        ),
                    });
                    continue;
                }
            }
        } else if agent_source.exists() {
            let source_origin = agent_source
                .strip_prefix(&paths.root)
                .ok()
                .map(|path| path.to_string_lossy().replace('\\', "/"));
            let content_hash = fs::read(&agent_source)
                .ok()
                .map(|bytes| format!("sha256:{}", sha256_hex(&bytes)));
            if !recorded_agents.get(&symbol).is_some_and(|(path, hash)| {
                source_origin.as_deref() == Some(path.as_str())
                    && content_hash.as_deref() == Some(hash.as_str())
            }) {
                diagnostics.push(BindingDiagnostic {
                        path: agent_source,
                        message: format!(
                            "durable implementation `{symbol}` is neither manifest-bound nor backed by matching agent provenance"
                        ),
                    });
                continue;
            }
            (
                agent_source,
                format!("_cott_impl.{}.{}", callable.module, function),
                function.clone(),
                BindingOwner::Agent,
            )
        } else {
            unresolved.push(UnresolvedBinding {
                module: callable.module,
                function,
                source: agent_source,
            });
            continue;
        };

        match read_binding(
            &source,
            &implementation_function,
            &callable.declaration,
            &local_imports,
            &generated_type_modules,
            &allowed_facade_imports,
            &locked_imports,
        ) {
            Ok(bytes) => resolved.push(ResolvedBinding {
                module: callable.module,
                function,
                implementation_module,
                implementation_function,
                owner,
                source,
                generated_relative,
                sha256: sha256_hex(&bytes),
                bytes,
            }),
            Err(message) => diagnostics.push(BindingDiagnostic {
                path: source,
                message,
            }),
        }
    }
    let stale = collect_stale_agent_files(
        &paths.python_source_dir.join("_cott_impl"),
        &expected_agent_files,
        &mut diagnostics,
    );
    if diagnostics.is_empty() {
        resolved.sort_by(|left, right| {
            (&left.module, &left.function).cmp(&(&right.module, &right.function))
        });

        unresolved.sort_by(|left, right| {
            (&left.module, &left.function).cmp(&(&right.module, &right.function))
        });
        Ok(ImplementationResolution {
            resolved,
            unresolved,
            stale,
        })
    } else {
        Err(diagnostics)
    }
}
fn recorded_agent_sources(
    paths: &ProjectPaths,
) -> Result<BTreeMap<String, (String, String)>, String> {
    let generation = paths
        .generated_dir
        .parent()
        .unwrap_or(&paths.generated_dir)
        .join("generation.json");
    let bytes = match fs::read(&generation) {
        Ok(bytes) => bytes,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(BTreeMap::new()),
        Err(error) => return Err(format!("read generation provenance: {error}")),
    };
    let record = GenerationRecord::parse(&bytes)
        .map_err(|error| format!("invalid generation provenance: {error}"))?;
    let runs = record
        .current
        .agent_runs
        .iter()
        .map(|run| {
            (
                run.symbol.as_str(),
                run.implementation_hash
                    .strip_prefix("sha256:")
                    .unwrap_or(&run.implementation_hash),
            )
        })
        .collect::<BTreeSet<_>>();
    Ok(record
        .current
        .implementations
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|implementation| {
            if implementation
                .get("owner")
                .and_then(serde_json::Value::as_str)
                != Some("agent")
            {
                return None;
            }
            let symbol = implementation.get("cott_symbol")?.as_str()?;
            let path = implementation.get("source_origin")?.as_str()?;
            let hash = implementation.get("content_hash")?.as_str()?;
            let bare_hash = hash.strip_prefix("sha256:").unwrap_or(hash);
            runs.contains(&(symbol, bare_hash))
                .then(|| (symbol.to_owned(), (path.to_owned(), hash.to_owned())))
        })
        .collect())
}

fn json_contains_opaque(value: &serde_json::Value) -> bool {
    match value {
        serde_json::Value::Object(object) => {
            object.get("kind").and_then(serde_json::Value::as_str) == Some("opaque")
                || object.values().any(json_contains_opaque)
        }
        serde_json::Value::Array(values) => values.iter().any(json_contains_opaque),
        _ => false,
    }
}

fn manifest_target(
    paths: &ProjectPaths,
    target: &str,
    local_imports: &HashSet<String>,
    generated_type_modules: &HashSet<String>,
    locked_imports: &HashSet<String>,
) -> Result<(PathBuf, String, String), String> {
    let Some((module, function)) = target.split_once(':') else {
        return Err("must use `module:function` syntax".to_owned());
    };
    if target.matches(':').count() != 1 || !valid_dotted_name(module) || !valid_identifier(function)
    {
        return Err("must name a dotted Python module and simple function".to_owned());
    }
    if generated_type_modules.iter().any(|generated| {
        module == generated.as_str()
            || module
                .strip_prefix(generated.as_str())
                .is_some_and(|suffix| suffix.starts_with('.'))
    }) {
        return Err("generated `*_types` modules cannot own manifest implementations".to_owned());
    }
    let root = module
        .split('.')
        .next()
        .expect("validated module has a root");
    if root == "_cott_impl" {
        return Err(
            "module root `_cott_impl` is reserved for generated implementations".to_owned(),
        );
    }
    if root == "cott_runtime" {
        return Err("module root `cott_runtime` is reserved for the runtime".to_owned());
    }
    if root != "cott_bindings" && local_imports.contains(root) {
        return Err(format!("module root `{root}` is a public Cott facade"));
    }
    if stdlib_modules().contains(root) {
        return Err(format!(
            "module root `{root}` is reserved for the Python standard library"
        ));
    }
    if locked_imports.contains(root) {
        return Err(format!(
            "module root `{root}` is selected as a locked distribution"
        ));
    }
    if !module.starts_with("cott_bindings.") {
        return Err("manifest implementation modules must be below `cott_bindings`".to_owned());
    }
    let mut source = paths.python_source_dir.clone();
    for segment in module.split('.') {
        source.push(segment);
    }
    source.set_extension("py");
    Ok((source, module.to_owned(), function.to_owned()))
}

fn valid_dotted_name(value: &str) -> bool {
    !value.is_empty() && value.split('.').all(valid_identifier)
}

fn valid_identifier(value: &str) -> bool {
    let mut characters = value.chars();
    characters
        .next()
        .is_some_and(|character| character == '_' || character.is_ascii_alphabetic())
        && characters.all(|character| character == '_' || character.is_ascii_alphanumeric())
}

fn collect_stale_agent_files(
    root: &Path,
    expected: &BTreeSet<PathBuf>,
    diagnostics: &mut Vec<BindingDiagnostic>,
) -> Vec<PathBuf> {
    let mut stale = Vec::new();
    if !root.exists() {
        return stale;
    }
    collect_stale_agent_files_at(root, expected, &mut stale, diagnostics);
    stale.sort();
    stale
}

fn collect_stale_agent_files_at(
    directory: &Path,
    expected: &BTreeSet<PathBuf>,
    stale: &mut Vec<PathBuf>,
    diagnostics: &mut Vec<BindingDiagnostic>,
) {
    let entries = match fs::read_dir(directory) {
        Ok(entries) => entries,
        Err(error) => {
            diagnostics.push(BindingDiagnostic {
                path: directory.to_path_buf(),
                message: format!("unable to inspect durable implementations: {error}"),
            });
            return;
        }
    };
    for entry in entries {
        let entry = match entry {
            Ok(entry) => entry,
            Err(error) => {
                diagnostics.push(BindingDiagnostic {
                    path: directory.to_path_buf(),
                    message: format!("unable to inspect durable implementation entry: {error}"),
                });
                continue;
            }
        };
        let path = entry.path();
        let metadata = match fs::symlink_metadata(&path) {
            Ok(metadata) => metadata,
            Err(error) => {
                diagnostics.push(BindingDiagnostic {
                    path,
                    message: format!("unable to inspect durable implementation: {error}"),
                });
                continue;
            }
        };
        if metadata.file_type().is_symlink() {
            diagnostics.push(BindingDiagnostic {
                path,
                message: "durable implementation tree must not contain symlinks".to_owned(),
            });
        } else if metadata.is_dir() {
            collect_stale_agent_files_at(&path, expected, stale, diagnostics);
        } else if metadata.is_file()
            && path.extension().and_then(|extension| extension.to_str()) == Some("py")
            && path.file_name().and_then(|name| name.to_str()) != Some("__init__.py")
            && !expected.contains(&path)
        {
            stale.push(path);
        }
    }
}

pub fn validate_candidate(
    config: &ProjectConfig,
    paths: &ProjectPaths,
    plan: &PythonArtifactPlan,
    function: &str,
    bytes: &[u8],
) -> Result<(), String> {
    let source =
        std::str::from_utf8(bytes).map_err(|_| "binding source is not valid UTF-8".to_owned())?;
    let mut matches = plan.callable_functions().into_iter().filter(|callable| {
        callable.function == function || callable.function.rsplit('.').next() == Some(function)
    });
    let callable = matches
        .next()
        .ok_or_else(|| format!("unknown canonical function `{function}`"))?;
    if matches.next().is_some() {
        return Err(format!("ambiguous canonical function `{function}`"));
    }
    validate_source(
        source,
        callable
            .function
            .rsplit('.')
            .next()
            .unwrap_or(&callable.function),
        &callable.declaration,
        &local_import_roots(config, plan),
        &generated_type_modules(plan),
        &allowed_facade_imports(plan),
        &locked_import_roots(paths, &config.project.name)?,
    )
}

fn local_import_roots(config: &ProjectConfig, plan: &PythonArtifactPlan) -> HashSet<String> {
    let mut roots = HashSet::from([
        String::from("_cott_impl"),
        String::from("cott_bindings"),
        config.project.name.clone(),
    ]);
    for module in plan.modules() {
        if let Some(root) = module.module.split('.').next() {
            roots.insert(root.to_owned());
        }
    }
    roots
}

fn allowed_facade_imports(plan: &PythonArtifactPlan) -> BTreeMap<String, BTreeSet<String>> {
    let mut imports = BTreeMap::<String, BTreeSet<String>>::new();
    for callable in plan.public_callable_functions() {
        let function = callable
            .function
            .rsplit('.')
            .next()
            .unwrap_or(&callable.function)
            .to_owned();
        imports.entry(callable.module).or_default().insert(function);
    }
    imports
}

fn module_segments(module: &str) -> Option<Vec<&str>> {
    let segments = module.split('.').collect::<Vec<_>>();
    (!segments.is_empty()
        && segments.iter().all(|segment| {
            !segment.is_empty()
                && *segment != "."
                && *segment != ".."
                && !segment.contains('/')
                && !segment.contains('\\')
        }))
    .then_some(segments)
}

fn generated_type_modules(plan: &PythonArtifactPlan) -> HashSet<String> {
    plan.modules()
        .iter()
        .map(|module| format!("{}_types", module.module))
        .collect()
}

fn locked_import_roots(
    paths: &ProjectPaths,
    project_name: &str,
) -> Result<HashSet<String>, String> {
    let Some(path) = &paths.lockfile else {
        return Ok(HashSet::new());
    };
    let text = fs::read_to_string(path)
        .map_err(|error| format!("unable to read lockfile {}: {error}", path.display()))?;
    let lock: toml::Value = toml::from_str(&text)
        .map_err(|error| format!("invalid uv lockfile {}: {error}", path.display()))?;
    let packages = lock
        .get("package")
        .and_then(toml::Value::as_array)
        .ok_or_else(|| format!("lockfile {} has no package array", path.display()))?;
    if packages.is_empty() {
        return Ok(HashSet::new());
    }
    let normalize = |name: &str| name.to_ascii_lowercase().replace('_', "-");
    let dependencies = |package: &toml::Value| {
        package
            .get("dependencies")
            .and_then(toml::Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(|dependency| dependency.get("name").and_then(toml::Value::as_str))
            .map(&normalize)
            .collect::<Vec<_>>()
    };
    let project_name = normalize(project_name);
    let project = packages
        .iter()
        .find(|package| {
            package
                .get("name")
                .and_then(toml::Value::as_str)
                .is_some_and(|name| normalize(name) == project_name)
        })
        .ok_or_else(|| {
            format!(
                "lockfile {} omits project package `{project_name}`",
                path.display()
            )
        })?;
    let mut pending = dependencies(project);
    let mut selected = HashSet::new();
    while let Some(name) = pending.pop() {
        if !selected.insert(name.clone()) {
            continue;
        }
        for package in packages.iter().filter(|package| {
            package
                .get("name")
                .and_then(toml::Value::as_str)
                .is_some_and(|candidate| normalize(candidate) == name)
        }) {
            pending.extend(dependencies(package));
        }
    }
    Ok(selected
        .into_iter()
        .map(|name| name.replace('-', "_"))
        .collect())
}

fn read_binding(
    path: &Path,
    expected_function: &str,
    declaration: &serde_json::Value,
    local_imports: &HashSet<String>,
    generated_type_modules: &HashSet<String>,
    allowed_facade_imports: &BTreeMap<String, BTreeSet<String>>,
    locked_imports: &HashSet<String>,
) -> Result<Vec<u8>, String> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| format!("missing or unreadable binding: {error}"))?;
    if metadata.file_type().is_symlink() || !metadata.is_file() || metadata.nlink() != 1 {
        return Err(String::from(
            "binding must be a regular non-symlink single-link file",
        ));
    }

    let bytes = fs::read(path).map_err(|error| format!("unable to read binding: {error}"))?;
    let text = std::str::from_utf8(&bytes)
        .map_err(|_| String::from("binding source is not valid UTF-8"))?;
    validate_source(
        text,
        expected_function,
        declaration,
        local_imports,
        generated_type_modules,
        allowed_facade_imports,
        locked_imports,
    )?;
    Ok(bytes)
}

fn validate_source(
    source: &str,
    expected_function: &str,
    declaration: &serde_json::Value,
    local_imports: &HashSet<String>,
    generated_type_modules: &HashSet<String>,
    allowed_facade_imports: &BTreeMap<String, BTreeSet<String>>,
    locked_imports: &HashSet<String>,
) -> Result<(), String> {
    let masked = mask_python(source);
    let mut errors = Vec::new();
    let mut add_error = |message: String| {
        if !errors.contains(&message) {
            errors.push(message);
        }
    };

    if !source.ends_with('\n') || source.ends_with("\n\n") {
        add_error("binding must end in exactly one newline".to_owned());
    }
    for marker in ["# type: ignore", "# pyright: ignore", "# noqa"] {
        if source.contains(marker) {
            add_error(format!("suppression `{marker}` is not allowed"));
        }
    }
    for token in identifier_tokens(&masked) {
        match token.as_str() {
            "pass" => add_error(String::from("placeholder statement 'pass' is not allowed")),
            "NotImplementedError" => add_error(String::from(
                "placeholder exception 'NotImplementedError' is not allowed",
            )),
            "eval" | "exec" | "compile" => {
                add_error(format!("dynamic operation '{token}' is not allowed"))
            }
            "__import__" | "importlib" | "import_module" => {
                add_error(String::from("dynamic imports are not allowed"))
            }
            "builtins" | "__builtins__" => {
                add_error(String::from("builtin reflection is not allowed"))
            }
            "__file__" | "__path__" | "__spec__" | "__loader__" | "__package__" => {
                add_error(format!("runtime reflection `{token}` is not allowed"))
            }
            "agent" | "agents" => add_error(String::from("agent operations are not allowed")),
            "async" => add_error(String::from("async implementation is not allowed")),
            "global" | "nonlocal" => {
                add_error(format!("function statement `{token}` is not allowed"))
            }
            "yield" => add_error(String::from("generator implementations are not allowed")),
            _ => {}
        }
    }
    if masked.lines().any(|line| {
        let line = line.trim();
        line == "..." || line == "return ..." || line.ends_with("= ...") || line.ends_with(": ...")
    }) {
        add_error(String::from("ellipsis placeholder '...' is not allowed"));
    }
    inspect_imports(
        &masked,
        local_imports,
        generated_type_modules,
        allowed_facade_imports,
        locked_imports,
        &mut add_error,
    );
    inspect_function_definitions(&masked, expected_function, declaration, &mut add_error);
    inspect_top_level(&masked, &mut add_error);

    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors.join("; "))
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct ParameterShape {
    name: String,
    keyword_only: bool,
}

fn inspect_function_definitions(
    source: &str,
    expected_function: &str,
    declaration: &serde_json::Value,
    add_error: &mut impl FnMut(String),
) {
    let expected = declaration
        .get("parameters")
        .and_then(serde_json::Value::as_array)
        .map(|parameters| {
            parameters
                .iter()
                .filter_map(|parameter| {
                    Some(ParameterShape {
                        name: parameter.get("name")?.as_str()?.to_owned(),
                        keyword_only: parameter.get("kind")?.as_str()? == "keyword_only",
                    })
                })
                .collect::<Vec<_>>()
        })
        .unwrap_or_default();
    let lines: Vec<&str> = source.lines().collect();
    let mut expected_count = 0;

    for (line_number, line) in lines.iter().enumerate() {
        if !line.starts_with("def ") {
            continue;
        }
        let signature = collect_signature(&lines, line_number);
        let Some((name, parameters)) = parse_signature(&signature, add_error) else {
            continue;
        };
        if name == expected_function {
            expected_count += 1;
            if parameters != expected {
                add_error(format!(
                    "function '{expected_function}' parameters do not match the canonical signature"
                ));
            }
        }
        let mut previous = line_number;
        while previous > 0 {
            previous -= 1;
            let previous_line = lines[previous].trim();
            if previous_line.is_empty() {
                continue;
            }
            if previous_line.starts_with('@') {
                add_error(format!("function '{name}' must not be decorated"));
            }
            break;
        }
    }

    match expected_count {
        0 => add_error(format!(
            "implementation must define expected function '{expected_function}'"
        )),
        1 => {}
        _ => add_error(format!(
            "implementation must define exactly one top-level function '{expected_function}'"
        )),
    }
}

fn parse_signature(
    signature: &str,
    add_error: &mut impl FnMut(String),
) -> Option<(String, Vec<ParameterShape>)> {
    let rest = signature.strip_prefix("def ")?;
    let open = rest.find('(')?;
    let close = matching_close(rest, open)?;
    let name = rest[..open].trim();
    if !valid_identifier(name) {
        add_error("top-level function must have a simple name".to_owned());
        return None;
    }
    let tail = rest[close + 1..].trim();
    let Some(annotation) = tail.strip_prefix("->") else {
        add_error(format!("function '{name}' must have a return annotation"));
        return None;
    };
    let Some(colon) = annotation.rfind(':') else {
        add_error(format!("function '{name}' has an incomplete signature"));
        return None;
    };
    if annotation[..colon].trim().is_empty() {
        add_error(format!("function '{name}' must have a return annotation"));
    }

    let mut keyword_only = false;
    let mut parameters = Vec::new();
    for raw in split_top_level(&rest[open + 1..close], ',') {
        let raw = raw.trim();
        if raw.is_empty() {
            continue;
        }
        if raw == "*" {
            keyword_only = true;
            continue;
        }
        if raw == "/" {
            add_error(format!(
                "function '{name}' must not use positional-only parameters"
            ));
            continue;
        }
        if raw.starts_with('*') {
            add_error(format!(
                "function '{name}' must not use variadic parameters"
            ));
            continue;
        }
        if split_top_level(raw, '=').len() != 1 {
            add_error(format!(
                "function '{name}' parameters must not have defaults"
            ));
            continue;
        }
        let parts = split_top_level(raw, ':');
        if parts.len() != 2 || parts[1].trim().is_empty() {
            add_error(format!(
                "function '{name}' parameter `{raw}` must have one concrete annotation"
            ));
            continue;
        }
        let parameter = parts[0].trim();
        if !valid_identifier(parameter) {
            add_error(format!(
                "function '{name}' has an invalid parameter `{parameter}`"
            ));
            continue;
        }
        parameters.push(ParameterShape {
            name: parameter.to_owned(),
            keyword_only,
        });
    }
    Some((name.to_owned(), parameters))
}

fn matching_close(value: &str, open: usize) -> Option<usize> {
    let mut depth = 0usize;
    for (index, character) in value.char_indices().skip_while(|(index, _)| *index < open) {
        match character {
            '(' => depth += 1,
            ')' => {
                depth = depth.checked_sub(1)?;
                if depth == 0 {
                    return Some(index);
                }
            }
            _ => {}
        }
    }
    None
}

fn split_top_level(value: &str, separator: char) -> Vec<&str> {
    let mut parts = Vec::new();
    let mut start = 0;
    let mut depth = 0usize;
    for (index, character) in value.char_indices() {
        match character {
            '(' | '[' | '{' => depth += 1,
            ')' | ']' | '}' => depth = depth.saturating_sub(1),
            _ if character == separator && depth == 0 => {
                parts.push(&value[start..index]);
                start = index + character.len_utf8();
            }
            _ => {}
        }
    }
    parts.push(&value[start..]);
    parts
}

fn collect_signature(lines: &[&str], start: usize) -> String {
    let mut result = String::new();
    let mut depth = 0i32;
    for line in &lines[start..] {
        if !result.is_empty() {
            result.push(' ');
        }
        result.push_str(line.trim());
        for character in line.chars() {
            match character {
                '(' | '[' | '{' => depth += 1,
                ')' | ']' | '}' => depth = (depth - 1).max(0),
                ':' if depth == 0 => return result,
                _ => {}
            }
        }
    }
    result
}

fn inspect_top_level(source: &str, add_error: &mut impl FnMut(String)) {
    for line in source.lines() {
        if line.is_empty() || line.starts_with(char::is_whitespace) {
            continue;
        }
        let line = line.trim();
        let punctuation_only = line
            .chars()
            .all(|character| matches!(character, ',' | ')' | ']' | '}'));
        let allowed = line.starts_with("def ")
            || line.starts_with("import ")
            || line.starts_with("from ")
            || line.starts_with('@')
            || line.contains("TypeVar(")
            || (line.contains("Final[") && line.contains('='))
            || punctuation_only;
        if !allowed {
            add_error(format!(
                "executable top-level statement is not allowed: `{line}`"
            ));
        }
    }
}

fn inspect_imports(
    source: &str,
    local_imports: &HashSet<String>,
    generated_type_modules: &HashSet<String>,
    allowed_facade_imports: &BTreeMap<String, BTreeSet<String>>,
    locked_imports: &HashSet<String>,
    add_error: &mut impl FnMut(String),
) {
    for line in source.lines() {
        let trimmed = line.trim_start();
        let nested = trimmed.len() != line.len();
        if let Some(rest) = trimmed.strip_prefix("import ") {
            if nested {
                add_error("nested imports are not allowed".to_owned());
            }
            for item in rest.split(',') {
                let module = item.split_whitespace().next().unwrap_or_default();
                inspect_import_target(
                    module,
                    rest,
                    local_imports,
                    generated_type_modules,
                    None,
                    locked_imports,
                    add_error,
                );
            }
        } else if let Some(rest) = trimmed.strip_prefix("from ") {
            if nested {
                add_error("nested imports are not allowed".to_owned());
            }
            let Some((module, imported)) = rest.split_once(" import ") else {
                continue;
            };
            let module = module.trim();
            if module == "__future__" && imported.trim() != "annotations" {
                add_error("only `from __future__ import annotations` is allowed".to_owned());
            }
            inspect_import_target(
                module,
                imported,
                local_imports,
                generated_type_modules,
                allowed_facade_imports.get(module),
                locked_imports,
                add_error,
            );
            if imported.split_whitespace().any(|word| word == "*") {
                add_error(String::from("star imports are not allowed"));
            }
        }
    }
}

fn inspect_import_target(
    module: &str,
    imported: &str,
    local_imports: &HashSet<String>,
    generated_type_modules: &HashSet<String>,
    allowed_facade_functions: Option<&BTreeSet<String>>,
    locked_imports: &HashSet<String>,
    add_error: &mut impl FnMut(String),
) {
    if module.starts_with('.') {
        add_error(String::from("relative imports are not allowed"));
        return;
    }
    if module.is_empty() || module == "*" {
        add_error(String::from("dynamic imports are not allowed"));
        return;
    }
    if imported.split_whitespace().any(|word| word == "*") {
        add_error(String::from("star imports are not allowed"));
    }
    if let Some(functions) = allowed_facade_functions {
        for item in imported.split(',').map(str::trim) {
            if item.split_whitespace().count() != 1 {
                add_error(String::from("import aliases are not allowed"));
            } else if !functions.contains(item) {
                add_error(format!(
                    "project-local import '{module}.{item}' is not allowed"
                ));
            }
        }
        return;
    }
    let root = module.split('.').next().unwrap_or(module);
    if generated_type_modules.contains(module) {
        return;
    }
    if local_imports.contains(root) {
        add_error(format!("project-local import '{module}' is not allowed"));
    } else if root == "cott_runtime" || stdlib_modules().contains(root) {
        return;
    } else if !locked_imports.contains(root) {
        add_error(format!(
            "external distribution import '{module}' is not selected in uv.lock"
        ));
    }
}

fn stdlib_modules() -> HashSet<&'static str> {
    HashSet::from([
        "__future__",
        "abc",
        "array",
        "ast",
        "asyncio",
        "base64",
        "binascii",
        "bisect",
        "builtins",
        "calendar",
        "cmath",
        "codecs",
        "collections",
        "contextlib",
        "copy",
        "csv",
        "dataclasses",
        "datetime",
        "decimal",
        "enum",
        "errno",
        "faulthandler",
        "fnmatch",
        "fractions",
        "functools",
        "gc",
        "getopt",
        "glob",
        "gzip",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "importlib",
        "inspect",
        "io",
        "itertools",
        "json",
        "keyword",
        "logging",
        "math",
        "numbers",
        "operator",
        "os",
        "pathlib",
        "pickle",
        "platform",
        "pprint",
        "random",
        "re",
        "secrets",
        "select",
        "shlex",
        "shutil",
        "signal",
        "site",
        "socket",
        "sqlite3",
        "ssl",
        "stat",
        "statistics",
        "string",
        "struct",
        "subprocess",
        "sys",
        "tempfile",
        "textwrap",
        "threading",
        "time",
        "timeit",
        "token",
        "traceback",
        "types",
        "typing",
        "unicodedata",
        "unittest",
        "urllib",
        "uuid",
        "warnings",
        "weakref",
        "xml",
        "zipfile",
    ])
}

fn identifier_tokens(source: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut current = String::new();
    for character in source.chars() {
        if character == '_' || character.is_ascii_alphanumeric() {
            current.push(character);
        } else if !current.is_empty() {
            tokens.push(std::mem::take(&mut current));
        }
    }
    if !current.is_empty() {
        tokens.push(current);
    }
    tokens
}

fn mask_python(source: &str) -> String {
    let input: Vec<char> = source.chars().collect();
    let mut output = input.clone();
    let mut index = 0;
    let mut quote = None;
    let mut triple = false;
    while index < input.len() {
        if quote.is_none() {
            if input[index] == '#' {
                while index < input.len() && input[index] != '\n' {
                    output[index] = ' ';
                    index += 1;
                }
                continue;
            }
            if input[index] == '\'' || input[index] == '"' {
                quote = Some(input[index]);
                triple = input.get(index + 1) == quote.as_ref()
                    && input.get(index + 2) == quote.as_ref();
                output[index] = ' ';
                if triple {
                    output[index + 1] = ' ';
                    output[index + 2] = ' ';
                    index += 3;
                } else {
                    index += 1;
                }
                continue;
            }
            index += 1;
            continue;
        }

        if input[index] == '\n' {
            if !triple {
                quote = None;
            }
            index += 1;
            continue;
        }
        if input[index] == '\\' && !triple {
            output[index] = ' ';
            if index + 1 < input.len() && input[index + 1] != '\n' {
                output[index + 1] = ' ';
                index += 2;
            } else {
                index += 1;
            }
            continue;
        }
        if input[index] == quote.unwrap() {
            if triple {
                if input.get(index + 1) == quote.as_ref() && input.get(index + 2) == quote.as_ref()
                {
                    output[index] = ' ';
                    output[index + 1] = ' ';
                    output[index + 2] = ' ';
                    index += 3;
                    quote = None;
                    triple = false;
                    continue;
                }
            } else {
                output[index] = ' ';
                index += 1;
                quote = None;
                continue;
            }
        }
        output[index] = ' ';
        index += 1;
    }
    output.into_iter().collect()
}
