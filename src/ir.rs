use std::fmt::Write as _;
use std::path::{Path, PathBuf};
use std::sync::LazyLock;

use serde_json::Value;

use crate::diagnostics::Span;
use crate::hir::{
    HirAnnotation, HirBinaryOp, HirClause, HirClauseKind, HirCompareOp, HirContract,
    HirDeclaration, HirDoc, HirEffect, HirExpr, HirExprKind, HirField, HirGenericParam,
    HirImplInitializer, HirImplMethod, HirMethod, HirModule, HirParameter, HirParameterKind,
    HirPattern, HirPatternKind, HirProject, HirReference, HirType, HirUnaryOp, HirValue,
    HirVariant, PrimitiveType,
};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CanonicalIr {
    pub modules: Vec<CanonicalModule>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CanonicalModule {
    pub module: crate::hir::ModuleId,
    pub source: PathBuf,
    pub bytes: Vec<u8>,
}

/// Render owned HIR without consulting source files.
pub fn render(project: &HirProject) -> Result<CanonicalIr, String> {
    let ir = CanonicalIr {
        modules: project.modules.iter().map(render_module).collect(),
    };
    for module in &ir.modules {
        validate(&module.bytes)?;
    }
    Ok(ir)
}

pub fn load(bytes: &[u8]) -> Result<Value, String> {
    validate(bytes)?;
    serde_json::from_slice(bytes).map_err(|error| format!("invalid canonical IR JSON: {error}"))
}

pub fn canonical_bytes(value: &Value) -> Result<Vec<u8>, String> {
    let mut bytes =
        serde_json::to_vec(value).map_err(|error| format!("serialize canonical IR: {error}"))?;
    bytes.push(b'\n');
    validate(&bytes)?;
    Ok(bytes)
}

fn validate(bytes: &[u8]) -> Result<(), String> {
    let value: Value = serde_json::from_slice(bytes)
        .map_err(|error| format!("invalid canonical IR JSON: {error}"))?;
    static SCHEMA: LazyLock<Value> = LazyLock::new(|| {
        serde_json::from_str(include_str!("../schemas/canonical-ir.schema.json"))
            .expect("embedded canonical IR schema is valid JSON")
    });
    let validator = jsonschema::validator_for(&SCHEMA)
        .map_err(|error| format!("invalid embedded canonical IR schema: {error}"))?;
    let errors = validator
        .iter_errors(&value)
        .map(|error| error.to_string())
        .collect::<Vec<_>>();
    if errors.is_empty() {
        Ok(())
    } else {
        Err(format!(
            "canonical IR schema violation: {}",
            errors.join("; ")
        ))
    }
}

fn render_module(module: &HirModule) -> CanonicalModule {
    let mut json = Json::new(&module.source_bytes);
    json.object_start();
    json.key("declarations");
    json.array_start();
    for (index, declaration) in module.declarations.iter().enumerate() {
        if index != 0 {
            json.comma();
        }
        render_declaration(&mut json, declaration);
    }
    json.array_end();
    json.comma();
    json.key("imports");
    json.array_start();
    let mut imports = module
        .imports
        .iter()
        .map(|import| import.symbol.as_string())
        .collect::<Vec<_>>();
    imports.sort();
    imports.dedup();
    for (index, import) in imports.iter().enumerate() {
        if index != 0 {
            json.comma();
        }
        json.string(import);
    }
    json.array_end();
    json.comma();
    json.key("module");
    json.string(&module.id.as_string());
    json.comma();
    json.key("schema_version");
    json.number("1");
    json.comma();
    json.key("source");
    json.string(&source_string(&module.source));
    json.object_end();
    json.newline();
    CanonicalModule {
        module: module.id.clone(),
        source: module.source.clone(),
        bytes: json.bytes,
    }
}

fn render_declaration(json: &mut Json, declaration: &HirDeclaration) {
    match declaration {
        HirDeclaration::Alias(value) => {
            declaration_start(
                json,
                "alias",
                value.id.as_string().as_str(),
                &value.annotations,
                &value.doc,
                &value.span,
                value.public,
                value.source_order,
                &value.generics,
            );
            json.comma();
            json.key("target");
            render_type(json, &value.target);
            json.object_end();
        }
        HirDeclaration::Newtype(value) => {
            declaration_start(
                json,
                "newtype",
                value.id.as_string().as_str(),
                &value.annotations,
                &value.doc,
                &value.span,
                value.public,
                value.source_order,
                &value.generics,
            );
            json.comma();
            json.key("carrier");
            render_type(json, &value.carrier);
            json.comma();
            json.key("refinement");
            match &value.refinement {
                Some(e) => render_expr(json, e),
                None => json.null(),
            }
            json.object_end();
        }
        HirDeclaration::Struct(value) => {
            declaration_start(
                json,
                "struct",
                value.id.as_string().as_str(),
                &value.annotations,
                &value.doc,
                &value.span,
                value.public,
                value.source_order,
                &value.generics,
            );
            json.comma();
            json.key("fields");
            render_fields(json, &value.fields);
            json.object_end();
        }
        HirDeclaration::Enum(value) => {
            declaration_start(
                json,
                "enum",
                value.id.as_string().as_str(),
                &value.annotations,
                &value.doc,
                &value.span,
                value.public,
                value.source_order,
                &value.generics,
            );
            json.comma();
            json.key("variants");
            render_variants(json, &value.variants);
            json.object_end();
        }
        HirDeclaration::Trait(value) => {
            declaration_start(
                json,
                "trait",
                value.id.as_string().as_str(),
                &value.annotations,
                &value.doc,
                &value.span,
                value.public,
                value.source_order,
                &value.generics,
            );
            json.comma();
            json.key("methods");
            json.array_start();
            for (i, method) in value.methods.iter().enumerate() {
                if i != 0 {
                    json.comma();
                }
                render_method(json, method);
            }
            json.array_end();
            json.object_end();
        }
        HirDeclaration::Impl(value) => {
            json.object_start();
            json.key("annotations");
            render_annotations(json, &value.annotations);
            json.comma();
            json.key("doc");
            json.null();
            json.comma();
            json.key("generics");
            json.array_start();
            json.array_end();
            json.comma();
            json.key("init");
            match &value.initializer {
                Some(initializer) => render_impl_initializer(json, initializer),
                None => json.null(),
            }
            json.comma();
            json.key("invariants");
            json.array_start();
            for (index, invariant) in value.invariants.iter().enumerate() {
                if index != 0 {
                    json.comma();
                }
                json.object_start();
                json.key("clause_id");
                json.number_u32(invariant.clause_id);
                json.comma();
                json.key("expression");
                render_expr(json, &invariant.expression);
                json.comma();
                json.key("span");
                render_span(json, &invariant.span);
                json.object_end();
            }
            json.array_end();
            json.comma();
            json.key("kind");
            json.string("impl");
            json.comma();
            json.key("methods");
            json.array_start();
            for (index, method) in value.methods.iter().enumerate() {
                if index != 0 {
                    json.comma();
                }
                render_impl_method(json, method);
            }
            json.array_end();
            json.comma();
            json.key("name");
            json.string(&value.id.as_string());
            json.comma();
            json.key("public");
            json.boolean(value.public);
            json.comma();
            json.key("source_order");
            json.number_usize(value.source_order);
            json.comma();
            json.key("span");
            render_span(json, &value.span);
            json.comma();
            json.key("state");
            render_fields(json, &value.state);
            json.comma();
            json.key("traits");
            json.array_start();
            for (index, trait_ref) in value.traits.iter().enumerate() {
                if index != 0 {
                    json.comma();
                }
                render_type(json, trait_ref);
            }
            json.array_end();
            json.object_end();
        }
        HirDeclaration::Rule(value) => {
            declaration_start(
                json,
                "rule",
                value.id.as_string().as_str(),
                &value.annotations,
                &value.doc,
                &value.span,
                value.public,
                value.source_order,
                &value.generics,
            );
            json.comma();
            json.key("base");
            if let Some(base) = &value.base {
                json.string(&base.as_string());
            } else {
                json.null();
            }
            json.comma();
            json.key("contract");
            render_contract(json, &value.contract);
            json.object_end();
        }
        HirDeclaration::Const(value) => {
            declaration_start(
                json,
                "const",
                value.id.as_string().as_str(),
                &value.annotations,
                &value.doc,
                &value.span,
                value.public,
                value.source_order,
                &[],
            );
            json.comma();
            json.key("type");
            render_type(json, &value.ty);
            json.comma();
            json.key("value");
            render_value(json, &value.value);
            json.object_end();
        }
        HirDeclaration::Function(value) => {
            declaration_start(
                json,
                "function",
                value.id.as_string().as_str(),
                &value.annotations,
                &value.doc,
                &value.span,
                value.public,
                value.source_order,
                &value.generics,
            );
            json.comma();
            json.key("parameters");
            render_parameters(json, &value.parameters);
            json.comma();
            json.key("return_type");
            render_type(json, &value.return_type);
            json.comma();
            json.key("contract");
            render_contract(json, &value.contract);
            json.comma();
            json.key("body");
            match &value.body {
                Some(e) => render_expr(json, e),
                None => json.null(),
            }
            json.object_end();
        }
    }
}

fn declaration_start(
    json: &mut Json,
    kind: &str,
    name: &str,
    annotations: &[HirAnnotation],
    doc: &Option<HirDoc>,
    span: &Span,
    public: bool,
    source_order: usize,
    generics: &[HirGenericParam],
) {
    json.object_start();
    json.key("annotations");
    render_annotations(json, annotations);
    json.comma();
    json.key("doc");
    render_doc(json, doc.as_ref());
    json.comma();
    json.key("generics");
    render_generics(json, generics);
    json.comma();
    json.key("kind");
    json.string(kind);
    json.comma();
    json.key("name");
    json.string(name);
    json.comma();
    json.key("public");
    json.boolean(public);
    json.comma();
    json.key("source_order");
    json.number_usize(source_order);
    json.comma();
    json.key("span");
    render_span(json, span);
}
fn render_annotations(json: &mut Json, annotations: &[HirAnnotation]) {
    json.array_start();
    for (i, ann) in annotations.iter().enumerate() {
        if i != 0 {
            json.comma();
        }
        json.object_start();
        json.key("argument");
        if let Some(arg) = &ann.argument {
            json.string(arg);
        } else {
            json.null();
        }
        json.comma();
        json.key("name");
        json.string(&ann.name);
        json.comma();
        json.key("span");
        render_span(json, &ann.span);
        json.object_end();
    }
    json.array_end();
}

fn render_generics(json: &mut Json, values: &[HirGenericParam]) {
    json.array_start();
    for (i, value) in values.iter().enumerate() {
        if i != 0 {
            json.comma();
        }
        json.object_start();
        json.key("bounds");
        json.array_start();
        for (j, bound) in value.bounds.iter().enumerate() {
            if j != 0 {
                json.comma();
            }
            render_type(json, bound);
        }
        json.array_end();
        json.comma();
        json.key("name");
        json.string(&value.name);
        json.comma();
        json.key("source_order");
        json.number_usize(value.source_order);
        json.comma();
        json.key("span");
        render_span(json, &value.span);
        json.object_end();
    }
    json.array_end();
}

fn render_type(json: &mut Json, ty: &HirType) {
    json.object_start();
    match ty {
        HirType::Primitive(value) => {
            json.key("kind");
            json.string("primitive");
            json.comma();
            json.key("name");
            json.string(primitive_name(*value));
        }
        HirType::Named { symbol, args } => {
            json.key("args");
            json.array_start();
            for (i, arg) in args.iter().enumerate() {
                if i != 0 {
                    json.comma();
                }
                render_type(json, arg);
            }
            json.array_end();
            json.comma();
            json.key("kind");
            json.string("named");
            json.comma();
            json.key("name");
            json.string(&symbol.as_string());
        }
        HirType::TypeParameter { name } => {
            json.key("kind");
            json.string("type_parameter");
            json.comma();
            json.key("name");
            json.string(name);
        }
        HirType::List { item } => {
            json.key("item");
            render_type(json, item);
            json.comma();
            json.key("kind");
            json.string("list");
        }
        HirType::Set { item } => {
            json.key("item");
            render_type(json, item);
            json.comma();
            json.key("kind");
            json.string("set");
        }
        HirType::Map { key, value } => {
            json.key("key");
            render_type(json, key);
            json.comma();
            json.key("kind");
            json.string("map");
            json.comma();
            json.key("value");
            render_type(json, value);
        }
        HirType::Tuple2 { first, second } => {
            json.key("first");
            render_type(json, first);
            json.comma();
            json.key("kind");
            json.string("tuple2");
            json.comma();
            json.key("second");
            render_type(json, second);
        }
        HirType::Option { item } => {
            json.key("item");
            render_type(json, item);
            json.comma();
            json.key("kind");
            json.string("option");
        }
        HirType::Result { ok, error } => {
            json.key("error");
            render_type(json, error);
            json.comma();
            json.key("kind");
            json.string("result");
            json.comma();
            json.key("ok");
            render_type(json, ok);
        }
        HirType::Opaque { tag } => {
            json.key("kind");
            json.string("opaque");
            json.comma();
            json.key("tag");
            json.string(tag);
        }
    }
    json.object_end();
}

fn render_fields(json: &mut Json, fields: &[HirField]) {
    json.array_start();
    for (i, field) in fields.iter().enumerate() {
        if i != 0 {
            json.comma();
        }
        render_field(json, field);
    }
    json.array_end();
}
fn render_field(json: &mut Json, field: &HirField) {
    json.object_start();
    json.key("default");
    match &field.default {
        Some(value) => render_value(json, value),
        None => json.null(),
    };
    json.comma();
    json.key("name");
    json.string(&field.name);
    json.comma();
    json.key("source_order");
    json.number_usize(field.source_order);
    json.comma();
    json.key("span");
    render_span(json, &field.span);
    json.comma();
    json.key("type");
    render_type(json, &field.ty);
    json.object_end();
}
fn render_parameters(json: &mut Json, values: &[HirParameter]) {
    json.array_start();
    for (i, value) in values.iter().enumerate() {
        if i != 0 {
            json.comma();
        }
        json.object_start();
        json.key("default");
        match &value.default {
            Some(v) => render_value(json, v),
            None => json.null(),
        };
        json.comma();
        json.key("kind");
        json.string(parameter_kind(value.kind));
        json.comma();
        json.key("name");
        json.string(&value.name);
        json.comma();
        json.key("source_order");
        json.number_usize(value.source_order);
        json.comma();
        json.key("span");
        render_span(json, &value.span);
        json.comma();
        json.key("type");
        render_type(json, &value.ty);
        json.object_end();
    }
    json.array_end();
}
fn render_variants(json: &mut Json, values: &[HirVariant]) {
    json.array_start();
    for (i, value) in values.iter().enumerate() {
        if i != 0 {
            json.comma();
        }
        json.object_start();
        json.key("fields");
        render_fields(json, &value.fields);
        json.comma();
        json.key("name");
        json.string(&value.name);
        json.comma();
        json.key("source_order");
        json.number_usize(value.source_order);
        json.comma();
        json.key("span");
        render_span(json, &value.span);
        json.comma();
        json.key("symbol");
        json.string(&value.symbol.as_string());
        json.object_end();
    }
    json.array_end();
}
fn render_method(json: &mut Json, value: &HirMethod) {
    json.object_start();
    json.key("contract");
    render_contract(json, &value.contract);
    json.comma();
    json.key("doc");
    render_doc(json, value.doc.as_ref());
    json.comma();
    json.key("generics");
    render_generics(json, &value.generics);
    json.comma();
    json.key("kind");
    json.string("method");
    json.comma();
    json.key("name");
    json.string(value.id.as_string().as_str());
    json.comma();
    json.key("parameters");
    render_parameters(json, &value.parameters);
    json.comma();
    json.key("public");
    json.boolean(value.public);
    json.comma();
    json.key("return_type");
    render_type(json, &value.return_type);
    json.comma();
    json.key("source_order");
    json.number_usize(value.source_order);
    json.comma();
    json.key("span");
    render_span(json, &value.span);
    json.object_end();
}

fn render_impl_initializer(json: &mut Json, value: &HirImplInitializer) {
    json.object_start();
    json.key("contracts");
    render_impl_contract(json, value.doc.as_ref(), &value.contract, false);
    json.comma();
    json.key("parameters");
    render_parameters(json, &value.parameters);
    json.comma();
    json.key("span");
    render_span(json, &value.span);
    json.object_end();
}

fn render_impl_method(json: &mut Json, value: &HirImplMethod) {
    json.object_start();
    json.key("contracts");
    render_impl_contract(json, value.doc.as_ref(), &value.contract, true);
    json.comma();
    json.key("effects");
    render_effects(json, &value.contract.effects);
    json.comma();
    json.key("modifies");
    json.array_start();
    for (index, field) in value.modifies.iter().enumerate() {
        if index != 0 {
            json.comma();
        }
        json.string(&field.as_string());
    }
    json.array_end();
    json.comma();
    json.key("name");
    json.string(&value.name);
    json.comma();
    json.key("parameters");
    render_parameters(json, &value.parameters);
    json.comma();
    json.key("return_type");
    render_type(json, &value.return_type);
    json.comma();
    json.key("span");
    render_span(json, &value.span);
    json.object_end();
}

fn render_impl_contract(
    json: &mut Json,
    doc: Option<&HirDoc>,
    contract: &HirContract,
    include_errors: bool,
) {
    json.object_start();
    json.key("doc");
    match doc {
        Some(value) => json.string(&value.text),
        None => json.null(),
    }
    json.comma();
    json.key("ensures");
    render_impl_clauses(json, contract, "ensures");
    if include_errors {
        json.comma();
        json.key("errors");
        render_impl_clauses(json, contract, "error");
    }
    json.comma();
    json.key("requires");
    render_impl_clauses(json, contract, "requires");
    json.object_end();
}

fn render_impl_clauses(json: &mut Json, contract: &HirContract, expected_kind: &str) {
    json.array_start();
    let mut first = true;
    for clause in &contract.clauses {
        let matches = matches!(
            (&clause.kind, expected_kind),
            (HirClauseKind::Requires { .. }, "requires")
                | (HirClauseKind::Ensures { .. }, "ensures")
                | (HirClauseKind::Error { .. }, "error")
        );
        if !matches {
            continue;
        }
        if !first {
            json.comma();
        }
        first = false;
        render_clause(json, clause);
    }
    json.array_end();
}

fn render_effects(json: &mut Json, effects: &[HirEffect]) {
    json.array_start();
    let mut effects = effects.iter().collect::<Vec<_>>();
    effects.sort_by(|left, right| left.key.cmp(&right.key));
    for (index, effect) in effects.into_iter().enumerate() {
        if index != 0 {
            json.comma();
        }
        render_effect(json, effect);
    }
    json.array_end();
}
fn render_doc(json: &mut Json, doc: Option<&HirDoc>) {
    match doc {
        Some(doc) => {
            json.object_start();
            json.key("span");
            render_span(json, &doc.span);
            json.comma();
            json.key("text");
            json.string(&doc.text);
            json.object_end();
        }
        None => json.null(),
    }
}
fn render_span(json: &mut Json<'_>, span: &Span) {
    let (start_line, start_column) = json.location(span.start);
    let (end_line, end_column) = json.location(span.end);
    json.object_start();
    json.key("end_byte");
    json.number_usize(span.end);
    json.comma();
    json.key("end_column");
    json.number_usize(end_column);
    json.comma();
    json.key("end_line");
    json.number_usize(end_line);
    json.comma();
    json.key("start_byte");
    json.number_usize(span.start);
    json.comma();
    json.key("start_column");
    json.number_usize(start_column);
    json.comma();
    json.key("start_line");
    json.number_usize(start_line);
    json.object_end();
}
fn render_contract(json: &mut Json, contract: &HirContract) {
    json.object_start();
    json.key("clauses");
    json.array_start();
    for (i, clause) in contract.clauses.iter().enumerate() {
        if i != 0 {
            json.comma();
        }
        render_clause(json, clause);
    }
    json.array_end();
    json.comma();
    json.key("effects");
    json.array_start();
    let mut effects = contract.effects.iter().collect::<Vec<_>>();
    effects.sort_by(|left, right| left.key.cmp(&right.key));
    for (i, effect) in effects.into_iter().enumerate() {
        if i != 0 {
            json.comma();
        }
        render_effect(json, effect);
    }
    json.array_end();
    json.object_end();
}
fn render_clause(json: &mut Json, clause: &HirClause) {
    json.object_start();
    json.key("clause_id");
    json.number_u32(clause.clause_id);
    json.comma();
    json.key("kind");
    match &clause.kind {
        HirClauseKind::Requires { expression } => {
            json.string("requires");
            json.comma();
            json.key("expression");
            render_expr(json, expression);
        }
        HirClauseKind::Modifies { fields } => {
            json.string("modifies");
            json.comma();
            json.key("fields");
            json.array_start();
            for (index, field) in fields.iter().enumerate() {
                if index != 0 {
                    json.comma();
                }
                json.string(&field.as_string());
            }
            json.array_end();
        }
        HirClauseKind::Ensures {
            pattern,
            expression,
        } => {
            json.string("ensures");
            json.comma();
            json.key("expression");
            render_expr(json, expression);
            json.comma();
            json.key("pattern");
            match pattern {
                Some(value) => render_pattern(json, value),
                None => json.null(),
            }
        }
        HirClauseKind::Error {
            variant,
            priority,
            when,
        } => {
            json.string("error");
            json.comma();
            json.key("priority");
            match priority {
                Some(value) => json.number_u32(*value),
                None => json.null(),
            };
            json.comma();
            json.key("variant");
            json.string(&variant.as_string());
            json.comma();
            json.key("when");
            match when {
                Some(value) => render_expr(json, value),
                None => json.null(),
            }
        }
    }
    json.comma();
    json.key("span");
    render_span(json, &clause.span);
    json.object_end();
}
fn render_effect(json: &mut Json, effect: &HirEffect) {
    json.object_start();
    json.key("key");
    json.string(&effect.key);
    json.comma();
    json.key("source_order");
    json.number_usize(effect.source_order);
    json.comma();
    json.key("span");
    render_span(json, &effect.span);
    json.object_end();
}

fn render_expr(json: &mut Json, expression: &HirExpr) {
    json.object_start();
    json.key("kind");
    match &expression.kind {
        HirExprKind::Literal(value) => {
            json.string("literal");
            json.comma();
            json.key("value");
            render_value(json, value);
        }
        HirExprKind::ParameterRef(symbol) => {
            json.string("parameter_ref");
            json.comma();
            json.key("symbol");
            json.string(&symbol.as_string());
        }
        HirExprKind::BindingRef(symbol) => {
            json.string("binding_ref");
            json.comma();
            json.key("symbol");
            json.string(&symbol.as_string());
        }
        HirExprKind::SelfRef => json.string("self_ref"),
        HirExprKind::ResultRef => json.string("result_ref"),
        HirExprKind::OldStateField { field } => {
            json.string("old_state_field");
            json.comma();
            json.key("field");
            json.string(&field.as_string());
        }
        HirExprKind::ConstantRef(symbol) => {
            json.string("constant_ref");
            json.comma();
            json.key("symbol");
            json.string(&symbol.as_string());
        }
        HirExprKind::EnumSingletonRef(symbol) => {
            json.string("enum_singleton_ref");
            json.comma();
            json.key("symbol");
            json.string(&symbol.as_string());
        }
        HirExprKind::Field { base, name } => {
            json.string("field");
            json.comma();
            json.key("base");
            render_expr(json, base);
            json.comma();
            json.key("name");
            json.string(name);
        }
        HirExprKind::Len { value } => {
            json.string("len");
            json.comma();
            json.key("value");
            render_expr(json, value);
        }
        HirExprKind::Unary { op, operand } => {
            json.string("unary");
            json.comma();
            json.key("op");
            json.string(unary_name(*op));
            json.comma();
            json.key("operand");
            render_expr(json, operand);
        }
        HirExprKind::Binary { op, left, right } => {
            json.string("binary");
            json.comma();
            json.key("left");
            render_expr(json, left);
            json.comma();
            json.key("op");
            json.string(binary_name(*op));
            json.comma();
            json.key("right");
            render_expr(json, right);
        }
        HirExprKind::ComparisonChain {
            operands,
            operators,
        } => {
            json.string("comparison_chain");
            json.comma();
            json.key("operands");
            json.array_start();
            for (i, value) in operands.iter().enumerate() {
                if i != 0 {
                    json.comma();
                }
                render_expr(json, value);
            }
            json.array_end();
            json.comma();
            json.key("operators");
            json.array_start();
            for (i, value) in operators.iter().enumerate() {
                if i != 0 {
                    json.comma();
                }
                json.string(compare_name(*value));
            }
            json.array_end();
        }
    }
    json.comma();
    json.key("reference");
    match &expression.reference {
        Some(value) => render_reference(json, value),
        None => json.null(),
    };
    json.comma();
    json.key("span");
    render_span(json, &expression.span);
    json.comma();
    json.key("type");
    render_type(json, &expression.ty);
    json.object_end();
}
fn render_reference(json: &mut Json, reference: &HirReference) {
    json.object_start();
    match reference {
        HirReference::Parameter(value) => {
            json.key("kind");
            json.string("parameter");
            json.comma();
            json.key("symbol");
            json.string(&value.as_string());
        }
        HirReference::Binding(value) => {
            json.key("kind");
            json.string("binding");
            json.comma();
            json.key("symbol");
            json.string(&value.as_string());
        }
        HirReference::Constant(value) => {
            json.key("kind");
            json.string("constant");
            json.comma();
            json.key("symbol");
            json.string(&value.as_string());
        }
        HirReference::EnumSingleton(value) => {
            json.key("kind");
            json.string("enum_singleton");
            json.comma();
            json.key("symbol");
            json.string(&value.as_string());
        }
        HirReference::Field(value) => {
            json.key("kind");
            json.string("field");
            json.comma();
            json.key("symbol");
            json.string(&value.as_string());
        }
        HirReference::OldStateField(value) => {
            json.key("kind");
            json.string("old_state_field");
            json.comma();
            json.key("symbol");
            json.string(&value.as_string());
        }
    }
    json.object_end();
}
fn render_pattern(json: &mut Json, pattern: &HirPattern) {
    json.object_start();
    json.key("kind");
    match &pattern.kind {
        HirPatternKind::Variant { symbol, arguments } => {
            json.string("variant");
            json.comma();
            json.key("arguments");
            json.array_start();
            for (i, value) in arguments.iter().enumerate() {
                if i != 0 {
                    json.comma();
                }
                render_pattern(json, value);
            }
            json.array_end();
            json.comma();
            json.key("symbol");
            json.string(&symbol.as_string());
        }
        HirPatternKind::Binding { symbol, name } => {
            json.string("binding");
            json.comma();
            json.key("name");
            json.string(name);
            json.comma();
            json.key("symbol");
            json.string(&symbol.as_string());
        }
        HirPatternKind::Wildcard => json.string("wildcard"),
    }
    json.comma();
    json.key("span");
    render_span(json, &pattern.span);
    json.comma();
    json.key("type");
    render_type(json, &pattern.ty);
    json.object_end();
}

fn render_value(json: &mut Json, value: &HirValue) {
    json.object_start();
    match value {
        HirValue::Bool(value) => {
            json.key("kind");
            json.string("bool");
            json.comma();
            json.key("value");
            json.boolean(*value);
        }
        HirValue::Integer(value) => {
            json.key("kind");
            json.string("integer");
            json.comma();
            json.key("value");
            json.string(value);
        }
        HirValue::F32 { bits } => {
            json.key("bits");
            json.string(bits);
            json.comma();
            json.key("kind");
            json.string("f32");
        }
        HirValue::F64 { bits } => {
            json.key("bits");
            json.string(bits);
            json.comma();
            json.key("kind");
            json.string("f64");
        }
        HirValue::String(value) => {
            json.key("kind");
            json.string("string");
            json.comma();
            json.key("value");
            json.string(value);
        }
        HirValue::Bytes(value) => {
            json.key("kind");
            json.string("bytes");
            json.comma();
            json.key("value");
            let mut hex = String::with_capacity(value.len() * 2);
            for byte in value {
                write!(hex, "{byte:02x}").expect("writing to a String cannot fail");
            }
            json.string(&hex);
        }
        HirValue::Unit => {
            json.key("kind");
            json.string("unit");
        }
        HirValue::Option(value) => {
            json.key("kind");
            json.string("option");
            json.comma();
            json.key("value");
            match value {
                Some(value) => render_value(json, value),
                None => json.null(),
            }
        }
        HirValue::Result { ok, value } => {
            json.key("kind");
            json.string("result");
            json.comma();
            json.key("ok");
            json.boolean(*ok);
            json.comma();
            json.key("value");
            render_value(json, value);
        }
        HirValue::List(value) => {
            json.key("items");
            render_values(json, value);
            json.comma();
            json.key("kind");
            json.string("list");
        }
        HirValue::Set(value) => {
            json.key("items");
            render_values(json, value);
            json.comma();
            json.key("kind");
            json.string("set");
        }
        HirValue::Map(value) => {
            json.key("entries");
            json.array_start();
            for (i, (key, value)) in value.iter().enumerate() {
                if i != 0 {
                    json.comma();
                }
                json.array_start();
                render_value(json, key);
                json.comma();
                render_value(json, value);
                json.array_end();
            }
            json.array_end();
            json.comma();
            json.key("kind");
            json.string("map");
        }
        HirValue::Tuple2(first, second) => {
            json.key("first");
            render_value(json, first);
            json.comma();
            json.key("kind");
            json.string("tuple2");
            json.comma();
            json.key("second");
            render_value(json, second);
        }
        HirValue::Named { symbol, fields } => {
            json.key("fields");
            render_named_fields(json, fields);
            json.comma();
            json.key("kind");
            json.string("named");
            json.comma();
            json.key("symbol");
            json.string(&symbol.as_string());
        }
        HirValue::Enum { variant, fields } => {
            json.key("fields");
            render_values(json, fields);
            json.comma();
            json.key("kind");
            json.string("enum");
            json.comma();
            json.key("variant");
            json.string(&variant.as_string());
        }
        HirValue::Json(value) => {
            json.key("kind");
            json.string("json");
            json.comma();
            json.key("value");
            json.raw_value(value);
        }
    }
    json.object_end();
}
fn render_values(json: &mut Json, values: &[HirValue]) {
    json.array_start();
    for (i, value) in values.iter().enumerate() {
        if i != 0 {
            json.comma();
        }
        render_value(json, value);
    }
    json.array_end();
}
fn render_named_fields(json: &mut Json, fields: &[(String, HirValue)]) {
    json.array_start();
    for (i, (name, value)) in fields.iter().enumerate() {
        if i != 0 {
            json.comma();
        }
        json.object_start();
        json.key("name");
        json.string(name);
        json.comma();
        json.key("value");
        render_value(json, value);
        json.object_end();
    }
    json.array_end();
}

fn primitive_name(value: PrimitiveType) -> &'static str {
    match value {
        PrimitiveType::Bool => "bool",
        PrimitiveType::I8 => "i8",
        PrimitiveType::I16 => "i16",
        PrimitiveType::I32 => "i32",
        PrimitiveType::I64 => "i64",
        PrimitiveType::U8 => "u8",
        PrimitiveType::U16 => "u16",
        PrimitiveType::U32 => "u32",
        PrimitiveType::U64 => "u64",
        PrimitiveType::F32 => "f32",
        PrimitiveType::F64 => "f64",
        PrimitiveType::Str => "str",
        PrimitiveType::Bytes => "bytes",
        PrimitiveType::Path => "path",
        PrimitiveType::Unit => "unit",
        PrimitiveType::JsonValue => "json",
        PrimitiveType::Never => "never",
    }
}
fn parameter_kind(value: HirParameterKind) -> &'static str {
    match value {
        HirParameterKind::Positional => "positional",
        HirParameterKind::KeywordOnly => "keyword_only",
        HirParameterKind::VarArg => "vararg",
        HirParameterKind::KwArg => "kwarg",
    }
}
fn unary_name(value: HirUnaryOp) -> &'static str {
    match value {
        HirUnaryOp::Not => "not",
        HirUnaryOp::Plus => "plus",
        HirUnaryOp::Minus => "minus",
    }
}
fn binary_name(value: HirBinaryOp) -> &'static str {
    match value {
        HirBinaryOp::Or => "or",
        HirBinaryOp::And => "and",
        HirBinaryOp::Add => "add",
        HirBinaryOp::Subtract => "subtract",
        HirBinaryOp::Multiply => "multiply",
        HirBinaryOp::Divide => "divide",
        HirBinaryOp::Remainder => "remainder",
    }
}
fn compare_name(value: HirCompareOp) -> &'static str {
    match value {
        HirCompareOp::Equal => "equal",
        HirCompareOp::NotEqual => "not_equal",
        HirCompareOp::Less => "less",
        HirCompareOp::LessEqual => "less_equal",
        HirCompareOp::Greater => "greater",
        HirCompareOp::GreaterEqual => "greater_equal",
    }
}
fn source_string(path: &Path) -> String {
    path.to_string_lossy().replace('\\', "/")
}

