use std::collections::{BTreeMap, BTreeSet, HashSet};
use std::fmt::Write as _;
use std::path::{Path, PathBuf};

use serde_json::{Value, json};

use crate::binding::{BindingOwner, ResolvedBinding};
use crate::contract_test::derive_strategies;
use crate::hash::sha256_hex;
use crate::ir::CanonicalIr;
use crate::manifest::{ProjectConfig, RuntimeValidation};
use crate::provenance::{GenerationRecord, GenerationSnapshot};
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
    let callables = plan
        .callables()
        .into_iter()
        .map(|callable| (callable.cott_symbol.clone(), callable))
        .collect::<BTreeMap<_, _>>();
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
                validate_named(ty, &module.module, &declarations, &mut diagnostics);
            }
            if kind == "struct" {
                if let Some(fields) = object.get("fields").and_then(Value::as_array) {
                    for field in fields {
                        if let Some(ty) = field.get("type") {
                            validate_named(ty, &module.module, &declarations, &mut diagnostics);
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
        for (source, names) in referenced_imports(module, &declarations) {
            for name in names {
                owners.entry(name).or_default().insert(source.clone());
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
    for (path, bytes) in render_runtime(&config.project.name) {
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
            finish(render_types(module, &modules, &declarations)),
        );
        add_file(
            &mut files,
            &mut diagnostics,
            facade_path(&module.module),
            finish(render_facade(module, bindings, &declarations, config)),
        );
        add_file(
            &mut files,
            &mut diagnostics,
            stub_path(&module.module),
            finish(render_stub(module, &declarations)),
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
    match derive_strategies(ir) {
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
            let (kind, concrete, method) = match &binding.kind {
                PythonCallableKind::Function => ("function", Value::Null, Value::Null),
                PythonCallableKind::ImplMethod { concrete } => (
                    "impl_method",
                    Value::String(concrete.clone()),
                    Value::String(binding.function.clone()),
                ),
            };
            json!({
                "content_hash": format!("sha256:{}", binding.sha256),
                "concrete": concrete,
                "cott_symbol": binding.cott_symbol,
                "kind": kind,
                "method": method,
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
        .keys()
        .filter(|symbol| !seen_bindings.contains(*symbol))
        .cloned()
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
            "runtime": {"abi": "1", "version": env!("CARGO_PKG_VERSION")},
        }),
        ir: Value::Object(ir_hashes),
        contract_surface,
        public_python_symbols: Value::Object(public_python_symbols),
        implementations: Value::Array(implementation_symbols),
        dependencies: json!([]),
        managed_files,
        unresolved,
        verification: Value::Null,
        agent_runs: Vec::new(),
    };
    if let Err(error) = snapshot.compute_generation_id() {
        diagnostics.push(diag(
            "generation.json",
            format!("failed to compute generation identity: {error}"),
        ));
    } else {
        let record = GenerationRecord {
            schema_version: 1,
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
    match kind {
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
        "struct" => validate_fields(object, "fields", module, diagnostics),
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
        "trait" => {
            if let Some(methods) = required_array(object, "methods", module, diagnostics) {
                for method in methods {
                    let Some(method) = method.as_object() else {
                        unsupported(module, "trait method must be an object", diagnostics);
                        continue;
                    };
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
        "rule" => {}
        "function" => {
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
        }
        other => unsupported(
            module,
            format!("canonical declaration kind `{other}` is unsupported"),
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
            if let Some(args) = object.get("args").and_then(Value::as_array) {
                for arg in args {
                    validate_type(arg, module, diagnostics);
                }
            }
        }
        "type_parameter" => {
            required_string(object, "name", module, diagnostics);
        }
        "list" | "set" | "option" => {
            if let Some(item) = required_value(object, "item", module, diagnostics) {
                validate_type(item, module, diagnostics);
            }
        }
        "map" => {
            for field in ["key", "value"] {
                if let Some(item) = required_value(object, field, module, diagnostics) {
                    validate_type(item, module, diagnostics);
                }
            }
        }
        "tuple2" => {
            for field in ["first", "second"] {
                if let Some(item) = required_value(object, field, module, diagnostics) {
                    validate_type(item, module, diagnostics);
                }
            }
        }
        "result" => {
            for field in ["ok", "error"] {
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
        "tuple2" => {
            for field in ["first", "second"] {
                if let Some(item) = required_value(object, field, module, diagnostics) {
                    validate_value(item, module, diagnostics);
                }
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

fn render_types(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    modules: &BTreeMap<String, &crate::python::artifact_plan::PythonArtifactModule>,
    declarations: &BTreeMap<String, String>,
) -> Vec<u8> {
    let mut out = String::from(
        "from __future__ import annotations\n\nimport dataclasses as _dataclasses\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom typing import Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable\n\nfrom cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi\n",
    );
    let imports = referenced_imports(module, declarations);
    for (source, names) in &imports {
        writeln!(
            out,
            "from {} import {}",
            type_module_name(source),
            names.iter().cloned().collect::<Vec<_>>().join(", ")
        )
        .unwrap();
    }
    if !imports.is_empty() {
        out.push('\n');
    }
    let has_generics = module.declarations.iter().any(|declaration| {
        declaration
            .get("generics")
            .and_then(Value::as_array)
            .is_some_and(|generics| !generics.is_empty())
    });
    render_generic_typevars(&mut out, module, declarations, false, true);
    if has_generics {
        out.push('\n');
    }
    for declaration in &module.declarations {
        render_type_declaration(&mut out, declaration, module, modules, declarations);
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
            let base = if generics.is_empty() {
                "Protocol".to_owned()
            } else {
                format!("Protocol[{generics}]")
            };
            writeln!(out, "@runtime_checkable\nclass {name}({base}):").unwrap();
            let methods = object.get("methods").and_then(Value::as_array).unwrap();
            if methods.is_empty() {
                out.push_str("    pass\n\n");
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
                        "    def {method_name}({signature}) -> {return_type}:\n        ...\n"
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
            signatures.insert(
                serde_json::to_string(generic.get("bounds").unwrap_or(&Value::Null))
                    .expect("generic bounds serialize"),
            );
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
            if bounds.len() > 1 && render_composites {
                render_bound_protocol(out, module, declarations, &typevar, &bounds);
            }
            let declaration = match bounds.as_slice() {
                [bound] => format!(
                    ", bound={}",
                    render_type(bound, &module.module, declarations)
                ),
                [_first, ..] => format!(", bound=_cott_{typevar}_Bounds"),
                [] => String::new(),
            };
            writeln!(
                out,
                "{typevar} = TypeVar({}{declaration})",
                json_string(&typevar)
            )
            .unwrap();
        }
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
fn render_facade(
    module: &crate::python::artifact_plan::PythonArtifactModule,

    bindings: &[ResolvedBinding],
    declarations: &BTreeMap<String, String>,
    config: &ProjectConfig,
) -> Vec<u8> {
    let mut out = String::from(
        "from __future__ import annotations\n\nimport dataclasses as _dataclasses\nimport threading as _threading\nfrom pathlib import Path\nfrom typing import Literal, Never, Protocol, TypeVar, final\n\nfrom cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi\n",
    );
    let names = exported_names(module);
    let mut local_imports = type_exported_names(module);
    local_imports.extend(function_bound_protocol_names(module));
    if !local_imports.is_empty() {
        writeln!(
            out,
            "\nfrom {} import {}",
            type_module_name(&module.module),
            local_imports.join(", ")
        )
        .unwrap();
    }
    for (source, names) in referenced_imports(module, declarations) {
        writeln!(
            out,
            "from {} import {}",
            type_module_name(&source),
            names.into_iter().collect::<Vec<_>>().join(", ")
        )
        .unwrap();
    }
    render_function_typevars(&mut out, module, declarations, false);
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
        writeln!(out, "\ndef {function}({signature}) -> {return_type}:").unwrap();
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
        writeln!(out, "        _result = _implementation({call})").unwrap();
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
    render_impl_classes(
        &mut out,
        module,
        bindings,
        declarations,
        config,
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

fn render_impl_classes(
    out: &mut String,
    module: &crate::python::artifact_plan::PythonArtifactModule,
    bindings: &[ResolvedBinding],
    declarations: &BTreeMap<String, String>,
    config: &ProjectConfig,
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
        writeln!(out, "\n@final\nclass {name}:").unwrap();
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
        out.push_str("        self._cott_lock = _threading.RLock()\n");
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

        for method in implementation
            .get("methods")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(Value::as_object)
        {
            let method_name = method
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default();
            let cott_symbol = format!("{}.{}.{}", module.module, name, method_name);
            let Some(binding) = bindings
                .iter()
                .find(|binding| binding.cott_symbol == cott_symbol)
            else {
                continue;
            };
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
            writeln!(
                out,
                "\n    def {method_name}({signature}) -> {return_type}:"
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
            out.push_str("        with self._cott_lock:\n");
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
                "                _result = _implementation(self{}{})",
                if call.is_empty() { "" } else { ", " },
                call
            )
            .unwrap();
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
            out.push_str("            return _result\n");
        }
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
        let span = serde_json::to_string(invariant.get("span").unwrap()).expect("span serializes");
        let label = format!(
            "invariant:{}",
            invariant
                .get("clause_id")
                .and_then(Value::as_u64)
                .unwrap_or_default()
        );
        writeln!(
            out,
            "{prefix}if not ({expression}):\n{prefix}    raise CottContractViolation(\"invariant failed\", symbol={}, clause={}, phase=\"invariant\", span={span}, expected=\"true\", actual=\"false\")",
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
        let span = serde_json::to_string(clause.get("span").unwrap()).expect("span serializes");
        let symbol = function
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or_default();
        writeln!(
            out,
            "    if not ({expression}):\n        raise CottContractViolation(\"requires clause failed\", symbol={}, clause={}, phase=\"requires\", span={span}, expected=\"true\", actual=\"false\")",
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
            let Some(condition) = clause.get("when").filter(|value| !value.is_null()) else {
                continue;
            };
            let variant = enum_variant_name(
                clause
                    .get("variant")
                    .and_then(Value::as_str)
                    .unwrap_or_default(),
            );
            let span = serde_json::to_string(clause.get("span").unwrap()).expect("span serializes");
            let label = clause_label(clause);
            writeln!(
                out,
                "    if _expected_error is None and ({}):\n        _expected_error = {variant}\n        _expected_error_span = {span}\n        _expected_error_clause = {}",
                render_contract_expression(condition),
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
        let pattern = clause.get("pattern").filter(|value| !value.is_null());
        if let Some(pattern) = pattern {
            let (guard, bindings) = render_pattern(pattern, "_result");
            writeln!(out, "    if {guard}:").unwrap();
            for binding in bindings {
                writeln!(out, "        {binding}").unwrap();
            }
            writeln!(
                out,
                "        if not ({expression}):\n            raise CottContractViolation(\"ensures clause failed\", symbol={}, clause={}, phase=\"ensures\", span={span}, expected=\"true\", actual=\"false\")",
                json_string(symbol),
                json_string(&label),
            )
            .unwrap();
        } else {
            writeln!(
                out,
                "    if not ({expression}):\n        raise CottContractViolation(\"ensures clause failed\", symbol={}, clause={}, phase=\"ensures\", span={span}, expected=\"true\", actual=\"false\")",
                json_string(symbol),
                json_string(&label),
            )
            .unwrap();
        }
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
                    .unwrap_or("_binding")
            )],
        ),
        "variant" => {
            let symbol = pattern
                .get("symbol")
                .and_then(Value::as_str)
                .unwrap_or_default();
            let variant = if symbol.split('.').count() >= 3 {
                enum_variant_name(symbol)
            } else {
                local_name(symbol).to_owned()
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
) -> Vec<u8> {
    let mut out = String::from(
        "from __future__ import annotations\n\nfrom pathlib import Path\nfrom typing import Literal, Never, Protocol, TypeVar, final\n\nfrom cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit\n",
    );
    let names = exported_names(module);
    let type_names = type_exported_names(module);
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
    for (source, names) in referenced_imports(module, declarations) {
        writeln!(
            out,
            "from {} import {}",
            type_module_name(&source),
            names.into_iter().collect::<Vec<_>>().join(", ")
        )
        .unwrap();
    }
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
        writeln!(out, "def {name}({signature}) -> {return_type}: ...\n").unwrap();
        exported.push(name.to_owned());
    }
    render_impl_stubs(&mut out, module, declarations);
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
        for method in implementation
            .get("methods")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(Value::as_object)
        {
            let method_name = method
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default();
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
                "    def {method_name}({signature}) -> {return_type}: ..."
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
            "never" => "Never",
            _ => "object",
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
                .map(|argument| {
                    render_type_with_names(argument, module, declarations, typevar_names)
                })
                .collect::<Vec<_>>();
            if args.is_empty() {
                name.to_owned()
            } else {
                format!("{name}[{}]", args.join(", "))
            }
        }
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
        "tuple2" => format!(
            "CottTuple2[{}, {}]",
            render_type_with_names(
                object.get("first").unwrap(),
                module,
                declarations,
                typevar_names
            ),
            render_type_with_names(
                object.get("second").unwrap(),
                module,
                declarations,
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
        "opaque" => format!(
            "Opaque[Literal[{}]]",
            json_string(
                object
                    .get("tag")
                    .and_then(Value::as_str)
                    .unwrap_or_default()
            )
        ),
        _ => "object".into(),
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
        "tuple2" => format!(
            "CottTuple2(first={}, second={})",
            render_value(object.get("first").unwrap()),
            render_value(object.get("second").unwrap())
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
        _ => "None".into(),
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
fn referenced_imports(
    module: &crate::python::artifact_plan::PythonArtifactModule,
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
        for generic in object
            .get("generics")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
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
    imports
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
        if declarations.get(owner).map(String::as_str) != Some("enum") {
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
                Some("alias" | "newtype" | "struct" | "enum" | "trait" | "const")
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
                collect_named(argument, module, declarations, imports);
            }
        }
        "list" | "set" | "option" => {
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
        "tuple2" => {
            for key in ["first", "second"] {
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
            if let Some(name) = object.get("name").and_then(Value::as_str) {
                if !matches!(
                    declarations.get(name).map(String::as_str),
                    Some("alias" | "newtype" | "struct" | "enum")
                ) {
                    unsupported(
                        module,
                        format!("unknown or non-type named declaration `{name}`"),
                        diagnostics,
                    );
                }
            }
        }
        "option" => {
            if let Some(item) = object.get("item") {
                validate_named(item, module, declarations, diagnostics);
            }
        }
        "result" => {
            if let Some(item) = object.get("ok") {
                validate_named(item, module, declarations, diagnostics);
            }
            if let Some(item) = object.get("error") {
                validate_named(item, module, declarations, diagnostics);
            }
        }
        _ => {}
    }
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
        if !object
            .get("public")
            .and_then(Value::as_bool)
            .unwrap_or(false)
            || object.get("kind").and_then(Value::as_str) == Some("function")
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
        Some("tuple2") => {
            hash_stable_type(object.get("first").unwrap(), modules, visiting)
                && hash_stable_type(object.get("second").unwrap(), modules, visiting)
        }
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
        Some("tuple2") => true,
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
    dirs.insert("_cott_impl".into());
    for binding in bindings {
        let path = path_string(&binding.generated_relative);
        let parts: Vec<_> = path.split('/').collect();
        for n in 1..parts.len().saturating_sub(1) {
            dirs.insert(parts[..=n].join("/"));
        }
    }
    for dir in dirs {
        let base = PathBuf::from("python").join(dir);
        add_file(files, diagnostics, base.join("__init__.py"), b"\n".to_vec());
        add_file(files, diagnostics, base.join("py.typed"), b"\n".to_vec());
    }
}
fn binding_defines_symbol(bytes: &[u8], symbol: &str) -> bool {
    String::from_utf8_lossy(bytes).lines().any(|line| {
        line.trim_start()
            .strip_prefix("def ")
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
    if let PythonCallableKind::ImplMethod { concrete } = kind {
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
        "CottContractViolation",
        "CottList",
        "CottSet",
        "CottTuple2",
        "Err",
        "F32",
        "F64",
        "Final",
        "FrozenMap",
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
