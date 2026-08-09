use std::collections::{BTreeMap, BTreeSet, HashSet};
use std::fmt::Write as _;
use std::path::{Path, PathBuf};

use serde_json::Value;

use crate::binding::ResolvedBinding;
use crate::hash::sha256_hex;
use crate::ir::CanonicalIr;
use crate::python::artifact_plan::PythonArtifactPlan;
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
    project_name: &str,
    plan: &PythonArtifactPlan,
    ir: &CanonicalIr,
    bindings: &[ResolvedBinding],
) -> Result<Emission, Vec<EmitDiagnostic>> {
    let mut diagnostics = Vec::new();
    let mut modules = BTreeMap::<String, _>::new();
    for module in plan.modules() {
        if modules.insert(module.module.clone(), module).is_some() {
            diagnostics.push(diag(
                module_path(&module.module),
                "duplicate canonical module",
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
    let functions: BTreeSet<(String, String)> = declarations
        .iter()
        .filter_map(|(name, kind)| {
            (kind == "function").then(|| {
                let (module, function) = name.rsplit_once('.').unwrap_or(("", name));
                (module.to_owned(), function.to_owned())
            })
        })
        .collect();
    let mut seen_bindings = BTreeSet::new();
    let mut seen_paths = HashSet::new();
    for binding in bindings {
        let function = local_name(&binding.function);
        let key = (binding.module.clone(), function.to_owned());
        if !functions.contains(&key) {
            diagnostics.push(diag(
                binding.source.clone(),
                format!(
                    "binding does not match a canonical function: {}",
                    binding.function
                ),
            ));
        } else if !seen_bindings.insert(key) {
            diagnostics.push(diag(
                binding.source.clone(),
                "duplicate binding for canonical function",
            ));
        }
        let expected = binding_path(&binding.module, function);
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
        if !binding_defines_symbol(&binding.bytes, function) {
            diagnostics.push(diag(
                binding.source.clone(),
                format!("binding does not define symbol {function}"),
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
    if !diagnostics.is_empty() {
        return Err(diagnostics);
    }
    let mut files = BTreeMap::new();
    for (path, bytes) in render_runtime(project_name) {
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
            finish(render_types(module, &declarations)),
        );
        add_file(
            &mut files,
            &mut diagnostics,
            facade_path(&module.module),
            finish(render_facade(module, bindings)),
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
    let mut ordered: Vec<_> = bindings.iter().collect();
    ordered.sort_by(|a, b| {
        (a.module.clone(), a.function.clone()).cmp(&(b.module.clone(), b.function.clone()))
    });
    let mut metadata = String::from("{\"bindings\":[");
    for (index, binding) in ordered.iter().enumerate() {
        if index != 0 {
            metadata.push(',');
        }
        write!(
            metadata,
            "{{\"function\":{},\"module\":{},\"path\":{},\"sha256\":{}}}",
            json_string(&binding.function),
            json_string(&binding.module),
            json_string(&path_string(&binding.generated_relative)),
            json_string(&binding.sha256)
        )
        .unwrap();
    }
    write!(metadata, "],\"managed_files\":{{").unwrap();
    for (index, (path, bytes)) in files.iter().enumerate() {
        if index != 0 {
            metadata.push(',');
        }
        write!(
            metadata,
            "{}:{}",
            json_string(&path_string(path)),
            json_string(&sha256_hex(bytes))
        )
        .unwrap();
    }
    write!(
        metadata,
        "}},\"project\":{},\"verified\":false}}",
        json_string(project_name)
    )
    .unwrap();
    add_file(
        &mut files,
        &mut diagnostics,
        PathBuf::from("generation.json"),
        finish(metadata.into_bytes()),
    );
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
            if object
                .get("refinement")
                .is_some_and(|value| !value.is_null())
            {
                unsupported(module, "newtype refinements are unsupported", diagnostics);
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
        "const" => {
            if let Some(ty) = required_value(object, "type", module, diagnostics) {
                validate_type(ty, module, diagnostics);
            }
            if let Some(value) = required_value(object, "value", module, diagnostics) {
                validate_value(value, module, diagnostics);
            }
        }
        "function" => {
            let Some(parameters) = required_array(object, "parameters", module, diagnostics) else {
                return;
            };
            if !parameters.is_empty() {
                unsupported(
                    module,
                    "functions with parameters are unsupported",
                    diagnostics,
                );
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
                    | "unit"
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
            if object
                .get("args")
                .and_then(Value::as_array)
                .is_some_and(|args| !args.is_empty())
            {
                unsupported(module, "generic named types are unsupported", diagnostics);
            }
        }
        "option" => {
            if let Some(item) = required_value(object, "item", module, diagnostics) {
                validate_type(item, module, diagnostics);
            }
        }
        "result" => {
            if let Some(item) = required_value(object, "ok", module, diagnostics) {
                validate_type(item, module, diagnostics);
            }
            if let Some(item) = required_value(object, "error", module, diagnostics) {
                validate_type(item, module, diagnostics);
            }
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
            if object.get("value").and_then(Value::as_array).is_none() {
                unsupported(module, "byte value is missing", diagnostics);
            }
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
    declarations: &BTreeMap<String, String>,
) -> Vec<u8> {
    let mut out = String::from(
        "from __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom typing import TypeAlias, Union\n\nfrom cott_runtime import Option, Result, UNIT, Unit\n",
    );
    let imports = referenced_imports(module, declarations);
    for (source, names) in &imports {
        writeln!(
            out,
            "from {}_types import {}",
            type_module_name(source),
            names.iter().cloned().collect::<Vec<_>>().join(", ")
        )
        .unwrap();
    }
    if !imports.is_empty() {
        out.push('\n');
    }
    for declaration in &module.declarations {
        render_type_declaration(&mut out, declaration, module, declarations);
    }
    let names = exported_names(module);
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
    declarations: &BTreeMap<String, String>,
) {
    let object = declaration.as_object().unwrap();
    let kind = object.get("kind").and_then(Value::as_str).unwrap();
    let name = local_name(
        object
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or_default(),
    );
    render_doc(out, object.get("doc"));
    match kind {
        "alias" => writeln!(
            out,
            "{name}: TypeAlias = {}\n",
            render_type(object.get("target").unwrap(), &module.module, declarations)
        )
        .unwrap(),
        "newtype" => writeln!(
            out,
            "@dataclass(frozen=True, slots=True, kw_only=True)\nclass {name}:\n    value: {}\n",
            render_type(object.get("carrier").unwrap(), &module.module, declarations)
        )
        .unwrap(),
        "struct" => {
            writeln!(
                out,
                "@dataclass(frozen=True, slots=True, kw_only=True)\nclass {name}:"
            )
            .unwrap();
            let fields = object.get("fields").and_then(Value::as_array).unwrap();
            if fields.is_empty() {
                out.push_str("    pass\n\n");
            } else {
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
                        render_type(field.get("type").unwrap(), &module.module, declarations)
                    )
                    .unwrap();
                    if let Some(value) = field.get("default").filter(|value| !value.is_null()) {
                        write!(out, " = {}", render_value(value)).unwrap();
                    }
                    out.push('\n');
                }
                out.push('\n');
            }
        }
        "enum" => {
            let variants = object.get("variants").and_then(Value::as_array).unwrap();
            for variant in variants {
                let variant = variant.as_object().unwrap();
                let variant_name = local_name(
                    variant
                        .get("name")
                        .and_then(Value::as_str)
                        .unwrap_or_default(),
                );
                let fields = variant.get("fields").and_then(Value::as_array).unwrap();
                writeln!(
                    out,
                    "@dataclass(frozen=True, slots=True, kw_only=True)\nclass {variant_name}:"
                )
                .unwrap();
                if fields.is_empty() {
                    out.push_str("    pass\n\n");
                } else {
                    for field in fields {
                        let field = field.as_object().unwrap();
                        writeln!(
                            out,
                            "    {}: {}",
                            local_name(
                                field
                                    .get("name")
                                    .and_then(Value::as_str)
                                    .unwrap_or_default()
                            ),
                            render_type(field.get("type").unwrap(), &module.module, declarations)
                        )
                        .unwrap();
                    }
                    out.push('\n');
                }
            }
            writeln!(
                out,
                "{name}: TypeAlias = Union[{}]\n",
                variants
                    .iter()
                    .map(|variant| local_name(
                        variant
                            .get("name")
                            .and_then(Value::as_str)
                            .unwrap_or_default()
                    ))
                    .collect::<Vec<_>>()
                    .join(", ")
            )
            .unwrap();
        }
        "const" => writeln!(
            out,
            "{name}: {} = {}\n",
            render_type(object.get("type").unwrap(), &module.module, declarations),
            render_value(object.get("value").unwrap())
        )
        .unwrap(),
        "function" => {}
        _ => {}
    }
}
fn render_facade(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    bindings: &[ResolvedBinding],
) -> Vec<u8> {
    let mut out =
        String::from("from __future__ import annotations\n\nfrom cott_runtime import _cott_load\n");
    let names = exported_names(module);
    if !names.is_empty() {
        writeln!(
            out,
            "\nfrom {} import {}",
            type_module_name(&module.module),
            names.join(", ")
        )
        .unwrap();
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
        if let Some(binding) = bindings.iter().find(|binding| {
            binding.module == module.module && local_name(&binding.function) == function
        }) {
            writeln!(
                out,
                "\n{function} = _cott_load({}, {}, {})",
                json_string(&path_string(&binding.generated_relative)),
                json_string(&binding.sha256),
                json_string(function)
            )
            .unwrap();
            if object
                .get("public")
                .and_then(Value::as_bool)
                .unwrap_or(false)
            {
                exported.push(function.to_owned());
            }
        }
    }
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
fn render_stub(
    module: &crate::python::artifact_plan::PythonArtifactModule,
    declarations: &BTreeMap<String, String>,
) -> Vec<u8> {
    let mut out =
        String::from("from __future__ import annotations\n\nfrom typing import TypeAlias, Union\n");
    let names = exported_names(module);
    if !names.is_empty() {
        writeln!(
            out,
            "\nfrom {} import {}",
            type_module_name(&module.module),
            names.join(", ")
        )
        .unwrap();
    }
    for (source, names) in referenced_imports(module, declarations) {
        writeln!(
            out,
            "from {}_types import {}",
            type_module_name(&source),
            names.into_iter().collect::<Vec<_>>().join(", ")
        )
        .unwrap();
    }
    for declaration in &module.declarations {
        let object = declaration.as_object().unwrap();
        let kind = object.get("kind").and_then(Value::as_str).unwrap();
        let name = local_name(
            object
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        );
        render_doc(&mut out, object.get("doc"));
        match kind {
            "alias" => writeln!(
                out,
                "{name}: TypeAlias = {}\n",
                render_type(object.get("target").unwrap(), &module.module, declarations)
            )
            .unwrap(),
            "newtype" | "struct" => writeln!(out, "class {name}: ...\n").unwrap(),
            "enum" => {
                let variants = object.get("variants").and_then(Value::as_array).unwrap();
                writeln!(
                    out,
                    "{name}: TypeAlias = Union[{}]\n",
                    variants
                        .iter()
                        .map(|v| local_name(
                            v.get("name").and_then(Value::as_str).unwrap_or_default()
                        ))
                        .collect::<Vec<_>>()
                        .join(", ")
                )
                .unwrap();
            }
            "const" => writeln!(
                out,
                "{name}: {}\n",
                render_type(object.get("type").unwrap(), &module.module, declarations)
            )
            .unwrap(),
            "function" => writeln!(
                out,
                "def {name}() -> {}: ...\n",
                render_type(
                    object.get("return_type").unwrap(),
                    &module.module,
                    declarations
                )
            )
            .unwrap(),
            _ => {}
        }
    }
    out.into_bytes()
}
fn render_type(value: &Value, _module: &str, _declarations: &BTreeMap<String, String>) -> String {
    let object = value.as_object().unwrap();
    match object.get("kind").and_then(Value::as_str).unwrap() {
        "primitive" => match object.get("name").and_then(Value::as_str).unwrap() {
            "bool" => "bool",
            "i8" | "i16" | "i32" | "i64" | "u8" | "u16" | "u32" | "u64" => "int",
            "f32" | "f64" => "float",
            "str" => "str",
            "bytes" => "bytes",
            "unit" => "Unit",
            other => other,
        }
        .into(),
        "named" => local_name(
            object
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        )
        .into(),
        "option" => format!(
            "Option[{}]",
            render_type(object.get("item").unwrap(), _module, _declarations)
        ),
        "result" => format!(
            "Result[{}, {}]",
            render_type(object.get("ok").unwrap(), _module, _declarations),
            render_type(object.get("error").unwrap(), _module, _declarations)
        ),
        _ => "typing.Any".into(),
    }
}
fn render_value(value: &Value) -> String {
    let object = value.as_object().unwrap();
    match object.get("kind").and_then(Value::as_str).unwrap() {
        "bool" => object.get("value").unwrap().to_string(),
        "integer" | "string" => object
            .get("value")
            .map(|value| {
                if value.is_string() {
                    json_string(value.as_str().unwrap())
                } else {
                    value.to_string()
                }
            })
            .unwrap_or_default(),
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
            "bytes([{}])",
            object
                .get("value")
                .and_then(Value::as_array)
                .map(|values| values
                    .iter()
                    .map(Value::to_string)
                    .collect::<Vec<_>>()
                    .join(", "))
                .unwrap_or_default()
        ),
        "unit" => "UNIT".into(),
        _ => "None".into(),
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
        if matches!(kind, "struct" | "enum") {
            if let Some(groups) = object
                .get(if kind == "struct" {
                    "fields"
                } else {
                    "variants"
                })
                .and_then(Value::as_array)
            {
                for group in groups {
                    let fields = if kind == "struct" {
                        Some(group)
                    } else {
                        group.get("fields")
                    };
                    if let Some(fields) = fields.and_then(Value::as_array) {
                        for field in fields {
                            if let Some(ty) = field.get("type") {
                                collect_named(ty, &module.module, declarations, &mut imports);
                            }
                        }
                    }
                }
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
                if let Some((source, local)) = name.rsplit_once('.') {
                    if source != module
                        && matches!(
                            declarations.get(name).map(String::as_str),
                            Some("alias" | "newtype" | "struct" | "enum")
                        )
                    {
                        imports
                            .entry(source.to_owned())
                            .or_default()
                            .insert(local.to_owned());
                    }
                }
            }
        }
        "option" => {
            if let Some(item) = object.get("item") {
                collect_named(item, module, declarations, imports);
            }
        }
        "result" => {
            if let Some(item) = object.get("ok") {
                collect_named(item, module, declarations, imports);
            }
            if let Some(item) = object.get("error") {
                collect_named(item, module, declarations, imports);
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
fn exported_names(module: &crate::python::artifact_plan::PythonArtifactModule) -> Vec<String> {
    module
        .declarations
        .iter()
        .filter_map(|declaration| {
            let object = declaration.as_object()?;
            if !object
                .get("public")
                .and_then(Value::as_bool)
                .unwrap_or(false)
            {
                return None;
            }
            let kind = object.get("kind").and_then(Value::as_str)?;
            (kind != "function").then(|| {
                local_name(
                    object
                        .get("name")
                        .and_then(Value::as_str)
                        .unwrap_or_default(),
                )
                .to_owned()
            })
        })
        .collect()
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
fn binding_path(module: &str, function: &str) -> PathBuf {
    let mut path = PathBuf::from("_cott_impl");
    for segment in module.split('.') {
        path.push(segment);
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
