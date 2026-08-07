use std::path::{Path, PathBuf};

use crate::diagnostics::Span;
use crate::semantic::{
    PrimitiveType, ResolvedType, SemanticDeclaration, SemanticDoc, SemanticField, SemanticImport,
    SemanticModule, SemanticParameter, SemanticProject, SemanticValue, SemanticVariant,
};

/// Deterministic canonical IR for a semantic project.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CanonicalIr {
    pub modules: Vec<CanonicalModule>,
}

/// One complete canonical JSON module document.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CanonicalModule {
    pub module: crate::semantic::ModuleId,
    pub source: PathBuf,
    pub bytes: Vec<u8>,
}

/// Render a semantic project without consulting its source files.
pub fn render(project: &SemanticProject) -> CanonicalIr {
    CanonicalIr {
        modules: project.modules.iter().map(render_module).collect(),
    }
}

fn render_module(module: &SemanticModule) -> CanonicalModule {
    let mut json = Json::new();
    json.object_start();
    json.key("declarations");
    json.array_start();
    for declaration in &module.declarations {
        render_declaration(&mut json, declaration);
    }
    json.array_end();
    json.comma();
    json.key("imports");
    let mut imports: Vec<&SemanticImport> = module.imports.iter().collect();
    imports.sort_by(|a, b| a.symbol.as_string().cmp(&b.symbol.as_string()));
    json.array_start();
    for (index, import) in imports.iter().enumerate() {
        if index != 0 {
            json.comma();
        }
        json.string(&import.symbol.as_string());
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

fn render_declaration(json: &mut Json, declaration: &SemanticDeclaration) {
    match declaration {
        SemanticDeclaration::Alias(value) => {
            json.object_start();
            json.key("doc");
            render_doc(json, value.doc.as_ref());
            json.comma();
            json.key("kind");
            json.string("alias");
            json.comma();
            json.key("name");
            json.string(&value.id.as_string());
            json.comma();
            json.key("span");
            render_span(json, &value.span);
            json.comma();
            json.key("target");
            render_type(json, &value.target);
            json.object_end();
        }
        SemanticDeclaration::Newtype(value) => {
            json.object_start();
            json.key("carrier");
            render_type(json, &value.underlying);
            json.comma();
            json.key("doc");
            render_doc(json, value.doc.as_ref());
            json.comma();
            json.key("kind");
            json.string("newtype");
            json.comma();
            json.key("name");
            json.string(&value.id.as_string());
            json.comma();
            json.key("span");
            render_span(json, &value.span);
            json.object_end();
        }
        SemanticDeclaration::Struct(value) => {
            json.object_start();
            json.key("doc");
            render_doc(json, value.doc.as_ref());
            json.comma();
            json.key("fields");
            render_fields(json, &value.fields);
            json.comma();
            json.key("kind");
            json.string("struct");
            json.comma();
            json.key("name");
            json.string(&value.id.as_string());
            json.comma();
            json.key("span");
            render_span(json, &value.span);
            json.object_end();
        }
        SemanticDeclaration::Enum(value) => {
            json.object_start();
            json.key("doc");
            render_doc(json, value.doc.as_ref());
            json.comma();
            json.key("kind");
            json.string("enum");
            json.comma();
            json.key("name");
            json.string(&value.id.as_string());
            json.comma();
            json.key("span");
            render_span(json, &value.span);
            json.comma();
            json.key("variants");
            render_variants(json, &value.variants);
            json.object_end();
        }
        SemanticDeclaration::Const(value) => {
            json.object_start();
            json.key("doc");
            render_doc(json, value.doc.as_ref());
            json.comma();
            json.key("kind");
            json.string("const");
            json.comma();
            json.key("name");
            json.string(&value.id.as_string());
            json.comma();
            json.key("span");
            render_span(json, &value.span);
            json.comma();
            json.key("type");
            render_type(json, &value.ty);
            json.comma();
            json.key("value");
            render_value(json, &value.value);
            json.object_end();
        }
        SemanticDeclaration::Function(value) => {
            json.object_start();
            json.key("doc");
            render_doc(json, value.doc.as_ref());
            json.comma();
            json.key("kind");
            json.string("function");
            json.comma();
            json.key("name");
            json.string(&value.id.as_string());
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
    }
}

fn render_type(json: &mut Json, ty: &ResolvedType) {
    match ty {
        ResolvedType::Primitive(primitive) => {
            json.object_start();
            json.key("kind");
            json.string("primitive");
            json.comma();
            json.key("name");
            json.string(primitive_name(*primitive));
            json.object_end();
        }
        ResolvedType::Named(symbol) => {
            json.object_start();
            json.key("kind");
            json.string("named");
            json.comma();
            json.key("name");
            json.string(&symbol.as_string());
            json.object_end();
        }
        ResolvedType::Option(item) => {
            json.object_start();
            json.key("item");
            render_type(json, item);
            json.comma();
            json.key("kind");
            json.string("option");
            json.object_end();
        }
        ResolvedType::Result { ok, error } => {
            json.object_start();
            json.key("error");
            json.object_start();
            json.key("kind");
            json.string("named");
            json.comma();
            json.key("name");
            json.string(&error.as_string());
            json.object_end();
            json.comma();
            json.key("kind");
            json.string("result");
            json.comma();
            json.key("ok");
            render_type(json, ok);
            json.object_end();
        }
    }
}

fn render_fields(json: &mut Json, fields: &[SemanticField]) {
    json.array_start();
    for (index, field) in fields.iter().enumerate() {
        if index != 0 {
            json.comma();
        }
        json.object_start();
        json.key("default");
        match &field.default {
            Some(value) => render_value(json, value),
            None => json.null(),
        }
        json.comma();
        json.key("name");
        json.string(&field.name);
        json.comma();
        json.key("span");
        render_span(json, &field.span);
        json.comma();
        json.key("type");
        render_type(json, &field.ty);
        json.object_end();
    }
    json.array_end();
}

fn render_parameters(json: &mut Json, parameters: &[SemanticParameter]) {
    json.array_start();
    for (index, parameter) in parameters.iter().enumerate() {
        if index != 0 {
            json.comma();
        }
        json.object_start();
        json.key("name");
        json.string(&parameter.name);
        json.comma();
        json.key("span");
        render_span(json, &parameter.span);
        json.comma();
        json.key("type");
        render_type(json, &parameter.ty);
        json.object_end();
    }
    json.array_end();
}

fn render_variants(json: &mut Json, variants: &[SemanticVariant]) {
    json.array_start();
    for (index, variant) in variants.iter().enumerate() {
        if index != 0 {
            json.comma();
        }
        json.object_start();
        json.key("name");
        json.string(&variant.id.as_string());
        json.comma();
        json.key("parameters");
        render_parameters(json, &variant.parameters);
        json.comma();
        json.key("span");
        render_span(json, &variant.span);
        json.object_end();
    }
    json.array_end();
}

fn render_doc(json: &mut Json, doc: Option<&SemanticDoc>) {
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

fn render_span(json: &mut Json, span: &Span) {
    json.object_start();
    json.key("end");
    json.number_usize(span.end);
    json.comma();
    json.key("start");
    json.number_usize(span.start);
    json.object_end();
}

fn render_value(json: &mut Json, value: &SemanticValue) {
    match value {
        SemanticValue::Bool(value) => json.boolean(*value),
        SemanticValue::Integer(value) | SemanticValue::Float(value) => json.string(value),
        SemanticValue::String(value) => json.string(value),
        SemanticValue::Unit => json.null(),
    }
}

fn primitive_name(primitive: PrimitiveType) -> &'static str {
    match primitive {
        PrimitiveType::Bool => "bool",
        PrimitiveType::I8 => "i8",
        PrimitiveType::I16 => "i16",
        PrimitiveType::I32 => "i32",
        PrimitiveType::I64 => "i64",
        PrimitiveType::U8 => "u8",
        PrimitiveType::U16 => "u16",
        PrimitiveType::U32 => "u32",
        PrimitiveType::U64 => "u64",
        PrimitiveType::F64 => "f64",
        PrimitiveType::Str => "str",
        PrimitiveType::Bytes => "bytes",
        PrimitiveType::Unit => "unit",
    }
}

fn source_string(path: &Path) -> String {
    path.to_string_lossy().replace('\\', "/")
}

struct Json {
    bytes: Vec<u8>,
}

impl Json {
    fn new() -> Self {
        Self { bytes: Vec::new() }
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

    fn string(&mut self, value: &str) {
        self.bytes.push(b'"');
        for character in value.chars() {
            match character {
                '"' => self.bytes.extend_from_slice(b"\\\""),
                '\\' => self.bytes.extend_from_slice(b"\\\\"),
                '\u{08}' => self.bytes.extend_from_slice(b"\\b"),
                '\u{0C}' => self.bytes.extend_from_slice(b"\\f"),
                '\n' => self.bytes.extend_from_slice(b"\\n"),
                '\r' => self.bytes.extend_from_slice(b"\\r"),
                '\t' => self.bytes.extend_from_slice(b"\\t"),
                character if character < '\u{20}' => self
                    .bytes
                    .extend_from_slice(format!("\\u{:04x}", character as u32).as_bytes()),
                character => {
                    let mut encoded = [0; 4];
                    self.bytes
                        .extend_from_slice(character.encode_utf8(&mut encoded).as_bytes());
                }
            }
        }
        self.bytes.push(b'"');
    }

    fn number(&mut self, value: &str) {
        self.bytes.extend_from_slice(value.as_bytes());
    }

    fn number_usize(&mut self, value: usize) {
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
