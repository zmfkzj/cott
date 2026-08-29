use std::collections::{BTreeMap, BTreeSet, HashSet};
use std::fmt::Write as _;
use std::path::{Path, PathBuf};

use serde_json::{Value, json};

use crate::binding::{BindingOwner, ResolvedBinding};
use crate::contract_test::derive_strategies;
use crate::hash::sha256_hex;
use crate::ir::CanonicalIr;
use crate::manifest::{ProjectConfig, RuntimeValidation};
use crate::provenance::{
    GENERATION_SCHEMA_VERSION, GenerationCompatibility, GenerationRecord, GenerationSnapshot,
    RUNTIME_ABI_VERSION, SemanticCoverage, SourceSpan, UnresolvedKind, UnresolvedRecord,
};
use crate::python::artifact_plan::{PythonArtifactPlan, PythonCallableKind};
use crate::python_runtime::render_runtime;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Emission {
    pub files: BTreeMap<PathBuf, Vec<u8>>,
}
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EmitDiagnostic {
    pub path: PathBuf,
    pub message: String,
}

pub fn emit(
    config: &ProjectConfig,
    plan: &PythonArtifactPlan,
    ir: &CanonicalIr,
    bindings: &[ResolvedBinding],
) -> Result<Emission, Vec<EmitDiagnostic>> {
    let (target_machine, target_platform) = target_python_identity();
    let mut diagnostics = Vec::new();
    if target_machine == "unknown" {
        return Err(vec![diag(
            "generation.json",
            "unsupported Python target architecture",
        )]);
    }
    let mut modules = BTreeMap::<String, _>::new();
    for module in plan.modules() {
        if modules.insert(module.module.clone(), module).is_some() {
            diagnostics.push(diag(
                module_path(&module.module),
                "duplicate canonical module",
            ));
        }
        let segments = module.module.split('.').collect::<Vec<_>>();
        if segments.iter().any(|segment| !valid_python_name(segment))
            || matches!(segments.first(), Some(&"cott_runtime" | &"_cott_impl"))
            || segments
                .last()
                .is_some_and(|segment| segment.ends_with("_types"))
        {
            diagnostics.push(diag(
                module_path(&module.module),
                "module name is reserved or is not a valid Python target name",
            ));
        }
    }
    if modules.is_empty() {
        diagnostics.push(diag("python", "canonical plan has no modules"));
    }
    let mut prefixes = HashSet::new();
    for name in modules.keys() {
        let parts: Vec<_> = name.split('.').collect();
        for n in 1..parts.len() {
            prefixes.insert(parts[..n].join("."));
        }
    }
    for name in modules.keys() {
        if prefixes.contains(name) {
            diagnostics.push(diag(
                module_path(name),
                "module is also a package prefix; Python facade paths would collide",
            ));
        }
    }
    let mut declarations = BTreeMap::<String, String>::new();
    for module in modules.values() {
        for declaration in &module.declarations {
            let Some(object) = declaration.as_object() else {
                diagnostics.push(diag(
                    module_path(&module.module),
                    "declaration must be an object",
                ));
                continue;
            };
            let kind = required_string(object, "kind", &module.module, &mut diagnostics);
            let name = required_string(object, "name", &module.module, &mut diagnostics);
            if let (Some(kind), Some(name)) = (kind, name) {
                if declarations.insert(name, kind).is_some() {
                    diagnostics.push(diag(
                        module_path(&module.module),
                        "duplicate declaration identity",
                    ));
                }
            }
            validate_declaration(&module.module, object, &mut diagnostics);
        }
    }
    let generic_parameters = modules
        .values()
        .flat_map(|module| &module.declarations)
        .filter_map(Value::as_object)
        .filter_map(|declaration| {
            Some((
                declaration.get("name")?.as_str()?.to_owned(),
                declaration.get("generics")?.as_array()?.clone(),
            ))
        })
        .collect::<BTreeMap<_, _>>();
    validate_external_types(
        &modules,
        &declarations,
        &config.python.external_types,
        &mut diagnostics,
    );
    for module in modules.values() {
        let mut projected = BTreeSet::new();
        for declaration in &module.declarations {
            let Some(object) = declaration.as_object() else {
                continue;
            };
            if !object
                .get("public")
                .and_then(Value::as_bool)
                .unwrap_or(false)
            {
                continue;
            }
            let Some(name) = object.get("name").and_then(Value::as_str).map(local_name) else {
                continue;
            };
            if !valid_python_name(name) || python_support_names().contains(&name) {
                diagnostics.push(diag(
                    module_path(&module.module),
                    format!("public symbol `{name}` collides with a Python target support name"),
                ));
            }
            if !projected.insert(name.to_owned()) {
                diagnostics.push(diag(
                    module_path(&module.module),
                    format!("public Python symbol `{name}` collides"),
                ));
            }
            if object.get("kind").and_then(Value::as_str) == Some("enum")
                && let Some(variants) = object.get("variants").and_then(Value::as_array)
            {
                for variant in variants {
                    let Some(variant) = variant.get("name").and_then(Value::as_str) else {
                        continue;
                    };
                    let projected_variant = format!("{name}_{variant}");
                    if !projected.insert(projected_variant.clone()) {
                        diagnostics.push(diag(
                            module_path(&module.module),
                            format!("public Python symbol `{projected_variant}` collides"),
                        ));
                    }
                }
            }
        }
    }
    for module in modules.values() {
        let mut external_aliases = BTreeSet::new();
        for declaration in &module.declarations {
            let Some(object) = declaration.as_object() else {
                continue;
            };
            if object.get("kind").and_then(Value::as_str) == Some("external_type")
                && !external_aliases.insert(external_import_alias(object))
            {
                diagnostics.push(diag(
                    module_path(&module.module),
                    "external Python import aliases collide",
                ));
            }
        }
        for declaration in &module.declarations {
            let Some(object) = declaration.as_object() else {
                continue;
            };
            if object.get("kind").and_then(Value::as_str) != Some("external_type")
                && external_aliases.contains(&format!(
                    "_cott_external_{}",
                    local_name(
                        object
                            .get("name")
                            .and_then(Value::as_str)
                            .unwrap_or_default(),
                    )
                ))
            {
                diagnostics.push(diag(
                    module_path(&module.module),
                    "external Python import alias collides with a generated declaration",
                ));
            }
        }
    }
    validate_impl_selections(&modules, &mut diagnostics);
    let callables = plan
        .callables()
        .into_iter()
        .map(|callable| (callable.cott_symbol.clone(), callable))
        .collect::<BTreeMap<_, _>>();
    for module in modules.values() {
        for implementation in module
            .declarations
            .iter()
            .filter_map(Value::as_object)
            .filter(|declaration| declaration.get("kind").and_then(Value::as_str) == Some("impl"))
        {
            for method in implementation
                .get("selected_methods")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                let Some(function) = method
                    .get("selected")
                    .and_then(Value::as_object)
                    .filter(|selected| {
                        matches!(
                            selected.get("origin").and_then(Value::as_str),
                            Some("default" | "specialization")
                        )
                    })
                    .and_then(|selected| selected.get("function"))
                    .and_then(Value::as_object)
                else {
                    continue;
                };
                let verified_facade = function
                    .get("verified_facade")
                    .and_then(Value::as_str)
                    .unwrap_or_default();
                if !callables.get(verified_facade).is_some_and(|callable| {
                    matches!(
                        &callable.kind,
                        PythonCallableKind::Function | PythonCallableKind::AsyncFunction
                    )
                }) {
                    diagnostics.push(diag(
                        module_path(&module.module),
                        "trait default or specialization dispatch must depend on a verified free-function facade",
                    ));
                }
            }
        }
    }
    let mut seen_bindings = BTreeSet::new();
    let mut seen_paths = HashSet::new();
    for binding in bindings {
        let Some(callable) = callables.get(&binding.cott_symbol) else {
            diagnostics.push(diag(
                binding.source.clone(),
                format!(
                    "binding does not match a canonical callable: {}",
                    binding.cott_symbol
                ),
            ));
            continue;
        };
        if binding.module != callable.module
            || binding.function != callable.name
            || binding.kind != callable.kind
        {
            diagnostics.push(diag(
                binding.source.clone(),
                "binding callable identity does not match canonical callable",
            ));
        } else if !seen_bindings.insert(binding.cott_symbol.clone()) {
            diagnostics.push(diag(
                binding.source.clone(),
                "duplicate binding for canonical callable",
            ));
        }
        let expected = binding_path(&binding.module, &binding.kind, &binding.function);
        if binding.generated_relative != expected {
            diagnostics.push(diag(
                binding.generated_relative.clone(),
                format!("binding path must be {}", path_string(&expected)),
            ));
        }
        if !valid_binding_path(&binding.generated_relative) {
            diagnostics.push(diag(
                binding.generated_relative.clone(),
                "binding path must be a normalized relative Python path below _cott_impl",
            ));
        }
        if !seen_paths.insert(binding.generated_relative.clone()) {
            diagnostics.push(diag(
                binding.generated_relative.clone(),
                "colliding binding output path",
            ));
        }
        if binding.sha256 != sha256_hex(&binding.bytes) {
            diagnostics.push(diag(
                binding.source.clone(),
                "binding SHA-256 does not match its bytes",
            ));
        }
        if !exactly_one_newline(&binding.bytes) {
            diagnostics.push(diag(
                binding.source.clone(),
                "binding bytes must end in exactly one newline",
            ));
        }
        if !binding_defines_symbol(&binding.bytes, &binding.implementation_function) {
            diagnostics.push(diag(
                binding.source.clone(),
                format!(
                    "binding does not define symbol {}",
                    binding.implementation_function
                ),
            ));
        }
    }
    for module in modules.values() {
        for declaration in &module.declarations {
            let Some(object) = declaration.as_object() else {
                continue;
            };
            let kind = object
                .get("kind")
                .and_then(Value::as_str)
                .unwrap_or_default();
            for ty in declaration_types(object, kind) {
                validate_named(
                    ty,
                    &module.module,
                    &declarations,
                    &generic_parameters,
                    &mut diagnostics,
                );
            }
            if kind == "struct" {
                if let Some(fields) = object.get("fields").and_then(Value::as_array) {
                    for field in fields {
                        if let Some(ty) = field.get("type") {
                            validate_named(
                                ty,
                                &module.module,
                                &declarations,
                                &generic_parameters,
                                &mut diagnostics,
                            );
                        }
                    }
                }
            }
        }
    }
    for module in modules.values() {
        if let Some(ir_module) = ir
            .modules
            .iter()
            .find(|candidate| candidate.module.as_string() == module.module)
        {
            if !exactly_one_newline(&ir_module.bytes) {
                diagnostics.push(diag(
                    ir_path_dotted(&module.module),
                    "canonical IR bytes must end in exactly one newline",
                ));
            }
        } else {
            diagnostics.push(diag(
                ir_path_dotted(&module.module),
                "missing canonical IR module",
            ));
        }
    }
    for ir_module in &ir.modules {
        if !modules.contains_key(&ir_module.module.as_string()) {
            diagnostics.push(diag(
                ir_path_dotted(&ir_module.module.as_string()),
                "canonical IR contains an unknown module",
            ));
        }
    }
    for module in modules.values() {
        let mut owners = BTreeMap::<String, BTreeSet<String>>::new();
        for imports in [
            referenced_imports(module, &modules, &declarations),
            factory_concrete_imports(module, &declarations),
            resolved_method_imports(module, &modules, &declarations),
            concrete_trait_marker_imports(module, &modules),
        ] {
            for (source, names) in imports {
                for name in names {
                    owners.entry(name).or_default().insert(source.clone());
                }
            }
        }
        for (name, sources) in owners {
            if sources.len() > 1 {
                diagnostics.push(diag(
                    module_path(&module.module),
                    format!(
                        "ambiguous cross-module Python import `{name}` from {}",
                        sources.into_iter().collect::<Vec<_>>().join(", ")
                    ),
                ));
            }
        }
    }
    if !diagnostics.is_empty() {
        return Err(diagnostics);
    }
    let mut files = BTreeMap::new();
    for (path, bytes) in render_runtime(&config.project.name, &config.project.version) {
        add_file(
            &mut files,
            &mut diagnostics,
            prefixed("python", path),
            finish(bytes),
        );
    }
    add_package_markers(&mut files, &mut diagnostics, modules.keys(), bindings);
    for module in modules.values() {
        add_file(
            &mut files,
            &mut diagnostics,
            type_path(&module.module),
            finish(render_types(
                module,
                &modules,
                &declarations,
                &config.python.external_types,
            )),
        );
        add_file(
            &mut files,
            &mut diagnostics,
            facade_path(&module.module),
            finish(render_facade(
                module,
                bindings,
                &declarations,
                config,
                &modules,
            )),
        );
        add_file(
            &mut files,
            &mut diagnostics,
            stub_path(&module.module),
            finish(render_stub(module, &declarations, bindings, &modules)),
        );
    }
    for ir_module in &ir.modules {
        add_file(
            &mut files,
            &mut diagnostics,
            ir_path_dotted(&ir_module.module.as_string()),
            finish(ir_module.bytes.clone()),
        );
    }
    match derive_strategies(ir, &config.verification) {
        Ok(strategies) => {
            for strategy in strategies {
                let (module, function) = strategy
                    .symbol
                    .rsplit_once('.')
                    .unwrap_or(("", &strategy.symbol));
                let mut path = PathBuf::from("tests/generated");
                for segment in module.split('.').filter(|segment| !segment.is_empty()) {
                    path.push(segment);
                }
                path.push(format!("{function}.json"));
                match serde_json::to_vec(&strategy) {
                    Ok(bytes) => add_file(&mut files, &mut diagnostics, path, finish(bytes)),
                    Err(error) => diagnostics.push(diag(
                        path,
                        format!("failed to serialize contract test strategy: {error}"),
                    )),
                }
            }
        }
        Err(error) => diagnostics.push(diag(
            "tests/generated",
            format!("failed to derive contract test strategies: {error}"),
        )),
    }
    for binding in bindings {
        add_file(
            &mut files,
            &mut diagnostics,
            prefixed("python", binding.generated_relative.clone()),
            binding.bytes.clone(),
        );
    }
    if !diagnostics.is_empty() {
        return Err(diagnostics);
    }
    let mut ir_hashes = serde_json::Map::new();
    for module in &ir.modules {
        ir_hashes.insert(
            module.module.as_string(),
            json!(format!("sha256:{}", sha256_hex(&module.bytes))),
        );
    }
    let contract_surface = plan.contract_surface();
    let mut public_python_symbols = serde_json::Map::new();
    for module in modules.values() {
        let mut names = exported_names(module);
        names.extend(module.declarations.iter().filter_map(|declaration| {
            let object = declaration.as_object()?;
            (object.get("kind").and_then(Value::as_str) == Some("function")
                && object
                    .get("public")
                    .and_then(Value::as_bool)
                    .unwrap_or(false))
            .then(|| {
                local_name(
                    object
                        .get("name")
                        .and_then(Value::as_str)
                        .unwrap_or_default(),
                )
                .to_owned()
            })
        }));
        names.sort();
        names.dedup();
        public_python_symbols.insert(module.module.clone(), json!(names));
    }
    let implementation_symbols = bindings
        .iter()
        .map(|binding| {
            let source_module = binding.implementation_module.replace('.', "/");
            let runtime_module = binding
                .generated_relative
                .with_extension("")
                .to_string_lossy()
                .replace('/', ".");
            let (kind, callable_kind, concrete, method) = match &binding.kind {
                PythonCallableKind::Function => ("function", "sync", Value::Null, Value::Null),
                PythonCallableKind::AsyncFunction => {
                    ("async_function", "async", Value::Null, Value::Null)
                }
                PythonCallableKind::ImplMethod { concrete } => (
                    "impl_method",
                    "sync",
                    Value::String(concrete.clone()),
                    Value::String(binding.function.clone()),
                ),
                PythonCallableKind::AsyncImplMethod { concrete } => (
                    "async_impl_method",
                    "async",
                    Value::String(concrete.clone()),
                    Value::String(binding.function.clone()),
                ),
            };
            let selection = match &binding.kind {
                PythonCallableKind::ImplMethod { .. }
                | PythonCallableKind::AsyncImplMethod { .. } => callables
                    .get(&binding.cott_symbol)
                    .and_then(|callable| {
                        (callable
                            .declaration
                            .get("selected")
                            .and_then(Value::as_object)?
                            .get("origin")
                            .and_then(Value::as_str)
                            == Some("explicit"))
                        .then(|| {
                            callable
                                .declaration
                                .get("trait_method")
                                .and_then(Value::as_str)
                        })
                        .flatten()
                    })
                    .map(|trait_method| json!({"kind": "explicit", "trait_method": trait_method}))
                    .unwrap_or(Value::Null),
                PythonCallableKind::Function | PythonCallableKind::AsyncFunction => Value::Null,
            };
            json!({
                "content_hash": format!("sha256:{}", binding.sha256),
                "concrete": concrete,
                "cott_symbol": binding.cott_symbol,
                "callable_kind": callable_kind,
                "kind": kind,
                "method": method,
                "selection": selection,
                "owner": match binding.owner {
                    BindingOwner::Manifest => "manifest",
                    BindingOwner::Agent => "agent",
                },
                "python_symbol": format!(
                    "{runtime_module}:{}",
                    binding.implementation_function
                ),
                "runtime_origin": path_string(
                    &Path::new(
                        Path::new(&config.python.generated)
                            .file_name()
                            .unwrap_or_default()
                    )
                    .join(&binding.generated_relative)
                ),
                "source_origin": path_string(
                    &Path::new(&config.python.source).join(format!("{source_module}.py"))
                ),
            })
        })
        .collect::<Vec<_>>();
    let unresolved = callables
        .values()
        .filter(|callable| !seen_bindings.contains(&callable.cott_symbol))
        .filter(|callable| {
            matches!(
                &callable.kind,
                PythonCallableKind::Function | PythonCallableKind::AsyncFunction
            ) || callable
                .declaration
                .get("selected")
                .and_then(Value::as_object)
                .and_then(|selected| selected.get("origin"))
                .and_then(Value::as_str)
                == Some("explicit")
        })
        .map(|callable| {
            let span = callable
                .declaration
                .get("span")
                .and_then(Value::as_object)
                .expect("validated canonical callable span");
            let coordinate = |field| {
                span.get(field)
                    .and_then(Value::as_u64)
                    .expect("validated canonical callable span coordinate")
            };
            UnresolvedRecord {
                cott_symbol: callable.cott_symbol.clone(),
                kind: match &callable.kind {
                    PythonCallableKind::Function => UnresolvedKind::Function,
                    PythonCallableKind::AsyncFunction => UnresolvedKind::AsyncFunction,
                    PythonCallableKind::ImplMethod { .. } => UnresolvedKind::ImplMethod,
                    PythonCallableKind::AsyncImplMethod { .. } => UnresolvedKind::AsyncImplMethod,
                },
                callable_kind: match &callable.kind {
                    PythonCallableKind::Function | PythonCallableKind::ImplMethod { .. } => {
                        "sync".to_owned()
                    }
                    PythonCallableKind::AsyncFunction
                    | PythonCallableKind::AsyncImplMethod { .. } => "async".to_owned(),
                },
                span: SourceSpan {
                    start_byte: coordinate("start_byte"),
                    end_byte: coordinate("end_byte"),
                    start_line: coordinate("start_line"),
                    start_column: coordinate("start_column"),
                    end_line: coordinate("end_line"),
                    end_column: coordinate("end_column"),
                },
            }
        })
        .collect::<Vec<_>>();
    let artifact_prefix = Path::new(&config.python.generated)
        .parent()
        .unwrap_or_else(|| Path::new(""));
    let managed_files = files
        .iter()
        .map(|(path, bytes)| {
            (
                path_string(&artifact_prefix.join(path)),
                format!("sha256:{}", sha256_hex(bytes)),
            )
        })
        .collect();
    let mut snapshot = GenerationSnapshot {
        generation_id: String::new(),
        verified: false,
        project_version: config.project.version.clone(),
        compatibility: GenerationCompatibility::current(),
        inputs: json!({}),
        tools: json!({
            "compiler": {"version": env!("CARGO_PKG_VERSION")},
            "python": {
                "cache_tag": "cpython-314",
                "implementation": "cpython",
                "machine": target_machine,
                "os": std::env::consts::OS,
                "platform": target_platform,
                "version": "3.14.6",
            },
            "runtime": {"abi": RUNTIME_ABI_VERSION.to_string(), "version": env!("CARGO_PKG_VERSION")},
        }),
        ir: Value::Object(ir_hashes),
        contract_surface,
        public_python_symbols: Value::Object(public_python_symbols),
        implementations: Value::Array(implementation_symbols),
        dependencies: json!([]),
        managed_files,
        unresolved,
        verification: Value::Null,
        semantic_coverage: SemanticCoverage::default(),
        agent_runs: Vec::new(),
    };
    if let Err(error) = snapshot.compute_generation_id() {
        diagnostics.push(diag(
            "generation.json",
            format!("failed to compute generation identity: {error}"),
        ));
    } else {
        let record = GenerationRecord {
            schema_version: GENERATION_SCHEMA_VERSION,
            current: snapshot,
            last_verified: None,
        };
        match record.canonical_bytes() {
            Ok(bytes) => add_file(
                &mut files,
                &mut diagnostics,
                PathBuf::from("generation.json"),
                bytes,
            ),
            Err(error) => diagnostics.push(diag(
                "generation.json",
                format!("failed to serialize generation record: {error}"),
            )),
        }
    }
    if !diagnostics.is_empty() {
        return Err(diagnostics);
    }
    Ok(Emission { files })
}

