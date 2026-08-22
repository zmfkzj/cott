use std::sync::Arc;

use crate::diagnostics::Span;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Keyword {
    Module,
    Use,
    External,
    Type,
    Alias,
    Newtype,
    Struct,
    Enum,
    Trait,
    Impl,
    For,
    State,
    Fn,
    Const,
    Where,
    Requires,
    Invariant,
    Init,
    Ensures,
    Error,
    When,
    Modifies,
    Old,
    Effects,
    Doc,
    SelfValue,
    True,
    False,
    And,
    Or,
    Not,
    Rule,
    Override,
    Delete,
    Remove,
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
    At,
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

/// Lossless lexical view. `source` preserves every input byte, including
/// comments and trivia that the grammar intentionally skips.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Cst {
    pub source: Arc<[u8]>,
    pub tokens: Vec<Token>,
}

impl Cst {
    pub fn parse(source: &str) -> Result<Self, Vec<crate::diagnostics::Diagnostic>> {
        Ok(Self {
            source: Arc::from(source.as_bytes()),
            tokens: crate::lexer::lex(source)?,
        })
    }
}
