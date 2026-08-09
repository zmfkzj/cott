//! Owned, target-independent high-level intermediate representation.
//!
//! Lowering and structural validation live entirely in this module.

use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::path::{Component, Path, PathBuf};

use crate::ast::{
    self, BinaryOp, ClauseKind, CompareOp, ConstExpr, Declaration, Expr, ExprKind, FunctionBody,
    LiteralKind, PatternKind, TypeArgKind, UnaryOp,
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
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum OwnedDeclKind {
    Type { generics: usize },
    Enum,
    Const,
    Function,
    Trait,
}

struct OwnedLower<'a> {
    parsed: &'a ParsedProject,
    modules: Vec<ModuleId>,
    declarations: HashMap<SymbolId, OwnedDeclKind>,
    imports: Vec<HashMap<String, SymbolId>>,
    errors: Vec<ProjectDiagnostic>,
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
                    Declaration::Alias(v) => (&v.name, OwnedDeclKind::Type { generics: 0 }),
                    Declaration::Newtype(v) => (&v.name, OwnedDeclKind::Type { generics: 0 }),
                    Declaration::Struct(v) => (
                        &v.name,
                        OwnedDeclKind::Type {
                            generics: v.generics.len(),
                        },
                    ),
                    Declaration::Enum(v) => (&v.name, OwnedDeclKind::Enum),
                    Declaration::Trait(v) => (&v.name, OwnedDeclKind::Trait),
                    Declaration::Const(v) => (&v.name, OwnedDeclKind::Const),
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

    fn resolve(
        &mut self,
        module: usize,
        path: &ast::QualifiedName,
        span: &Span,
    ) -> Option<SymbolId> {
        let name = path.segments.last()?.clone();
        let symbol = if path.segments.len() == 1 {
            self.imports[module].get(&name).cloned().or_else(|| {
                let candidate = SymbolId::new(self.modules[module].clone(), name.clone());
                self.declarations
                    .contains_key(&candidate)
                    .then_some(candidate)
            })
        } else {
            let candidate = SymbolId::new(
                ModuleId::new(path.segments[..path.segments.len() - 1].to_vec()),
                name.clone(),
            );
            self.declarations
                .contains_key(&candidate)
                .then_some(candidate)
        };
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
}

impl<'a> OwnedLower<'a> {
    fn ty(&mut self, module: usize, value: &ast::Type, generics: &HashSet<String>) -> HirType {
        let name = value.path.segments.last().cloned().unwrap_or_default();
        if value.path.segments.len() == 1 {
            if generics.contains(&name) {
                return HirType::TypeParameter { name };
            }
            if let Some(primitive) = owned_primitive(&name) {
                self.arity(module, value, 0, &name);
                return HirType::Primitive(primitive);
            }
            let expected = match name.as_str() {
                "List" | "Set" | "Option" => Some(1),
                "Map" | "Tuple2" | "Result" => Some(2),
                _ => None,
            };
            if let Some(expected) = expected {
                self.arity(module, value, expected, &name);
                let args = value
                    .arguments
                    .iter()
                    .map(|argument| match &argument.kind {
                        TypeArgKind::Type(inner) => self.ty(module, inner, generics),
                        TypeArgKind::String(_) => {
                            self.error(
                                module,
                                argument.span.clone(),
                                "string type arguments are unsupported",
                            );
                            HirType::Opaque {
                                tag: "string-type-argument".into(),
                            }
                        }
                    })
                    .collect::<Vec<_>>();
                return match name.as_str() {
                    "List" => HirType::List {
                        item: Box::new(args.into_iter().next().unwrap_or_else(|| {
                            HirType::Opaque {
                                tag: "missing".into(),
                            }
                        })),
                    },
                    "Set" => HirType::Set {
                        item: Box::new(args.into_iter().next().unwrap_or_else(|| {
                            HirType::Opaque {
                                tag: "missing".into(),
                            }
                        })),
                    },
                    "Option" => HirType::Option {
                        item: Box::new(args.into_iter().next().unwrap_or_else(|| {
                            HirType::Opaque {
                                tag: "missing".into(),
                            }
                        })),
                    },
                    "Map" => HirType::Map {
                        key: Box::new(args.first().cloned().unwrap_or_else(|| HirType::Opaque {
                            tag: "missing".into(),
                        })),
                        value: Box::new(args.get(1).cloned().unwrap_or_else(|| HirType::Opaque {
                            tag: "missing".into(),
                        })),
                    },
                    "Tuple2" => HirType::Tuple2 {
                        first: Box::new(args.first().cloned().unwrap_or_else(|| HirType::Opaque {
                            tag: "missing".into(),
                        })),
                        second: Box::new(args.get(1).cloned().unwrap_or_else(|| HirType::Opaque {
                            tag: "missing".into(),
                        })),
                    },
                    "Result" => {
                        let error = args.get(1).cloned().unwrap_or_else(|| HirType::Opaque {
                            tag: "missing".into(),
                        });
                        if !matches!(&error, HirType::Named { symbol, .. } if self.declarations.get(symbol) == Some(&OwnedDeclKind::Enum))
                        {
                            self.error(
                                module,
                                value.span.clone(),
                                "Result error type must resolve to an enum declaration",
                            );
                        }
                        HirType::Result {
                            ok: Box::new(args.first().cloned().unwrap_or_else(|| {
                                HirType::Opaque {
                                    tag: "missing".into(),
                                }
                            })),
                            error: Box::new(error),
                        }
                    }
                    _ => unreachable!(),
                };
            }
        }
        let Some(symbol) = self.resolve(module, &value.path, &value.span) else {
            return HirType::Opaque {
                tag: value.path.segments.join("."),
            };
        };
        let expected = match self.declarations.get(&symbol).copied() {
            Some(OwnedDeclKind::Type { generics }) => generics,
            _ => 0,
        };
        self.arity(module, value, expected, &symbol.as_string());
        let args = value
            .arguments
            .iter()
            .filter_map(|argument| match &argument.kind {
                TypeArgKind::Type(inner) => Some(self.ty(module, inner, generics)),
                TypeArgKind::String(_) => {
                    self.error(
                        module,
                        argument.span.clone(),
                        "string type arguments are unsupported",
                    );
                    None
                }
            })
            .collect();
        HirType::Named { symbol, args }
    }

    fn generics(&mut self, module: usize, values: &[ast::GenericParam]) -> Vec<HirGenericParam> {
        let names = values
            .iter()
            .map(|value| value.name.clone())
            .collect::<HashSet<_>>();
        values
            .iter()
            .enumerate()
            .map(|(source_order, value)| HirGenericParam {
                span: value.span.clone(),
                name: value.name.clone(),
                bounds: value
                    .bounds
                    .iter()
                    .map(|bound| self.ty(module, bound, &names))
                    .collect(),
                source_order,
            })
            .collect()
    }

    fn value(&mut self, module: usize, value: &ConstExpr) -> Option<HirValue> {
        match value {
            ConstExpr::Constructor { span, .. } => {
                self.error(
                    module,
                    span.clone(),
                    "constructors are unsupported in literal constants",
                );
                None
            }
            ConstExpr::Expression(expression) => match &expression.kind {
                ExprKind::Literal(literal) => Some(match &literal.kind {
                    LiteralKind::Bool(value) => HirValue::Bool(*value),
                    LiteralKind::Integer(value) => HirValue::Integer(value.clone()),
                    LiteralKind::Float(value) => HirValue::F64 {
                        bits: value
                            .parse::<f64>()
                            .map(|v| format!("{:016x}", v.to_bits()))
                            .unwrap_or_default(),
                    },
                    LiteralKind::String(value) => HirValue::String(value.clone()),
                }),
                ExprKind::Unit => Some(HirValue::Unit),
                ExprKind::Parenthesized(inner) => {
                    self.value(module, &ConstExpr::Expression((**inner).clone()))
                }
                _ => {
                    self.error(
                        module,
                        expression.span.clone(),
                        "constants must be typed literals",
                    );
                    None
                }
            },
        }
    }
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
        "Unit" => PrimitiveType::Unit,
        "JsonValue" => PrimitiveType::JsonValue,
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

fn owned_has_unresolved_type(ty: &HirType) -> bool {
    match ty {
        HirType::TypeParameter { .. } | HirType::Opaque { .. } => true,
        HirType::Named { args, .. } => args.iter().any(owned_has_unresolved_type),
        HirType::List { item } | HirType::Set { item } | HirType::Option { item } => {
            owned_has_unresolved_type(item)
        }
        HirType::Map { key, value } => {
            owned_has_unresolved_type(key) || owned_has_unresolved_type(value)
        }
        HirType::Tuple2 { first, second } => {
            owned_has_unresolved_type(first) || owned_has_unresolved_type(second)
        }
        HirType::Result { ok, error } => {
            owned_has_unresolved_type(ok) || owned_has_unresolved_type(error)
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
            owned_is_numeric(left) && owned_is_numeric(right)
        }
        CompareOp::Equal | CompareOp::NotEqual => {
            (owned_is_numeric(left) && owned_is_numeric(right)) || left == right
        }
    }
}

fn owned_invalid_expr_type(tag: &'static str) -> HirType {
    HirType::Opaque { tag: tag.into() }
}

fn owned_binary_is_logical(op: BinaryOp) -> bool {
    matches!(op, BinaryOp::Or | BinaryOp::And)
}

fn owned_binary_is_numeric_compatible(left: &HirType, right: &HirType) -> bool {
    owned_is_numeric(left) && owned_is_numeric(right)
}

impl<'a> OwnedLower<'a> {
    fn expr(
        &mut self,
        module: usize,
        value: &Expr,
        env: &HashMap<String, (SymbolId, HirType)>,
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
            ExprKind::Name(path) => {
                let name = path.segments.last().cloned().unwrap_or_default();
                if let Some((symbol, ty)) = env.get(&name) {
                    (
                        HirExprKind::ParameterRef(symbol.clone()),
                        ty.clone(),
                        Some(HirReference::Parameter(symbol.clone())),
                    )
                } else if let Some(symbol) = self.resolve(module, path, &value.span) {
                    match self.declarations.get(&symbol).copied() {
                        Some(OwnedDeclKind::Const) => (
                            HirExprKind::ConstantRef(symbol.clone()),
                            HirType::Opaque {
                                tag: "constant".into(),
                            },
                            Some(HirReference::Constant(symbol)),
                        ),
                        _ => (
                            HirExprKind::EnumSingletonRef(symbol.clone()),
                            HirType::Named {
                                symbol: symbol.clone(),
                                args: Vec::new(),
                            },
                            Some(HirReference::EnumSingleton(symbol)),
                        ),
                    }
                } else {
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
                let ty = if name == "len" {
                    HirType::Primitive(PrimitiveType::I64)
                } else {
                    HirType::Opaque { tag: name.clone() }
                };
                (
                    HirExprKind::Field {
                        base: Box::new(base),
                        name: name.clone(),
                    },
                    ty,
                    None,
                )
            }
            ExprKind::Unary { op, operand } => {
                let operand = self.expr(module, operand, env);
                let ty = if matches!(op, UnaryOp::Not) {
                    HirType::Primitive(PrimitiveType::Bool)
                } else {
                    operand.ty.clone()
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
                let left = self.expr(module, left, env);
                let right = self.expr(module, right, env);
                let valid = if owned_binary_is_logical(*op) {
                    left.ty == HirType::Primitive(PrimitiveType::Bool)
                        && right.ty == HirType::Primitive(PrimitiveType::Bool)
                } else {
                    owned_binary_is_numeric_compatible(&left.ty, &right.ty)
                };
                if !valid {
                    self.error(
                        module,
                        value.span.clone(),
                        if owned_binary_is_logical(*op) {
                            "logical operator requires boolean operands"
                        } else {
                            "arithmetic operator requires numeric operands"
                        },
                    );
                }
                let ty = if valid {
                    if owned_binary_is_logical(*op) {
                        HirType::Primitive(PrimitiveType::Bool)
                    } else {
                        left.ty.clone()
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
                        left: Box::new(left),
                        right: Box::new(right),
                    },
                    ty,
                    None,
                )
            }
            ExprKind::Comparison { first, rest } => {
                let first = self.expr(module, first, env);
                let mut operands = vec![first];
                let mut valid = true;
                let operators = rest
                    .iter()
                    .map(|(op, expression)| {
                        let operand = self.expr(module, expression, env);
                        if !owned_comparison_compatible(
                            &operands[operands.len() - 1].ty,
                            &operand.ty,
                            *op,
                        ) {
                            valid = false;
                            self.error(
                                module,
                                value.span.clone(),
                                "comparison operands are incompatible or unsupported",
                            );
                        }
                        operands.push(operand);
                        match op {
                            CompareOp::Equal => HirCompareOp::Equal,
                            CompareOp::NotEqual => HirCompareOp::NotEqual,
                            CompareOp::Less => HirCompareOp::Less,
                            CompareOp::LessEqual => HirCompareOp::LessEqual,
                            CompareOp::Greater => HirCompareOp::Greater,
                            CompareOp::GreaterEqual => HirCompareOp::GreaterEqual,
                        }
                    })
                    .collect();
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
    fn field(
        &mut self,
        module: usize,
        field: &ast::Field,
        generics: &HashSet<String>,
        order: usize,
    ) -> HirField {
        if let Some(default) = &field.default {
            if !owned_default_compatible(&field.ty, default) {
                self.error(
                    module,
                    default.span().clone(),
                    "default value does not match its declared type",
                );
            }
        }
        HirField {
            span: field.span.clone(),
            name: field.name.clone(),
            ty: self.ty(module, &field.ty, generics),
            default: field
                .default
                .as_ref()
                .and_then(|value| self.value(module, value)),
            source_order: order,
        }
    }

    fn parameter(
        &mut self,
        module: usize,
        parameter: &ast::Parameter,
        generics: &HashSet<String>,
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

    fn contract(
        &mut self,
        module: usize,
        body: &FunctionBody,
        env: &HashMap<String, (SymbolId, HirType)>,
    ) -> (HirContract, Option<HirDoc>) {
        let mut contract = HirContract::default();
        let mut doc = None;
        let FunctionBody::Clauses { clauses, .. } = body else {
            return (contract, doc);
        };
        for (clause_id, clause) in clauses.iter().enumerate() {
            match &clause.kind {
                ClauseKind::Documentation(value) => {
                    doc = Some(HirDoc {
                        span: value.span.clone(),
                        text: value.text.clone(),
                    });
                }
                ClauseKind::Requires { condition } => {
                    let expression = self.expr(module, condition, env);
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
                        kind: HirClauseKind::Requires { expression },
                    });
                }
                ClauseKind::Ensures { pattern, condition } => {
                    let expression = self.expr(module, condition, env);
                    if expression.ty != HirType::Primitive(PrimitiveType::Bool) {
                        self.error(
                            module,
                            condition.span.clone(),
                            "contract condition must be boolean",
                        );
                    }
                    let pattern = pattern
                        .as_ref()
                        .map(|pattern| self.pattern(module, pattern, env));
                    contract.clauses.push(HirClause {
                        clause_id: clause_id as u32,
                        span: clause.span.clone(),
                        kind: HirClauseKind::Ensures {
                            pattern,
                            expression,
                        },
                    });
                }
                ClauseKind::Error { error, when } => {
                    let variant = if error.segments.len() >= 2 {
                        let enum_path = ast::QualifiedName::new(
                            error.span.clone(),
                            error.segments[..error.segments.len() - 1].to_vec(),
                        );
                        let enum_id = self
                            .resolve(module, &enum_path, &error.span)
                            .unwrap_or_else(|| {
                                SymbolId::new(
                                    self.modules[module].clone(),
                                    error.segments[error.segments.len() - 2].clone(),
                                )
                            });
                        SymbolId::new(
                            enum_id.module,
                            format!("{}.{}", enum_id.name, error.segments.last().unwrap()),
                        )
                    } else {
                        self.resolve(module, error, &error.span).unwrap_or_else(|| {
                            SymbolId::new(self.modules[module].clone(), error.segments.join("."))
                        })
                    };
                    let when = when.as_ref().map(|value| {
                        let expression = self.expr(module, value, env);
                        if expression.ty != HirType::Primitive(PrimitiveType::Bool) {
                            self.error(
                                module,
                                value.span.clone(),
                                "contract condition must be boolean",
                            );
                        }
                        expression
                    });
                    contract.clauses.push(HirClause {
                        clause_id: clause_id as u32,
                        span: clause.span.clone(),
                        kind: HirClauseKind::Error {
                            variant,
                            priority: None,
                            when,
                        },
                    });
                }
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

    fn pattern(
        &mut self,
        module: usize,
        pattern: &ast::Pattern,
        env: &HashMap<String, (SymbolId, HirType)>,
    ) -> HirPattern {
        match &pattern.kind {
            PatternKind::Wildcard => HirPattern {
                span: pattern.span.clone(),
                ty: HirType::Opaque {
                    tag: "pattern".into(),
                },
                kind: HirPatternKind::Wildcard,
            },
            PatternKind::Binding(name) => {
                let symbol = SymbolId::new(self.modules[module].clone(), name.clone());
                HirPattern {
                    span: pattern.span.clone(),
                    ty: HirType::Opaque {
                        tag: "pattern".into(),
                    },
                    kind: HirPatternKind::Binding {
                        symbol,
                        name: name.clone(),
                    },
                }
            }
            PatternKind::Variant { path, arguments } => {
                let symbol = self
                    .resolve(module, path, &pattern.span)
                    .unwrap_or_else(|| {
                        SymbolId::new(self.modules[module].clone(), path.segments.join("."))
                    });
                HirPattern {
                    span: pattern.span.clone(),
                    ty: HirType::Opaque {
                        tag: "variant".into(),
                    },
                    kind: HirPatternKind::Variant {
                        symbol,
                        arguments: arguments
                            .iter()
                            .map(|value| self.pattern(module, value, env))
                            .collect(),
                    },
                }
            }
        }
    }
    fn declaration(
        &mut self,
        module: usize,
        declaration: &Declaration,
        order: usize,
    ) -> HirDeclaration {
        let module_id = self.modules[module].clone();
        let id_for = |name: &str| SymbolId::new(module_id.clone(), name);
        match declaration {
            Declaration::Alias(value) => HirDeclaration::Alias(HirAlias {
                id: id_for(&value.name),
                span: value.span.clone(),
                doc: value.doc.as_ref().map(|v| HirDoc {
                    span: v.span.clone(),
                    text: v.text.clone(),
                }),
                generics: Vec::new(),
                target: self.ty(module, &value.target, &HashSet::new()),
                public: true,
                source_order: order,
            }),
            Declaration::Newtype(value) => HirDeclaration::Newtype(HirNewtype {
                id: id_for(&value.name),
                span: value.span.clone(),
                doc: value.doc.as_ref().map(|v| HirDoc {
                    span: v.span.clone(),
                    text: v.text.clone(),
                }),
                generics: Vec::new(),
                carrier: self.ty(module, &value.underlying, &HashSet::new()),
                refinement: value
                    .where_clause
                    .as_ref()
                    .map(|v| self.expr(module, v, &HashMap::new())),
                public: true,
                source_order: order,
            }),
            Declaration::Struct(value) => {
                let names = value
                    .generics
                    .iter()
                    .map(|v| v.name.clone())
                    .collect::<HashSet<_>>();
                HirDeclaration::Struct(HirStruct {
                    id: id_for(&value.name),
                    span: value.span.clone(),
                    doc: value.doc.as_ref().map(|v| HirDoc {
                        span: v.span.clone(),
                        text: v.text.clone(),
                    }),
                    generics: self.generics(module, &value.generics),
                    fields: value
                        .fields
                        .iter()
                        .enumerate()
                        .map(|(i, v)| self.field(module, v, &names, i))
                        .collect(),
                    public: true,
                    source_order: order,
                })
            }
            Declaration::Enum(value) => {
                let names = value
                    .generics
                    .iter()
                    .map(|v| v.name.clone())
                    .collect::<HashSet<_>>();
                let enum_id = id_for(&value.name);
                HirDeclaration::Enum(HirEnum {
                    id: enum_id.clone(),
                    span: value.span.clone(),
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
                                    ty: self.ty(module, &p.ty, &names),
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
                let names = value
                    .generics
                    .iter()
                    .map(|v| v.name.clone())
                    .collect::<HashSet<_>>();
                let trait_id = id_for(&value.name);
                HirDeclaration::Trait(HirTrait {
                    id: trait_id.clone(),
                    span: value.span.clone(),
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
                                .map(|(j, p)| self.parameter(module, p, &names, j))
                                .collect(),
                            return_type: self.ty(module, &method.return_type, &names),
                            contract: HirContract::default(),
                            public: true,
                            source_order: i,
                        })
                        .collect(),
                    public: true,
                    source_order: order,
                })
            }
            Declaration::Const(value) => {
                if !owned_default_compatible(&value.ty, &value.value) {
                    self.error(
                        module,
                        value.value.span().clone(),
                        "constant literal does not match its declared type",
                    );
                }
                HirDeclaration::Const(HirConst {
                    id: id_for(&value.name),
                    span: value.span.clone(),
                    doc: value.doc.as_ref().map(|v| HirDoc {
                        span: v.span.clone(),
                        text: v.text.clone(),
                    }),
                    ty: self.ty(module, &value.ty, &HashSet::new()),
                    value: self.value(module, &value.value).unwrap_or(HirValue::Unit),
                    public: true,
                    source_order: order,
                })
            }
            Declaration::Function(value) => {
                let names = value
                    .generics
                    .iter()
                    .map(|v| v.name.clone())
                    .collect::<HashSet<_>>();
                let id = id_for(&value.name);
                let mut env = HashMap::new();
                let parameters = value
                    .parameters
                    .iter()
                    .enumerate()
                    .map(|(i, p)| {
                        let parameter = self.parameter(module, p, &names, i);
                        env.insert(
                            p.name.clone(),
                            (
                                SymbolId::new(id.module.clone(), p.name.clone()),
                                parameter.ty.clone(),
                            ),
                        );
                        parameter
                    })
                    .collect::<Vec<_>>();
                let (contract, doc) = self.contract(module, &value.body, &env);
                HirDeclaration::Function(HirFunction {
                    id,
                    span: value.span.clone(),
                    doc,
                    generics: self.generics(module, &value.generics),
                    parameters,
                    return_type: self.ty(module, &value.return_type, &names),
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
            id: self.modules[index].clone(),
            imports,
            declarations,
            source_order: index,
        }
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
fn owned_default_compatible(ty: &ast::Type, value: &ConstExpr) -> bool {
    let kind = match value {
        ConstExpr::Expression(expression) => match &expression.kind {
            ExprKind::Literal(literal) => &literal.kind,
            ExprKind::Unit => return ty.path.segments == ["Unit"],
            ExprKind::Parenthesized(inner) => {
                return owned_default_compatible(ty, &ConstExpr::Expression((**inner).clone()));
            }
            _ => return false,
        },
        ConstExpr::Constructor { .. } => return true,
    };
    match kind {
        LiteralKind::Bool(_) => ty.path.segments == ["Bool"],
        LiteralKind::Integer(value) => {
            let Some(number) = value.parse::<i128>().ok() else {
                return false;
            };
            match ty.path.segments.last().map(String::as_str) {
                Some("I8") => (-128..=127).contains(&number),
                Some("I16") => (-32_768..=32_767).contains(&number),
                Some("I32") => (-2_147_483_648..=2_147_483_647).contains(&number),
                Some("I64") => {
                    (-9_223_372_036_854_775_808..=9_223_372_036_854_775_807).contains(&number)
                }
                Some("U8") => (0..=255).contains(&number),
                Some("U16") => (0..=65_535).contains(&number),
                Some("U32") => (0..=4_294_967_295).contains(&number),
                Some("U64") => (0..=18_446_744_073_709_551_615).contains(&number),
                _ => false,
            }
        }
        LiteralKind::Float(value) => {
            value.parse::<f64>().ok().is_some_and(f64::is_finite)
                && matches!(
                    ty.path.segments.last().map(String::as_str),
                    Some("F32" | "F64")
                )
        }
        LiteralKind::String(_) => ty.path.segments == ["Str"],
    }
}

fn owned_type_paths(value: &ast::Type, out: &mut Vec<ast::QualifiedName>) {
    out.push(value.path.clone());
    for argument in &value.arguments {
        if let TypeArgKind::Type(inner) = &argument.kind {
            owned_type_paths(inner, out);
        }
    }
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
                Declaration::Alias(value) => (&value.name, true),
                Declaration::Newtype(value) => (&value.name, true),
                Declaration::Struct(value) => (&value.name, true),
                Declaration::Enum(value) => (&value.name, true),
                Declaration::Trait(value) => (&value.name, false),
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
            if owned_primitive(name).is_some() || matches!(name.as_str(), "Option" | "Result") {
                report(
                    declaration.span().clone(),
                    format!("declaration `{name}` collides with a prelude type"),
                );
            }
            let generics = match declaration {
                Declaration::Struct(value) => Some(&value.generics),
                Declaration::Enum(value) => Some(&value.generics),
                Declaration::Trait(value) => Some(&value.generics),
                Declaration::Function(value) => Some(&value.generics),
                _ => None,
            };
            if let Some(generics) = generics {
                let mut names = BTreeSet::new();
                for generic in generics {
                    if !names.insert(&generic.name) {
                        report(
                            generic.span.clone(),
                            format!("duplicate generic parameter `{}`", generic.name),
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
                Declaration::Alias(v) => &v.name,
                Declaration::Newtype(v) => &v.name,
                Declaration::Struct(v) => &v.name,
                Declaration::Enum(v) => &v.name,
                Declaration::Trait(v) => &v.name,
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
            let (name, types): (&String, Vec<&ast::Type>) = match declaration {
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

/// not used as the source of any HIR field.
pub fn lower(
    source_root: &Path,
    parsed: ParsedProject,
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
