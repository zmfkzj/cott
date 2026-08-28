use rustpython_parser::{Parse, ast};
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

/// Resolves every agent- or manifest-owned canonical callable to its Python implementation.
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
            Some(callable) if is_compiler_owned_selected_method(callable) => {
                diagnostics.push(BindingDiagnostic {
                    path: paths.manifest.clone(),
                    message: format!(
                        "implementation binding key `{symbol}` names a compiler-owned {} implementation method",
                        selected_implementation_kind(callable).expect("compiler-owned selection has a kind"),
                    ),
                })
            }
            Some(PythonCallable {
                kind: PythonCallableKind::Function | PythonCallableKind::AsyncFunction,
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
    for callable in callables
        .values()
        .filter(|callable| is_compiler_owned_selected_method(callable))
    {
        let kind =
            selected_implementation_kind(callable).expect("compiler-owned selection has a kind");
        let Some(symbol) = selected_verified_facade(callable) else {
            diagnostics.push(BindingDiagnostic {
                path: paths.python_source_dir.clone(),
                message: format!(
                    "{kind} implementation method `{}` has no verified facade dependency",
                    callable.cott_symbol
                ),
            });
            continue;
        };
        if !matches!(
            callables.get(symbol),
            Some(PythonCallable {
                kind: PythonCallableKind::Function | PythonCallableKind::AsyncFunction,
                ..
            })
        ) {
            diagnostics.push(BindingDiagnostic {
                path: paths.python_source_dir.clone(),
                message: format!(
                    "{kind} implementation method `{}` references non-callable verified facade `{symbol}`",
                    callable.cott_symbol
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
        if is_compiler_owned_selected_method(&callable) {
            continue;
        }
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
        if let Some(concrete) = impl_concrete(&callable.kind) {
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
            plan,
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
            .any(|callable| is_free_function(&callable.kind))
        {
            matches.retain(|callable| is_free_function(&callable.kind));
        }
    }
    let callable = matches
        .first()
        .ok_or_else(|| format!("unknown canonical function `{function}`"))?
        .to_owned();
    if matches.len() != 1 {
        return Err(format!("ambiguous canonical function `{function}`"));
    }
    if is_compiler_owned_selected_method(&callable) {
        let kind =
            selected_implementation_kind(&callable).expect("compiler-owned selection has a kind");
        return Err(format!(
            "compiler-owned {kind} implementation method `{}` does not accept an agent implementation",
            callable.cott_symbol
        ));
    }
    let factory_imports = factory_concrete_imports(plan, &callable);
    validate_source(
        source,
        &expected_implementation_function(&callable),
        plan,
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
    for callable in plan.callables() {
        if is_free_function(&callable.kind) {
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

fn selected_implementation_kind(callable: &PythonCallable) -> Option<&str> {
    let kind = callable
        .declaration
        .get("selected")
        .and_then(|selected| selected.get("origin"))
        .and_then(serde_json::Value::as_str)?;
    matches!(kind, "default" | "specialization").then_some(kind)
}

fn is_compiler_owned_selected_method(callable: &PythonCallable) -> bool {
    impl_concrete(&callable.kind).is_some() && selected_implementation_kind(callable).is_some()
}

fn selected_verified_facade(callable: &PythonCallable) -> Option<&str> {
    let selected = callable
        .declaration
        .get("selected")
        .and_then(serde_json::Value::as_object)?;
    selected_implementation_kind(callable)?;
    let function = selected
        .get("function")
        .and_then(serde_json::Value::as_object)?;
    let module = function.get("module").and_then(serde_json::Value::as_str)?;
    let symbol = function.get("symbol").and_then(serde_json::Value::as_str)?;
    let facade = function
        .get("verified_facade")
        .and_then(serde_json::Value::as_str)?;
    (facade == format!("{module}.{symbol}")).then_some(facade)
}

fn is_free_function(kind: &PythonCallableKind) -> bool {
    matches!(
        kind,
        PythonCallableKind::Function | PythonCallableKind::AsyncFunction
    )
}

fn is_async_function(kind: &PythonCallableKind) -> bool {
    matches!(
        kind,
        PythonCallableKind::AsyncFunction | PythonCallableKind::AsyncImplMethod { .. }
    )
}

fn impl_concrete(kind: &PythonCallableKind) -> Option<&str> {
    match kind {
        PythonCallableKind::ImplMethod { concrete }
        | PythonCallableKind::AsyncImplMethod { concrete } => Some(concrete),
        _ => None,
    }
}

fn expected_implementation_function(callable: &PythonCallable) -> String {
    match impl_concrete(&callable.kind) {
        Some(concrete) => format!("_cott_impl_{concrete}_{}", callable.name),
        None => callable.name.clone(),
    }
}

fn agent_implementation_module(callable: &PythonCallable) -> String {
    match impl_concrete(&callable.kind) {
        Some(concrete) => format!(
            "_cott_impl.{}.{concrete}.{}",
            callable.module, callable.name
        ),
        None => format!("_cott_impl.{}.{}", callable.module, callable.name),
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
    plan: &PythonArtifactPlan,
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
        plan,
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
    plan: &PythonArtifactPlan,
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
            "getattr" | "setattr" | "delattr" | "hasattr" | "dir" | "vars" | "globals"
            | "locals" | "__getattr__" | "__getattribute__" | "attrgetter" | "methodcaller" => {
                add_error(format!("runtime reflection `{token}` is not allowed"))
            }
            "__file__" | "__path__" | "__spec__" | "__loader__" | "__package__" => {
                add_error(format!("runtime reflection `{token}` is not allowed"))
            }
            "agent" | "agents" => add_error(String::from("agent operations are not allowed")),
            "async" if !is_async_function(&callable.kind) => {
                add_error(String::from("async implementation is not allowed"))
            }
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
    inspect_effects(source, expected_function, callable, plan, &mut add_error);
    inspect_top_level(source, &masked, &mut add_error);

    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors.join("; "))
    }
}

#[derive(Default)]
struct EffectGraph {
    async_cott: BTreeSet<String>,
    cott: BTreeMap<String, BTreeSet<String>>,
    imported: BTreeMap<String, String>,
    modules: BTreeMap<String, String>,
    module_roots: BTreeSet<String>,
    leaves: BTreeSet<String>,
    factory_parameters: BTreeSet<String>,
    target_function: String,
    local: BTreeMap<String, LocalEffects>,
    impl_concrete: Option<String>,
    impl_methods: BTreeMap<String, String>,
    async_function: bool,
    dyn_closures: BTreeMap<String, BTreeMap<String, usize>>,
    dyn_specializations: BTreeMap<String, String>,
    dyn_methods: BTreeMap<(String, String), String>,
    dyn_dispatches: BTreeMap<(String, String), String>,
    dyn_conflicts: BTreeSet<(String, String)>,
    dyn_aliases: BTreeMap<String, String>,
    errors: BTreeSet<String>,
}

#[derive(Clone)]
struct DynReceiver {
    trait_ref: String,
}

#[derive(Clone, Default)]
struct LocalEffects {
    local_calls: BTreeSet<String>,
    cott_calls: BTreeSet<String>,
    factory_parameters: BTreeSet<String>,
    parameters: BTreeSet<String>,
    assigned: BTreeSet<String>,
    impl_receivers: BTreeSet<String>,
    dyn_receivers: BTreeMap<String, DynReceiver>,
    task_groups: BTreeSet<String>,
}

fn record_effect_cott_call(
    symbol: &str,
    awaited: bool,
    local: &mut LocalEffects,
    graph: &mut EffectGraph,
) {
    if graph.async_cott.contains(symbol) {
        if !awaited {
            graph
                .errors
                .insert(format!("async Cott callable `{symbol}` must be awaited"));
        }
    } else if awaited {
        graph
            .errors
            .insert(format!("sync Cott callable `{symbol}` must not be awaited"));
    }
    local.cott_calls.insert(symbol.to_owned());
}

fn inspect_effects(
    source: &str,
    expected_function: &str,
    callable: &PythonCallable,
    plan: &PythonArtifactPlan,
    add_error: &mut impl FnMut(String),
) {
    let suite = match ast::Suite::parse(source, "<binding>") {
        Ok(suite) => suite,
        Err(error) => {
            add_error(format!("binding source is not valid Python: {error}"));
            return;
        }
    };
    let plan_callables = plan.callables();
    let impl_methods = impl_concrete(&callable.kind).map_or_else(BTreeMap::new, |concrete| {
        plan_callables
            .iter()
            .filter(|candidate| {
                candidate.module == callable.module
                    && impl_concrete(&candidate.kind) == Some(concrete)
            })
            .map(|candidate| (candidate.name.clone(), candidate.cott_symbol.clone()))
            .collect()
    });
    let mut graph = EffectGraph {
        cott: plan_callables
            .iter()
            .filter(|candidate| {
                is_free_function(&candidate.kind)
                    || (candidate.module == callable.module
                        && impl_concrete(&candidate.kind).is_some()
                        && impl_concrete(&candidate.kind) == impl_concrete(&callable.kind))
            })
            .map(|candidate| {
                (
                    candidate.cott_symbol.clone(),
                    declaration_effects(&candidate.declaration),
                )
            })
            .collect(),
        async_cott: plan_callables
            .iter()
            .filter(|candidate| is_async_function(&candidate.kind))
            .map(|candidate| candidate.cott_symbol.clone())
            .collect(),
        impl_concrete: impl_concrete(&callable.kind).map(str::to_owned),
        impl_methods,
        target_function: expected_function.to_owned(),
        ..EffectGraph::default()
    };
    build_dyn_effects(&plan_callables, plan, &mut graph);
    graph.factory_parameters.extend(
        callable
            .declaration
            .get("parameters")
            .and_then(serde_json::Value::as_array)
            .into_iter()
            .flatten()
            .filter(|parameter| {
                parameter
                    .get("type")
                    .and_then(|ty| ty.get("kind"))
                    .and_then(serde_json::Value::as_str)
                    == Some("factory")
            })
            .filter_map(|parameter| parameter.get("name").and_then(serde_json::Value::as_str))
            .map(str::to_owned),
    );
    for statement in &suite {
        collect_effect_imports(statement, &mut graph);
        collect_dyn_imports(statement, &mut graph);
    }
    for statement in &suite {
        match statement {
            ast::Stmt::FunctionDef(function) => {
                graph
                    .local
                    .insert(function.name.as_str().to_owned(), LocalEffects::default());
            }
            ast::Stmt::AsyncFunctionDef(function) => {
                graph
                    .local
                    .insert(function.name.as_str().to_owned(), LocalEffects::default());
            }
            _ => {}
        }
    }
    for statement in &suite {
        match statement {
            ast::Stmt::FunctionDef(function) => inspect_effect_function(
                function.name.as_str(),
                false,
                &function.args,
                &function.body,
                &mut graph,
            ),
            ast::Stmt::AsyncFunctionDef(function) => inspect_effect_function(
                function.name.as_str(),
                true,
                &function.args,
                &function.body,
                &mut graph,
            ),
            _ => {}
        }
    }
    let declared = declaration_effects(&callable.declaration);
    let actual = effect_union(expected_function, &graph, &mut BTreeSet::new());
    for (effect, path) in actual {
        if !declared.contains(&effect) {
            graph.errors.insert(format!(
                "effect `{effect}` reaches `{expected_function}` through {}",
                path.join(" -> ")
            ));
        }
    }
    for error in graph.errors {
        add_error(error);
    }
}

fn declaration_effects(declaration: &serde_json::Value) -> BTreeSet<String> {
    declaration
        .get("effects")
        .or_else(|| {
            declaration
                .get("contract")
                .and_then(|contract| contract.get("effects"))
        })
        .and_then(serde_json::Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(|effect| {
            effect
                .get("key")
                .and_then(serde_json::Value::as_str)
                .or_else(|| effect.as_str())
        })
        .map(str::to_owned)
        .collect()
}

fn named_trait_symbol(value: &serde_json::Value) -> Option<&str> {
    (value.get("kind").and_then(serde_json::Value::as_str) == Some("named"))
        .then(|| value.get("name").and_then(serde_json::Value::as_str))
        .flatten()
}

fn canonical_trait_reference(value: &serde_json::Value) -> Option<String> {
    let name = named_trait_symbol(value)?;
    let args = value
        .get("args")
        .and_then(serde_json::Value::as_array)
        .into_iter()
        .flatten()
        .map(
            |argument| match argument.get("kind").and_then(serde_json::Value::as_str) {
                Some("type") => canonical_type_reference(argument.get("type")?),
                Some("const") => argument.get("value").and_then(|value| {
                    value
                        .get("value")
                        .map(serde_json::Value::to_string)
                        .map(|value| format!("Literal[{value}]"))
                }),
                _ => None,
            },
        )
        .collect::<Option<Vec<_>>>()?;
    (!args.is_empty())
        .then(|| format!("{}[{}]", name, args.join(",")))
        .or_else(|| Some(name.to_owned()))
}

fn canonical_type_reference(value: &serde_json::Value) -> Option<String> {
    let kind = value.get("kind").and_then(serde_json::Value::as_str)?;
    let item = |name: &str| canonical_type_reference(value.get(name)?);
    let pair = |left: &str, right: &str| {
        Some(format!(
            "{},{}",
            canonical_type_reference(value.get(left)?)?,
            canonical_type_reference(value.get(right)?)?
        ))
    };
    match kind {
        "named" => {
            let name = named_trait_symbol(value)?.rsplit('.').next()?;
            let args = value
                .get("args")
                .and_then(serde_json::Value::as_array)
                .into_iter()
                .flatten()
                .map(
                    |argument| match argument.get("kind").and_then(serde_json::Value::as_str) {
                        Some("type") => canonical_type_reference(argument.get("type")?),
                        Some("const") => canonical_fixed_length(argument.get("value")?),
                        _ => None,
                    },
                )
                .collect::<Option<Vec<_>>>()?;
            Some(if args.is_empty() {
                name.to_owned()
            } else {
                format!("{name}[{}]", args.join(","))
            })
        }
        "type_parameter" => value
            .get("name")
            .and_then(serde_json::Value::as_str)
            .map(str::to_owned),
        "primitive" => match value.get("name").and_then(serde_json::Value::as_str)? {
            "bool" => Some("bool".to_owned()),
            "i8" => Some("I8".to_owned()),
            "i16" => Some("I16".to_owned()),
            "i32" => Some("I32".to_owned()),
            "i64" => Some("I64".to_owned()),
            "u8" => Some("U8".to_owned()),
            "u16" => Some("U16".to_owned()),
            "u32" => Some("U32".to_owned()),
            "u64" => Some("U64".to_owned()),
            "f32" => Some("F32".to_owned()),
            "f64" => Some("F64".to_owned()),
            "str" => Some("str".to_owned()),
            "bytes" => Some("bytes".to_owned()),
            "path" => Some("Path".to_owned()),
            "unit" => Some("Unit".to_owned()),
            "json" => Some("JsonValue".to_owned()),
            "any" => Some("Any".to_owned()),
            "unknown" => Some("object".to_owned()),
            "never" => Some("Never".to_owned()),
            _ => None,
        },
        "list" => Some(format!("CottList[{}]", item("item")?)),
        "set" => Some(format!("CottSet[{}]", item("item")?)),
        "map" => Some(format!("FrozenMap[{}]", pair("key", "value")?)),
        "option" => Some(format!("Option[{}]", item("item")?)),
        "result" => Some(format!("Result[{}]", pair("ok", "error")?)),
        "iterator" => Some(format!("Iterator[{}]", item("item")?)),
        "async_iterator" => Some(format!("AsyncIterator[{}]", item("item")?)),
        "factory" => Some(format!("type[{}]", item("instance")?)),
        "dyn" => Some(format!("Dyn[{}]", item("trait")?)),
        "array" => Some(format!(
            "CottArray[{},{}]",
            item("item")?,
            canonical_fixed_length(value.get("length")?)?
        )),
        "buffer" => Some(format!(
            "CottBuffer[{}]",
            canonical_fixed_length(value.get("length")?)?
        )),
        "tuple" => value
            .get("items")
            .and_then(serde_json::Value::as_array)
            .and_then(|items| {
                items
                    .iter()
                    .map(canonical_type_reference)
                    .collect::<Option<Vec<_>>>()
                    .map(|items| {
                        if items.is_empty() {
                            "tuple[()]".to_owned()
                        } else {
                            format!("tuple[{}]", items.join(","))
                        }
                    })
            }),
        "generator" => Some(format!(
            "Generator[{},{},{}]",
            item("yield")?,
            item("send")?,
            item("return")?
        )),
        "async_generator" => Some(format!(
            "AsyncGenerator[{},{}]",
            item("yield")?,
            item("send")?
        )),
        "opaque" => Some(format!(
            "Opaque[Literal[{}]]",
            serde_json::to_string(value.get("tag")?.as_str()?).ok()?
        )),
        "associated_projection" => Some(format!(
            "{}_{}_{}",
            value.get("trait")?.as_str()?.replace('.', "_"),
            value.get("name")?.as_str()?.replace('.', "_"),
            sha256_hex(&serde_json::to_vec(value.get("base")?).ok()?)
        )),
        _ => None,
    }
}

fn canonical_fixed_length(value: &serde_json::Value) -> Option<String> {
    let value = value.get("value")?;
    match value {
        serde_json::Value::String(value)
            if value.chars().all(|character| character.is_ascii_digit()) =>
        {
            Some(format!("Literal[{value}]"))
        }
        serde_json::Value::String(value) => {
            Some(format!("Literal[{}]", serde_json::to_string(value).ok()?))
        }
        serde_json::Value::Number(value) => Some(format!("Literal[{value}]")),
        _ => None,
    }
}

fn trait_method_key(name: &str) -> Option<(&str, &str)> {
    name.rsplit_once('.')
}

fn build_dyn_effects(
    callables: &[PythonCallable],
    plan: &PythonArtifactPlan,
    graph: &mut EffectGraph,
) {
    let mut members = BTreeMap::new();
    let mut parents = BTreeMap::<String, Vec<String>>::new();
    let mut declared_closures = BTreeMap::<String, BTreeSet<String>>::new();
    for (_, declaration) in plan.declarations() {
        if declaration.get("kind").and_then(serde_json::Value::as_str) != Some("trait") {
            continue;
        }
        let Some(trait_name) = declaration.get("name").and_then(serde_json::Value::as_str) else {
            continue;
        };
        let mut closure = declaration
            .get("closure")
            .and_then(serde_json::Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(named_trait_symbol)
            .map(str::to_owned)
            .collect::<BTreeSet<_>>();
        closure.insert(trait_name.to_owned());
        declared_closures.insert(trait_name.to_owned(), closure);
        parents.insert(
            trait_name.to_owned(),
            declaration
                .get("parents")
                .and_then(serde_json::Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(|parent| parent.get("trait").and_then(named_trait_symbol))
                .map(str::to_owned)
                .collect(),
        );
        for method in declaration
            .get("methods")
            .and_then(serde_json::Value::as_array)
            .into_iter()
            .flatten()
        {
            let Some((member_trait, method_name)) = method
                .get("name")
                .and_then(serde_json::Value::as_str)
                .and_then(trait_method_key)
            else {
                continue;
            };
            let Some(kind) = method
                .get("callable_kind")
                .and_then(serde_json::Value::as_str)
            else {
                continue;
            };
            members.insert(
                (member_trait.to_owned(), method_name.to_owned()),
                (kind.to_owned(), declaration_effects(method)),
            );
        }
    }
    for (trait_name, declared) in &declared_closures {
        let mut closure = BTreeMap::new();
        let mut pending = BTreeSet::from([(0usize, trait_name.clone())]);
        while let Some((distance, current)) = pending.pop_first() {
            if !declared.contains(&current)
                || closure.get(&current).is_some_and(|best| *best <= distance)
            {
                continue;
            }
            closure.insert(current.clone(), distance);
            for parent in parents.get(&current).into_iter().flatten() {
                pending.insert((distance + 1, parent.clone()));
            }
        }
        graph.dyn_closures.insert(trait_name.clone(), closure);
    }
    for trait_name in graph.dyn_closures.keys() {
        graph
            .dyn_specializations
            .insert(trait_name.clone(), trait_name.clone());
    }
    for candidate in callables
        .iter()
        .filter_map(|candidate| candidate.owner.as_ref())
    {
        for slot in candidate
            .get("selected_methods")
            .and_then(serde_json::Value::as_array)
            .into_iter()
            .flatten()
        {
            let Some(trait_ref) = slot.get("trait_ref") else {
                continue;
            };
            let Some(trait_name) = named_trait_symbol(trait_ref) else {
                continue;
            };
            let Some(specialization) = canonical_trait_reference(trait_ref) else {
                continue;
            };
            graph
                .dyn_specializations
                .insert(specialization, trait_name.to_owned());
        }
    }
    let specializations = graph.dyn_specializations.clone();
    for (specialization, trait_name) in specializations {
        let Some(closure) = graph.dyn_closures.get(&trait_name) else {
            continue;
        };
        let mut effective = BTreeMap::<String, (usize, String, (String, BTreeSet<String>))>::new();
        for ((member_trait, method), kind) in &members {
            let Some(distance) = closure.get(member_trait) else {
                continue;
            };
            match effective.get(method) {
                Some((best, _, existing_kind)) if *best < *distance => {}
                Some((best, _, existing_kind)) if *best == *distance && existing_kind != kind => {
                    graph
                        .dyn_conflicts
                        .insert((specialization.clone(), method.clone()));
                }
                Some((best, _, _)) if *best > *distance => {
                    effective.insert(
                        method.clone(),
                        (*distance, member_trait.clone(), kind.clone()),
                    );
                    graph
                        .dyn_conflicts
                        .remove(&(specialization.clone(), method.clone()));
                }
                _ => {
                    effective.insert(
                        method.clone(),
                        (*distance, member_trait.clone(), kind.clone()),
                    );
                }
            }
        }
        for (method, (_, _, kind)) in effective {
            if graph
                .dyn_conflicts
                .contains(&(specialization.clone(), method.clone()))
            {
                continue;
            }
            let symbol = format!("dyn.{specialization}.{method}");
            graph
                .dyn_methods
                .insert((specialization.clone(), method.clone()), symbol.clone());
            graph.cott.entry(symbol.clone()).or_default();
            if kind.0 == "async" {
                graph.async_cott.insert(symbol.clone());
            }
            graph
                .dyn_dispatches
                .insert((specialization.clone(), method), symbol);
        }
    }
    for candidate in callables
        .iter()
        .filter(|candidate| impl_concrete(&candidate.kind).is_some())
    {
        let Some(owner) = &candidate.owner else {
            continue;
        };
        for slot in owner
            .get("selected_methods")
            .and_then(serde_json::Value::as_array)
            .into_iter()
            .flatten()
            .filter(|slot| {
                slot.get("trait_method") == candidate.declaration.get("trait_method")
                    && slot.get("selected") == candidate.declaration.get("selected")
            })
        {
            let Some(trait_ref) = slot.get("trait_ref") else {
                continue;
            };
            let Some(case_trait) = named_trait_symbol(trait_ref) else {
                continue;
            };
            let Some(case_specialization) = canonical_trait_reference(trait_ref) else {
                continue;
            };
            let Some((member_trait, method)) = slot
                .get("trait_method")
                .and_then(serde_json::Value::as_str)
                .and_then(trait_method_key)
            else {
                continue;
            };
            if !graph
                .dyn_closures
                .get(case_trait)
                .is_some_and(|closure| closure.contains_key(member_trait))
            {
                continue;
            }
            let Some(symbol) = graph
                .dyn_dispatches
                .get(&(case_specialization.clone(), method.to_owned()))
                .cloned()
            else {
                continue;
            };
            let expected_kind = if graph.async_cott.contains(&symbol) {
                "async"
            } else {
                "sync"
            };
            if slot
                .get("callable_kind")
                .and_then(serde_json::Value::as_str)
                != Some(expected_kind)
            {
                graph.errors.insert(format!(
                    "Dyn trait method `{case_trait}.{method}` has inconsistent callable kinds"
                ));
                continue;
            }
            graph
                .cott
                .entry(symbol)
                .or_default()
                .extend(declaration_effects(&candidate.declaration));
        }
    }
}

fn collect_dyn_imports(statement: &ast::Stmt, graph: &mut EffectGraph) {
    match statement {
        ast::Stmt::Import(import) => {
            for alias in &import.names {
                let Some(binding) = alias.asname.as_ref() else {
                    continue;
                };
                let module = alias.name.as_str();
                if graph
                    .dyn_closures
                    .keys()
                    .any(|trait_name| trait_name.starts_with(&format!("{module}.")))
                {
                    graph
                        .dyn_aliases
                        .insert(binding.as_str().to_owned(), module.to_owned());
                }
            }
        }
        ast::Stmt::ImportFrom(import) => {
            let Some(module) = import.module.as_ref().map(|module| module.as_str()) else {
                return;
            };
            for alias in &import.names {
                let imported = alias.name.as_str();
                let binding = alias.asname.as_ref().map_or(imported, |name| name.as_str());
                let symbol = format!("{module}.{imported}");
                if graph.dyn_closures.contains_key(&symbol)
                    || graph
                        .dyn_closures
                        .keys()
                        .any(|trait_name| trait_name.starts_with(&format!("{symbol}.")))
                {
                    graph.dyn_aliases.insert(binding.to_owned(), symbol);
                }
            }
        }
        _ => {}
    }
}

fn collect_effect_imports(statement: &ast::Stmt, graph: &mut EffectGraph) {
    match statement {
        ast::Stmt::Import(import) => {
            for alias in &import.names {
                let module = alias.name.as_str();
                if let Some(name) = &alias.asname {
                    graph
                        .modules
                        .insert(name.as_str().to_owned(), module.to_owned());
                } else {
                    let root = module.split('.').next().unwrap_or(module);
                    graph.module_roots.insert(root.to_owned());
                    if !graph
                        .cott
                        .keys()
                        .any(|symbol| symbol.starts_with(&format!("{module}.")))
                    {
                        graph.leaves.insert(root.to_owned());
                    }
                }
            }
        }
        ast::Stmt::ImportFrom(import) => {
            let Some(module) = import.module.as_ref().map(|module| module.as_str()) else {
                return;
            };
            for alias in &import.names {
                let imported = alias.name.as_str();
                let binding = alias.asname.as_ref().map_or(imported, |name| name.as_str());
                let symbol = format!("{module}.{imported}");
                if graph.cott.contains_key(&symbol) {
                    graph.imported.insert(binding.to_owned(), symbol);
                } else {
                    let child_module = format!("{module}.{imported}");
                    if graph
                        .cott
                        .keys()
                        .any(|symbol| symbol.starts_with(&format!("{child_module}.")))
                    {
                        graph.modules.insert(binding.to_owned(), child_module);
                    }
                    if !graph.modules.contains_key(binding)
                        || imported.chars().next().is_some_and(char::is_uppercase)
                    {
                        graph.leaves.insert(binding.to_owned());
                    }
                }
            }
        }
        _ => {}
    }
}

fn inspect_effect_function(
    name: &str,
    async_function: bool,
    arguments: &ast::Arguments,
    body: &[ast::Stmt],
    graph: &mut EffectGraph,
) {
    let Some(mut local) = graph.local.get(name).cloned() else {
        return;
    };
    if name == graph.target_function {
        local.factory_parameters = graph.factory_parameters.clone();
    }
    graph.async_function = async_function;
    inspect_effect_arguments(arguments, &mut local, graph);
    for statement in body {
        inspect_effect_statement(statement, &mut local, graph);
    }
    graph.async_function = false;
    graph.local.insert(name.to_owned(), local);
}

fn inspect_effect_binding(name: &str, _local: &mut LocalEffects, graph: &mut EffectGraph) {
    if graph.local.contains_key(name) {
        graph
            .errors
            .insert(format!("helper `{name}` must not be shadowed"));
    } else if let Some(symbol) = graph.imported.get(name) {
        graph
            .errors
            .insert(format!("Cott callable `{symbol}` must not be shadowed"));
    } else if let Some(module) = graph.modules.get(name) {
        graph
            .errors
            .insert(format!("Cott facade `{module}` must not be shadowed"));
    }
}

fn inspect_effect_arguments(
    arguments: &ast::Arguments,
    local: &mut LocalEffects,
    graph: &mut EffectGraph,
) {
    for argument in arguments
        .posonlyargs
        .iter()
        .chain(&arguments.args)
        .chain(&arguments.kwonlyargs)
    {
        let name = argument.def.arg.as_str();
        inspect_effect_binding(name, local, graph);
        if graph.impl_concrete.as_deref().is_some_and(|concrete| {
            argument
                .def
                .annotation
                .as_deref()
                .and_then(expression_dotted)
                .as_deref()
                == Some(concrete)
        }) {
            local.impl_receivers.insert(name.to_owned());
        }
        if let Some(annotation) = argument
            .def
            .annotation
            .as_deref()
            .filter(|annotation| is_dyn_annotation(annotation))
        {
            if let Some(trait_name) = dyn_annotation_trait(annotation, graph) {
                local.dyn_receivers.insert(name.to_owned(), trait_name);
            } else {
                graph.errors.insert(format!(
                    "Dyn receiver `{name}` must name an exact canonical trait"
                ));
            }
        }
        if !graph.leaves.contains(name) {
            local.parameters.insert(name.to_owned());
        }
    }
    for argument in [&arguments.vararg, &arguments.kwarg].into_iter().flatten() {
        let name = argument.arg.as_str();
        inspect_effect_binding(name, local, graph);
        if !graph.leaves.contains(name) {
            local.parameters.insert(name.to_owned());
        }
    }
}
fn inherit_impl_receiver(
    target: &ast::Expr,
    value: &ast::Expr,
    local: &mut LocalEffects,
    graph: &mut EffectGraph,
) {
    if let (Some(target), Some(value)) = (expression_name(target), expression_name(value)) {
        if let Some(trait_name) = local.dyn_receivers.get(value).cloned() {
            local.dyn_receivers.insert(target.to_owned(), trait_name);
        } else {
            local.dyn_receivers.remove(target);
        }
    } else {
        clear_dyn_receivers(target, local);
    }
    match (expression_name(target), expression_name(value)) {
        (Some(target), Some(value)) => {
            if local.impl_receivers.contains(value) {
                local.impl_receivers.insert(target.to_owned());
            } else {
                local.impl_receivers.remove(target);
            }
        }
        (None, _) if sequence_elements(target).is_some() && sequence_elements(value).is_some() => {
            let targets = sequence_elements(target).expect("checked sequence target");
            let values = sequence_elements(value).expect("checked sequence value");
            if targets.len() == values.len() {
                for (target, value) in targets.iter().zip(values) {
                    inherit_impl_receiver(target, value, local, graph);
                }
                return;
            }
            clear_impl_receivers(target, local);
            if expression_contains_impl_receiver(value, local) {
                graph.errors.insert(
                    "receiver alias containing a concrete implementation receiver is not statically analyzable"
                        .to_owned(),
                );
            }
        }
        _ => {
            clear_impl_receivers(target, local);
            if expression_contains_impl_receiver(value, local) {
                graph.errors.insert(
                    "receiver alias containing a concrete implementation receiver is not statically analyzable"
                        .to_owned(),
                );
            }
        }
    }
}

fn sequence_elements(expression: &ast::Expr) -> Option<&[ast::Expr]> {
    match expression {
        ast::Expr::List(list) => Some(&list.elts),
        ast::Expr::Tuple(tuple) => Some(&tuple.elts),
        _ => None,
    }
}

fn clear_impl_receivers(expression: &ast::Expr, local: &mut LocalEffects) {
    match expression {
        ast::Expr::Name(name) => {
            local.impl_receivers.remove(name.id.as_str());
        }
        ast::Expr::List(list) => {
            for element in &list.elts {
                clear_impl_receivers(element, local);
            }
        }
        ast::Expr::Tuple(tuple) => {
            for element in &tuple.elts {
                clear_impl_receivers(element, local);
            }
        }
        ast::Expr::Starred(starred) => clear_impl_receivers(&starred.value, local),
        _ => {}
    }
}
fn clear_dyn_receivers(expression: &ast::Expr, local: &mut LocalEffects) {
    match expression {
        ast::Expr::Name(name) => {
            local.dyn_receivers.remove(name.id.as_str());
        }
        ast::Expr::List(list) => {
            for element in &list.elts {
                clear_dyn_receivers(element, local);
            }
        }
        ast::Expr::Tuple(tuple) => {
            for element in &tuple.elts {
                clear_dyn_receivers(element, local);
            }
        }
        ast::Expr::Starred(starred) => clear_dyn_receivers(&starred.value, local),
        _ => {}
    }
}

fn expression_contains_impl_receiver(expression: &ast::Expr, local: &LocalEffects) -> bool {
    match expression {
        ast::Expr::Name(name) => local.impl_receivers.contains(name.id.as_str()),
        ast::Expr::Constant(_) => false,
        ast::Expr::BoolOp(value) => value
            .values
            .iter()
            .any(|value| expression_contains_impl_receiver(value, local)),
        ast::Expr::NamedExpr(value) => expression_contains_impl_receiver(&value.value, local),
        ast::Expr::BinOp(value) => {
            expression_contains_impl_receiver(&value.left, local)
                || expression_contains_impl_receiver(&value.right, local)
        }
        ast::Expr::UnaryOp(value) => expression_contains_impl_receiver(&value.operand, local),
        ast::Expr::IfExp(value) => {
            expression_contains_impl_receiver(&value.test, local)
                || expression_contains_impl_receiver(&value.body, local)
                || expression_contains_impl_receiver(&value.orelse, local)
        }
        ast::Expr::Dict(value) => value
            .keys
            .iter()
            .flatten()
            .chain(value.values.iter())
            .any(|value| expression_contains_impl_receiver(value, local)),
        ast::Expr::Set(value) => value
            .elts
            .iter()
            .any(|value| expression_contains_impl_receiver(value, local)),
        ast::Expr::List(value) => value
            .elts
            .iter()
            .any(|value| expression_contains_impl_receiver(value, local)),
        ast::Expr::Tuple(value) => value
            .elts
            .iter()
            .any(|value| expression_contains_impl_receiver(value, local)),
        ast::Expr::Compare(value) => {
            expression_contains_impl_receiver(&value.left, local)
                || value
                    .comparators
                    .iter()
                    .any(|value| expression_contains_impl_receiver(value, local))
        }
        ast::Expr::Call(value) => {
            expression_contains_impl_receiver(&value.func, local)
                || value
                    .args
                    .iter()
                    .chain(value.keywords.iter().map(|keyword| &keyword.value))
                    .any(|value| expression_contains_impl_receiver(value, local))
        }
        ast::Expr::FormattedValue(value) => {
            expression_contains_impl_receiver(&value.value, local)
                || value
                    .format_spec
                    .as_deref()
                    .is_some_and(|value| expression_contains_impl_receiver(value, local))
        }
        ast::Expr::JoinedStr(value) => value
            .values
            .iter()
            .any(|value| expression_contains_impl_receiver(value, local)),
        ast::Expr::Attribute(value) => expression_contains_impl_receiver(&value.value, local),
        ast::Expr::Subscript(value) => {
            expression_contains_impl_receiver(&value.value, local)
                || expression_contains_impl_receiver(&value.slice, local)
        }
        ast::Expr::Starred(value) => expression_contains_impl_receiver(&value.value, local),
        ast::Expr::ListComp(value) => {
            expression_contains_impl_receiver(&value.elt, local)
                || comprehensions_contain_impl_receiver(&value.generators, local)
        }
        ast::Expr::SetComp(value) => {
            expression_contains_impl_receiver(&value.elt, local)
                || comprehensions_contain_impl_receiver(&value.generators, local)
        }
        ast::Expr::DictComp(value) => {
            expression_contains_impl_receiver(&value.key, local)
                || expression_contains_impl_receiver(&value.value, local)
                || comprehensions_contain_impl_receiver(&value.generators, local)
        }
        ast::Expr::GeneratorExp(value) => {
            expression_contains_impl_receiver(&value.elt, local)
                || comprehensions_contain_impl_receiver(&value.generators, local)
        }
        ast::Expr::Lambda(value) => {
            value
                .args
                .posonlyargs
                .iter()
                .chain(&value.args.args)
                .chain(&value.args.kwonlyargs)
                .filter_map(|argument| argument.default.as_deref())
                .any(|value| expression_contains_impl_receiver(value, local))
                || expression_contains_impl_receiver(&value.body, local)
        }
        ast::Expr::Await(value) => expression_contains_impl_receiver(&value.value, local),
        ast::Expr::Yield(value) => value
            .value
            .as_deref()
            .is_some_and(|value| expression_contains_impl_receiver(value, local)),
        ast::Expr::YieldFrom(value) => expression_contains_impl_receiver(&value.value, local),
        ast::Expr::Slice(value) => [&value.lower, &value.upper, &value.step]
            .into_iter()
            .flatten()
            .any(|value| expression_contains_impl_receiver(value, local)),
    }
}

fn comprehensions_contain_impl_receiver(
    comprehensions: &[ast::Comprehension],
    local: &LocalEffects,
) -> bool {
    comprehensions.iter().any(|comprehension| {
        expression_contains_impl_receiver(&comprehension.iter, local)
            || comprehension
                .ifs
                .iter()
                .any(|value| expression_contains_impl_receiver(value, local))
    })
}

fn inspect_effect_statement(
    statement: &ast::Stmt,
    local: &mut LocalEffects,
    graph: &mut EffectGraph,
) {
    match statement {
        ast::Stmt::Return(statement) => {
            if let Some(value) = &statement.value {
                inspect_effect_expression(value, false, local, graph);
            }
        }
        ast::Stmt::Delete(statement) => {
            for target in &statement.targets {
                inspect_effect_target(target, local, graph);
            }
        }
        ast::Stmt::Assign(statement) => {
            for target in &statement.targets {
                inspect_effect_target(target, local, graph);
            }
            inspect_effect_expression(&statement.value, false, local, graph);
            for target in &statement.targets {
                inherit_impl_receiver(target, &statement.value, local, graph);
            }
        }
        ast::Stmt::AugAssign(statement) => {
            inspect_effect_target(&statement.target, local, graph);
            inspect_effect_expression(&statement.value, false, local, graph);
        }
        ast::Stmt::AnnAssign(statement) => {
            inspect_effect_target(&statement.target, local, graph);
            if let Some(value) = &statement.value {
                inspect_effect_expression(value, false, local, graph);
                inherit_impl_receiver(&statement.target, value, local, graph);
            }
        }
        ast::Stmt::For(statement) => {
            inspect_effect_target(&statement.target, local, graph);
            inspect_effect_expression(&statement.iter, false, local, graph);
            inspect_effect_statements(&statement.body, local, graph);
            inspect_effect_statements(&statement.orelse, local, graph);
        }
        ast::Stmt::While(statement) => {
            inspect_effect_expression(&statement.test, false, local, graph);
            inspect_effect_statements(&statement.body, local, graph);
            inspect_effect_statements(&statement.orelse, local, graph);
        }
        ast::Stmt::If(statement) => {
            inspect_effect_expression(&statement.test, false, local, graph);
            inspect_effect_statements(&statement.body, local, graph);
            inspect_effect_statements(&statement.orelse, local, graph);
        }
        ast::Stmt::Expr(statement) => {
            inspect_effect_expression(&statement.value, false, local, graph)
        }
        ast::Stmt::Pass(_) | ast::Stmt::Break(_) | ast::Stmt::Continue(_) => {}
        ast::Stmt::With(statement) => {
            inspect_effect_with(&statement.items, &statement.body, false, local, graph)
        }
        ast::Stmt::AsyncWith(statement) => {
            inspect_effect_with(&statement.items, &statement.body, true, local, graph)
        }
        ast::Stmt::Match(statement) => {
            inspect_effect_expression(&statement.subject, false, local, graph);
            for case in &statement.cases {
                if let Some(guard) = &case.guard {
                    inspect_effect_expression(guard, false, local, graph);
                }
                inspect_effect_statements(&case.body, local, graph);
            }
        }
        ast::Stmt::Raise(statement) => {
            for value in [&statement.exc, &statement.cause].into_iter().flatten() {
                inspect_effect_expression(value, false, local, graph);
            }
        }
        ast::Stmt::Try(statement) => inspect_effect_try(
            &statement.body,
            &statement.handlers,
            &statement.orelse,
            &statement.finalbody,
            local,
            graph,
        ),
        ast::Stmt::TryStar(statement) => inspect_effect_try(
            &statement.body,
            &statement.handlers,
            &statement.orelse,
            &statement.finalbody,
            local,
            graph,
        ),
        ast::Stmt::Assert(statement) => {
            inspect_effect_expression(&statement.test, false, local, graph);
            if let Some(message) = &statement.msg {
                inspect_effect_expression(message, false, local, graph);
            }
        }
        ast::Stmt::FunctionDef(_) | ast::Stmt::AsyncFunctionDef(_) | ast::Stmt::ClassDef(_) => {
            graph
                .errors
                .insert("nested definitions are not allowed".to_owned());
        }
        ast::Stmt::Import(_) | ast::Stmt::ImportFrom(_) => {
            graph
                .errors
                .insert("nested imports are not allowed".to_owned());
        }
        _ => {
            graph
                .errors
                .insert("effect analysis does not support this Python statement".to_owned());
        }
    }
}

fn inspect_effect_statements(
    statements: &[ast::Stmt],
    local: &mut LocalEffects,
    graph: &mut EffectGraph,
) {
    for statement in statements {
        inspect_effect_statement(statement, local, graph);
    }
}

fn inspect_effect_with(
    items: &[ast::WithItem],
    body: &[ast::Stmt],
    async_with: bool,
    local: &mut LocalEffects,
    graph: &mut EffectGraph,
) {
    let mut task_groups = BTreeSet::new();
    for item in items {
        if is_task_group_constructor(&item.context_expr) {
            let Some(name) = async_with
                .then(|| {
                    item.optional_vars
                        .as_ref()
                        .and_then(|expression| expression_name(expression.as_ref()))
                })
                .flatten()
            else {
                graph.errors.insert(
                    "TaskGroup must be used as `async with TaskGroup() as <name>`".to_owned(),
                );
                continue;
            };
            if !local.task_groups.insert(name.to_owned()) {
                graph
                    .errors
                    .insert(format!("TaskGroup binding `{name}` must not be shadowed"));
            } else {
                task_groups.insert(name.to_owned());
            }
            continue;
        }
        inspect_effect_expression(&item.context_expr, false, local, graph);
        if let Some(target) = &item.optional_vars {
            inspect_effect_target(target, local, graph);
        }
    }
    inspect_effect_statements(body, local, graph);
    for name in task_groups {
        local.task_groups.remove(&name);
    }
}

fn inspect_effect_try(
    body: &[ast::Stmt],
    handlers: &[ast::ExceptHandler],
    orelse: &[ast::Stmt],
    finalbody: &[ast::Stmt],
    local: &mut LocalEffects,
    graph: &mut EffectGraph,
) {
    inspect_effect_statements(body, local, graph);
    for handler in handlers {
        let ast::ExceptHandler::ExceptHandler(handler) = handler;
        if let Some(ty) = &handler.type_ {
            inspect_effect_expression(ty, false, local, graph);
        }
        if let Some(name) = &handler.name {
            inspect_effect_binding(name.as_str(), local, graph);
        }
        inspect_effect_statements(&handler.body, local, graph);
    }
    inspect_effect_statements(orelse, local, graph);
    inspect_effect_statements(finalbody, local, graph);
}

fn inspect_effect_target(
    expression: &ast::Expr,
    local: &mut LocalEffects,
    graph: &mut EffectGraph,
) {
    if let Some(name) = expression_name(expression) {
        if graph.local.contains_key(name) {
            graph
                .errors
                .insert(format!("helper `{name}` must not be rebound"));
        } else if let Some(symbol) = graph.imported.get(name) {
            graph
                .errors
                .insert(format!("Cott callable `{symbol}` must not be rebound"));
        } else if let Some(module) = graph.modules.get(name) {
            graph
                .errors
                .insert(format!("Cott facade `{module}` must not be rebound"));
        } else {
            local.assigned.insert(name.to_owned());
        }
    } else if let Some(symbol) = effect_cott_target(expression, graph)
        .or_else(|| effect_impl_self_target(expression, local, graph))
    {
        graph
            .errors
            .insert(format!("Cott callable `{symbol}` must not be rebound"));
    }
    inspect_effect_expression(expression, false, local, graph);
}

fn inspect_effect_expression(
    expression: &ast::Expr,
    callee: bool,
    local: &mut LocalEffects,
    graph: &mut EffectGraph,
) {
    inspect_effect_expression_with_await(expression, callee, false, local, graph);
}

fn inspect_effect_expression_with_await(
    expression: &ast::Expr,
    callee: bool,
    awaited: bool,
    local: &mut LocalEffects,
    graph: &mut EffectGraph,
) {
    if !callee {
        if is_concurrency_api_reference(expression) {
            graph.errors.insert(
                "asyncio concurrency APIs may only be used as exact structured calls".to_owned(),
            );
            return;
        }
        if is_dyn_value(expression, local) {
            graph.errors.insert(
                "Dyn value may only be used for an exact `.value.<method>(...)` invocation"
                    .to_owned(),
            );
            return;
        }
        if is_dyn_dispatch(expression, local) {
            graph.errors.insert(
                "Dyn method may only be used as an exact `.value.<method>(...)` invocation"
                    .to_owned(),
            );
            return;
        }
        if matches!(expression, ast::Expr::Attribute(attribute) if dyn_receiver_name(&attribute.value, local).is_some())
        {
            graph
                .errors
                .insert("Dyn method invocation must go through `.value`".to_owned());
            return;
        }
        if let Some(symbol) = effect_cott_target(expression, graph)
            .or_else(|| effect_impl_self_target(expression, local, graph))
        {
            graph.errors.insert(format!(
                "Cott callable `{symbol}` may only be used as an exact call"
            ));
            return;
        }
        if let Some(name) = expression_name(expression) {
            if graph.local.contains_key(name) {
                graph
                    .errors
                    .insert(format!("helper `{name}` may only be used as an exact call"));
                return;
            }
        }
    }
    match expression {
        ast::Expr::BoolOp(expression) => {
            for value in &expression.values {
                inspect_effect_expression(value, false, local, graph);
            }
        }
        ast::Expr::NamedExpr(expression) => {
            inspect_effect_target(&expression.target, local, graph);
            inspect_effect_expression(&expression.value, false, local, graph);
            inherit_impl_receiver(&expression.target, &expression.value, local, graph);
        }
        ast::Expr::BinOp(expression) => {
            inspect_effect_expression(&expression.left, false, local, graph);
            inspect_effect_expression(&expression.right, false, local, graph);
        }
        ast::Expr::UnaryOp(expression) => {
            inspect_effect_expression(&expression.operand, false, local, graph)
        }
        ast::Expr::IfExp(expression) => {
            inspect_effect_expression(&expression.test, false, local, graph);
            inspect_effect_expression(&expression.body, false, local, graph);
            inspect_effect_expression(&expression.orelse, false, local, graph);
        }
        ast::Expr::Dict(expression) => {
            for key in expression.keys.iter().flatten() {
                inspect_effect_expression(key, false, local, graph);
            }
            for value in &expression.values {
                inspect_effect_expression(value, false, local, graph);
            }
        }
        ast::Expr::Set(expression) => {
            for value in &expression.elts {
                inspect_effect_expression(value, false, local, graph);
            }
        }
        ast::Expr::List(expression) => {
            for value in &expression.elts {
                inspect_effect_expression(value, false, local, graph);
            }
        }
        ast::Expr::Tuple(expression) => {
            for value in &expression.elts {
                inspect_effect_expression(value, false, local, graph);
            }
        }
        ast::Expr::Compare(expression) => {
            inspect_effect_expression(&expression.left, false, local, graph);
            for value in &expression.comparators {
                inspect_effect_expression(value, false, local, graph);
            }
        }
        ast::Expr::Call(expression) => {
            if is_task_group_constructor_call(&expression.func) {
                graph.errors.insert(
                    "TaskGroup must be used as `async with TaskGroup() as <name>`".to_owned(),
                );
            }
            if is_detached_task_call(&expression.func, local) {
                graph
                    .errors
                    .insert("detached task APIs are not allowed".to_owned());
            }
            if is_gather_call(&expression.func) && !awaited {
                graph
                    .errors
                    .insert("asyncio.gather must be directly awaited".to_owned());
            }
            inspect_impl_receiver_call_base(&expression.func, local, graph);
            if is_dyn_constructor(&expression.func)
                && (!expression.args.is_empty()
                    || expression.keywords.len() != 2
                    || expression
                        .keywords
                        .iter()
                        .any(|keyword| keyword.arg.is_none())
                    || !["value", "trait"].into_iter().all(|name| {
                        expression
                            .keywords
                            .iter()
                            .any(|keyword| keyword.arg.as_deref() == Some(name))
                    }))
            {
                graph.errors.insert(
                    "Dyn must be constructed exactly as `Dyn(value=<concrete>, trait=<Trait>)`"
                        .to_owned(),
                );
            }
            let statically_resolved = if is_dyn_constructor(&expression.func) {
                true
            } else if matches!(&*expression.func, ast::Expr::Attribute(attribute) if dyn_receiver_name(&attribute.value, local).is_some())
            {
                graph
                    .errors
                    .insert("Dyn method invocation must go through `.value`".to_owned());
                false
            } else if let Some((receiver, method)) = dyn_dispatch_method(&expression.func, local) {
                let trait_ = local
                    .dyn_receivers
                    .get(receiver)
                    .expect("Dyn dispatch receiver was checked");
                if graph
                    .dyn_conflicts
                    .contains(&(trait_.trait_ref.clone(), method.to_owned()))
                {
                    graph.errors.insert(format!(
                        "Dyn trait `{}` has ambiguous inherited method `{method}`",
                        trait_.trait_ref
                    ));
                    false
                } else if let Some(symbol) = dyn_dispatch_symbol(&trait_.trait_ref, method, graph) {
                    record_effect_cott_call(&symbol, awaited, local, graph);
                    true
                } else {
                    graph.errors.insert(format!(
                        "Dyn trait `{}` has no method `{method}`",
                        trait_.trait_ref
                    ));
                    false
                }
            } else if let Some(name) = expression_name(&expression.func) {
                if graph.local.contains_key(name) {
                    if awaited {
                        graph
                            .errors
                            .insert(format!("synchronous helper `{name}` must not be awaited"));
                    }
                    local.local_calls.insert(name.to_owned());
                    true
                } else if let Some(symbol) = graph.imported.get(name).cloned() {
                    record_effect_cott_call(&symbol, awaited, local, graph);
                    true
                } else if (local.parameters.contains(name) || local.assigned.contains(name))
                    && !local.factory_parameters.contains(name)
                {
                    graph
                        .errors
                        .insert(format!("dynamic Cott call `{name}` is not allowed"));
                    false
                } else {
                    local.factory_parameters.contains(name)
                        || graph.leaves.contains(name)
                        || builtin_leaf(name)
                }
            } else if let Some(symbol) = effect_impl_self_target(&expression.func, local, graph) {
                record_effect_cott_call(&symbol, awaited, local, graph);
                true
            } else if let Some(symbol) = effect_cott_target(&expression.func, graph) {
                record_effect_cott_call(&symbol, awaited, local, graph);
                true
            } else if let Some(symbol) = cott_callable_origin(&expression.func, graph) {
                graph
                    .errors
                    .insert(format!("dynamic Cott call `{symbol}` is not allowed"));
                false
            } else {
                matches!(&*expression.func, ast::Expr::Attribute(_))
            };
            if !statically_resolved {
                inspect_effect_expression(&expression.func, false, local, graph);
                if expression_contains_impl_receiver(&expression.func, local)
                    || expression
                        .args
                        .iter()
                        .chain(expression.keywords.iter().map(|keyword| &keyword.value))
                        .any(|value| expression_contains_impl_receiver(value, local))
                {
                    graph.errors.insert(
                        "receiver call containing a concrete implementation receiver is not statically analyzable"
                            .to_owned(),
                    );
                }
            }
            for argument in &expression.args {
                inspect_effect_expression(argument, false, local, graph);
            }
            for keyword in &expression.keywords {
                inspect_effect_expression(&keyword.value, false, local, graph);
            }
        }
        ast::Expr::FormattedValue(expression) => {
            inspect_effect_expression(&expression.value, false, local, graph);
            if let Some(specification) = &expression.format_spec {
                inspect_effect_expression(specification, false, local, graph);
            }
        }
        ast::Expr::JoinedStr(expression) => {
            for value in &expression.values {
                inspect_effect_expression(value, false, local, graph);
            }
        }
        ast::Expr::Attribute(expression) => {
            inspect_effect_expression(&expression.value, false, local, graph);
        }
        ast::Expr::Subscript(expression) => {
            inspect_effect_expression(&expression.value, false, local, graph);
            inspect_effect_expression(&expression.slice, false, local, graph);
        }
        ast::Expr::Starred(expression) => {
            inspect_effect_expression(&expression.value, false, local, graph)
        }
        ast::Expr::ListComp(expression) => {
            inspect_effect_expression(&expression.elt, false, local, graph);
            inspect_effect_comprehensions(&expression.generators, local, graph);
        }
        ast::Expr::SetComp(expression) => {
            inspect_effect_expression(&expression.elt, false, local, graph);
            inspect_effect_comprehensions(&expression.generators, local, graph);
        }
        ast::Expr::DictComp(expression) => {
            inspect_effect_expression(&expression.key, false, local, graph);
            inspect_effect_expression(&expression.value, false, local, graph);
            inspect_effect_comprehensions(&expression.generators, local, graph);
        }
        ast::Expr::GeneratorExp(expression) => {
            inspect_effect_expression(&expression.elt, false, local, graph);
            inspect_effect_comprehensions(&expression.generators, local, graph);
        }
        ast::Expr::Lambda(expression) => {
            inspect_effect_arguments(&expression.args, local, graph);
            inspect_effect_expression(&expression.body, false, local, graph);
        }
        ast::Expr::Await(expression) => {
            inspect_effect_expression_with_await(&expression.value, false, true, local, graph)
        }
        ast::Expr::Yield(expression) => {
            if graph.async_function {
                graph
                    .errors
                    .insert("native async-generator functions are not allowed".to_owned());
            }
            if let Some(value) = &expression.value {
                inspect_effect_expression(value, false, local, graph);
            }
        }
        ast::Expr::YieldFrom(expression) => {
            if graph.async_function {
                graph
                    .errors
                    .insert("native async-generator functions are not allowed".to_owned());
            }
            inspect_effect_expression(&expression.value, false, local, graph)
        }
        ast::Expr::Slice(expression) => {
            for value in [&expression.lower, &expression.upper, &expression.step]
                .into_iter()
                .flatten()
            {
                inspect_effect_expression(value, false, local, graph);
            }
        }
        ast::Expr::Constant(_) | ast::Expr::Name(_) => {}
    }
}

fn expression_name(expression: &ast::Expr) -> Option<&str> {
    match expression {
        ast::Expr::Name(name) => Some(name.id.as_str()),
        _ => None,
    }
}

fn call_leaf_name(expression: &ast::Expr) -> Option<&str> {
    match expression {
        ast::Expr::Name(name) => Some(name.id.as_str()),
        ast::Expr::Attribute(attribute) => Some(attribute.attr.as_str()),
        _ => None,
    }
}

fn is_task_group_constructor(expression: &ast::Expr) -> bool {
    matches!(expression, ast::Expr::Call(call) if is_task_group_constructor_call(&call.func))
}

fn is_task_group_constructor_call(function: &ast::Expr) -> bool {
    call_leaf_name(function) == Some("TaskGroup")
}

fn is_gather_call(function: &ast::Expr) -> bool {
    call_leaf_name(function) == Some("gather")
}

fn is_detached_task_call(function: &ast::Expr, local: &LocalEffects) -> bool {
    match call_leaf_name(function) {
        Some("ensure_future") | Some("Task") => true,
        Some("create_task") => match function {
            ast::Expr::Attribute(attribute) => !expression_name(&attribute.value)
                .is_some_and(|name| local.task_groups.contains(name)),
            _ => true,
        },
        _ => false,
    }
}

fn is_concurrency_api_reference(expression: &ast::Expr) -> bool {
    matches!(
        call_leaf_name(expression),
        Some("create_task" | "ensure_future" | "Task" | "gather" | "TaskGroup")
    )
}

fn inspect_effect_comprehensions(
    comprehensions: &[ast::Comprehension],
    local: &mut LocalEffects,
    graph: &mut EffectGraph,
) {
    for comprehension in comprehensions {
        inspect_effect_target(&comprehension.target, local, graph);
        inspect_effect_expression(&comprehension.iter, false, local, graph);
        for condition in &comprehension.ifs {
            inspect_effect_expression(condition, false, local, graph);
        }
    }
}

fn expression_dotted(expression: &ast::Expr) -> Option<String> {
    match expression {
        ast::Expr::Name(name) => Some(name.id.as_str().to_owned()),
        ast::Expr::Attribute(attribute) => Some(format!(
            "{}.{}",
            expression_dotted(&attribute.value)?,
            attribute.attr
        )),
        _ => None,
    }
}
fn is_dyn_annotation(expression: &ast::Expr) -> bool {
    matches!(
        expression,
        ast::Expr::Subscript(subscript)
            if expression_dotted(&subscript.value).as_deref().is_some_and(|name| name == "Dyn" || name == "cott_runtime.Dyn")
    )
}

fn normalized_type_reference(expression: &ast::Expr) -> Option<String> {
    match expression {
        ast::Expr::Name(_) | ast::Expr::Attribute(_) => expression_dotted(expression),
        ast::Expr::Subscript(subscript) => Some(format!(
            "{}[{}]",
            normalized_type_reference(&subscript.value)?,
            normalized_type_reference(&subscript.slice)?
        )),
        ast::Expr::Tuple(tuple) => tuple
            .elts
            .iter()
            .map(normalized_type_reference)
            .collect::<Option<Vec<_>>>()
            .map(|values| values.join(",")),
        ast::Expr::Constant(constant) => match &constant.value {
            ast::Constant::Int(value) => {
                let value = value.to_string();
                (!value.starts_with('-')).then_some(value)
            }
            ast::Constant::Str(value) => serde_json::to_string(value).ok(),
            _ => None,
        },
        _ => None,
    }
}

fn trait_reference_origin(expression: &ast::Expr) -> Option<String> {
    match expression {
        ast::Expr::Subscript(subscript) => trait_reference_origin(&subscript.value),
        _ => expression_dotted(expression),
    }
}

fn canonical_dyn_trait_origin(origin: String, graph: &EffectGraph) -> Option<String> {
    if graph.dyn_closures.contains_key(&origin) {
        return Some(origin);
    }
    if let Some(trait_name) = graph.dyn_aliases.get(&origin) {
        return graph
            .dyn_closures
            .contains_key(trait_name)
            .then(|| trait_name.clone());
    }
    let (prefix, suffix) = origin.split_once('.')?;
    let module = graph.dyn_aliases.get(prefix)?;
    let trait_name = format!("{module}.{suffix}");
    graph
        .dyn_closures
        .contains_key(&trait_name)
        .then_some(trait_name)
}

fn dyn_annotation_trait(expression: &ast::Expr, graph: &EffectGraph) -> Option<DynReceiver> {
    let ast::Expr::Subscript(subscript) = expression else {
        return None;
    };
    let origin = trait_reference_origin(&subscript.slice)?;
    let reference = normalized_type_reference(&subscript.slice)?;
    let trait_symbol = canonical_dyn_trait_origin(origin.clone(), graph)?;
    Some(DynReceiver {
        trait_ref: format!(
            "{trait_symbol}{}",
            reference
                .strip_prefix(&origin)
                .expect("normalized Dyn trait reference has its origin")
        ),
    })
}

fn dyn_receiver_name<'a>(expression: &'a ast::Expr, local: &LocalEffects) -> Option<&'a str> {
    expression_name(expression).filter(|name| local.dyn_receivers.contains_key(*name))
}

fn is_dyn_value(expression: &ast::Expr, local: &LocalEffects) -> bool {
    matches!(
        expression,
        ast::Expr::Attribute(attribute)
            if attribute.attr.as_str() == "value"
                && dyn_receiver_name(&attribute.value, local).is_some()
    )
}

fn is_dyn_dispatch(expression: &ast::Expr, local: &LocalEffects) -> bool {
    matches!(
        expression,
        ast::Expr::Attribute(attribute) if is_dyn_value(&attribute.value, local)
    )
}

fn dyn_dispatch_method<'a>(
    expression: &'a ast::Expr,
    local: &LocalEffects,
) -> Option<(&'a str, &'a str)> {
    let ast::Expr::Attribute(method) = expression else {
        return None;
    };
    let ast::Expr::Attribute(value) = &*method.value else {
        return None;
    };
    (value.attr.as_str() == "value").then_some((
        dyn_receiver_name(&value.value, local)?,
        method.attr.as_str(),
    ))
}

fn dyn_dispatch_symbol(trait_name: &str, method: &str, graph: &EffectGraph) -> Option<String> {
    graph
        .dyn_dispatches
        .get(&(trait_name.to_owned(), method.to_owned()))
        .cloned()
}
fn is_dyn_constructor(expression: &ast::Expr) -> bool {
    expression_dotted(expression)
        .as_deref()
        .is_some_and(|name| name == "Dyn" || name == "cott_runtime.Dyn")
}

fn inspect_impl_receiver_call_base(
    expression: &ast::Expr,
    local: &mut LocalEffects,
    graph: &mut EffectGraph,
) {
    if is_dyn_dispatch(expression, local) {
        return;
    }
    let ast::Expr::Attribute(attribute) = expression else {
        return;
    };
    if expression_name(&attribute.value).is_none() {
        inspect_effect_expression(&attribute.value, false, local, graph);
        if impl_receiver_name(&attribute.value, local).is_none()
            && expression_contains_impl_receiver(&attribute.value, local)
        {
            graph.errors.insert(
                "receiver call containing a concrete implementation receiver is not statically analyzable"
                    .to_owned(),
            );
        }
    }
}

fn impl_receiver_name<'a>(expression: &'a ast::Expr, local: &LocalEffects) -> Option<&'a str> {
    match expression {
        ast::Expr::Name(name) => local
            .impl_receivers
            .contains(name.id.as_str())
            .then_some(name.id.as_str()),
        ast::Expr::NamedExpr(named) => {
            expression_name(&named.target).filter(|name| local.impl_receivers.contains(*name))
        }
        _ => None,
    }
}

fn effect_impl_self_target(
    expression: &ast::Expr,
    local: &LocalEffects,
    graph: &EffectGraph,
) -> Option<String> {
    let ast::Expr::Attribute(attribute) = expression else {
        return None;
    };
    impl_receiver_name(&attribute.value, local)
        .and_then(|_| graph.impl_methods.get(attribute.attr.as_str()))
        .cloned()
}

fn effect_cott_target(expression: &ast::Expr, graph: &EffectGraph) -> Option<String> {
    let dotted = expression_dotted(expression)?;
    if let Some(symbol) = graph.imported.get(&dotted) {
        return Some(symbol.clone());
    }
    let mut segments = dotted.split('.');
    let first = segments.next()?;
    let rest = segments.collect::<Vec<_>>();
    let imported_facade = graph.modules.contains_key(first) || graph.module_roots.contains(first);
    let resolved = graph
        .modules
        .get(first)
        .map(|module| {
            std::iter::once(module.as_str())
                .chain(rest)
                .collect::<Vec<_>>()
                .join(".")
        })
        .unwrap_or(dotted);
    (imported_facade && graph.cott.contains_key(&resolved)).then_some(resolved)
}

fn cott_callable_origin(expression: &ast::Expr, graph: &EffectGraph) -> Option<String> {
    effect_cott_target(expression, graph).or_else(|| match expression {
        ast::Expr::Attribute(attribute) => cott_callable_origin(&attribute.value, graph),
        ast::Expr::Subscript(subscript) => cott_callable_origin(&subscript.value, graph),
        ast::Expr::Starred(starred) => cott_callable_origin(&starred.value, graph),
        _ => None,
    })
}

fn builtin_leaf(name: &str) -> bool {
    matches!(
        name,
        "abs"
            | "aiter"
            | "all"
            | "anext"
            | "any"
            | "ascii"
            | "bin"
            | "bool"
            | "breakpoint"
            | "bytearray"
            | "bytes"
            | "callable"
            | "chr"
            | "classmethod"
            | "complex"
            | "delattr"
            | "dict"
            | "dir"
            | "divmod"
            | "enumerate"
            | "filter"
            | "float"
            | "format"
            | "frozenset"
            | "getattr"
            | "globals"
            | "hasattr"
            | "hash"
            | "help"
            | "hex"
            | "id"
            | "input"
            | "int"
            | "isinstance"
            | "issubclass"
            | "iter"
            | "len"
            | "list"
            | "locals"
            | "map"
            | "max"
            | "memoryview"
            | "min"
            | "next"
            | "object"
            | "oct"
            | "open"
            | "ord"
            | "pow"
            | "print"
            | "property"
            | "range"
            | "repr"
            | "reversed"
            | "round"
            | "set"
            | "setattr"
            | "slice"
            | "sorted"
            | "staticmethod"
            | "str"
            | "sum"
            | "super"
            | "tuple"
            | "type"
            | "vars"
            | "zip"
            | "BaseException"
            | "BaseExceptionGroup"
            | "BlockingIOError"
            | "BrokenPipeError"
            | "BufferError"
            | "BytesWarning"
            | "ChildProcessError"
            | "ConnectionAbortedError"
            | "ConnectionError"
            | "ConnectionRefusedError"
            | "ConnectionResetError"
            | "DeprecationWarning"
            | "EOFError"
            | "EncodingWarning"
            | "EnvironmentError"
            | "Exception"
            | "ExceptionGroup"
            | "FileExistsError"
            | "FileNotFoundError"
            | "FloatingPointError"
            | "FutureWarning"
            | "GeneratorExit"
            | "IOError"
            | "ImportError"
            | "ImportWarning"
            | "IndentationError"
            | "IndexError"
            | "InterruptedError"
            | "IsADirectoryError"
            | "KeyError"
            | "KeyboardInterrupt"
            | "LookupError"
            | "MemoryError"
            | "ModuleNotFoundError"
            | "NameError"
            | "NotADirectoryError"
            | "OSError"
            | "OverflowError"
            | "PendingDeprecationWarning"
            | "PermissionError"
            | "ProcessLookupError"
            | "RecursionError"
            | "ReferenceError"
            | "ResourceWarning"
            | "RuntimeError"
            | "RuntimeWarning"
            | "StopAsyncIteration"
            | "StopIteration"
            | "SyntaxError"
            | "SyntaxWarning"
            | "SystemError"
            | "SystemExit"
            | "TabError"
            | "TimeoutError"
            | "TypeError"
            | "UnboundLocalError"
            | "UnicodeDecodeError"
            | "UnicodeEncodeError"
            | "UnicodeError"
            | "UnicodeTranslateError"
            | "UnicodeWarning"
            | "UserWarning"
            | "ValueError"
            | "Warning"
            | "ZeroDivisionError"
    )
}

fn effect_union(
    function: &str,
    graph: &EffectGraph,
    visiting: &mut BTreeSet<String>,
) -> BTreeMap<String, Vec<String>> {
    if !visiting.insert(function.to_owned()) {
        return BTreeMap::new();
    }
    let mut effects = BTreeMap::new();
    if let Some(local) = graph.local.get(function) {
        for symbol in &local.cott_calls {
            if let Some(callee_effects) = graph.cott.get(symbol) {
                for effect in callee_effects {
                    effects.insert(effect.clone(), vec![function.to_owned(), symbol.clone()]);
                }
            }
        }
        for callee in &local.local_calls {
            for (effect, mut path) in effect_union(callee, graph, visiting) {
                path.insert(0, function.to_owned());
                effects.entry(effect).or_insert(path);
            }
        }
    }
    visiting.remove(function);
    effects
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
        let (async_definition, signature) = if line.starts_with("async def ") {
            (true, collect_signature(&lines, line_number))
        } else if line.starts_with("def ") {
            (false, collect_signature(&lines, line_number))
        } else {
            continue;
        };
        let signature = signature.strip_prefix("async ").unwrap_or(&signature);
        let Some((name, parameters)) = parse_signature(signature, add_error) else {
            continue;
        };
        if name == expected_function {
            if async_definition != is_async_function(&callable.kind) {
                add_error(format!(
                    "function '{expected_function}' must be an exact top-level {}",
                    if is_async_function(&callable.kind) {
                        "async def"
                    } else {
                        "def"
                    }
                ));
            } else {
                expected_count += 1;
            }
            let parameters = if let Some(concrete) = impl_concrete(&callable.kind) {
                match parameters.split_first() {
                    Some((self_parameter, parameters))
                        if self_parameter.name == "self"
                            && !self_parameter.keyword_only
                            && self_parameter.annotation == concrete =>
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
            if async_definition {
                add_error(format!("helper function '{name}' must be synchronous"));
            }
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
            || line.starts_with("async def ")
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
                if module == "cott_runtime" && item != "cott_runtime" {
                    add_error("cott_runtime must not be imported with an alias".to_owned());
                }
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
            if module.split('.').next() == Some("asyncio") {
                inspect_asyncio_concurrency_imports(imported, add_error);
            }
            if module == "cott_runtime" {
                inspect_dyn_import(imported, add_error);
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

fn inspect_dyn_import(imported: &str, add_error: &mut impl FnMut(String)) {
    for item in imported.split(',').map(str::trim) {
        if item.split_whitespace().next() == Some("Dyn") && item != "Dyn" {
            add_error("Dyn must be imported from cott_runtime without an alias".to_owned());
        }
    }
}

fn inspect_asyncio_concurrency_imports(imported: &str, add_error: &mut impl FnMut(String)) {
    for item in imported.split(',').map(str::trim) {
        let mut words = item.split_whitespace();
        let Some(name) = words.next() else {
            continue;
        };
        if words.next().is_none() {
            continue;
        }
        match name {
            "create_task" | "ensure_future" | "Task" => {
                add_error("detached task APIs are not allowed".to_owned())
            }
            "gather" | "TaskGroup" => {
                add_error("asyncio concurrency imports must not be aliased".to_owned())
            }
            _ => {}
        }
    }
}

fn impl_concrete_import_source(callable: &PythonCallable) -> Option<(&str, &str)> {
    let concrete = impl_concrete(&callable.kind)?;
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
