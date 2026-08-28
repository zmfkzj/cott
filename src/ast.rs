use crate::diagnostics::Span;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct File {
    pub span: Span,
    pub module: ModuleDecl,
    pub uses: Vec<UseDecl>,
    pub declarations: Vec<Declaration>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ModuleDecl {
    pub span: Span,
    pub path: QualifiedName,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct UseDecl {
    pub span: Span,
    pub path: QualifiedName,
    pub names: Option<Vec<String>>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Declaration {
    ExternalType(ExternalTypeDecl),
    Alias(AliasDecl),
    Newtype(NewtypeDecl),
    Struct(StructDecl),
    Enum(EnumDecl),
    Trait(TraitDecl),
    Const(ConstDecl),
    Function(FunctionDecl),
    Impl(ImplDecl),
    Resource(ResourceDecl),
    Rule(RuleDecl),
}

impl Declaration {
    pub fn span(&self) -> &Span {
        match self {
            Self::ExternalType(value) => &value.span,
            Self::Alias(value) => &value.span,
            Self::Newtype(value) => &value.span,
            Self::Struct(value) => &value.span,
            Self::Enum(value) => &value.span,
            Self::Trait(value) => &value.span,
            Self::Const(value) => &value.span,
            Self::Function(value) => &value.span,
            Self::Impl(value) => &value.span,
            Self::Resource(value) => &value.span,
            Self::Rule(value) => &value.span,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DocBlock {
    pub span: Span,
    pub text: String,
}
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Annotation {
    pub span: Span,
    pub name: String,
    pub argument: Option<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ExternalTypeDecl {
    pub span: Span,
    pub annotations: Vec<Annotation>,
    pub doc: Option<DocBlock>,
    pub name: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AliasDecl {
    pub span: Span,
    pub annotations: Vec<Annotation>,
    pub doc: Option<DocBlock>,
    pub name: String,
    pub target: Type,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct NewtypeDecl {
    pub span: Span,
    pub annotations: Vec<Annotation>,
    pub doc: Option<DocBlock>,
    pub name: String,
    pub underlying: Type,
    pub where_clause: Option<Expr>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct StructDecl {
    pub span: Span,
    pub annotations: Vec<Annotation>,
    pub doc: Option<DocBlock>,
    pub name: String,
    pub generics: Vec<GenericParam>,
    pub fields: Vec<Field>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EnumDecl {
    pub span: Span,
    pub annotations: Vec<Annotation>,
    pub doc: Option<DocBlock>,
    pub name: String,
    pub generics: Vec<GenericParam>,
    pub variants: Vec<Variant>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TraitDecl {
    pub span: Span,
    pub annotations: Vec<Annotation>,
    pub doc: Option<DocBlock>,
    pub name: String,
    pub generics: Vec<GenericParam>,
    pub associated_types: Vec<AssociatedTypeDecl>,
    pub methods: Vec<TraitMethod>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AssociatedTypeDecl {
    pub span: Span,
    pub name: String,
    pub bounds: Vec<Type>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ConstDecl {
    pub span: Span,
    pub annotations: Vec<Annotation>,
    pub doc: Option<DocBlock>,
    pub name: String,
    pub ty: Type,
    pub value: ConstExpr,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FunctionDecl {
    pub span: Span,
    pub annotations: Vec<Annotation>,
    pub name: String,
    pub generics: Vec<GenericParam>,
    pub parameters: Vec<Parameter>,
    pub return_type: Type,
    pub callable_kind: CallableKind,
    pub body: FunctionBody,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CallableKind {
    Sync,
    Async,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ImplDecl {
    pub span: Span,
    pub annotations: Vec<Annotation>,
    pub name: String,
    pub traits: Vec<Type>,
    pub state: Vec<Field>,
    pub associated_types: Vec<AssociatedTypeAssignment>,
    pub invariants: Vec<ImplInvariant>,
    pub initializer: Option<ImplInitializer>,
    pub methods: Vec<ImplMethod>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AssociatedTypeAssignment {
    pub span: Span,
    pub name: String,
    pub ty: Type,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ImplInvariant {
    pub span: Span,
    pub guard: Option<MatchGuard>,
    pub condition: Expr,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ImplInitializer {
    pub span: Span,
    pub parameters: Vec<Parameter>,
    pub clauses: Vec<Clause>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ImplMethod {
    pub span: Span,
    pub name: String,
    pub self_span: Span,
    pub parameters: Vec<Parameter>,
    pub return_type: Type,
    pub clauses: Vec<Clause>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ResourceDecl {
    pub span: Span,
    pub annotations: Vec<Annotation>,
    pub doc: Option<DocBlock>,
    pub name: String,
    pub initial: ResourceStateRef,
    pub states: Vec<ResourceState>,
    pub terminals: Vec<ResourceStateRef>,
    pub transitions: Vec<ResourceTransition>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ResourceState {
    pub span: Span,
    pub name: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ResourceStateRef {
    pub span: Span,
    pub name: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ResourceTransition {
    pub span: Span,
    pub from: ResourceStateRef,
    pub to: ResourceStateRef,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum FunctionBody {
    Signature { span: Span },
    Clauses { span: Span, clauses: Vec<Clause> },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RuleDecl {
    pub span: Span,
    pub annotations: Vec<Annotation>,
    pub doc: Option<DocBlock>,
    pub name: String,
    pub generics: Vec<GenericParam>,
    pub base: Option<Type>,
    pub clauses: Vec<RuleClause>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RuleClause {
    pub span: Span,
    pub action: RuleClauseAction,
    pub kind: ClauseKind,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RuleClauseAction {
    Add,
    Override,
    Delete,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Field {
    pub span: Span,
    pub name: String,
    pub ty: Type,
    pub default: Option<ConstExpr>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Variant {
    pub span: Span,
    pub name: String,
    pub parameters: Vec<Parameter>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TraitMethod {
    pub span: Span,
    pub name: String,
    pub self_span: Span,
    pub parameters: Vec<Parameter>,
    pub return_type: Type,
    pub default: Option<QualifiedName>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Parameter {
    pub span: Span,
    pub name: String,
    pub ty: Type,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum GenericParam {
    Type {
        span: Span,
        name: String,
        bounds: Vec<Type>,
    },
    Const {
        span: Span,
        name: String,
        ty: ConstKind,
    },
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ConstKind {
    U8,
    U16,
    U32,
    U64,
}

impl ConstKind {
    pub const fn name(self) -> &'static str {
        match self {
            Self::U8 => "U8",
            Self::U16 => "U16",
            Self::U32 => "U32",
            Self::U64 => "U64",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Type {
    pub span: Span,
    pub path: QualifiedName,
    pub arguments: Vec<GenericArg>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GenericArg {
    pub span: Span,
    pub kind: GenericArgKind,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum GenericArgKind {
    Type(Type),
    Const(ConstExpr),
    Ambiguous { ty: Type, value: ConstExpr },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct QualifiedName {
    pub span: Span,
    pub segments: Vec<String>,
}

impl QualifiedName {
    pub fn new(span: Span, segments: Vec<String>) -> Self {
        Self { span, segments }
    }

    pub fn single(span: Span, segment: impl Into<String>) -> Self {
        Self::new(span, vec![segment.into()])
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ConstExpr {
    Expression(Expr),
    Constructor {
        span: Span,
        path: QualifiedName,
        argument: Box<ConstExpr>,
    },
    Tuple {
        span: Span,
        values: Vec<ConstExpr>,
    },
    Array {
        span: Span,
        values: Vec<ConstExpr>,
    },
    Buffer {
        span: Span,
        hex: String,
    },
}

impl ConstExpr {
    pub fn span(&self) -> &Span {
        match self {
            Self::Expression(value) => &value.span,
            Self::Constructor { span, .. }
            | Self::Tuple { span, .. }
            | Self::Array { span, .. }
            | Self::Buffer { span, .. } => span,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Clause {
    pub span: Span,
    pub kind: ClauseKind,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ClauseKind {
    Documentation(DocBlock),
    Rule {
        name: QualifiedName,
    },
    Requires {
        guard: Option<MatchGuard>,
        condition: Expr,
    },
    Modifies {
        fields: Vec<ModifiedField>,
    },
    Transitions {
        transitions: Vec<MethodTransition>,
    },
    Ensures {
        guard: Option<MatchGuard>,
        condition: Expr,
    },
    Error {
        error: QualifiedName,
        guard: Option<MatchGuard>,
        when: Option<Expr>,
    },
    Effects {
        effects: Vec<QualifiedName>,
    },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ModifiedField {
    pub span: Span,
    pub name: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct MethodTransition {
    pub span: Span,
    pub field: ModifiedField,
    pub from: QualifiedName,
    pub to: QualifiedName,
}
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct MatchGuard {
    pub span: Span,
    pub scrutinee: Expr,
    pub pattern: Pattern,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Pattern {
    pub span: Span,
    pub kind: PatternKind,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum PatternKind {
    Wildcard,
    Binding(String),
    Variant {
        path: QualifiedName,
        arguments: Vec<Pattern>,
    },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Expr {
    pub span: Span,
    pub kind: ExprKind,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ExprKind {
    Literal(Literal),
    Name(QualifiedName),
    Unit,
    Parenthesized(Box<Expr>),
    Unary {
        op: UnaryOp,
        operand: Box<Expr>,
    },
    Binary {
        left: Box<Expr>,
        op: BinaryOp,
        right: Box<Expr>,
    },
    Comparison {
        first: Box<Expr>,
        rest: Vec<(CompareOp, Expr)>,
    },
    Field {
        base: Box<Expr>,
        name: String,
    },
    OldStateField {
        field: ModifiedField,
    },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Literal {
    pub span: Span,
    pub kind: LiteralKind,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum LiteralKind {
    Bool(bool),
    Integer(String),
    Float(String),
    String(String),
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum UnaryOp {
    Not,
    Plus,
    Minus,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BinaryOp {
    Or,
    And,
    Add,
    Subtract,
    Multiply,
    Divide,
    Remainder,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CompareOp {
    Equal,
    NotEqual,
    Less,
    LessEqual,
    Greater,
    GreaterEqual,
}
