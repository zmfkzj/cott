//! Owned, target-independent high-level intermediate representation.
//!
//! Lowering and structural validation live entirely in this module.

use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::path::{Component, Path, PathBuf};
use std::sync::Arc;

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
    Path,
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
    Alias,
    Type { generics: usize },
    Enum { generics: usize },
    Const,
    Function,
    Trait { generics: usize },
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
            constant_values: HashMap::new(),
            resolving_constants: HashSet::new(),
            resolving_aliases: HashSet::new(),
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
        Some(self.ty(source_index, &underlying, &HashSet::new()))
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
                        args: args.iter().map(|arg| resolve(lower, arg, seen)).collect(),
                    }
                }
                HirType::Named { symbol, args } => HirType::Named {
                    symbol: symbol.clone(),
                    args: args.iter().map(|arg| resolve(lower, arg, seen)).collect(),
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
                HirType::Tuple2 { first, second } => HirType::Tuple2 {
                    first: Box::new(resolve(lower, first, seen)),
                    second: Box::new(resolve(lower, second, seen)),
                },
                HirType::Option { item } => HirType::Option {
                    item: Box::new(resolve(lower, item, seen)),
                },
                HirType::Result { ok, error } => HirType::Result {
                    ok: Box::new(resolve(lower, ok, seen)),
                    error: Box::new(resolve(lower, error, seen)),
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
        Some(self.ty(index, &ty, &HashSet::new()))
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
            if name == "Opaque" {
                self.arity(module, value, 1, &name);
                return match value.arguments.first().map(|argument| &argument.kind) {
                    Some(TypeArgKind::String(tag)) if valid_opaque_tag(tag) => {
                        HirType::Opaque { tag: tag.clone() }
                    }
                    Some(TypeArgKind::String(_)) => {
                        self.error(
                            module,
                            value.span.clone(),
                            "Opaque tag must match [a-z][a-z0-9._-]{0,63}",
                        );
                        HirType::Opaque {
                            tag: "invalid".into(),
                        }
                    }
                    _ => {
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
            let expected = match name.as_str() {
                "List" | "Set" | "Option" => Some(1),
                "Map" | "Tuple" | "Result" => Some(2),
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
                    "Tuple" => HirType::Tuple2 {
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
                        if !matches!(&error, HirType::Named { symbol, .. } if matches!(self.declarations.get(symbol), Some(OwnedDeclKind::Enum { .. })))
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
        if self.declarations.get(&symbol) == Some(&OwnedDeclKind::Alias) {
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
        let expected = match self.declarations.get(&symbol).copied() {
            Some(
                OwnedDeclKind::Type { generics }
                | OwnedDeclKind::Enum { generics }
                | OwnedDeclKind::Trait { generics },
            ) => generics,
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
        let expected = self.ty(module, &declaration.ty, &HashSet::new());
        let value = self.value(module, &declaration.value, &expected);
        self.resolving_constants.remove(symbol);
        if let Some(value) = &value {
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
                let carrier = self.ty(source_module, &carrier, &HashSet::new());
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
            ExprKind::Field { .. } => {
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
                HirValue::List(value) => Some(HirValue::Integer(value.len().to_string())),
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
fn contains_opaque(ty: &HirType) -> bool {
    match ty {
        HirType::Opaque { .. } => true,
        HirType::Named { args, .. } => args.iter().any(contains_opaque),
        HirType::List { item } | HirType::Set { item } | HirType::Option { item } => {
            contains_opaque(item)
        }
        HirType::Map { key, value } => contains_opaque(key) || contains_opaque(value),
        HirType::Tuple2 { first, second } => contains_opaque(first) || contains_opaque(second),
        HirType::Result { ok, error } => contains_opaque(ok) || contains_opaque(error),
        HirType::Primitive(_) | HirType::TypeParameter { .. } => false,
    }
}

fn is_opaque_boundary(ty: &HirType) -> bool {
    match ty {
        HirType::Opaque { .. } => true,
        HirType::Option { item } => matches!(item.as_ref(), HirType::Opaque { .. }),
        HirType::Result { ok, error } => {
            matches!(ok.as_ref(), HirType::Opaque { .. }) && !contains_opaque(error)
        }
        _ => false,
    }
}

fn validate_opaque_boundaries(modules: &[HirModule], errors: &mut Vec<ProjectDiagnostic>) {
    let mut report = |module: &HirModule, span: &Span, message: &str| {
        errors.push(ProjectDiagnostic {
            path: module.source.clone(),
            diagnostic: Diagnostic::new(message, span.clone()),
        });
    };
    for module in modules {
        for declaration in &module.declarations {
            match declaration {
                HirDeclaration::Alias(value) if contains_opaque(&value.target) => report(
                    module,
                    &value.span,
                    "Opaque is allowed only as a manifest-bound function boundary",
                ),
                HirDeclaration::Newtype(value) if contains_opaque(&value.carrier) => {
                    report(module, &value.span, "Opaque cannot be a newtype carrier")
                }
                HirDeclaration::Struct(value)
                    if value.fields.iter().any(|field| contains_opaque(&field.ty)) =>
                {
                    report(module, &value.span, "Opaque cannot occur in a struct field")
                }
                HirDeclaration::Enum(value)
                    if value
                        .variants
                        .iter()
                        .flat_map(|variant| &variant.fields)
                        .any(|field| contains_opaque(&field.ty)) =>
                {
                    report(
                        module,
                        &value.span,
                        "Opaque cannot occur in an enum payload",
                    )
                }
                HirDeclaration::Trait(value)
                    if value.methods.iter().any(|method| {
                        contains_opaque(&method.return_type)
                            || method
                                .parameters
                                .iter()
                                .any(|parameter| contains_opaque(&parameter.ty))
                    }) =>
                {
                    report(module, &value.span, "Opaque cannot occur in a trait")
                }
                HirDeclaration::Const(value) if contains_opaque(&value.ty) => {
                    report(module, &value.span, "Opaque cannot be a constant type")
                }
                HirDeclaration::Function(value) => {
                    for parameter in &value.parameters {
                        if contains_opaque(&parameter.ty) && !is_opaque_boundary(&parameter.ty) {
                            report(
                                module,
                                &parameter.span,
                                "Opaque must be a direct function boundary type",
                            );
                        }
                    }
                    if contains_opaque(&value.return_type)
                        && !is_opaque_boundary(&value.return_type)
                    {
                        report(
                            module,
                            &value.span,
                            "Opaque must be a direct function boundary type",
                        );
                    }
                }
                _ => {}
            }
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
        "Path" => PrimitiveType::Path,
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
fn owned_len_allowed(ty: &HirType) -> bool {
    matches!(
        ty,
        HirType::Primitive(PrimitiveType::Str | PrimitiveType::Bytes)
            | HirType::List { .. }
            | HirType::Set { .. }
            | HirType::Map { .. }
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
                            kind: if path.segments[0] == "result" || path.segments[0] == "self" {
                                HirExprKind::SelfRef
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
                    if name == "result" || name == "self" {
                        (HirExprKind::SelfRef, ty.clone(), None)
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
                        .map(|field| {
                            (
                                field.ty.clone(),
                                value
                                    .generics
                                    .iter()
                                    .map(|generic| generic.name.clone())
                                    .collect::<Vec<_>>(),
                            )
                        }),
                    Declaration::Newtype(value)
                        if value.name == symbol.name && field_name == "value" =>
                    {
                        Some((value.underlying.clone(), Vec::new()))
                    }
                    _ => None,
                })?
        };
        let generic_set = generics.iter().cloned().collect::<HashSet<_>>();
        let lowered = self.ty(source_index, &field_type, &generic_set);
        let substitutions = generics
            .into_iter()
            .zip(args.iter().cloned())
            .collect::<HashMap<_, _>>();
        Some(substitute_hir_type(lowered, &substitutions))
    }

    fn field(
        &mut self,
        module: usize,
        field: &ast::Field,
        generics: &HashSet<String>,
        order: usize,
    ) -> HirField {
        let ty = self.ty(module, &field.ty, generics);
        let default = field
            .default
            .as_ref()
            .and_then(|value| self.value(module, value, &ty));
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

    fn contract(
        &mut self,
        module: usize,
        body: &FunctionBody,
        env: &HashMap<String, (SymbolId, HirType, bool)>,
        return_type: &HirType,
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
                    let mut clause_env = env.clone();
                    let pattern = if let Some(pattern) = pattern {
                        Some(self.pattern(module, pattern, return_type, &mut clause_env))
                    } else {
                        clause_env.insert(
                            "result".to_owned(),
                            (
                                SymbolId::new(self.modules[module].clone(), "result"),
                                return_type.clone(),
                                false,
                            ),
                        );
                        None
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
                        kind: HirClauseKind::Ensures {
                            pattern,
                            expression,
                        },
                    });
                }
                ClauseKind::Error { error, when } => {
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
                    if let Some((variant, _)) = resolved.filter(|_| valid_return) {
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
        let Some((field_types, generic_names)) = self.parsed.sources[source_index]
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
                            value
                                .generics
                                .iter()
                                .map(|generic| generic.name.clone())
                                .collect::<Vec<_>>(),
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
        let generic_set = generic_names.iter().cloned().collect::<HashSet<_>>();
        let substitutions = generic_names
            .into_iter()
            .zip(args.iter().cloned())
            .collect::<HashMap<_, _>>();
        let fields = field_types
            .iter()
            .map(|field| {
                let ty = self.ty(source_index, field, &generic_set);
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
                env.insert(name.clone(), (symbol.clone(), expected.clone(), true));
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
            Declaration::Newtype(value) => {
                let carrier = self.ty(module, &value.underlying, &HashSet::new());
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
                let id = id_for(&value.name);
                let ty = self.ty(module, &value.ty, &HashSet::new());
                let constant_value = self.constant_value(&id).unwrap_or(HirValue::Unit);
                HirDeclaration::Const(HirConst {
                    id,
                    span: value.span.clone(),
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
                                false,
                            ),
                        );
                        parameter
                    })
                    .collect::<Vec<_>>();
                let return_type = self.ty(module, &value.return_type, &names);
                let (contract, doc) = self.contract(module, &value.body, &env, &return_type);
                HirDeclaration::Function(HirFunction {
                    id,
                    span: value.span.clone(),
                    doc,
                    generics: self.generics(module, &value.generics),
                    parameters,
                    return_type,
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

fn substitute_hir_type(ty: HirType, substitutions: &HashMap<String, HirType>) -> HirType {
    match ty {
        HirType::TypeParameter { name } => substitutions
            .get(&name)
            .cloned()
            .unwrap_or(HirType::TypeParameter { name }),
        HirType::Named { symbol, args } => HirType::Named {
            symbol,
            args: args
                .into_iter()
                .map(|arg| substitute_hir_type(arg, substitutions))
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
        HirType::Tuple2 { first, second } => HirType::Tuple2 {
            first: Box::new(substitute_hir_type(*first, substitutions)),
            second: Box::new(substitute_hir_type(*second, substitutions)),
        },
        HirType::Option { item } => HirType::Option {
            item: Box::new(substitute_hir_type(*item, substitutions)),
        },
        HirType::Result { ok, error } => HirType::Result {
            ok: Box::new(substitute_hir_type(*ok, substitutions)),
            error: Box::new(substitute_hir_type(*error, substitutions)),
        },
        other => other,
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
        if let TypeArgKind::Type(inner) = &argument.kind {
            owned_type_paths(inner, out);
        }
    }
}
fn owned_visit_type<F: FnMut(&ast::QualifiedName)>(value: &ast::Type, visit: &mut F) {
    visit(&value.path);
    for argument in &value.arguments {
        if let TypeArgKind::Type(inner) = &argument.kind {
            owned_visit_type(inner, visit);
        }
    }
}

fn owned_visit_expr<F: FnMut(&ast::QualifiedName)>(value: &ast::Expr, visit: &mut F) {
    match &value.kind {
        ExprKind::Name(path) => visit(path),
        ExprKind::Parenthesized(inner) | ExprKind::Unary { operand: inner, .. } => {
            owned_visit_expr(inner, visit);
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
        ExprKind::Literal(_) | ExprKind::Unit => {}
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
    }
}

fn owned_visit_clause<F: FnMut(&ast::QualifiedName)>(value: &ast::Clause, visit: &mut F) {
    match &value.kind {
        ast::ClauseKind::Requires { condition } => owned_visit_expr(condition, visit),
        ast::ClauseKind::Ensures { pattern, condition } => {
            if let Some(pattern) = pattern {
                owned_visit_pattern(pattern, visit);
            }
            owned_visit_expr(condition, visit);
        }
        ast::ClauseKind::Error { error, when } => {
            visit(error);
            if let Some(when) = when {
                owned_visit_expr(when, visit);
            }
        }
        ast::ClauseKind::Effects { .. } | ast::ClauseKind::Documentation(_) => {}
    }
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
        Declaration::Newtype(value) => {
            owned_visit_type(&value.underlying, &mut visit);
            if let Some(refinement) = &value.where_clause {
                owned_visit_expr(refinement, &mut visit);
            }
        }
        Declaration::Struct(value) => {
            for generic in &value.generics {
                for bound in &generic.bounds {
                    owned_visit_type(bound, &mut visit);
                }
            }
            for field in &value.fields {
                owned_visit_type(&field.ty, &mut visit);
                if let Some(default) = &field.default {
                    owned_visit_const_expr(default, &mut visit);
                }
            }
        }
        Declaration::Enum(value) => {
            for generic in &value.generics {
                for bound in &generic.bounds {
                    owned_visit_type(bound, &mut visit);
                }
            }
            for variant in &value.variants {
                for parameter in &variant.parameters {
                    owned_visit_parameter(parameter, &mut visit);
                }
            }
        }
        Declaration::Trait(value) => {
            for generic in &value.generics {
                for bound in &generic.bounds {
                    owned_visit_type(bound, &mut visit);
                }
            }
            for method in &value.methods {
                for parameter in &method.parameters {
                    owned_visit_parameter(parameter, &mut visit);
                }
                owned_visit_type(&method.return_type, &mut visit);
            }
        }
        Declaration::Const(value) => {
            owned_visit_type(&value.ty, &mut visit);
            owned_visit_const_expr(&value.value, &mut visit);
        }
        Declaration::Function(value) => {
            for generic in &value.generics {
                for bound in &generic.bounds {
                    owned_visit_type(bound, &mut visit);
                }
            }
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
                Declaration::Alias(value) => (&value.name, true),
                Declaration::Newtype(value) => (&value.name, true),
                Declaration::Struct(value) => (&value.name, true),
                Declaration::Enum(value) => (&value.name, true),
                Declaration::Trait(value) => (&value.name, true),
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
                    "List" | "Set" | "Map" | "Tuple" | "Option" | "Result" | "Opaque"
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
            HirType::Tuple2 { first, second } => {
                stable(first, modules, visiting) && stable(second, modules, visiting)
            }
            HirType::Named { symbol, args } if visiting.insert(symbol.clone()) => {
                let result = match declaration(modules, symbol) {
                    Some(HirDeclaration::Newtype(value)) => {
                        let substitutions = value
                            .generics
                            .iter()
                            .map(|generic| generic.name.clone())
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
            HirType::List { item } | HirType::Option { item } => {
                visit(item, modules, path, span, errors);
            }
            HirType::Tuple2 { first, second } => {
                visit(first, modules, path, span, errors);
                visit(second, modules, path, span, errors);
            }
            HirType::Result { ok, error } => {
                visit(ok, modules, path, span, errors);
                visit(error, modules, path, span, errors);
            }
            HirType::Named { args, .. } => {
                for argument in args {
                    visit(argument, modules, path, span, errors);
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
                }
                HirDeclaration::Const(value) => types.push(&value.ty),
                HirDeclaration::Function(value) => {
                    types.extend(value.parameters.iter().map(|parameter| &parameter.ty));
                    types.push(&value.return_type);
                }
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
        validate_opaque_boundaries(&modules, &mut errors);
    }
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