fn validate_declaration(
    module: &str,
    object: &serde_json::Map<String, Value>,
    diagnostics: &mut Vec<EmitDiagnostic>,
) {
    let Some(kind) = object.get("kind").and_then(Value::as_str) else {
        return;
    };
    if !matches!(kind, "external_type" | "scenario") {
        validate_generic_parameters(object, module, diagnostics);
    }
    match kind {
        "external_type" => {}
        "alias" => {
            if let Some(ty) = required_value(object, "target", module, diagnostics) {
                validate_type(ty, module, diagnostics);
            }
        }
        "newtype" => {
            if let Some(ty) = required_value(object, "carrier", module, diagnostics) {
                validate_type(ty, module, diagnostics);
            }
        }
        "struct" => {
            validate_fields(object, "fields", module, diagnostics);
            if let Some(invariants) = required_array(object, "invariants", module, diagnostics) {
                for invariant in invariants {
                    validate_clause_guard(invariant, module, diagnostics);
                }
            }
        }
        "enum" => {
            let Some(variants) = required_array(object, "variants", module, diagnostics) else {
                return;
            };
            for variant in variants {
                let Some(value) = variant.as_object() else {
                    unsupported(module, "enum variant must be an object", diagnostics);
                    continue;
                };
                if required_string(value, "name", module, diagnostics).is_some() {
                    validate_fields(value, "fields", module, diagnostics);
                }
            }
        }
        "resource" => {
            required_string(object, "initial", module, diagnostics);
            let mut states = BTreeMap::new();
            if let Some(values) = required_array(object, "states", module, diagnostics) {
                for state in values {
                    let Some(state) = state.as_object() else {
                        unsupported(module, "resource state must be an object", diagnostics);
                        continue;
                    };
                    let Some(name) = required_string(state, "name", module, diagnostics) else {
                        continue;
                    };
                    if state.get("source_order").and_then(Value::as_u64).is_none() {
                        unsupported(
                            module,
                            "resource state source_order must be an integer",
                            diagnostics,
                        );
                        continue;
                    }
                    if !state.get("terminal").is_some_and(Value::is_boolean) {
                        unsupported(
                            module,
                            "resource state terminal must be a bool",
                            diagnostics,
                        );
                        continue;
                    }
                    if states
                        .insert(
                            name,
                            state.get("terminal").and_then(Value::as_bool) == Some(true),
                        )
                        .is_some()
                    {
                        unsupported(module, "resource state names must be unique", diagnostics);
                    }
                }
            }
            let mut terminals = BTreeSet::new();
            let mut previous_order = None;
            if let Some(values) = required_array(object, "terminals", module, diagnostics) {
                for terminal in values {
                    let Some(terminal) = terminal.as_object() else {
                        unsupported(module, "resource terminal must be an object", diagnostics);
                        continue;
                    };
                    if terminal.len() != 3
                        || !["state", "source_order", "span"]
                            .into_iter()
                            .all(|field| terminal.contains_key(field))
                    {
                        unsupported(
                            module,
                            "resource terminal must contain exactly state, source_order, and span",
                            diagnostics,
                        );
                        continue;
                    }
                    let Some(state) = required_string(terminal, "state", module, diagnostics)
                    else {
                        continue;
                    };
                    let Some(source_order) = terminal.get("source_order").and_then(Value::as_u64)
                    else {
                        unsupported(
                            module,
                            "resource terminal source_order must be an integer",
                            diagnostics,
                        );
                        continue;
                    };
                    let Some(span) = terminal.get("span") else {
                        unsupported(module, "resource terminal span is missing", diagnostics);
                        continue;
                    };
                    if !valid_source_span(span) {
                        unsupported(module, "resource terminal span is malformed", diagnostics);
                        continue;
                    }
                    let Some(is_terminal) = states.get(&state) else {
                        unsupported(
                            module,
                            "resource terminal state must belong to its resource",
                            diagnostics,
                        );
                        continue;
                    };
                    if !terminals.insert(state.clone()) {
                        unsupported(
                            module,
                            "resource terminal states must be unique",
                            diagnostics,
                        );
                    }
                    if previous_order.is_some_and(|previous| source_order <= previous) {
                        unsupported(
                            module,
                            "resource terminals must preserve terminal declaration order",
                            diagnostics,
                        );
                    }
                    previous_order = Some(source_order);
                    if !*is_terminal {
                        unsupported(
                            module,
                            "resource terminal must correspond to a terminal state",
                            diagnostics,
                        );
                    }
                }
            }
            let terminal_states = states
                .into_iter()
                .filter_map(|(name, terminal)| terminal.then_some(name))
                .collect::<BTreeSet<_>>();
            if terminals != terminal_states {
                unsupported(
                    module,
                    "resource terminals must exactly match terminal states",
                    diagnostics,
                );
            }
            if let Some(edges) = required_array(object, "edges", module, diagnostics) {
                for edge in edges {
                    let Some(edge) = edge.as_object() else {
                        unsupported(module, "resource edge must be an object", diagnostics);
                        continue;
                    };
                    required_string(edge, "from", module, diagnostics);
                    required_string(edge, "to", module, diagnostics);
                }
            }
        }
        "trait" => {
            if let Some(associated_types) =
                required_array(object, "associated_types", module, diagnostics)
            {
                for associated in associated_types {
                    let Some(associated) = associated.as_object() else {
                        unsupported(module, "associated type must be an object", diagnostics);
                        continue;
                    };
                    required_string(associated, "name", module, diagnostics);
                    if let Some(bounds) = required_array(associated, "bounds", module, diagnostics)
                    {
                        for bound in bounds {
                            validate_type(bound, module, diagnostics);
                        }
                    }
                }
            }
            if let Some(methods) = required_array(object, "methods", module, diagnostics) {
                for method in methods {
                    let Some(method) = method.as_object() else {
                        unsupported(module, "trait method must be an object", diagnostics);
                        continue;
                    };
                    match required_string(method, "callable_kind", module, diagnostics).as_deref() {
                        Some("sync" | "async") => {}
                        Some(other) => unsupported(
                            module,
                            format!("trait method callable_kind `{other}` is unsupported"),
                            diagnostics,
                        ),
                        None => {}
                    }
                    if let Some(parameters) =
                        required_array(method, "parameters", module, diagnostics)
                    {
                        for parameter in parameters {
                            if let Some(parameter) = parameter.as_object() {
                                if let Some(ty) =
                                    required_value(parameter, "type", module, diagnostics)
                                {
                                    validate_type(ty, module, diagnostics);
                                }
                            }
                        }
                    }
                    if let Some(ty) = required_value(method, "return_type", module, diagnostics) {
                        validate_type(ty, module, diagnostics);
                    }
                }
            }
        }
        "impl" => {
            validate_fields(object, "state", module, diagnostics);
            if let Some(associated_types) =
                required_array(object, "associated_types", module, diagnostics)
            {
                for associated in associated_types {
                    let Some(associated) = associated.as_object() else {
                        unsupported(
                            module,
                            "associated type assignment must be an object",
                            diagnostics,
                        );
                        continue;
                    };
                    required_string(associated, "name", module, diagnostics);
                    required_string(associated, "trait", module, diagnostics);
                    if let Some(ty) = required_value(associated, "type", module, diagnostics) {
                        validate_type(ty, module, diagnostics);
                    }
                }
            }
            for callable in object
                .get("init")
                .into_iter()
                .chain(object.get("methods"))
                .flat_map(|value| match value {
                    Value::Object(value) => vec![value],
                    Value::Array(values) => values.iter().filter_map(Value::as_object).collect(),
                    _ => Vec::new(),
                })
            {
                for parameter in callable
                    .get("parameters")
                    .and_then(Value::as_array)
                    .into_iter()
                    .flatten()
                    .filter_map(Value::as_object)
                {
                    if let Some(ty) = parameter.get("type") {
                        validate_type(ty, module, diagnostics);
                    }
                }
                if let Some(ty) = callable.get("return_type") {
                    validate_type(ty, module, diagnostics);
                }
                validate_contract_guards(callable.get("contracts"), module, diagnostics);
            }
            let Some(selected_methods) =
                required_array(object, "selected_methods", module, diagnostics)
            else {
                return;
            };
            let mut selected_explicit = BTreeSet::new();
            for method in selected_methods {
                let Some(method) = method.as_object() else {
                    unsupported(
                        module,
                        "selected implementation method must be an object",
                        diagnostics,
                    );
                    continue;
                };
                match required_string(method, "callable_kind", module, diagnostics).as_deref() {
                    Some("sync" | "async") => {}
                    Some(other) => unsupported(
                        module,
                        format!("implementation method callable_kind `{other}` is unsupported"),
                        diagnostics,
                    ),
                    None => {}
                }
                validate_dispatch_slot(method, module, diagnostics);
                if method
                    .get("selected")
                    .and_then(Value::as_object)
                    .and_then(|selected| selected.get("origin"))
                    .and_then(Value::as_str)
                    == Some("explicit")
                    && let Some(name) = method
                        .get("trait_method")
                        .and_then(Value::as_str)
                        .map(local_name)
                {
                    selected_explicit.insert(name.to_owned());
                }
            }
            for method in object
                .get("methods")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                let Some(name) = method.get("name").and_then(Value::as_str).map(local_name) else {
                    continue;
                };
                if !selected_explicit.contains(name) {
                    unsupported(
                        module,
                        format!("implementation method `{name}` is absent from `selected_methods`"),
                        diagnostics,
                    );
                }
            }
            for method in object
                .get("methods")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                let Some(method) = method.as_object() else {
                    unsupported(
                        module,
                        "implementation method must be an object",
                        diagnostics,
                    );
                    continue;
                };
                match required_string(method, "callable_kind", module, diagnostics).as_deref() {
                    Some("sync" | "async") => {}
                    Some(other) => unsupported(
                        module,
                        format!("implementation method callable_kind `{other}` is unsupported"),
                        diagnostics,
                    ),
                    None => {}
                }
                if let Some(transitions) =
                    required_array(method, "transitions", module, diagnostics)
                {
                    for transition in transitions {
                        let Some(transition) = transition.as_object() else {
                            unsupported(
                                module,
                                "implementation transition must be an object",
                                diagnostics,
                            );
                            continue;
                        };
                        required_string(transition, "field", module, diagnostics);
                        required_string(transition, "from", module, diagnostics);
                        required_string(transition, "resource", module, diagnostics);
                        required_string(transition, "to", module, diagnostics);
                    }
                }
            }
            for invariant in object
                .get("invariants")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                validate_clause_guard(invariant, module, diagnostics);
            }
        }
        "specialization" => {
            if let Some(receiver) = required_value(object, "receiver_type", module, diagnostics) {
                validate_type(receiver, module, diagnostics);
            }
            if let Some(trait_ref) = required_value(object, "trait", module, diagnostics) {
                validate_type(trait_ref, module, diagnostics);
            }
            if let Some(methods) = required_array(object, "methods", module, diagnostics) {
                for method in methods.iter().filter_map(Value::as_object) {
                    required_string(method, "name", module, diagnostics);
                    required_string(method, "trait_method", module, diagnostics);
                    match required_string(method, "callable_kind", module, diagnostics).as_deref() {
                        Some("sync" | "async") => {}
                        Some(other) => unsupported(
                            module,
                            format!("specialization method callable_kind `{other}` is unsupported"),
                            diagnostics,
                        ),
                        None => {}
                    }
                    let Some(function) = required_value(method, "function", module, diagnostics)
                        .and_then(Value::as_object)
                    else {
                        unsupported(
                            module,
                            "specialization method function must be an object",
                            diagnostics,
                        );
                        continue;
                    };
                    required_string(function, "module", module, diagnostics);
                    required_string(function, "symbol", module, diagnostics);
                    required_string(function, "verified_facade", module, diagnostics);
                }
            }
        }
        "const" => {
            if let Some(ty) = required_value(object, "type", module, diagnostics) {
                validate_type(ty, module, diagnostics);
            }
            if let Some(value) = required_value(object, "value", module, diagnostics) {
                validate_value(value, module, diagnostics);
            }
        }
        "rule" | "scenario" => {}
        "function" => {
            match required_string(object, "callable_kind", module, diagnostics).as_deref() {
                Some("sync" | "async") => {}
                Some(other) => unsupported(
                    module,
                    format!("function callable_kind `{other}` is unsupported"),
                    diagnostics,
                ),
                None => {}
            }
            let Some(parameters) = required_array(object, "parameters", module, diagnostics) else {
                return;
            };
            for parameter in parameters {
                let Some(parameter) = parameter.as_object() else {
                    unsupported(module, "function parameter must be an object", diagnostics);
                    continue;
                };
                required_string(parameter, "name", module, diagnostics);
                required_string(parameter, "kind", module, diagnostics);
                if let Some(ty) = required_value(parameter, "type", module, diagnostics) {
                    validate_type(ty, module, diagnostics);
                }
                if let Some(default) = parameter.get("default").filter(|value| !value.is_null()) {
                    validate_value(default, module, diagnostics);
                }
            }
            if let Some(ty) = required_value(object, "return_type", module, diagnostics) {
                validate_type(ty, module, diagnostics);
            }
            validate_contract_guards(object.get("contract"), module, diagnostics);
        }
        other => unsupported(
            module,
            format!("canonical declaration kind `{other}` is unsupported"),
            diagnostics,
        ),
    }
}

fn valid_source_span(value: &Value) -> bool {
    let Some(span) = value.as_object() else {
        return false;
    };
    if span.len() != 6
        || ![
            "start_byte",
            "end_byte",
            "start_line",
            "start_column",
            "end_line",
            "end_column",
        ]
        .into_iter()
        .all(|field| span.get(field).and_then(Value::as_u64).is_some())
    {
        return false;
    }
    let start_byte = span["start_byte"].as_u64().expect("validated source span");
    let end_byte = span["end_byte"].as_u64().expect("validated source span");
    let start_line = span["start_line"].as_u64().expect("validated source span");
    let start_column = span["start_column"]
        .as_u64()
        .expect("validated source span");
    let end_line = span["end_line"].as_u64().expect("validated source span");
    let end_column = span["end_column"].as_u64().expect("validated source span");
    end_byte >= start_byte
        && end_line >= start_line
        && start_line > 0
        && start_column > 0
        && end_line > 0
        && end_column > 0
}
fn validate_generic_parameters(
    object: &serde_json::Map<String, Value>,
    module: &str,
    diagnostics: &mut Vec<EmitDiagnostic>,
) {
    let Some(parameters) = required_array(object, "generics", module, diagnostics) else {
        return;
    };
    let mut names = BTreeSet::new();
    for parameter in parameters {
        let Some(parameter) = parameter.as_object() else {
            unsupported(module, "generic parameter must be an object", diagnostics);
            continue;
        };
        let Some(name) = required_string(parameter, "name", module, diagnostics) else {
            continue;
        };
        if !valid_python_name(&name) || !names.insert(name) {
            unsupported(
                module,
                "generic parameter names must be unique Python identifiers",
                diagnostics,
            );
        }
        match required_string(parameter, "kind", module, diagnostics).as_deref() {
            Some("type") => {
                if let Some(bounds) = parameter.get("bounds") {
                    let Some(bounds) = bounds.as_array() else {
                        unsupported(module, "type generic bounds must be an array", diagnostics);
                        continue;
                    };
                    for bound in bounds {
                        validate_type(bound, module, diagnostics);
                    }
                }
            }
            Some("const") => match parameter.get("type").and_then(Value::as_str) {
                Some("U8" | "U16" | "U32" | "U64") => {}
                _ => unsupported(
                    module,
                    "const generic type must be U8, U16, U32, or U64",
                    diagnostics,
                ),
            },
            Some(other) => unsupported(
                module,
                format!("generic parameter kind `{other}` is unsupported"),
                diagnostics,
            ),
            None => {}
        }
    }
}
fn validate_dispatch_slot(
    method: &serde_json::Map<String, Value>,
    module: &str,
    diagnostics: &mut Vec<EmitDiagnostic>,
) {
    required_string(method, "trait_method", module, diagnostics);
    match required_string(method, "callable_kind", module, diagnostics).as_deref() {
        Some("sync" | "async") => {}
        Some(other) => unsupported(
            module,
            format!("dispatch slot callable_kind `{other}` is unsupported"),
            diagnostics,
        ),
        None => {}
    }
    if let Some(receiver) = required_value(method, "receiver_type", module, diagnostics) {
        validate_type(receiver, module, diagnostics);
    }
    let Some(selected) =
        required_value(method, "selected", module, diagnostics).and_then(Value::as_object)
    else {
        unsupported(
            module,
            "dispatch slot selected value must be an object",
            diagnostics,
        );
        return;
    };
    if !matches!(
        selected.get("origin").and_then(Value::as_str),
        Some("explicit" | "default" | "specialization")
    ) {
        unsupported(
            module,
            "dispatch slot origin must be explicit, specialization, or default",
            diagnostics,
        );
    }
    let Some(function) = selected.get("function").and_then(Value::as_object) else {
        unsupported(
            module,
            "dispatch slot function must be an object",
            diagnostics,
        );
        return;
    };
    let Some(function_module) = function.get("module").and_then(Value::as_str) else {
        unsupported(
            module,
            "dispatch function module must be a dotted identifier",
            diagnostics,
        );
        return;
    };
    let Some(symbol) = function.get("symbol").and_then(Value::as_str) else {
        unsupported(
            module,
            "dispatch function symbol must be a dotted identifier",
            diagnostics,
        );
        return;
    };
    let Some(verified_facade) = function.get("verified_facade").and_then(Value::as_str) else {
        unsupported(
            module,
            "dispatch function verified_facade must be a string",
            diagnostics,
        );
        return;
    };
    if function_module
        .split('.')
        .chain(symbol.split('.'))
        .any(|part| !valid_python_name(part))
        || verified_facade != format!("{function_module}.{symbol}")
    {
        unsupported(
            module,
            "dispatch function provenance must identify its exact verified facade",
            diagnostics,
        );
    }
}

fn validate_external_types(
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    declarations: &BTreeMap<String, String>,
    external_types: &BTreeMap<String, String>,
    diagnostics: &mut Vec<EmitDiagnostic>,
) {
    for (name, kind) in declarations {
        if kind == "external_type" && !external_types.contains_key(name) {
            let module = modules
                .values()
                .find(|module| {
                    module.declarations.iter().any(|declaration| {
                        declaration.get("name").and_then(Value::as_str) == Some(name)
                    })
                })
                .map_or("python", |module| module.module.as_str());

            diagnostics.push(diag(
                module_path(module),
                format!("external type `{name}` has no Python projection"),
            ));
        }
    }
    for (name, projection) in external_types {
        match declarations.get(name).map(String::as_str) {
            Some("external_type") => {
                if external_type_target(projection).is_none() {
                    diagnostics.push(diag(
                        "cott.toml",
                        format!(
                            "external type `{name}` has malformed Python projection `{projection}`"
                        ),
                    ));
                }
            }
            Some(_) => diagnostics.push(diag(
                "cott.toml",
                format!("Python external type projection `{name}` is not an external type"),
            )),
            None => diagnostics.push(diag(
                "cott.toml",
                format!("Python external type projection `{name}` is stale"),
            )),
        }
    }
}
fn validate_contract_guards(
    contract: Option<&Value>,
    module: &str,
    diagnostics: &mut Vec<EmitDiagnostic>,
) {
    let Some(contract) = contract.and_then(Value::as_object) else {
        return;
    };
    if let Some(clauses) = contract.get("clauses").and_then(Value::as_array) {
        for clause in clauses {
            validate_clause_guard(clause, module, diagnostics);
        }
    }
    for name in ["requires", "errors", "ensures"] {
        for clause in contract
            .get(name)
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
        {
            validate_clause_guard(clause, module, diagnostics);
        }
    }
}

fn validate_clause_guard(clause: &Value, module: &str, diagnostics: &mut Vec<EmitDiagnostic>) {
    let Some(guard) = clause.get("guard").filter(|guard| !guard.is_null()) else {
        return;
    };
    let Some(guard) = guard.as_object() else {
        unsupported(module, "contract guard must be an object", diagnostics);
        return;
    };
    if !guard.get("scrutinee").is_some_and(Value::is_object) {
        unsupported(
            module,
            "contract guard scrutinee must be an expression",
            diagnostics,
        );
    }
    if let Some(pattern) = guard.get("pattern") {
        validate_contract_pattern(pattern, module, diagnostics);
    } else {
        unsupported(module, "contract guard pattern is missing", diagnostics);
    }
}

fn validate_contract_pattern(pattern: &Value, module: &str, diagnostics: &mut Vec<EmitDiagnostic>) {
    let Some(pattern) = pattern.as_object() else {
        unsupported(module, "contract pattern must be an object", diagnostics);
        return;
    };
    let Some(kind) = pattern.get("kind").and_then(Value::as_str) else {
        unsupported(module, "contract pattern kind is missing", diagnostics);
        return;
    };
    if let Some(ty) = pattern.get("type") {
        validate_type(ty, module, diagnostics);
    } else {
        unsupported(module, "contract pattern type is missing", diagnostics);
    }
    match kind {
        "wildcard" => {}
        "binding" => {
            if !pattern
                .get("name")
                .and_then(Value::as_str)
                .is_some_and(valid_python_name)
            {
                unsupported(
                    module,
                    "contract binding pattern name is invalid",
                    diagnostics,
                );
            }
        }
        "variant" | "result_ok" | "result_err" | "option_some" | "option_none" | "enum" => {
            required_string(pattern, "symbol", module, diagnostics);
            let Some(arguments) = required_array(pattern, "arguments", module, diagnostics) else {
                return;
            };
            for argument in arguments {
                validate_contract_pattern(argument, module, diagnostics);
            }
        }
        _ => unsupported(
            module,
            format!("contract pattern kind `{kind}` is unsupported"),
            diagnostics,
        ),
    }
}

fn validate_fields(
    object: &serde_json::Map<String, Value>,
    field: &str,
    module: &str,
    diagnostics: &mut Vec<EmitDiagnostic>,
) {
    let Some(fields) = required_array(object, field, module, diagnostics) else {
        return;
    };
    for item in fields {
        let Some(value) = item.as_object() else {
            unsupported(module, "field must be an object", diagnostics);
            continue;
        };
        required_string(value, "name", module, diagnostics);
        if let Some(ty) = required_value(value, "type", module, diagnostics) {
            validate_type(ty, module, diagnostics);
        }
        if let Some(default) = value.get("default").filter(|value| !value.is_null()) {
            validate_value(default, module, diagnostics);
        }
    }
}
fn validate_type(value: &Value, module: &str, diagnostics: &mut Vec<EmitDiagnostic>) {
    let Some(object) = value.as_object() else {
        unsupported(module, "type must be an object", diagnostics);
        return;
    };
    let Some(kind) = required_string(object, "kind", module, diagnostics) else {
        return;
    };
    match kind.as_str() {
        "primitive" => {
            let Some(name) = required_string(object, "name", module, diagnostics) else {
                return;
            };
            if !matches!(
                name.as_str(),
                "bool"
                    | "i8"
                    | "i16"
                    | "i32"
                    | "i64"
                    | "u8"
                    | "u16"
                    | "u32"
                    | "u64"
                    | "f32"
                    | "f64"
                    | "str"
                    | "bytes"
                    | "path"
                    | "unit"
                    | "json"
                    | "any"
                    | "unknown"
                    | "never"
            ) {
                unsupported(
                    module,
                    format!("primitive type `{name}` is unsupported"),
                    diagnostics,
                );
            }
        }
        "named" => {
            required_string(object, "name", module, diagnostics);
            let Some(args) = required_array(object, "args", module, diagnostics) else {
                return;
            };
            for arg in args {
                let Some(arg) = arg.as_object() else {
                    unsupported(module, "generic argument must be an object", diagnostics);
                    continue;
                };
                match required_string(arg, "kind", module, diagnostics).as_deref() {
                    Some("type") => {
                        if let Some(ty) = required_value(arg, "type", module, diagnostics) {
                            validate_type(ty, module, diagnostics);
                        }
                    }
                    Some("const") => {
                        if let Some(value) = required_value(arg, "value", module, diagnostics) {
                            validate_const_argument(value, None, "generic", module, diagnostics);
                        }
                    }
                    Some(other) => unsupported(
                        module,
                        format!("generic argument kind `{other}` is unsupported"),
                        diagnostics,
                    ),
                    None => {}
                }
            }
        }
        "type_parameter" => {
            required_string(object, "name", module, diagnostics);
        }
        "associated_projection" => {
            required_string(object, "name", module, diagnostics);
            required_string(object, "trait", module, diagnostics);
            if let Some(base) = required_value(object, "base", module, diagnostics) {
                validate_type(base, module, diagnostics);
            }
        }
        "list" | "set" | "option" | "iterator" | "async_iterator" => {
            if let Some(item) = required_value(object, "item", module, diagnostics) {
                validate_type(item, module, diagnostics);
            }
        }
        "dyn" => {
            if let Some(trait_ref) = required_value(object, "trait", module, diagnostics) {
                validate_type(trait_ref, module, diagnostics);
            }
        }
        "factory" => {
            if let Some(instance) = required_value(object, "instance", module, diagnostics) {
                validate_type(instance, module, diagnostics);
            }
        }
        "map" => {
            for field in ["key", "value"] {
                if let Some(item) = required_value(object, field, module, diagnostics) {
                    validate_type(item, module, diagnostics);
                }
            }
        }
        "tuple" => {
            if let Some(items) = required_array(object, "items", module, diagnostics) {
                for item in items {
                    validate_type(item, module, diagnostics);
                }
            }
        }
        "array" => {
            if let Some(item) = required_value(object, "item", module, diagnostics) {
                validate_type(item, module, diagnostics);
            }
            validate_fixed_length(object, "length", module, diagnostics);
        }
        "buffer" => validate_fixed_length(object, "length", module, diagnostics),
        "result" => {
            for field in ["ok", "error"] {
                if let Some(item) = required_value(object, field, module, diagnostics) {
                    validate_type(item, module, diagnostics);
                }
            }
        }
        "generator" => {
            for field in ["yield", "send", "return"] {
                if let Some(item) = required_value(object, field, module, diagnostics) {
                    validate_type(item, module, diagnostics);
                }
            }
        }
        "async_generator" => {
            for field in ["yield", "send"] {
                if let Some(item) = required_value(object, field, module, diagnostics) {
                    validate_type(item, module, diagnostics);
                }
            }
        }
        "opaque" => {
            required_string(object, "tag", module, diagnostics);
        }
        other => unsupported(
            module,
            format!("canonical type kind `{other}` is unsupported"),
            diagnostics,
        ),
    }
}
fn validate_fixed_length(
    object: &serde_json::Map<String, Value>,
    field: &str,
    module: &str,
    diagnostics: &mut Vec<EmitDiagnostic>,
) {
    let Some(length) = object.get(field) else {
        unsupported(
            module,
            format!("{field} must be a const argument object"),
            diagnostics,
        );
        return;
    };
    validate_const_argument(length, None, field, module, diagnostics);
}