struct Json<'a> {
    bytes: Vec<u8>,
    source: &'a [u8],
}
impl<'a> Json<'a> {
    fn new(source: &'a [u8]) -> Self {
        Self {
            bytes: Vec::new(),
            source,
        }
    }
    fn location(&self, offset: usize) -> (usize, usize) {
        let offset = offset.min(self.source.len());
        let before = &self.source[..offset];
        let line_start = before
            .iter()
            .rposition(|byte| *byte == b'\n')
            .map_or(0, |index| index + 1);
        let line = before.iter().filter(|byte| **byte == b'\n').count() + 1;
        let column = std::str::from_utf8(&self.source[line_start..offset])
            .expect("Cott source is UTF-8")
            .chars()
            .count()
            + 1;
        (line, column)
    }
    fn object_start(&mut self) {
        self.bytes.push(b'{');
    }
    fn object_end(&mut self) {
        self.bytes.push(b'}');
    }
    fn array_start(&mut self) {
        self.bytes.push(b'[');
    }
    fn array_end(&mut self) {
        self.bytes.push(b']');
    }
    fn comma(&mut self) {
        self.bytes.push(b',');
    }
    fn key(&mut self, key: &str) {
        self.string(key);
        self.bytes.push(b':');
    }
    fn raw_value(&mut self, value: &Value) {
        self.bytes
            .extend(serde_json::to_vec(value).expect("JSON values serialize"));
    }
    fn string(&mut self, value: &str) {
        self.bytes
            .extend(serde_json::to_vec(value).expect("strings serialize"));
    }
    fn number(&mut self, value: &str) {
        self.bytes.extend_from_slice(value.as_bytes());
    }
    fn number_usize(&mut self, value: usize) {
        self.number(&value.to_string());
    }
    fn number_u32(&mut self, value: u32) {
        self.number(&value.to_string());
    }
    fn boolean(&mut self, value: bool) {
        self.number(if value { "true" } else { "false" });
    }
    fn null(&mut self) {
        self.number("null");
    }
    fn newline(&mut self) {
        self.bytes.push(b'\n');
    }
}
