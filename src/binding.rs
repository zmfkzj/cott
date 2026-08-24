use std::collections::{BTreeMap, BTreeSet, HashSet};
use std::fs;
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};

use crate::hash::sha256_hex;
use crate::manifest::ProjectConfig;
use crate::project::ProjectPaths;
use crate::provenance::GenerationRecord;
use crate::python::artifact_plan::{PythonArtifactPlan, PythonCallable, PythonCallableKind};

/// A validated implementation binding and its byte identity.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ResolvedBinding {
    pub module: String,
    pub function: String,
    pub cott_symbol: String,
    pub kind: PythonCallableKind,
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
    pub cott_symbol: String,
    pub kind: PythonCallableKind,
    pub expected_implementation_function: String,
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
        .callables()
        .into_iter()
        .map(|callable| (callable.cott_symbol.clone(), callable))
        .collect::<BTreeMap<_, _>>();
    let mut diagnostics = Vec::new();
    for symbol in config.python.implementations.keys() {
        match callables.get(symbol) {
            Some(PythonCallable {
                kind: PythonCallableKind::Function,
                ..
            }) => {}
            Some(_) => diagnostics.push(BindingDiagnostic {
                path: paths.manifest.clone(),
                message: format!(
                    "implementation binding key `{symbol}` names an implementation method; implementation methods are agent-only"
                ),
            }),
            None => diagnostics.push(BindingDiagnostic {
                path: paths.manifest.clone(),
                message: format!(
                    "implementation binding key `{symbol}` does not name a public function"
                ),
            }),
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
        let Some(segments) = module_segments(&callable.module) else {
            diagnostics.push(BindingDiagnostic {
                path: paths.python_source_dir.clone(),
                message: format!("invalid canonical module path `{}`", callable.module),
            });
            continue;
        };
        let expected_implementation_function = expected_implementation_function(&callable);
        let mut agent_source = paths.python_source_dir.join("_cott_impl");
        for segment in segments {
            agent_source.push(segment);
        }
        if let PythonCallableKind::ImplMethod { concrete } = &callable.kind {
            agent_source.push(concrete);
        }
        agent_source.push(format!("{}.py", callable.name));
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
                agent_implementation_module(&callable),
                expected_implementation_function.clone(),
                BindingOwner::Agent,
            )
        } else {
            unresolved.push(UnresolvedBinding {
                module: callable.module.clone(),
                function: callable.name.clone(),
                cott_symbol: symbol,
                kind: callable.kind.clone(),
                expected_implementation_function,
                source: agent_source,
            });
            continue;
        };

        let factory_imports = factory_concrete_imports(plan, &callable);
        match read_binding(
            &source,
            &implementation_function,
            &callable,
            &local_imports,
            &generated_type_modules,
            &allowed_facade_imports,
            &factory_imports,
            &locked_imports,
        ) {
            Ok(bytes) => resolved.push(ResolvedBinding {
                module: callable.module,
                function: callable.name,
                cott_symbol: symbol,
                kind: callable.kind,
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
        resolved.sort_by(|left, right| left.cott_symbol.cmp(&right.cott_symbol));
        unresolved.sort_by(|left, right| left.cott_symbol.cmp(&right.cott_symbol));
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

fn private_name(value: &str) -> bool {
    value
        .strip_prefix('_')
        .is_some_and(|suffix| !suffix.is_empty() && !suffix.starts_with('_'))
        && !value.starts_with("_cott_")
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
    let callables = plan.callables();
    let mut matches = callables
        .iter()
        .filter(|callable| callable.cott_symbol == function)
        .collect::<Vec<_>>();
    if matches.is_empty() {
        matches = callables
            .iter()
            .filter(|callable| callable.name == function)
            .collect();
        if matches
            .iter()
            .any(|callable| matches!(&callable.kind, PythonCallableKind::Function))
        {
            matches.retain(|callable| matches!(&callable.kind, PythonCallableKind::Function));
        }
    }
    let callable = matches
        .first()
        .ok_or_else(|| format!("unknown canonical function `{function}`"))?
        .to_owned();
    if matches.len() != 1 {
        return Err(format!("ambiguous canonical function `{function}`"));
    }
    let factory_imports = factory_concrete_imports(plan, &callable);
    validate_source(
        source,
        &expected_implementation_function(&callable),
        &callable,
        &local_import_roots(config, plan),
        &generated_type_modules(plan),
        &allowed_facade_imports(plan),
        &factory_imports,
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
    for callable in plan.public_callables() {
        if matches!(&callable.kind, PythonCallableKind::Function) {
            imports
                .entry(callable.module)
                .or_default()
                .insert(callable.name);
        }
    }
    imports
}

pub(crate) fn factory_concrete_imports(
    plan: &PythonArtifactPlan,
    callable: &PythonCallable,
) -> BTreeMap<String, BTreeSet<String>> {
    let concrete_symbols = plan
        .modules()
        .iter()
        .flat_map(|module| module.declarations.iter())
        .filter(|declaration| {
            declaration.get("kind").and_then(serde_json::Value::as_str) == Some("impl")
        })
        .filter_map(|declaration| declaration.get("name").and_then(serde_json::Value::as_str))
        .collect::<BTreeSet<_>>();
    let mut imports = BTreeMap::new();
    for ty in callable
        .declaration
        .get("parameters")
        .and_then(serde_json::Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(|parameter| parameter.get("type"))
        .chain(callable.declaration.get("return_type"))
    {
        collect_factory_concrete_imports(ty, &callable.module, &concrete_symbols, &mut imports);
    }
    imports
}

fn collect_factory_concrete_imports(
    value: &serde_json::Value,
    callable_module: &str,
    concrete_symbols: &BTreeSet<&str>,
    imports: &mut BTreeMap<String, BTreeSet<String>>,
) {
    let Some(object) = value.as_object() else {
        return;
    };
    if object.get("kind").and_then(serde_json::Value::as_str) == Some("factory") {
        let Some(instance) = object
            .get("instance")
            .and_then(serde_json::Value::as_object)
        else {
            return;
        };
        let Some(symbol) = (instance.get("kind").and_then(serde_json::Value::as_str)
            == Some("named")
            && instance
                .get("args")
                .and_then(serde_json::Value::as_array)
                .is_some_and(Vec::is_empty))
        .then(|| instance.get("name").and_then(serde_json::Value::as_str))
        .flatten() else {
            return;
        };
        let Some((facade, concrete)) = symbol.rsplit_once('.') else {
            return;
        };
        if facade != callable_module && concrete_symbols.contains(symbol) {
            imports
                .entry(facade.to_owned())
                .or_default()
                .insert(concrete.to_owned());
        }
        return;
    }
    for child in object.values() {
        match child {
            serde_json::Value::Object(_) => {
                collect_factory_concrete_imports(child, callable_module, concrete_symbols, imports);
            }
            serde_json::Value::Array(values) => {
                for child in values {
                    collect_factory_concrete_imports(
                        child,
                        callable_module,
                        concrete_symbols,
                        imports,
                    );
                }
            }
            _ => {}
        }
    }
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

fn expected_implementation_function(callable: &PythonCallable) -> String {
    match &callable.kind {
        PythonCallableKind::Function => callable.name.clone(),
        PythonCallableKind::ImplMethod { concrete } => {
            format!("_cott_impl_{concrete}_{}", callable.name)
        }
    }
}

fn agent_implementation_module(callable: &PythonCallable) -> String {
    match &callable.kind {
        PythonCallableKind::Function => format!("_cott_impl.{}.{}", callable.module, callable.name),
        PythonCallableKind::ImplMethod { concrete } => {
            format!(
                "_cott_impl.{}.{concrete}.{}",
                callable.module, callable.name
            )
        }
    }
}

fn generated_type_modules(plan: &PythonArtifactPlan) -> HashSet<String> {
    plan.modules()
        .iter()
        .map(|module| format!("{}_types", module.module))
        .collect()
}
fn is_generated_facade_or_package(module: &str, generated_type_modules: &HashSet<String>) -> bool {
    generated_type_modules.iter().any(|generated| {
        let facade = generated
            .strip_suffix("_types")
            .expect("generated type module suffix");
        facade == module
            || facade
                .strip_prefix(module)
                .is_some_and(|suffix| suffix.starts_with('.'))
    })
}

fn is_exact_generated_facade(module: &str, generated_type_modules: &HashSet<String>) -> bool {
    generated_type_modules.contains(&format!("{module}_types"))
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
    callable: &PythonCallable,
    local_imports: &HashSet<String>,
    generated_type_modules: &HashSet<String>,
    allowed_facade_imports: &BTreeMap<String, BTreeSet<String>>,
    factory_imports: &BTreeMap<String, BTreeSet<String>>,
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
        callable,
        local_imports,
        generated_type_modules,
        allowed_facade_imports,
        factory_imports,
        locked_imports,
    )?;
    Ok(bytes)
}

fn validate_source(
    source: &str,
    expected_function: &str,
    callable: &PythonCallable,
    local_imports: &HashSet<String>,
    generated_type_modules: &HashSet<String>,
    allowed_facade_imports: &BTreeMap<String, BTreeSet<String>>,
    factory_imports: &BTreeMap<String, BTreeSet<String>>,
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
        factory_imports,
        callable,
        locked_imports,
        &mut add_error,
    );
    inspect_function_definitions(&masked, expected_function, callable, &mut add_error);
    inspect_top_level(source, &masked, &mut add_error);

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
    annotation: String,
}

fn inspect_function_definitions(
    source: &str,
    expected_function: &str,
    callable: &PythonCallable,
    add_error: &mut impl FnMut(String),
) {
    let expected = callable
        .declaration
        .get("parameters")
        .and_then(serde_json::Value::as_array)
        .map(|parameters| {
            parameters
                .iter()
                .filter_map(|parameter| {
                    Some(ParameterShape {
                        name: parameter.get("name")?.as_str()?.to_owned(),
                        keyword_only: parameter.get("kind")?.as_str()? == "keyword_only",
                        annotation: String::new(),
                    })
                })
                .collect::<Vec<_>>()
        })
        .unwrap_or_default();
    let lines: Vec<&str> = source.lines().collect();
    let mut expected_count = 0;
    let mut helper_names = HashSet::new();

    for line in &lines {
        let trimmed = line.trim_start();
        if trimmed.starts_with("class ") {
            add_error("class definitions are not allowed".to_owned());
        }
    }
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
            let parameters = if let PythonCallableKind::ImplMethod { concrete } = &callable.kind {
                match parameters.split_first() {
                    Some((self_parameter, parameters))
                        if self_parameter.name == "self"
                            && !self_parameter.keyword_only
                            && self_parameter.annotation == *concrete =>
                    {
                        parameters
                    }
                    _ => {
                        add_error(format!(
                            "function '{expected_function}' must begin with `self: {concrete}`"
                        ));
                        &parameters[..]
                    }
                }
            } else {
                &parameters[..]
            };
            if parameters.len() != expected.len()
                || parameters.iter().zip(&expected).any(|(actual, expected)| {
                    actual.name != expected.name || actual.keyword_only != expected.keyword_only
                })
            {
                add_error(format!(
                    "function '{expected_function}' parameters do not match the canonical signature"
                ));
            }
        } else {
            if !private_name(&name) {
                add_error(format!(
                    "helper function '{name}' must have a single private `_` prefix"
                ));
            }
            if !helper_names.insert(name.clone()) {
                add_error(format!(
                    "implementation must not define duplicate function '{name}'"
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
            annotation: parts[1].trim().to_owned(),
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

fn inspect_top_level(source: &str, masked: &str, add_error: &mut impl FnMut(String)) {
    for (source_line, line) in source.lines().zip(masked.lines()) {
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
            || private_final_literal(source_line.trim())
            || punctuation_only;
        if !allowed {
            add_error(format!(
                "executable top-level statement is not allowed: `{line}`"
            ));
        }
    }
}

fn private_final_literal(line: &str) -> bool {
    let Some((name, rest)) = line.split_once(':') else {
        return false;
    };
    let Some((annotation, value)) = rest.split_once('=') else {
        return false;
    };
    let Some(annotation) = annotation.trim().strip_prefix("Final[") else {
        return false;
    };
    let Some(kind) = annotation.strip_suffix(']') else {
        return false;
    };
    if !private_name(name.trim()) {
        return false;
    }
    let value = value.trim();
    match kind.trim() {
        "bool" => matches!(value, "True" | "False"),
        "int" => integer_literal(value),
        "float" => float_literal(value),
        "str" => string_literal(value),
        "bytes" => value.strip_prefix('b').is_some_and(string_literal),
        _ => false,
    }
}

fn integer_literal(value: &str) -> bool {
    let value = value
        .strip_prefix('+')
        .or_else(|| value.strip_prefix('-'))
        .unwrap_or(value);
    !value.is_empty()
        && value
            .chars()
            .all(|character| character.is_ascii_digit() || character == '_')
        && value.replace('_', "").parse::<i128>().is_ok()
}

fn float_literal(value: &str) -> bool {
    let value = value.replace('_', "");
    !value.is_empty()
        && value.chars().all(|character| {
            character.is_ascii_digit() || matches!(character, '.' | '+' | '-' | 'e' | 'E')
        })
        && (value.contains('.') || value.contains('e') || value.contains('E'))
        && value.parse::<f64>().is_ok()
}

fn string_literal(value: &str) -> bool {
    value.len() >= 2
        && matches!(
            (value.as_bytes()[0], value.as_bytes()[value.len() - 1]),
            (b'\'', b'\'') | (b'"', b'"')
        )
}

fn inspect_imports(
    source: &str,
    local_imports: &HashSet<String>,
    generated_type_modules: &HashSet<String>,
    allowed_facade_imports: &BTreeMap<String, BTreeSet<String>>,
    factory_imports: &BTreeMap<String, BTreeSet<String>>,
    callable: &PythonCallable,
    locked_imports: &HashSet<String>,
    add_error: &mut impl FnMut(String),
) {
    let impl_concrete_import = impl_concrete_import_source(callable);
    let mut imports_impl_concrete = false;
    let mut saw_impl_concrete_import = false;
    for line in source.lines() {
        let trimmed = line.trim_start();
        let nested = trimmed.len() != line.len();
        if let Some(rest) = trimmed.strip_prefix("import ") {
            if nested {
                add_error("nested imports are not allowed".to_owned());
            }
            for item in rest.split(',') {
                let item = item.trim();
                let module = item.split_whitespace().next().unwrap_or_default();
                if is_generated_facade_or_package(module, generated_type_modules) {
                    continue;
                }
                inspect_import_target(
                    module,
                    rest,
                    local_imports,
                    generated_type_modules,
                    None,
                    None,
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
            inspect_impl_concrete_import(
                module,
                imported,
                impl_concrete_import,
                &mut imports_impl_concrete,
                &mut saw_impl_concrete_import,
                add_error,
            );
            inspect_factory_concrete_import(
                module,
                imported,
                generated_type_modules,
                factory_imports,
                add_error,
            );
            let imports_generated_facade_modules = imported.split(',').all(|item| {
                let child = item.split_whitespace().next().unwrap_or_default();
                is_generated_facade_or_package(&format!("{module}.{child}"), generated_type_modules)
            });
            if !imports_generated_facade_modules {
                inspect_import_target(
                    module,
                    imported,
                    local_imports,
                    generated_type_modules,
                    allowed_facade_imports.get(module),
                    factory_imports.get(module),
                    impl_concrete_import
                        .filter(|(facade, _)| module == *facade)
                        .map(|(_, concrete)| concrete),
                    locked_imports,
                    add_error,
                );
            }
            if imported.split_whitespace().any(|word| word == "*") {
                add_error(String::from("star imports are not allowed"));
            }
        }
    }
    if let Some((facade, concrete)) = impl_concrete_import {
        if !imports_impl_concrete && !saw_impl_concrete_import {
            add_error(format!(
                "impl helper concrete `{concrete}` must be imported from facade `{facade}`"
            ));
        }
    }
}

fn impl_concrete_import_source(callable: &PythonCallable) -> Option<(&str, &str)> {
    let PythonCallableKind::ImplMethod { concrete } = &callable.kind else {
        return None;
    };
    let owner = callable.owner.as_ref()?.get("name")?.as_str()?;
    let (facade, owner_concrete) = owner.rsplit_once('.')?;
    (facade == callable.module && owner_concrete == concrete).then_some((facade, concrete))
}

fn inspect_impl_concrete_import(
    module: &str,
    imported: &str,
    impl_concrete_import: Option<(&str, &str)>,
    imports_impl_concrete: &mut bool,
    saw_impl_concrete_import: &mut bool,
    add_error: &mut impl FnMut(String),
) {
    let Some((facade, concrete)) = impl_concrete_import else {
        return;
    };
    for item in imported.split(',').map(str::trim) {
        if item.split_whitespace().next() != Some(concrete) {
            continue;
        }
        *saw_impl_concrete_import = true;
        if module == facade && item == concrete {
            *imports_impl_concrete = true;
        } else if module == facade {
            add_error(format!(
                "impl helper concrete `{concrete}` must be imported from facade `{facade}` without an alias"
            ));
        } else if module.strip_suffix("_types") == Some(facade) {
            add_error(format!(
                "impl helper concrete `{concrete}` must be imported from facade `{facade}`, not generated types `{module}`"
            ));
        } else {
            add_error(format!(
                "impl helper concrete `{concrete}` must be imported from facade `{facade}`, not `{module}`"
            ));
        }
    }
}

fn inspect_factory_concrete_import(
    module: &str,
    imported: &str,
    generated_type_modules: &HashSet<String>,
    factory_imports: &BTreeMap<String, BTreeSet<String>>,
    add_error: &mut impl FnMut(String),
) {
    for (facade, concretes) in factory_imports {
        for item in imported.split(',').map(str::trim) {
            let Some(concrete) = item.split_whitespace().next() else {
                continue;
            };
            if !concretes.contains(concrete)
                || is_exact_generated_facade(module, generated_type_modules) && item == concrete
            {
                continue;
            }
            if module == facade {
                add_error(format!(
                    "factory concrete `{concrete}` must be imported from facade `{facade}` without an alias"
                ));
            } else if module.strip_suffix("_types") == Some(facade) {
                add_error(format!(
                    "factory concrete `{concrete}` must be imported from facade `{facade}`, not generated types `{module}`"
                ));
            } else {
                add_error(format!(
                    "factory concrete `{concrete}` must be imported from facade `{facade}`, not `{module}`"
                ));
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
    allowed_factory_concretes: Option<&BTreeSet<String>>,
    allowed_impl_concrete: Option<&str>,
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
    if is_exact_generated_facade(module, generated_type_modules) {
        for item in imported.split(',').map(str::trim) {
            if item.split_whitespace().count() != 1 {
                add_error(String::from("import aliases are not allowed"));
            } else if item.starts_with('_') {
                add_error(format!(
                    "private generated facade import '{module}.{item}' is not allowed"
                ));
            }
        }
        return;
    }
    if allowed_facade_functions.is_some()
        || allowed_factory_concretes.is_some()
        || allowed_impl_concrete.is_some()
    {
        for item in imported.split(',').map(str::trim) {
            if item.split_whitespace().count() != 1 {
                add_error(String::from("import aliases are not allowed"));
            } else if !allowed_facade_functions.is_some_and(|functions| functions.contains(item))
                && !allowed_factory_concretes.is_some_and(|concretes| concretes.contains(item))
                && allowed_impl_concrete != Some(item)
            {
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