fn validate_const_argument(
    value: &Value,
    expected_type: Option<&str>,
    label: &str,
    module: &str,
    diagnostics: &mut Vec<EmitDiagnostic>,
) {
    let Some(argument) = value.as_object() else {
        unsupported(
            module,
            format!("{label} const argument must be an object"),
            diagnostics,
        );
        return;
    };
    let Some(ty) = argument.get("type").and_then(Value::as_str) else {
        unsupported(
            module,
            format!("{label} const argument type is missing"),
            diagnostics,
        );
        return;
    };
    if expected_type.is_some_and(|expected| expected != ty) {
        unsupported(
            module,
            format!("{label} const argument type does not match its parameter"),
            diagnostics,
        );
        return;
    }
    let maximum = match ty {
        "U8" => u8::MAX as u64,
        "U16" => u16::MAX as u64,
        "U32" => u32::MAX as u64,
        "U64" => u64::MAX,
        _ => {
            unsupported(
                module,
                format!("{label} const argument type is unsupported"),
                diagnostics,
            );
            return;
        }
    };
    match argument.get("kind").and_then(Value::as_str) {
        Some("value") => match argument.get("value").and_then(Value::as_u64) {
            Some(value) if value <= maximum => {}
            _ => unsupported(
                module,
                format!("{label} const value is outside its type range"),
                diagnostics,
            ),
        },
        Some("parameter") => {
            if !argument
                .get("name")
                .and_then(Value::as_str)
                .is_some_and(valid_python_name)
            {
                unsupported(
                    module,
                    format!("{label} const parameter name is invalid"),
                    diagnostics,
                );
            }
        }
        _ => unsupported(
            module,
            format!("{label} const argument kind is unsupported"),
            diagnostics,
        ),
    }
}

fn render_fixed_length(value: &Value, typevar_names: &BTreeMap<String, String>) -> String {
    let object = value.as_object().expect("validated fixed length");
    match object.get("kind").and_then(Value::as_str) {
        Some("value") => object
            .get("value")
            .and_then(Value::as_u64)
            .expect("validated fixed length value")
            .to_string(),
        Some("parameter") => {
            let name = object
                .get("name")
                .and_then(Value::as_str)
                .expect("validated fixed length parameter");
            typevar_names
                .get(name)
                .cloned()
                .unwrap_or_else(|| name.to_owned())
        }
        _ => unreachable!("validated fixed length kind"),
    }
}

fn validate_value(value: &Value, module: &str, diagnostics: &mut Vec<EmitDiagnostic>) {
    let Some(object) = value.as_object() else {
        unsupported(module, "value must be an object", diagnostics);
        return;
    };
    let Some(kind) = required_string(object, "kind", module, diagnostics) else {
        return;
    };
    match kind.as_str() {
        "bool" => {
            if object.get("value").and_then(Value::as_bool).is_none() {
                unsupported(module, "boolean value is missing", diagnostics);
            }
        }
        "integer" | "string" => {
            required_value(object, "value", module, diagnostics);
        }
        "f32" | "f64" => {
            required_string(object, "bits", module, diagnostics);
        }
        "unit" => {}
        "bytes" => {
            if object.get("value").and_then(Value::as_str).is_none() {
                unsupported(module, "byte value is missing", diagnostics);
            }
        }
        "option" => {
            if let Some(value) = object.get("value").filter(|value| !value.is_null()) {
                validate_value(value, module, diagnostics);
            }
        }
        "result" => {
            if let Some(value) = required_value(object, "value", module, diagnostics) {
                validate_value(value, module, diagnostics);
            }
        }
        "list" | "set" => {
            if let Some(items) = required_array(object, "items", module, diagnostics) {
                for item in items {
                    validate_value(item, module, diagnostics);
                }
            }
        }
        "map" => {
            if let Some(entries) = required_array(object, "entries", module, diagnostics) {
                for entry in entries.iter().filter_map(Value::as_array) {
                    for item in entry {
                        validate_value(item, module, diagnostics);
                    }
                }
            }
        }
        "tuple" | "array" => {
            if let Some(items) = required_array(object, "items", module, diagnostics) {
                for item in items {
                    validate_value(item, module, diagnostics);
                }
            }
        }
        "buffer" => {
            let Some(hex) = required_string(object, "hex", module, diagnostics) else {
                return;
            };
            if hex.len() % 2 != 0
                || hex
                    .bytes()
                    .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
            {
                unsupported(
                    module,
                    "buffer hex must be lowercase hexadecimal with an even length",
                    diagnostics,
                );
            }
        }
        "named" => {
            required_string(object, "symbol", module, diagnostics);
            if let Some(fields) = required_array(object, "fields", module, diagnostics) {
                for field in fields.iter().filter_map(Value::as_object) {
                    if let Some(value) = required_value(field, "value", module, diagnostics) {
                        validate_value(value, module, diagnostics);
                    }
                }
            }
        }
        "enum" => {
            required_string(object, "variant", module, diagnostics);
            if let Some(fields) = required_array(object, "fields", module, diagnostics) {
                for field in fields {
                    validate_value(field, module, diagnostics);
                }
            }
        }
        "json" => {
            required_value(object, "value", module, diagnostics);
        }
        other => unsupported(
            module,
            format!("canonical value kind `{other}` is unsupported"),
            diagnostics,
        ),
    }
}

fn ordered_trait_declarations(
    module: &crate::python::artifact_plan::PythonArtifactModule,
) -> Vec<&Value> {
    fn collect_local_trait_references(
        value: &Value,
        traits: &BTreeMap<String, &Value>,
        references: &mut BTreeSet<String>,
    ) {
        if let Some(object) = value.as_object() {
            if object.get("kind").and_then(Value::as_str) == Some("named")
                && let Some(name) = object.get("name").and_then(Value::as_str)
                && traits.contains_key(name)
            {
                references.insert(name.to_owned());
            }
            for child in object.values() {
                collect_local_trait_references(child, traits, references);
            }
        } else if let Some(values) = value.as_array() {
            for value in values {
                collect_local_trait_references(value, traits, references);
            }
        }
    }

    fn visit<'a>(
        name: &str,
        traits: &BTreeMap<String, &'a Value>,
        visiting: &mut BTreeSet<String>,
        complete: &mut BTreeSet<String>,
        ordered: &mut Vec<&'a Value>,
    ) {
        if complete.contains(name) || !visiting.insert(name.to_owned()) {
            return;
        }
        let declaration = traits.get(name).expect("known local trait");
        for parent in declaration
            .get("parents")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(|parent| parent.get("trait"))
            .filter_map(|trait_ref| trait_ref.get("name"))
            .filter_map(Value::as_str)
        {
            if traits.contains_key(parent) {
                visit(parent, traits, visiting, complete, ordered);
            }
        }
        let mut bound_traits = BTreeSet::new();
        for generic in declaration
            .get("generics")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
        {
            if let Some(bounds) = generic.get("bounds") {
                collect_local_trait_references(bounds, traits, &mut bound_traits);
            }
        }
        for bound_trait in bound_traits {
            visit(&bound_trait, traits, visiting, complete, ordered);
        }
        visiting.remove(name);
        complete.insert(name.to_owned());
        ordered.push(declaration);
    }

    let traits = module
        .declarations
        .iter()
        .filter(|declaration| declaration.get("kind").and_then(Value::as_str) == Some("trait"))
        .filter_map(|declaration| {
            declaration
                .get("name")
                .and_then(Value::as_str)
                .map(|name| (name.to_owned(), declaration))
        })
        .collect::<BTreeMap<_, _>>();
    let mut visiting = BTreeSet::new();
    let mut complete = BTreeSet::new();
    let mut ordered = Vec::new();
    for declaration in &module.declarations {
        if let Some(name) = declaration
            .get("name")
            .and_then(Value::as_str)
            .filter(|name| traits.contains_key(*name))
        {
            visit(name, &traits, &mut visiting, &mut complete, &mut ordered);
        }
    }
    ordered
}

fn render_types(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    declarations: &BTreeMap<String, String>,
    external_types: &BTreeMap<String, String>,
) -> Vec<u8> {
    let mut out = String::from(
        "from __future__ import annotations\n\nfrom collections.abc import Generator, Iterator\nimport dataclasses as _dataclasses\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable\n\nfrom cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction\n",
    );
    for (source, name, alias) in external_imports(module, external_types) {
        writeln!(out, "from {source} import {name} as {alias}").unwrap();
    }
    let imports = referenced_imports(module, modules, declarations);
    for (source, names) in &imports {
        writeln!(
            out,
            "from {} import {}",
            type_module_name(source),
            names.iter().cloned().collect::<Vec<_>>().join(", ")
        )
        .unwrap();
    }
    let factory_imports = factory_concrete_imports(module, declarations);
    for (source, names) in &factory_imports {
        writeln!(
            out,
            "from {source} import {}",
            names.iter().cloned().collect::<Vec<_>>().join(", ")
        )
        .unwrap();
    }
    if !imports.is_empty() || !factory_imports.is_empty() {
        out.push('\n');
    }
    let mut rendered_typevars = BTreeSet::new();
    for declaration in ordered_trait_declarations(module) {
        render_generic_typevars_for_declaration(
            &mut out,
            module,
            declarations,
            declaration
                .as_object()
                .expect("validated trait declaration"),
            false,
            true,
            true,
            &mut rendered_typevars,
        );
        render_type_declaration(
            &mut out,
            declaration,
            module,
            modules,
            declarations,
            external_types,
        );
    }
    let has_associated_typevars =
        render_associated_typevars(&mut out, module, modules, declarations);
    for declaration in &module.declarations {
        let Some(object) = declaration.as_object() else {
            continue;
        };
        if matches!(
            object.get("kind").and_then(Value::as_str),
            Some("trait" | "function" | "scenario")
        ) {
            continue;
        }
        render_generic_typevars_for_declaration(
            &mut out,
            module,
            declarations,
            object,
            false,
            true,
            true,
            &mut rendered_typevars,
        );
    }
    if !rendered_typevars.is_empty() || has_associated_typevars {
        out.push('\n');
    }
    for declaration in &module.declarations {
        if matches!(
            declaration.get("kind").and_then(Value::as_str),
            Some("trait" | "scenario")
        ) {
            continue;
        }
        render_type_declaration(
            &mut out,
            declaration,
            module,
            modules,
            declarations,
            external_types,
        );
    }
    render_function_bound_protocols(&mut out, module, declarations);
    let names = type_exported_names(module);
    writeln!(
        out,
        "__all__ = [{}]",
        names
            .iter()
            .map(|name| json_string(name))
            .collect::<Vec<_>>()
            .join(", ")
    )
    .unwrap();
    out.into_bytes()
}
fn render_type_declaration(
    out: &mut String,
    declaration: &Value,
    module: &crate::python::artifact_plan::PythonArtifactModule,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    declarations: &BTreeMap<String, String>,
    external_types: &BTreeMap<String, String>,
) {
    let object = declaration.as_object().unwrap();
    let typevar_names = generic_typevar_names(module, object, false);
    let kind = object.get("kind").and_then(Value::as_str).unwrap();
    let name = local_name(
        object
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or_default(),
    );
    let generics = generic_parameters_with_names(object, &typevar_names);
    let generic_base = (!generics.is_empty())
        .then(|| format!("(Generic[{generics}])"))
        .unwrap_or_default();
    match kind {
        "struct" => render_private_defaults(
            out,
            name,
            object,
            module,
            modules,
            declarations,
            &typevar_names,
        ),
        "enum" => {
            for variant in object
                .get("variants")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(Value::as_object)
            {
                let owner = format!(
                    "{name}_{}",
                    variant
                        .get("name")
                        .and_then(Value::as_str)
                        .unwrap_or_default()
                );
                render_private_defaults(
                    out,
                    &owner,
                    variant,
                    module,
                    modules,
                    declarations,
                    &typevar_names,
                );
            }
        }
        _ => {}
    }
    render_doc(out, object.get("doc"));
    match kind {
        "external_type" => {
            let canonical_name = object.get("name").and_then(Value::as_str).unwrap();
            let projection = external_types
                .get(canonical_name)
                .expect("validated Python external type projection");
            let (_, qualified) = external_type_target(projection)
                .expect("validated Python external type projection");
            let nested = qualified.find('.').map_or("", |index| &qualified[index..]);
            writeln!(
                out,
                "{name}: TypeAlias = Annotated[{}{nested}, CottExternal({})]\n",
                external_import_alias(object),
                json_string(projection),
            )
            .unwrap();
        }
        "alias" => writeln!(
            out,
            "{name}: TypeAlias = {}\n",
            render_type_with_names(
                object.get("target").unwrap(),
                &module.module,
                declarations,
                &typevar_names,
            )
        )
        .unwrap(),
        "newtype" => {
            let carrier = render_type_with_names(
                object.get("carrier").unwrap(),
                &module.module,
                declarations,
                &typevar_names,
            );
            writeln!(
                out,
                "@final\n@dataclass(frozen=True, slots=True, kw_only=True)\nclass {name}{generic_base}:\n    value: {carrier}\n\n    def __post_init__(self) -> None:\n        object.__setattr__(self, \"value\", _cott_validate_abi(self.value, {carrier}, path=\"$.value\"))"
            )
            .unwrap();
            if let Some(refinement) = object.get("refinement").filter(|value| !value.is_null()) {
                let condition =
                    render_contract_expression(refinement).replace("_result", "self.value");
                let span = serde_json::to_string(refinement.get("span").unwrap())
                    .expect("span serializes");
                let symbol = object
                    .get("name")
                    .and_then(Value::as_str)
                    .unwrap_or_default();
                writeln!(
                    out,
                    "        if not ({condition}):\n            raise CottContractViolation({}, symbol={}, phase=\"refinement\", span={span}, expected=\"true\", actual=\"false\")",
                    json_string(&format!("{name} refinement failed")),
                    json_string(symbol),
                )
                .unwrap();
            }
            if !hash_stable_type(
                object.get("carrier").unwrap(),
                modules,
                &mut BTreeSet::new(),
            ) {
                out.push_str("\n    __hash__ = None");
            }
            out.push('\n');
        }
        "struct" => {
            writeln!(
                out,
                "@final\n@dataclass(frozen=True, slots=True, kw_only=True)\nclass {name}{generic_base}:"
            )
            .unwrap();
            out.push_str("    __hash__ = None\n");
            render_fields(
                out,
                object,
                name,
                module,
                modules,
                declarations,
                &typevar_names,
            );
            render_struct_post_init(out, object, &module.module, declarations, &typevar_names);
        }
        "resource" => {
            let states = object.get("states").and_then(Value::as_array).unwrap();
            for state in states {
                let state_name = format!(
                    "{name}_{}",
                    local_name(
                        state
                            .get("name")
                            .and_then(Value::as_str)
                            .unwrap_or_default()
                    )
                );
                writeln!(
                    out,
                    "@final\nclass {state_name}:\n    __slots__ = ()\n    _instance: {state_name} | None = None\n\n    def __new__(cls) -> {state_name}:\n        if cls._instance is None:\n            cls._instance = object.__new__(cls)\n        return cls._instance\n\n    def __repr__(self) -> str:\n        return {}",
                    json_string(&format!("{name}.{}", local_name(state.get("name").and_then(Value::as_str).unwrap_or_default())))
                )
                .unwrap();
            }
            writeln!(
                out,
                "{name}: TypeAlias = Union[{}]\n",
                states
                    .iter()
                    .map(|state| format!(
                        "{name}_{}",
                        local_name(
                            state
                                .get("name")
                                .and_then(Value::as_str)
                                .unwrap_or_default()
                        )
                    ))
                    .collect::<Vec<_>>()
                    .join(", ")
            )
            .unwrap();
        }
        "enum" => {
            let variants = object.get("variants").and_then(Value::as_array).unwrap();
            for variant in variants {
                let variant = variant.as_object().unwrap();
                let variant_name = format!(
                    "{name}_{}",
                    variant
                        .get("name")
                        .and_then(Value::as_str)
                        .unwrap_or_default()
                );
                writeln!(
                    out,
                    "@final\n@dataclass(frozen=True, slots=True, kw_only=True)\nclass {variant_name}{generic_base}:"
                )
                .unwrap();
                if variant
                    .get("fields")
                    .and_then(Value::as_array)
                    .is_some_and(|fields| !fields.is_empty())
                {
                    out.push_str("    __hash__ = None\n");
                }
                render_fields(
                    out,
                    variant,
                    &variant_name,
                    module,
                    modules,
                    declarations,
                    &typevar_names,
                );
            }
            let generic_args = (!generics.is_empty())
                .then(|| format!("[{generics}]"))
                .unwrap_or_default();
            writeln!(
                out,
                "{name}: TypeAlias = Union[{}]\n",
                variants
                    .iter()
                    .filter_map(|variant| variant.get("name").and_then(Value::as_str))
                    .map(|variant| format!("{name}_{variant}{generic_args}"))
                    .collect::<Vec<_>>()
                    .join(", ")
            )
            .unwrap();
        }
        "trait" => {
            let mut bases = object
                .get("parents")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(|parent| parent.get("trait"))
                .map(|trait_ref| {
                    render_type_with_names(trait_ref, &module.module, declarations, &typevar_names)
                })
                .collect::<Vec<_>>();
            bases.push(if generics.is_empty() {
                "Protocol".to_owned()
            } else {
                format!("Protocol[{generics}]")
            });
            writeln!(
                out,
                "@runtime_checkable\nclass {name}({}):",
                bases.join(", ")
            )
            .unwrap();
            out.push_str("    _cott_trait = True\n");
            let methods = object.get("methods").and_then(Value::as_array).unwrap();
            if methods.is_empty() {
                out.push('\n');
            } else {
                for method in methods {
                    let method = method.as_object().unwrap();
                    let method_name = local_name(
                        method
                            .get("name")
                            .and_then(Value::as_str)
                            .unwrap_or_default(),
                    );
                    let typevar_names = generic_typevar_names(module, object, false);
                    let (signature, _, _) = render_function_parameters_with_names(
                        method,
                        &module.module,
                        declarations,
                        &typevar_names,
                    );
                    let signature = if signature.is_empty() {
                        "self".to_owned()
                    } else {
                        format!("self, {signature}")
                    };
                    let return_type = render_type_with_names(
                        method.get("return_type").unwrap(),
                        &module.module,
                        declarations,
                        &typevar_names,
                    );
                    writeln!(
                        out,
                        "    {}def {method_name}({signature}) -> {return_type}:\n        ...\n",
                        if method.get("callable_kind").and_then(Value::as_str) == Some("async") {
                            "async "
                        } else {
                            ""
                        }
                    )
                    .unwrap();
                }
                out.push('\n');
            }
        }
        "rule" => {
            let base_name = object.get("base").and_then(Value::as_str);
            let base_str = if let Some(base) = base_name {
                let short_base = local_name(base);
                if generics.is_empty() {
                    format!("({short_base})")
                } else {
                    format!("({short_base}[{generics}])")
                }
            } else if generics.is_empty() {
                String::new()
            } else {
                format!("(Generic[{generics}])")
            };
            writeln!(out, "class {name}{base_str}:").unwrap();
            out.push_str("    pass\n\n");
        }
        "const" => writeln!(
            out,
            "{name}: Final[{}] = {}\n",
            render_type_with_names(
                object.get("type").unwrap(),
                &module.module,
                declarations,
                &typevar_names,
            ),
            render_value(object.get("value").unwrap())
        )
        .unwrap(),
        "function" => {}
        _ => {}
    }
}

fn generic_parameters_with_names(
    object: &serde_json::Map<String, Value>,
    names: &BTreeMap<String, String>,
) -> String {
    object
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(|generic| generic.get("name").and_then(Value::as_str))
        .map(|name| names.get(name).cloned().unwrap_or_else(|| name.to_owned()))
        .collect::<Vec<_>>()
        .join(", ")
}
fn render_const_generic_type(name: &str) -> &'static str {
    match name {
        "U8" => "U8",
        "U16" => "U16",
        "U32" => "U32",
        "U64" => "U64",
        _ => "int",
    }
}

fn generic_specs<'a>(
    module: &'a crate::python::artifact_plan::PythonArtifactModule,
    functions_only: bool,
) -> BTreeMap<String, Vec<&'a Value>> {
    let mut specs = BTreeMap::new();
    for declaration in &module.declarations {
        let Some(object) = declaration.as_object() else {
            continue;
        };
        if functions_only && object.get("kind").and_then(Value::as_str) != Some("function") {
            continue;
        }
        for generic in object
            .get("generics")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("type"))
        {
            let Some(name) = generic.get("name").and_then(Value::as_str) else {
                continue;
            };
            let bounds = generic
                .get("bounds")
                .and_then(Value::as_array)
                .map(|bounds| bounds.iter().collect())
                .unwrap_or_default();
            specs.entry(name.to_owned()).or_insert(bounds);
        }
    }
    specs
}

fn generic_typevar_name(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    object: &serde_json::Map<String, Value>,
    name: &str,
    functions_only: bool,
) -> String {
    let mut signatures = BTreeSet::new();
    for declaration in &module.declarations {
        let Some(candidate) = declaration.as_object() else {
            continue;
        };
        if (functions_only && candidate.get("kind").and_then(Value::as_str) != Some("function"))
            || (!functions_only
                && candidate.get("kind").and_then(Value::as_str) == Some("function"))
        {
            continue;
        }
        for generic in candidate
            .get("generics")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter(|generic| generic.get("name").and_then(Value::as_str) == Some(name))
        {
            signatures
                .insert(serde_json::to_string(generic).expect("generic parameter serializes"));
        }
    }
    if signatures.len() <= 1 {
        return name.to_owned();
    }
    format!(
        "_cott_{}_{}",
        local_name(
            object
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or("generic")
        ),
        name
    )
}
fn associated_typevar_name(trait_name: &str, associated_name: &str) -> String {
    format!(
        "_cott_{}_{}",
        trait_name.replace('.', "_"),
        associated_name.replace('.', "_")
    )
}
fn associated_projection_typevar_name(object: &serde_json::Map<String, Value>) -> String {
    let trait_name = object
        .get("trait")
        .and_then(Value::as_str)
        .unwrap_or_default();
    let associated_name = object
        .get("name")
        .and_then(Value::as_str)
        .unwrap_or_default();
    let base_identity = serde_json::to_vec(
        object
            .get("base")
            .expect("validated associated projection base"),
    )
    .expect("canonical associated base serializes");
    format!(
        "{}_{}",
        associated_typevar_name(trait_name, associated_name),
        sha256_hex(&base_identity)
    )
}

fn collect_associated_projection_typevars(
    value: &Value,
    projections: &mut BTreeMap<String, (String, String)>,
) {
    if let Some(object) = value.as_object() {
        if object.get("kind").and_then(Value::as_str) == Some("associated_projection")
            && let (Some(trait_name), Some(associated_name)) = (
                object.get("trait").and_then(Value::as_str),
                object.get("name").and_then(Value::as_str),
            )
        {
            projections
                .entry(associated_projection_typevar_name(object))
                .or_insert_with(|| (trait_name.to_owned(), associated_name.to_owned()));
        }
        for value in object.values() {
            collect_associated_projection_typevars(value, projections);
        }
    } else if let Some(values) = value.as_array() {
        for value in values {
            collect_associated_projection_typevars(value, projections);
        }
    }
}

fn trait_declaration<'a>(
    modules: &'a BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    trait_name: &str,
) -> Option<&'a serde_json::Map<String, Value>> {
    modules
        .values()
        .flat_map(|module| &module.declarations)
        .filter_map(Value::as_object)
        .find(|declaration| {
            declaration.get("kind").and_then(Value::as_str) == Some("trait")
                && declaration.get("name").and_then(Value::as_str) == Some(trait_name)
        })
}

fn associated_type_bounds<'a>(
    modules: &'a BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    trait_name: &str,
    associated_name: &str,
) -> Vec<&'a Value> {
    trait_declaration(modules, trait_name)
        .and_then(|trait_declaration| trait_declaration.get("associated_types"))
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(Value::as_object)
        .find(|associated| {
            associated
                .get("name")
                .and_then(Value::as_str)
                .is_some_and(|name| {
                    name == associated_name || local_name(name) == local_name(associated_name)
                })
        })
        .and_then(|associated| associated.get("bounds"))
        .and_then(Value::as_array)
        .map(|bounds| bounds.iter().collect())
        .unwrap_or_default()
}

