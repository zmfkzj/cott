use crate::diagnostics::Span;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Keyword {
    Module,
    Use,
    Alias,
    Newtype,
    Struct,
    Enum,
    Trait,
    Const,
    Fn,
    Where,
    Requires,
    Ensures,
    Error,
    When,
    Effects,
    Doc,
    SelfValue,
    True,
    False,
    And,
    Or,
    Not,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum TokenKind {
    Name(String),
    Integer(String),
    Float(String),
    String(String),
    TripleString(String),
    Keyword(Keyword),
    Newline,
    Indent,
    Dedent,
    Eof,
    Dot,
    Comma,
    Colon,
    Equal,
    Arrow,
    FatArrow,
    LParen,
    RParen,
    LBracket,
    RBracket,
    LBrace,
    RBrace,
    Plus,
    Minus,
    Star,
    Slash,
    Percent,
    EqualEqual,
    NotEqual,
    Less,
    LessEqual,
    Greater,
    GreaterEqual,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Token {
    pub kind: TokenKind,
    pub span: Span,
}

impl Token {
    pub const fn new(kind: TokenKind, span: Span) -> Self {
        Self { kind, span }
    }
}
