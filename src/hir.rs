//! Owned, target-independent high-level intermediate representation.
//!
//! Lowering and structural validation live entirely in this module.

use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::path::{Component, Path, PathBuf};
use std::sync::Arc;

use crate::ast::{
    self, BinaryOp, ClauseKind, CompareOp, ConstExpr, Declaration, Expr, ExprKind, FunctionBody,
    GenericArgKind, LiteralKind, PatternKind, UnaryOp,
};
use crate::compiler::{ParsedProject, ProjectDiagnostic};
use crate::diagnostics::{Diagnostic, Span};

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
    Path,
    Unit,
    JsonValue,
    Any,
    Unknown,
    Never,
}

/// Alias-free HIR type representation.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum HirType {
    Primitive(PrimitiveType),
    Named {
        symbol: SymbolId,
        args: Vec<HirGenericArg>,
    },
    TypeParameter {
        name: String,
    },
    AssociatedProjection {
        base: Box<HirType>,
        trait_id: SymbolId,
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
    Tuple {
        items: Vec<HirType>,
    },
    Array {
        item: Box<HirType>,
        length: HirConstArgument,
    },
    Buffer {
        length: HirConstArgument,
    },
    Option {
        item: Box<HirType>,
    },
    Result {
        ok: Box<HirType>,
        error: Box<HirType>,
    },
    Factory {
        instance: Box<HirType>,
    },
    Iterator {
        item: Box<HirType>,
    },
    Generator {
        yield_type: Box<HirType>,
        send_type: Box<HirType>,
        return_type: Box<HirType>,
    },
    Opaque {
        tag: String,
    },
}

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum HirConstType {
    U8,
    U16,
    U32,
    U64,
}

