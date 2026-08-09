//! Owned, target-independent high-level intermediate representation.
//!
//! This module deliberately contains no semantic aliases.  The temporary
//! [`lower`] bridge retains the old analyzer for callers that have not moved
//! to the HIR pipeline yet; every type below is owned by this module.

use std::path::{Path, PathBuf};

use crate::compiler::{ParsedProject, ProjectDiagnostic};
use crate::diagnostics::Span;

/// Canonical module identity, in source order from the root segment.
#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct ModuleId {
    pub segments: Vec<String>,
}

impl ModuleId {
    pub fn new(segments: Vec<String>) -> Self {
        Self { segments }
    }

    pub fn as_string(&self) -> String {
        self.segments.join(".")
    }
}

/// Canonical declaration, binding, and reference identity.
#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct SymbolId {
    pub module: ModuleId,
    pub name: String,
}

impl SymbolId {
    pub fn new(module: ModuleId, name: impl Into<String>) -> Self {
        Self {
            module,
            name: name.into(),
        }
    }

    pub fn as_string(&self) -> String {
        if self.module.segments.is_empty() {
            self.name.clone()
        } else {
            format!("{}.{}", self.module.as_string(), self.name)
        }
    }
}

/// Primitive types have a closed representation so target backends cannot
/// invent additional semantic cases.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum PrimitiveType {
    Bool,
    I8,
    I16,
    I32,
    I64,
    U8,
    U16,
    U32,
    U64,
    F32,
    F64,
    Str,
    Bytes,
    Unit,
    JsonValue,
    Never,
}