fn associated_projection_typevars(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
) -> BTreeMap<String, (String, String)> {
    let mut projections = BTreeMap::new();
    for declaration in &module.declarations {
        collect_associated_projection_typevars(declaration, &mut projections);
    }
    loop {
        let before = projections.len();
        for (trait_name, associated_name) in projections.values().cloned().collect::<Vec<_>>() {
            for bound in associated_type_bounds(modules, &trait_name, &associated_name) {
                collect_associated_projection_typevars(bound, &mut projections);
            }
        }
        if projections.len() == before {
            return projections;
        }
    }
}

fn render_typevar_bound(
    bound: &Value,
    module: &str,
    declarations: &BTreeMap<String, String>,
    typevar_names: Option<&BTreeMap<String, String>>,
) -> String {
    let rendered = typevar_names
        .map(|names| render_type_with_names(bound, module, declarations, names))
        .unwrap_or_else(|| render_type(bound, module, declarations));
    if let Some(name) = bound.get("name").and_then(Value::as_str)
        && bound.get("kind").and_then(Value::as_str) == Some("named")
        && name
            .rsplit_once('.')
            .is_some_and(|(source, _)| source == module)
        && declarations.contains_key(name)
    {
        return format!("ForwardRef({})", json_string(&rendered));
    }
    rendered
}
fn render_typevar_with_bounds(
    out: &mut String,
    module: &crate::python::artifact_plan::PythonArtifactModule,
    declarations: &BTreeMap<String, String>,
    typevar: &str,
    bounds: &[&Value],
) {
    match bounds {
        [] => writeln!(out, "{typevar} = TypeVar({})", json_string(typevar)).unwrap(),
        [bound] => writeln!(
            out,
            "{typevar} = TypeVar({}, bound={})",
            json_string(typevar),
            render_typevar_bound(bound, &module.module, declarations, None)
        )
        .unwrap(),
        _ => {
            render_bound_protocol(out, module, declarations, typevar, bounds);
            writeln!(
                out,
                "{typevar} = TypeVar({}, bound=_cott_{typevar}_Bounds)",
                json_string(typevar)
            )
            .unwrap();
        }
    }
}

fn render_associated_typevars(
    out: &mut String,
    module: &crate::python::artifact_plan::PythonArtifactModule,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    declarations: &BTreeMap<String, String>,
) -> bool {
    let mut rendered = false;
    for trait_declaration in module
        .declarations
        .iter()
        .filter_map(Value::as_object)
        .filter(|declaration| declaration.get("kind").and_then(Value::as_str) == Some("trait"))
    {
        let trait_name = trait_declaration
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or_default();
        for associated in trait_declaration
            .get("associated_types")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(Value::as_object)
        {
            let name = associated
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default();
            let bounds = associated
                .get("bounds")
                .and_then(Value::as_array)
                .map(|bounds| bounds.iter().collect::<Vec<_>>())
                .unwrap_or_default();
            render_typevar_with_bounds(
                out,
                module,
                declarations,
                &associated_typevar_name(trait_name, name),
                &bounds,
            );
            rendered = true;
        }
    }
    for (typevar, (trait_name, associated_name)) in associated_projection_typevars(module, modules)
    {
        let bounds = associated_type_bounds(modules, &trait_name, &associated_name);
        render_typevar_with_bounds(out, module, declarations, &typevar, &bounds);
        rendered = true;
    }
    rendered
}

fn associated_typevar_names(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
) -> Vec<String> {
    let mut names = module
        .declarations
        .iter()
        .filter_map(Value::as_object)
        .filter(|declaration| declaration.get("kind").and_then(Value::as_str) == Some("trait"))
        .flat_map(|trait_declaration| {
            let trait_name = trait_declaration
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default();
            trait_declaration
                .get("associated_types")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(|associated| associated.get("name").and_then(Value::as_str))
                .map(move |associated| associated_typevar_name(trait_name, associated))
        })
        .collect::<BTreeSet<_>>();
    names.extend(associated_projection_typevars(module, modules).into_keys());
    names.into_iter().collect()
}

fn generic_typevar_names(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    object: &serde_json::Map<String, Value>,
    functions_only: bool,
) -> BTreeMap<String, String> {
    object
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(|generic| {
            let name = generic.get("name").and_then(Value::as_str)?;
            Some((
                name.to_owned(),
                generic_typevar_name(module, object, name, functions_only),
            ))
        })
        .collect()
}

fn render_generic_typevars_for_declaration(
    out: &mut String,
    module: &crate::python::artifact_plan::PythonArtifactModule,
    declarations: &BTreeMap<String, String>,
    object: &serde_json::Map<String, Value>,
    functions_only: bool,
    render_composites: bool,
    render_protocols: bool,
    rendered: &mut BTreeSet<String>,
) {
    let typevar_names = generic_typevar_names(module, object, functions_only);
    for generic in object
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
    {
        let Some(name) = generic.get("name").and_then(Value::as_str) else {
            continue;
        };
        let bounds = generic
            .get("bounds")
            .and_then(Value::as_array)
            .map(|bounds| bounds.iter().collect::<Vec<_>>())
            .unwrap_or_default();
        let typevar = generic_typevar_name(module, object, name, functions_only);
        if !rendered.insert(typevar.clone()) {
            continue;
        }
        let variance = if matches!(
            object.get("kind").and_then(Value::as_str),
            Some("struct" | "enum" | "trait")
        ) && generic.get("kind").and_then(Value::as_str) == Some("type")
        {
            match generic.get("variance").and_then(Value::as_str) {
                Some("covariant") => ", covariant=True",
                Some("contravariant") => ", contravariant=True",
                _ => "",
            }
        } else {
            ""
        };
        if bounds.len() > 1 && render_composites && render_protocols {
            render_bound_protocol(out, module, declarations, &typevar, &bounds);
        }
        let declaration = match generic.get("kind").and_then(Value::as_str) {
            Some("const") => format!(
                ", bound={}",
                generic
                    .get("type")
                    .and_then(Value::as_str)
                    .map(render_const_generic_type)
                    .unwrap_or("int")
            ),
            Some("type") => match bounds.as_slice() {
                [bound] => format!(
                    "{variance}, bound={}",
                    if render_protocols {
                        render_typevar_bound(
                            bound,
                            &module.module,
                            declarations,
                            Some(&typevar_names),
                        )
                    } else {
                        render_type(bound, &module.module, declarations)
                    }
                ),
                [_first, ..] if render_composites => {
                    format!("{variance}, bound=_cott_{typevar}_Bounds")
                }
                _ => variance.to_owned(),
            },
            _ => String::new(),
        };
        writeln!(
            out,
            "{typevar} = TypeVar({}{declaration})",
            json_string(&typevar)
        )
        .unwrap();
    }
}

fn render_generic_typevars(
    out: &mut String,
    module: &crate::python::artifact_plan::PythonArtifactModule,
    declarations: &BTreeMap<String, String>,
    functions_only: bool,
    render_composites: bool,
) {
    let mut rendered = BTreeSet::new();
    for declaration in &module.declarations {
        let Some(object) = declaration.as_object() else {
            continue;
        };
        if (functions_only && object.get("kind").and_then(Value::as_str) != Some("function"))
            || (!functions_only && object.get("kind").and_then(Value::as_str) == Some("function"))
        {
            continue;
        }
        render_generic_typevars_for_declaration(
            out,
            module,
            declarations,
            object,
            functions_only,
            render_composites,
            false,
            &mut rendered,
        );
    }
}
fn render_bound_protocol(
    out: &mut String,
    module: &crate::python::artifact_plan::PythonArtifactModule,
    declarations: &BTreeMap<String, String>,
    typevar: &str,
    bounds: &[&Value],
) {
    let protocol = format!("_cott_{typevar}_Bounds");
    let bases = bounds
        .iter()
        .map(|bound| render_type(bound, &module.module, declarations))
        .chain(std::iter::once("Protocol".to_owned()))
        .collect::<Vec<_>>()
        .join(", ");
    writeln!(out, "class {protocol}({bases}):\n    pass\n").unwrap();
}

fn render_function_bound_protocols(
    out: &mut String,
    module: &crate::python::artifact_plan::PythonArtifactModule,
    declarations: &BTreeMap<String, String>,
) {
    let mut rendered = BTreeSet::new();
    for object in module.declarations.iter().filter_map(Value::as_object) {
        if object.get("kind").and_then(Value::as_str) != Some("function") {
            continue;
        }
        for generic in object
            .get("generics")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("type"))
        {
            let bounds = generic
                .get("bounds")
                .and_then(Value::as_array)
                .map(|bounds| bounds.iter().collect::<Vec<_>>())
                .unwrap_or_default();
            if bounds.len() <= 1 {
                continue;
            }
            let name = generic.get("name").and_then(Value::as_str).unwrap();
            let typevar = generic_typevar_name(module, object, name, true);
            if rendered.insert(typevar.clone()) {
                render_bound_protocol(out, module, declarations, &typevar, &bounds);
            }
        }
    }
}

fn function_bound_protocol_names(
    module: &crate::python::artifact_plan::PythonArtifactModule,
) -> Vec<String> {
    let mut names = BTreeSet::new();
    for object in module.declarations.iter().filter_map(Value::as_object) {
        if object.get("kind").and_then(Value::as_str) != Some("function") {
            continue;
        }
        for generic in object
            .get("generics")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("type"))
        {
            if generic
                .get("bounds")
                .and_then(Value::as_array)
                .is_none_or(|bounds| bounds.len() <= 1)
            {
                continue;
            }
            let name = generic.get("name").and_then(Value::as_str).unwrap();
            names.insert(format!(
                "_cott_{}_Bounds",
                generic_typevar_name(module, object, name, true)
            ));
        }
    }
    names.into_iter().collect()
}

fn render_private_defaults(
    out: &mut String,
    owner: &str,
    object: &serde_json::Map<String, Value>,
    module: &crate::python::artifact_plan::PythonArtifactModule,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    declarations: &BTreeMap<String, String>,
    typevar_names: &BTreeMap<String, String>,
) {
    for field in object
        .get("fields")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(Value::as_object)
    {
        let Some(value) = field.get("default").filter(|value| !value.is_null()) else {
            continue;
        };
        if python_default_hashable_type(field.get("type").unwrap(), modules, &mut BTreeSet::new()) {
            continue;
        }
        let field_name = local_name(
            field
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        );
        writeln!(
            out,
            "_cott_default_{owner}_{field_name}: Final[{}] = {}",
            render_type_with_names(
                field.get("type").unwrap(),
                &module.module,
                declarations,
                typevar_names,
            ),
            render_value(value),
        )
        .unwrap();
    }
}

fn render_fields(
    out: &mut String,
    object: &serde_json::Map<String, Value>,
    owner: &str,
    module: &crate::python::artifact_plan::PythonArtifactModule,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    declarations: &BTreeMap<String, String>,
    typevar_names: &BTreeMap<String, String>,
) {
    let fields = object.get("fields").and_then(Value::as_array).unwrap();
    if fields.is_empty() {
        out.push_str("    pass\n\n");
        return;
    }
    for field in fields {
        let field = field.as_object().unwrap();
        write!(
            out,
            "    {}: {}",
            local_name(
                field
                    .get("name")
                    .and_then(Value::as_str)
                    .unwrap_or_default()
            ),
            render_type_with_names(
                field.get("type").unwrap(),
                &module.module,
                declarations,
                typevar_names,
            )
        )
        .unwrap();
        if let Some(value) = field.get("default").filter(|value| !value.is_null()) {
            if python_default_hashable_type(
                field.get("type").unwrap(),
                modules,
                &mut BTreeSet::new(),
            ) {
                write!(out, " = {}", render_value(value)).unwrap();
            } else {
                let field_name = local_name(
                    field
                        .get("name")
                        .and_then(Value::as_str)
                        .unwrap_or_default(),
                );
                write!(
                    out,
                    " = _dataclasses.field(default_factory=lambda: _cott_default_{owner}_{field_name})"
                )
                .unwrap();
            }
        }
        out.push('\n');
    }
    out.push('\n');
}
fn type_uses_generic_const(value: &Value, generic_names: &BTreeSet<String>) -> bool {
    match value {
        Value::Array(values) => values
            .iter()
            .any(|value| type_uses_generic_const(value, generic_names)),
        Value::Object(object) => {
            (object.get("kind").and_then(Value::as_str) == Some("parameter")
                && object
                    .get("name")
                    .and_then(Value::as_str)
                    .is_some_and(|name| generic_names.contains(name)))
                || object
                    .values()
                    .any(|value| type_uses_generic_const(value, generic_names))
        }
        _ => false,
    }
}
fn render_struct_post_init(
    out: &mut String,
    object: &serde_json::Map<String, Value>,
    module: &str,
    declarations: &BTreeMap<String, String>,
    typevar_names: &BTreeMap<String, String>,
) {
    let fields = object.get("fields").and_then(Value::as_array).unwrap();
    let generic_names = object
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(|generic| generic.get("name").and_then(Value::as_str))
        .map(str::to_owned)
        .collect::<BTreeSet<_>>();
    let has_invariants = object
        .get("invariants")
        .and_then(Value::as_array)
        .is_some_and(|invariants| !invariants.is_empty());
    let has_normalized_fields = fields.iter().any(|field| {
        field
            .get("type")
            .is_some_and(|ty| !type_uses_generic_const(ty, &generic_names))
    });
    if !has_normalized_fields && !has_invariants {
        return;
    }
    out.push_str("    def __post_init__(self) -> None:\n");
    for field in fields {
        let field = field.as_object().expect("validated struct field");
        let name = local_name(
            field
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        );
        if type_uses_generic_const(
            field.get("type").expect("validated struct field type"),
            &generic_names,
        ) {
            continue;
        }
        let ty = render_type_with_names(
            field.get("type").expect("validated struct field type"),
            module,
            declarations,
            typevar_names,
        );
        writeln!(
            out,
            "        if not _cott_validated_construction():\n            object.__setattr__(self, {}, _cott_validate_abi(self.{name}, {ty}, path={}))",
            json_string(name),
            json_string(&format!("$.{name}")),
        )
        .unwrap();
    }
    render_invariants(
        out,
        object,
        object
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or_default(),
        8,
    );
    out.push('\n');
}
fn render_function_typevars(
    out: &mut String,
    module: &crate::python::artifact_plan::PythonArtifactModule,
    declarations: &BTreeMap<String, String>,
    render_composites: bool,
) {
    if generic_specs(module, true).is_empty() {
        return;
    }
    out.push('\n');
    render_generic_typevars(out, module, declarations, true, render_composites);
}
fn validate_impl_selections(
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    diagnostics: &mut Vec<EmitDiagnostic>,
) {
    for module in modules.values() {
        for implementation in module
            .declarations
            .iter()
            .filter_map(Value::as_object)
            .filter(|declaration| declaration.get("kind").and_then(Value::as_str) == Some("impl"))
        {
            let mut selected = BTreeMap::new();
            for slot in implementation
                .get("selected_methods")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                let Some(name) = slot
                    .get("trait_method")
                    .and_then(Value::as_str)
                    .map(local_name)
                else {
                    continue;
                };
                let Some(method) = resolve_impl_slot(implementation, slot, modules) else {
                    unsupported(
                        &module.module,
                        format!("selected implementation method `{name}` cannot be resolved"),
                        diagnostics,
                    );
                    continue;
                };
                if let Some(previous) = selected.insert(name.to_owned(), method.clone())
                    && !same_selected_method(&previous, &method)
                {
                    unsupported(
                        &module.module,
                        format!("selected implementation method `{name}` has conflicting slots"),
                        diagnostics,
                    );
                }
            }
        }
    }
}

fn same_selected_method(left: &Value, right: &Value) -> bool {
    [
        "selected",
        "callable_kind",
        "parameters",
        "return_type",
        "contract",
        "contracts",
        "effects",
        "modifies",
    ]
    .iter()
    .all(|field| left.get(*field) == right.get(*field))
}

fn resolved_impl_methods(
    implementation: &serde_json::Map<String, Value>,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
) -> Vec<Value> {
    let mut names = BTreeSet::new();
    implementation
        .get("selected_methods")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(|slot| {
            let name = slot
                .get("trait_method")
                .and_then(Value::as_str)
                .map(local_name)?;
            names
                .insert(name.to_owned())
                .then(|| resolve_impl_slot(implementation, slot, modules))
                .flatten()
        })
        .collect()
}

fn resolve_impl_slot(
    implementation: &serde_json::Map<String, Value>,
    slot: &Value,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
) -> Option<Value> {
    let trait_method = slot.get("trait_method")?.as_str()?;
    let method_name = local_name(trait_method);
    let selected = slot.get("selected")?.as_object()?;
    let mut method = match selected.get("origin")?.as_str()? {
        "explicit" => implementation
            .get("methods")?
            .as_array()?
            .iter()
            .find(|method| {
                method.get("name").and_then(Value::as_str).map(local_name) == Some(method_name)
            })?
            .clone(),
        "default" | "specialization" => resolve_trait_default(
            implementation,
            slot.get("trait_ref").and_then(Value::as_object),
            trait_method,
            selected,
            modules,
        )?,
        _ => return None,
    };
    let method = method.as_object_mut()?;
    method.insert("name".to_owned(), Value::String(method_name.to_owned()));
    method.insert(
        "callable_kind".to_owned(),
        slot.get("callable_kind")?.clone(),
    );
    method.insert("selected".to_owned(), Value::Object(selected.clone()));
    method.insert(
        "receiver_type".to_owned(),
        slot.get("receiver_type").cloned().unwrap_or(Value::Null),
    );
    method.insert(
        "trait_method".to_owned(),
        Value::String(trait_method.to_owned()),
    );
    if matches!(
        selected.get("origin").and_then(Value::as_str),
        Some("default" | "specialization")
    ) {
        let (contracts, effects) = default_method_contract(method);
        method.insert("contracts".to_owned(), contracts);
        method.insert("effects".to_owned(), effects);
        method.insert("modifies".to_owned(), json!([]));
    }
    let mut resolved = Value::Object(method.clone());
    substitute_associated_types(&mut resolved, implementation);
    Some(resolved)
}

fn default_method_contract(method: &serde_json::Map<String, Value>) -> (Value, Value) {
    let clauses = method
        .get("contract")
        .and_then(Value::as_object)
        .and_then(|contract| contract.get("clauses"))
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    let clauses_for = |kind| {
        clauses
            .iter()
            .filter(|clause| clause.get("kind").and_then(Value::as_str) == Some(kind))
            .cloned()
            .collect::<Vec<_>>()
    };
    (
        json!({
            "doc": method
                .get("doc")
                .and_then(Value::as_object)
                .and_then(|doc| doc.get("text"))
                .cloned()
                .unwrap_or(Value::Null),
            "requires": clauses_for("requires"),
            "errors": clauses_for("error"),
            "ensures": clauses_for("ensures"),
        }),
        method
            .get("contract")
            .and_then(Value::as_object)
            .and_then(|contract| contract.get("effects"))
            .cloned()
            .unwrap_or_else(|| json!([])),
    )
}

fn resolve_trait_default(
    implementation: &serde_json::Map<String, Value>,
    slot_trait_ref: Option<&serde_json::Map<String, Value>>,
    trait_method: &str,
    selected: &serde_json::Map<String, Value>,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
) -> Option<Value> {
    let (trait_name, method_name) = trait_method.rsplit_once('.')?;
    let trait_declaration = modules
        .values()
        .flat_map(|module| &module.declarations)
        .filter_map(Value::as_object)
        .find(|declaration| {
            declaration.get("kind").and_then(Value::as_str) == Some("trait")
                && declaration.get("name").and_then(Value::as_str) == Some(trait_name)
        })?;
    let trait_ref = slot_trait_ref.or_else(|| {
        implementation
            .get("traits")?
            .as_array()?
            .iter()
            .filter_map(Value::as_object)
            .find(|trait_ref| {
                trait_ref.get("kind").and_then(Value::as_str) == Some("named")
                    && trait_ref.get("name").and_then(Value::as_str) == Some(trait_name)
            })
    })?;
    let mut method = trait_declaration
        .get("methods")?
        .as_array()?
        .iter()
        .find(|method| {
            method.get("name").and_then(Value::as_str).map(local_name) == Some(method_name)
        })?
        .clone();
    (selected.get("origin").and_then(Value::as_str) == Some("specialization")
        || method.get("default")? == selected.get("function")?)
    .then_some(())?;
    substitute_trait_arguments(&mut method, trait_declaration, trait_ref);
    Some(method)
}

fn substitute_trait_arguments(
    value: &mut Value,
    trait_declaration: &serde_json::Map<String, Value>,
    trait_ref: &serde_json::Map<String, Value>,
) {
    let mut types = BTreeMap::new();
    let mut constants = BTreeMap::new();
    for (parameter, argument) in trait_declaration
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(Value::as_object)
        .zip(
            trait_ref
                .get("args")
                .and_then(Value::as_array)
                .into_iter()
                .flatten(),
        )
    {
        let Some(name) = parameter.get("name").and_then(Value::as_str) else {
            continue;
        };
        match parameter.get("kind").and_then(Value::as_str) {
            Some("type") => {
                if let Some(argument) = argument.get("type") {
                    types.insert(name.to_owned(), argument.clone());
                }
            }
            Some("const") => {
                if let Some(argument) = argument.get("value") {
                    constants.insert(name.to_owned(), argument.clone());
                }
            }
            _ => {}
        }
    }
    substitute_generic_arguments(value, &types, &constants);
}

fn substitute_generic_arguments(
    value: &mut Value,
    types: &BTreeMap<String, Value>,
    constants: &BTreeMap<String, Value>,
) {
    let replacement = value.as_object().and_then(|object| {
        match (
            object.get("kind").and_then(Value::as_str),
            object.get("name").and_then(Value::as_str),
        ) {
            (Some("type_parameter"), Some(name)) => types.get(name).cloned(),
            (Some("parameter"), Some(name)) => constants.get(name).cloned(),
            _ => None,
        }
    });
    if let Some(replacement) = replacement {
        *value = replacement;
        return;
    }
    match value {
        Value::Array(values) => {
            for value in values {
                substitute_generic_arguments(value, types, constants);
            }
        }
        Value::Object(object) => {
            for value in object.values_mut() {
                substitute_generic_arguments(value, types, constants);
            }
        }
        _ => {}
    }
}
fn substitute_associated_types(value: &mut Value, implementation: &serde_json::Map<String, Value>) {
    let replacement = value.as_object().and_then(|projection| {
        (projection.get("kind").and_then(Value::as_str) == Some("associated_projection")).then(
            || {
                let trait_name = projection.get("trait").and_then(Value::as_str)?;
                let name = projection.get("name").and_then(Value::as_str)?;
                implementation
                    .get("associated_types")?
                    .as_array()?
                    .iter()
                    .filter_map(Value::as_object)
                    .find(|assignment| {
                        assignment.get("trait").and_then(Value::as_str) == Some(trait_name)
                            && assignment
                                .get("name")
                                .and_then(Value::as_str)
                                .map(local_name)
                                == Some(local_name(name))
                    })?
                    .get("type")
                    .cloned()
            },
        )?
    });
    if let Some(replacement) = replacement {
        *value = replacement;
        return;
    }
    match value {
        Value::Array(values) => {
            for value in values {
                substitute_associated_types(value, implementation);
            }
        }
        Value::Object(object) => {
            for value in object.values_mut() {
                substitute_associated_types(value, implementation);
            }
        }
        _ => {}
    }
}
fn default_dispatch<'a>(
    method: &'a serde_json::Map<String, Value>,
) -> Option<&'a serde_json::Map<String, Value>> {
    method
        .get("selected")
        .and_then(Value::as_object)
        .filter(|selected| {
            matches!(
                selected.get("origin").and_then(Value::as_str),
                Some("default" | "specialization")
            )
        })
        .and_then(|selected| selected.get("function"))
        .and_then(Value::as_object)
}

fn default_alias(implementation: &str, method: &str) -> String {
    format!("_cott_default_{implementation}_{method}")
}