impl HirConstType {
    pub const fn name(self) -> &'static str {
        match self {
            Self::U8 => "U8",
            Self::U16 => "U16",
            Self::U32 => "U32",
            Self::U64 => "U64",
        }
    }

    fn primitive(self) -> PrimitiveType {
        match self {
            Self::U8 => PrimitiveType::U8,
            Self::U16 => PrimitiveType::U16,
            Self::U32 => PrimitiveType::U32,
            Self::U64 => PrimitiveType::U64,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum HirConstArgument {
    Value {
        value: u64,
        ty: HirConstType,
    },
    Parameter {
        name: String,
        ty: HirConstType,
    },
    Reference {
        symbol: SymbolId,
        ty: HirConstType,
    },
    Binary {
        op: HirBinaryOp,
        left: Box<HirConstArgument>,
        right: Box<HirConstArgument>,
        ty: HirConstType,
    },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum HirGenericArg {
    Type(HirType),
    Const(HirConstArgument),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum HirGenericParam {
    Type {
        span: Span,
        name: String,
        bounds: Vec<HirType>,
        source_order: usize,
    },
    Const {
        span: Span,
        name: String,
        ty: HirConstType,
        source_order: usize,
    },
}

impl HirGenericParam {
    pub fn name(&self) -> &str {
        match self {
            Self::Type { name, .. } | Self::Const { name, .. } => name,
        }
    }
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
pub struct HirMatchGuard {
    pub span: Span,
    pub scrutinee: HirExpr,
    pub pattern: HirPattern,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum HirClauseKind {
    Requires {
        guard: Option<HirMatchGuard>,
        expression: HirExpr,
    },
    Modifies {
        fields: Vec<SymbolId>,
    },
    Ensures {
        guard: Option<HirMatchGuard>,
        expression: HirExpr,
    },
    Error {
        variant: SymbolId,
        priority: Option<u32>,
        guard: Option<HirMatchGuard>,
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
pub struct HirAnnotation {
    pub span: Span,
    pub name: String,
    pub argument: Option<String>,
}
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirExternalType {
    pub id: SymbolId,
    pub span: Span,
    pub annotations: Vec<HirAnnotation>,
    pub doc: Option<HirDoc>,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirAlias {
    pub id: SymbolId,
    pub span: Span,
    pub annotations: Vec<HirAnnotation>,
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
    pub annotations: Vec<HirAnnotation>,
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
    pub annotations: Vec<HirAnnotation>,
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
    pub annotations: Vec<HirAnnotation>,
    pub doc: Option<HirDoc>,
    pub generics: Vec<HirGenericParam>,
    pub variants: Vec<HirVariant>,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirAssociatedType {
    pub id: SymbolId,
    pub span: Span,
    pub name: String,
    pub bounds: Vec<HirType>,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirAssociatedTypeAssignment {
    pub id: SymbolId,
    pub span: Span,
    pub trait_id: SymbolId,
    pub name: String,
    pub ty: HirType,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirResourceState {
    pub id: SymbolId,
    pub span: Span,
    pub name: String,
    pub terminal: bool,
    pub source_order: usize,
}
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirResourceTerminal {
    pub state: SymbolId,
    pub span: Span,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirResourceEdge {
    pub span: Span,
    pub from: SymbolId,
    pub to: SymbolId,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirResource {
    pub id: SymbolId,
    pub span: Span,
    pub annotations: Vec<HirAnnotation>,
    pub doc: Option<HirDoc>,
    pub initial: SymbolId,
    pub states: Vec<HirResourceState>,
    pub terminals: Vec<HirResourceTerminal>,
    pub edges: Vec<HirResourceEdge>,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirResourceTransition {
    pub span: Span,
    pub field: SymbolId,
    pub resource: SymbolId,
    pub from: SymbolId,
    pub to: SymbolId,
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
    pub default: Option<HirVerifiedFunction>,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirVerifiedFunction {
    pub module: ModuleId,
    pub symbol: String,
    pub verified_facade: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum HirSelectedImplementation {
    Explicit { function: HirVerifiedFunction },
    Default { function: HirVerifiedFunction },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirSelectedMethod {
    pub trait_method: SymbolId,
    pub receiver_type: HirType,
    pub selected: HirSelectedImplementation,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirTrait {
    pub id: SymbolId,
    pub span: Span,
    pub annotations: Vec<HirAnnotation>,
    pub doc: Option<HirDoc>,
    pub generics: Vec<HirGenericParam>,
    pub methods: Vec<HirMethod>,
    pub associated_types: Vec<HirAssociatedType>,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirImplInvariant {
    pub clause_id: u32,
    pub span: Span,
    pub guard: Option<HirMatchGuard>,
    pub expression: HirExpr,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirImplInitializer {
    pub span: Span,
    pub parameters: Vec<HirParameter>,
    pub doc: Option<HirDoc>,
    pub contract: HirContract,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirImplMethod {
    pub id: SymbolId,
    pub span: Span,
    pub name: String,
    pub self_span: Span,
    pub parameters: Vec<HirParameter>,
    pub return_type: HirType,
    pub doc: Option<HirDoc>,
    pub contract: HirContract,
    pub modifies: Vec<SymbolId>,
    pub transitions: Vec<HirResourceTransition>,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirImpl {
    pub id: SymbolId,
    pub span: Span,
    pub annotations: Vec<HirAnnotation>,
    pub traits: Vec<HirType>,
    pub state: Vec<HirField>,
    pub invariants: Vec<HirImplInvariant>,
    pub initializer: Option<HirImplInitializer>,
    pub methods: Vec<HirImplMethod>,
    pub associated_types: Vec<HirAssociatedTypeAssignment>,
    pub selected_methods: Vec<HirSelectedMethod>,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HirRuleClauseAction {
    Add,
    Override,
    Delete,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirRuleClause {
    pub clause_id: u32,
    pub span: Span,
    pub action: HirRuleClauseAction,
    pub kind: HirClauseKind,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirRule {
    pub id: SymbolId,
    pub span: Span,
    pub annotations: Vec<HirAnnotation>,
    pub doc: Option<HirDoc>,
    pub generics: Vec<HirGenericParam>,
    pub base: Option<SymbolId>,
    pub base_type: Option<HirType>,
    pub declared_clauses: Vec<HirRuleClause>,
    pub contract: HirContract,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirConst {
    pub id: SymbolId,
    pub span: Span,
    pub annotations: Vec<HirAnnotation>,
    pub doc: Option<HirDoc>,
    pub ty: HirType,
    pub value: HirValue,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HirCallableKind {
    Sync,
    Async,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirFunction {
    pub id: SymbolId,
    pub span: Span,
    pub annotations: Vec<HirAnnotation>,
    pub doc: Option<HirDoc>,
    pub generics: Vec<HirGenericParam>,
    pub parameters: Vec<HirParameter>,
    pub return_type: HirType,
    pub callable_kind: HirCallableKind,
    pub contract: HirContract,
    pub body: Option<HirExpr>,
    pub public: bool,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum HirDeclaration {
    ExternalType(HirExternalType),
    Alias(HirAlias),
    Newtype(HirNewtype),
    Struct(HirStruct),
    Enum(HirEnum),
    Trait(HirTrait),
    Impl(HirImpl),
    Rule(HirRule),
    Const(HirConst),
    Resource(HirResource),
    Function(HirFunction),
}

impl HirDeclaration {
    pub fn id(&self) -> &SymbolId {
        match self {
            Self::ExternalType(value) => &value.id,
            Self::Alias(value) => &value.id,
            Self::Newtype(value) => &value.id,
            Self::Struct(value) => &value.id,
            Self::Enum(value) => &value.id,
            Self::Trait(value) => &value.id,
            Self::Impl(value) => &value.id,
            Self::Rule(value) => &value.id,
            Self::Const(value) => &value.id,
            Self::Resource(value) => &value.id,
            Self::Function(value) => &value.id,
        }
    }

    pub fn span(&self) -> &Span {
        match self {
            Self::ExternalType(value) => &value.span,
            Self::Alias(value) => &value.span,
            Self::Newtype(value) => &value.span,
            Self::Struct(value) => &value.span,
            Self::Enum(value) => &value.span,
            Self::Trait(value) => &value.span,
            Self::Impl(value) => &value.span,
            Self::Rule(value) => &value.span,
            Self::Const(value) => &value.span,
            Self::Resource(value) => &value.span,
            Self::Function(value) => &value.span,
        }
    }

    pub fn public(&self) -> bool {
        match self {
            Self::ExternalType(value) => value.public,
            Self::Alias(value) => value.public,
            Self::Newtype(value) => value.public,
            Self::Struct(value) => value.public,
            Self::Enum(value) => value.public,
            Self::Trait(value) => value.public,
            Self::Impl(value) => value.public,
            Self::Rule(value) => value.public,
            Self::Const(value) => value.public,
            Self::Resource(value) => value.public,
            Self::Function(value) => value.public,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirModule {
    pub source: PathBuf,
    pub source_bytes: Arc<[u8]>,
    pub id: ModuleId,
    pub imports: Vec<HirImport>,
    pub declarations: Vec<HirDeclaration>,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HirProject {
    pub modules: Vec<HirModule>,
}

impl HirProject {
    pub fn new(modules: Vec<HirModule>) -> Self {
        Self { modules }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum HirReference {
    Parameter(SymbolId),
    Binding(SymbolId),
    Constant(SymbolId),
    EnumSingleton(SymbolId),
    Field(SymbolId),
    OldStateField(SymbolId),
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
    ResultRef,
    ConstantRef(SymbolId),
    EnumSingletonRef(SymbolId),
    OldStateField {
        field: SymbolId,
    },
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
    Tuple(Vec<HirValue>),
    Array(Vec<HirValue>),
    Buffer(Vec<u8>),
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
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum OwnedDeclKind {
    Alias,
    Type { generics: usize },
    Enum { generics: usize },
    Const,
    Function,
    Trait { generics: usize },
    Impl,
    Rule { generics: usize },
    Resource,
}

struct OwnedLower<'a> {
    parsed: &'a ParsedProject,
    modules: Vec<ModuleId>,
    declarations: HashMap<SymbolId, OwnedDeclKind>,
    imports: Vec<HashMap<String, SymbolId>>,
    errors: Vec<ProjectDiagnostic>,
    resolving_aliases: HashSet<SymbolId>,
    constant_values: HashMap<SymbolId, HirValue>,
    resolving_constants: HashSet<SymbolId>,
    lowered_rules: HashMap<SymbolId, HirRule>,
    default_functions: HashMap<SymbolId, Option<HirVerifiedFunction>>,
}

#[derive(Default)]
struct GenericScope {
    types: HashSet<String>,
    type_bounds: HashMap<String, Vec<ast::Type>>,
    consts: HashMap<String, HirConstType>,
}

impl GenericScope {
    fn from_params(
        lower: &mut OwnedLower<'_>,
        module: usize,
        values: &[ast::GenericParam],
    ) -> Self {
        let mut names = HashSet::new();
        for value in values {
            let (span, name) = match value {
                ast::GenericParam::Type { span, name, .. }
                | ast::GenericParam::Const { span, name, .. } => (span, name),
            };
            if !names.insert(name.clone()) {
                lower.error(
                    module,
                    span.clone(),
                    format!("duplicate generic parameter `{name}`"),
                );
            }
        }
        Self::from_declared(values)
    }

    fn from_declared(values: &[ast::GenericParam]) -> Self {
        let mut scope = Self::default();
        for value in values {
            match value {
                ast::GenericParam::Type { name, bounds, .. } => {
                    scope.types.insert(name.clone());
                    scope.type_bounds.insert(name.clone(), bounds.clone());
                }
                ast::GenericParam::Const { name, ty, .. } => {
                    scope.consts.insert(
                        name.clone(),
                        match ty {
                            ast::ConstKind::U8 => HirConstType::U8,
                            ast::ConstKind::U16 => HirConstType::U16,
                            ast::ConstKind::U32 => HirConstType::U32,
                            ast::ConstKind::U64 => HirConstType::U64,
                        },
                    );
                }
            }
        }
        scope
    }
}

impl<'a> OwnedLower<'a> {
    fn new(parsed: &'a ParsedProject) -> Self {
        let modules = parsed
            .sources
            .iter()
            .map(|source| ModuleId::new(source.syntax.module.path.segments.clone()))
            .collect::<Vec<_>>();
        let mut declarations = HashMap::new();
        for (index, source) in parsed.sources.iter().enumerate() {
            for declaration in &source.syntax.declarations {
                let (name, kind) = match declaration {
                    Declaration::ExternalType(v) => (&v.name, OwnedDeclKind::Type { generics: 0 }),
                    Declaration::Alias(v) => (&v.name, OwnedDeclKind::Alias),
                    Declaration::Newtype(v) => (&v.name, OwnedDeclKind::Type { generics: 0 }),
                    Declaration::Struct(v) => (
                        &v.name,
                        OwnedDeclKind::Type {
                            generics: v.generics.len(),
                        },
                    ),
                    Declaration::Enum(v) => (
                        &v.name,
                        OwnedDeclKind::Enum {
                            generics: v.generics.len(),
                        },
                    ),
                    Declaration::Trait(v) => (
                        &v.name,
                        OwnedDeclKind::Trait {
                            generics: v.generics.len(),
                        },
                    ),
                    Declaration::Impl(v) => (&v.name, OwnedDeclKind::Impl),
                    Declaration::Const(v) => (&v.name, OwnedDeclKind::Const),
                    Declaration::Rule(v) => (
                        &v.name,
                        OwnedDeclKind::Rule {
                            generics: v.generics.len(),
                        },
                    ),
                    Declaration::Resource(v) => (&v.name, OwnedDeclKind::Resource),
                    Declaration::Function(v) => (&v.name, OwnedDeclKind::Function),
                };
                declarations.insert(SymbolId::new(modules[index].clone(), name.clone()), kind);
            }
        }
        let mut out = Self {
            parsed,
            modules,
            declarations,
            imports: vec![HashMap::new(); parsed.sources.len()],
            errors: Vec::new(),
            constant_values: HashMap::new(),
            resolving_constants: HashSet::new(),
            resolving_aliases: HashSet::new(),
            lowered_rules: HashMap::new(),
            default_functions: HashMap::new(),
        };
        for index in 0..out.parsed.sources.len() {
            let uses = out.parsed.sources[index].syntax.uses.clone();
            for use_decl in uses {
                let (module, names) = match &use_decl.names {
                    Some(names) => (use_decl.path.segments.clone(), names.clone()),
                    None if use_decl.path.segments.len() >= 2 => (
                        use_decl.path.segments[..use_decl.path.segments.len() - 1].to_vec(),
                        vec![use_decl.path.segments.last().cloned().unwrap_or_default()],
                    ),
                    None => continue,
                };
                for name in names {
                    let target = SymbolId::new(ModuleId::new(module.clone()), name.clone());
                    if out.declarations.contains_key(&target) {
                        out.imports[index].insert(name, target);
                    }
                }
            }
        }
        out
    }

    fn error(&mut self, module: usize, span: Span, message: impl Into<String>) {
        self.errors.push(ProjectDiagnostic {
            path: self.parsed.sources[module].path.clone(),
            diagnostic: Diagnostic::new(message, span),
        });
    }

    fn lookup(&self, module: usize, path: &ast::QualifiedName) -> Option<SymbolId> {
        let name = path.segments.last()?.clone();
        if path.segments.len() == 1 {
            self.imports[module].get(&name).cloned().or_else(|| {
                let candidate = SymbolId::new(self.modules[module].clone(), name);
                self.declarations
                    .contains_key(&candidate)
                    .then_some(candidate)
            })
        } else {
            let candidate = SymbolId::new(
                ModuleId::new(path.segments[..path.segments.len() - 1].to_vec()),
                name,
            );
            self.declarations
                .contains_key(&candidate)
                .then_some(candidate)
        }
    }

    fn resolve(
        &mut self,
        module: usize,
        path: &ast::QualifiedName,
        span: &Span,
    ) -> Option<SymbolId> {
        let symbol = self.lookup(module, path);
        if symbol.is_none() {
            self.error(
                module,
                span.clone(),
                format!("unknown type or declaration `{}`", path.segments.join(".")),
            );
        }
        symbol
    }

    fn arity(&mut self, module: usize, value: &ast::Type, expected: usize, name: &str) {
        if value.arguments.len() != expected {
            self.error(
                module,
                value.span.clone(),
                format!(
                    "type constructor `{name}` expects {expected} argument(s), got {}",
                    value.arguments.len()
                ),
            );
        }
    }
    fn newtype_carrier(&mut self, symbol: &SymbolId) -> Option<HirType> {
        let source_index = self
            .modules
            .iter()
            .position(|module| module == &symbol.module)?;
        let underlying = self.parsed.sources[source_index]
            .syntax
            .declarations
            .iter()
            .find_map(|declaration| match declaration {
                Declaration::Newtype(value) if value.name == symbol.name => {
                    Some(value.underlying.clone())
                }
                _ => None,
            })?;
        Some(self.ty(source_index, &underlying, &GenericScope::default()))
    }

    fn expression_compat_type(&mut self, ty: &HirType) -> HirType {
        fn resolve(
            lower: &mut OwnedLower<'_>,
            ty: &HirType,
            seen: &mut HashSet<SymbolId>,
        ) -> HirType {
            match ty {
                HirType::Named { symbol, args }
                    if lower.declarations.get(symbol)
                        == Some(&OwnedDeclKind::Type { generics: 0 })
                        && seen.insert(symbol.clone()) =>
                {
                    if let Some(carrier) = lower.newtype_carrier(symbol) {
                        let resolved = resolve(lower, &carrier, seen);
                        seen.remove(symbol);
                        return resolved;
                    }
                    HirType::Named {
                        symbol: symbol.clone(),
                        args: args
                            .iter()
                            .map(|arg| match arg {
                                HirGenericArg::Type(arg) => {
                                    HirGenericArg::Type(resolve(lower, arg, seen))
                                }
                                HirGenericArg::Const(arg) => HirGenericArg::Const(arg.clone()),
                            })
                            .collect(),
                    }
                }
                HirType::Named { symbol, args } => HirType::Named {
                    symbol: symbol.clone(),
                    args: args
                        .iter()
                        .map(|arg| match arg {
                            HirGenericArg::Type(arg) => {
                                HirGenericArg::Type(resolve(lower, arg, seen))
                            }
                            HirGenericArg::Const(arg) => HirGenericArg::Const(arg.clone()),
                        })
                        .collect(),
                },
                HirType::List { item } => HirType::List {
                    item: Box::new(resolve(lower, item, seen)),
                },
                HirType::Set { item } => HirType::Set {
                    item: Box::new(resolve(lower, item, seen)),
                },
                HirType::Map { key, value } => HirType::Map {
                    key: Box::new(resolve(lower, key, seen)),
                    value: Box::new(resolve(lower, value, seen)),
                },
                HirType::Tuple { items } => HirType::Tuple {
                    items: items
                        .iter()
                        .map(|item| resolve(lower, item, seen))
                        .collect(),
                },
                HirType::Array { item, length } => HirType::Array {
                    item: Box::new(resolve(lower, item, seen)),
                    length: length.clone(),
                },
                HirType::Buffer { length } => HirType::Buffer {
                    length: length.clone(),
                },
                HirType::Option { item } => HirType::Option {
                    item: Box::new(resolve(lower, item, seen)),
                },
                HirType::Iterator { item } => HirType::Iterator {
                    item: Box::new(resolve(lower, item, seen)),
                },
                HirType::Generator {
                    yield_type,
                    send_type,
                    return_type,
                } => HirType::Generator {
                    yield_type: Box::new(resolve(lower, yield_type, seen)),
                    send_type: Box::new(resolve(lower, send_type, seen)),
                    return_type: Box::new(resolve(lower, return_type, seen)),
                },
                HirType::Result { ok, error } => HirType::Result {
                    ok: Box::new(resolve(lower, ok, seen)),
                    error: Box::new(resolve(lower, error, seen)),
                },
                HirType::Factory { instance } => HirType::Factory {
                    instance: Box::new(resolve(lower, instance, seen)),
                },
                _ => ty.clone(),
            }
        }

        resolve(self, ty, &mut HashSet::new())
    }

    fn transparent_expression(&mut self, mut expression: HirExpr) -> HirExpr {
        loop {
            let HirType::Named { symbol, .. } = &expression.ty else {
                return expression;
            };
            if self.newtype_carrier(symbol).is_none()
                || !matches!(
                    &expression.kind,
                    HirExprKind::ParameterRef(_)
                        | HirExprKind::BindingRef(_)
                        | HirExprKind::SelfRef
                        | HirExprKind::ConstantRef(_)
                        | HirExprKind::Field { .. }
                )
            {
                return expression;
            }
            let carrier = self.newtype_carrier(symbol).unwrap();
            expression = HirExpr {
                span: expression.span.clone(),
                ty: carrier,
                reference: None,
                kind: HirExprKind::Field {
                    base: Box::new(expression),
                    name: "value".to_owned(),
                },
            };
        }
    }
}

impl<'a> OwnedLower<'a> {
    fn alias_target(&self, symbol: &SymbolId) -> Option<(usize, ast::Type)> {
        let index = self
            .modules
            .iter()
            .position(|module| module == &symbol.module)?;
        self.parsed.sources[index]
            .syntax
            .declarations
            .iter()
            .find_map(|declaration| match declaration {
                Declaration::Alias(value) if value.name == symbol.name => {
                    Some((index, value.target.clone()))
                }
                _ => None,
            })
    }

    fn constant_type(&mut self, symbol: &SymbolId) -> Option<HirType> {
        let index = self
            .modules
            .iter()
            .position(|module| module == &symbol.module)?;
        let ty = self.parsed.sources[index]
            .syntax
            .declarations
            .iter()
            .find_map(|declaration| match declaration {
                Declaration::Const(value) if value.name == symbol.name => Some(value.ty.clone()),
                _ => None,
            })?;
        Some(self.ty(index, &ty, &GenericScope::default()))
    }

    fn enum_variant(
        &self,
        module: usize,
        path: &ast::QualifiedName,
    ) -> Option<(SymbolId, HirType)> {
        if path.segments.len() < 2 {
            return None;
        }
        let enum_path = ast::QualifiedName::new(
            path.span.clone(),
            path.segments[..path.segments.len() - 1].to_vec(),
        );
        let enum_symbol = self.lookup(module, &enum_path)?;
        if !matches!(
            self.declarations.get(&enum_symbol),
            Some(OwnedDeclKind::Enum { .. })
        ) {
            return None;
        }
        let index = self
            .modules
            .iter()
            .position(|candidate| candidate == &enum_symbol.module)?;
        let variant = path.segments.last()?;
        let exists = self.parsed.sources[index]
            .syntax
            .declarations
            .iter()
            .any(|declaration| {
                matches!(
                    declaration,
                    Declaration::Enum(value)
                        if value.name == enum_symbol.name
                            && value.variants.iter().any(|item| &item.name == variant)
                )
            });
        exists.then(|| {
            (
                SymbolId::new(
                    enum_symbol.module.clone(),
                    format!("{}.{}", enum_symbol.name, variant),
                ),
                HirType::Named {
                    symbol: enum_symbol,
                    args: Vec::new(),
                },
            )
        })
    }
    fn declaration_generics(&self, symbol: &SymbolId) -> Vec<ast::GenericParam> {
        self.modules
            .iter()
            .position(|module| module == &symbol.module)
            .and_then(|module| {
                self.parsed.sources[module]
                    .syntax
                    .declarations
                    .iter()
                    .find_map(|declaration| match declaration {
                        Declaration::Struct(value) if value.name == symbol.name => {
                            Some(value.generics.clone())
                        }
                        Declaration::Enum(value) if value.name == symbol.name => {
                            Some(value.generics.clone())
                        }
                        Declaration::Trait(value) if value.name == symbol.name => {
                            Some(value.generics.clone())
                        }
                        Declaration::Rule(value) if value.name == symbol.name => {
                            Some(value.generics.clone())
                        }
                        _ => None,
                    })
            })
            .unwrap_or_default()
    }

    fn is_known_type_argument(
        &self,
        module: usize,
        value: &ast::Type,
        generics: &GenericScope,
    ) -> bool {
        if value.path.segments.len() == 1
            && (generics.types.contains(&value.path.segments[0])
                || owned_primitive(&value.path.segments[0]).is_some())
        {
            return true;
        }
        self.lookup(module, &value.path).is_some_and(|symbol| {
            matches!(
                self.declarations.get(&symbol),
                Some(
                    OwnedDeclKind::Alias
                        | OwnedDeclKind::Type { .. }
                        | OwnedDeclKind::Enum { .. }
                        | OwnedDeclKind::Trait { .. }
                        | OwnedDeclKind::Rule { .. }
                        | OwnedDeclKind::Resource
                )
            )
        })
    }

    fn type_argument(
        &mut self,
        module: usize,
        argument: &ast::GenericArg,
        generics: &GenericScope,
    ) -> HirType {
        match &argument.kind {
            GenericArgKind::Type(value) | GenericArgKind::Ambiguous { ty: value, .. } => {
                self.ty(module, value, generics)
            }
            _ => {
                self.error(
                    module,
                    argument.span.clone(),
                    "type argument must be a type",
                );
                HirType::Primitive(PrimitiveType::Unknown)
            }
        }
    }

    fn const_argument(
        &mut self,
        module: usize,
        value: &ConstExpr,
        generics: &GenericScope,
        expected: Option<HirConstType>,
    ) -> Option<HirConstArgument> {
        let ty = expected.unwrap_or(HirConstType::U64);
        if let ConstExpr::Expression(expression) = value
            && self.is_symbolic_const_expression(module, expression, generics)
        {
            return self.symbolic_const_argument(module, expression, generics, expected);
        }

        let span = value.span().clone();
        let evaluated = self.value(module, value, &HirType::Primitive(ty.primitive()))?;
        let HirValue::Integer(text) = evaluated else {
            self.error(
                module,
                span,
                "const argument must evaluate to an unsigned integer",
            );
            return None;
        };
        let Ok(value) = text.parse::<u64>() else {
            self.error(
                module,
                span,
                "const argument must evaluate to an unsigned integer",
            );
            return None;
        };
        let in_range = match ty {
            HirConstType::U8 => u8::try_from(value).is_ok(),
            HirConstType::U16 => u16::try_from(value).is_ok(),
            HirConstType::U32 => u32::try_from(value).is_ok(),
            HirConstType::U64 => true,
        };
        if !in_range {
            self.error(
                module,
                span,
                format!("const argument is out of range for {}", ty.name()),
            );
            return None;
        }
        Some(HirConstArgument::Value { value, ty })
    }

    fn is_symbolic_const_expression(
        &self,
        module: usize,
        expression: &Expr,
        generics: &GenericScope,
    ) -> bool {
        match &expression.kind {
            ExprKind::Name(path) => {
                (path.segments.len() == 1 && generics.consts.contains_key(&path.segments[0]))
                    || self.lookup(module, path).is_some_and(|symbol| {
                        self.declarations.get(&symbol) == Some(&OwnedDeclKind::Const)
                    })
            }
            ExprKind::Parenthesized(value) => {
                self.is_symbolic_const_expression(module, value, generics)
            }
            ExprKind::Binary { .. } => true,
            _ => false,
        }
    }
    fn const_expression_domain(
        &mut self,
        module: usize,
        expression: &Expr,
        generics: &GenericScope,
    ) -> Option<HirConstType> {
        match &expression.kind {
            ExprKind::Name(path) if path.segments.len() == 1 => {
                generics.consts.get(&path.segments[0]).copied().or_else(|| {
                    self.lookup(module, path).and_then(|symbol| {
                        (self.declarations.get(&symbol) == Some(&OwnedDeclKind::Const))
                            .then(|| self.constant_type(&symbol))
                            .flatten()
                            .and_then(|ty| match ty {
                                HirType::Primitive(PrimitiveType::U8) => Some(HirConstType::U8),
                                HirType::Primitive(PrimitiveType::U16) => Some(HirConstType::U16),
                                HirType::Primitive(PrimitiveType::U32) => Some(HirConstType::U32),
                                HirType::Primitive(PrimitiveType::U64) => Some(HirConstType::U64),
                                _ => None,
                            })
                    })
                })
            }
            ExprKind::Name(path) => self.lookup(module, path).and_then(|symbol| {
                (self.declarations.get(&symbol) == Some(&OwnedDeclKind::Const))
                    .then(|| self.constant_type(&symbol))
                    .flatten()
                    .and_then(|ty| match ty {
                        HirType::Primitive(PrimitiveType::U8) => Some(HirConstType::U8),
                        HirType::Primitive(PrimitiveType::U16) => Some(HirConstType::U16),
                        HirType::Primitive(PrimitiveType::U32) => Some(HirConstType::U32),
                        HirType::Primitive(PrimitiveType::U64) => Some(HirConstType::U64),
                        _ => None,
                    })
            }),
            ExprKind::Parenthesized(value) => self.const_expression_domain(module, value, generics),
            ExprKind::Binary { left, right, .. } => self
                .const_expression_domain(module, left, generics)
                .or_else(|| self.const_expression_domain(module, right, generics)),
            _ => None,
        }
    }

    fn symbolic_const_argument(
        &mut self,
        module: usize,
        expression: &Expr,
        generics: &GenericScope,
        expected: Option<HirConstType>,
    ) -> Option<HirConstArgument> {
        match &expression.kind {
            ExprKind::Name(path) => {
                if path.segments.len() == 1
                    && let Some(ty) = generics.consts.get(&path.segments[0]).copied()
                {
                    if expected.is_some_and(|expected| expected != ty) {
                        self.error(
                            module,
                            path.span.clone(),
                            format!(
                                "const argument `{}` must have domain {}",
                                path.segments[0],
                                expected.unwrap().name()
                            ),
                        );
                        return None;
                    }
                    return Some(HirConstArgument::Parameter {
                        name: path.segments[0].clone(),
                        ty,
                    });
                }
                let Some(symbol) = self.lookup(module, path) else {
                    self.error(module, path.span.clone(), "unknown constant reference");
                    return None;
                };
                if self.declarations.get(&symbol) != Some(&OwnedDeclKind::Const) {
                    self.error(
                        module,
                        path.span.clone(),
                        "const argument must be a constant",
                    );
                    return None;
                }
                let Some(HirType::Primitive(actual)) = self.constant_type(&symbol) else {
                    self.error(
                        module,
                        path.span.clone(),
                        "const argument must have an unsigned integer type",
                    );
                    return None;
                };
                let actual = match actual {
                    PrimitiveType::U8 => HirConstType::U8,
                    PrimitiveType::U16 => HirConstType::U16,
                    PrimitiveType::U32 => HirConstType::U32,
                    PrimitiveType::U64 => HirConstType::U64,
                    _ => {
                        self.error(
                            module,
                            path.span.clone(),
                            "const argument must have an unsigned integer type",
                        );
                        return None;
                    }
                };
                if expected.is_some_and(|expected| expected != actual) {
                    self.error(
                        module,
                        path.span.clone(),
                        format!(
                            "const argument must have domain {}",
                            expected.unwrap().name()
                        ),
                    );
                    return None;
                }
                Some(HirConstArgument::Reference { symbol, ty: actual })
            }
            ExprKind::Parenthesized(value) => {
                self.symbolic_const_argument(module, value, generics, expected)
            }
            ExprKind::Binary { left, op, right } => {
                let op = match op {
                    BinaryOp::Add => HirBinaryOp::Add,
                    BinaryOp::Subtract => HirBinaryOp::Subtract,
                    BinaryOp::Multiply => HirBinaryOp::Multiply,
                    BinaryOp::Divide => HirBinaryOp::Divide,
                    BinaryOp::Remainder => HirBinaryOp::Remainder,
                    _ => {
                        self.error(
                            module,
                            expression.span.clone(),
                            "const expressions only support arithmetic",
                        );
                        return None;
                    }
                };
                let expected = expected.or_else(|| {
                    self.const_expression_domain(module, left, generics)
                        .or_else(|| self.const_expression_domain(module, right, generics))
                });
                let left = if self.is_symbolic_const_expression(module, left, generics) {
                    self.symbolic_const_argument(module, left, generics, expected)
                } else {
                    self.const_argument(
                        module,
                        &ConstExpr::Expression((**left).clone()),
                        generics,
                        expected,
                    )
                }?;
                let right = if self.is_symbolic_const_expression(module, right, generics) {
                    self.symbolic_const_argument(module, right, generics, expected)
                } else {
                    self.const_argument(
                        module,
                        &ConstExpr::Expression((**right).clone()),
                        generics,
                        expected,
                    )
                }?;
                let ty = expected.unwrap_or_else(|| const_argument_type(&left));
                if const_argument_type(&right) != ty {
                    self.error(
                        module,
                        expression.span.clone(),
                        "const arithmetic operands must have the same unsigned domain",
                    );
                    return None;
                }
                Some(HirConstArgument::Binary {
                    op,
                    left: Box::new(left),
                    right: Box::new(right),
                    ty,
                })
            }
            _ => self.const_argument(
                module,
                &ConstExpr::Expression(expression.clone()),
                generics,
                expected,
            ),
        }
    }
    fn associated_projection(
        &mut self,
        module: usize,
        value: &ast::Type,
        generics: &GenericScope,
    ) -> Option<HirType> {
        let (name, base_segments) = value.path.segments.split_last()?;
        if base_segments.is_empty() {
            return None;
        }
        let base_path = ast::QualifiedName::new(value.path.span.clone(), base_segments.to_vec());
        let base = if base_segments.len() == 1 && generics.types.contains(&base_segments[0]) {
            HirType::TypeParameter {
                name: base_segments[0].clone(),
            }
        } else if self.lookup(module, &base_path).is_some() {
            self.ty(
                module,
                &ast::Type {
                    span: value.span.clone(),
                    path: base_path,
                    arguments: Vec::new(),
                },
                generics,
            )
        } else {
            return None;
        };
        let trait_ids = match &base {
            HirType::TypeParameter { name } => generics
                .type_bounds
                .get(name)
                .into_iter()
                .flatten()
                .filter_map(|bound| {
                    let HirType::Named { symbol, .. } = self.ty(module, bound, generics) else {
                        return None;
                    };
                    (self.declarations.get(&symbol) == Some(&OwnedDeclKind::Trait { generics: 0 })
                        || matches!(
                            self.declarations.get(&symbol),
                            Some(OwnedDeclKind::Trait { .. })
                        ))
                    .then_some(symbol)
                })
                .collect::<BTreeSet<_>>(),
            HirType::Named { symbol, .. }
                if matches!(
                    self.declarations.get(symbol),
                    Some(OwnedDeclKind::Trait { .. })
                ) =>
            {
                BTreeSet::from([symbol.clone()])
            }
            HirType::Named { symbol, .. }
                if self.declarations.get(symbol) == Some(&OwnedDeclKind::Impl) =>
            {
                self.declaration_traits(symbol)
                    .into_iter()
                    .filter_map(|ty| match ty {
                        HirType::Named { symbol, .. }
                            if matches!(
                                self.declarations.get(&symbol),
                                Some(OwnedDeclKind::Trait { .. })
                            ) =>
                        {
                            Some(symbol)
                        }
                        _ => None,
                    })
                    .collect()
            }
            _ => BTreeSet::new(),
        };
        let mut candidates = trait_ids
            .into_iter()
            .filter(|trait_id| self.trait_associated_type(trait_id, name))
            .collect::<Vec<_>>();
        if candidates.len() != 1 {
            self.error(
                module,
                value.span.clone(),
                if candidates.is_empty() {
                    format!(
                        "associated projection `{}` is not declared by its trait bounds",
                        value.path.segments.join(".")
                    )
                } else {
                    format!(
                        "associated projection `{}` is ambiguous",
                        value.path.segments.join(".")
                    )
                },
            );
            return Some(HirType::Primitive(PrimitiveType::Unknown));
        }
        Some(HirType::AssociatedProjection {
            base: Box::new(base),
            trait_id: candidates.pop().unwrap(),
            name: name.clone(),
        })
    }

    fn trait_associated_type(&self, trait_id: &SymbolId, name: &str) -> bool {
        self.modules
            .iter()
            .position(|module| module == &trait_id.module)
            .is_some_and(|module| {
                self.parsed.sources[module]
                    .syntax
                    .declarations
                    .iter()
                    .any(|declaration| {
                        matches!(
                            declaration,
                            Declaration::Trait(value)
                                if value.name == trait_id.name
                                    && value.associated_types.iter().any(|item| item.name == name)
                        )
                    })
            })
    }

    fn declaration_traits(&mut self, symbol: &SymbolId) -> Vec<HirType> {
        let Some(module) = self
            .modules
            .iter()
            .position(|module| module == &symbol.module)
        else {
            return Vec::new();
        };
        self.parsed.sources[module]
            .syntax
            .declarations
            .iter()
            .find_map(|declaration| match declaration {
                Declaration::Impl(value) if value.name == symbol.name => Some(
                    value
                        .traits
                        .iter()
                        .map(|trait_ref| self.ty(module, trait_ref, &GenericScope::default()))
                        .collect(),
                ),
                _ => None,
            })
            .unwrap_or_default()
    }

    fn ty(&mut self, module: usize, value: &ast::Type, generics: &GenericScope) -> HirType {
        if value.arguments.is_empty()
            && let Some(projection) = self.associated_projection(module, value, generics)
        {
            return projection;
        }
        let name = value.path.segments.last().cloned().unwrap_or_default();
        if value.path.segments.len() == 1 {
            if generics.types.contains(&name) {
                self.arity(module, value, 0, &name);
                return HirType::TypeParameter { name };
            }
            if let Some(primitive) = owned_primitive(&name) {
                self.arity(module, value, 0, &name);
                return HirType::Primitive(primitive);
            }
            if name == "Opaque" {
                self.arity(module, value, 1, &name);
                let tag = value
                    .arguments
                    .first()
                    .and_then(|argument| match &argument.kind {
                        GenericArgKind::Const(ConstExpr::Expression(Expr {
                            kind:
                                ExprKind::Literal(ast::Literal {
                                    kind: LiteralKind::String(tag),
                                    ..
                                }),
                            ..
                        })) => Some(tag.as_str()),
                        _ => None,
                    });
                return match tag {
                    Some(tag) if valid_opaque_tag(tag) => HirType::Opaque {
                        tag: tag.to_owned(),
                    },
                    Some(_) => {
                        self.error(
                            module,
                            value.span.clone(),
                            "Opaque tag must match [a-z][a-z0-9._-]{0,63}",
                        );
                        HirType::Opaque {
                            tag: "invalid".into(),
                        }
                    }
                    None => {
                        self.error(
                            module,
                            value.span.clone(),
                            "Opaque expects one string literal argument",
                        );
                        HirType::Opaque {
                            tag: "invalid".into(),
                        }
                    }
                };
            }

            let type_at = |lower: &mut Self, index: usize| {
                value
                    .arguments
                    .get(index)
                    .map(|argument| lower.type_argument(module, argument, generics))
                    .unwrap_or(HirType::Primitive(PrimitiveType::Unknown))
            };
            match name.as_str() {
                "Factory" => {
                    self.arity(module, value, 1, &name);
                    let instance = type_at(self, 0);
                    if value.arguments.len() == 1
                        && !matches!(
                            &instance,
                            HirType::Named { symbol, args }
                                if args.is_empty()
                                    && self.declarations.get(symbol) == Some(&OwnedDeclKind::Impl)
                        )
                    {
                        self.error(
                            module,
                            value.span.clone(),
                            "Factory instance type must resolve to an impl declaration without type arguments",
                        );
                    }
                    return HirType::Factory {
                        instance: Box::new(instance),
                    };
                }
                "List" | "Set" | "Option" | "Iterator" => {
                    self.arity(module, value, 1, &name);
                    let item = Box::new(type_at(self, 0));
                    return match name.as_str() {
                        "List" => HirType::List { item },
                        "Set" => HirType::Set { item },
                        "Option" => HirType::Option { item },
                        "Iterator" => HirType::Iterator { item },
                        _ => unreachable!(),
                    };
                }
                "Map" | "Result" => {
                    self.arity(module, value, 2, &name);
                    let first = type_at(self, 0);
                    let second = type_at(self, 1);
                    if name == "Result"
                        && !matches!(&second, HirType::Named { symbol, .. } if matches!(self.declarations.get(symbol), Some(OwnedDeclKind::Enum { .. })))
                    {
                        self.error(
                            module,
                            value.span.clone(),
                            "Result error type must resolve to an enum declaration",
                        );
                    }
                    return if name == "Map" {
                        HirType::Map {
                            key: Box::new(first),
                            value: Box::new(second),
                        }
                    } else {
                        HirType::Result {
                            ok: Box::new(first),
                            error: Box::new(second),
                        }
                    };
                }
                "Tuple" => {
                    if value.arguments.is_empty() {
                        self.error(
                            module,
                            value.span.clone(),
                            "Tuple requires at least one type argument",
                        );
                    }
                    return HirType::Tuple {
                        items: value
                            .arguments
                            .iter()
                            .map(|argument| self.type_argument(module, argument, generics))
                            .collect(),
                    };
                }
                "Array" => {
                    self.arity(module, value, 2, &name);
                    let item = type_at(self, 0);
                    let length = value
                        .arguments
                        .get(1)
                        .and_then(|argument| match &argument.kind {
                            GenericArgKind::Const(value) => {
                                self.const_argument(module, value, generics, None)
                            }
                            _ => {
                                self.error(
                                    module,
                                    argument.span.clone(),
                                    "Array length must be a const argument",
                                );
                                None
                            }
                        })
                        .unwrap_or(HirConstArgument::Value {
                            value: 0,
                            ty: HirConstType::U64,
                        });
                    return HirType::Array {
                        item: Box::new(item),
                        length,
                    };
                }
                "Buffer" => {
                    self.arity(module, value, 1, &name);
                    let length = value
                        .arguments
                        .first()
                        .and_then(|argument| match &argument.kind {
                            GenericArgKind::Const(value) => {
                                self.const_argument(module, value, generics, None)
                            }
                            _ => {
                                self.error(
                                    module,
                                    argument.span.clone(),
                                    "Buffer length must be a const argument",
                                );
                                None
                            }
                        })
                        .unwrap_or(HirConstArgument::Value {
                            value: 0,
                            ty: HirConstType::U64,
                        });
                    return HirType::Buffer { length };
                }
                "Generator" => {
                    self.arity(module, value, 3, &name);
                    return HirType::Generator {
                        yield_type: Box::new(type_at(self, 0)),
                        send_type: Box::new(type_at(self, 1)),
                        return_type: Box::new(type_at(self, 2)),
                    };
                }
                _ => {}
            }
        }

        let Some(symbol) = self.resolve(module, &value.path, &value.span) else {
            return HirType::Primitive(PrimitiveType::Unknown);
        };
        if self.declarations.get(&symbol) == Some(&OwnedDeclKind::Alias) {
            self.arity(module, value, 0, &symbol.as_string());
            if !self.resolving_aliases.insert(symbol.clone()) {
                return HirType::Opaque {
                    tag: "alias-cycle".into(),
                };
            }
            let resolved = self
                .alias_target(&symbol)
                .map(|(alias_module, target)| self.ty(alias_module, &target, generics))
                .unwrap_or_else(|| HirType::Opaque {
                    tag: "invalid-alias".into(),
                });
            self.resolving_aliases.remove(&symbol);
            return resolved;
        }

        let parameters = self.declaration_generics(&symbol);
        self.arity(module, value, parameters.len(), &symbol.as_string());
        let mut args = Vec::new();
        for (parameter, argument) in parameters.iter().zip(&value.arguments) {
            match (parameter, &argument.kind) {
                (ast::GenericParam::Type { .. }, GenericArgKind::Type(value))
                | (ast::GenericParam::Type { .. }, GenericArgKind::Ambiguous { ty: value, .. }) => {
                    args.push(HirGenericArg::Type(self.ty(module, value, generics)));
                }
                (ast::GenericParam::Const { ty, .. }, GenericArgKind::Const(value)) => {
                    let ty = match ty {
                        ast::ConstKind::U8 => HirConstType::U8,
                        ast::ConstKind::U16 => HirConstType::U16,
                        ast::ConstKind::U32 => HirConstType::U32,
                        ast::ConstKind::U64 => HirConstType::U64,
                    };
                    let value = self
                        .const_argument(module, value, generics, Some(ty))
                        .unwrap_or(HirConstArgument::Value { value: 0, ty });
                    args.push(HirGenericArg::Const(value));
                }
                (
                    ast::GenericParam::Const { ty, .. },
                    GenericArgKind::Ambiguous {
                        ty: candidate,
                        value,
                    },
                ) => {
                    let ty = match ty {
                        ast::ConstKind::U8 => HirConstType::U8,
                        ast::ConstKind::U16 => HirConstType::U16,
                        ast::ConstKind::U32 => HirConstType::U32,
                        ast::ConstKind::U64 => HirConstType::U64,
                    };
                    if self.is_known_type_argument(module, candidate, generics) {
                        self.error(
                            module,
                            argument.span.clone(),
                            "generic argument kind must match its const parameter",
                        );
                        args.push(HirGenericArg::Const(HirConstArgument::Value {
                            value: 0,
                            ty,
                        }));
                    } else {
                        let value = self
                            .const_argument(module, value, generics, Some(ty))
                            .unwrap_or(HirConstArgument::Value { value: 0, ty });
                        args.push(HirGenericArg::Const(value));
                    }
                }
                (ast::GenericParam::Type { .. }, _) => {
                    self.error(
                        module,
                        argument.span.clone(),
                        "generic argument kind must match its type parameter",
                    );
                    args.push(HirGenericArg::Type(HirType::Primitive(
                        PrimitiveType::Unknown,
                    )));
                }
                (ast::GenericParam::Const { ty, .. }, _) => {
                    let ty = match ty {
                        ast::ConstKind::U8 => HirConstType::U8,
                        ast::ConstKind::U16 => HirConstType::U16,
                        ast::ConstKind::U32 => HirConstType::U32,
                        ast::ConstKind::U64 => HirConstType::U64,
                    };
                    self.error(
                        module,
                        argument.span.clone(),
                        "generic argument kind must match its const parameter",
                    );
                    args.push(HirGenericArg::Const(HirConstArgument::Value {
                        value: 0,
                        ty,
                    }));
                }
            }
        }
        HirType::Named { symbol, args }
    }

    fn generics(&mut self, module: usize, values: &[ast::GenericParam]) -> Vec<HirGenericParam> {
        let scope = GenericScope::from_params(self, module, values);
        values
            .iter()
            .enumerate()
            .map(|(source_order, value)| match value {
                ast::GenericParam::Type { span, name, bounds } => HirGenericParam::Type {
                    span: span.clone(),
                    name: name.clone(),
                    bounds: bounds
                        .iter()
                        .map(|bound| self.ty(module, bound, &scope))
                        .collect(),
                    source_order,
                },
                ast::GenericParam::Const { span, name, ty } => HirGenericParam::Const {
                    span: span.clone(),
                    name: name.clone(),
                    ty: match ty {
                        ast::ConstKind::U8 => HirConstType::U8,
                        ast::ConstKind::U16 => HirConstType::U16,
                        ast::ConstKind::U32 => HirConstType::U32,
                        ast::ConstKind::U64 => HirConstType::U64,
                    },
                    source_order,
                },
            })
            .collect()
    }

    fn constant_value(&mut self, symbol: &SymbolId) -> Option<HirValue> {
        if let Some(value) = self.constant_values.get(symbol) {
            return Some(value.clone());
        }
        let module = self
            .modules
            .iter()
            .position(|candidate| candidate == &symbol.module)?;
        let declaration = self.parsed.sources[module]
            .syntax
            .declarations
            .iter()
            .find_map(|declaration| match declaration {
                Declaration::Const(value) if value.name == symbol.name => Some(value.clone()),
                _ => None,
            })?;
        if !self.resolving_constants.insert(symbol.clone()) {
            self.error(
                module,
                declaration.span,
                format!("constant dependency cycle through `{}`", symbol.as_string()),
            );
            return None;
        }
        let expected = self.ty(module, &declaration.ty, &GenericScope::default());
        let value = self.value(module, &declaration.value, &expected);
        self.resolving_constants.remove(symbol);
        if let Some(value) = &value {
            let length_mismatch = match (value, &expected) {
                (
                    HirValue::Array(values),
                    HirType::Array {
                        length: HirConstArgument::Value { value: length, .. },
                        ..
                    },
                ) if values.len() as u64 != *length => {
                    Some("Array constant length does not match its declared type")
                }
                (
                    HirValue::Buffer(bytes),
                    HirType::Buffer {
                        length: HirConstArgument::Value { value: length, .. },
                    },
                ) if bytes.len() as u64 != *length => {
                    Some("Buffer constant length does not match its declared type")
                }
                _ => None,
            };
            if let Some(message) = length_mismatch {
                self.error(module, declaration.value.span().clone(), message);
                return None;
            }
            if !hir_value_matches_type(value, &expected) {
                self.error(
                    module,
                    declaration.value.span().clone(),
                    "constant value does not match its declared type",
                );
                return None;
            }
            self.constant_values.insert(symbol.clone(), value.clone());
        }
        value
    }

    fn value(&mut self, module: usize, value: &ConstExpr, expected: &HirType) -> Option<HirValue> {
        match value {
            ConstExpr::Constructor {
                span,
                path,
                argument,
            } => {
                let Some(symbol) = self.resolve(module, path, span) else {
                    return None;
                };
                if self.declarations.get(&symbol) != Some(&OwnedDeclKind::Type { generics: 0 }) {
                    self.error(
                        module,
                        span.clone(),
                        "constant constructor must name a newtype",
                    );
                    return None;
                }
                let source_module = self
                    .modules
                    .iter()
                    .position(|candidate| candidate == &symbol.module)?;
                let (carrier, refinement) = self.parsed.sources[source_module]
                    .syntax
                    .declarations
                    .iter()
                    .find_map(|declaration| match declaration {
                        Declaration::Newtype(value) if value.name == symbol.name => {
                            Some((value.underlying.clone(), value.where_clause.clone()))
                        }
                        _ => None,
                    })?;
                let carrier = self.ty(source_module, &carrier, &GenericScope::default());
                let argument = self.value(module, argument, &carrier)?;
                if !hir_value_matches_type(&argument, &carrier) {
                    self.error(
                        module,
                        span.clone(),
                        "newtype constructor argument does not match its carrier type",
                    );
                    return None;
                }
                if !matches!(expected, HirType::Named { symbol: target, .. } if target == &symbol) {
                    self.error(
                        module,
                        span.clone(),
                        "newtype constructor does not match the declared constant type",
                    );
                }
                if let Some(refinement) = refinement {
                    let mut env = HashMap::new();
                    env.insert(
                        "self".to_owned(),
                        (
                            SymbolId::new(symbol.module.clone(), "self"),
                            carrier.clone(),
                            false,
                        ),
                    );
                    let refinement = self.expr(source_module, &refinement, &env);
                    if self.eval_hir_constant(&refinement, Some(&argument))
                        != Some(HirValue::Bool(true))
                    {
                        self.error(
                            module,
                            span.clone(),
                            "newtype constant does not satisfy its refinement",
                        );
                        return None;
                    }
                }
                Some(HirValue::Named {
                    symbol,
                    fields: vec![("value".to_owned(), argument)],
                })
            }
            ConstExpr::Tuple { span, values } => {
                let HirType::Tuple { items } = expected else {
                    self.error(
                        module,
                        span.clone(),
                        "Tuple constant requires a Tuple[T1, T2, ...] type",
                    );
                    return None;
                };
                if values.len() != items.len() {
                    self.error(
                        module,
                        span.clone(),
                        "Tuple constant arity must exactly match its type",
                    );
                    return None;
                }
                values
                    .iter()
                    .zip(items)
                    .map(|(value, item)| self.value(module, value, item))
                    .collect::<Option<Vec<_>>>()
                    .map(HirValue::Tuple)
            }
            ConstExpr::Array { span, values } => {
                let HirType::Array { item, .. } = expected else {
                    self.error(
                        module,
                        span.clone(),
                        "Array constant requires an Array[T, N] type",
                    );
                    return None;
                };
                values
                    .iter()
                    .map(|value| self.value(module, value, item))
                    .collect::<Option<Vec<_>>>()
                    .map(HirValue::Array)
            }
            ConstExpr::Buffer { span, hex } => {
                if !matches!(expected, HirType::Buffer { .. }) {
                    self.error(
                        module,
                        span.clone(),
                        "Buffer constant requires a Buffer[N] type",
                    );
                    return None;
                }
                if hex.len() % 2 != 0
                    || !hex
                        .bytes()
                        .all(|byte| byte.is_ascii_digit() || (byte as char).is_ascii_lowercase())
                {
                    self.error(
                        module,
                        span.clone(),
                        "Buffer hex must contain lowercase hexadecimal byte pairs",
                    );
                    return None;
                }
                hex.as_bytes()
                    .chunks_exact(2)
                    .map(|pair| {
                        std::str::from_utf8(pair)
                            .ok()
                            .and_then(|pair| u8::from_str_radix(pair, 16).ok())
                    })
                    .collect::<Option<Vec<_>>>()
                    .map(HirValue::Buffer)
            }
            ConstExpr::Expression(expression) => {
                self.constant_expression(module, expression, expected)
            }
        }
    }

    fn constant_expression(
        &mut self,
        module: usize,
        expression: &Expr,
        expected: &HirType,
    ) -> Option<HirValue> {
        match &expression.kind {
            ExprKind::Literal(literal) => match &literal.kind {
                LiteralKind::Bool(value) => Some(HirValue::Bool(*value)),
                LiteralKind::Integer(value) => Some(HirValue::Integer(value.clone())),
                LiteralKind::Float(value) => {
                    let parsed = value.parse::<f64>().ok()?;
                    if matches!(expected, HirType::Primitive(PrimitiveType::F32)) {
                        Some(HirValue::F32 {
                            bits: format!("{:08x}", (parsed as f32).to_bits()),
                        })
                    } else {
                        Some(HirValue::F64 {
                            bits: format!("{:016x}", parsed.to_bits()),
                        })
                    }
                }
                LiteralKind::String(value) => Some(HirValue::String(value.clone())),
            },
            ExprKind::Unit => Some(HirValue::Unit),
            ExprKind::Parenthesized(inner) => self.constant_expression(module, inner, expected),
            ExprKind::Name(path) => {
                if path.segments.as_slice() == ["Option", "Nothing"] {
                    if matches!(expected, HirType::Option { .. }) {
                        return Some(HirValue::Option(None));
                    }
                    self.error(
                        module,
                        expression.span.clone(),
                        "Option.Nothing does not match the declared constant type",
                    );
                    return None;
                }
                if let Some(symbol) = self.lookup(module, path)
                    && self.declarations.get(&symbol) == Some(&OwnedDeclKind::Const)
                {
                    return self.constant_value(&symbol);
                }
                self.enum_variant(module, path)
                    .map(|(variant, _)| HirValue::Enum {
                        variant,
                        fields: Vec::new(),
                    })
                    .or_else(|| {
                        self.error(
                            module,
                            expression.span.clone(),
                            "unknown constant reference",
                        );
                        None
                    })
            }
            ExprKind::Unary { op, operand } => {
                let value = self.constant_expression(module, operand, expected)?;
                eval_const_unary(*op, value).or_else(|| {
                    self.error(
                        module,
                        expression.span.clone(),
                        "invalid constant unary operation",
                    );
                    None
                })
            }
            ExprKind::Binary { left, op, right } => {
                let left = self.constant_expression(module, left, expected)?;
                let right = self.constant_expression(module, right, expected)?;
                eval_const_binary(left, *op, right).or_else(|| {
                    self.error(
                        module,
                        expression.span.clone(),
                        "invalid constant binary operation",
                    );
                    None
                })
            }
            ExprKind::Comparison { first, rest } => {
                let mut left = self.constant_expression(module, first, expected)?;
                for (op, right) in rest {
                    let right = self.constant_expression(module, right, expected)?;
                    if !eval_const_compare(&left, *op, &right)? {
                        return Some(HirValue::Bool(false));
                    }
                    left = right;
                }
                Some(HirValue::Bool(true))
            }
            ExprKind::Field { .. } | ExprKind::OldStateField { .. } => {
                self.error(
                    module,
                    expression.span.clone(),
                    "field access is not allowed in constant expressions",
                );
                None
            }
        }
    }

    fn eval_hir_constant(
        &mut self,
        expression: &HirExpr,
        self_value: Option<&HirValue>,
    ) -> Option<HirValue> {
        match &expression.kind {
            HirExprKind::Literal(value) => Some(value.clone()),
            HirExprKind::SelfRef => self_value.cloned(),
            HirExprKind::ConstantRef(symbol) => self.constant_value(symbol),
            HirExprKind::Unary { op, operand } => eval_const_unary(
                match op {
                    HirUnaryOp::Not => UnaryOp::Not,
                    HirUnaryOp::Plus => UnaryOp::Plus,
                    HirUnaryOp::Minus => UnaryOp::Minus,
                },
                self.eval_hir_constant(operand, self_value)?,
            ),
            HirExprKind::Binary { op, left, right } => eval_const_binary(
                self.eval_hir_constant(left, self_value)?,
                match op {
                    HirBinaryOp::Or => BinaryOp::Or,
                    HirBinaryOp::And => BinaryOp::And,
                    HirBinaryOp::Add => BinaryOp::Add,
                    HirBinaryOp::Subtract => BinaryOp::Subtract,
                    HirBinaryOp::Multiply => BinaryOp::Multiply,
                    HirBinaryOp::Divide => BinaryOp::Divide,
                    HirBinaryOp::Remainder => BinaryOp::Remainder,
                },
                self.eval_hir_constant(right, self_value)?,
            ),
            HirExprKind::ComparisonChain {
                operands,
                operators,
            } => {
                let mut values = operands
                    .iter()
                    .map(|operand| self.eval_hir_constant(operand, self_value))
                    .collect::<Option<Vec<_>>>()?
                    .into_iter();
                let mut left = values.next()?;
                for (operator, right) in operators.iter().zip(values) {
                    let operator = match operator {
                        HirCompareOp::Equal => CompareOp::Equal,
                        HirCompareOp::NotEqual => CompareOp::NotEqual,
                        HirCompareOp::Less => CompareOp::Less,
                        HirCompareOp::LessEqual => CompareOp::LessEqual,
                        HirCompareOp::Greater => CompareOp::Greater,
                        HirCompareOp::GreaterEqual => CompareOp::GreaterEqual,
                    };
                    if !eval_const_compare(&left, operator, &right)? {
                        return Some(HirValue::Bool(false));
                    }
                    left = right;
                }
                Some(HirValue::Bool(true))
            }
            HirExprKind::Len { value } => match self.eval_hir_constant(value, self_value)? {
                HirValue::String(value) => {
                    Some(HirValue::Integer(value.chars().count().to_string()))
                }
                HirValue::Bytes(value) => Some(HirValue::Integer(value.len().to_string())),
                HirValue::List(value) | HirValue::Tuple(value) | HirValue::Array(value) => {
                    Some(HirValue::Integer(value.len().to_string()))
                }
                HirValue::Buffer(value) => Some(HirValue::Integer(value.len().to_string())),
                _ => None,
            },
            HirExprKind::Field { base, name } => match self.eval_hir_constant(base, self_value)? {
                HirValue::Named { fields, .. } => fields
                    .into_iter()
                    .find_map(|(field, value)| (field == *name).then_some(value)),
                _ => None,
            },
            HirExprKind::ParameterRef(_)
            | HirExprKind::BindingRef(_)
            | HirExprKind::ResultRef
            | HirExprKind::OldStateField { .. }
            | HirExprKind::EnumSingletonRef(_) => None,
        }
    }
}

fn eval_const_unary(op: UnaryOp, value: HirValue) -> Option<HirValue> {
    match (op, value) {
        (UnaryOp::Not, HirValue::Bool(value)) => Some(HirValue::Bool(!value)),
        (
            UnaryOp::Plus,
            value @ (HirValue::Integer(_) | HirValue::F32 { .. } | HirValue::F64 { .. }),
        ) => Some(value),
        (UnaryOp::Minus, HirValue::Integer(value)) => value
            .parse::<i128>()
            .ok()?
            .checked_neg()
            .map(|value| HirValue::Integer(value.to_string())),
        (UnaryOp::Minus, HirValue::F32 { bits }) => Some(HirValue::F32 {
            bits: format!(
                "{:08x}",
                (-f32::from_bits(u32::from_str_radix(&bits, 16).ok()?)).to_bits()
            ),
        }),
        (UnaryOp::Minus, HirValue::F64 { bits }) => Some(HirValue::F64 {
            bits: format!(
                "{:016x}",
                (-f64::from_bits(u64::from_str_radix(&bits, 16).ok()?)).to_bits()
            ),
        }),
        _ => None,
    }
}

fn eval_const_binary(left: HirValue, op: BinaryOp, right: HirValue) -> Option<HirValue> {
    match (left, right) {
        (HirValue::Bool(left), HirValue::Bool(right)) => match op {
            BinaryOp::And => Some(HirValue::Bool(left && right)),
            BinaryOp::Or => Some(HirValue::Bool(left || right)),
            _ => None,
        },
        (HirValue::Integer(left), HirValue::Integer(right)) => {
            let left = left.parse::<i128>().ok()?;
            let right = right.parse::<i128>().ok()?;
            let value = match op {
                BinaryOp::Add => left.checked_add(right),
                BinaryOp::Subtract => left.checked_sub(right),
                BinaryOp::Multiply => left.checked_mul(right),
                BinaryOp::Remainder => left.checked_rem_euclid(right),
                _ => None,
            }?;
            Some(HirValue::Integer(value.to_string()))
        }
        (HirValue::F32 { bits: left }, HirValue::F32 { bits: right }) => {
            let left = f32::from_bits(u32::from_str_radix(&left, 16).ok()?);
            let right = f32::from_bits(u32::from_str_radix(&right, 16).ok()?);
            let value = match op {
                BinaryOp::Add => left + right,
                BinaryOp::Subtract => left - right,
                BinaryOp::Multiply => left * right,
                BinaryOp::Divide => left / right,
                BinaryOp::Remainder => left % right,
                _ => return None,
            };
            value.is_finite().then(|| HirValue::F32 {
                bits: format!("{:08x}", value.to_bits()),
            })
        }
        (HirValue::F64 { bits: left }, HirValue::F64 { bits: right }) => {
            let left = f64::from_bits(u64::from_str_radix(&left, 16).ok()?);
            let right = f64::from_bits(u64::from_str_radix(&right, 16).ok()?);
            let value = match op {
                BinaryOp::Add => left + right,
                BinaryOp::Subtract => left - right,
                BinaryOp::Multiply => left * right,
                BinaryOp::Divide => left / right,
                BinaryOp::Remainder => left % right,
                _ => return None,
            };
            value.is_finite().then(|| HirValue::F64 {
                bits: format!("{:016x}", value.to_bits()),
            })
        }
        _ => None,
    }
}

fn hir_value_matches_type(value: &HirValue, ty: &HirType) -> bool {
    match (value, ty) {
        (HirValue::Bool(_), HirType::Primitive(PrimitiveType::Bool)) => true,
        (HirValue::Integer(value), HirType::Primitive(primitive)) => {
            let Ok(value) = value.parse::<i128>() else {
                return false;
            };
            match primitive {
                PrimitiveType::I8 => i8::try_from(value).is_ok(),
                PrimitiveType::I16 => i16::try_from(value).is_ok(),
                PrimitiveType::I32 => i32::try_from(value).is_ok(),
                PrimitiveType::I64 => i64::try_from(value).is_ok(),
                PrimitiveType::U8 => u8::try_from(value).is_ok(),
                PrimitiveType::U16 => u16::try_from(value).is_ok(),
                PrimitiveType::U32 => u32::try_from(value).is_ok(),
                PrimitiveType::U64 => u64::try_from(value).is_ok(),
                _ => false,
            }
        }
        (HirValue::F32 { bits }, HirType::Primitive(PrimitiveType::F32)) => {
            u32::from_str_radix(bits, 16)
                .ok()
                .map(f32::from_bits)
                .is_some_and(f32::is_finite)
        }
        (HirValue::F64 { bits }, HirType::Primitive(PrimitiveType::F64)) => {
            u64::from_str_radix(bits, 16)
                .ok()
                .map(f64::from_bits)
                .is_some_and(f64::is_finite)
        }
        (HirValue::String(_), HirType::Primitive(PrimitiveType::Str))
        | (HirValue::Bytes(_), HirType::Primitive(PrimitiveType::Bytes))
        | (HirValue::Unit, HirType::Primitive(PrimitiveType::Unit)) => true,
        (HirValue::Named { symbol, .. }, HirType::Named { symbol: ty, .. }) => symbol == ty,
        (HirValue::Enum { variant, .. }, HirType::Named { symbol, .. }) => {
            variant.module == symbol.module
                && variant
                    .name
                    .strip_prefix(&format!("{}.", symbol.name))
                    .is_some()
        }
        (HirValue::Tuple(values), HirType::Tuple { items }) => {
            values.len() == items.len()
                && values
                    .iter()
                    .zip(items)
                    .all(|(value, item)| hir_value_matches_type(value, item))
        }
        (HirValue::Array(values), HirType::Array { item, length }) => {
            matches!(length, HirConstArgument::Value { value, .. } if *value == values.len() as u64)
                && values
                    .iter()
                    .all(|value| hir_value_matches_type(value, item))
        }
        (HirValue::Buffer(bytes), HirType::Buffer { length }) => {
            matches!(length, HirConstArgument::Value { value, .. } if *value == bytes.len() as u64)
        }
        (HirValue::Option(None), HirType::Option { .. }) => true,
        (HirValue::Option(Some(value)), HirType::Option { item }) => {
            hir_value_matches_type(value, item)
        }
        _ => false,
    }
}

fn eval_const_compare(left: &HirValue, op: CompareOp, right: &HirValue) -> Option<bool> {
    let numeric = const_number(left).zip(const_number(right));
    let ordering = if let Some((left, right)) = numeric {
        left.partial_cmp(&right)
    } else {
        None
    };
    Some(match op {
        CompareOp::Equal => ordering.map_or(left == right, std::cmp::Ordering::is_eq),
        CompareOp::NotEqual => ordering.map_or(left != right, |value| !value.is_eq()),
        CompareOp::Less => ordering?.is_lt(),
        CompareOp::LessEqual => ordering?.is_le(),
        CompareOp::Greater => ordering?.is_gt(),
        CompareOp::GreaterEqual => ordering?.is_ge(),
    })
}

fn const_number(value: &HirValue) -> Option<f64> {
    match value {
        HirValue::Integer(value) => value.parse::<f64>().ok(),
        HirValue::F32 { bits } => Some(f32::from_bits(u32::from_str_radix(bits, 16).ok()?) as f64),
        HirValue::F64 { bits } => Some(f64::from_bits(u64::from_str_radix(bits, 16).ok()?)),
        _ => None,
    }
}

fn valid_opaque_tag(tag: &str) -> bool {
    (1..=64).contains(&tag.len())
        && tag
            .bytes()
            .enumerate()
            .all(|(index, byte)| match (index, byte) {
                (0, b'a'..=b'z') => true,
                (_, b'a'..=b'z' | b'0'..=b'9' | b'.' | b'_' | b'-') => true,
                _ => false,
            })
}

fn owned_primitive(name: &str) -> Option<PrimitiveType> {
    Some(match name {
        "Bool" => PrimitiveType::Bool,
        "I8" => PrimitiveType::I8,
        "I16" => PrimitiveType::I16,
        "I32" => PrimitiveType::I32,
        "I64" => PrimitiveType::I64,
        "U8" => PrimitiveType::U8,
        "U16" => PrimitiveType::U16,
        "U32" => PrimitiveType::U32,
        "U64" => PrimitiveType::U64,
        "F32" => PrimitiveType::F32,
        "F64" => PrimitiveType::F64,
        "Str" => PrimitiveType::Str,
        "Bytes" => PrimitiveType::Bytes,
        "Path" => PrimitiveType::Path,
        "Unit" => PrimitiveType::Unit,
        "JsonValue" => PrimitiveType::JsonValue,
        "Any" => PrimitiveType::Any,
        "Unknown" => PrimitiveType::Unknown,
        "Never" => PrimitiveType::Never,
        _ => return None,
    })
}

fn owned_is_numeric(ty: &HirType) -> bool {
    matches!(
        ty,
        HirType::Primitive(
            PrimitiveType::I8
                | PrimitiveType::I16
                | PrimitiveType::I32
                | PrimitiveType::I64
                | PrimitiveType::U8
                | PrimitiveType::U16
                | PrimitiveType::U32
                | PrimitiveType::U64
                | PrimitiveType::F32
                | PrimitiveType::F64
        )
    )
}
fn owned_len_allowed(ty: &HirType) -> bool {
    matches!(
        ty,
        HirType::Primitive(PrimitiveType::Str | PrimitiveType::Bytes)
            | HirType::List { .. }
            | HirType::Set { .. }
            | HirType::Map { .. }
            | HirType::Tuple { .. }
            | HirType::Array { .. }
            | HirType::Buffer { .. }
    )
}
fn hir_const_argument_has_parameter(value: &HirConstArgument) -> bool {
    match value {
        HirConstArgument::Parameter { .. } => true,
        HirConstArgument::Binary { left, right, .. } => {
            hir_const_argument_has_parameter(left) || hir_const_argument_has_parameter(right)
        }
        HirConstArgument::Value { .. } | HirConstArgument::Reference { .. } => false,
    }
}
fn const_argument_type(value: &HirConstArgument) -> HirConstType {
    match value {
        HirConstArgument::Value { ty, .. }
        | HirConstArgument::Parameter { ty, .. }
        | HirConstArgument::Reference { ty, .. }
        | HirConstArgument::Binary { ty, .. } => *ty,
    }
}

fn owned_has_unresolved_type(ty: &HirType) -> bool {
    match ty {
        HirType::TypeParameter { .. } | HirType::Opaque { .. } => true,
        HirType::AssociatedProjection { base, .. } => owned_has_unresolved_type(base),
        HirType::Named { args, .. } => args.iter().any(|arg| match arg {
            HirGenericArg::Type(arg) => owned_has_unresolved_type(arg),
            HirGenericArg::Const(arg) => hir_const_argument_has_parameter(arg),
        }),
        HirType::Factory { instance } => owned_has_unresolved_type(instance),
        HirType::List { item }
        | HirType::Set { item }
        | HirType::Option { item }
        | HirType::Iterator { item } => owned_has_unresolved_type(item),
        HirType::Tuple { items } => items.iter().any(owned_has_unresolved_type),
        HirType::Array { item, length } => {
            owned_has_unresolved_type(item) || hir_const_argument_has_parameter(length)
        }
        HirType::Buffer { length } => hir_const_argument_has_parameter(length),
        HirType::Map { key, value } => {
            owned_has_unresolved_type(key) || owned_has_unresolved_type(value)
        }
        HirType::Result { ok, error } => {
            owned_has_unresolved_type(ok) || owned_has_unresolved_type(error)
        }
        HirType::Generator {
            yield_type,
            send_type,
            return_type,
        } => {
            owned_has_unresolved_type(yield_type)
                || owned_has_unresolved_type(send_type)
                || owned_has_unresolved_type(return_type)
        }
        HirType::Primitive(_) => false,
    }
}

fn owned_comparison_compatible(left: &HirType, right: &HirType, op: CompareOp) -> bool {
    if owned_has_unresolved_type(left) || owned_has_unresolved_type(right) {
        return false;
    }
    match op {
        CompareOp::Less | CompareOp::LessEqual | CompareOp::Greater | CompareOp::GreaterEqual => {
            owned_is_numeric(left) && left == right
        }
        CompareOp::Equal | CompareOp::NotEqual => left == right,
    }
}

fn owned_invalid_expr_type(tag: &'static str) -> HirType {
    HirType::Opaque { tag: tag.into() }
}

fn owned_binary_is_logical(op: BinaryOp) -> bool {
    matches!(op, BinaryOp::Or | BinaryOp::And)
}

fn owned_numeric_literal_expression(value: &Expr) -> bool {
    match &value.kind {
        ExprKind::Literal(literal)
            if matches!(
                literal.kind,
                LiteralKind::Integer(_) | LiteralKind::Float(_)
            ) =>
        {
            true
        }
        ExprKind::Parenthesized(inner) => owned_numeric_literal_expression(inner),
        ExprKind::Unary {
            op: UnaryOp::Plus | UnaryOp::Minus,
            operand,
        } => owned_numeric_literal_expression(operand),
        ExprKind::Binary { left, op, right }
            if !owned_binary_is_logical(*op)
                && owned_numeric_literal_expression(left)
                && owned_numeric_literal_expression(right) =>
        {
            true
        }
        _ => false,
    }
}

fn owned_retype_numeric_literal(value: &mut HirExpr, target: &HirType) {
    match &mut value.kind {
        HirExprKind::Literal(HirValue::Integer(_)) if owned_is_numeric(target) => {
            value.ty = target.clone();
        }
        HirExprKind::Literal(HirValue::F64 { bits })
            if matches!(
                target,
                HirType::Primitive(PrimitiveType::F32 | PrimitiveType::F64)
            ) =>
        {
            if matches!(target, HirType::Primitive(PrimitiveType::F32))
                && let Ok(bits) = u64::from_str_radix(bits, 16)
            {
                value.kind = HirExprKind::Literal(HirValue::F32 {
                    bits: format!("{:08x}", (f64::from_bits(bits) as f32).to_bits()),
                });
            }
            value.ty = target.clone();
        }
        HirExprKind::Unary { operand, .. } => {
            owned_retype_numeric_literal(operand, target);
            value.ty = target.clone();
        }
        HirExprKind::Binary { left, right, .. } => {
            owned_retype_numeric_literal(left, target);
            owned_retype_numeric_literal(right, target);
            value.ty = target.clone();
        }
        _ => {}
    }
}
fn owned_value_is_zero(value: &HirValue) -> bool {
    match value {
        HirValue::Integer(value) => value.parse::<i128>() == Ok(0),
        HirValue::F32 { bits } => {
            u32::from_str_radix(bits, 16).is_ok_and(|bits| f32::from_bits(bits) == 0.0)
        }
        HirValue::F64 { bits } => {
            u64::from_str_radix(bits, 16).is_ok_and(|bits| f64::from_bits(bits) == 0.0)
        }
        _ => false,
    }
}

impl<'a> OwnedLower<'a> {
    fn expr(
        &mut self,
        module: usize,
        value: &Expr,
        env: &HashMap<String, (SymbolId, HirType, bool)>,
    ) -> HirExpr {
        let (kind, ty, reference) = match &value.kind {
            ExprKind::Literal(literal) => {
                let (value, ty) = match &literal.kind {
                    LiteralKind::Bool(v) => {
                        (HirValue::Bool(*v), HirType::Primitive(PrimitiveType::Bool))
                    }
                    LiteralKind::Integer(v) => (
                        HirValue::Integer(v.clone()),
                        HirType::Primitive(PrimitiveType::I64),
                    ),
                    LiteralKind::Float(v) => (
                        HirValue::F64 {
                            bits: v
                                .parse::<f64>()
                                .map(|n| format!("{:016x}", n.to_bits()))
                                .unwrap_or_default(),
                        },
                        HirType::Primitive(PrimitiveType::F64),
                    ),
                    LiteralKind::String(v) => (
                        HirValue::String(v.clone()),
                        HirType::Primitive(PrimitiveType::Str),
                    ),
                };
                (HirExprKind::Literal(value), ty, None)
            }
            ExprKind::Unit => (
                HirExprKind::Literal(HirValue::Unit),
                HirType::Primitive(PrimitiveType::Unit),
                None,
            ),
            ExprKind::OldStateField { field } => {
                let key = format!("old:{}", field.name);
                if let Some((symbol, ty, _)) = env.get(&key) {
                    (
                        HirExprKind::OldStateField {
                            field: symbol.clone(),
                        },
                        ty.clone(),
                        Some(HirReference::OldStateField(symbol.clone())),
                    )
                } else {
                    self.error(
                        module,
                        value.span.clone(),
                        "old(self.field) is only allowed in an impl method ensures clause",
                    );
                    (
                        HirExprKind::Literal(HirValue::Unit),
                        owned_invalid_expr_type("invalid-old-state-field"),
                        None,
                    )
                }
            }
            ExprKind::Name(path) => {
                let name = path.segments.last().cloned().unwrap_or_default();
                if path.segments.len() > 1 {
                    if let Some((symbol, ty, binding)) = env.get(&path.segments[0]).cloned() {
                        let mut expression = HirExpr {
                            span: value.span.clone(),
                            ty,
                            reference: if binding {
                                Some(HirReference::Binding(symbol.clone()))
                            } else {
                                Some(HirReference::Parameter(symbol.clone()))
                            },
                            kind: if path.segments[0] == "self" {
                                HirExprKind::SelfRef
                            } else if path.segments[0] == "result" {
                                HirExprKind::ResultRef
                            } else if binding {
                                HirExprKind::BindingRef(symbol)
                            } else {
                                HirExprKind::ParameterRef(symbol)
                            },
                        };
                        for field in path.segments.iter().skip(1) {
                            if field == "len" {
                                let valid = owned_len_allowed(&expression.ty);
                                if !valid {
                                    self.error(
                                        module,
                                        value.span.clone(),
                                        "length is only defined for strings, bytes, lists, sets, and maps",
                                    );
                                }
                                expression = HirExpr {
                                    span: value.span.clone(),
                                    ty: if valid {
                                        HirType::Primitive(PrimitiveType::U64)
                                    } else {
                                        owned_invalid_expr_type("invalid-len")
                                    },
                                    reference: None,
                                    kind: HirExprKind::Len {
                                        value: Box::new(expression),
                                    },
                                };
                            } else {
                                let ty = self
                                    .named_field_type(&expression.ty, field)
                                    .unwrap_or_else(|| HirType::Opaque { tag: field.clone() });
                                expression = HirExpr {
                                    span: value.span.clone(),
                                    ty,
                                    reference: None,
                                    kind: HirExprKind::Field {
                                        base: Box::new(expression),
                                        name: field.clone(),
                                    },
                                };
                            }
                        }
                        return expression;
                    }
                }
                if let Some((symbol, ty, binding)) = env.get(&name) {
                    if name == "self" {
                        (HirExprKind::SelfRef, ty.clone(), None)
                    } else if name == "result" {
                        (HirExprKind::ResultRef, ty.clone(), None)
                    } else if *binding {
                        (
                            HirExprKind::BindingRef(symbol.clone()),
                            ty.clone(),
                            Some(HirReference::Binding(symbol.clone())),
                        )
                    } else {
                        (
                            HirExprKind::ParameterRef(symbol.clone()),
                            ty.clone(),
                            Some(HirReference::Parameter(symbol.clone())),
                        )
                    }
                } else if let Some(symbol) = self.lookup(module, path) {
                    match self.declarations.get(&symbol).copied() {
                        Some(OwnedDeclKind::Const) => {
                            let ty = self
                                .constant_type(&symbol)
                                .unwrap_or_else(|| owned_invalid_expr_type("constant"));
                            (
                                HirExprKind::ConstantRef(symbol.clone()),
                                ty,
                                Some(HirReference::Constant(symbol)),
                            )
                        }
                        _ => (
                            HirExprKind::EnumSingletonRef(symbol.clone()),
                            HirType::Named {
                                symbol: symbol.clone(),
                                args: Vec::new(),
                            },
                            Some(HirReference::EnumSingleton(symbol)),
                        ),
                    }
                } else if let Some((symbol, ty)) = self.enum_variant(module, path) {
                    (
                        HirExprKind::EnumSingletonRef(symbol.clone()),
                        ty,
                        Some(HirReference::EnumSingleton(symbol)),
                    )
                } else {
                    self.error(
                        module,
                        value.span.clone(),
                        format!("unknown type or declaration `{}`", path.segments.join(".")),
                    );
                    (
                        HirExprKind::Literal(HirValue::Unit),
                        HirType::Opaque {
                            tag: "unknown".into(),
                        },
                        None,
                    )
                }
            }
            ExprKind::Parenthesized(inner) => {
                let expression = self.expr(module, inner, env);
                return HirExpr {
                    span: value.span.clone(),
                    ty: expression.ty.clone(),
                    reference: expression.reference.clone(),
                    kind: expression.kind,
                };
            }
            ExprKind::Field { base, name } => {
                let base = self.expr(module, base, env);
                if name == "len" {
                    let valid = owned_len_allowed(&base.ty);
                    if !valid {
                        self.error(
                            module,
                            value.span.clone(),
                            "length is only defined for strings, bytes, lists, sets, and maps",
                        );
                    }
                    (
                        HirExprKind::Len {
                            value: Box::new(base),
                        },
                        if valid {
                            HirType::Primitive(PrimitiveType::U64)
                        } else {
                            owned_invalid_expr_type("invalid-len")
                        },
                        None,
                    )
                } else {
                    let ty = self
                        .named_field_type(&base.ty, name)
                        .unwrap_or_else(|| HirType::Opaque { tag: name.clone() });
                    (
                        HirExprKind::Field {
                            base: Box::new(base),
                            name: name.clone(),
                        },
                        ty,
                        None,
                    )
                }
            }
            ExprKind::Unary { op, operand } => {
                let operand = self.expr(module, operand, env);
                let operand = self.transparent_expression(operand);
                let valid = match op {
                    UnaryOp::Not => operand.ty == HirType::Primitive(PrimitiveType::Bool),
                    UnaryOp::Plus => owned_is_numeric(&operand.ty),
                    UnaryOp::Minus => matches!(
                        operand.ty,
                        HirType::Primitive(
                            PrimitiveType::I8
                                | PrimitiveType::I16
                                | PrimitiveType::I32
                                | PrimitiveType::I64
                                | PrimitiveType::F32
                                | PrimitiveType::F64
                        )
                    ),
                };
                if !valid {
                    self.error(
                        module,
                        value.span.clone(),
                        "unary operator is incompatible with its operand",
                    );
                }
                let ty = if valid {
                    if matches!(op, UnaryOp::Not) {
                        HirType::Primitive(PrimitiveType::Bool)
                    } else {
                        operand.ty.clone()
                    }
                } else {
                    owned_invalid_expr_type("invalid-unary")
                };
                (
                    HirExprKind::Unary {
                        op: match op {
                            UnaryOp::Not => HirUnaryOp::Not,
                            UnaryOp::Plus => HirUnaryOp::Plus,
                            UnaryOp::Minus => HirUnaryOp::Minus,
                        },
                        operand: Box::new(operand),
                    },
                    ty,
                    None,
                )
            }
            ExprKind::Binary { left, op, right } => {
                let mut left_value = self.expr(module, left, env);
                let mut right_value = self.expr(module, right, env);
                let mut left_compat = self.expression_compat_type(&left_value.ty);
                let mut right_compat = self.expression_compat_type(&right_value.ty);
                if owned_numeric_literal_expression(left)
                    && !owned_numeric_literal_expression(right)
                    && owned_is_numeric(&right_compat)
                {
                    owned_retype_numeric_literal(&mut left_value, &right_compat);
                } else if owned_numeric_literal_expression(right)
                    && !owned_numeric_literal_expression(left)
                    && owned_is_numeric(&left_compat)
                {
                    owned_retype_numeric_literal(&mut right_value, &left_compat);
                }
                if !owned_numeric_literal_expression(left) {
                    left_value = self.transparent_expression(left_value);
                }
                if !owned_numeric_literal_expression(right) {
                    right_value = self.transparent_expression(right_value);
                }
                left_compat = self.expression_compat_type(&left_value.ty);
                right_compat = self.expression_compat_type(&right_value.ty);
                let zero_divisor = matches!(op, BinaryOp::Divide | BinaryOp::Remainder)
                    && self
                        .eval_hir_constant(&right_value, None)
                        .is_some_and(|value| owned_value_is_zero(&value));
                if zero_divisor {
                    self.error(
                        module,
                        right.span.clone(),
                        "division or remainder by a compile-time zero divisor",
                    );
                }
                let valid = !zero_divisor
                    && match op {
                        BinaryOp::Or | BinaryOp::And => {
                            left_value.ty == HirType::Primitive(PrimitiveType::Bool)
                                && right_value.ty == HirType::Primitive(PrimitiveType::Bool)
                        }
                        BinaryOp::Divide => {
                            left_compat == right_compat
                                && matches!(
                                    left_compat,
                                    HirType::Primitive(PrimitiveType::F32 | PrimitiveType::F64)
                                )
                        }
                        BinaryOp::Remainder => {
                            left_compat == right_compat
                                && matches!(
                                    left_compat,
                                    HirType::Primitive(
                                        PrimitiveType::I8
                                            | PrimitiveType::I16
                                            | PrimitiveType::I32
                                            | PrimitiveType::I64
                                            | PrimitiveType::U8
                                            | PrimitiveType::U16
                                            | PrimitiveType::U32
                                            | PrimitiveType::U64
                                    )
                                )
                        }
                        _ => owned_is_numeric(&left_compat) && left_compat == right_compat,
                    };
                if !valid && !zero_divisor {
                    self.error(
                        module,
                        value.span.clone(),
                        if owned_binary_is_logical(*op) {
                            "logical operator requires boolean operands"
                        } else {
                            "arithmetic operands must have the same compatible numeric type"
                        },
                    );
                }
                let ty = if valid {
                    if owned_binary_is_logical(*op) {
                        HirType::Primitive(PrimitiveType::Bool)
                    } else {
                        left_value.ty.clone()
                    }
                } else {
                    owned_invalid_expr_type("invalid-binary")
                };
                let op = match op {
                    BinaryOp::Or => HirBinaryOp::Or,
                    BinaryOp::And => HirBinaryOp::And,
                    BinaryOp::Add => HirBinaryOp::Add,
                    BinaryOp::Subtract => HirBinaryOp::Subtract,
                    BinaryOp::Multiply => HirBinaryOp::Multiply,
                    BinaryOp::Divide => HirBinaryOp::Divide,
                    BinaryOp::Remainder => HirBinaryOp::Remainder,
                };
                (
                    HirExprKind::Binary {
                        op,
                        left: Box::new(left_value),
                        right: Box::new(right_value),
                    },
                    ty,
                    None,
                )
            }
            ExprKind::Comparison { first, rest } => {
                let raw_operands = std::iter::once(first.as_ref())
                    .chain(rest.iter().map(|(_, expression)| expression))
                    .collect::<Vec<_>>();
                let mut operands = raw_operands
                    .iter()
                    .map(|expression| self.expr(module, expression, env))
                    .collect::<Vec<_>>();
                let initial_compat = operands
                    .iter()
                    .map(|operand| self.expression_compat_type(&operand.ty))
                    .collect::<Vec<_>>();
                let context = raw_operands
                    .iter()
                    .zip(initial_compat.iter())
                    .find(|(expression, ty)| {
                        !owned_numeric_literal_expression(expression) && owned_is_numeric(ty)
                    })
                    .map(|(_, ty)| ty.clone());
                if let Some(context) = &context {
                    for (expression, operand) in raw_operands.iter().zip(&mut operands) {
                        if owned_numeric_literal_expression(expression) {
                            owned_retype_numeric_literal(operand, context);
                        }
                    }
                }
                let compat_types = operands
                    .iter()
                    .map(|operand| self.expression_compat_type(&operand.ty))
                    .collect::<Vec<_>>();
                for (expression, operand) in raw_operands.iter().zip(&mut operands) {
                    if !owned_numeric_literal_expression(expression) {
                        *operand = self.transparent_expression(operand.clone());
                    }
                }
                let mut valid = context.is_some()
                    || !raw_operands
                        .iter()
                        .all(|expression| owned_numeric_literal_expression(expression));
                let operators = rest
                    .iter()
                    .map(|(op, _)| match op {
                        CompareOp::Equal => HirCompareOp::Equal,
                        CompareOp::NotEqual => HirCompareOp::NotEqual,
                        CompareOp::Less => HirCompareOp::Less,
                        CompareOp::LessEqual => HirCompareOp::LessEqual,
                        CompareOp::Greater => HirCompareOp::Greater,
                        CompareOp::GreaterEqual => HirCompareOp::GreaterEqual,
                    })
                    .collect::<Vec<_>>();
                for (index, (op, _)) in rest.iter().enumerate() {
                    if !owned_comparison_compatible(
                        &compat_types[index],
                        &compat_types[index + 1],
                        *op,
                    ) {
                        valid = false;
                    }
                }
                if !valid {
                    self.error(
                        module,
                        value.span.clone(),
                        "comparison operands require the same resolved type and numeric literals require context",
                    );
                }
                (
                    HirExprKind::ComparisonChain {
                        operands,
                        operators,
                    },
                    if valid {
                        HirType::Primitive(PrimitiveType::Bool)
                    } else {
                        owned_invalid_expr_type("invalid-comparison")
                    },
                    None,
                )
            }
        };
        HirExpr {
            span: value.span.clone(),
            ty,
            reference,
            kind,
        }
    }
}

impl<'a> OwnedLower<'a> {
    fn named_field_type(&mut self, ty: &HirType, field_name: &str) -> Option<HirType> {
        let HirType::Named { symbol, args } = ty else {
            return None;
        };
        let source_index = self
            .modules
            .iter()
            .position(|module| module == &symbol.module)?;
        let (field_type, generics) = {
            let declarations = &self.parsed.sources[source_index].syntax.declarations;
            declarations
                .iter()
                .find_map(|declaration| match declaration {
                    Declaration::Struct(value) if value.name == symbol.name => value
                        .fields
                        .iter()
                        .find(|field| field.name == field_name)
                        .map(|field| (field.ty.clone(), value.generics.clone())),
                    Declaration::Newtype(value)
                        if value.name == symbol.name && field_name == "value" =>
                    {
                        Some((value.underlying.clone(), Vec::new()))
                    }
                    Declaration::Impl(value) if value.name == symbol.name => value
                        .state
                        .iter()
                        .find(|field| field.name == field_name)
                        .map(|field| (field.ty.clone(), Vec::new())),
                    _ => None,
                })?
        };
        let lowered = self.ty(
            source_index,
            &field_type,
            &GenericScope::from_declared(&generics),
        );
        let substitutions = generics
            .into_iter()
            .map(|generic| match generic {
                ast::GenericParam::Type { name, .. } | ast::GenericParam::Const { name, .. } => {
                    name
                }
            })
            .zip(args.iter().cloned())
            .collect::<HashMap<_, _>>();
        Some(substitute_hir_type(lowered, &substitutions))
    }

    fn field(
        &mut self,
        module: usize,
        field: &ast::Field,
        generics: &GenericScope,
        order: usize,
    ) -> HirField {
        let ty = self.ty(module, &field.ty, generics);
        let default = match (&ty, &field.default) {
            (HirType::Named { symbol, args }, value)
                if args.is_empty()
                    && self.declarations.get(symbol) == Some(&OwnedDeclKind::Resource) =>
            {
                let initial = self.resource_initial_state(symbol);
                if let Some(value) = value {
                    let ConstExpr::Expression(Expr {
                        kind: ExprKind::Name(path),
                        ..
                    }) = value
                    else {
                        self.error(
                            module,
                            value.span().clone(),
                            "resource default must be its initial state",
                        );
                        return HirField {
                            span: field.span.clone(),
                            name: field.name.clone(),
                            ty,
                            default: None,
                            source_order: order,
                        };
                    };
                    let state = self
                        .resource_state_ref(module, path)
                        .map(|(_, state)| state);
                    if state.as_ref() != initial.as_ref() {
                        self.error(
                            module,
                            value.span().clone(),
                            "resource default must be its initial state",
                        );
                    }
                }
                initial.map(|variant| HirValue::Enum {
                    variant,
                    fields: Vec::new(),
                })
            }
            (_, Some(value)) => self.value(module, value, &ty),
            (_, None) => None,
        };
        if default
            .as_ref()
            .is_some_and(|value| !hir_value_matches_type(value, &ty))
        {
            self.error(
                module,
                field.default.as_ref().unwrap().span().clone(),
                "default value does not match its declared type",
            );
        }
        HirField {
            span: field.span.clone(),
            name: field.name.clone(),
            ty,
            default,
            source_order: order,
        }
    }

    fn parameter(
        &mut self,
        module: usize,
        parameter: &ast::Parameter,
        generics: &GenericScope,
        order: usize,
    ) -> HirParameter {
        HirParameter {
            span: parameter.span.clone(),
            name: parameter.name.clone(),
            ty: self.ty(module, &parameter.ty, generics),
            default: None,
            kind: HirParameterKind::Positional,
            source_order: order,
        }
    }

    fn error_variant(
        &mut self,
        module: usize,
        path: &ast::QualifiedName,
    ) -> Option<(SymbolId, SymbolId)> {
        if path.segments.len() < 2 {
            self.error(
                module,
                path.span.clone(),
                "error clause must name an enum variant",
            );
            return None;
        }
        let prefix = ast::QualifiedName::new(
            path.span.clone(),
            path.segments[..path.segments.len() - 1].to_vec(),
        );
        let Some(owner) = self.resolve(module, &prefix, &path.span) else {
            return None;
        };
        if !matches!(
            self.declarations.get(&owner),
            Some(OwnedDeclKind::Enum { .. })
        ) {
            self.error(
                module,
                path.span.clone(),
                "error clause variant owner must be an enum",
            );
            return None;
        }
        let Some(source_index) = self
            .modules
            .iter()
            .position(|candidate| candidate == &owner.module)
        else {
            return None;
        };
        let variant_name = path.segments.last().cloned().unwrap_or_default();
        let exists = self.parsed.sources[source_index]
            .syntax
            .declarations
            .iter()
            .any(|declaration| {
                matches!(
                    declaration,
                    Declaration::Enum(value)
                        if value.name == owner.name
                            && value.variants.iter().any(|variant| variant.name == variant_name)
                )
            });
        if !exists {
            self.error(
                module,
                path.span.clone(),
                format!("unknown enum variant `{}`", path.segments.join(".")),
            );
            return None;
        }
        Some((
            SymbolId::new(
                owner.module.clone(),
                format!("{}.{}", owner.name, variant_name),
            ),
            owner,
        ))
    }

    fn match_guard(
        &mut self,
        module: usize,
        guard: &ast::MatchGuard,
        env: &HashMap<String, (SymbolId, HirType, bool)>,
    ) -> (HirMatchGuard, HashMap<String, (SymbolId, HirType, bool)>) {
        let scrutinee = self.expr(module, &guard.scrutinee, env);
        let mut clause_env = env.clone();
        let pattern = self.pattern(module, &guard.pattern, &scrutinee.ty, &mut clause_env);
        (
            HirMatchGuard {
                span: guard.span.clone(),
                scrutinee,
                pattern,
            },
            clause_env,
        )
    }

    fn contract(
        &mut self,
        module: usize,
        clauses: &[ast::Clause],
        env: &HashMap<String, (SymbolId, HirType, bool)>,
        return_type: &HirType,
        old_fields: Option<&HashMap<String, (SymbolId, HirType, bool)>>,
        allow_result: bool,
    ) -> (HirContract, Option<HirDoc>) {
        let mut contract = HirContract::default();
        let mut doc = None;
        for (clause_id, clause) in clauses.iter().enumerate() {
            match &clause.kind {
                ClauseKind::Documentation(value) => {
                    doc = Some(HirDoc {
                        span: value.span.clone(),
                        text: value.text.clone(),
                    });
                }
                ClauseKind::Rule { name } => {
                    if let Some(rule_sym) = self.resolve(module, name, &name.span) {
                        if !matches!(
                            self.declarations.get(&rule_sym),
                            Some(OwnedDeclKind::Rule { .. })
                        ) {
                            self.error(
                                module,
                                name.span.clone(),
                                format!("`{}` is not a rule", name.segments.join(".")),
                            );
                        } else if let Some(rule) = self.lowered_rules.get(&rule_sym) {
                            for clause in &rule.contract.clauses {
                                contract.clauses.push(HirClause {
                                    clause_id: contract.clauses.len() as u32,
                                    span: clause.span.clone(),
                                    kind: clause.kind.clone(),
                                });
                            }
                            for effect in &rule.contract.effects {
                                contract.effects.push(effect.clone());
                            }
                        }
                    }
                }
                ClauseKind::Requires { guard, condition } => {
                    let (guard, clause_env) = match guard {
                        Some(guard) => {
                            let (guard, clause_env) = self.match_guard(module, guard, env);
                            (Some(guard), clause_env)
                        }
                        None => (None, env.clone()),
                    };
                    let expression = self.expr(module, condition, &clause_env);
                    if expression.ty != HirType::Primitive(PrimitiveType::Bool) {
                        self.error(
                            module,
                            condition.span.clone(),
                            "contract condition must be boolean",
                        );
                    }
                    contract.clauses.push(HirClause {
                        clause_id: clause_id as u32,
                        span: clause.span.clone(),
                        kind: HirClauseKind::Requires { guard, expression },
                    });
                }
                ClauseKind::Ensures { guard, condition } => {
                    let mut clause_env = env.clone();
                    if let Some(old_fields) = old_fields {
                        clause_env.extend(old_fields.clone());
                    }
                    if allow_result {
                        clause_env.insert(
                            "result".to_owned(),
                            (
                                SymbolId::new(self.modules[module].clone(), "result"),
                                return_type.clone(),
                                false,
                            ),
                        );
                    }
                    let (guard, mut clause_env) = match guard {
                        Some(guard) => {
                            let (guard, clause_env) = self.match_guard(module, guard, &clause_env);
                            (Some(guard), clause_env)
                        }
                        None => (None, clause_env),
                    };
                    if guard.is_some() {
                        clause_env.remove("result");
                    }
                    let expression = self.expr(module, condition, &clause_env);
                    if expression.ty != HirType::Primitive(PrimitiveType::Bool) {
                        self.error(
                            module,
                            condition.span.clone(),
                            "contract condition must be boolean",
                        );
                    }
                    contract.clauses.push(HirClause {
                        clause_id: clause_id as u32,
                        span: clause.span.clone(),
                        kind: HirClauseKind::Ensures { guard, expression },
                    });
                }
                ClauseKind::Error { error, guard, when } => {
                    let resolved = self.error_variant(module, error);
                    let valid_return = matches!(
                        return_type,
                        HirType::Result { error: expected, .. }
                            if resolved.as_ref().is_some_and(|(_, owner)| {
                                matches!(expected.as_ref(), HirType::Named { symbol, .. } if symbol == owner)
                            })
                    );
                    if !matches!(return_type, HirType::Result { .. }) {
                        self.error(
                            module,
                            error.span.clone(),
                            "error clauses require a Result return type",
                        );
                    } else if resolved.is_some() && !valid_return {
                        self.error(
                            module,
                            error.span.clone(),
                            "error clause variant does not belong to the Result error type",
                        );
                    }
                    let (guard, clause_env) = match guard {
                        Some(guard) => {
                            let (guard, clause_env) = self.match_guard(module, guard, env);
                            (Some(guard), clause_env)
                        }
                        None => (None, env.clone()),
                    };
                    let when = when.as_ref().map(|value| {
                        let expression = self.expr(module, value, &clause_env);
                        if expression.ty != HirType::Primitive(PrimitiveType::Bool) {
                            self.error(
                                module,
                                value.span.clone(),
                                "contract condition must be boolean",
                            );
                        }
                        expression
                    });
                    if let Some((variant, _)) = resolved.filter(|_| valid_return) {
                        contract.clauses.push(HirClause {
                            clause_id: clause_id as u32,
                            span: clause.span.clone(),
                            kind: HirClauseKind::Error {
                                variant,
                                priority: None,
                                guard,
                                when,
                            },
                        });
                    }
                }
                ClauseKind::Modifies { .. } | ClauseKind::Transitions { .. } => {}
                ClauseKind::Effects { effects } => {
                    for (source_order, effect) in effects.iter().enumerate() {
                        contract.effects.push(HirEffect {
                            span: effect.span.clone(),
                            key: effect.segments.join("."),
                            source_order,
                        });
                    }
                }
            }
        }
        (contract, doc)
    }

    fn pattern_argument_types(
        &mut self,
        module: usize,
        expected: &HirType,
        path: &ast::QualifiedName,
        count: usize,
    ) -> Option<(SymbolId, Vec<HirType>)> {
        let name = path.segments.last().map(String::as_str).unwrap_or_default();
        if matches!(
            path.segments.as_slice(),
            [container, _] if container == "Result" || container == "Option"
        ) {
            let (symbol, payload) = match (path.segments[0].as_str(), name, expected) {
                ("Result", "Ok", HirType::Result { ok, .. }) => (
                    SymbolId::new(ModuleId::new(Vec::new()), "Result.Ok"),
                    vec![(**ok).clone()],
                ),
                ("Result", "Err", HirType::Result { error, .. }) => (
                    SymbolId::new(ModuleId::new(Vec::new()), "Result.Err"),
                    vec![(**error).clone()],
                ),
                ("Option", "Some", HirType::Option { item }) => (
                    SymbolId::new(ModuleId::new(Vec::new()), "Option.Some"),
                    vec![(**item).clone()],
                ),
                ("Option", "Nothing", HirType::Option { .. }) => (
                    SymbolId::new(ModuleId::new(Vec::new()), "Option.Nothing"),
                    Vec::new(),
                ),
                ("Result" | "Option", _, _) => {
                    self.error(
                        module,
                        path.span.clone(),
                        format!(
                            "pattern `{}` does not belong to the declared return type",
                            path.segments.join(".")
                        ),
                    );
                    return None;
                }
                _ => unreachable!(),
            };
            if payload.len() != count {
                self.error(
                    module,
                    path.span.clone(),
                    format!(
                        "pattern `{}` expects {} argument(s), got {}",
                        path.segments.join("."),
                        payload.len(),
                        count
                    ),
                );
                return None;
            }
            return Some((symbol, payload));
        }

        let HirType::Named {
            symbol: expected_owner,
            args,
        } = expected
        else {
            self.error(
                module,
                path.span.clone(),
                format!(
                    "pattern `{}` does not belong to the declared return type",
                    path.segments.join(".")
                ),
            );
            return None;
        };
        if path.segments.len() < 2 {
            self.error(
                module,
                path.span.clone(),
                "nominal patterns must name an enum variant",
            );
            return None;
        }
        let prefix = ast::QualifiedName::new(
            path.span.clone(),
            path.segments[..path.segments.len() - 1].to_vec(),
        );
        let Some(owner) = self.resolve(module, &prefix, &path.span) else {
            return None;
        };
        if &owner != expected_owner
            || !matches!(
                self.declarations.get(&owner),
                Some(OwnedDeclKind::Enum { .. })
            )
        {
            self.error(
                module,
                path.span.clone(),
                format!(
                    "pattern `{}` does not belong to the declared return type",
                    path.segments.join(".")
                ),
            );
            return None;
        }
        let Some(source_index) = self
            .modules
            .iter()
            .position(|candidate| candidate == &owner.module)
        else {
            return None;
        };
        let variant_name = name;
        let Some((field_types, generic_parameters)) = self.parsed.sources[source_index]
            .syntax
            .declarations
            .iter()
            .find_map(|declaration| match declaration {
                Declaration::Enum(value) if value.name == owner.name => value
                    .variants
                    .iter()
                    .find(|variant| variant.name == variant_name)
                    .map(|variant| {
                        (
                            variant
                                .parameters
                                .iter()
                                .map(|field| field.ty.clone())
                                .collect::<Vec<_>>(),
                            value.generics.clone(),
                        )
                    }),
                _ => None,
            })
        else {
            self.error(
                module,
                path.span.clone(),
                format!("unknown enum variant `{}`", path.segments.join(".")),
            );
            return None;
        };
        if field_types.len() != count {
            self.error(
                module,
                path.span.clone(),
                format!(
                    "pattern `{}` expects {} argument(s), got {}",
                    path.segments.join("."),
                    field_types.len(),
                    count
                ),
            );
            return None;
        }
        let scope = GenericScope::from_declared(&generic_parameters);
        let substitutions = generic_parameters
            .into_iter()
            .map(|generic| match generic {
                ast::GenericParam::Type { name, .. } | ast::GenericParam::Const { name, .. } => {
                    name
                }
            })
            .zip(args.iter().cloned())
            .collect::<HashMap<_, _>>();
        let fields = field_types
            .iter()
            .map(|field| {
                let ty = self.ty(source_index, field, &scope);
                substitute_hir_type(ty, &substitutions)
            })
            .collect();
        Some((
            SymbolId::new(
                owner.module.clone(),
                format!("{}.{}", owner.name, variant_name),
            ),
            fields,
        ))
    }

    fn pattern(
        &mut self,
        module: usize,
        pattern: &ast::Pattern,
        expected: &HirType,
        env: &mut HashMap<String, (SymbolId, HirType, bool)>,
    ) -> HirPattern {
        match &pattern.kind {
            PatternKind::Wildcard => HirPattern {
                span: pattern.span.clone(),
                ty: expected.clone(),
                kind: HirPatternKind::Wildcard,
            },
            PatternKind::Binding(name) => {
                let symbol = SymbolId::new(self.modules[module].clone(), name.clone());
                if env.contains_key(name) {
                    self.error(
                        module,
                        pattern.span.clone(),
                        format!("duplicate pattern binding `{name}`"),
                    );
                } else {
                    env.insert(name.clone(), (symbol.clone(), expected.clone(), true));
                }
                HirPattern {
                    span: pattern.span.clone(),
                    ty: expected.clone(),
                    kind: HirPatternKind::Binding {
                        symbol,
                        name: name.clone(),
                    },
                }
            }
            PatternKind::Variant { path, arguments } => {
                let Some((symbol, argument_types)) =
                    self.pattern_argument_types(module, expected, path, arguments.len())
                else {
                    return HirPattern {
                        span: pattern.span.clone(),
                        ty: expected.clone(),
                        kind: HirPatternKind::Wildcard,
                    };
                };
                HirPattern {
                    span: pattern.span.clone(),
                    ty: expected.clone(),
                    kind: HirPatternKind::Variant {
                        symbol,
                        arguments: arguments
                            .iter()
                            .zip(argument_types.iter())
                            .map(|(value, ty)| self.pattern(module, value, ty, env))
                            .collect(),
                    },
                }
            }
        }
    }
    fn infer_rule_pattern_type(
        &mut self,
        module: usize,
        pattern: &ast::Pattern,
        generics: &HashSet<String>,
    ) -> HirType {
        match &pattern.kind {
            PatternKind::Variant { path, arguments }
                if path.segments.as_slice() == ["Result", "Ok"] =>
            {
                HirType::Result {
                    ok: Box::new(
                        arguments
                            .first()
                            .map(|argument| {
                                self.infer_rule_pattern_type(module, argument, generics)
                            })
                            .unwrap_or(HirType::Primitive(PrimitiveType::Unit)),
                    ),
                    error: Box::new(HirType::Primitive(PrimitiveType::Never)),
                }
            }
            PatternKind::Variant { path, arguments }
                if path.segments.as_slice() == ["Result", "Err"] =>
            {
                HirType::Result {
                    ok: Box::new(HirType::Primitive(PrimitiveType::Never)),
                    error: Box::new(
                        arguments
                            .first()
                            .map(|argument| {
                                self.infer_rule_pattern_type(module, argument, generics)
                            })
                            .unwrap_or(HirType::Primitive(PrimitiveType::Unit)),
                    ),
                }
            }
            PatternKind::Variant { path, arguments }
                if path.segments.as_slice() == ["Option", "Some"] =>
            {
                HirType::Option {
                    item: Box::new(
                        arguments
                            .first()
                            .map(|argument| {
                                self.infer_rule_pattern_type(module, argument, generics)
                            })
                            .unwrap_or(HirType::Primitive(PrimitiveType::Unit)),
                    ),
                }
            }
            PatternKind::Variant { path, .. }
                if path.segments.as_slice() == ["Option", "Nothing"] =>
            {
                HirType::Option {
                    item: Box::new(HirType::Primitive(PrimitiveType::Never)),
                }
            }
            PatternKind::Variant { path, .. } => {
                let prefix = ast::QualifiedName::new(
                    path.span.clone(),
                    path.segments[..path.segments.len().saturating_sub(1)].to_vec(),
                );
                self.resolve(module, &prefix, &path.span)
                    .map(|symbol| HirType::Named {
                        symbol,
                        args: Vec::new(),
                    })
                    .unwrap_or(HirType::Primitive(PrimitiveType::Unit))
            }
            PatternKind::Binding(name) => {
                let mut chars = name.chars();
                let capitalized = chars
                    .next()
                    .map(|first| first.to_uppercase().collect::<String>() + chars.as_str())
                    .unwrap_or_default();
                for candidate in [capitalized, name.clone()] {
                    let path = ast::QualifiedName::new(pattern.span.clone(), vec![candidate]);
                    if let Some(symbol) = self.lookup(module, &path) {
                        return HirType::Named {
                            symbol,
                            args: Vec::new(),
                        };
                    }
                }
                if generics.contains(name) {
                    HirType::TypeParameter { name: name.clone() }
                } else {
                    HirType::Primitive(PrimitiveType::Str)
                }
            }
            PatternKind::Wildcard => HirType::Primitive(PrimitiveType::Unit),
        }
    }

    fn state_type_allowed(&self, ty: &HirType) -> bool {
        match ty {
            HirType::Primitive(PrimitiveType::Never)
            | HirType::TypeParameter { .. }
            | HirType::AssociatedProjection { .. } => false,
            HirType::Primitive(_) | HirType::Opaque { .. } => true,
            HirType::Factory { .. } => false,
            HirType::Named { symbol, args } => {
                matches!(
                    self.declarations.get(symbol),
                    Some(
                        OwnedDeclKind::Type { .. }
                            | OwnedDeclKind::Enum { .. }
                            | OwnedDeclKind::Resource
                    )
                ) && args.iter().all(|arg| match arg {
                    HirGenericArg::Type(arg) => self.state_type_allowed(arg),
                    HirGenericArg::Const(arg) => !hir_const_argument_has_parameter(arg),
                })
            }
            HirType::List { item }
            | HirType::Set { item }
            | HirType::Option { item }
            | HirType::Iterator { item } => self.state_type_allowed(item),
            HirType::Tuple { items } => items.iter().all(|item| self.state_type_allowed(item)),
            HirType::Array { item, length } => {
                self.state_type_allowed(item) && !hir_const_argument_has_parameter(length)
            }
            HirType::Buffer { length } => !hir_const_argument_has_parameter(length),
            HirType::Map { key, value } => {
                self.state_type_allowed(key) && self.state_type_allowed(value)
            }
            HirType::Result { ok, error } => {
                self.state_type_allowed(ok) && self.state_type_allowed(error)
            }
            HirType::Generator {
                yield_type,
                send_type,
                return_type,
            } => {
                self.state_type_allowed(yield_type)
                    && self.state_type_allowed(send_type)
                    && self.state_type_allowed(return_type)
            }
        }
    }

    fn default_function(
        &mut self,
        module: usize,
        trait_id: &SymbolId,
        method: &ast::TraitMethod,
        trait_generics: &[ast::GenericParam],
        trait_scope: &GenericScope,
    ) -> Option<HirVerifiedFunction> {
        let method_id = SymbolId::new(
            trait_id.module.clone(),
            format!("{}.{}", trait_id.name, method.name),
        );
        if let Some(default) = self.default_functions.get(&method_id) {
            return default.clone();
        }
        let resolved = (|| {
            let path = method.default.as_ref()?;
            let symbol = self.resolve(module, path, &path.span)?;
            if self.declarations.get(&symbol) != Some(&OwnedDeclKind::Function) {
                self.error(
                    module,
                    path.span.clone(),
                    "trait default must reference a free function",
                );
                return None;
            }
            let Some(function_module) = self
                .modules
                .iter()
                .position(|candidate| candidate == &symbol.module)
            else {
                return None;
            };
            let Some(function) = self.parsed.sources[function_module]
                .syntax
                .declarations
                .iter()
                .find_map(|declaration| match declaration {
                    Declaration::Function(value) if value.name == symbol.name => {
                        Some(value.clone())
                    }
                    _ => None,
                })
            else {
                return None;
            };
            if function.callable_kind != ast::CallableKind::Sync {
                self.error(
                    module,
                    path.span.clone(),
                    "trait default must reference a sync free function",
                );
                return None;
            }
            let same_generics = trait_generics.len() == function.generics.len()
                && trait_generics
                    .iter()
                    .zip(&function.generics)
                    .all(|(left, right)| match (left, right) {
                        (
                            ast::GenericParam::Type { name: left, .. },
                            ast::GenericParam::Type { name: right, .. },
                        ) => left == right,
                        (
                            ast::GenericParam::Const {
                                name: left,
                                ty: left_ty,
                                ..
                            },
                            ast::GenericParam::Const {
                                name: right,
                                ty: right_ty,
                                ..
                            },
                        ) => left == right && left_ty == right_ty,
                        _ => false,
                    });
            if !same_generics {
                self.error(
                    module,
                    path.span.clone(),
                    "trait default generic parameters must exactly match the trait",
                );
                return None;
            }
            let function_scope = GenericScope::from_declared(&function.generics);
            let receiver = HirType::Named {
                symbol: trait_id.clone(),
                args: trait_generics
                    .iter()
                    .map(|generic| match generic {
                        ast::GenericParam::Type { name, .. } => {
                            HirGenericArg::Type(HirType::TypeParameter { name: name.clone() })
                        }
                        ast::GenericParam::Const { name, ty, .. } => {
                            let ty = match ty {
                                ast::ConstKind::U8 => HirConstType::U8,
                                ast::ConstKind::U16 => HirConstType::U16,
                                ast::ConstKind::U32 => HirConstType::U32,
                                ast::ConstKind::U64 => HirConstType::U64,
                            };
                            HirGenericArg::Const(HirConstArgument::Parameter {
                                name: name.clone(),
                                ty,
                            })
                        }
                    })
                    .collect(),
            };
            let signature_matches = function.parameters.len() == method.parameters.len() + 1
                && function.parameters.first().is_some_and(|parameter| {
                    self.ty(function_module, &parameter.ty, &function_scope) == receiver
                })
                && function
                    .parameters
                    .iter()
                    .skip(1)
                    .zip(&method.parameters)
                    .all(|(function, trait_method)| {
                        function.name == trait_method.name
                            && self.ty(function_module, &function.ty, &function_scope)
                                == self.ty(module, &trait_method.ty, trait_scope)
                    })
                && self.ty(function_module, &function.return_type, &function_scope)
                    == self.ty(module, &method.return_type, trait_scope);
            if !signature_matches {
                self.error(
                    module,
                    path.span.clone(),
                    "trait default must take the trait receiver first and exactly match the method signature",
                );
                return None;
            }
            Some(HirVerifiedFunction {
                module: symbol.module.clone(),
                symbol: symbol.name.clone(),
                verified_facade: symbol.as_string(),
            })
        })();
        self.default_functions.insert(method_id, resolved.clone());
        resolved
    }

    fn validate_impl_methods(
        &mut self,
        module: usize,
        impl_id: &SymbolId,
        impl_span: &Span,
        traits: &[HirType],
        associated_types: &[HirAssociatedTypeAssignment],
        methods: &[HirImplMethod],
    ) -> Vec<HirSelectedMethod> {
        struct RequiredMethod {
            name: String,
            parameters: Vec<(String, HirType)>,
            return_type: HirType,
            trait_methods: Vec<SymbolId>,
            defaults: Vec<HirVerifiedFunction>,
        }

        let mut required = Vec::<RequiredMethod>::new();
        for trait_ref in traits {
            let HirType::Named { symbol, args } = trait_ref else {
                continue;
            };
            let Some(source_module) = self
                .modules
                .iter()
                .position(|candidate| candidate == &symbol.module)
            else {
                continue;
            };
            let Some((generics, trait_methods)) = self.parsed.sources[source_module]
                .syntax
                .declarations
                .iter()
                .find_map(|declaration| match declaration {
                    Declaration::Trait(value) if value.name == symbol.name => {
                        Some((value.generics.clone(), value.methods.clone()))
                    }
                    _ => None,
                })
            else {
                continue;
            };
            let scope = GenericScope::from_declared(&generics);
            let substitutions = generics
                .iter()
                .map(|generic| match generic {
                    ast::GenericParam::Type { name, .. }
                    | ast::GenericParam::Const { name, .. } => name.clone(),
                })
                .zip(args.iter().cloned())
                .collect::<HashMap<_, _>>();
            for trait_method in &trait_methods {
                let parameters = trait_method
                    .parameters
                    .iter()
                    .map(|parameter| {
                        (
                            parameter.name.clone(),
                            substitute_associated_type(
                                substitute_hir_type(
                                    self.ty(source_module, &parameter.ty, &scope),
                                    &substitutions,
                                ),
                                associated_types,
                            ),
                        )
                    })
                    .collect::<Vec<_>>();
                let return_type = substitute_associated_type(
                    substitute_hir_type(
                        self.ty(source_module, &trait_method.return_type, &scope),
                        &substitutions,
                    ),
                    associated_types,
                );
                let trait_method_id = SymbolId::new(
                    symbol.module.clone(),
                    format!("{}.{}", symbol.name, trait_method.name),
                );
                let default =
                    self.default_function(source_module, symbol, trait_method, &generics, &scope);
                if let Some(existing) = required
                    .iter_mut()
                    .find(|existing| existing.name == trait_method.name)
                {
                    if existing.parameters != parameters || existing.return_type != return_type {
                        self.error(
                            module,
                            trait_method.span.clone(),
                            "impl traits have incompatible methods with the same name",
                        );
                    } else {
                        existing.trait_methods.push(trait_method_id);
                        if let Some(default) = default
                            && !existing.defaults.contains(&default)
                        {
                            existing.defaults.push(default);
                        }
                    }
                } else {
                    required.push(RequiredMethod {
                        name: trait_method.name.clone(),
                        parameters,
                        return_type,
                        trait_methods: vec![trait_method_id],
                        defaults: default.into_iter().collect(),
                    });
                }
            }
        }

        let mut explicit = BTreeMap::<String, usize>::new();
        for (index, method) in methods.iter().enumerate() {
            if explicit.insert(method.name.clone(), index).is_some() {
                self.error(
                    module,
                    method.span.clone(),
                    format!("duplicate impl method `{}`", method.name),
                );
                continue;
            }
            let Some(required) = required
                .iter()
                .find(|required| required.name == method.name)
            else {
                self.error(
                    module,
                    method.span.clone(),
                    "impl method is not declared by its traits",
                );
                continue;
            };
            if method.return_type != required.return_type
                || method
                    .parameters
                    .iter()
                    .map(|parameter| (parameter.name.clone(), parameter.ty.clone()))
                    .collect::<Vec<_>>()
                    != required.parameters
            {
                self.error(
                    module,
                    method.span.clone(),
                    "impl method signature must exactly match its trait method",
                );
            }
        }

        let receiver_type = HirType::Named {
            symbol: impl_id.clone(),
            args: Vec::new(),
        };
        let mut selected = Vec::new();
        for required in required {
            let selected_implementation = if let Some(index) = explicit.get(&required.name) {
                let method = &methods[*index];
                HirSelectedImplementation::Explicit {
                    function: HirVerifiedFunction {
                        module: impl_id.module.clone(),
                        symbol: format!("{}.{}", impl_id.name, method.name),
                        verified_facade: format!(
                            "{}.{}.{}",
                            impl_id.module.as_string(),
                            impl_id.name,
                            method.name
                        ),
                    },
                }
            } else if required.defaults.len() == 1 {
                HirSelectedImplementation::Default {
                    function: required.defaults.into_iter().next().unwrap(),
                }
            } else {
                if required.defaults.is_empty() {
                    self.error(
                        module,
                        impl_span.clone(),
                        format!("impl is missing trait method `{}`", required.name),
                    );
                } else {
                    self.error(
                        module,
                        impl_span.clone(),
                        format!(
                            "ambiguous trait defaults for method `{}`; declare an explicit impl method",
                            required.name
                        ),
                    );
                }
                continue;
            };
            for trait_method in required.trait_methods {
                selected.push(HirSelectedMethod {
                    trait_method,
                    receiver_type: receiver_type.clone(),
                    selected: selected_implementation.clone(),
                });
            }
        }
        selected
    }
    fn associated_requirements(
        &mut self,
        traits: &[HirType],
    ) -> Vec<(SymbolId, String, Vec<HirType>)> {
        let mut requirements = Vec::new();
        for trait_ref in traits {
            let HirType::Named { symbol, args } = trait_ref else {
                continue;
            };
            let Some(module) = self
                .modules
                .iter()
                .position(|module| module == &symbol.module)
            else {
                continue;
            };
            let Some((generics, associated_types)) = self.parsed.sources[module]
                .syntax
                .declarations
                .iter()
                .find_map(|declaration| match declaration {
                    Declaration::Trait(value) if value.name == symbol.name => {
                        Some((value.generics.clone(), value.associated_types.clone()))
                    }
                    _ => None,
                })
            else {
                continue;
            };
            let substitutions = generics
                .iter()
                .map(|generic| match generic {
                    ast::GenericParam::Type { name, .. }
                    | ast::GenericParam::Const { name, .. } => name.clone(),
                })
                .zip(args.iter().cloned())
                .collect::<HashMap<_, _>>();
            let scope = GenericScope::from_declared(&generics);
            for associated in associated_types {
                requirements.push((
                    symbol.clone(),
                    associated.name,
                    associated
                        .bounds
                        .iter()
                        .map(|bound| {
                            substitute_hir_type(self.ty(module, bound, &scope), &substitutions)
                        })
                        .collect(),
                ));
            }
        }
        requirements
    }

    fn associated_assignment_satisfies(&mut self, value: &HirType, bound: &HirType) -> bool {
        value == bound
            || matches!(
                value,
                HirType::Named { symbol, .. }

                    if self.declarations.get(symbol) == Some(&OwnedDeclKind::Impl)
                        && self.declaration_traits(symbol).iter().any(|trait_ref| trait_ref == bound)
            )
    }
    fn resource_state_ref(
        &mut self,
        module: usize,
        path: &ast::QualifiedName,
    ) -> Option<(SymbolId, SymbolId)> {
        let (state, resource_path) = path.segments.split_last()?;
        if resource_path.is_empty() {
            self.error(
                module,
                path.span.clone(),
                "resource state must be qualified",
            );
            return None;
        }

        let resource_path = ast::QualifiedName::new(path.span.clone(), resource_path.to_vec());
        let resource = self.resolve(module, &resource_path, &path.span)?;
        if self.declarations.get(&resource) != Some(&OwnedDeclKind::Resource) {
            self.error(
                module,
                path.span.clone(),
                "transition state owner must be a resource",
            );
            return None;
        }
        let source = self
            .modules
            .iter()
            .position(|candidate| candidate == &resource.module)?;
        let declared = self.parsed.sources[source]
            .syntax
            .declarations
            .iter()
            .any(|declaration| {
                matches!(
                    declaration,
                    Declaration::Resource(value)
                        if value.name == resource.name
                            && value.states.iter().any(|candidate| candidate.name == *state)
                )
            });
        if !declared {
            self.error(
                module,
                path.span.clone(),
                "transition state must be declared by its resource",
            );
            return None;
        }
        Some((
            resource.clone(),
            SymbolId::new(
                resource.module.clone(),
                format!("{}.{}", resource.name, state),
            ),
        ))
    }
    fn resource_initial_state(&self, resource: &SymbolId) -> Option<SymbolId> {
        let module = self
            .modules
            .iter()
            .position(|module| module == &resource.module)?;
        self.parsed.sources[module]
            .syntax
            .declarations
            .iter()
            .find_map(|declaration| match declaration {
                Declaration::Resource(value) if value.name == resource.name => Some(SymbolId::new(
                    resource.module.clone(),
                    format!("{}.{}", resource.name, value.initial.name),
                )),
                _ => None,
            })
    }
    fn resource_edge_exists(&self, resource: &SymbolId, from: &SymbolId, to: &SymbolId) -> bool {
        self.modules
            .iter()
            .position(|module| module == &resource.module)
            .is_some_and(|module| {
                self.parsed.sources[module].syntax.declarations.iter().any(|declaration| {
                    matches!(
                        declaration,
                        Declaration::Resource(value)
                            if value.name == resource.name
                                && value.transitions.iter().any(|edge| {
                                    from.name == format!("{}.{}", resource.name, edge.from.name)
                                        && to.name == format!("{}.{}", resource.name, edge.to.name)
                                })
                    )
                })
            })
    }

    fn declaration(
        &mut self,
        module: usize,
        declaration: &Declaration,
        order: usize,
    ) -> HirDeclaration {
        let module_id = self.modules[module].clone();
        let id_for = |name: &str| SymbolId::new(module_id.clone(), name);
        let lower_annotations = |anns: &[ast::Annotation]| {
            anns.iter()
                .map(|a| HirAnnotation {
                    span: a.span.clone(),
                    name: a.name.clone(),
                    argument: a.argument.clone(),
                })
                .collect::<Vec<_>>()
        };

        match declaration {
            Declaration::ExternalType(value) => HirDeclaration::ExternalType(HirExternalType {
                id: id_for(&value.name),
                span: value.span.clone(),
                annotations: lower_annotations(&value.annotations),
                doc: value.doc.as_ref().map(|v| HirDoc {
                    span: v.span.clone(),
                    text: v.text.clone(),
                }),
                public: true,
                source_order: order,
            }),
            Declaration::Alias(value) => HirDeclaration::Alias(HirAlias {
                id: id_for(&value.name),
                span: value.span.clone(),
                annotations: lower_annotations(&value.annotations),
                doc: value.doc.as_ref().map(|v| HirDoc {
                    span: v.span.clone(),
                    text: v.text.clone(),
                }),
                generics: Vec::new(),
                target: self.ty(module, &value.target, &GenericScope::default()),
                public: true,
                source_order: order,
            }),
            Declaration::Newtype(value) => {
                let carrier = self.ty(module, &value.underlying, &GenericScope::default());
                let mut env = HashMap::new();
                env.insert(
                    "self".to_owned(),
                    (
                        SymbolId::new(module_id.clone(), "self"),
                        carrier.clone(),
                        false,
                    ),
                );
                HirDeclaration::Newtype(HirNewtype {
                    id: id_for(&value.name),
                    span: value.span.clone(),
                    annotations: lower_annotations(&value.annotations),
                    doc: value.doc.as_ref().map(|v| HirDoc {
                        span: v.span.clone(),
                        text: v.text.clone(),
                    }),
                    generics: Vec::new(),
                    carrier,
                    refinement: value
                        .where_clause
                        .as_ref()
                        .map(|v| self.expr(module, v, &env)),
                    public: true,
                    source_order: order,
                })
            }
            Declaration::Struct(value) => {
                let scope = GenericScope::from_declared(&value.generics);
                HirDeclaration::Struct(HirStruct {
                    id: id_for(&value.name),
                    span: value.span.clone(),
                    annotations: lower_annotations(&value.annotations),
                    doc: value.doc.as_ref().map(|v| HirDoc {
                        span: v.span.clone(),
                        text: v.text.clone(),
                    }),
                    generics: self.generics(module, &value.generics),
                    fields: value
                        .fields
                        .iter()
                        .enumerate()
                        .map(|(i, v)| self.field(module, v, &scope, i))
                        .collect(),
                    public: true,
                    source_order: order,
                })
            }
            Declaration::Enum(value) => {
                let scope = GenericScope::from_declared(&value.generics);
                let enum_id = id_for(&value.name);
                HirDeclaration::Enum(HirEnum {
                    id: enum_id.clone(),
                    span: value.span.clone(),
                    annotations: lower_annotations(&value.annotations),
                    doc: value.doc.as_ref().map(|v| HirDoc {
                        span: v.span.clone(),
                        text: v.text.clone(),
                    }),
                    generics: self.generics(module, &value.generics),
                    variants: value
                        .variants
                        .iter()
                        .enumerate()
                        .map(|(i, variant)| HirVariant {
                            symbol: SymbolId::new(
                                enum_id.module.clone(),
                                format!("{}.{}", enum_id.name, variant.name),
                            ),
                            span: variant.span.clone(),
                            name: variant.name.clone(),
                            fields: variant
                                .parameters
                                .iter()
                                .enumerate()
                                .map(|(j, p)| HirField {
                                    span: p.span.clone(),
                                    name: p.name.clone(),
                                    ty: self.ty(module, &p.ty, &scope),
                                    default: None,
                                    source_order: j,
                                })
                                .collect(),
                            source_order: i,
                        })
                        .collect(),
                    public: true,
                    source_order: order,
                })
            }
            Declaration::Trait(value) => {
                let scope = GenericScope::from_declared(&value.generics);
                let trait_id = id_for(&value.name);
                let mut associated_names = BTreeSet::new();
                let associated_types = value
                    .associated_types
                    .iter()
                    .enumerate()
                    .map(|(source_order, associated)| {
                        if !associated_names.insert(associated.name.clone()) {
                            self.error(
                                module,
                                associated.span.clone(),
                                format!("duplicate associated type `{}`", associated.name),
                            );
                        }
                        let bounds = associated
                            .bounds
                            .iter()
                            .map(|bound| self.ty(module, bound, &scope))
                            .collect::<Vec<_>>();
                        for bound in &bounds {
                            if !matches!(
                                bound,
                                HirType::Named { symbol, .. }
                                    if matches!(
                                        self.declarations.get(symbol),
                                        Some(OwnedDeclKind::Trait { .. })
                                    )
                            ) {
                                self.error(
                                    module,
                                    associated.span.clone(),
                                    "associated type bound must be a trait",
                                );
                            }
                        }
                        HirAssociatedType {
                            id: SymbolId::new(
                                trait_id.module.clone(),
                                format!("{}.{}", trait_id.name, associated.name),
                            ),
                            span: associated.span.clone(),
                            name: associated.name.clone(),
                            bounds,
                            source_order,
                        }
                    })
                    .collect::<Vec<_>>();
                HirDeclaration::Trait(HirTrait {
                    id: trait_id.clone(),
                    span: value.span.clone(),
                    annotations: lower_annotations(&value.annotations),
                    doc: value.doc.as_ref().map(|v| HirDoc {
                        span: v.span.clone(),
                        text: v.text.clone(),
                    }),
                    generics: self.generics(module, &value.generics),
                    methods: value
                        .methods
                        .iter()
                        .enumerate()
                        .map(|(i, method)| HirMethod {
                            id: SymbolId::new(
                                trait_id.module.clone(),
                                format!("{}.{}", trait_id.name, method.name),
                            ),
                            span: method.span.clone(),
                            doc: None,
                            generics: Vec::new(),
                            parameters: method
                                .parameters
                                .iter()
                                .enumerate()
                                .map(|(j, p)| self.parameter(module, p, &scope, j))
                                .collect(),
                            return_type: self.ty(module, &method.return_type, &scope),
                            contract: HirContract::default(),
                            default: self.default_function(
                                module,
                                &trait_id,
                                method,
                                &value.generics,
                                &scope,
                            ),
                            public: true,
                            source_order: i,
                        })
                        .collect(),
                    associated_types,
                    public: true,
                    source_order: order,
                })
            }
            Declaration::Impl(value) => {
                let id = id_for(&value.name);
                let traits = value
                    .traits
                    .iter()
                    .map(|trait_ref| self.ty(module, trait_ref, &GenericScope::default()))
                    .collect::<Vec<_>>();
                let mut trait_symbols = BTreeSet::new();
                for (source, trait_ref) in value.traits.iter().zip(&traits) {
                    match trait_ref {
                        HirType::Named { symbol, .. }
                            if matches!(
                                self.declarations.get(symbol),
                                Some(OwnedDeclKind::Trait { .. })
                            ) =>
                        {
                            if !trait_symbols.insert(symbol.clone()) {
                                self.error(module, source.span.clone(), "duplicate impl trait");
                            }
                        }
                        _ => self.error(module, source.span.clone(), "impl target must be a trait"),
                    }
                }
                let requirements = self.associated_requirements(&traits);
                let mut assigned_names = BTreeSet::new();
                let associated_types = value
                    .associated_types
                    .iter()
                    .enumerate()
                    .filter_map(|(source_order, assignment)| {
                        if !assigned_names.insert(assignment.name.clone()) {
                            self.error(
                                module,
                                assignment.span.clone(),
                                format!(
                                    "duplicate associated type assignment `{}`",
                                    assignment.name
                                ),
                            );
                            return None;
                        }
                        let candidates = requirements
                            .iter()
                            .filter(|(_, name, _)| name == &assignment.name)
                            .collect::<Vec<_>>();
                        if candidates.len() != 1 {
                            self.error(
                                module,
                                assignment.span.clone(),
                                if candidates.is_empty() {
                                    format!("unknown associated type `{}`", assignment.name)
                                } else {
                                    format!(
                                        "associated type assignment `{}` is ambiguous",
                                        assignment.name
                                    )
                                },
                            );
                            return None;
                        }
                        let (trait_id, name, bounds) = candidates[0];
                        let ty = self.ty(module, &assignment.ty, &GenericScope::default());
                        if associated_type_contains(&ty, trait_id, name) {
                            self.error(
                                module,
                                assignment.span.clone(),
                                "associated type assignment must not be cyclic",
                            );
                        }
                        for bound in bounds {
                            if !self.associated_assignment_satisfies(&ty, bound) {
                                self.error(
                                    module,
                                    assignment.span.clone(),
                                    "associated type assignment does not satisfy its bound",
                                );
                            }
                        }
                        Some(HirAssociatedTypeAssignment {
                            id: SymbolId::new(
                                id.module.clone(),
                                format!("{}.{}.{}", id.name, trait_id.name, name),
                            ),
                            span: assignment.span.clone(),
                            trait_id: trait_id.clone(),
                            name: name.clone(),
                            ty,
                            source_order,
                        })
                    })
                    .collect::<Vec<_>>();
                for (trait_id, name, _) in &requirements {
                    if !associated_types.iter().any(|assignment| {
                        assignment.trait_id == *trait_id && assignment.name == *name
                    }) {
                        self.error(
                            module,
                            value.span.clone(),
                            format!("impl is missing associated type assignment `{}`", name),
                        );
                    }
                }
                let state = value
                    .state
                    .iter()
                    .enumerate()
                    .map(|(i, field)| self.field(module, field, &GenericScope::default(), i))
                    .collect::<Vec<_>>();
                let mut state_names = BTreeSet::new();
                let mut optional = false;
                for field in &state {
                    if !state_names.insert(field.name.clone()) {
                        self.error(
                            module,
                            field.span.clone(),
                            format!("duplicate state field `{}`", field.name),
                        );
                    }
                    if field.default.is_some() {
                        optional = true;
                    } else if optional {
                        self.error(
                            module,
                            field.span.clone(),
                            "required state fields must precede default state fields",
                        );
                    }
                    if !self.state_type_allowed(&field.ty) {
                        self.error(
                            module,
                            field.span.clone(),
                            "state field type must be a closed immutable cott value type",
                        );
                    }
                }
                let mut self_env = HashMap::new();
                self_env.insert(
                    "self".into(),
                    (
                        SymbolId::new(id.module.clone(), "self"),
                        HirType::Named {
                            symbol: id.clone(),
                            args: vec![],
                        },
                        false,
                    ),
                );
                let invariants = value
                    .invariants
                    .iter()
                    .enumerate()
                    .map(|(clause_id, invariant)| {
                        let (guard, clause_env) = match &invariant.guard {
                            Some(guard) => {
                                let (guard, clause_env) =
                                    self.match_guard(module, guard, &self_env);
                                (Some(guard), clause_env)
                            }
                            None => (None, self_env.clone()),
                        };
                        let expression = self.expr(module, &invariant.condition, &clause_env);
                        if expression.ty != HirType::Primitive(PrimitiveType::Bool) {
                            self.error(
                                module,
                                invariant.condition.span.clone(),
                                "contract condition must be boolean",
                            );
                        }
                        HirImplInvariant {
                            clause_id: clause_id as u32,
                            span: invariant.span.clone(),
                            guard,
                            expression,
                        }
                    })
                    .collect();
                let initializer = value.initializer.as_ref().map(|init| {
                    let mut env = HashMap::new();
                    let parameters = init
                        .parameters
                        .iter()
                        .enumerate()
                        .map(|(i, parameter)| {
                            let parameter =
                                self.parameter(module, parameter, &GenericScope::default(), i);
                            env.insert(
                                parameter.name.clone(),
                                (
                                    SymbolId::new(id.module.clone(), parameter.name.clone()),
                                    parameter.ty.clone(),
                                    false,
                                ),
                            );
                            parameter
                        })
                        .collect::<Vec<_>>();
                    let mut last = None;
                    for parameter in &parameters {
                        let Some((index, field)) = state
                            .iter()
                            .enumerate()
                            .find(|(_, field)| field.name == parameter.name)
                        else {
                            self.error(
                                module,
                                parameter.span.clone(),
                                "init parameter must name a state field",
                            );
                            continue;
                        };
                        if last.is_some_and(|last| index <= last) || field.ty != parameter.ty {
                            self.error(
                                module,
                                parameter.span.clone(),
                                "init parameters must be an ordered exact state-field subsequence",
                            );
                        }
                        last = Some(index);
                    }
                    for field in state.iter().filter(|field| field.default.is_none()) {
                        if !parameters.iter().any(|parameter| {
                            parameter.name == field.name && parameter.ty == field.ty
                        }) {
                            self.error(
                                module,
                                field.span.clone(),
                                "init must include every required state field",
                            );
                        }
                    }
                    let mut ensures_env = env.clone();
                    ensures_env.extend(self_env.clone());
                    let (contract, doc) = self.contract(
                        module,
                        &init.clauses,
                        &ensures_env,
                        &HirType::Primitive(PrimitiveType::Unit),
                        None,
                        false,
                    );
                    HirImplInitializer {
                        span: init.span.clone(),
                        parameters,
                        doc,
                        contract,
                    }
                });
                if state.is_empty() && initializer.is_some() {
                    self.error(
                        module,
                        value.span.clone(),
                        "impl without state cannot declare init",
                    );
                } else if state.iter().any(|field| field.default.is_none()) && initializer.is_none()
                {
                    self.error(
                        module,
                        value.span.clone(),
                        "impl with required state fields requires init",
                    );
                }
                let methods = value
                    .methods
                    .iter()
                    .enumerate()
                    .map(|(source_order, method)| {
                        let mut env = self_env.clone();
                        let parameters = method
                            .parameters
                            .iter()
                            .enumerate()
                            .map(|(i, parameter)| {
                                let parameter =
                                    self.parameter(module, parameter, &GenericScope::default(), i);
                                env.insert(
                                    parameter.name.clone(),
                                    (
                                        SymbolId::new(id.module.clone(), parameter.name.clone()),
                                        parameter.ty.clone(),
                                        false,
                                    ),
                                );
                                parameter
                            })
                            .collect::<Vec<_>>();
                        let mut resource_transitions = Vec::new();
                        for (index, clause) in method.clauses.iter().enumerate() {
                            let ClauseKind::Transitions {
                                transitions: declared_transitions,
                            } = &clause.kind
                            else {
                                continue;
                            };
                            if method.clauses[..index].iter().any(|clause| {
                                !matches!(
                                    &clause.kind,
                                    ClauseKind::Documentation(_) | ClauseKind::Requires { .. }
                                )
                            }) {
                                self.error(
                                    module,
                                    clause.span.clone(),
                                    "transitions clause must follow requires clauses",
                                );
                            }
                            for transition in declared_transitions {
                                let field = &transition.field;
                                if let Some(state) =
                                    state.iter().find(|state| state.name == field.name)
                                {
                                    let HirType::Named {
                                        symbol: resource,
                                        args,
                                    } = &state.ty
                                    else {
                                        self.error(
                                            module,
                                            field.span.clone(),
                                            "transitions field must be a resource state field",
                                        );
                                        continue;
                                    };
                                    if !args.is_empty()
                                        || self.declarations.get(resource)
                                            != Some(&OwnedDeclKind::Resource)
                                    {
                                        self.error(
                                            module,
                                            field.span.clone(),
                                            "transitions field must be a resource state field",
                                        );
                                        continue;
                                    }
                                    let (from_resource, from_state) = self
                                        .resource_state_ref(module, &transition.from)
                                        .unwrap_or_else(|| {
                                            (
                                                resource.clone(),
                                                SymbolId::new(resource.module.clone(), "invalid"),
                                            )
                                        });
                                    let (to_resource, to_state) = self
                                        .resource_state_ref(module, &transition.to)
                                        .unwrap_or_else(|| {
                                            (
                                                resource.clone(),
                                                SymbolId::new(resource.module.clone(), "invalid"),
                                            )
                                        });
                                    if &from_resource != resource || &to_resource != resource {
                                        self.error(
                                            module,
                                            transition.span.clone(),
                                            "transition states must belong to the field resource",
                                        );
                                    }
                                    if !self.resource_edge_exists(resource, &from_state, &to_state)
                                    {
                                        self.error(
                                            module,
                                            transition.span.clone(),
                                            "transition must match a declared resource edge",
                                        );
                                    }
                                    resource_transitions.push(HirResourceTransition {
                                        span: transition.span.clone(),
                                        field: SymbolId::new(
                                            id.module.clone(),
                                            format!("{}.{}", id.name, field.name),
                                        ),
                                        resource: resource.clone(),
                                        from: from_state,
                                        to: to_state,
                                    });
                                } else {
                                    self.error(
                                        module,
                                        field.span.clone(),
                                        "transitions field must be impl state",
                                    );
                                }
                            }
                        }
                        let return_type =
                            self.ty(module, &method.return_type, &GenericScope::default());
                        let old_fields = state
                            .iter()
                            .map(|field| {
                                (
                                    format!("old:{}", field.name),
                                    (
                                        SymbolId::new(
                                            id.module.clone(),
                                            format!("{}.{}", id.name, field.name),
                                        ),
                                        field.ty.clone(),
                                        false,
                                    ),
                                )
                            })
                            .collect::<HashMap<_, _>>();
                        let (contract, doc) = self.contract(
                            module,
                            &method.clauses,
                            &env,
                            &return_type,
                            Some(&old_fields),
                            true,
                        );
                        let mut modifies = Vec::new();
                        for clause in &method.clauses {
                            if let ClauseKind::Modifies { fields } = &clause.kind {
                                if !modifies.is_empty() {
                                    self.error(
                                        module,
                                        clause.span.clone(),
                                        "method may have at most one modifies clause",
                                    );
                                }
                                for field in fields {
                                    if !state_names.contains(&field.name) {
                                        self.error(
                                            module,
                                            field.span.clone(),
                                            "modifies field must be impl state",
                                        );
                                    } else {
                                        let symbol = SymbolId::new(
                                            id.module.clone(),
                                            format!("{}.{}", id.name, field.name),
                                        );
                                        if modifies.contains(&symbol) {
                                            self.error(
                                                module,
                                                field.span.clone(),
                                                "duplicate modifies field",
                                            );
                                        } else {
                                            modifies.push(symbol);
                                        }
                                    }
                                }
                            }
                        }
                        for field in &modifies {
                            if state
                                .iter()
                                .find(|state| field.name == format!("{}.{}", id.name, state.name))
                                .is_some_and(|state| {
                                    matches!(
                                        &state.ty,
                                        HirType::Named { symbol, .. }
                                            if self.declarations.get(symbol)
                                                == Some(&OwnedDeclKind::Resource)
                                    )
                                })
                            {
                                self.error(
                                    module,
                                    method.span.clone(),
                                    "resource state fields must use transitions, not modifies",
                                );
                            }
                        }
                        for transition in &resource_transitions {
                            if modifies.contains(&transition.field) {
                                self.error(
                                    module,
                                    transition.span.clone(),
                                    "transitions field cannot overlap modifies",
                                );
                            }
                        }
                        HirImplMethod {
                            id: SymbolId::new(
                                id.module.clone(),
                                format!("{}.{}", id.name, method.name),
                            ),
                            span: method.span.clone(),
                            name: method.name.clone(),
                            self_span: method.self_span.clone(),
                            parameters,
                            return_type,
                            doc,
                            contract,
                            modifies,
                            source_order,
                            transitions: resource_transitions,
                        }
                    })
                    .collect::<Vec<_>>();
                let selected_methods = self.validate_impl_methods(
                    module,
                    &id,
                    &value.span,
                    &traits,
                    &associated_types,
                    &methods,
                );
                HirDeclaration::Impl(HirImpl {
                    id,
                    span: value.span.clone(),
                    annotations: lower_annotations(&value.annotations),
                    traits,
                    state,
                    invariants,
                    initializer,
                    methods,
                    associated_types,
                    selected_methods,
                    public: true,
                    source_order: order,
                })
            }
            Declaration::Resource(value) => {
                let id = id_for(&value.name);
                let mut names = BTreeMap::new();
                let terminal_names = value
                    .terminals
                    .iter()
                    .map(|terminal| terminal.name.clone())
                    .collect::<BTreeSet<_>>();
                let states = value
                    .states
                    .iter()
                    .enumerate()
                    .map(|(source_order, state)| {
                        let state_id =
                            SymbolId::new(id.module.clone(), format!("{}.{}", id.name, state.name));
                        if names.insert(state.name.clone(), state_id.clone()).is_some() {
                            self.error(
                                module,
                                state.span.clone(),
                                format!("duplicate resource state `{}`", state.name),
                            );
                        }
                        HirResourceState {
                            id: state_id,
                            span: state.span.clone(),
                            name: state.name.clone(),
                            terminal: terminal_names.contains(&state.name),
                            source_order,
                        }
                    })
                    .collect::<Vec<_>>();
                let initial = names.get(&value.initial.name).cloned().unwrap_or_else(|| {
                    self.error(
                        module,
                        value.initial.span.clone(),
                        "resource initial state must be declared",
                    );
                    SymbolId::new(id.module.clone(), format!("{}.invalid", id.name))
                });
                let mut terminal_states = BTreeSet::new();
                let mut terminals = Vec::new();
                for (source_order, terminal) in value.terminals.iter().enumerate() {
                    if !terminal_states.insert(terminal.name.clone()) {
                        self.error(
                            module,
                            terminal.span.clone(),
                            "duplicate resource terminal state",
                        );
                    }
                    let Some(state) = names.get(&terminal.name).cloned() else {
                        self.error(
                            module,
                            terminal.span.clone(),
                            "resource terminal state must be declared",
                        );
                        continue;
                    };
                    terminals.push(HirResourceTerminal {
                        state,
                        span: terminal.span.clone(),
                        source_order,
                    });
                }
                if terminal_states.is_empty() {
                    self.error(
                        module,
                        value.span.clone(),
                        "resource must declare at least one terminal state",
                    );
                }
                let mut edge_names = BTreeSet::new();
                let mut edges = Vec::new();
                for (source_order, edge) in value.transitions.iter().enumerate() {
                    let Some(from) = names.get(&edge.from.name).cloned() else {
                        self.error(
                            module,
                            edge.from.span.clone(),
                            "resource edge state must be declared",
                        );
                        continue;
                    };
                    let Some(to) = names.get(&edge.to.name).cloned() else {
                        self.error(
                            module,
                            edge.to.span.clone(),
                            "resource edge state must be declared",
                        );
                        continue;
                    };
                    if !edge_names.insert((from.clone(), to.clone())) {
                        self.error(module, edge.span.clone(), "duplicate resource edge");
                        continue;
                    }
                    edges.push(HirResourceEdge {
                        span: edge.span.clone(),
                        from,
                        to,
                        source_order,
                    });
                }
                let reachable = resource_reachable(&initial, &edges);
                for state in &states {
                    if !reachable.contains(&state.id) {
                        self.error(
                            module,
                            state.span.clone(),
                            "resource state must be reachable from its initial state",
                        );
                    }
                    let has_outgoing = edges.iter().any(|edge| edge.from == state.id);
                    if state.terminal && has_outgoing {
                        self.error(
                            module,
                            state.span.clone(),
                            "resource terminal state cannot have outgoing edges",
                        );
                    } else if !state.terminal && !has_outgoing {
                        self.error(
                            module,
                            state.span.clone(),
                            "resource non-terminal state must have an outgoing edge",
                        );
                    }
                }
                HirDeclaration::Resource(HirResource {
                    id,
                    span: value.span.clone(),
                    annotations: lower_annotations(&value.annotations),
                    doc: value.doc.as_ref().map(|doc| HirDoc {
                        span: doc.span.clone(),
                        text: doc.text.clone(),
                    }),
                    initial,
                    states,
                    terminals,
                    edges,
                    public: true,
                    source_order: order,
                })
            }
            Declaration::Const(value) => {
                let id = id_for(&value.name);
                let ty = self.ty(module, &value.ty, &GenericScope::default());
                let constant_value = self.constant_value(&id).unwrap_or(HirValue::Unit);
                HirDeclaration::Const(HirConst {
                    id,
                    span: value.span.clone(),
                    annotations: lower_annotations(&value.annotations),
                    doc: value.doc.as_ref().map(|v| HirDoc {
                        span: v.span.clone(),
                        text: v.text.clone(),
                    }),
                    ty,
                    value: constant_value,
                    public: true,
                    source_order: order,
                })
            }
            Declaration::Rule(value) => {
                let id = id_for(&value.name);
                let generic_scope = GenericScope::from_declared(&value.generics);
                let (base_symbol, base_type) = if let Some(base_ty) = &value.base {
                    let hir_base_type = self.ty(module, base_ty, &generic_scope);
                    let base_sym = self.resolve(module, &base_ty.path, &base_ty.span);
                    if let Some(ref sym) = base_sym {
                        if !matches!(self.declarations.get(sym), Some(OwnedDeclKind::Rule { .. })) {
                            self.error(
                                module,
                                base_ty.span.clone(),
                                format!("base `{}` is not a rule", base_ty.path.segments.join(".")),
                            );
                        }
                    }
                    (base_sym, Some(hir_base_type))
                } else {
                    (None, None)
                };

                let generics = self.generics(module, &value.generics);

                let mut declared_clauses = Vec::new();
                let mut doc = value.doc.as_ref().map(|v| HirDoc {
                    span: v.span.clone(),
                    text: v.text.clone(),
                });

                for (clause_id, clause) in value.clauses.iter().enumerate() {
                    let action = match clause.action {
                        ast::RuleClauseAction::Add => HirRuleClauseAction::Add,
                        ast::RuleClauseAction::Override => HirRuleClauseAction::Override,
                        ast::RuleClauseAction::Delete => HirRuleClauseAction::Delete,
                    };
                    match &clause.kind {
                        ClauseKind::Documentation(v) => {
                            if doc.is_none() {
                                doc = Some(HirDoc {
                                    span: v.span.clone(),
                                    text: v.text.clone(),
                                });
                            }
                        }
                        ClauseKind::Rule { name } => {
                            if let Some(rule_sym) = self.resolve(module, name, &name.span) {
                                if !matches!(
                                    self.declarations.get(&rule_sym),
                                    Some(OwnedDeclKind::Rule { .. })
                                ) {
                                    self.error(
                                        module,
                                        name.span.clone(),
                                        format!("`{}` is not a rule", name.segments.join(".")),
                                    );
                                } else if let Some(rule) = self.lowered_rules.get(&rule_sym) {
                                    for clause in &rule.contract.clauses {
                                        declared_clauses.push(HirRuleClause {
                                            clause_id: clause_id as u32,
                                            span: clause.span.clone(),
                                            action,
                                            kind: clause.kind.clone(),
                                        });
                                    }
                                }
                            }
                        }
                        ClauseKind::Requires { guard, condition } => {
                            let env = HashMap::new();
                            let (guard, env) = match guard {
                                Some(guard) => {
                                    let (guard, env) = self.match_guard(module, guard, &env);
                                    (Some(guard), env)
                                }
                                None => (None, env),
                            };
                            let expression = self.expr(module, condition, &env);
                            if expression.ty != HirType::Primitive(PrimitiveType::Bool) {
                                self.error(
                                    module,
                                    condition.span.clone(),
                                    "contract condition must be boolean",
                                );
                            }
                            declared_clauses.push(HirRuleClause {
                                clause_id: clause_id as u32,
                                span: clause.span.clone(),
                                action,
                                kind: HirClauseKind::Requires { guard, expression },
                            });
                        }
                        ClauseKind::Ensures { guard, condition } => {
                            let mut env = HashMap::new();
                            let result_type = guard
                                .as_ref()
                                .filter(|guard| {
                                    matches!(
                                        &guard.scrutinee.kind,
                                        ExprKind::Name(path) if path.segments.as_slice() == ["result"]
                                    )
                                })
                                .map(|guard| {
                                    self.infer_rule_pattern_type(
                                        module,
                                        &guard.pattern,
                                        &generic_scope.types,
                                    )
                                })
                                .unwrap_or(HirType::Primitive(PrimitiveType::Unit));
                            env.insert(
                                "result".to_owned(),
                                (
                                    SymbolId::new(self.modules[module].clone(), "result"),
                                    result_type,
                                    false,
                                ),
                            );
                            let (guard, env) = match guard {
                                Some(guard) => {
                                    let (guard, env) = self.match_guard(module, guard, &env);
                                    (Some(guard), env)
                                }
                                None => (None, env),
                            };
                            let expression = self.expr(module, condition, &env);
                            if expression.ty != HirType::Primitive(PrimitiveType::Bool) {
                                self.error(
                                    module,
                                    condition.span.clone(),
                                    "contract condition must be boolean",
                                );
                            }
                            declared_clauses.push(HirRuleClause {
                                clause_id: clause_id as u32,
                                span: clause.span.clone(),
                                action,
                                kind: HirClauseKind::Ensures { guard, expression },
                            });
                        }
                        ClauseKind::Error { error, guard, when } => {
                            let resolved = self.error_variant(module, error);
                            let env = HashMap::new();
                            let (guard, env) = match guard {
                                Some(guard) => {
                                    let (guard, env) = self.match_guard(module, guard, &env);
                                    (Some(guard), env)
                                }
                                None => (None, env),
                            };
                            let when = when.as_ref().map(|value| {
                                let expression = self.expr(module, value, &env);
                                if expression.ty != HirType::Primitive(PrimitiveType::Bool) {
                                    self.error(
                                        module,
                                        value.span.clone(),
                                        "contract condition must be boolean",
                                    );
                                }
                                expression
                            });
                            let variant = resolved.map(|(v, _)| v).unwrap_or_else(|| {
                                self.resolve(module, error, &error.span).unwrap_or_else(|| {
                                    SymbolId::new(
                                        self.modules[module].clone(),
                                        error.segments.join("."),
                                    )
                                })
                            });
                            declared_clauses.push(HirRuleClause {
                                clause_id: clause_id as u32,
                                span: clause.span.clone(),
                                action,
                                kind: HirClauseKind::Error {
                                    variant,
                                    priority: None,
                                    guard,
                                    when,
                                },
                            });
                        }
                        ClauseKind::Modifies { .. } | ClauseKind::Transitions { .. } => {}
                        ClauseKind::Effects { .. } => {}
                    }
                }

                let mut resolved_clauses: Vec<HirClause> = Vec::new();
                if let Some(ref base_sym) = base_symbol {
                    if let Some(base_rule) = self.lowered_rules.get(base_sym) {
                        resolved_clauses = base_rule.contract.clauses.clone();
                    }
                }

                for declared in &declared_clauses {
                    match declared.action {
                        HirRuleClauseAction::Add => {
                            resolved_clauses.push(HirClause {
                                clause_id: resolved_clauses.len() as u32,
                                span: declared.span.clone(),
                                kind: declared.kind.clone(),
                            });
                        }
                        HirRuleClauseAction::Override => {
                            let mut matched = false;
                            for target in resolved_clauses.iter_mut() {
                                if clauses_match(&target.kind, &declared.kind) {
                                    target.kind = declared.kind.clone();
                                    target.span = declared.span.clone();
                                    matched = true;
                                    break;
                                }
                            }
                            if !matched {
                                resolved_clauses.push(HirClause {
                                    clause_id: resolved_clauses.len() as u32,
                                    span: declared.span.clone(),
                                    kind: declared.kind.clone(),
                                });
                            }
                        }
                        HirRuleClauseAction::Delete => {
                            resolved_clauses
                                .retain(|target| !clauses_match(&target.kind, &declared.kind));
                        }
                    }
                }

                for (idx, clause) in resolved_clauses.iter_mut().enumerate() {
                    clause.clause_id = idx as u32;
                }

                let contract = HirContract {
                    clauses: resolved_clauses,
                    effects: Vec::new(),
                };

                let hir_rule = HirRule {
                    id: id.clone(),
                    span: value.span.clone(),
                    annotations: lower_annotations(&value.annotations),
                    doc,
                    generics,
                    base: base_symbol,
                    base_type,
                    declared_clauses,
                    contract,
                    public: true,
                    source_order: order,
                };
                HirDeclaration::Rule(hir_rule)
            }
            Declaration::Function(value) => {
                let scope = GenericScope::from_declared(&value.generics);
                let id = id_for(&value.name);
                let mut env = HashMap::new();
                let parameters = value
                    .parameters
                    .iter()
                    .enumerate()
                    .map(|(i, p)| {
                        let parameter = self.parameter(module, p, &scope, i);
                        env.insert(
                            p.name.clone(),
                            (
                                SymbolId::new(id.module.clone(), p.name.clone()),
                                parameter.ty.clone(),
                                false,
                            ),
                        );
                        parameter
                    })
                    .collect::<Vec<_>>();
                let return_type = self.ty(module, &value.return_type, &scope);
                let callable_kind = match value.callable_kind {
                    ast::CallableKind::Sync => HirCallableKind::Sync,
                    ast::CallableKind::Async => HirCallableKind::Async,
                };
                if callable_kind == HirCallableKind::Async
                    && matches!(
                        &return_type,
                        HirType::Iterator { .. }
                            | HirType::Generator { .. }
                            | HirType::Primitive(PrimitiveType::Never)
                    )
                {
                    self.error(
                        module,
                        value.return_type.span.clone(),
                        "async function cannot return Iterator, Generator, or Never",
                    );
                }
                let clauses: &[ast::Clause] = match &value.body {
                    FunctionBody::Clauses { clauses, .. } => clauses,
                    FunctionBody::Signature { .. } => &[],
                };
                let (contract, doc) =
                    self.contract(module, clauses, &env, &return_type, None, true);
                HirDeclaration::Function(HirFunction {
                    id,
                    span: value.span.clone(),
                    annotations: lower_annotations(&value.annotations),
                    doc,
                    generics: self.generics(module, &value.generics),
                    parameters,
                    return_type,
                    callable_kind,
                    contract,
                    body: None,
                    public: true,
                    source_order: order,
                })
            }
        }
    }
    fn module(&mut self, index: usize) -> HirModule {
        let source = self.parsed.sources[index].clone();
        let mut imports = Vec::new();
        for (source_order, use_decl) in source.syntax.uses.iter().enumerate() {
            let names = use_decl.names.clone().unwrap_or_else(|| {
                vec![use_decl.path.segments.last().cloned().unwrap_or_default()]
            });
            for name in names {
                if let Some(symbol) = self.imports[index].get(&name).cloned() {
                    imports.push(HirImport {
                        span: use_decl.span.clone(),
                        symbol,
                        name,
                        source_order,
                    });
                }
            }
        }
        let declarations = source
            .syntax
            .declarations
            .iter()
            .enumerate()
            .map(|(i, d)| self.declaration(index, d, i))
            .collect();
        HirModule {
            source: source.path,
            source_bytes: source.cst.source,
            id: self.modules[index].clone(),
            imports,
            declarations,
            source_order: index,
        }
    }
}
fn substitute_associated_type(ty: HirType, assignments: &[HirAssociatedTypeAssignment]) -> HirType {
    match ty {
        HirType::AssociatedProjection {
            base,
            trait_id,
            name,
        } => assignments
            .iter()
            .find(|assignment| assignment.trait_id == trait_id && assignment.name == name)
            .map(|assignment| assignment.ty.clone())
            .unwrap_or(HirType::AssociatedProjection {
                base: Box::new(substitute_associated_type(*base, assignments)),
                trait_id,
                name,
            }),
        HirType::Named { symbol, args } => HirType::Named {
            symbol,
            args: args
                .into_iter()
                .map(|arg| match arg {
                    HirGenericArg::Type(value) => {
                        HirGenericArg::Type(substitute_associated_type(value, assignments))
                    }
                    value => value,
                })
                .collect(),
        },
        HirType::List { item } => HirType::List {
            item: Box::new(substitute_associated_type(*item, assignments)),
        },
        HirType::Set { item } => HirType::Set {
            item: Box::new(substitute_associated_type(*item, assignments)),
        },
        HirType::Map { key, value } => HirType::Map {
            key: Box::new(substitute_associated_type(*key, assignments)),
            value: Box::new(substitute_associated_type(*value, assignments)),
        },
        HirType::Tuple { items } => HirType::Tuple {
            items: items
                .into_iter()
                .map(|item| substitute_associated_type(item, assignments))
                .collect(),
        },
        HirType::Array { item, length } => HirType::Array {
            item: Box::new(substitute_associated_type(*item, assignments)),
            length,
        },
        HirType::Option { item } => HirType::Option {
            item: Box::new(substitute_associated_type(*item, assignments)),
        },
        HirType::Iterator { item } => HirType::Iterator {
            item: Box::new(substitute_associated_type(*item, assignments)),
        },
        HirType::Generator {
            yield_type,
            send_type,
            return_type,
        } => HirType::Generator {
            yield_type: Box::new(substitute_associated_type(*yield_type, assignments)),
            send_type: Box::new(substitute_associated_type(*send_type, assignments)),
            return_type: Box::new(substitute_associated_type(*return_type, assignments)),
        },
        HirType::Factory { instance } => HirType::Factory {
            instance: Box::new(substitute_associated_type(*instance, assignments)),
        },
        HirType::Result { ok, error } => HirType::Result {
            ok: Box::new(substitute_associated_type(*ok, assignments)),
            error: Box::new(substitute_associated_type(*error, assignments)),
        },
        value => value,
    }
}

fn associated_type_contains(ty: &HirType, trait_id: &SymbolId, name: &str) -> bool {
    match ty {
        HirType::AssociatedProjection {
            base,
            trait_id: candidate,
            name: candidate_name,
        } => {
            (candidate == trait_id && candidate_name == name)
                || associated_type_contains(base, trait_id, name)
        }
        HirType::Named { args, .. } => args.iter().any(|argument| {
            matches!(argument, HirGenericArg::Type(ty) if associated_type_contains(ty, trait_id, name))
        }),
        HirType::List { item }
        | HirType::Set { item }
        | HirType::Option { item }
        | HirType::Iterator { item }
        | HirType::Factory { instance: item } => associated_type_contains(item, trait_id, name),
        HirType::Map { key, value } => {
            associated_type_contains(key, trait_id, name)
                || associated_type_contains(value, trait_id, name)
        }
        HirType::Tuple { items } => items
            .iter()
            .any(|item| associated_type_contains(item, trait_id, name)),
        HirType::Array { item, .. } => associated_type_contains(item, trait_id, name),
        HirType::Result { ok, error } => {
            associated_type_contains(ok, trait_id, name)
                || associated_type_contains(error, trait_id, name)
        }
        HirType::Generator {
            yield_type,
            send_type,
            return_type,
        } => {
            associated_type_contains(yield_type, trait_id, name)
                || associated_type_contains(send_type, trait_id, name)
                || associated_type_contains(return_type, trait_id, name)
        }
        HirType::Primitive(_) | HirType::TypeParameter { .. } | HirType::Buffer { .. } | HirType::Opaque { .. } => false,
    }
}

fn resource_reachable(initial: &SymbolId, edges: &[HirResourceEdge]) -> BTreeSet<SymbolId> {
    let mut reachable = BTreeSet::from([initial.clone()]);
    let mut pending = vec![initial.clone()];
    while let Some(state) = pending.pop() {
        for edge in edges.iter().filter(|edge| edge.from == state) {
            if reachable.insert(edge.to.clone()) {
                pending.push(edge.to.clone());
            }
        }
    }
    reachable
}

fn clauses_match(a: &HirClauseKind, b: &HirClauseKind) -> bool {
    match (a, b) {
        (
            HirClauseKind::Requires { guard: guard_a, .. },
            HirClauseKind::Requires { guard: guard_b, .. },
        )
        | (
            HirClauseKind::Ensures { guard: guard_a, .. },
            HirClauseKind::Ensures { guard: guard_b, .. },
        ) => guards_match(guard_a.as_ref(), guard_b.as_ref()),
        (
            HirClauseKind::Error {
                variant: var_a,
                guard: guard_a,
                ..
            },
            HirClauseKind::Error {
                variant: var_b,
                guard: guard_b,
                ..
            },
        ) => {
            (var_a == var_b || var_a.name == var_b.name)
                && guards_match(guard_a.as_ref(), guard_b.as_ref())
        }
        _ => false,
    }
}

fn guards_match(a: Option<&HirMatchGuard>, b: Option<&HirMatchGuard>) -> bool {
    match (a, b) {
        (Some(a), Some(b)) => patterns_match(&a.pattern, &b.pattern),
        (None, None) => true,
        _ => false,
    }
}

fn patterns_match(a: &HirPattern, b: &HirPattern) -> bool {
    match (&a.kind, &b.kind) {
        (HirPatternKind::Wildcard, HirPatternKind::Wildcard) => true,
        (
            HirPatternKind::Binding { name: name_a, .. },
            HirPatternKind::Binding { name: name_b, .. },
        ) => name_a == name_b,
        (
            HirPatternKind::Variant {
                symbol: sym_a,
                arguments: args_a,
            },
            HirPatternKind::Variant {
                symbol: sym_b,
                arguments: args_b,
            },
        ) => {
            (sym_a == sym_b || sym_a.name == sym_b.name)
                && args_a.len() == args_b.len()
                && args_a
                    .iter()
                    .zip(args_b.iter())
                    .all(|(x, y)| patterns_match(x, y))
        }
        _ => false,
    }
}

fn substitute_hir_type(ty: HirType, substitutions: &HashMap<String, HirGenericArg>) -> HirType {
    match ty {
        HirType::TypeParameter { name } => match substitutions.get(&name) {
            Some(HirGenericArg::Type(value)) => value.clone(),
            _ => HirType::TypeParameter { name },
        },
        HirType::AssociatedProjection {
            base,
            trait_id,
            name,
        } => HirType::AssociatedProjection {
            base: Box::new(substitute_hir_type(*base, substitutions)),
            trait_id,
            name,
        },
        HirType::Named { symbol, args } => HirType::Named {
            symbol,
            args: args
                .into_iter()
                .map(|arg| match arg {
                    HirGenericArg::Type(value) => {
                        HirGenericArg::Type(substitute_hir_type(value, substitutions))
                    }
                    HirGenericArg::Const(value) => {
                        HirGenericArg::Const(substitute_const_argument(value, substitutions))
                    }
                })
                .collect(),
        },
        HirType::List { item } => HirType::List {
            item: Box::new(substitute_hir_type(*item, substitutions)),
        },
        HirType::Set { item } => HirType::Set {
            item: Box::new(substitute_hir_type(*item, substitutions)),
        },
        HirType::Map { key, value } => HirType::Map {
            key: Box::new(substitute_hir_type(*key, substitutions)),
            value: Box::new(substitute_hir_type(*value, substitutions)),
        },
        HirType::Tuple { items } => HirType::Tuple {
            items: items
                .into_iter()
                .map(|item| substitute_hir_type(item, substitutions))
                .collect(),
        },
        HirType::Array { item, length } => HirType::Array {
            item: Box::new(substitute_hir_type(*item, substitutions)),
            length: substitute_const_argument(length, substitutions),
        },
        HirType::Buffer { length } => HirType::Buffer {
            length: substitute_const_argument(length, substitutions),
        },
        HirType::Option { item } => HirType::Option {
            item: Box::new(substitute_hir_type(*item, substitutions)),
        },
        HirType::Iterator { item } => HirType::Iterator {
            item: Box::new(substitute_hir_type(*item, substitutions)),
        },
        HirType::Generator {
            yield_type,
            send_type,
            return_type,
        } => HirType::Generator {
            yield_type: Box::new(substitute_hir_type(*yield_type, substitutions)),
            send_type: Box::new(substitute_hir_type(*send_type, substitutions)),
            return_type: Box::new(substitute_hir_type(*return_type, substitutions)),
        },
        HirType::Factory { instance } => HirType::Factory {
            instance: Box::new(substitute_hir_type(*instance, substitutions)),
        },
        HirType::Result { ok, error } => HirType::Result {
            ok: Box::new(substitute_hir_type(*ok, substitutions)),
            error: Box::new(substitute_hir_type(*error, substitutions)),
        },
        other => other,
    }
}

fn substitute_const_argument(
    value: HirConstArgument,
    substitutions: &HashMap<String, HirGenericArg>,
) -> HirConstArgument {
    match value {
        HirConstArgument::Parameter { name, ty } => substitutions
            .get(&name)
            .and_then(|value| match value {
                HirGenericArg::Const(value) => Some(value.clone()),
                HirGenericArg::Type(_) => None,
            })
            .unwrap_or(HirConstArgument::Parameter { name, ty }),
        HirConstArgument::Binary {
            op,
            left,
            right,
            ty,
        } => HirConstArgument::Binary {
            op,
            left: Box::new(substitute_const_argument(*left, substitutions)),
            right: Box::new(substitute_const_argument(*right, substitutions)),
            ty,
        },
        value => value,
    }
}

fn owned_module_path(root: &Path, source: &Path) -> Result<Vec<String>, String> {
    let relative = if source.is_absolute() {
        source
            .strip_prefix(root)
            .map_err(|_| "source path is outside the supplied source root".to_owned())?
    } else if !root.as_os_str().is_empty() {
        source.strip_prefix(root).unwrap_or(source)
    } else {
        source
    };
    let mut components = relative.components();
    let mut segments = Vec::new();
    while let Some(component) = components.next() {
        match component {
            Component::Normal(value) => {
                let value = value
                    .to_str()
                    .ok_or_else(|| "source path is not valid UTF-8".to_owned())?;
                if components.clone().next().is_none() {
                    let stem = value
                        .strip_suffix(".cott")
                        .ok_or_else(|| "source path must end in `.cott`".to_owned())?;
                    if stem.is_empty() {
                        return Err("source path has an empty module name".to_owned());
                    }
                    segments.push(stem.to_owned());
                } else {
                    segments.push(value.to_owned());
                }
            }
            Component::CurDir => {}
            Component::ParentDir | Component::RootDir | Component::Prefix(_) => {
                return Err("source path must be inside the supplied source root".to_owned());
            }
        }
    }
    if segments.is_empty() {
        Err("source path has no module components".to_owned())
    } else {
        Ok(segments)
    }
}

fn owned_type_paths(value: &ast::Type, out: &mut Vec<ast::QualifiedName>) {
    out.push(value.path.clone());
    for argument in &value.arguments {
        match &argument.kind {
            GenericArgKind::Type(inner) => owned_type_paths(inner, out),
            GenericArgKind::Const(value) => {
                owned_visit_const_expr(value, &mut |path| out.push(path.clone()))
            }
            GenericArgKind::Ambiguous { ty, value } => {
                owned_type_paths(ty, out);
                owned_visit_const_expr(value, &mut |path| out.push(path.clone()));
            }
        }
    }
}
fn owned_visit_type<F: FnMut(&ast::QualifiedName)>(value: &ast::Type, visit: &mut F) {
    visit(&value.path);
    for argument in &value.arguments {
        match &argument.kind {
            GenericArgKind::Type(inner) => owned_visit_type(inner, visit),
            GenericArgKind::Const(value) => owned_visit_const_expr(value, visit),
            GenericArgKind::Ambiguous { ty, value } => {
                owned_visit_type(ty, visit);
                owned_visit_const_expr(value, visit);
            }
        }
    }
}

fn owned_visit_expr<F: FnMut(&ast::QualifiedName)>(value: &ast::Expr, visit: &mut F) {
    match &value.kind {
        ExprKind::Name(path) => visit(path),
        ExprKind::Parenthesized(inner) | ExprKind::Unary { operand: inner, .. } => {
            owned_visit_expr(inner, visit)
        }
        ExprKind::Binary { left, right, .. } => {
            owned_visit_expr(left, visit);
            owned_visit_expr(right, visit);
        }
        ExprKind::Comparison { first, rest } => {
            owned_visit_expr(first, visit);
            for (_, expression) in rest {
                owned_visit_expr(expression, visit);
            }
        }
        ExprKind::Field { base, .. } => owned_visit_expr(base, visit),
        ExprKind::OldStateField { .. } | ExprKind::Literal(_) | ExprKind::Unit => {}
    }
}
fn owned_visit_pattern<F: FnMut(&ast::QualifiedName)>(value: &ast::Pattern, visit: &mut F) {
    if let PatternKind::Variant { path, arguments } = &value.kind {
        visit(path);
        for argument in arguments {
            owned_visit_pattern(argument, visit);
        }
    }
}
fn owned_visit_const_expr<F: FnMut(&ast::QualifiedName)>(value: &ast::ConstExpr, visit: &mut F) {
    match value {
        ast::ConstExpr::Expression(expression) => owned_visit_expr(expression, visit),
        ast::ConstExpr::Constructor { path, argument, .. } => {
            visit(path);
            owned_visit_const_expr(argument, visit);
        }
        ast::ConstExpr::Tuple { values, .. } | ast::ConstExpr::Array { values, .. } => {
            for value in values {
                owned_visit_const_expr(value, visit);
            }
        }
        ast::ConstExpr::Buffer { .. } => {}
    }
}
fn owned_visit_match_guard<F: FnMut(&ast::QualifiedName)>(value: &ast::MatchGuard, visit: &mut F) {
    owned_visit_expr(&value.scrutinee, visit);
    owned_visit_pattern(&value.pattern, visit);
}
fn owned_visit_clause_kind<F: FnMut(&ast::QualifiedName)>(kind: &ast::ClauseKind, visit: &mut F) {
    match kind {
        ast::ClauseKind::Requires { guard, condition }
        | ast::ClauseKind::Ensures { guard, condition } => {
            if let Some(guard) = guard {
                owned_visit_match_guard(guard, visit);
            }
            owned_visit_expr(condition, visit);
        }
        ast::ClauseKind::Error { error, guard, when } => {
            visit(error);
            if let Some(guard) = guard {
                owned_visit_match_guard(guard, visit);
            }
            if let Some(when) = when {
                owned_visit_expr(when, visit);
            }
        }
        ast::ClauseKind::Rule { name } => visit(name),
        ast::ClauseKind::Modifies { .. }
        | ast::ClauseKind::Transitions { .. }
        | ast::ClauseKind::Effects { .. }
        | ast::ClauseKind::Documentation(_) => {}
    }
}
fn owned_visit_clause<F: FnMut(&ast::QualifiedName)>(value: &ast::Clause, visit: &mut F) {
    owned_visit_clause_kind(&value.kind, visit);
}
fn owned_visit_parameter<F: FnMut(&ast::QualifiedName)>(value: &ast::Parameter, visit: &mut F) {
    owned_visit_type(&value.ty, visit);
}
fn owned_visit_declaration<F: FnMut(&ast::QualifiedName)>(
    declaration: &ast::Declaration,
    mut visit: F,
) {
    match declaration {
        Declaration::Alias(value) => owned_visit_type(&value.target, &mut visit),
        Declaration::ExternalType(_) => {}
        Declaration::Newtype(value) => {
            owned_visit_type(&value.underlying, &mut visit);
            if let Some(refinement) = &value.where_clause {
                owned_visit_expr(refinement, &mut visit);
            }
        }
        Declaration::Struct(value) => {
            for field in &value.fields {
                owned_visit_type(&field.ty, &mut visit);
                if let Some(default) = &field.default {
                    owned_visit_const_expr(default, &mut visit);
                }
            }
        }
        Declaration::Enum(value) => {
            for variant in &value.variants {
                for parameter in &variant.parameters {
                    owned_visit_parameter(parameter, &mut visit);
                }
            }
        }
        Declaration::Trait(value) => {
            for associated in &value.associated_types {
                for bound in &associated.bounds {
                    owned_visit_type(bound, &mut visit);
                }
            }
            for method in &value.methods {
                for parameter in &method.parameters {
                    owned_visit_parameter(parameter, &mut visit);
                }
                owned_visit_type(&method.return_type, &mut visit);
                if let Some(default) = &method.default {
                    visit(default);
                }
            }
        }
        Declaration::Impl(value) => {
            for trait_ref in &value.traits {
                owned_visit_type(trait_ref, &mut visit);
            }
            for associated in &value.associated_types {
                owned_visit_type(&associated.ty, &mut visit);
            }
            for field in &value.state {
                owned_visit_type(&field.ty, &mut visit);
                if let Some(default) = &field.default {
                    owned_visit_const_expr(default, &mut visit);
                }
            }
            for invariant in &value.invariants {
                if let Some(guard) = &invariant.guard {
                    owned_visit_match_guard(guard, &mut visit);
                }
                owned_visit_expr(&invariant.condition, &mut visit);
            }
            if let Some(init) = &value.initializer {
                for parameter in &init.parameters {
                    owned_visit_parameter(parameter, &mut visit);
                }
                for clause in &init.clauses {
                    owned_visit_clause(clause, &mut visit);
                }
            }
            for method in &value.methods {
                for parameter in &method.parameters {
                    owned_visit_parameter(parameter, &mut visit);
                }
                owned_visit_type(&method.return_type, &mut visit);
                for clause in &method.clauses {
                    owned_visit_clause(clause, &mut visit);
                }
            }
        }
        Declaration::Resource(_) => {}
        Declaration::Const(value) => {
            owned_visit_type(&value.ty, &mut visit);
            owned_visit_const_expr(&value.value, &mut visit);
        }
        Declaration::Rule(value) => {
            if let Some(base) = &value.base {
                owned_visit_type(base, &mut visit);
            }
            for clause in &value.clauses {
                owned_visit_clause_kind(&clause.kind, &mut visit);
            }
        }
        Declaration::Function(value) => {
            for parameter in &value.parameters {
                owned_visit_parameter(parameter, &mut visit);
            }
            owned_visit_type(&value.return_type, &mut visit);
            if let ast::FunctionBody::Clauses { clauses, .. } = &value.body {
                for clause in clauses {
                    owned_visit_clause(clause, &mut visit);
                }
            }
        }
    }
}
fn owned_qualified_owner(
    path: &ast::QualifiedName,
    declarations: &BTreeMap<SymbolId, usize>,
    parsed: &ParsedProject,
) -> Option<usize> {
    if path.segments.len() < 2 {
        return None;
    }
    let name = path.segments.last()?.clone();
    let module = ModuleId::new(path.segments[..path.segments.len() - 1].to_vec());
    let target = SymbolId::new(module, name.clone());
    if let Some(index) = declarations.get(&target) {
        return Some(*index);
    }
    if path.segments.len() < 3 {
        return None;
    }
    let enum_module = ModuleId::new(path.segments[..path.segments.len() - 2].to_vec());
    let enum_name = path.segments[path.segments.len() - 2].clone();
    let enum_symbol = SymbolId::new(enum_module, enum_name);
    let Some(index) = declarations.get(&enum_symbol).copied() else {
        return None;
    };
    parsed.sources[index]
        .syntax
        .declarations
        .iter()
        .any(|declaration| {
            matches!(
                declaration,

                Declaration::Enum(value)
                    if value.name == enum_symbol.name
                        && value
                            .variants
                            .iter()
                            .any(|variant| variant.name == name)
            )
        })
        .then_some(index)
}

fn owned_valid_snake(value: &str) -> bool {
    let mut chars = value.chars();
    matches!(chars.next(), Some('_' | 'a'..='z'))
        && chars.all(|ch| ch == '_' || ch.is_ascii_lowercase() || ch.is_ascii_digit())
        && value != "_"
}

fn owned_valid_type_name(value: &str) -> bool {
    let mut chars = value.chars();
    matches!(chars.next(), Some('A'..='Z')) && chars.all(|ch| ch.is_ascii_alphanumeric())
}

fn owned_shape_checks(parsed: &ParsedProject, errors: &mut Vec<ProjectDiagnostic>) {
    for source in &parsed.sources {
        let mut report = |span: Span, message: String| {
            errors.push(ProjectDiagnostic {
                path: source.path.clone(),
                diagnostic: Diagnostic::new(message, span),
            });
        };
        for declaration in &source.syntax.declarations {
            let (name, type_decl) = match declaration {
                Declaration::ExternalType(value) => (&value.name, true),
                Declaration::Alias(value) => (&value.name, true),
                Declaration::Newtype(value) => (&value.name, true),
                Declaration::Struct(value) => (&value.name, true),
                Declaration::Enum(value) => (&value.name, true),
                Declaration::Trait(value) => (&value.name, true),
                Declaration::Impl(value) => (&value.name, true),
                Declaration::Rule(value) => (&value.name, true),
                Declaration::Resource(value) => (&value.name, true),
                Declaration::Const(value) => (&value.name, false),
                Declaration::Function(value) => (&value.name, false),
            };
            if (type_decl && !owned_valid_type_name(name))
                || (!type_decl
                    && !owned_valid_snake(name)
                    && !(matches!(declaration, Declaration::Const(_))
                        && name
                            .chars()
                            .next()
                            .is_some_and(|ch| ch == '_' || ch.is_ascii_uppercase())))
            {
                report(
                    declaration.span().clone(),
                    format!("invalid name `{name}` for declaration"),
                );
            }
            if owned_primitive(name).is_some()
                || matches!(
                    name.as_str(),
                    "List"
                        | "Set"
                        | "Map"
                        | "Tuple"
                        | "Array"
                        | "Buffer"
                        | "Option"
                        | "Result"
                        | "Factory"
                        | "Iterator"
                        | "Generator"
                        | "Opaque"
                )
            {
                report(
                    declaration.span().clone(),
                    format!("declaration `{name}` collides with a prelude type"),
                );
            }
            let generics = match declaration {
                Declaration::Struct(value) => Some(&value.generics),
                Declaration::Enum(value) => Some(&value.generics),
                Declaration::Trait(value) => Some(&value.generics),
                Declaration::Rule(value) => Some(&value.generics),
                Declaration::Function(value) => Some(&value.generics),
                _ => None,
            };
            if let Some(generics) = generics {
                let mut names = BTreeSet::new();
                for generic in generics {
                    let (span, name) = match generic {
                        ast::GenericParam::Type { span, name, .. }
                        | ast::GenericParam::Const { span, name, .. } => (span, name),
                    };
                    if !names.insert(name) {
                        report(
                            span.clone(),
                            format!("duplicate generic parameter `{name}`"),
                        );
                    }
                }
            }
            match declaration {
                Declaration::Struct(value) => {
                    let mut names = BTreeSet::new();
                    for field in &value.fields {
                        if !owned_valid_snake(&field.name) {
                            report(
                                field.span.clone(),
                                format!("invalid field name `{}`", field.name),
                            );
                        }
                        if !names.insert(&field.name) {
                            report(
                                field.span.clone(),
                                format!("duplicate field `{}`", field.name),
                            );
                        }
                    }
                }
                Declaration::Enum(value) => {
                    let mut variants = BTreeSet::new();
                    for variant in &value.variants {
                        if !owned_valid_type_name(&variant.name) {
                            report(
                                variant.span.clone(),
                                format!("invalid enum variant name `{}`", variant.name),
                            );
                        }
                        if !variants.insert(&variant.name) {
                            report(
                                variant.span.clone(),
                                format!("duplicate enum variant `{}`", variant.name),
                            );
                        }
                        let mut parameters = BTreeSet::new();
                        for parameter in &variant.parameters {
                            if !owned_valid_snake(&parameter.name) {
                                report(
                                    parameter.span.clone(),
                                    format!("invalid variant parameter name `{}`", parameter.name),
                                );
                            }
                            if !parameters.insert(&parameter.name) {
                                report(
                                    parameter.span.clone(),
                                    format!("duplicate variant parameter `{}`", parameter.name),
                                );
                            }
                        }
                    }
                }
                Declaration::Function(value) => {
                    let mut parameters = BTreeSet::new();
                    for parameter in &value.parameters {
                        if !owned_valid_snake(&parameter.name) {
                            report(
                                parameter.span.clone(),
                                format!("invalid parameter name `{}`", parameter.name),
                            );
                        }
                        if !parameters.insert(&parameter.name) {
                            report(
                                parameter.span.clone(),
                                format!("duplicate parameter `{}`", parameter.name),
                            );
                        }
                    }
                }
                Declaration::Trait(value) => {
                    for method in &value.methods {
                        let mut parameters = BTreeSet::new();
                        for parameter in &method.parameters {
                            if !owned_valid_snake(&parameter.name) {
                                report(
                                    parameter.span.clone(),
                                    format!("invalid parameter name `{}`", parameter.name),
                                );
                            }
                            if !parameters.insert(&parameter.name) {
                                report(
                                    parameter.span.clone(),
                                    format!("duplicate parameter `{}`", parameter.name),
                                );
                            }
                        }
                    }
                }
                _ => {}
            }
        }
    }
}

fn owned_preflight(
    source_root: &Path,
    parsed: &ParsedProject,
) -> Result<(), Vec<ProjectDiagnostic>> {
    let mut errors = Vec::new();
    owned_shape_checks(parsed, &mut errors);
    let mut modules = Vec::new();
    for source in &parsed.sources {
        let module = ModuleId::new(source.syntax.module.path.segments.clone());
        if module
            .segments
            .iter()
            .any(|segment| !owned_valid_snake(segment))
        {
            errors.push(ProjectDiagnostic {
                path: source.path.clone(),
                diagnostic: Diagnostic::new(
                    "module path segments must use snake_case",
                    source.syntax.module.path.span.clone(),
                ),
            });
        }
        if module
            .segments
            .first()
            .is_some_and(|segment| segment == "core")
        {
            errors.push(ProjectDiagnostic {
                path: source.path.clone(),
                diagnostic: Diagnostic::new(
                    "module root `core` is reserved for the compiler prelude",
                    source.syntax.module.path.span.clone(),
                ),
            });
        }
        match owned_module_path(source_root, &source.path) {
            Ok(expected) if expected == module.segments => {}
            Ok(expected) => errors.push(ProjectDiagnostic {
                path: source.path.clone(),
                diagnostic: Diagnostic::new(
                    format!(
                        "module declaration `{}` does not match source path module `{}`",
                        module.as_string(),
                        expected.join(".")
                    ),
                    source.syntax.module.path.span.clone(),
                ),
            }),
            Err(message) => errors.push(ProjectDiagnostic {
                path: source.path.clone(),
                diagnostic: Diagnostic::new(message, source.syntax.module.span.clone()),
            }),
        }
        modules.push(module);
    }
    let mut module_by_id = BTreeMap::new();
    for (index, module) in modules.iter().enumerate() {
        if let Some(previous) = module_by_id.insert(module.clone(), index) {
            errors.push(ProjectDiagnostic {
                path: parsed.sources[index].path.clone(),
                diagnostic: Diagnostic::new(
                    format!(
                        "duplicate module `{}` (already defined by source {})",
                        module.as_string(),
                        previous + 1
                    ),
                    parsed.sources[index].syntax.module.span.clone(),
                ),
            });
        }
    }
    for (index, module) in modules.iter().enumerate() {
        for (longer_index, longer) in modules.iter().enumerate() {
            if index == longer_index || module == longer {
                continue;
            }
            if module.segments.len() < longer.segments.len()
                && longer.segments.starts_with(&module.segments)
            {
                errors.push(ProjectDiagnostic {
                    path: parsed.sources[longer_index].path.clone(),
                    diagnostic: Diagnostic::new(
                        format!(
                            "module `{}` is a strict prefix of `{}`",
                            module.as_string(),
                            longer.as_string()
                        ),
                        parsed.sources[longer_index].syntax.module.path.span.clone(),
                    ),
                });
            }
        }
    }
    let mut declarations = BTreeMap::<SymbolId, usize>::new();
    for (module_index, source) in parsed.sources.iter().enumerate() {
        let Some(module) = modules.get(module_index) else {
            continue;
        };
        let first_declaration = source.syntax.declarations.first().map(Declaration::span);
        for use_decl in &source.syntax.uses {
            if first_declaration
                .map(|span| use_decl.span.start > span.start)
                .unwrap_or(false)
            {
                errors.push(ProjectDiagnostic { path: source.path.clone(), diagnostic: Diagnostic::new("imports must form one contiguous block immediately after the module declaration", use_decl.span.clone()) });
            }
        }
        for declaration in &source.syntax.declarations {
            let name = match declaration {
                Declaration::ExternalType(v) => &v.name,
                Declaration::Alias(v) => &v.name,
                Declaration::Newtype(v) => &v.name,
                Declaration::Struct(v) => &v.name,
                Declaration::Enum(v) => &v.name,
                Declaration::Trait(v) => &v.name,
                Declaration::Impl(v) => &v.name,
                Declaration::Rule(v) => &v.name,
                Declaration::Resource(v) => &v.name,
                Declaration::Const(v) => &v.name,
                Declaration::Function(v) => &v.name,
            };
            let id = SymbolId::new(module.clone(), name.clone());
            if declarations.insert(id.clone(), module_index).is_some() {
                errors.push(ProjectDiagnostic {
                    path: source.path.clone(),
                    diagnostic: Diagnostic::new(
                        format!("duplicate declaration `{}`", id.as_string()),
                        declaration.span().clone(),
                    ),
                });
            }
        }
    }
    let mut type_dependencies = BTreeMap::<SymbolId, BTreeSet<SymbolId>>::new();
    for (module_index, source) in parsed.sources.iter().enumerate() {
        let Some(module) = modules.get(module_index) else {
            continue;
        };
        for declaration in &source.syntax.declarations {
            let (name, types): (&String, Vec<&ast::Type>) =
                match declaration {
                    Declaration::Alias(v) => (&v.name, vec![&v.target]),
                    Declaration::Newtype(v) => (&v.name, vec![&v.underlying]),
                    Declaration::Struct(v) => (&v.name, v.fields.iter().map(|f| &f.ty).collect()),
                    Declaration::Enum(v) => (
                        &v.name,
                        v.variants
                            .iter()
                            .flat_map(|v| v.parameters.iter().map(|p| &p.ty))
                            .collect(),
                    ),
                    Declaration::Impl(v) => (
                        &v.name,
                        v.traits
                            .iter()
                            .chain(v.state.iter().map(|field| &field.ty))
                            .chain(v.initializer.iter().flat_map(|init| {
                                init.parameters.iter().map(|parameter| &parameter.ty)
                            }))
                            .chain(v.methods.iter().flat_map(|method| {
                                method
                                    .parameters
                                    .iter()
                                    .map(|parameter| &parameter.ty)
                                    .chain(std::iter::once(&method.return_type))
                            }))
                            .collect(),
                    ),
                    Declaration::Resource(v) => (&v.name, Vec::new()),
                    Declaration::Rule(v) => (&v.name, v.base.as_ref().into_iter().collect()),
                    _ => continue,
                };
            let current = SymbolId::new(module.clone(), name.clone());
            let mut paths = Vec::new();
            for ty in types {
                owned_type_paths(ty, &mut paths);
            }
            for path in paths {
                let target_name = path.segments.last().cloned().unwrap_or_default();
                let target = if path.segments.len() == 1 {
                    SymbolId::new(module.clone(), target_name)
                } else {
                    SymbolId::new(
                        ModuleId::new(path.segments[..path.segments.len() - 1].to_vec()),
                        target_name,
                    )
                };
                if declarations.contains_key(&target) {
                    type_dependencies
                        .entry(current.clone())
                        .or_default()
                        .insert(target);
                }
            }
        }
    }
    fn visit_type_cycle(
        symbol: &SymbolId,
        deps: &BTreeMap<SymbolId, BTreeSet<SymbolId>>,
        state: &mut HashMap<SymbolId, u8>,
        declarations: &BTreeMap<SymbolId, usize>,
        parsed: &ParsedProject,
        errors: &mut Vec<ProjectDiagnostic>,
    ) {
        if state.get(symbol) == Some(&2) {
            return;
        }
        if state.get(symbol) == Some(&1) {
            if let Some(index) = declarations.get(symbol) {
                errors.push(ProjectDiagnostic {
                    path: parsed.sources[*index].path.clone(),
                    diagnostic: Diagnostic::new(
                        format!("cyclic type reference involving `{}`", symbol.as_string()),
                        parsed.sources[*index].syntax.module.span.clone(),
                    ),
                });
            }
            return;
        }
        state.insert(symbol.clone(), 1);
        if let Some(children) = deps.get(symbol) {
            for child in children {
                visit_type_cycle(child, deps, state, declarations, parsed, errors);
            }
        }
        state.insert(symbol.clone(), 2);
    }
    let mut type_state = HashMap::new();
    for symbol in type_dependencies.keys() {
        visit_type_cycle(
            symbol,
            &type_dependencies,
            &mut type_state,
            &declarations,
            parsed,
            &mut errors,
        );
    }
    let mut imports = vec![BTreeMap::<String, SymbolId>::new(); parsed.sources.len()];
    let mut dependencies = vec![BTreeSet::new(); parsed.sources.len()];
    for (module_index, source) in parsed.sources.iter().enumerate() {
        let Some(current) = modules.get(module_index) else {
            continue;
        };
        for use_decl in &source.syntax.uses {
            let (target_module, names) = match &use_decl.names {
                Some(names) => (ModuleId::new(use_decl.path.segments.clone()), names.clone()),
                None if use_decl.path.segments.len() >= 2 => (
                    ModuleId::new(
                        use_decl.path.segments[..use_decl.path.segments.len() - 1].to_vec(),
                    ),
                    vec![use_decl.path.segments.last().cloned().unwrap_or_default()],
                ),
                None => {
                    errors.push(ProjectDiagnostic {
                        path: source.path.clone(),
                        diagnostic: Diagnostic::new(
                            "a single import must name a public type declaration",
                            use_decl.span.clone(),
                        ),
                    });
                    continue;
                }
            };
            let Some(&target_index) = module_by_id.get(&target_module) else {
                errors.push(ProjectDiagnostic {
                    path: source.path.clone(),
                    diagnostic: Diagnostic::new(
                        format!("unknown imported module `{}`", target_module.as_string()),
                        use_decl.span.clone(),
                    ),
                });
                continue;
            };
            dependencies[module_index].insert(target_index);
            for name in names {
                let target = SymbolId::new(target_module.clone(), name.clone());
                if !declarations.contains_key(&target) {
                    errors.push(ProjectDiagnostic {
                        path: source.path.clone(),
                        diagnostic: Diagnostic::new(
                            format!("unknown imported declaration `{}`", target.as_string()),
                            use_decl.span.clone(),
                        ),
                    });
                } else if declarations
                    .get(&SymbolId::new(current.clone(), name.clone()))
                    .is_some()
                {
                    errors.push(ProjectDiagnostic {
                        path: source.path.clone(),
                        diagnostic: Diagnostic::new(
                            format!("import `{name}` collides with a local declaration"),
                            use_decl.span.clone(),
                        ),
                    });
                } else if imports[module_index].insert(name.clone(), target).is_some() {
                    errors.push(ProjectDiagnostic {
                        path: source.path.clone(),
                        diagnostic: Diagnostic::new(
                            format!("duplicate import `{name}`"),
                            use_decl.span.clone(),
                        ),
                    });
                }
            }
        }
    }
    // Qualified references own their dependency even without a `use` declaration.
    for (module_index, source) in parsed.sources.iter().enumerate() {
        for declaration in &source.syntax.declarations {
            owned_visit_declaration(declaration, |path| {
                if let Some(owner) = owned_qualified_owner(path, &declarations, parsed) {
                    if owner != module_index {
                        dependencies[module_index].insert(owner);
                    }
                }
            });
        }
    }
    fn visit(
        index: usize,
        dependencies: &[BTreeSet<usize>],
        state: &mut [u8],
        parsed: &ParsedProject,
        errors: &mut Vec<ProjectDiagnostic>,
    ) {
        if state[index] == 2 {
            return;
        }
        if state[index] == 1 {
            errors.push(ProjectDiagnostic {
                path: parsed.sources[index].path.clone(),
                diagnostic: Diagnostic::new(
                    "cyclic module import/reference dependency",
                    parsed.sources[index].syntax.module.span.clone(),
                ),
            });
            return;
        }
        state[index] = 1;
        for &dependency in &dependencies[index] {
            visit(dependency, dependencies, state, parsed, errors);
        }
        state[index] = 2;
    }
    let mut state = vec![0; parsed.sources.len()];
    for index in 0..parsed.sources.len() {
        visit(index, &dependencies, &mut state, parsed, &mut errors);
    }
    if errors.is_empty() {
        Ok(())
    } else {
        errors.sort_by_key(|error| {
            (
                parsed
                    .sources
                    .iter()
                    .position(|source| source.path == error.path)
                    .unwrap_or(usize::MAX),
                error.diagnostic.span.start,
                error.diagnostic.span.end,
            )
        });
        Err(errors)
    }
}

fn validate_hash_stable_keys(modules: &[HirModule], errors: &mut Vec<ProjectDiagnostic>) {
    fn declaration<'a>(modules: &'a [HirModule], symbol: &SymbolId) -> Option<&'a HirDeclaration> {
        modules
            .iter()
            .flat_map(|module| &module.declarations)
            .find(|declaration| declaration.id() == symbol)
    }

    fn stable(ty: &HirType, modules: &[HirModule], visiting: &mut BTreeSet<SymbolId>) -> bool {
        match ty {
            HirType::Primitive(
                PrimitiveType::Bool
                | PrimitiveType::I8
                | PrimitiveType::I16
                | PrimitiveType::I32
                | PrimitiveType::I64
                | PrimitiveType::U8
                | PrimitiveType::U16
                | PrimitiveType::U32
                | PrimitiveType::U64
                | PrimitiveType::Str
                | PrimitiveType::Bytes
                | PrimitiveType::Path,
            ) => true,
            HirType::Tuple { items } => items.iter().all(|item| stable(item, modules, visiting)),
            HirType::Array { item, .. } => stable(item, modules, visiting),
            HirType::Buffer { .. } => true,
            HirType::Named { symbol, args } if visiting.insert(symbol.clone()) => {
                let result = match declaration(modules, symbol) {
                    Some(HirDeclaration::Newtype(value)) => {
                        let substitutions = value
                            .generics
                            .iter()
                            .map(|generic| generic.name().to_owned())
                            .zip(args.iter().cloned())
                            .collect::<HashMap<_, _>>();
                        stable(
                            &substitute_hir_type(value.carrier.clone(), &substitutions),
                            modules,
                            visiting,
                        )
                    }
                    Some(HirDeclaration::Enum(value)) => value
                        .variants
                        .iter()
                        .all(|variant| variant.fields.is_empty()),
                    _ => false,
                };
                visiting.remove(symbol);
                result
            }
            HirType::Factory { .. } => false,
            _ => false,
        }
    }

    fn visit(
        ty: &HirType,
        modules: &[HirModule],
        path: &Path,
        span: &Span,
        errors: &mut Vec<ProjectDiagnostic>,
    ) {
        match ty {
            HirType::Set { item } => {
                if !stable(item, modules, &mut BTreeSet::new()) {
                    errors.push(ProjectDiagnostic {
                        path: path.to_path_buf(),
                        diagnostic: Diagnostic::new(
                            "Set item type must be hash-stable",
                            span.clone(),
                        ),
                    });
                }
                visit(item, modules, path, span, errors);
            }
            HirType::Map { key, value } => {
                if !stable(key, modules, &mut BTreeSet::new()) {
                    errors.push(ProjectDiagnostic {
                        path: path.to_path_buf(),
                        diagnostic: Diagnostic::new(
                            "Map key type must be hash-stable",
                            span.clone(),
                        ),
                    });
                }
                visit(key, modules, path, span, errors);
                visit(value, modules, path, span, errors);
            }
            HirType::Factory { instance } => visit(instance, modules, path, span, errors),
            HirType::List { item } | HirType::Option { item } | HirType::Iterator { item } => {
                visit(item, modules, path, span, errors);
            }
            HirType::Tuple { items } => {
                for item in items {
                    visit(item, modules, path, span, errors);
                }
            }
            HirType::Array { item, .. } => visit(item, modules, path, span, errors),
            HirType::Buffer { .. } => {}
            HirType::Generator {
                yield_type,
                send_type,
                return_type,
            } => {
                visit(yield_type, modules, path, span, errors);
                visit(send_type, modules, path, span, errors);
                visit(return_type, modules, path, span, errors);
            }
            HirType::Result { ok, error } => {
                visit(ok, modules, path, span, errors);
                visit(error, modules, path, span, errors);
            }
            HirType::AssociatedProjection { base, .. } => {
                visit(base, modules, path, span, errors);
            }
            HirType::Named { args, .. } => {
                for argument in args {
                    if let HirGenericArg::Type(argument) = argument {
                        visit(argument, modules, path, span, errors);
                    }
                }
            }
            _ => {}
        }
    }

    for module in modules {
        for declaration in &module.declarations {
            let span = declaration.span();
            let mut types = Vec::new();
            match declaration {
                HirDeclaration::ExternalType(_) => {}
                HirDeclaration::Alias(value) => types.push(&value.target),
                HirDeclaration::Newtype(value) => types.push(&value.carrier),
                HirDeclaration::Struct(value) => {
                    types.extend(value.fields.iter().map(|field| &field.ty));
                }
                HirDeclaration::Enum(value) => {
                    types.extend(
                        value
                            .variants
                            .iter()
                            .flat_map(|variant| &variant.fields)
                            .map(|field| &field.ty),
                    );
                }
                HirDeclaration::Trait(value) => {
                    for method in &value.methods {
                        types.extend(method.parameters.iter().map(|parameter| &parameter.ty));
                        types.push(&method.return_type);
                    }
                    for associated in &value.associated_types {
                        types.extend(&associated.bounds);
                    }
                }
                HirDeclaration::Impl(value) => {
                    types.extend(value.traits.iter());
                    types.extend(value.state.iter().map(|field| &field.ty));
                    if let Some(initializer) = &value.initializer {
                        types.extend(initializer.parameters.iter().map(|parameter| &parameter.ty));
                    }
                    for method in &value.methods {
                        types.extend(method.parameters.iter().map(|parameter| &parameter.ty));
                        types.push(&method.return_type);
                    }
                    types.extend(
                        value
                            .associated_types
                            .iter()
                            .map(|associated| &associated.ty),
                    );
                }
                HirDeclaration::Const(value) => types.push(&value.ty),
                HirDeclaration::Function(value) => {
                    types.extend(value.parameters.iter().map(|parameter| &parameter.ty));
                    types.push(&value.return_type);
                }
                HirDeclaration::Rule(value) => {
                    if let Some(base_type) = &value.base_type {
                        types.push(base_type);
                    }
                }
                HirDeclaration::Resource(_) => {}
            }
            for ty in types {
                visit(ty, modules, &module.source, span, errors);
            }
        }
    }
}

fn validate_effects(
    modules: &[HirModule],
    custom: &BTreeSet<String>,
    errors: &mut Vec<ProjectDiagnostic>,
) {
    let builtins = [
        "file.read",
        "file.write",
        "network",
        "database.read",
        "database.write",
        "clock",
        "random",
        "process.exit",
    ];
    for module in modules {
        let contracts = module
            .declarations
            .iter()
            .flat_map(|declaration| match declaration {
                HirDeclaration::Function(value) => vec![&value.contract],
                HirDeclaration::Trait(value) => value
                    .methods
                    .iter()
                    .map(|method| &method.contract)
                    .collect(),
                HirDeclaration::Impl(value) => value
                    .initializer
                    .iter()
                    .map(|initializer| &initializer.contract)
                    .chain(value.methods.iter().map(|method| &method.contract))
                    .collect(),
                HirDeclaration::Rule(value) => vec![&value.contract],
                _ => Vec::new(),
            });
        for contract in contracts {
            let mut seen = BTreeSet::new();
            for effect in &contract.effects {
                if !builtins.contains(&effect.key.as_str()) && !custom.contains(&effect.key) {
                    errors.push(ProjectDiagnostic {
                        path: module.source.clone(),
                        diagnostic: Diagnostic::new(
                            format!("unknown effect `{}`", effect.key),
                            effect.span.clone(),
                        ),
                    });
                }
                if !seen.insert(&effect.key) {
                    errors.push(ProjectDiagnostic {
                        path: module.source.clone(),
                        diagnostic: Diagnostic::new(
                            format!("duplicate effect `{}`", effect.key),
                            effect.span.clone(),
                        ),
                    });
                }
            }
        }
    }
}

pub fn lower(
    source_root: &Path,
    parsed: ParsedProject,
) -> Result<HirProject, Vec<ProjectDiagnostic>> {
    lower_with_effects(source_root, parsed, &BTreeSet::new())
}

/// Lower with the custom effect keys declared by the project manifest.
pub fn lower_with_effects(
    source_root: &Path,
    parsed: ParsedProject,
    custom_effects: &BTreeSet<String>,
) -> Result<HirProject, Vec<ProjectDiagnostic>> {
    let mut errors = owned_preflight(source_root, &parsed)
        .err()
        .unwrap_or_default();
    let mut lowerer = OwnedLower::new(&parsed);
    let modules = (0..parsed.sources.len())
        .map(|index| lowerer.module(index))
        .collect::<Vec<_>>();
    errors.extend(lowerer.errors);
    if errors.is_empty() {
        validate_hash_stable_keys(&modules, &mut errors);
    }
    if errors.is_empty() {
        validate_effects(&modules, custom_effects, &mut errors);
    }
    if errors.is_empty() {
        Ok(HirProject::new(modules))
    } else {
        errors.sort_by_key(|error| {
            (
                parsed
                    .sources
                    .iter()
                    .position(|source| source.path == error.path)
                    .unwrap_or(usize::MAX),
                error.diagnostic.span.start,
                error.diagnostic.span.end,
            )
        });
        Err(errors)
    }
}