/// Alias-free HIR type representation.
#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub enum HirType {
    Primitive(PrimitiveType),
    Named {
        symbol: SymbolId,
        args: Vec<HirType>,
    },
    TypeParameter {
        name: String,
    },
    List {
        item: Box<HirType>,
    },
    Set {
        item: Box<HirType>,
    },
    Map {
        key: Box<HirType>,
        value: Box<HirType>,
    },
    Tuple2 {
        first: Box<HirType>,
        second: Box<HirType>,
    },
    Option {
        item: Box<HirType>,
    },
    Result {
        ok: Box<HirType>,
        error: Box<HirType>,
    },
    Opaque {
        tag: String,
    },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirDoc {
    pub span: Span,
    pub text: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirImport {
    pub span: Span,
    pub symbol: SymbolId,
    pub name: String,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirGenericParam {
    pub span: Span,
    pub name: String,
    pub bounds: Vec<HirType>,
    pub source_order: usize,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HirParameterKind {
    Positional,
    KeywordOnly,
    VarArg,
    KwArg,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirParameter {
    pub span: Span,
    pub name: String,
    pub ty: HirType,
    pub default: Option<HirValue>,
    pub kind: HirParameterKind,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirField {
    pub span: Span,
    pub name: String,
    pub ty: HirType,
    pub default: Option<HirValue>,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirVariant {
    pub symbol: SymbolId,
    pub span: Span,
    pub name: String,
    pub fields: Vec<HirField>,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirEffect {
    pub span: Span,
    pub key: String,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirClause {
    pub clause_id: u32,
    pub span: Span,
    pub kind: HirClauseKind,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum HirClauseKind {
    Requires {
        expression: HirExpr,
    },
    Ensures {
        pattern: Option<HirPattern>,
        expression: HirExpr,
    },
    Error {
        variant: SymbolId,
        priority: Option<u32>,
        when: Option<HirExpr>,
    },
}

#[derive(Clone, Debug, Eq, PartialEq, Default)]
pub struct HirContract {
    /// Clauses retain source order; `clause_id` is stable within a function.
    pub clauses: Vec<HirClause>,
    pub effects: Vec<HirEffect>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirAlias {
    pub id: SymbolId,
    pub span: Span,
    pub doc: Option<HirDoc>,
    pub generics: Vec<HirGenericParam>,
    pub target: HirType,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirNewtype {
    pub id: SymbolId,
    pub span: Span,
    pub doc: Option<HirDoc>,
    pub generics: Vec<HirGenericParam>,
    pub carrier: HirType,
    pub refinement: Option<HirExpr>,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirStruct {
    pub id: SymbolId,
    pub span: Span,
    pub doc: Option<HirDoc>,
    pub generics: Vec<HirGenericParam>,
    pub fields: Vec<HirField>,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirEnum {
    pub id: SymbolId,
    pub span: Span,
    pub doc: Option<HirDoc>,
    pub generics: Vec<HirGenericParam>,
    pub variants: Vec<HirVariant>,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirMethod {
    pub id: SymbolId,
    pub span: Span,
    pub doc: Option<HirDoc>,
    pub generics: Vec<HirGenericParam>,
    pub parameters: Vec<HirParameter>,
    pub return_type: HirType,
    pub contract: HirContract,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirTrait {
    pub id: SymbolId,
    pub span: Span,
    pub doc: Option<HirDoc>,
    pub generics: Vec<HirGenericParam>,
    pub methods: Vec<HirMethod>,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirConst {
    pub id: SymbolId,
    pub span: Span,
    pub doc: Option<HirDoc>,
    pub ty: HirType,
    pub value: HirValue,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirFunction {
    pub id: SymbolId,
    pub span: Span,
    pub doc: Option<HirDoc>,
    pub generics: Vec<HirGenericParam>,
    pub parameters: Vec<HirParameter>,
    pub return_type: HirType,
    pub contract: HirContract,
    pub body: Option<HirExpr>,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum HirDeclaration {
    Alias(HirAlias),
    Newtype(HirNewtype),
    Struct(HirStruct),
    Enum(HirEnum),
    Trait(HirTrait),
    Const(HirConst),
    Function(HirFunction),
}

impl HirDeclaration {
    pub fn id(&self) -> &SymbolId {
        match self {
            Self::Alias(value) => &value.id,
            Self::Newtype(value) => &value.id,
            Self::Struct(value) => &value.id,
            Self::Enum(value) => &value.id,
            Self::Trait(value) => &value.id,
            Self::Const(value) => &value.id,
            Self::Function(value) => &value.id,
        }
    }

    pub fn span(&self) -> &Span {
        match self {
            Self::Alias(value) => &value.span,
            Self::Newtype(value) => &value.span,
            Self::Struct(value) => &value.span,
            Self::Enum(value) => &value.span,
            Self::Trait(value) => &value.span,
            Self::Const(value) => &value.span,
            Self::Function(value) => &value.span,
        }
    }

    pub fn public(&self) -> bool {
        match self {
            Self::Alias(value) => value.public,
            Self::Newtype(value) => value.public,
            Self::Struct(value) => value.public,
            Self::Enum(value) => value.public,
            Self::Trait(value) => value.public,
            Self::Const(value) => value.public,
            Self::Function(value) => value.public,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirModule {
    pub source: PathBuf,
    pub id: ModuleId,
    pub imports: Vec<HirImport>,
    pub declarations: Vec<HirDeclaration>,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirProject {
    pub modules: Vec<HirModule>,
    /// Temporary bridge for old emitters. New passes must consume `modules`.
    legacy: Option<crate::semantic::SemanticProject>,
}

impl HirProject {
    pub fn new(modules: Vec<HirModule>) -> Self {
        Self {
            modules,
            legacy: None,
        }
    }

    fn from_legacy(legacy: crate::semantic::SemanticProject) -> Self {
        let modules = legacy
            .modules
            .iter()
            .enumerate()
            .map(|(source_order, module)| lower_module(module, source_order))
            .collect();
        Self {
            modules,
            legacy: Some(legacy),
        }
    }

    /// Explicitly exposes the retained legacy snapshot to the few consumers
    /// that still use the pre-HIR emitter and binding APIs.
    pub(crate) fn legacy(&self) -> Option<&crate::semantic::SemanticProject> {
        self.legacy.as_ref()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum HirReference {
    Parameter(SymbolId),
    Binding(SymbolId),
    Constant(SymbolId),
    EnumSingleton(SymbolId),
    Field(SymbolId),
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HirUnaryOp {
    Not,
    Plus,
    Minus,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HirBinaryOp {
    Or,
    And,
    Add,
    Subtract,
    Multiply,
    Divide,
    Remainder,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HirCompareOp {
    Equal,
    NotEqual,
    Less,
    LessEqual,
    Greater,
    GreaterEqual,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirExpr {
    pub span: Span,
    pub ty: HirType,
    pub reference: Option<HirReference>,
    pub kind: HirExprKind,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum HirExprKind {
    Literal(HirValue),
    ParameterRef(SymbolId),
    BindingRef(SymbolId),
    SelfRef,
    ConstantRef(SymbolId),
    EnumSingletonRef(SymbolId),
    Field {
        base: Box<HirExpr>,
        name: String,
    },
    Len {
        value: Box<HirExpr>,
    },
    Unary {
        op: HirUnaryOp,
        operand: Box<HirExpr>,
    },
    Binary {
        op: HirBinaryOp,
        left: Box<HirExpr>,
        right: Box<HirExpr>,
    },
    ComparisonChain {
        operands: Vec<HirExpr>,
        operators: Vec<HirCompareOp>,
    },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirPattern {
    pub span: Span,
    pub ty: HirType,
    pub kind: HirPatternKind,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum HirPatternKind {
    Variant {
        symbol: SymbolId,
        arguments: Vec<HirPattern>,
    },
    Binding {
        symbol: SymbolId,
        name: String,
    },
    Wildcard,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum HirValue {
    Bool(bool),
    Integer(String),
    F32 {
        bits: String,
    },
    F64 {
        bits: String,
    },
    String(String),
    Bytes(Vec<u8>),
    Unit,
    Option(Option<Box<HirValue>>),
    Result {
        ok: bool,
        value: Box<HirValue>,
    },
    List(Vec<HirValue>),
    Set(Vec<HirValue>),
    Map(Vec<(HirValue, HirValue)>),
    Tuple2(Box<HirValue>, Box<HirValue>),
    Named {
        symbol: SymbolId,
        fields: Vec<(String, HirValue)>,
    },
    Enum {
        variant: SymbolId,
        fields: Vec<HirValue>,
    },
    Json(serde_json::Value),
}
fn lower_module(module: &crate::semantic::SemanticModule, source_order: usize) -> HirModule {
    let imports = module
        .imports
        .iter()
        .enumerate()
        .map(|(source_order, import)| HirImport {
            span: import.span.clone(),
            symbol: lower_symbol(&import.symbol),
            name: import.name.clone(),
            source_order,
        })
        .collect();
    let declarations = module
        .declarations
        .iter()
        .enumerate()
        .map(|(source_order, declaration)| lower_declaration(declaration, source_order))
        .collect();
    HirModule {
        source: module.source.clone(),
        id: lower_module_id(&module.id),
        imports,
        declarations,
        source_order,
    }
}

fn lower_module_id(id: &crate::semantic::ModuleId) -> ModuleId {
    ModuleId::new(id.segments.clone())
}

fn lower_symbol(id: &crate::semantic::SymbolId) -> SymbolId {
    SymbolId::new(lower_module_id(&id.module), id.name.clone())
}

fn lower_doc(doc: Option<&crate::semantic::SemanticDoc>) -> Option<HirDoc> {
    doc.map(|doc| HirDoc {
        span: doc.span.clone(),
        text: doc.text.clone(),
    })
}

fn lower_type(ty: &crate::semantic::ResolvedType) -> HirType {
    use crate::semantic::{PrimitiveType as LegacyPrimitiveType, ResolvedType};
    match ty {
        ResolvedType::Primitive(primitive) => HirType::Primitive(match primitive {
            LegacyPrimitiveType::Bool => PrimitiveType::Bool,
            LegacyPrimitiveType::I8 => PrimitiveType::I8,
            LegacyPrimitiveType::I16 => PrimitiveType::I16,
            LegacyPrimitiveType::I32 => PrimitiveType::I32,
            LegacyPrimitiveType::I64 => PrimitiveType::I64,
            LegacyPrimitiveType::U8 => PrimitiveType::U8,
            LegacyPrimitiveType::U16 => PrimitiveType::U16,
            LegacyPrimitiveType::U32 => PrimitiveType::U32,
            LegacyPrimitiveType::U64 => PrimitiveType::U64,
            LegacyPrimitiveType::F64 => PrimitiveType::F64,
            LegacyPrimitiveType::Str => PrimitiveType::Str,
            LegacyPrimitiveType::Bytes => PrimitiveType::Bytes,
            LegacyPrimitiveType::Unit => PrimitiveType::Unit,
        }),
        ResolvedType::Named(symbol) => HirType::Named {
            symbol: lower_symbol(symbol),
            args: Vec::new(),
        },
        ResolvedType::Option(item) => HirType::Option {
            item: Box::new(lower_type(item)),
        },
        ResolvedType::Result { ok, error } => HirType::Result {
            ok: Box::new(lower_type(ok)),
            error: Box::new(HirType::Named {
                symbol: lower_symbol(error),
                args: Vec::new(),
            }),
        },
    }
}

fn lower_value(value: &crate::semantic::SemanticValue) -> HirValue {
    use crate::semantic::SemanticValue;
    match value {
        SemanticValue::Bool(value) => HirValue::Bool(*value),
        SemanticValue::Integer(value) => HirValue::Integer(value.clone()),
        SemanticValue::Float(value) => HirValue::F64 {
            bits: value
                .parse::<f64>()
                .map(|value| format!("{:016x}", value.to_bits()))
                .unwrap_or_else(|_| String::from("0000000000000000")),
        },
        SemanticValue::String(value) => HirValue::String(value.clone()),
        SemanticValue::Unit => HirValue::Unit,
    }
}

fn lower_parameter(
    parameter: &crate::semantic::SemanticParameter,
    source_order: usize,
) -> HirParameter {
    HirParameter {
        span: parameter.span.clone(),
        name: parameter.name.clone(),
        ty: lower_type(&parameter.ty),
        default: None,
        kind: HirParameterKind::Positional,
        source_order,
    }
}

fn lower_field(field: &crate::semantic::SemanticField, source_order: usize) -> HirField {
    HirField {
        span: field.span.clone(),
        name: field.name.clone(),
        ty: lower_type(&field.ty),
        default: field.default.as_ref().map(lower_value),
        source_order,
    }
}

fn lower_declaration(
    declaration: &crate::semantic::SemanticDeclaration,
    source_order: usize,
) -> HirDeclaration {
    use crate::semantic::SemanticDeclaration;
    match declaration {
        SemanticDeclaration::Alias(value) => HirDeclaration::Alias(HirAlias {
            id: lower_symbol(&value.id),
            span: value.span.clone(),
            doc: lower_doc(value.doc.as_ref()),
            generics: Vec::new(),
            target: lower_type(&value.target),
            public: true,
            source_order,
        }),
        SemanticDeclaration::Newtype(value) => HirDeclaration::Newtype(HirNewtype {
            id: lower_symbol(&value.id),
            span: value.span.clone(),
            doc: lower_doc(value.doc.as_ref()),
            generics: Vec::new(),
            carrier: lower_type(&value.underlying),
            refinement: None,
            public: true,
            source_order,
        }),
        SemanticDeclaration::Struct(value) => HirDeclaration::Struct(HirStruct {
            id: lower_symbol(&value.id),
            span: value.span.clone(),
            doc: lower_doc(value.doc.as_ref()),
            generics: Vec::new(),
            fields: value
                .fields
                .iter()
                .enumerate()
                .map(|(source_order, field)| lower_field(field, source_order))
                .collect(),
            public: true,
            source_order,
        }),
        SemanticDeclaration::Enum(value) => HirDeclaration::Enum(HirEnum {
            id: lower_symbol(&value.id),
            span: value.span.clone(),
            doc: lower_doc(value.doc.as_ref()),
            generics: Vec::new(),
            variants: value
                .variants
                .iter()
                .enumerate()
                .map(|(source_order, variant)| HirVariant {
                    symbol: lower_symbol(&variant.id),
                    span: variant.span.clone(),
                    name: variant.name.clone(),
                    fields: variant
                        .parameters
                        .iter()
                        .enumerate()
                        .map(|(source_order, parameter)| HirField {
                            span: parameter.span.clone(),
                            name: parameter.name.clone(),
                            ty: lower_type(&parameter.ty),
                            default: None,
                            source_order,
                        })
                        .collect(),
                    source_order,
                })
                .collect(),
            public: true,
            source_order,
        }),
        SemanticDeclaration::Const(value) => HirDeclaration::Const(HirConst {
            id: lower_symbol(&value.id),
            span: value.span.clone(),
            doc: lower_doc(value.doc.as_ref()),
            ty: lower_type(&value.ty),
            value: lower_value(&value.value),
            public: true,
            source_order,
        }),
        SemanticDeclaration::Function(value) => HirDeclaration::Function(HirFunction {
            id: lower_symbol(&value.id),
            span: value.span.clone(),
            doc: lower_doc(value.doc.as_ref()),
            generics: Vec::new(),
            parameters: value
                .parameters
                .iter()
                .enumerate()
                .map(|(source_order, parameter)| lower_parameter(parameter, source_order))
                .collect(),
            return_type: lower_type(&value.return_type),
            contract: HirContract::default(),
            body: None,
            public: true,
            source_order,
        }),
    }
}

/// Temporary lowering bridge. New passes should consume `HirProject::new`
/// values directly; legacy consumers use the explicit internal accessor.
pub fn lower(
    source_root: &Path,
    parsed: ParsedProject,
) -> Result<HirProject, Vec<ProjectDiagnostic>> {
    crate::semantic::analyze_project(source_root, parsed).map(HirProject::from_legacy)
}