fn default_dispatch_resolved(
    function: &serde_json::Map<String, Value>,
    callable_kind: &str,
    bindings: &[ResolvedBinding],
) -> bool {
    let Some(module) = function.get("module").and_then(Value::as_str) else {
        return false;
    };
    let Some(symbol) = function.get("symbol").and_then(Value::as_str) else {
        return false;
    };
    bindings.iter().any(|binding| {
        binding.module == module
            && binding.function == symbol
            && matches!(
                (&binding.kind, callable_kind),
                (PythonCallableKind::Function, "sync")
                    | (PythonCallableKind::AsyncFunction, "async")
            )
    })
}
fn resolved_method_imports(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    declarations: &BTreeMap<String, String>,
) -> BTreeMap<String, BTreeSet<String>> {
    let mut imports = BTreeMap::new();
    for implementation in module
        .declarations
        .iter()
        .filter_map(Value::as_object)
        .filter(|declaration| declaration.get("kind").and_then(Value::as_str) == Some("impl"))
    {
        for method in resolved_impl_methods(implementation, modules) {
            for parameter in method
                .get("parameters")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                if let Some(ty) = parameter.get("type") {
                    collect_named(ty, &module.module, declarations, &mut imports);
                }
            }
            if let Some(ty) = method.get("return_type") {
                collect_named(ty, &module.module, declarations, &mut imports);
            }
            for transition in method
                .get("transitions")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                for state in ["from", "to"] {
                    if let Some(symbol) = transition.get(state).and_then(Value::as_str) {
                        collect_symbol(symbol, &module.module, declarations, &mut imports, true);
                    }
                }
            }
        }
    }
    imports
}
fn resolved_factory_imports(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    declarations: &BTreeMap<String, String>,
) -> BTreeMap<String, BTreeSet<String>> {
    let mut imports = BTreeMap::new();
    for implementation in module
        .declarations
        .iter()
        .filter_map(Value::as_object)
        .filter(|declaration| declaration.get("kind").and_then(Value::as_str) == Some("impl"))
    {
        for method in resolved_impl_methods(implementation, modules) {
            collect_factory_concrete_imports(&method, &module.module, declarations, &mut imports);
        }
    }
    imports
}

fn render_default_aliases(
    out: &mut String,
    module: &crate::python::artifact_plan::PythonArtifactModule,
    bindings: &[ResolvedBinding],
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
) {
    for implementation in module
        .declarations
        .iter()
        .filter_map(Value::as_object)
        .filter(|declaration| declaration.get("kind").and_then(Value::as_str) == Some("impl"))
    {
        let implementation_name = local_name(
            implementation
                .get("name")
                .and_then(Value::as_str)
                .expect("validated implementation name"),
        );
        for method in resolved_impl_methods(implementation, modules)
            .iter()
            .filter_map(Value::as_object)
        {
            let Some(function) = default_dispatch(method) else {
                continue;
            };
            if !default_dispatch_resolved(
                function,
                method
                    .get("callable_kind")
                    .and_then(Value::as_str)
                    .expect("validated default callable_kind"),
                bindings,
            ) {
                continue;
            }
            let target_module = function
                .get("module")
                .and_then(Value::as_str)
                .expect("validated default module");
            let target_symbol = function
                .get("symbol")
                .and_then(Value::as_str)
                .expect("validated default symbol");
            let method_name = method
                .get("name")
                .and_then(Value::as_str)
                .expect("validated implementation method name");
            let alias = default_alias(implementation_name, method_name);
            if target_module == module.module {
                writeln!(out, "\n{alias} = {target_symbol}").unwrap();
            } else {
                writeln!(
                    out,
                    "\nfrom {target_module} import {target_symbol} as {alias}"
                )
                .unwrap();
            }
        }
    }
}

fn render_facade(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    bindings: &[ResolvedBinding],
    declarations: &BTreeMap<String, String>,
    config: &ProjectConfig,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
) -> Vec<u8> {
    let mut out = String::from(
        "from __future__ import annotations\n\nfrom collections.abc import Generator, Iterator\nimport asyncio as _asyncio\nimport dataclasses as _dataclasses\nimport threading as _threading\nfrom pathlib import Path\nfrom typing import Any, Literal, Never, Protocol, TypeVar, final\n\nfrom cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol\n",
    );
    let names = exported_names(module);
    let mut local_imports = type_exported_names(module);
    local_imports.extend(function_bound_protocol_names(module));
    local_imports.extend(associated_typevar_names(module, modules));
    if !local_imports.is_empty() {
        writeln!(
            out,
            "\nfrom {} import {}",
            type_module_name(&module.module),
            local_imports.join(", ")
        )
        .unwrap();
    }
    let mut imports = referenced_imports(module, modules, declarations);
    for (source, names) in resolved_method_imports(module, modules, declarations) {
        imports.entry(source).or_default().extend(names);
    }
    for (source, names) in concrete_trait_marker_imports(module, modules) {
        imports.entry(source).or_default().extend(names);
    }
    for (source, names) in imports {
        writeln!(
            out,
            "from {} import {}",
            type_module_name(&source),
            names.into_iter().collect::<Vec<_>>().join(", ")
        )
        .unwrap();
    }
    let mut factory_imports = factory_concrete_imports(module, declarations);
    for (source, names) in resolved_factory_imports(module, modules, declarations) {
        factory_imports.entry(source).or_default().extend(names);
    }
    for (source, names) in factory_imports {
        writeln!(
            out,
            "from {source} import {}",
            names.into_iter().collect::<Vec<_>>().join(", ")
        )
        .unwrap();
    }
    render_function_typevars(&mut out, module, declarations, true);
    let boundary = config.python.runtime_validation == RuntimeValidation::Boundary;
    let test_only = config.python.runtime_validation == RuntimeValidation::TestOnly;
    if test_only {
        out.push_str(
            "\n_cott_test_context = False\n\ndef _cott_set_test_context(active: bool) -> None:\n    global _cott_test_context\n    _cott_test_context = active\n",
        );
    }
    let mut exported = names;
    for declaration in &module.declarations {
        let object = declaration.as_object().unwrap();
        if object.get("kind").and_then(Value::as_str) != Some("function") {
            continue;
        }
        let function = local_name(
            object
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        );
        let cott_symbol = object
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or_default();
        let function_span =
            serde_json::to_string(object.get("span").unwrap()).expect("span serializes");
        let Some(binding) = bindings.iter().find(|binding| {
            binding.module == module.module && local_name(&binding.function) == function
        }) else {
            continue;
        };
        let typevar_names = generic_typevar_names(module, object, true);
        let (signature, call, parameters) = render_function_parameters_with_names(
            object,
            &module.module,
            declarations,
            &typevar_names,
        );
        let return_type = render_type_with_names(
            object.get("return_type").unwrap(),
            &module.module,
            declarations,
            &typevar_names,
        );
        let asynchronous = object.get("callable_kind").and_then(Value::as_str) == Some("async");
        writeln!(
            out,
            "\n{}def {function}({signature}) -> {return_type}:",
            if asynchronous { "async " } else { "" }
        )
        .unwrap();
        render_indented_doc(&mut out, object.get("doc"));
        for (name, ty) in &parameters {
            let path = json_string(&format!("$.{name}"));
            if boundary {
                writeln!(
                    out,
                    "    {name} = _cott_validate_abi({name}, {ty}, path={path})"
                )
                .unwrap();
            } else {
                writeln!(
                    out,
                    "    {name} = _cott_normalize_f32_abi({name}, {ty}, path={path})"
                )
                .unwrap();
            }
        }
        if boundary {
            render_preconditions(&mut out, object, function);
        } else if test_only {
            render_test_only_contract(&mut out, object, function, true);
        }
        let never = object
            .get("return_type")
            .and_then(Value::as_object)
            .is_some_and(|ty| {
                ty.get("kind").and_then(Value::as_str) == Some("primitive")
                    && ty.get("name").and_then(Value::as_str) == Some("never")
            });
        let allows_exit = never
            && object
                .get("contract")
                .and_then(Value::as_object)
                .and_then(|contract| contract.get("effects"))
                .and_then(Value::as_array)
                .is_some_and(|effects| {
                    effects.iter().any(|effect| {
                        effect.get("key").and_then(Value::as_str) == Some("process.exit")
                    })
                });
        out.push_str("    try:\n");
        writeln!(
            out,
            "        _implementation = _cott_load({}, {}, {}, expected_project_name={}, expected_cott_symbol={})",
            json_string(&path_string(&binding.generated_relative)),
            json_string(&binding.sha256),
            json_string(&binding.implementation_function),
            json_string(&config.project.name),
            json_string(&format!("{}.{}", module.module, function)),
        )
        .unwrap();
        writeln!(
            out,
            "        _result = {}_implementation({call})",
            if asynchronous { "await " } else { "" }
        )
        .unwrap();
        writeln!(
            out,
            "    except CottContractViolation as _error:\n        if _error.symbol is None or _error.symbol == \"_cott_load\":\n            _error.symbol = {}\n        if _error.span is None:\n            _error.span = {function_span}\n        raise",
            json_string(cott_symbol),
        )
        .unwrap();
        if allows_exit {
            out.push_str("    except SystemExit:\n        raise\n");
        } else {
            writeln!(
                out,
                "    except SystemExit as _error:\n        raise CottContractViolation(\"implementation raised SystemExit\", symbol={}, phase=\"implementation-call\", span={function_span}, expected=\"ordinary return or declared Never process.exit\", actual=\"SystemExit\") from _error",
                json_string(cott_symbol),
            )
            .unwrap();
        }
        writeln!(
            out,
            "    except Exception as _error:\n        raise CottContractViolation(\"implementation raised an undeclared exception\", symbol={}, phase=\"implementation-call\", span={function_span}, expected=\"declared Result error or ordinary return\", actual=type(_error).__name__) from _error",
            json_string(cott_symbol),
        )
        .unwrap();
        if never {
            writeln!(
                out,
                "    raise CottContractViolation(\"Never function returned\", symbol={}, phase=\"return\", span={function_span}, expected=\"Never\", actual=repr(_result))",
                json_string(cott_symbol),
            )
            .unwrap();
        } else {
            if boundary {
                writeln!(
                    out,
                    "    _result = _cott_validate_abi(_result, {return_type}, path=\"$.return\")"
                )
                .unwrap();
                render_postconditions(&mut out, object, function);
            } else if test_only {
                writeln!(
                    out,
                    "    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, {return_type}, path=\"$.return\")"
                )
                .unwrap();
                render_test_only_contract(&mut out, object, function, false);
            } else {
                writeln!(
                    out,
                    "    _result = _cott_normalize_f32_abi(_result, {return_type}, path=\"$.return\")"
                )
                .unwrap();
            }
            writeln!(
                out,
                "    _result = _cott_wrap_async_protocol(_result, {return_type}, path=\"$.return\", validator={})",
                async_protocol_validator(boundary, test_only),
            )
            .unwrap();
            out.push_str("    return _result\n");
        }
        if object
            .get("public")
            .and_then(Value::as_bool)
            .unwrap_or(false)
        {
            exported.push(function.to_owned());
        }
    }
    render_default_aliases(&mut out, module, bindings, modules);
    render_impl_classes(
        &mut out,
        module,
        bindings,
        declarations,
        config,
        modules,
        boundary,
        test_only,
    );
    exported.sort();
    writeln!(
        out,
        "\n__all__ = [{}]",
        exported
            .iter()
            .map(|name| json_string(name))
            .collect::<Vec<_>>()
            .join(", ")
    )
    .unwrap();
    out.into_bytes()
}

fn concrete_trait_marker_names(
    implementation: &serde_json::Map<String, Value>,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
) -> BTreeSet<String> {
    let mut names = BTreeSet::new();
    for trait_name in implementation
        .get("traits")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(|trait_ref| trait_ref.get("name").and_then(Value::as_str))
    {
        names.insert(trait_name.to_owned());
        if let Some(closure) = trait_declaration(modules, trait_name)
            .and_then(|trait_declaration| trait_declaration.get("closure"))
            .and_then(Value::as_array)
        {
            names.extend(
                closure
                    .iter()
                    .filter_map(|trait_ref| trait_ref.get("name").and_then(Value::as_str))
                    .map(str::to_owned),
            );
        }
    }
    names
}

fn concrete_trait_markers(
    implementation: &serde_json::Map<String, Value>,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
) -> BTreeSet<String> {
    concrete_trait_marker_names(implementation, modules)
        .into_iter()
        .map(|name| local_name(&name).to_owned())
        .collect()
}

fn concrete_trait_marker_imports(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
) -> BTreeMap<String, BTreeSet<String>> {
    let mut imports = BTreeMap::<String, BTreeSet<String>>::new();
    for implementation in module
        .declarations
        .iter()
        .filter_map(Value::as_object)
        .filter(|declaration| declaration.get("kind").and_then(Value::as_str) == Some("impl"))
    {
        for name in concrete_trait_marker_names(implementation, modules) {
            if let Some((source, local)) = name.rsplit_once('.')
                && source != module.module
            {
                imports
                    .entry(source.to_owned())
                    .or_default()
                    .insert(local.to_owned());
            }
        }
    }
    imports
}

fn render_impl_classes(
    out: &mut String,
    module: &crate::python::artifact_plan::PythonArtifactModule,
    bindings: &[ResolvedBinding],
    declarations: &BTreeMap<String, String>,
    config: &ProjectConfig,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    boundary: bool,
    test_only: bool,
) {
    for declaration in &module.declarations {
        let Some(implementation) = declaration
            .as_object()
            .filter(|object| object.get("kind").and_then(Value::as_str) == Some("impl"))
        else {
            continue;
        };
        let name = local_name(
            implementation
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        );
        let state = implementation
            .get("state")
            .and_then(Value::as_array)
            .map(Vec::as_slice)
            .unwrap_or_default();
        let async_impl = implementation
            .get("selected_methods")
            .and_then(Value::as_array)
            .and_then(|methods| methods.first())
            .and_then(|method| method.get("callable_kind"))
            .and_then(Value::as_str)
            == Some("async");
        writeln!(out, "\n@final\nclass {name}:").unwrap();
        let traits = concrete_trait_markers(implementation, modules);
        let traits = if traits.is_empty() {
            "()".to_owned()
        } else {
            format!("({},)", traits.into_iter().collect::<Vec<_>>().join(", "))
        };
        writeln!(out, "    _cott_traits = {traits}").unwrap();
        let mut trait_specs = BTreeSet::new();
        for trait_ref in implementation
            .get("traits")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
        {
            trait_specs.insert(render_type(trait_ref, &module.module, declarations));
            if let (Some(name), Some(trait_ref_object)) = (
                trait_ref.get("name").and_then(Value::as_str),
                trait_ref.as_object(),
            ) && let Some(trait_declaration) = trait_declaration(modules, name)
                && let Some(closure) = trait_declaration.get("closure").and_then(Value::as_array)
            {
                for closure_ref in closure {
                    let mut closure_ref = closure_ref.clone();
                    substitute_trait_arguments(
                        &mut closure_ref,
                        trait_declaration,
                        trait_ref_object,
                    );
                    trait_specs.insert(render_type(&closure_ref, &module.module, declarations));
                }
            }
        }
        let trait_specs = if trait_specs.is_empty() {
            "()".to_owned()
        } else {
            format!(
                "({},)",
                trait_specs.into_iter().collect::<Vec<_>>().join(", ")
            )
        };
        writeln!(out, "    _cott_trait_specs = {trait_specs}").unwrap();
        let slots = state
            .iter()
            .filter_map(|field| field.get("name").and_then(Value::as_str))
            .chain(std::iter::once("_cott_lock"))
            .map(json_string)
            .collect::<Vec<_>>()
            .join(", ");
        for field in state {
            let field = field.as_object().expect("validated impl state field");
            let field_name = field
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default();
            let ty = render_type(field.get("type").unwrap(), &module.module, declarations);
            writeln!(out, "    {field_name}: {ty}").unwrap();
        }
        writeln!(out, "    __slots__ = ({slots},)").unwrap();
        writeln!(
            out,
            "\n    def __init_subclass__(cls, **_kwargs: object) -> None:\n        raise TypeError({})",
            json_string(&format!("{name} is final"))
        )
        .unwrap();

        let init = implementation.get("init").and_then(Value::as_object);
        let init_parameters = init
            .and_then(|init| init.get("parameters"))
            .and_then(Value::as_array)
            .map(Vec::as_slice)
            .unwrap_or_default();
        let (signature, _, parameters) =
            render_impl_parameters(init_parameters, &module.module, declarations);
        let signature = if signature.is_empty() {
            "self".to_owned()
        } else {
            format!("self, {signature}")
        };
        writeln!(out, "\n    def __init__({signature}) -> None:").unwrap();
        if let Some(doc) = init
            .and_then(|init| init.get("contracts"))
            .and_then(Value::as_object)
            .and_then(|contracts| contracts.get("doc"))
            .and_then(Value::as_str)
        {
            writeln!(
                out,
                "        \"\"\"{}\"\"\"",
                doc.replace('\\', "\\\\").replace("\"\"\"", "\\\"\\\"\\\"")
            )
            .unwrap();
        }
        for (parameter, ty) in &parameters {
            render_abi_assignment(out, parameter, ty, 8, boundary, test_only);
        }
        if let Some(init) = init {
            let contract =
                impl_contract_callable(init, &format!("{}.{}", module.module, name), false);
            render_contract_block(out, &contract, true, boundary, test_only, 4);
        }
        for field in state {
            let field = field.as_object().expect("validated impl state field");
            let field_name = field
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default();
            let ty = render_type(field.get("type").unwrap(), &module.module, declarations);
            let value = if parameters
                .iter()
                .any(|(parameter, _)| parameter == field_name)
            {
                field_name.to_owned()
            } else {
                render_value(
                    field
                        .get("default")
                        .expect("state without init parameter has default"),
                )
            };
            writeln!(
                out,
                "        self.{field_name} = _cott_validate_abi({value}, {ty}, path={})",
                json_string(&format!("$.{field_name}"))
            )
            .unwrap();
        }
        out.push_str(if async_impl {
            "        self._cott_lock = _CottAsyncRLock()\n"
        } else {
            "        self._cott_lock = _threading.RLock()\n"
        });
        if let Some(init) = init {
            let contract =
                impl_contract_callable(init, &format!("{}.{}", module.module, name), false);
            render_contract_block(out, &contract, false, boundary, test_only, 4);
        }
        render_invariants(
            out,
            implementation,
            &format!("{}.{}", module.module, name),
            8,
        );

        for method in resolved_impl_methods(implementation, modules)
            .iter()
            .filter_map(Value::as_object)
        {
            let method_name = method
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default();
            let cott_symbol = format!("{}.{}.{}", module.module, name, method_name);
            let default = default_dispatch(method);
            let binding = bindings
                .iter()
                .find(|binding| binding.cott_symbol == cott_symbol);
            if (default.is_none() && binding.is_none())
                || default.is_some_and(|function| {
                    !default_dispatch_resolved(
                        function,
                        method
                            .get("callable_kind")
                            .and_then(Value::as_str)
                            .expect("validated default callable_kind"),
                        bindings,
                    )
                })
            {
                continue;
            }
            let (signature, call, parameters) = render_impl_parameters(
                method
                    .get("parameters")
                    .and_then(Value::as_array)
                    .map(Vec::as_slice)
                    .unwrap_or_default(),
                &module.module,
                declarations,
            );
            let signature = if signature.is_empty() {
                format!("self: {name}")
            } else {
                format!("self: {name}, {signature}")
            };
            let return_type = render_type(
                method.get("return_type").unwrap(),
                &module.module,
                declarations,
            );
            let asynchronous = method.get("callable_kind").and_then(Value::as_str) == Some("async");
            writeln!(
                out,
                "\n    {}def {method_name}({signature}) -> {return_type}:",
                if asynchronous { "async " } else { "" }
            )
            .unwrap();
            if let Some(doc) = method
                .get("contracts")
                .and_then(Value::as_object)
                .and_then(|contracts| contracts.get("doc"))
                .and_then(Value::as_str)
            {
                writeln!(
                    out,
                    "        \"\"\"{}\"\"\"",
                    doc.replace('\\', "\\\\").replace("\"\"\"", "\\\"\\\"\\\"")
                )
                .unwrap();
            }
            out.push_str(if asynchronous {
                "        async with self._cott_lock:\n"
            } else {
                "        with self._cott_lock:\n"
            });
            for field in state {
                let field_name = field
                    .get("name")
                    .and_then(Value::as_str)
                    .unwrap_or_default();
                writeln!(
                    out,
                    "            _cott_old_{field_name} = self.{field_name}"
                )
                .unwrap();
            }
            for (parameter, ty) in &parameters {
                render_abi_assignment(out, parameter, ty, 12, boundary, test_only);
            }
            let contract = impl_contract_callable(method, &cott_symbol, true);
            render_contract_block(out, &contract, true, boundary, test_only, 8);
            let span = serde_json::to_string(method.get("span").unwrap()).expect("span serializes");
            out.push_str("            try:\n");
            if default.is_some() {
                let alias = default_alias(name, method_name);
                writeln!(
                    out,
                    "                _result = {}{alias}(self{}{})",
                    if asynchronous { "await " } else { "" },
                    if call.is_empty() { "" } else { ", " },
                    call
                )
                .unwrap();
            } else {
                let binding = binding.expect("explicit implementation has a verified binding");
                writeln!(
                    out,
                    "                _implementation = _cott_load({}, {}, {}, expected_project_name={}, expected_cott_symbol={})",
                    json_string(&path_string(&binding.generated_relative)),
                    json_string(&binding.sha256),
                    json_string(&binding.implementation_function),
                    json_string(&config.project.name),
                    json_string(&cott_symbol),
                )
                .unwrap();
                writeln!(
                    out,
                    "                _result = {}_implementation(self{}{})",
                    if asynchronous { "await " } else { "" },
                    if call.is_empty() { "" } else { ", " },
                    call
                )
                .unwrap();
            }
            if asynchronous {
                out.push_str("            except BaseException as _error:\n");
                render_async_exception_finalization(
                    out,
                    state,
                    method,
                    implementation,
                    module,
                    declarations,
                    &cott_symbol,
                    &span,
                    name,
                );
                writeln!(
                    out,
                    "                if isinstance(_error, _asyncio.CancelledError):\n                    raise\n                if isinstance(_error, CottContractViolation):\n                    if _error.symbol is None or _error.symbol == \"_cott_load\":\n                        _error.symbol = {}\n                    if _error.span is None:\n                        _error.span = {span}\n                    raise\n                if isinstance(_error, SystemExit):\n                    raise CottContractViolation(\"implementation raised SystemExit\", symbol={}, phase=\"implementation-call\", span={span}, expected=\"ordinary return\", actual=\"SystemExit\") from _error\n                if isinstance(_error, Exception):\n                    raise CottContractViolation(\"implementation raised an undeclared exception\", symbol={}, phase=\"implementation-call\", span={span}, expected=\"declared Result error or ordinary return\", actual=type(_error).__name__) from _error\n                raise",
                    json_string(&cott_symbol),
                    json_string(&cott_symbol),
                    json_string(&cott_symbol),
                )
                .unwrap();
            } else {
                writeln!(
                    out,
                    "            except CottContractViolation as _error:\n                if _error.symbol is None or _error.symbol == \"_cott_load\":\n                    _error.symbol = {}\n                if _error.span is None:\n                    _error.span = {span}\n                raise",
                    json_string(&cott_symbol),
                )
                .unwrap();
                writeln!(
                    out,
                    "            except SystemExit as _error:\n                raise CottContractViolation(\"implementation raised SystemExit\", symbol={}, phase=\"implementation-call\", span={span}, expected=\"ordinary return\", actual=\"SystemExit\") from _error",
                    json_string(&cott_symbol),
                )
                .unwrap();
                writeln!(
                    out,
                    "            except Exception as _error:\n                raise CottContractViolation(\"implementation raised an undeclared exception\", symbol={}, phase=\"implementation-call\", span={span}, expected=\"declared Result error or ordinary return\", actual=type(_error).__name__) from _error",
                    json_string(&cott_symbol),
                )
                .unwrap();
            }
            let never = is_never(method.get("return_type"));
            if !never {
                render_abi_assignment(out, "_result", &return_type, 12, boundary, test_only);
            }
            for field in state {
                let field_name = field
                    .get("name")
                    .and_then(Value::as_str)
                    .unwrap_or_default();
                let ty = render_type(field.get("type").unwrap(), &module.module, declarations);
                writeln!(
                    out,
                    "            self.{field_name} = _cott_validate_abi(self.{field_name}, {ty}, path={})",
                    json_string(&format!("$.{field_name}"))
                )
                .unwrap();
            }
            let transitions = method
                .get("transitions")
                .and_then(Value::as_array)
                .map(Vec::as_slice)
                .unwrap_or_default();
            for transition in transitions {
                let field_name = local_name(
                    transition
                        .get("field")
                        .and_then(Value::as_str)
                        .unwrap_or_default(),
                );
                let from = enum_variant_name(
                    transition
                        .get("from")
                        .and_then(Value::as_str)
                        .unwrap_or_default(),
                );
                let to = enum_variant_name(
                    transition
                        .get("to")
                        .and_then(Value::as_str)
                        .unwrap_or_default(),
                );
                writeln!(
                    out,
                    "            if _cott_old_{field_name} is not {from}():\n                raise CottContractViolation(\"resource transition source failed\", symbol={}, phase=\"transitions\", span={span}, expected={}, actual=repr(_cott_old_{field_name}))\n            if self.{field_name} is not {to}():\n                raise CottContractViolation(\"resource transition target failed\", symbol={}, phase=\"transitions\", span={span}, expected={}, actual=repr(self.{field_name}))",
                    json_string(&cott_symbol),
                    json_string(&format!("self.{field_name} is {from}")),
                    json_string(&cott_symbol),
                    json_string(&format!("self.{field_name} is {to}")),
                )
                .unwrap();
            }
            let modifies = method
                .get("modifies")
                .and_then(Value::as_array)
                .map(Vec::as_slice)
                .unwrap_or_default();
            for field in state {
                let field_name = field
                    .get("name")
                    .and_then(Value::as_str)
                    .unwrap_or_default();
                if modifies
                    .iter()
                    .chain(
                        transitions
                            .iter()
                            .map(|transition| transition.get("field").unwrap()),
                    )
                    .any(|value| local_name(value.as_str().unwrap_or_default()) == field_name)
                {
                    continue;
                }
                writeln!(
                    out,
                    "            if self.{field_name} is not _cott_old_{field_name}:\n                raise CottContractViolation(\"modifies clause failed\", symbol={}, phase=\"modifies\", span={span}, expected={}, actual={})",
                    json_string(&cott_symbol),
                    json_string(&format!("self.{field_name} unchanged")),
                    json_string(&format!("self.{field_name} changed")),
                )
                .unwrap();
            }
            if never {
                render_invariants(
                    out,
                    implementation,
                    &format!("{}.{}", module.module, name),
                    12,
                );
                writeln!(
                    out,
                    "            raise CottContractViolation(\"Never function returned\", symbol={}, phase=\"return\", span={span}, expected=\"Never\", actual=repr(_result))",
                    json_string(&cott_symbol)
                )
                .unwrap();
                continue;
            }
            render_contract_block(out, &contract, false, boundary, test_only, 8);
            render_invariants(
                out,
                implementation,
                &format!("{}.{}", module.module, name),
                12,
            );
            writeln!(
                out,
                "            _result = _cott_wrap_async_protocol(_result, {return_type}, path=\"$.return\", validator={})",
                async_protocol_validator(boundary, test_only),
            )
            .unwrap();
            out.push_str("            return _result\n");
        }
    }
}

