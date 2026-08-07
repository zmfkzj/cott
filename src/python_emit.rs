use std::collections::{BTreeMap, BTreeSet, HashSet};
use std::fmt::Write as _;
use std::path::{Path, PathBuf};

use crate::binding::ResolvedBinding;
use crate::hash::sha256_hex;
use crate::ir::CanonicalIr;
use crate::project::Project;
use crate::python_runtime::render_runtime;
use crate::semantic::{
    ModuleId, PrimitiveType, ResolvedType, SemanticDeclaration, SemanticEnum, SemanticFunction,
    SemanticModule, SemanticProject, SemanticValue, SymbolId,
};

/// The complete, in-memory Python artifact tree.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Emission {
    pub files: BTreeMap<PathBuf, Vec<u8>>,
    pub entry_module: ModuleId,
    pub entry_function: String,
}

/// A deterministic error attached to one generated artifact path.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EmitDiagnostic {
    pub path: PathBuf,
    pub message: String,
}

pub fn emit(
    project: &Project,
    semantic: &SemanticProject,
    ir: &CanonicalIr,
    bindings: &[ResolvedBinding],
) -> Result<Emission, Vec<EmitDiagnostic>> {
    let mut diagnostics = Vec::new();
    let mut modules = BTreeMap::new();
    for module in &semantic.modules {
        if modules.insert(module.id.clone(), module).is_some() {
            diagnostics.push(diag(module_path(&module.id), "duplicate semantic module"));
        }
    }
    if modules.is_empty() {
        diagnostics.push(diag("python", "semantic project has no modules"));
    }
    let mut prefix_modules = HashSet::new();
    for id in modules.keys() {
        for length in 1..id.segments.len() {
            prefix_modules.insert(ModuleId::new(id.segments[..length].to_vec()));
        }
    }
    for id in modules.keys() {
        if prefix_modules.contains(id) {
            diagnostics.push(diag(
                module_path(id),
                "module is also a package prefix; Python facade paths would collide",
            ));
        }
    }

    let mut symbols = BTreeMap::<SymbolId, SymbolKind>::new();
    let mut functions = BTreeMap::<(ModuleId, String), &SemanticFunction>::new();
    for module in modules.values() {
        for declaration in &module.declarations {
            let id = declaration.id().clone();
            let kind = match declaration {
                SemanticDeclaration::Alias(_) => SymbolKind::Type,
                SemanticDeclaration::Newtype(_) => SymbolKind::Type,
                SemanticDeclaration::Struct(_) => SymbolKind::Type,
                SemanticDeclaration::Enum(_) => SymbolKind::Enum,
                SemanticDeclaration::Const(_) => SymbolKind::Const,
                SemanticDeclaration::Function(function) => {
                    if functions
                        .insert((module.id.clone(), function.id.name.clone()), function)
                        .is_some()
                    {
                        diagnostics.push(diag(
                            module_path(&module.id),
                            "duplicate function declaration",
                        ));
                    }
                    SymbolKind::Function
                }
            };
            if symbols.insert(id, kind).is_some() {
                diagnostics.push(diag(
                    module_path(&module.id),
                    "duplicate declaration identity",
                ));
            }
        }
    }

    for module in modules.values() {
        for declaration in &module.declarations {
            validate_declaration(module, declaration, &symbols, &mut diagnostics);
        }
    }

    let mut expected_bindings = BTreeSet::new();
    for key in functions.keys() {
        expected_bindings.insert(key.clone());
    }
    let mut seen_bindings = BTreeSet::new();
    let mut seen_binding_paths = HashSet::new();
    for binding in bindings {
        let key = (binding.module.clone(), binding.function.clone());
        if !expected_bindings.contains(&key) {
            diagnostics.push(diag(
                binding.source.clone(),
                format!(
                    "binding does not match a semantic function: {}",
                    binding.function
                ),
            ));
        } else if !seen_bindings.insert(key.clone()) {
            diagnostics.push(diag(
                binding.source.clone(),
                "duplicate binding for semantic function",
            ));
        }
        let expected_path = binding_path(&binding.module, &binding.function);
        if binding.generated_relative != expected_path {
            diagnostics.push(diag(
                binding.generated_relative.clone(),
                format!("binding path must be {}", path_string(&expected_path)),
            ));
        }
        if !valid_binding_path(&binding.generated_relative) {
            diagnostics.push(diag(
                binding.generated_relative.clone(),
                "binding path must be a normalized relative Python path below _cott_impl",
            ));
        }
        if !seen_binding_paths.insert(binding.generated_relative.clone()) {
            diagnostics.push(diag(
                binding.generated_relative.clone(),
                "colliding binding output path",
            ));
        }
        let actual_hash = sha256_hex(&binding.bytes);
        if binding.sha256 != actual_hash {
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
        if let Some(function) = functions.get(&key) {
            if !binding_defines_symbol(&binding.bytes, &function.id.name) {
                diagnostics.push(diag(
                    binding.source.clone(),
                    format!("binding does not define symbol {}", function.id.name),
                ));
            }
        }
    }
    for key in expected_bindings {
        if !seen_bindings.contains(&key) {
            diagnostics.push(diag(
                binding_path(&key.0, &key.1),
                "missing binding for semantic function",
            ));
        }
    }

    for module in modules.values() {
        let mut imported_names = BTreeMap::<String, ModuleId>::new();
        for (source, names) in referenced_imports(module, &symbols) {
            for name in names {
                if let Some(previous) = imported_names.insert(name.clone(), source.clone()) {
                    if previous != source {
                        diagnostics.push(diag(
                            module_path(&module.id),
                            format!("cross-module type name collision for {}", name),
                        ));
                    }
                }
            }
        }
    }
    let Some((entry_module_text, entry_function)) = project.entry.rsplit_once('.') else {
        diagnostics.push(diag(
            "project.entry",
            "entry must be a fully qualified module.function name",
        ));
        return Err(diagnostics);
    };
    let entry_module = ModuleId::new(entry_module_text.split('.').map(str::to_owned).collect());
    let entry_key = (entry_module.clone(), entry_function.to_owned());
    match functions.get(&entry_key) {
        Some(function) if function.parameters.is_empty() => {}
        Some(_) => diagnostics.push(diag(
            "project.entry",
            "entry function must have zero arguments",
        )),
        None => diagnostics.push(diag("project.entry", "entry function was not found")),
    }
    if !modules.contains_key(&entry_module) {
        diagnostics.push(diag("project.entry", "entry module was not found"));
    }

    for module in modules.values() {
        if let Some(ir_module) = ir
            .modules
            .iter()
            .find(|candidate| candidate.module == module.id)
        {
            if !exactly_one_newline(&ir_module.bytes) {
                diagnostics.push(diag(
                    ir_path(&module.id),
                    "canonical IR bytes must end in exactly one newline",
                ));
            }
        } else {
            diagnostics.push(diag(ir_path(&module.id), "missing canonical IR module"));
        }
    }
    for ir_module in &ir.modules {
        if !modules.contains_key(&ir_module.module) {
            diagnostics.push(diag(
                ir_path(&ir_module.module),
                "canonical IR contains an unknown module",
            ));
        }
    }
    if !diagnostics.is_empty() {
        return Err(diagnostics);
    }

    let mut files = BTreeMap::new();
    for (path, bytes) in render_runtime(&project.name) {
        add_file(
            &mut files,
            &mut diagnostics,
            prefixed("python", path),
            finish(bytes),
        );
    }
    add_package_markers(&mut files, &mut diagnostics, &modules, bindings);
    for module in modules.values() {
        add_file(
            &mut files,
            &mut diagnostics,
            type_path(&module.id),
            finish(render_types(module, &symbols)),
        );
        let module_entry = (module.id == entry_module).then_some(entry_function);
        add_file(
            &mut files,
            &mut diagnostics,
            facade_path(&module.id),
            finish(render_facade(module, bindings, module_entry)),
        );
        add_file(
            &mut files,
            &mut diagnostics,
            stub_path(&module.id),
            finish(render_stub(module, &symbols)),
        );
    }
    for ir_module in &ir.modules {
        add_file(
            &mut files,
            &mut diagnostics,
            ir_path(&ir_module.module),
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
    add_file(
        &mut files,
        &mut diagnostics,
        PathBuf::from("python/__main__.py"),
        finish(render_main(&entry_module, &entry_function)),
    );
    if !diagnostics.is_empty() {
        return Err(diagnostics);
    }

    let mut ordered_bindings: Vec<&ResolvedBinding> = bindings.iter().collect();
    ordered_bindings.sort_by(|a, b| {
        (a.module.clone(), a.function.clone()).cmp(&(b.module.clone(), b.function.clone()))
    });
    let mut metadata = String::from("{\"bindings\":[");
    for (index, binding) in ordered_bindings.iter().enumerate() {
        if index != 0 {
            metadata.push(',');
        }
        write!(
            metadata,
            "{{\"function\":{},\"module\":{},\"path\":{},\"sha256\":{}}}",
            json_string(&binding.function),
            json_string(&binding.module.as_string()),
            json_string(&path_string(&binding.generated_relative)),
            json_string(&binding.sha256)
        )
        .unwrap();
    }
    write!(
        metadata,
        "],\"entry\":{},\"managed_files\":{{",
        json_string(&project.entry)
    )
    .unwrap();
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
        json_string(&project.name)
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
    Ok(Emission {
        files,
        entry_module,
        entry_function: entry_function.to_owned(),
    })
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

fn add_package_markers(
    files: &mut BTreeMap<PathBuf, Vec<u8>>,
    diagnostics: &mut Vec<EmitDiagnostic>,
    modules: &BTreeMap<ModuleId, &SemanticModule>,
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
    for id in modules.keys() {
        for length in 1..id.segments.len() {
            dirs.insert(id.segments[..length].to_vec());
        }
    }
    dirs.insert(vec!["_cott_impl".into()]);
    for binding in bindings {
        let parts: Vec<String> = path_string(&binding.generated_relative)
            .split('/')
            .map(str::to_owned)
            .collect();
        for count in 1..parts.len().saturating_sub(1) {
            dirs.insert(parts[..=count].to_vec());
        }
    }
    for dir in dirs {
        let base = dir
            .iter()
            .fold(PathBuf::from("python"), |path, part| path.join(part));
        add_file(files, diagnostics, base.join("__init__.py"), b"\n".to_vec());
        add_file(files, diagnostics, base.join("py.typed"), b"\n".to_vec());
    }
}

#[derive(Clone, Copy)]
enum SymbolKind {
    Type,
    Enum,
    Const,
    Function,
}

fn validate_declaration(
    module: &SemanticModule,
    declaration: &SemanticDeclaration,
    symbols: &BTreeMap<SymbolId, SymbolKind>,
    diagnostics: &mut Vec<EmitDiagnostic>,
) {
    match declaration {
        SemanticDeclaration::Alias(value) => {
            validate_type(&value.target, symbols, module, diagnostics)
        }
        SemanticDeclaration::Newtype(value) => {
            validate_type(&value.underlying, symbols, module, diagnostics)
        }
        SemanticDeclaration::Struct(value) => {
            for field in &value.fields {
                validate_type(&field.ty, symbols, module, diagnostics);
                validate_value(
                    field.default.as_ref(),
                    &field.ty,
                    symbols,
                    module,
                    diagnostics,
                );
            }
        }
        SemanticDeclaration::Enum(value) => {
            for variant in &value.variants {
                for parameter in &variant.parameters {
                    validate_type(&parameter.ty, symbols, module, diagnostics);
                }
            }
        }
        SemanticDeclaration::Const(value) => {
            validate_type(&value.ty, symbols, module, diagnostics);
            validate_value(Some(&value.value), &value.ty, symbols, module, diagnostics);
        }
        SemanticDeclaration::Function(value) => {
            if !value.parameters.is_empty() {
                diagnostics.push(diag(
                    module_path(&module.id),
                    format!("function {} has unsupported parameters", value.id.name),
                ));
            }
            validate_type(&value.return_type, symbols, module, diagnostics);
        }
    }
}

fn validate_type(
    ty: &ResolvedType,
    symbols: &BTreeMap<SymbolId, SymbolKind>,
    module: &SemanticModule,
    diagnostics: &mut Vec<EmitDiagnostic>,
) {
    match ty {
        ResolvedType::Primitive(_) => {}
        ResolvedType::Named(symbol) => match symbols.get(symbol) {
            Some(SymbolKind::Type | SymbolKind::Enum) => {}
            Some(_) => diagnostics.push(diag(
                module_path(&module.id),
                format!("named type {} is not a type", symbol.as_string()),
            )),
            None => diagnostics.push(diag(
                module_path(&module.id),
                format!("unknown named type {}", symbol.as_string()),
            )),
        },
        ResolvedType::Option(item) => validate_type(item, symbols, module, diagnostics),
        ResolvedType::Result { ok, error } => {
            validate_type(ok, symbols, module, diagnostics);
            match symbols.get(error) {
                Some(SymbolKind::Type | SymbolKind::Enum) => {}
                Some(_) => diagnostics.push(diag(
                    module_path(&module.id),
                    format!("result error {} is not a type", error.as_string()),
                )),
                None => diagnostics.push(diag(
                    module_path(&module.id),
                    format!("unknown result error type {}", error.as_string()),
                )),
            }
        }
    }
}

fn validate_value(
    value: Option<&SemanticValue>,
    ty: &ResolvedType,
    _symbols: &BTreeMap<SymbolId, SymbolKind>,
    module: &SemanticModule,
    diagnostics: &mut Vec<EmitDiagnostic>,
) {
    let Some(value) = value else {
        return;
    };
    let valid = matches!(
        (value, ty),
        (
            SemanticValue::Bool(_),
            ResolvedType::Primitive(PrimitiveType::Bool)
        ) | (
            SemanticValue::Integer(_),
            ResolvedType::Primitive(
                PrimitiveType::I8
                    | PrimitiveType::I16
                    | PrimitiveType::I32
                    | PrimitiveType::I64
                    | PrimitiveType::U8
                    | PrimitiveType::U16
                    | PrimitiveType::U32
                    | PrimitiveType::U64
            )
        ) | (
            SemanticValue::Float(_),
            ResolvedType::Primitive(PrimitiveType::F64)
        ) | (
            SemanticValue::String(_),
            ResolvedType::Primitive(PrimitiveType::Str)
        ) | (
            SemanticValue::Unit,
            ResolvedType::Primitive(PrimitiveType::Unit)
        )
    );
    if !valid {
        diagnostics.push(diag(
            module_path(&module.id),
            "literal constant/default does not match its type",
        ));
    }
}

fn render_types(module: &SemanticModule, symbols: &BTreeMap<SymbolId, SymbolKind>) -> Vec<u8> {
    let mut out = String::from(
        "from __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom typing import TypeAlias, Union\n\nfrom cott_runtime import Option, Result, UNIT, Unit\n",
    );
    let imports = referenced_imports(module, symbols);
    let has_imports = !imports.is_empty();
    for (source, names) in imports {
        write!(
            out,
            "from {}_types import {}\n",
            type_module_name(&source),
            names.into_iter().collect::<Vec<_>>().join(", ")
        )
        .unwrap();
    }
    if has_imports {
        out.push('\n');
    }
    for declaration in &module.declarations {
        render_type_declaration(&mut out, declaration, module, symbols);
    }
    let names = exported_names(module);
    write!(
        out,
        "__all__ = [{}]\n",
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
    declaration: &SemanticDeclaration,
    module: &SemanticModule,
    symbols: &BTreeMap<SymbolId, SymbolKind>,
) {
    match declaration {
        SemanticDeclaration::Alias(value) => {
            render_doc(out, value.doc.as_ref().map(|doc| doc.text.as_str()));
            write!(
                out,
                "{}: TypeAlias = {}\n\n",
                value.id.name,
                render_type(&value.target, module, symbols)
            )
            .unwrap();
        }
        SemanticDeclaration::Struct(value) => {
            render_doc(out, value.doc.as_ref().map(|doc| doc.text.as_str()));
            write!(
                out,
                "@dataclass(frozen=True, slots=True, kw_only=True)\nclass {}:\n",
                value.id.name
            )
            .unwrap();
            if value.fields.is_empty() {
                out.push_str("    pass\n\n");
            } else {
                for field in &value.fields {
                    write!(
                        out,
                        "    {}: {}",
                        field.name,
                        render_type(&field.ty, module, symbols)
                    )
                    .unwrap();
                    if let Some(default) = &field.default {
                        write!(out, " = {}", render_value(default)).unwrap();
                    }
                    out.push('\n');
                }
                out.push('\n');
            }
        }
        SemanticDeclaration::Newtype(value) => {
            render_doc(out, value.doc.as_ref().map(|doc| doc.text.as_str()));
            write!(
                out,
                "@dataclass(frozen=True, slots=True, kw_only=True)\nclass {}:\n    value: {}\n\n",
                value.id.name,
                render_type(&value.underlying, module, symbols)
            )
            .unwrap();
        }
        SemanticDeclaration::Enum(value) => render_enum(out, value, module, symbols),
        SemanticDeclaration::Const(value) => {
            render_doc(out, value.doc.as_ref().map(|doc| doc.text.as_str()));
            write!(
                out,
                "{}: {} = {}\n\n",
                value.id.name,
                render_type(&value.ty, module, symbols),
                render_value(&value.value)
            )
            .unwrap();
        }
        SemanticDeclaration::Function(_) => {}
    }
}

fn render_enum(
    out: &mut String,
    value: &SemanticEnum,
    module: &SemanticModule,
    symbols: &BTreeMap<SymbolId, SymbolKind>,
) {
    render_doc(out, value.doc.as_ref().map(|doc| doc.text.as_str()));
    for variant in &value.variants {
        if variant.parameters.is_empty() {
            write!(
                out,
                "@dataclass(frozen=True, slots=True, kw_only=True)\nclass {}:\n    pass\n\n",
                variant.name
            )
            .unwrap();
        } else {
            write!(
                out,
                "@dataclass(frozen=True, slots=True, kw_only=True)\nclass {}:\n",
                variant.name
            )
            .unwrap();
            for parameter in &variant.parameters {
                write!(
                    out,
                    "    {}: {}\n",
                    parameter.name,
                    render_type(&parameter.ty, module, symbols)
                )
                .unwrap();
            }
            out.push('\n');
        }
    }
    write!(
        out,
        "{}: TypeAlias = Union[{}]\n\n",
        value.id.name,
        value
            .variants
            .iter()
            .map(|variant| variant.name.clone())
            .collect::<Vec<_>>()
            .join(", ")
    )
    .unwrap();
}

fn render_facade(
    module: &SemanticModule,
    bindings: &[ResolvedBinding],
    entry_function: Option<&str>,
) -> Vec<u8> {
    let mut out =
        String::from("from __future__ import annotations\n\nfrom cott_runtime import _cott_load\n");
    let names = exported_names(module);
    if !names.is_empty() {
        write!(
            out,
            "\nfrom {} import {}\n",
            type_module_name(&module.id),
            names.join(", ")
        )
        .unwrap();
    }
    for declaration in &module.declarations {
        if let SemanticDeclaration::Function(function) = declaration {
            if let Some(binding) = bindings
                .iter()
                .find(|binding| binding.module == module.id && binding.function == function.id.name)
            {
                write!(
                    out,
                    "\n{} = _cott_load({}, {}, {})\n",
                    function.id.name,
                    json_string(&path_string(&binding.generated_relative)),
                    json_string(&binding.sha256),
                    json_string(&binding.function)
                )
                .unwrap();
            }
        }
    }
    write!(
        out,
        "\n__all__ = [{}]\n",
        names
            .iter()
            .chain(
                module
                    .declarations
                    .iter()
                    .filter_map(|declaration| match declaration {
                        SemanticDeclaration::Function(function) => Some(&function.id.name),
                        _ => None,
                    })
            )
            .map(|name| json_string(name))
            .collect::<Vec<_>>()
            .join(", ")
    )
    .unwrap();
    if let Some(function) = entry_function {
        write!(
            out,
            "\nif __name__ == \"__main__\":\n    from cott_runtime import _cott_display\n    print(_cott_display({function}()))\n"
        )
        .unwrap();
    }
    out.into_bytes()
}

fn render_stub(module: &SemanticModule, symbols: &BTreeMap<SymbolId, SymbolKind>) -> Vec<u8> {
    let mut out =
        String::from("from __future__ import annotations\n\nfrom typing import TypeAlias, Union\n");
    let names = exported_names(module);
    if !names.is_empty() {
        write!(
            out,
            "\nfrom {} import {}\n",
            type_module_name(&module.id),
            names.join(", ")
        )
        .unwrap();
    }
    let imports = referenced_imports(module, symbols);
    for (source, names) in imports {
        write!(
            out,
            "from {}_types import {}\n",
            type_module_name(&source),
            names.into_iter().collect::<Vec<_>>().join(", ")
        )
        .unwrap();
    }
    for declaration in &module.declarations {
        match declaration {
            SemanticDeclaration::Alias(value) => {
                render_doc(&mut out, value.doc.as_ref().map(|doc| doc.text.as_str()));
                write!(
                    out,
                    "{}: TypeAlias = {}\n\n",
                    value.id.name,
                    render_type(&value.target, module, symbols)
                )
                .unwrap();
            }
            SemanticDeclaration::Newtype(value) => {
                render_doc(&mut out, value.doc.as_ref().map(|doc| doc.text.as_str()));
                write!(out, "class {}: ...\n\n", value.id.name).unwrap();
            }
            SemanticDeclaration::Struct(value) => {
                render_doc(&mut out, value.doc.as_ref().map(|doc| doc.text.as_str()));
                write!(out, "class {}: ...\n\n", value.id.name).unwrap();
            }
            SemanticDeclaration::Enum(value) => {
                render_doc(&mut out, value.doc.as_ref().map(|doc| doc.text.as_str()));
                write!(
                    out,
                    "{}: TypeAlias = Union[{}]\n\n",
                    value.id.name,
                    value
                        .variants
                        .iter()
                        .map(|variant| variant.name.clone())
                        .collect::<Vec<_>>()
                        .join(", ")
                )
                .unwrap();
            }
            SemanticDeclaration::Const(value) => {
                render_doc(&mut out, value.doc.as_ref().map(|doc| doc.text.as_str()));
                write!(
                    out,
                    "{}: {}\n\n",
                    value.id.name,
                    render_type(&value.ty, module, symbols)
                )
                .unwrap();
            }
            SemanticDeclaration::Function(value) => {
                render_doc(&mut out, value.doc.as_ref().map(|doc| doc.text.as_str()));
                write!(
                    out,
                    "def {}() -> {}: ...\n\n",
                    value.id.name,
                    render_type(&value.return_type, module, symbols)
                )
                .unwrap();
            }
        }
    }
    out.into_bytes()
}

fn render_main(module: &ModuleId, function: &str) -> Vec<u8> {
    format!("from {} import {}\nfrom cott_runtime import _cott_display\n\nif __name__ == \"__main__\":\n    print(_cott_display({}()))\n", facade_module_name(module), function, function).into_bytes()
}

fn render_type(
    ty: &ResolvedType,
    module: &SemanticModule,
    symbols: &BTreeMap<SymbolId, SymbolKind>,
) -> String {
    match ty {
        ResolvedType::Primitive(primitive) => primitive_python(*primitive).into(),
        ResolvedType::Named(symbol) => {
            if symbol.module == module.id {
                symbol.name.clone()
            } else {
                let _ = symbols;
                symbol.name.clone()
            }
        }
        ResolvedType::Option(item) => format!("Option[{}]", render_type(item, module, symbols)),
        ResolvedType::Result { ok, error } => format!(
            "Result[{}, {}]",
            render_type(ok, module, symbols),
            named_type(error, module)
        ),
    }
}
fn named_type(symbol: &SymbolId, module: &SemanticModule) -> String {
    if symbol.module == module.id {
        symbol.name.clone()
    } else {
        symbol.name.clone()
    }
}
fn primitive_python(primitive: PrimitiveType) -> &'static str {
    match primitive {
        PrimitiveType::Bool => "bool",
        PrimitiveType::I8
        | PrimitiveType::I16
        | PrimitiveType::I32
        | PrimitiveType::I64
        | PrimitiveType::U8
        | PrimitiveType::U16
        | PrimitiveType::U32
        | PrimitiveType::U64 => "int",
        PrimitiveType::F64 => "float",
        PrimitiveType::Str => "str",
        PrimitiveType::Bytes => "bytes",
        PrimitiveType::Unit => "Unit",
    }
}
fn render_value(value: &SemanticValue) -> String {
    match value {
        SemanticValue::Bool(value) => value.to_string(),
        SemanticValue::Integer(value) | SemanticValue::Float(value) => value.clone(),
        SemanticValue::String(value) => json_string(value),
        SemanticValue::Unit => "UNIT".into(),
    }
}
fn render_doc(out: &mut String, text: Option<&str>) {
    if let Some(text) = text {
        out.push_str("\"\"\"");
        out.push_str(&text.replace("\\", "\\\\").replace("\"\"\"", "\\\"\\\"\\\""));
        out.push_str("\"\"\"\n");
    }
}

fn referenced_imports(
    module: &SemanticModule,
    symbols: &BTreeMap<SymbolId, SymbolKind>,
) -> BTreeMap<ModuleId, BTreeSet<String>> {
    let mut result = BTreeMap::new();
    for declaration in &module.declarations {
        for ty in declaration_types(declaration) {
            collect_named(ty, module, symbols, &mut result);
        }
    }
    result
}
fn declaration_types(declaration: &SemanticDeclaration) -> Vec<&ResolvedType> {
    match declaration {
        SemanticDeclaration::Alias(value) => vec![&value.target],
        SemanticDeclaration::Newtype(value) => vec![&value.underlying],
        SemanticDeclaration::Struct(value) => value.fields.iter().map(|field| &field.ty).collect(),
        SemanticDeclaration::Enum(value) => value
            .variants
            .iter()
            .flat_map(|variant| variant.parameters.iter().map(|parameter| &parameter.ty))
            .collect(),
        SemanticDeclaration::Const(value) => vec![&value.ty],
        SemanticDeclaration::Function(value) => vec![&value.return_type],
    }
}
fn collect_named(
    ty: &ResolvedType,
    module: &SemanticModule,
    symbols: &BTreeMap<SymbolId, SymbolKind>,
    imports: &mut BTreeMap<ModuleId, BTreeSet<String>>,
) {
    match ty {
        ResolvedType::Named(symbol) => {
            if symbol.module != module.id
                && matches!(
                    symbols.get(symbol),
                    Some(SymbolKind::Type | SymbolKind::Enum)
                )
            {
                imports
                    .entry(symbol.module.clone())
                    .or_default()
                    .insert(symbol.name.clone());
            }
        }
        ResolvedType::Option(item) => collect_named(item, module, symbols, imports),
        ResolvedType::Result { ok, error } => {
            collect_named(ok, module, symbols, imports);
            if error.module != module.id {
                imports
                    .entry(error.module.clone())
                    .or_default()
                    .insert(error.name.clone());
            }
        }
        ResolvedType::Primitive(_) => {}
    }
}
fn exported_names(module: &SemanticModule) -> Vec<String> {
    let mut names = Vec::new();
    for declaration in &module.declarations {
        match declaration {
            SemanticDeclaration::Alias(value) => names.push(value.id.name.clone()),
            SemanticDeclaration::Newtype(value) => names.push(value.id.name.clone()),
            SemanticDeclaration::Struct(value) => names.push(value.id.name.clone()),
            SemanticDeclaration::Enum(value) => {
                names.push(value.id.name.clone());
                names.extend(value.variants.iter().map(|variant| variant.name.clone()));
            }
            SemanticDeclaration::Const(value) => names.push(value.id.name.clone()),
            SemanticDeclaration::Function(_) => {}
        }
    }
    names
}

fn binding_defines_symbol(bytes: &[u8], symbol: &str) -> bool {
    let source = String::from_utf8_lossy(bytes);
    source.lines().any(|line| {
        let line = line.trim_start();
        line.strip_prefix("def ")
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
fn binding_path(module: &ModuleId, function: &str) -> PathBuf {
    let mut path = PathBuf::from("_cott_impl");
    for segment in &module.segments {
        path.push(segment);
    }
    path.push(format!("{}.py", function));
    path
}
fn type_path(module: &ModuleId) -> PathBuf {
    prefixed("python", module_file(module, "_types.py"))
}
fn facade_path(module: &ModuleId) -> PathBuf {
    prefixed("python", module_file(module, ".py"))
}
fn stub_path(module: &ModuleId) -> PathBuf {
    prefixed("stubs", module_file(module, ".pyi"))
}
fn ir_path(module: &ModuleId) -> PathBuf {
    prefixed("ir", module_file(module, ".json"))
}
fn module_file(module: &ModuleId, suffix: &str) -> PathBuf {
    let mut path = PathBuf::new();
    for segment in &module.segments[..module.segments.len().saturating_sub(1)] {
        path.push(segment);
    }
    if let Some(last) = module.segments.last() {
        path.push(format!("{}{}", last, suffix));
    }
    path
}
fn facade_module_name(module: &ModuleId) -> String {
    module.as_string()
}
fn type_module_name(module: &ModuleId) -> String {
    if module.segments.is_empty() {
        "_types".into()
    } else {
        format!("{}_types", module.as_string().replace('.', "."))
    }
}
fn module_path(module: &ModuleId) -> PathBuf {
    PathBuf::from(module.as_string())
}
fn prefixed(prefix: &str, path: PathBuf) -> PathBuf {
    PathBuf::from(prefix).join(path)
}
fn path_string(path: &Path) -> String {
    path.to_string_lossy().replace('\\', "/")
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
fn diag(path: impl Into<PathBuf>, message: impl Into<String>) -> EmitDiagnostic {
    EmitDiagnostic {
        path: path.into(),
        message: message.into(),
    }
}