fn render_async_exception_finalization(
    out: &mut String,
    state: &[Value],
    method: &serde_json::Map<String, Value>,
    implementation: &serde_json::Map<String, Value>,
    module: &crate::python::artifact_plan::PythonArtifactModule,
    declarations: &BTreeMap<String, String>,
    cott_symbol: &str,
    span: &str,
    concrete: &str,
) {
    for field in state {
        let field_name = field
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or_default();
        let ty = render_type(field.get("type").unwrap(), &module.module, declarations);
        writeln!(
            out,
            "                self.{field_name} = _cott_validate_abi(self.{field_name}, {ty}, path={})",
            json_string(&format!("$.{field_name}"))
        )
        .unwrap();
    }
    let transitions = method
        .get("transitions")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default();
    for transition in transitions {
        let field_name = local_name(
            transition
                .get("field")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        );
        let from = enum_variant_name(
            transition
                .get("from")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        );
        let to = enum_variant_name(
            transition
                .get("to")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        );
        writeln!(
            out,
            "                if _cott_old_{field_name} is not {from}():\n                    raise CottContractViolation(\"exceptional resource transition source failed\", symbol={}, phase=\"exceptional-transitions\", span={span}, expected={}, actual=repr(_cott_old_{field_name}))\n                if self.{field_name} is not _cott_old_{field_name} and self.{field_name} is not {to}():\n                    raise CottContractViolation(\"exceptional resource transition target failed\", symbol={}, phase=\"exceptional-transitions\", span={span}, expected={}, actual=repr(self.{field_name}))",
            json_string(cott_symbol),
            json_string(&format!("_cott_old_{field_name} is {from}")),
            json_string(cott_symbol),
            json_string(&format!("self.{field_name} is old or {to}")),
        )
        .unwrap();
    }
    let modifies = method
        .get("modifies")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default();
    for field in state {
        let field_name = field
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or_default();
        if modifies
            .iter()
            .chain(
                transitions
                    .iter()
                    .map(|transition| transition.get("field").unwrap()),
            )
            .any(|value| local_name(value.as_str().unwrap_or_default()) == field_name)
        {
            continue;
        }
        writeln!(
            out,
            "                if self.{field_name} is not _cott_old_{field_name}:\n                    raise CottContractViolation(\"exceptional frame clause failed\", symbol={}, phase=\"exceptional-frame\", span={span}, expected={}, actual={})",
            json_string(cott_symbol),
            json_string(&format!("self.{field_name} unchanged")),
            json_string(&format!("self.{field_name} changed")),
        )
        .unwrap();
    }
    render_invariants(
        out,
        implementation,
        &format!("{}.{}", module.module, concrete),
        16,
    );
}

fn async_protocol_validator(boundary: bool, test_only: bool) -> &'static str {
    if boundary {
        "_cott_validate_abi"
    } else if test_only {
        "(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)"
    } else {
        "_cott_normalize_f32_abi"
    }
}
fn render_impl_parameters(
    parameters: &[Value],
    module: &str,
    declarations: &BTreeMap<String, String>,
) -> (String, String, Vec<(String, String)>) {
    let mut signature = Vec::new();
    let mut call = Vec::new();
    let mut typed = Vec::new();
    let mut keyword_marker = false;
    for parameter in parameters {
        let name = parameter
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or_default();
        let kind = parameter
            .get("kind")
            .and_then(Value::as_str)
            .unwrap_or("positional");
        if kind == "keyword_only" && !keyword_marker {
            signature.push("*".to_owned());
            keyword_marker = true;
        }
        let ty = render_type(parameter.get("type").unwrap(), module, declarations);
        let default = parameter
            .get("default")
            .filter(|default| !default.is_null())
            .map(|default| format!(" = {}", render_value(default)))
            .unwrap_or_default();
        signature.push(format!("{name}: {ty}{default}"));
        call.push(if kind == "keyword_only" {
            format!("{name}={name}")
        } else {
            name.to_owned()
        });
        typed.push((name.to_owned(), ty));
    }
    (signature.join(", "), call.join(", "), typed)
}

fn render_abi_assignment(
    out: &mut String,
    name: &str,
    ty: &str,
    indent: usize,
    boundary: bool,
    test_only: bool,
) {
    let prefix = " ".repeat(indent);
    let path_string = if name == "_result" {
        "$.return".to_owned()
    } else {
        format!("$.{name}")
    };
    let path = json_string(&path_string);
    let validator = if boundary {
        "_cott_validate_abi"
    } else if test_only {
        "(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)"
    } else {
        "_cott_normalize_f32_abi"
    };
    writeln!(
        out,
        "{prefix}{name} = {validator}({name}, {ty}, path={path})"
    )
    .unwrap();
}

fn impl_contract_callable(
    callable: &serde_json::Map<String, Value>,
    symbol: &str,
    errors: bool,
) -> Value {
    let contracts = callable
        .get("contracts")
        .and_then(Value::as_object)
        .expect("validated impl callable contracts");
    let mut clauses = Vec::new();
    for name in ["requires", "errors", "ensures"] {
        if name == "errors" && !errors {
            continue;
        }
        clauses.extend(
            contracts
                .get(name)
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .cloned(),
        );
    }
    let effects = callable
        .get("effects")
        .cloned()
        .unwrap_or_else(|| json!([]));
    let mut value = json!({"name": symbol, "span": callable["span"], "contract": {"clauses": clauses, "effects": effects}});
    rewrite_impl_contract_references(&mut value);
    value
}

fn rewrite_impl_contract_references(value: &mut Value) {
    match value {
        Value::Array(values) => {
            for value in values {
                rewrite_impl_contract_references(value);
            }
        }
        Value::Object(object) => match object.get("kind").and_then(Value::as_str) {
            Some("self_ref") => {
                *object = serde_json::Map::from_iter([
                    ("kind".to_owned(), Value::String("parameter_ref".to_owned())),
                    ("symbol".to_owned(), Value::String("self".to_owned())),
                ]);
            }
            Some("result_ref") => {
                *object = serde_json::Map::from_iter([
                    ("kind".to_owned(), Value::String("parameter_ref".to_owned())),
                    ("symbol".to_owned(), Value::String("_result".to_owned())),
                ]);
            }
            Some("old_state_field") => {
                let field = local_name(
                    object
                        .get("field")
                        .and_then(Value::as_str)
                        .unwrap_or_default(),
                );
                *object = serde_json::Map::from_iter([
                    ("kind".to_owned(), Value::String("parameter_ref".to_owned())),
                    (
                        "symbol".to_owned(),
                        Value::String(format!("_cott_old_{field}")),
                    ),
                ]);
            }
            _ => {
                for value in object.values_mut() {
                    rewrite_impl_contract_references(value);
                }
            }
        },
        _ => {}
    }
}

fn render_contract_block(
    out: &mut String,
    callable: &Value,
    preconditions: bool,
    boundary: bool,
    test_only: bool,
    extra_indent: usize,
) {
    let callable = callable
        .as_object()
        .expect("synthetic callable is an object");
    let mut block = String::new();
    if boundary {
        if preconditions {
            render_preconditions(&mut block, callable, "");
        } else {
            render_postconditions(&mut block, callable, "");
        }
    } else if test_only {
        render_test_only_contract(&mut block, callable, "", preconditions);
    }
    if !block.is_empty() {
        let prefix = " ".repeat(extra_indent);
        for line in block.split_inclusive('\n') {
            out.push_str(&prefix);
            out.push_str(line);
        }
    }
}

fn render_invariants(
    out: &mut String,
    implementation: &serde_json::Map<String, Value>,
    symbol: &str,
    indent: usize,
) {
    let prefix = " ".repeat(indent);
    for invariant in implementation
        .get("invariants")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
    {
        let mut expression = invariant.get("expression").cloned().unwrap_or(Value::Null);
        rewrite_impl_contract_references(&mut expression);
        let expression = render_contract_expression(&expression);
        let mut guard = invariant.get("guard").cloned().unwrap_or(Value::Null);
        rewrite_impl_contract_references(&mut guard);
        let span = serde_json::to_string(invariant.get("span").unwrap()).expect("span serializes");
        let label = format!(
            "invariant:{}",
            invariant
                .get("clause_id")
                .and_then(Value::as_u64)
                .unwrap_or_default()
        );
        let condition = render_match_function(
            out,
            (!guard.is_null()).then_some(&guard),
            &expression,
            &format!("_cott_match_{}", label.replace(':', "_")),
            indent,
            true,
        )
        .map(|name| format!("{name}()"))
        .unwrap_or(expression);
        writeln!(
            out,
            "{prefix}if not ({condition}):\n{prefix}    raise CottContractViolation(\"invariant failed\", symbol={}, clause={}, phase=\"invariant\", span={span}, expected=\"true\", actual=\"false\")",
            json_string(symbol),
            json_string(&label),
        )
        .unwrap();
    }
}

fn is_never(value: Option<&Value>) -> bool {
    value.and_then(Value::as_object).is_some_and(|ty| {
        ty.get("kind").and_then(Value::as_str) == Some("primitive")
            && ty.get("name").and_then(Value::as_str) == Some("never")
    })
}

fn render_function_parameters_with_names(
    object: &serde_json::Map<String, Value>,
    module: &str,
    declarations: &BTreeMap<String, String>,
    typevar_names: &BTreeMap<String, String>,
) -> (String, String, Vec<(String, String)>) {
    let mut signature = Vec::new();
    let mut call = Vec::new();
    let mut typed = Vec::new();
    let mut keyword_marker = false;
    for parameter in object
        .get("parameters")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
    {
        let name = parameter
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or_default();
        let kind = parameter
            .get("kind")
            .and_then(Value::as_str)
            .unwrap_or("positional");
        if kind == "keyword_only" && !keyword_marker {
            signature.push("*".to_owned());
            keyword_marker = true;
        }
        let ty = render_type_with_names(
            parameter.get("type").unwrap(),
            module,
            declarations,
            typevar_names,
        );
        signature.push(format!("{name}: {ty}"));
        if kind == "keyword_only" {
            call.push(format!("{name}={name}"));
        } else {
            call.push(name.to_owned());
        }
        typed.push((name.to_owned(), ty));
    }
    (signature.join(", "), call.join(", "), typed)
}

fn render_indented_doc(out: &mut String, value: Option<&Value>) {
    if let Some(text) = value
        .and_then(Value::as_object)
        .and_then(|doc| doc.get("text"))
        .and_then(Value::as_str)
    {
        writeln!(
            out,
            "    \"\"\"{}\"\"\"",
            text.replace('\\', "\\\\").replace("\"\"\"", "\\\"\\\"\\\"")
        )
        .unwrap();
    }
}
fn render_test_only_contract(
    out: &mut String,
    function: &serde_json::Map<String, Value>,
    local_function: &str,
    preconditions: bool,
) {
    let mut block = String::new();
    if preconditions {
        render_preconditions(&mut block, function, local_function);
    } else {
        render_postconditions(&mut block, function, local_function);
    }
    if block.is_empty() {
        return;
    }
    out.push_str("    if _cott_test_context:\n");
    for line in block.split_inclusive('\n') {
        out.push_str("    ");
        out.push_str(line);
    }
}
fn render_match_function(
    out: &mut String,
    guard: Option<&Value>,
    predicate: &str,
    name: &str,
    indent: usize,
    non_match: bool,
) -> Option<String> {
    let guard = guard?.as_object()?;
    let scrutinee = render_contract_expression(guard.get("scrutinee")?);
    let (pattern, bindings) = render_pattern(guard.get("pattern")?, "_cott_match_value");
    let prefix = " ".repeat(indent);
    let nested = " ".repeat(indent + 4);
    let bound = " ".repeat(indent + 8);
    writeln!(out, "{prefix}def {name}() -> bool:").unwrap();
    writeln!(out, "{nested}_cott_match_value = {scrutinee}").unwrap();
    writeln!(out, "{nested}if {pattern}:").unwrap();
    for binding in bindings {
        writeln!(out, "{bound}{binding}").unwrap();
    }
    writeln!(out, "{bound}return ({predicate})").unwrap();
    writeln!(
        out,
        "{nested}return {}",
        if non_match { "True" } else { "False" }
    )
    .unwrap();
    Some(name.to_owned())
}

fn render_preconditions(
    out: &mut String,
    function: &serde_json::Map<String, Value>,
    _local_function: &str,
) {
    let clauses = function
        .get("contract")
        .and_then(Value::as_object)
        .and_then(|contract| contract.get("clauses"))
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default();
    for clause in clauses {
        if clause.get("kind").and_then(Value::as_str) != Some("requires") {
            continue;
        }
        let expression = render_contract_expression(clause.get("expression").unwrap());
        let label = clause_label(clause);
        let condition = render_match_function(
            out,
            clause.get("guard").filter(|guard| !guard.is_null()),
            &expression,
            &format!("_cott_match_{}", label.replace(':', "_")),
            4,
            true,
        )
        .map(|name| format!("{name}()"))
        .unwrap_or(expression);
        let span = serde_json::to_string(clause.get("span").unwrap()).expect("span serializes");
        let symbol = function
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or_default();
        writeln!(
            out,
            "    if not ({condition}):\n        raise CottContractViolation(\"requires clause failed\", symbol={}, clause={}, phase=\"requires\", span={span}, expected=\"true\", actual=\"false\")",
            json_string(symbol),
            json_string(&label),
        )
        .unwrap();
    }
    if clauses
        .iter()
        .any(|clause| clause.get("kind").and_then(Value::as_str) == Some("error"))
    {
        out.push_str("    _expected_error = None\n    _expected_error_span = None\n    _expected_error_clause = None\n");
        for clause in clauses {
            if clause.get("kind").and_then(Value::as_str) != Some("error") {
                continue;
            }
            let label = clause_label(clause);
            let predicate = clause
                .get("when")
                .filter(|value| !value.is_null())
                .map(render_contract_expression)
                .unwrap_or_else(|| "True".to_owned());
            let condition = render_match_function(
                out,
                clause.get("guard").filter(|guard| !guard.is_null()),
                &predicate,
                &format!("_cott_match_{}", label.replace(':', "_")),
                4,
                false,
            )
            .map(|name| format!("{name}()"))
            .or_else(|| {
                clause
                    .get("when")
                    .filter(|value| !value.is_null())
                    .map(render_contract_expression)
            });
            let Some(condition) = condition else {
                continue;
            };
            let variant = enum_variant_name(
                clause
                    .get("variant")
                    .and_then(Value::as_str)
                    .unwrap_or_default(),
            );
            let span = serde_json::to_string(clause.get("span").unwrap()).expect("span serializes");
            writeln!(
                out,
                "    if _expected_error is None and ({condition}):\n        _expected_error = {variant}\n        _expected_error_span = {span}\n        _expected_error_clause = {}",
                json_string(&label),
            )
            .unwrap();
        }
    }
}

fn render_postconditions(
    out: &mut String,
    function: &serde_json::Map<String, Value>,
    _local_function: &str,
) {
    let clauses = function
        .get("contract")
        .and_then(Value::as_object)
        .and_then(|contract| contract.get("clauses"))
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default();
    let symbol = function
        .get("name")
        .and_then(Value::as_str)
        .unwrap_or_default();
    let function_span =
        serde_json::to_string(function.get("span").unwrap()).expect("span serializes");
    let errors = clauses
        .iter()
        .filter(|clause| clause.get("kind").and_then(Value::as_str) == Some("error"))
        .collect::<Vec<_>>();
    if !errors.is_empty() {
        let unconditional = errors
            .iter()
            .filter(|clause| clause.get("guard").is_none_or(Value::is_null))
            .filter(|clause| clause.get("when").is_none_or(Value::is_null))
            .filter_map(|clause| clause.get("variant").and_then(Value::as_str))
            .map(enum_variant_name)
            .collect::<Vec<_>>();
        let allowed = if unconditional.is_empty() {
            "()".to_owned()
        } else {
            format!("({},)", unconditional.join(", "))
        };
        writeln!(
            out,
            "    if type(_result) is Err:\n        if _expected_error is not None:\n            if type(_result.error) is not _expected_error:\n                raise CottContractViolation(\"conditional error clause failed\", symbol={}, clause=_expected_error_clause, phase=\"error\", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)\n        elif type(_result.error) not in {allowed}:\n            raise CottContractViolation(\"returned error is not allowed\", symbol={}, phase=\"error\", span={function_span}, expected=\"declared unconditional error variant\", actual=type(_result.error).__name__)\n    elif _expected_error is not None:\n        raise CottContractViolation(\"expected conditional error was not returned\", symbol={}, clause=_expected_error_clause, phase=\"error\", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)",
            json_string(symbol),
            json_string(symbol),
            json_string(symbol),
        )
        .unwrap();
    }
    for clause in clauses {
        if clause.get("kind").and_then(Value::as_str) != Some("ensures") {
            continue;
        }
        let label = clause_label(clause);
        let span = serde_json::to_string(clause.get("span").unwrap()).expect("span serializes");
        let expression = render_contract_expression(clause.get("expression").unwrap());
        let guard = clause.get("guard").filter(|guard| !guard.is_null());
        let condition = render_match_function(
            out,
            guard,
            &expression,
            &format!("_cott_match_{}", label.replace(':', "_")),
            4,
            true,
        )
        .map(|name| format!("{name}()"))
        .unwrap_or(expression);
        writeln!(
            out,
            "    if not ({condition}):\n        raise CottContractViolation(\"ensures clause failed\", symbol={}, clause={}, phase=\"ensures\", span={span}, expected=\"true\", actual=\"false\")",
            json_string(symbol),
            json_string(&label),
        )
        .unwrap();
    }
}

fn clause_label(clause: &Value) -> String {
    format!(
        "{}:{}",
        clause
            .get("kind")
            .and_then(Value::as_str)
            .unwrap_or("clause"),
        clause
            .get("clause_id")
            .and_then(Value::as_u64)
            .unwrap_or_default()
    )
}

fn render_pattern(pattern: &Value, value: &str) -> (String, Vec<String>) {
    let kind = pattern
        .get("kind")
        .and_then(Value::as_str)
        .unwrap_or_default();
    match kind {
        "wildcard" => ("True".to_owned(), Vec::new()),
        "binding" => (
            "True".to_owned(),
            vec![format!(
                "{} = {value}",
                pattern
                    .get("name")
                    .and_then(Value::as_str)
                    .or_else(|| pattern
                        .get("symbol")
                        .and_then(Value::as_str)
                        .map(local_name))
                    .unwrap_or("_binding")
            )],
        ),
        "variant" | "result_ok" | "result_err" | "option_some" | "option_none" | "enum" => {
            let symbol = pattern
                .get("symbol")
                .and_then(Value::as_str)
                .unwrap_or_default();
            let variant = match kind {
                "result_ok" => "Ok".to_owned(),
                "result_err" => "Err".to_owned(),
                "option_some" => "Some".to_owned(),
                "option_none" => "Nothing".to_owned(),
                _ if symbol.split('.').count() >= 3 => enum_variant_name(symbol),
                _ => local_name(symbol).to_owned(),
            };
            let mut guards = vec![format!("type({value}) is {variant}")];
            let mut bindings = Vec::new();
            for (index, argument) in pattern
                .get("arguments")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .enumerate()
            {
                let field = match variant.as_str() {
                    "Ok" | "Some" => format!("{value}.value"),
                    "Err" => format!("{value}.error"),
                    _ => format!(
                        "getattr({value}, _dataclasses.fields(type({value}))[{index}].name)"
                    ),
                };
                let (guard, nested) = render_pattern(argument, &field);
                guards.push(guard);
                bindings.extend(nested);
            }
            (guards.join(" and "), bindings)
        }
        _ => ("False".to_owned(), Vec::new()),
    }
}

fn render_contract_expression(expression: &Value) -> String {
    let kind = expression
        .get("kind")
        .and_then(Value::as_str)
        .unwrap_or_default();
    match kind {
        "literal" => render_value(expression.get("value").unwrap()),
        "parameter_ref" | "binding_ref" | "constant_ref" => local_name(
            expression
                .get("symbol")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        )
        .to_owned(),
        "enum_singleton_ref" => format!(
            "{}()",
            enum_variant_name(
                expression
                    .get("symbol")
                    .and_then(Value::as_str)
                    .unwrap_or_default()
            )
        ),
        "self_ref" | "result_ref" => "_result".to_owned(),
        "field" => format!(
            "({}).{}",
            render_contract_expression(expression.get("base").unwrap()),
            expression
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default()
        ),
        "len" => format!(
            "len({})",
            render_contract_expression(expression.get("value").unwrap())
        ),
        "intrinsic" => {
            let arguments = expression
                .get("arguments")
                .and_then(Value::as_array)
                .map(|arguments| {
                    arguments
                        .iter()
                        .map(render_contract_expression)
                        .collect::<Vec<_>>()
                })
                .unwrap_or_default();
            let first = arguments.first().cloned().unwrap_or_default();
            let second = arguments.get(1).cloned().unwrap_or_default();
            match expression.get("name").and_then(Value::as_str) {
                Some("starts_with") => format!("_cott_starts_with({first}, {second})"),
                Some("ends_with") => format!("_cott_ends_with({first}, {second})"),
                Some("contains") => format!("({second} in {first})"),
                Some("unique_by") => format!(
                    "_cott_unique_by({first}, {})",
                    json_string(local_name(
                        expression
                            .get("selector")
                            .and_then(Value::as_object)
                            .and_then(|selector| selector.get("field"))
                            .and_then(Value::as_str)
                            .unwrap_or_default()
                    ))
                ),
                Some("descending_by") => format!(
                    "_cott_descending_by({first}, {})",
                    json_string(local_name(
                        expression
                            .get("selector")
                            .and_then(Value::as_object)
                            .and_then(|selector| selector.get("field"))
                            .and_then(Value::as_str)
                            .unwrap_or_default()
                    ))
                ),
                _ => "False".to_owned(),
            }
        }
        "unary" => {
            let op = match expression.get("op").and_then(Value::as_str) {
                Some("not") => "not ",
                Some("minus") => "-",
                _ => "+",
            };
            let rendered = format!(
                "({op}{})",
                render_contract_expression(expression.get("operand").unwrap())
            );
            normalize_contract_f32(expression, rendered)
        }
        "binary" => {
            let left = render_contract_expression(expression.get("left").unwrap());
            let right = render_contract_expression(expression.get("right").unwrap());
            let rendered = match expression.get("op").and_then(Value::as_str) {
                Some("remainder") => format!("_cott_euclidean_mod({left}, {right})"),
                op => {
                    let op = match op {
                        Some("or") => "or",
                        Some("and") => "and",
                        Some("subtract") => "-",
                        Some("multiply") => "*",
                        Some("divide") => "/",
                        _ => "+",
                    };
                    format!("({left} {op} {right})")
                }
            };
            normalize_contract_f32(expression, rendered)
        }
        "comparison_chain" => {
            let operands = expression
                .get("operands")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .map(render_contract_expression)
                .collect::<Vec<_>>();
            let operators = expression
                .get("operators")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .map(|operator| match operator.as_str() {
                    Some("not_equal") => "!=",
                    Some("less") => "<",
                    Some("less_equal") => "<=",
                    Some("greater") => ">",
                    Some("greater_equal") => ">=",
                    _ => "==",
                })
                .collect::<Vec<_>>();
            let mut rendered = String::from("(");
            if let Some(first) = operands.first() {
                rendered.push_str(first);
                for (operator, operand) in operators.iter().zip(operands.iter().skip(1)) {
                    write!(rendered, " {operator} {operand}").unwrap();
                }
            }
            rendered.push(')');
            rendered
        }
        _ => "False".to_owned(),
    }
}
fn normalize_contract_f32(expression: &Value, rendered: String) -> String {
    if expression
        .get("type")
        .and_then(Value::as_object)
        .is_some_and(|ty| {
            ty.get("kind").and_then(Value::as_str) == Some("primitive")
                && ty.get("name").and_then(Value::as_str) == Some("f32")
        })
    {
        format!("_cott_normalize_f32({rendered})")
    } else {
        rendered
    }
}

fn render_stub(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    declarations: &BTreeMap<String, String>,
    bindings: &[ResolvedBinding],
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
) -> Vec<u8> {
    let mut out = String::from(
        "from __future__ import annotations\n\nfrom collections.abc import Generator, Iterator\nfrom pathlib import Path\nfrom typing import Any, Literal, Never, Protocol, TypeVar, final\n\nfrom cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit\n",
    );
    let names = exported_names(module);
    let mut type_names = type_exported_names(module);
    type_names.extend(associated_typevar_names(module, modules));
    if !type_names.is_empty() {
        writeln!(
            out,
            "\nfrom {} import {}",
            type_module_name(&module.module),
            type_names
                .iter()
                .map(|name| format!("{name} as {name}"))
                .collect::<Vec<_>>()
                .join(", ")
        )
        .unwrap();
    }
    let mut imports = referenced_imports(module, modules, declarations);
    for (source, names) in resolved_method_imports(module, modules, declarations) {
        imports.entry(source).or_default().extend(names);
    }
    for (source, names) in imports {
        writeln!(
            out,
            "from {} import {}",
            type_module_name(&source),
            names.into_iter().collect::<Vec<_>>().join(", ")
        )
        .unwrap();
    }
    let mut factory_imports = factory_concrete_imports(module, declarations);
    for (source, names) in resolved_factory_imports(module, modules, declarations) {
        factory_imports.entry(source).or_default().extend(names);
    }
    for (source, names) in factory_imports {
        writeln!(
            out,
            "from {source} import {}",
            names.into_iter().collect::<Vec<_>>().join(", ")
        )
        .unwrap();
    }
    render_function_bound_protocols(&mut out, module, declarations);
    render_function_typevars(&mut out, module, declarations, true);
    let mut exported = names;
    for declaration in &module.declarations {
        let object = declaration.as_object().unwrap();
        if object.get("kind").and_then(Value::as_str) != Some("function")
            || !object
                .get("public")
                .and_then(Value::as_bool)
                .unwrap_or(false)
        {
            continue;
        }
        let name = local_name(
            object
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        );
        render_doc(&mut out, object.get("doc"));
        let typevar_names = generic_typevar_names(module, object, true);
        let (signature, _, _) = render_function_parameters_with_names(
            object,
            &module.module,
            declarations,
            &typevar_names,
        );
        let return_type = render_type_with_names(
            object.get("return_type").unwrap(),
            &module.module,
            declarations,
            &typevar_names,
        );
        writeln!(
            out,
            "{}def {name}({signature}) -> {return_type}: ...\n",
            if object.get("callable_kind").and_then(Value::as_str) == Some("async") {
                "async "
            } else {
                ""
            }
        )
        .unwrap();
        exported.push(name.to_owned());
    }
    render_impl_stubs(&mut out, module, declarations, bindings, modules);
    exported.sort();
    writeln!(
        out,
        "__all__ = [{}]",
        exported
            .iter()
            .map(|name| json_string(name))
            .collect::<Vec<_>>()
            .join(", ")
    )
    .unwrap();
    out.into_bytes()
}

fn render_impl_stubs(
    out: &mut String,
    module: &crate::python::artifact_plan::PythonArtifactModule,
    declarations: &BTreeMap<String, String>,
    bindings: &[ResolvedBinding],
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
) {
    for declaration in &module.declarations {
        let Some(implementation) = declaration
            .as_object()
            .filter(|object| object.get("kind").and_then(Value::as_str) == Some("impl"))
        else {
            continue;
        };
        let name = local_name(
            implementation
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        );
        writeln!(out, "\n@final\nclass {name}:").unwrap();
        for field in implementation
            .get("state")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
        {
            let field = field.as_object().expect("validated impl state field");
            let field_name = field
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default();
            let ty = render_type(field.get("type").unwrap(), &module.module, declarations);
            writeln!(out, "    {field_name}: {ty}").unwrap();
        }
        let init = implementation
            .get("init")
            .and_then(Value::as_object)
            .and_then(|init| init.get("parameters"))
            .and_then(Value::as_array)
            .map(Vec::as_slice)
            .unwrap_or_default();
        let (signature, _, _) = render_impl_parameters(init, &module.module, declarations);
        let signature = if signature.is_empty() {
            "self".to_owned()
        } else {
            format!("self, {signature}")
        };
        writeln!(out, "    def __init__({signature}) -> None: ...").unwrap();
        for method in resolved_impl_methods(implementation, modules)
            .iter()
            .filter_map(Value::as_object)
        {
            let method_name = method
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default();
            let cott_symbol = format!("{}.{}.{}", module.module, name, method_name);
            if default_dispatch(method).is_some_and(|function| {
                !default_dispatch_resolved(
                    function,
                    method
                        .get("callable_kind")
                        .and_then(Value::as_str)
                        .expect("validated default callable_kind"),
                    bindings,
                )
            }) || (default_dispatch(method).is_none()
                && !bindings
                    .iter()
                    .any(|binding| binding.cott_symbol == cott_symbol))
            {
                continue;
            }
            let parameters = method
                .get("parameters")
                .and_then(Value::as_array)
                .map(Vec::as_slice)
                .unwrap_or_default();
            let (signature, _, _) =
                render_impl_parameters(parameters, &module.module, declarations);
            let signature = if signature.is_empty() {
                format!("self: {name}")
            } else {
                format!("self: {name}, {signature}")
            };
            let return_type = render_type(
                method.get("return_type").unwrap(),
                &module.module,
                declarations,
            );
            writeln!(
                out,
                "    {}def {method_name}({signature}) -> {return_type}: ...",
                if method.get("callable_kind").and_then(Value::as_str) == Some("async") {
                    "async "
                } else {
                    ""
                }
            )
            .unwrap();
        }
    }
}
fn render_type(value: &Value, module: &str, declarations: &BTreeMap<String, String>) -> String {
    render_type_with_names(value, module, declarations, &BTreeMap::new())
}

fn render_type_with_names(
    value: &Value,
    module: &str,
    declarations: &BTreeMap<String, String>,
    typevar_names: &BTreeMap<String, String>,
) -> String {
    let object = value.as_object().unwrap();
    match object.get("kind").and_then(Value::as_str).unwrap() {
        "primitive" => match object.get("name").and_then(Value::as_str).unwrap() {
            "bool" => "bool",
            "i8" => "I8",
            "i16" => "I16",
            "i32" => "I32",
            "i64" => "I64",
            "u8" => "U8",
            "u16" => "U16",
            "u32" => "U32",
            "u64" => "U64",
            "f32" => "F32",
            "f64" => "F64",
            "str" => "str",
            "bytes" => "bytes",
            "path" => "Path",
            "unit" => "Unit",
            "json" => "JsonValue",
            "any" => "Any",
            "unknown" => "object",
            "never" => "Never",
            other => unreachable!("validated primitive type `{other}`"),
        }
        .into(),
        "named" => {
            let name = local_name(
                object
                    .get("name")
                    .and_then(Value::as_str)
                    .unwrap_or_default(),
            );
            let args = object
                .get("args")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .map(
                    |argument| match argument.get("kind").and_then(Value::as_str) {
                        Some("type") => render_type_with_names(
                            argument
                                .get("type")
                                .expect("validated generic type argument"),
                            module,
                            declarations,
                            typevar_names,
                        ),
                        Some("const") => format!(
                            "Literal[{}]",
                            render_fixed_length(
                                argument
                                    .get("value")
                                    .expect("validated generic const argument"),
                                typevar_names,
                            )
                        ),
                        _ => unreachable!("validated generic argument kind"),
                    },
                )
                .collect::<Vec<_>>();
            if args.is_empty() {
                name.to_owned()
            } else {
                format!("{name}[{}]", args.join(", "))
            }
        }
        "factory" => format!(
            "type[{}]",
            render_type_with_names(
                object.get("instance").unwrap(),
                module,
                declarations,
                typevar_names
            )
        ),
        "type_parameter" => {
            let name = object
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or("object");
            typevar_names
                .get(name)
                .cloned()
                .unwrap_or_else(|| name.to_owned())
        }
        "associated_projection" => associated_projection_typevar_name(object),
        "list" => format!(
            "CottList[{}]",
            render_type_with_names(
                object.get("item").unwrap(),
                module,
                declarations,
                typevar_names
            )
        ),
        "set" => format!(
            "CottSet[{}]",
            render_type_with_names(
                object.get("item").unwrap(),
                module,
                declarations,
                typevar_names
            )
        ),
        "map" => format!(
            "FrozenMap[{}, {}]",
            render_type_with_names(
                object.get("key").unwrap(),
                module,
                declarations,
                typevar_names
            ),
            render_type_with_names(
                object.get("value").unwrap(),
                module,
                declarations,
                typevar_names
            )
        ),
        "tuple" => {
            let items = object
                .get("items")
                .and_then(Value::as_array)
                .expect("validated tuple items");
            if items.is_empty() {
                "tuple[()]".to_owned()
            } else {
                format!(
                    "tuple[{}]",
                    items
                        .iter()
                        .map(|item| render_type_with_names(
                            item,
                            module,
                            declarations,
                            typevar_names
                        ))
                        .collect::<Vec<_>>()
                        .join(", ")
                )
            }
        }
        "array" => format!(
            "CottArray[{}, Literal[{}]]",
            render_type_with_names(
                object.get("item").unwrap(),
                module,
                declarations,
                typevar_names
            ),
            render_fixed_length(
                object.get("length").expect("validated fixed length"),
                typevar_names
            )
        ),
        "buffer" => format!(
            "CottBuffer[Literal[{}]]",
            render_fixed_length(
                object.get("length").expect("validated fixed length"),
                typevar_names
            )
        ),
        "option" => format!(
            "Option[{}]",
            render_type_with_names(
                object.get("item").unwrap(),
                module,
                declarations,
                typevar_names
            )
        ),
        "result" => format!(
            "Result[{}, {}]",
            render_type_with_names(
                object.get("ok").unwrap(),
                module,
                declarations,
                typevar_names
            ),
            render_type_with_names(
                object.get("error").unwrap(),
                module,
                declarations,
                typevar_names
            )
        ),
        "iterator" => format!(
            "Iterator[{}]",
            render_type_with_names(
                object.get("item").unwrap(),
                module,
                declarations,
                typevar_names
            )
        ),
        "generator" => format!(
            "Generator[{}, {}, {}]",
            render_type_with_names(
                object.get("yield").unwrap(),
                module,
                declarations,
                typevar_names
            ),
            render_type_with_names(
                object.get("send").unwrap(),
                module,
                declarations,
                typevar_names
            ),
            render_type_with_names(
                object.get("return").unwrap(),
                module,
                declarations,
                typevar_names
            )
        ),
        "async_iterator" => format!(
            "AsyncIterator[{}]",
            render_type_with_names(
                object.get("item").unwrap(),
                module,
                declarations,
                typevar_names
            )
        ),
        "async_generator" => format!(
            "AsyncGenerator[{}, {}]",
            render_type_with_names(
                object.get("yield").unwrap(),
                module,
                declarations,
                typevar_names
            ),
            render_type_with_names(
                object.get("send").unwrap(),
                module,
                declarations,
                typevar_names
            )
        ),
        "opaque" => format!(
            "Opaque[Literal[{}]]",
            json_string(
                object
                    .get("tag")
                    .and_then(Value::as_str)
                    .unwrap_or_default()
            )
        ),
        "dyn" => format!(
            "Dyn[{}]",
            render_type_with_names(
                object.get("trait").expect("validated Dyn trait"),
                module,
                declarations,
                typevar_names
            )
        ),
        other => unreachable!("validated canonical type kind `{other}`"),
    }
}
fn render_value(value: &Value) -> String {
    let object = value.as_object().unwrap();
    match object.get("kind").and_then(Value::as_str).unwrap() {
        "bool" => {
            if object.get("value").and_then(Value::as_bool) == Some(true) {
                "True".into()
            } else {
                "False".into()
            }
        }
        "integer" => object
            .get("value")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_owned(),
        "string" => json_string(
            object
                .get("value")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        ),
        "f32" => float_bits(
            object
                .get("bits")
                .and_then(Value::as_str)
                .unwrap_or_default(),
            true,
        ),
        "f64" => float_bits(
            object
                .get("bits")
                .and_then(Value::as_str)
                .unwrap_or_default(),
            false,
        ),
        "bytes" => format!(
            "bytes.fromhex({})",
            json_string(
                object
                    .get("value")
                    .and_then(Value::as_str)
                    .unwrap_or_default()
            )
        ),
        "unit" => "UNIT".into(),
        "option" => object
            .get("value")
            .filter(|value| !value.is_null())
            .map(|value| format!("Some(value={})", render_value(value)))
            .unwrap_or_else(|| "Nothing()".into()),
        "result" => {
            let constructor = if object.get("ok").and_then(Value::as_bool) == Some(true) {
                "Ok"
            } else {
                "Err"
            };
            let field = if constructor == "Ok" {
                "value"
            } else {
                "error"
            };
            format!(
                "{constructor}({field}={})",
                render_value(object.get("value").unwrap())
            )
        }
        "list" => format!(
            "CottList(values=[{}])",
            render_value_items(object.get("items"))
        ),
        "set" => format!(
            "CottSet(values=[{}])",
            render_value_items(object.get("items"))
        ),
        "map" => format!(
            "FrozenMap(values={{{}}})",
            object
                .get("entries")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(Value::as_array)
                .filter(|entry| entry.len() == 2)
                .map(|entry| format!("{}: {}", render_value(&entry[0]), render_value(&entry[1])))
                .collect::<Vec<_>>()
                .join(", ")
        ),
        "tuple" => format!("({})", render_tuple_value_items(object.get("items"))),
        "array" => format!(
            "CottArray(values=({}))",
            render_tuple_value_items(object.get("items"))
        ),
        "buffer" => format!(
            "CottBuffer(data=bytes.fromhex({}))",
            json_string(
                object
                    .get("hex")
                    .and_then(Value::as_str)
                    .unwrap_or_default()
            )
        ),
        "named" => format!(
            "{}({})",
            local_name(
                object
                    .get("symbol")
                    .and_then(Value::as_str)
                    .unwrap_or_default()
            ),
            object
                .get("fields")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(Value::as_object)
                .map(|field| format!(
                    "{}={}",
                    field
                        .get("name")
                        .and_then(Value::as_str)
                        .unwrap_or_default(),
                    render_value(field.get("value").unwrap())
                ))
                .collect::<Vec<_>>()
                .join(", ")
        ),
        "enum" => {
            let variant = enum_variant_name(
                object
                    .get("variant")
                    .and_then(Value::as_str)
                    .unwrap_or_default(),
            );
            let values = render_value_items(object.get("fields"));
            if values.is_empty() {
                format!("{variant}()")
            } else {
                format!(
                    "{variant}(**{{_field.name: _value for _field, _value in zip(_dataclasses.fields({variant}), ({values},))}})"
                )
            }
        }
        "json" => render_json_value(object.get("value").unwrap()),
        other => unreachable!("validated canonical value kind `{other}`"),
    }
}

fn render_value_items(value: Option<&Value>) -> String {
    value
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .map(render_value)
        .collect::<Vec<_>>()
        .join(", ")
}

fn render_tuple_value_items(value: Option<&Value>) -> String {
    let items = value
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default();
    match items {
        [] => String::new(),
        [item] => format!("{},", render_value(item)),
        items => items
            .iter()
            .map(render_value)
            .collect::<Vec<_>>()
            .join(", "),
    }
}

fn render_json_value(value: &Value) -> String {
    match value {
        Value::Null => "JsonNull()".into(),
        Value::Bool(value) => format!(
            "JsonBoolean(value={})",
            if *value { "True" } else { "False" }
        ),
        Value::Number(value) if value.is_i64() || value.is_u64() => {
            format!("JsonInteger(value={value})")
        }
        Value::Number(value) => format!("JsonFloat(value={value})"),
        Value::String(value) => format!("JsonString(value={})", json_string(value)),
        Value::Array(values) => format!(
            "JsonArray(value=CottList(values=[{}]))",
            values
                .iter()
                .map(render_json_value)
                .collect::<Vec<_>>()
                .join(", ")
        ),
        Value::Object(values) => format!(
            "JsonObject(value=FrozenMap(values={{{}}}))",
            values
                .iter()
                .map(|(key, value)| format!("{}: {}", json_string(key), render_json_value(value)))
                .collect::<Vec<_>>()
                .join(", ")
        ),
    }
}
fn float_bits(bits: &str, single: bool) -> String {
    let parsed = u64::from_str_radix(bits, 16).unwrap_or(0);
    if single {
        let value = f32::from_bits(parsed as u32);
        if value.is_nan() {
            "float(\"nan\")".into()
        } else if value.is_infinite() {
            if value.is_sign_negative() {
                "-float(\"inf\")".into()
            } else {
                "float(\"inf\")".into()
            }
        } else {
            value.to_string()
        }
    } else {
        let value = f64::from_bits(parsed);
        if value.is_nan() {
            "float(\"nan\")".into()
        } else if value.is_infinite() {
            if value.is_sign_negative() {
                "-float(\"inf\")".into()
            } else {
                "float(\"inf\")".into()
            }
        } else {
            value.to_string()
        }
    }
}

fn external_type_target(path: &str) -> Option<(&str, &str)> {
    let (module, qualified) = path.split_once(':')?;
    (!module.is_empty()
        && !qualified.is_empty()
        && module.split('.').all(valid_python_name)
        && qualified.split('.').all(valid_python_name))
    .then_some((module, qualified))
}

fn external_import_alias(object: &serde_json::Map<String, Value>) -> String {
    format!(
        "_cott_external_{}",
        local_name(
            object
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default()
        )
    )
}

fn external_imports(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    external_types: &BTreeMap<String, String>,
) -> BTreeSet<(String, String, String)> {
    module
        .declarations
        .iter()
        .filter_map(Value::as_object)
        .filter(|declaration| {
            declaration.get("kind").and_then(Value::as_str) == Some("external_type")
        })
        .map(|declaration| {
            let canonical_name = declaration.get("name").and_then(Value::as_str).unwrap();
            let projection = external_types
                .get(canonical_name)
                .expect("validated Python external type projection");
            let (source, qualified) = external_type_target(projection)
                .expect("validated Python external type projection");
            let root = qualified.split('.').next().unwrap();
            (
                source.to_owned(),
                root.to_owned(),
                external_import_alias(declaration),
            )
        })
        .collect()
}

fn referenced_imports(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    declarations: &BTreeMap<String, String>,
) -> BTreeMap<String, BTreeSet<String>> {
    let mut imports = BTreeMap::new();
    for declaration in &module.declarations {
        let Some(object) = declaration.as_object() else {
            continue;
        };
        let kind = object
            .get("kind")
            .and_then(Value::as_str)
            .unwrap_or_default();
        for ty in declaration_types(object, kind) {
            collect_named(ty, &module.module, declarations, &mut imports);
        }
        if kind == "trait" {
            for parent in object
                .get("parents")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                if let Some(trait_ref) = parent.get("trait") {
                    collect_named(trait_ref, &module.module, declarations, &mut imports);
                }
            }
        }
        for generic in object
            .get("generics")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("type"))
        {
            if let Some(bounds) = generic.get("bounds") {
                collect_references(bounds, &module.module, declarations, &mut imports);
            }
        }
        if kind == "function" {
            for parameter in object
                .get("parameters")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                if let Some(ty) = parameter.get("type") {
                    collect_named(ty, &module.module, declarations, &mut imports);
                }
                if let Some(default) = parameter.get("default") {
                    collect_references(default, &module.module, declarations, &mut imports);
                }
            }
            if let Some(contract) = object.get("contract") {
                collect_references(contract, &module.module, declarations, &mut imports);
            }
        }
        if kind == "trait" {
            for associated in object
                .get("associated_types")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                for bound in associated
                    .get("bounds")
                    .and_then(Value::as_array)
                    .into_iter()
                    .flatten()
                {
                    collect_named(bound, &module.module, declarations, &mut imports);
                }
            }
            for method in object
                .get("methods")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                for parameter in method
                    .get("parameters")
                    .and_then(Value::as_array)
                    .into_iter()
                    .flatten()
                {
                    if let Some(ty) = parameter.get("type") {
                        collect_named(ty, &module.module, declarations, &mut imports);
                    }
                }
                if let Some(ty) = method.get("return_type") {
                    collect_named(ty, &module.module, declarations, &mut imports);
                }
            }
        }
        if kind == "impl" {
            collect_references(declaration, &module.module, declarations, &mut imports);
        }
        if let Some(groups) = object
            .get(if kind == "struct" {
                "fields"
            } else {
                "variants"
            })
            .and_then(Value::as_array)
        {
            let mut fields = Vec::new();
            if kind == "struct" {
                fields.extend(groups.iter());
            } else {
                for variant in groups {
                    if let Some(variant_fields) = variant.get("fields").and_then(Value::as_array) {
                        fields.extend(variant_fields);
                    }
                }
            }
            for field in fields {
                if let Some(ty) = field.get("type") {
                    collect_named(ty, &module.module, declarations, &mut imports);
                }
                if let Some(default) = field.get("default") {
                    collect_references(default, &module.module, declarations, &mut imports);
                }
            }
        }
        if kind == "newtype" {
            if let Some(refinement) = object.get("refinement") {
                collect_references(refinement, &module.module, declarations, &mut imports);
            }
        }
    }
    for (trait_name, associated_name) in
        associated_projection_typevars(module, modules).into_values()
    {
        for bound in associated_type_bounds(modules, &trait_name, &associated_name) {
            collect_named(bound, &module.module, declarations, &mut imports);
        }
    }
    imports
}

fn factory_concrete_imports(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    declarations: &BTreeMap<String, String>,
) -> BTreeMap<String, BTreeSet<String>> {
    let mut imports = BTreeMap::new();
    for declaration in &module.declarations {
        collect_factory_concrete_imports(declaration, &module.module, declarations, &mut imports);
    }
    imports
}

fn collect_factory_concrete_imports(
    value: &Value,
    module: &str,
    declarations: &BTreeMap<String, String>,
    imports: &mut BTreeMap<String, BTreeSet<String>>,
) {
    let Some(object) = value.as_object() else {
        if let Some(values) = value.as_array() {
            for value in values {
                collect_factory_concrete_imports(value, module, declarations, imports);
            }
        }
        return;
    };
    if object.get("kind").and_then(Value::as_str) == Some("factory")
        && let Some(name) = object
            .get("instance")
            .and_then(Value::as_object)
            .filter(|instance| instance.get("kind").and_then(Value::as_str) == Some("named"))
            .and_then(|instance| instance.get("name"))
            .and_then(Value::as_str)
        && declarations.get(name).map(String::as_str) == Some("impl")
        && let Some((source, local)) = name.rsplit_once('.')
        && source != module
    {
        imports
            .entry(source.to_owned())
            .or_default()
            .insert(local.to_owned());
    }
    for child in object.values() {
        collect_factory_concrete_imports(child, module, declarations, imports);
    }
}

fn declaration_types<'a>(object: &'a serde_json::Map<String, Value>, kind: &str) -> Vec<&'a Value> {
    match kind {
        "alias" => object.get("target").into_iter().collect(),
        "newtype" => object.get("carrier").into_iter().collect(),
        "const" => object.get("type").into_iter().collect(),
        "function" => object.get("return_type").into_iter().collect(),
        _ => Vec::new(),
    }
}

fn collect_references(
    value: &Value,
    module: &str,
    declarations: &BTreeMap<String, String>,
    imports: &mut BTreeMap<String, BTreeSet<String>>,
) {
    let Some(object) = value.as_object() else {
        if let Some(values) = value.as_array() {
            for value in values {
                collect_references(value, module, declarations, imports);
            }
        }
        return;
    };
    match object
        .get("kind")
        .and_then(Value::as_str)
        .unwrap_or_default()
    {
        "named" => {
            collect_named(value, module, declarations, imports);
            if let Some(symbol) = object.get("symbol").and_then(Value::as_str) {
                collect_symbol(symbol, module, declarations, imports, false);
            }
        }
        "constant_ref" => {
            if let Some(symbol) = object.get("symbol").and_then(Value::as_str) {
                collect_symbol(symbol, module, declarations, imports, false);
            }
        }
        "enum_singleton_ref" => {
            if let Some(symbol) = object.get("symbol").and_then(Value::as_str) {
                collect_symbol(symbol, module, declarations, imports, true);
            }
        }
        "variant" => {
            if let Some(symbol) = object.get("symbol").and_then(Value::as_str) {
                collect_symbol(symbol, module, declarations, imports, true);
            }
        }
        "associated_projection" => {
            if let Some(base) = object.get("base") {
                collect_named(base, module, declarations, imports);
            }
        }
        _ => {}
    }
    for child in object.values() {
        collect_references(child, module, declarations, imports);
    }
}

fn collect_symbol(
    symbol: &str,
    module: &str,
    declarations: &BTreeMap<String, String>,
    imports: &mut BTreeMap<String, BTreeSet<String>>,
    enum_variant: bool,
) {
    if enum_variant {
        let Some((owner, _)) = symbol.rsplit_once('.') else {
            return;
        };
        if !matches!(
            declarations.get(owner).map(String::as_str),
            Some("enum" | "resource")
        ) {
            return;
        }
        let Some((source, _)) = owner.rsplit_once('.') else {
            return;
        };
        if source != module {
            imports
                .entry(source.to_owned())
                .or_default()
                .insert(enum_variant_name(symbol));
        }
    } else if let Some((source, local)) = symbol.rsplit_once('.') {
        if source != module
            && matches!(
                declarations.get(symbol).map(String::as_str),
                Some(
                    "alias"
                        | "external_type"
                        | "newtype"
                        | "struct"
                        | "enum"
                        | "resource"
                        | "trait"
                        | "const"
                )
            )
        {
            imports
                .entry(source.to_owned())
                .or_default()
                .insert(local.to_owned());
        }
    }
}

fn collect_named(
    value: &Value,
    module: &str,
    declarations: &BTreeMap<String, String>,
    imports: &mut BTreeMap<String, BTreeSet<String>>,
) {
    let Some(object) = value.as_object() else {
        return;
    };
    match object
        .get("kind")
        .and_then(Value::as_str)
        .unwrap_or_default()
    {
        "named" => {
            if let Some(name) = object.get("name").and_then(Value::as_str) {
                collect_symbol(name, module, declarations, imports, false);
            }
            for argument in object
                .get("args")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                if let Some(ty) = argument.get("type") {
                    collect_named(ty, module, declarations, imports);
                }
            }
        }
        "associated_projection" => {
            if let Some(base) = object.get("base") {
                collect_named(base, module, declarations, imports);
            }
        }
        "list" | "set" | "option" | "iterator" => {
            if let Some(item) = object.get("item") {
                collect_named(item, module, declarations, imports);
            }
        }
        "map" => {
            for key in ["key", "value"] {
                if let Some(value) = object.get(key) {
                    collect_named(value, module, declarations, imports);
                }
            }
        }
        "tuple" => {
            for item in object
                .get("items")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                collect_named(item, module, declarations, imports);
            }
        }
        "array" => {
            if let Some(item) = object.get("item") {
                collect_named(item, module, declarations, imports);
            }
        }
        "generator" => {
            for key in ["yield", "send", "return"] {
                if let Some(value) = object.get(key) {
                    collect_named(value, module, declarations, imports);
                }
            }
        }
        "result" => {
            for key in ["ok", "error"] {
                if let Some(value) = object.get(key) {
                    collect_named(value, module, declarations, imports);
                }
            }
        }
        _ => {}
    }
}
fn validate_named(
    value: &Value,
    module: &str,
    declarations: &BTreeMap<String, String>,
    generic_parameters: &BTreeMap<String, Vec<Value>>,
    diagnostics: &mut Vec<EmitDiagnostic>,
) {
    let Some(object) = value.as_object() else {
        return;
    };
    match object
        .get("kind")
        .and_then(Value::as_str)
        .unwrap_or_default()
    {
        "named" => {
            let Some(name) = object.get("name").and_then(Value::as_str) else {
                return;
            };
            if !matches!(
                declarations.get(name).map(String::as_str),
                Some(
                    "alias"
                        | "external_type"
                        | "newtype"
                        | "struct"
                        | "enum"
                        | "resource"
                        | "trait"
                )
            ) {
                unsupported(module, format!("unknown named type `{name}`"), diagnostics);
            }
            let expected = generic_parameters
                .get(name)
                .map(Vec::as_slice)
                .unwrap_or_default();
            let actual = object
                .get("args")
                .and_then(Value::as_array)
                .map(Vec::as_slice)
                .unwrap_or_default();
            if expected.len() != actual.len() {
                unsupported(
                    module,
                    format!("generic argument arity for `{name}` is not exact"),
                    diagnostics,
                );
            }
            for (expected, actual) in expected.iter().zip(actual) {
                let expected_kind = expected.get("kind").and_then(Value::as_str);
                let actual_kind = actual.get("kind").and_then(Value::as_str);
                if expected_kind != actual_kind {
                    unsupported(
                        module,
                        format!("generic argument kind for `{name}` is not exact"),
                        diagnostics,
                    );
                    continue;
                }
                if expected_kind == Some("const") {
                    validate_const_generic_argument(actual, expected, module, diagnostics);
                } else if let Some(ty) = actual.get("type") {
                    validate_named(ty, module, declarations, generic_parameters, diagnostics);
                }
            }
        }
        "factory" => {
            let Some(instance) = object.get("instance").and_then(Value::as_object) else {
                unsupported(
                    module,
                    "Factory instance must be a named implementation",
                    diagnostics,
                );
                return;
            };
            let name = instance.get("name").and_then(Value::as_str);
            let arguments = instance.get("args").and_then(Value::as_array);
            if instance.get("kind").and_then(Value::as_str) != Some("named")
                || !arguments.is_some_and(Vec::is_empty)
                || !name
                    .is_some_and(|name| declarations.get(name).map(String::as_str) == Some("impl"))
            {
                unsupported(
                    module,
                    "Factory instance must be a named implementation",
                    diagnostics,
                );
            }
        }
        "associated_projection" => {
            if let Some(base) = object.get("base") {
                validate_named(base, module, declarations, generic_parameters, diagnostics);
            }
        }
        "list" | "set" | "option" | "iterator" => {
            if let Some(item) = object.get("item") {
                validate_named(item, module, declarations, generic_parameters, diagnostics);
            }
        }
        "map" => {
            for key in ["key", "value"] {
                if let Some(item) = object.get(key) {
                    validate_named(item, module, declarations, generic_parameters, diagnostics);
                }
            }
        }
        "tuple" => {
            for item in object
                .get("items")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                validate_named(item, module, declarations, generic_parameters, diagnostics);
            }
        }
        "array" => {
            if let Some(item) = object.get("item") {
                validate_named(item, module, declarations, generic_parameters, diagnostics);
            }
        }
        "result" => {
            for key in ["ok", "error"] {
                if let Some(item) = object.get(key) {
                    validate_named(item, module, declarations, generic_parameters, diagnostics);
                }
            }
        }
        "generator" => {
            for key in ["yield", "send", "return"] {
                if let Some(item) = object.get(key) {
                    validate_named(item, module, declarations, generic_parameters, diagnostics);
                }
            }
        }
        _ => {}
    }
}
fn validate_const_generic_argument(
    argument: &Value,
    parameter: &Value,
    module: &str,
    diagnostics: &mut Vec<EmitDiagnostic>,
) {
    let Some(value) = argument.get("value") else {
        unsupported(module, "const generic argument is missing", diagnostics);
        return;
    };
    validate_const_argument(
        value,
        parameter.get("type").and_then(Value::as_str),
        "generic",
        module,
        diagnostics,
    );
}

fn target_python_identity() -> (&'static str, &'static str) {
    match (std::env::consts::OS, std::env::consts::ARCH) {
        ("linux", "x86_64") => ("x86_64", "linux-x86_64"),
        ("linux", "aarch64") => ("arm64", "linux-aarch64"),
        ("macos", "x86_64") => ("x86_64", "macosx-unknown-x86_64"),
        ("macos", "aarch64") => ("arm64", "macosx-unknown-arm64"),
        _ => ("unknown", "unknown"),
    }
}
fn exported_names(module: &crate::python::artifact_plan::PythonArtifactModule) -> Vec<String> {
    let mut names = Vec::new();
    for declaration in &module.declarations {
        let Some(object) = declaration.as_object() else {
            continue;
        };
        let kind = object.get("kind").and_then(Value::as_str);
        if !object
            .get("public")
            .and_then(Value::as_bool)
            .unwrap_or(false)
            || matches!(kind, Some("function" | "scenario"))
        {
            continue;
        }
        names.push(
            local_name(
                object
                    .get("name")
                    .and_then(Value::as_str)
                    .unwrap_or_default(),
            )
            .to_owned(),
        );
        if object.get("kind").and_then(Value::as_str) == Some("enum") {
            names.extend(
                object
                    .get("variants")
                    .and_then(Value::as_array)
                    .into_iter()
                    .flatten()
                    .filter_map(|variant| variant.get("name").and_then(Value::as_str))
                    .map(|variant| {
                        format!(
                            "{}_{variant}",
                            local_name(
                                object
                                    .get("name")
                                    .and_then(Value::as_str)
                                    .unwrap_or_default()
                            )
                        )
                    }),
            );
        }
        if object.get("kind").and_then(Value::as_str) == Some("resource") {
            names.extend(
                object
                    .get("states")
                    .and_then(Value::as_array)
                    .into_iter()
                    .flatten()
                    .filter_map(|state| state.get("name").and_then(Value::as_str))
                    .map(|state| {
                        format!(
                            "{}_{}",
                            local_name(
                                object
                                    .get("name")
                                    .and_then(Value::as_str)
                                    .unwrap_or_default()
                            ),
                            local_name(state)
                        )
                    }),
            );
        }
    }
    names.sort();
    names
}

fn type_exported_names(module: &crate::python::artifact_plan::PythonArtifactModule) -> Vec<String> {
    let mut names = exported_names(module);
    names.retain(|name| {
        module.declarations.iter().all(|declaration| {
            declaration.as_object().is_none_or(|object| {
                object.get("kind").and_then(Value::as_str) != Some("impl")
                    || local_name(
                        object
                            .get("name")
                            .and_then(Value::as_str)
                            .unwrap_or_default(),
                    ) != name
            })
        })
    });
    names
}
fn render_doc(out: &mut String, value: Option<&Value>) {
    if let Some(text) = value
        .and_then(Value::as_object)
        .and_then(|doc| doc.get("text"))
        .and_then(Value::as_str)
    {
        out.push_str("\"\"\"");
        out.push_str(&text.replace('\\', "\\\\").replace("\"\"\"", "\\\"\\\"\\\""));
        out.push_str("\"\"\"\n");
    }
}
fn enum_variant_name(symbol: &str) -> String {
    let mut segments = symbol.rsplit('.');
    let variant = segments.next().unwrap_or_default();
    let enumeration = segments.next().unwrap_or_default();
    format!("{enumeration}_{variant}")
}
fn hash_stable_type(
    value: &Value,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    visiting: &mut BTreeSet<String>,
) -> bool {
    let Some(object) = value.as_object() else {
        return false;
    };
    match object.get("kind").and_then(Value::as_str) {
        Some("primitive") => matches!(
            object.get("name").and_then(Value::as_str),
            Some(
                "bool"
                    | "i8"
                    | "i16"
                    | "i32"
                    | "i64"
                    | "u8"
                    | "u16"
                    | "u32"
                    | "u64"
                    | "str"
                    | "bytes"
                    | "path"
            )
        ),
        Some("type_parameter") => false,
        Some("tuple") => object
            .get("items")
            .and_then(Value::as_array)
            .is_some_and(|items| {
                items
                    .iter()
                    .all(|item| hash_stable_type(item, modules, visiting))
            }),
        Some("named") => {
            let Some(symbol) = object.get("name").and_then(Value::as_str) else {
                return false;
            };
            if !visiting.insert(symbol.to_owned()) {
                return false;
            }
            let stable = modules
                .values()
                .flat_map(|module| &module.declarations)
                .filter_map(Value::as_object)
                .find(|declaration| declaration.get("name").and_then(Value::as_str) == Some(symbol))
                .is_some_and(
                    |declaration| match declaration.get("kind").and_then(Value::as_str) {
                        Some("newtype") => {
                            hash_stable_type(declaration.get("carrier").unwrap(), modules, visiting)
                        }
                        Some("enum") => declaration
                            .get("variants")
                            .and_then(Value::as_array)
                            .is_some_and(|variants| {
                                variants.iter().all(|variant| {
                                    variant
                                        .get("fields")
                                        .and_then(Value::as_array)
                                        .is_some_and(Vec::is_empty)
                                })
                            }),
                        _ => false,
                    },
                );
            visiting.remove(symbol);
            stable
        }
        _ => false,
    }
}
fn python_default_hashable_type(
    value: &Value,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    visiting: &mut BTreeSet<String>,
) -> bool {
    let Some(object) = value.as_object() else {
        return false;
    };
    match object.get("kind").and_then(Value::as_str) {
        Some("primitive") => !matches!(
            object.get("name").and_then(Value::as_str),
            Some("never" | "unit" | "json_value")
        ),
        Some("tuple") => object
            .get("items")
            .and_then(Value::as_array)
            .is_some_and(|items| {
                items
                    .iter()
                    .all(|item| hash_stable_type(item, modules, visiting))
            }),
        Some("named") => hash_stable_type(value, modules, visiting),
        _ => false,
    }
}

fn add_file(
    files: &mut BTreeMap<PathBuf, Vec<u8>>,
    diagnostics: &mut Vec<EmitDiagnostic>,
    path: PathBuf,
    bytes: Vec<u8>,
) {
    if files.insert(path.clone(), bytes).is_some() {
        diagnostics.push(diag(path, "colliding generated output path"));
    }
}
fn add_package_markers<'a>(
    files: &mut BTreeMap<PathBuf, Vec<u8>>,
    diagnostics: &mut Vec<EmitDiagnostic>,
    modules: impl Iterator<Item = &'a String>,
    bindings: &[ResolvedBinding],
) {
    add_file(
        files,
        diagnostics,
        PathBuf::from("python/__init__.py"),
        b"\n".to_vec(),
    );
    add_file(
        files,
        diagnostics,
        PathBuf::from("python/py.typed"),
        b"\n".to_vec(),
    );
    let mut dirs = BTreeSet::new();
    for id in modules {
        let parts: Vec<_> = id.split('.').collect();
        for n in 1..parts.len() {
            dirs.insert(parts[..n].join("/"));
        }
    }
    for binding in bindings {
        let path = path_string(&binding.generated_relative);
        let parts: Vec<_> = path.split('/').collect();
        for n in 1..parts.len().saturating_sub(1) {
            dirs.insert(parts[..=n].join("/"));
        }
    }
    for dir in dirs
        .into_iter()
        .filter(|dir| *dir != "_cott_impl" && !dir.starts_with("_cott_impl/"))
    {
        let base = PathBuf::from("python").join(dir);
        add_file(files, diagnostics, base.join("__init__.py"), b"\n".to_vec());
        add_file(files, diagnostics, base.join("py.typed"), b"\n".to_vec());
    }
}
fn binding_defines_symbol(bytes: &[u8], symbol: &str) -> bool {
    String::from_utf8_lossy(bytes).lines().any(|line| {
        line.trim_start()
            .strip_prefix("async ")
            .or_else(|| Some(line.trim_start()))
            .and_then(|line| line.strip_prefix("def "))
            .and_then(|rest| rest.split_once('('))
            .map(|(name, _)| name == symbol)
            .unwrap_or(false)
    })
}
fn exactly_one_newline(bytes: &[u8]) -> bool {
    bytes.ends_with(b"\n") && !bytes.ends_with(b"\n\n")
}
fn finish(mut bytes: Vec<u8>) -> Vec<u8> {
    while bytes.ends_with(b"\n") {
        bytes.pop();
    }
    bytes.push(b'\n');
    bytes
}
fn valid_binding_path(path: &Path) -> bool {
    !path.is_absolute() && {
        let value = path.to_string_lossy();
        value.starts_with("_cott_impl/")
            && !value.contains('\\')
            && !value
                .split('/')
                .any(|part| part.is_empty() || part == "." || part == "..")
            && value.ends_with(".py")
    }
}
fn binding_path(module: &str, kind: &PythonCallableKind, function: &str) -> PathBuf {
    let mut path = PathBuf::from("_cott_impl");
    for segment in module.split('.') {
        path.push(segment);
    }
    if let PythonCallableKind::ImplMethod { concrete }
    | PythonCallableKind::AsyncImplMethod { concrete } = kind
    {
        path.push(concrete);
    }
    path.push(format!("{function}.py"));
    path
}
fn type_path(module: &str) -> PathBuf {
    prefixed("python", module_file(module, "_types.py"))
}
fn facade_path(module: &str) -> PathBuf {
    prefixed("python", module_file(module, ".py"))
}
fn stub_path(module: &str) -> PathBuf {
    prefixed("stubs", module_file(module, ".pyi"))
}
fn ir_path_dotted(module: &str) -> PathBuf {
    let mut path = PathBuf::new();
    let mut segments = module.split('.');
    if let Some(last) = segments.next_back() {
        for segment in segments {
            path.push(segment);
        }
        path.push(format!("{last}.json"));
    }
    prefixed("ir", path)
}
fn module_file(module: &str, suffix: &str) -> PathBuf {
    let mut path = PathBuf::new();
    let segments: Vec<_> = module.split('.').collect();
    for segment in &segments[..segments.len().saturating_sub(1)] {
        path.push(segment);
    }
    if let Some(last) = segments.last() {
        path.push(format!("{last}{suffix}"));
    }
    path
}
fn type_module_name(module: &str) -> String {
    format!("{}_types", module)
}
fn valid_python_name(name: &str) -> bool {
    let mut chars = name.chars();
    let identifier = matches!(chars.next(), Some('_' | 'a'..='z' | 'A'..='Z'))
        && chars.all(|ch| ch == '_' || ch.is_ascii_alphanumeric());
    identifier
        && !name.starts_with("_cott_")
        && !(name.starts_with("__") && name.ends_with("__"))
        && !matches!(
            name,
            "False"
                | "None"
                | "True"
                | "and"
                | "as"
                | "assert"
                | "async"
                | "await"
                | "break"
                | "class"
                | "continue"
                | "def"
                | "del"
                | "elif"
                | "else"
                | "except"
                | "finally"
                | "for"
                | "from"
                | "global"
                | "if"
                | "import"
                | "in"
                | "is"
                | "lambda"
                | "nonlocal"
                | "not"
                | "or"
                | "pass"
                | "raise"
                | "return"
                | "try"
                | "while"
                | "with"
                | "yield"
        )
}

fn python_support_names() -> &'static [&'static str] {
    &[
        "Annotated",
        "Any",
        "CottArray",
        "CottBuffer",
        "CottContractViolation",
        "CottExternal",
        "CottList",
        "CottSet",
        "Err",
        "F32",
        "F64",
        "Final",
        "FrozenMap",
        "Generator",
        "Generic",
        "I8",
        "I16",
        "I32",
        "I64",
        "JsonArray",
        "JsonBoolean",
        "JsonFloat",
        "JsonInteger",
        "JsonNull",
        "JsonObject",
        "JsonString",
        "JsonValue",
        "Literal",
        "Iterator",
        "Never",
        "Nothing",
        "Ok",
        "Opaque",
        "Option",
        "Path",
        "Protocol",
        "Result",
        "Some",
        "TypeAlias",
        "TypeVar",
        "U8",
        "U16",
        "U32",
        "U64",
        "UNIT",
        "Union",
        "Unit",
        "dataclass",
        "final",
        "runtime_checkable",
    ]
}

fn module_path(module: &str) -> PathBuf {
    PathBuf::from(module)
}
fn prefixed(prefix: &str, path: PathBuf) -> PathBuf {
    PathBuf::from(prefix).join(path)
}
fn path_string(path: &Path) -> String {
    path.to_string_lossy().replace('\\', "/")
}
fn local_name(name: &str) -> &str {
    name.rsplit('.').next().unwrap_or(name)
}
fn json_string(value: &str) -> String {
    let mut out = String::with_capacity(value.len() + 2);
    out.push('"');
    for ch in value.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if c.is_control() => write!(out, "\\u{:04x}", c as u32).unwrap(),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}
fn required_string(
    object: &serde_json::Map<String, Value>,
    field: &str,
    module: &str,
    diagnostics: &mut Vec<EmitDiagnostic>,
) -> Option<String> {
    match object.get(field).and_then(Value::as_str) {
        Some(value) => Some(value.to_owned()),
        None => {
            diagnostics.push(diag(
                module_path(module),
                format!("missing or invalid `{field}` field"),
            ));
            None
        }
    }
}
fn required_value<'a>(
    object: &'a serde_json::Map<String, Value>,
    field: &str,
    module: &str,
    diagnostics: &mut Vec<EmitDiagnostic>,
) -> Option<&'a Value> {
    match object.get(field) {
        Some(value) => Some(value),
        None => {
            diagnostics.push(diag(
                module_path(module),
                format!("missing `{field}` field"),
            ));
            None
        }
    }
}
fn required_array<'a>(
    object: &'a serde_json::Map<String, Value>,
    field: &str,
    module: &str,
    diagnostics: &mut Vec<EmitDiagnostic>,
) -> Option<&'a Vec<Value>> {
    match object.get(field).and_then(Value::as_array) {
        Some(value) => Some(value),
        None => {
            diagnostics.push(diag(
                module_path(module),
                format!("missing or invalid `{field}` field"),
            ));
            None
        }
    }
}
fn unsupported(module: &str, message: impl Into<String>, diagnostics: &mut Vec<EmitDiagnostic>) {
    diagnostics.push(diag(module_path(module), message));
}
fn diag(path: impl Into<PathBuf>, message: impl Into<String>) -> EmitDiagnostic {
    EmitDiagnostic {
        path: path.into(),
        message: message.into(),
    }
}
