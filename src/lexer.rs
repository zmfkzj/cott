use crate::diagnostics::{Diagnostic, Span};
use crate::syntax::{Keyword, Token, TokenKind};

/// Tokenize a cott source file while preserving byte-accurate source spans.
///
/// Layout is intentionally the only bit of structure handled here: names and
/// literals are not resolved, and delimiter contents are not parsed.
pub fn lex(source: &str) -> Result<Vec<Token>, Vec<Diagnostic>> {
    let bytes = source.as_bytes();
    let mut tokens = Vec::new();
    let mut diagnostics = Vec::new();
    let mut indent_stack = vec![0usize];
    let mut delimiters: Vec<u8> = Vec::new();
    let mut i = 0usize;
    let mut line_start = true;
    let mut line_code = false;

    while i < bytes.len() {
        if line_start {
            let ws_start = i;
            let mut columns = 0usize;
            while i < bytes.len() {
                match bytes[i] {
                    b' ' => {
                        columns += 1;
                        i += 1;
                    }
                    b'\t' => {
                        diagnostics.push(Diagnostic::new(
                            "tabs are not allowed in source indentation",
                            Span {
                                start: i,
                                end: i + 1,
                            },
                        ));
                        i += 1;
                    }
                    _ => break,
                }
            }

            // Blank and comment-only physical lines do not participate in
            // indentation, even when they contain leading spaces.
            if i == bytes.len() {
                break;
            }
            if bytes[i] == b'#' {
                while i < bytes.len() && !is_newline(bytes[i]) {
                    i += 1;
                }
                if i == bytes.len() {
                    break;
                }
            } else if is_newline(bytes[i]) {
                // Handled by the common newline path below.
            } else if delimiters.is_empty() {
                let previous = *indent_stack.last().unwrap_or(&0);
                if columns > previous {
                    indent_stack.push(columns);
                    tokens.push(Token::new(
                        TokenKind::Indent,
                        Span {
                            start: ws_start,
                            end: i,
                        },
                    ));
                } else if columns < previous {
                    while indent_stack.len() > 1 && columns < *indent_stack.last().unwrap_or(&0) {
                        indent_stack.pop();
                        tokens.push(Token::new(
                            TokenKind::Dedent,
                            Span {
                                start: ws_start,
                                end: i,
                            },
                        ));
                    }
                    if columns != *indent_stack.last().unwrap_or(&0) {
                        diagnostics.push(Diagnostic::new(
                            "inconsistent space indentation",
                            Span {
                                start: ws_start,
                                end: i,
                            },
                        ));
                        // Keep later lines usable without manufacturing an
                        // indentation level that was never established.
                    }
                }
                line_start = false;
            } else {
                // Whitespace inside an open delimiter is not layout.
                line_start = false;
            }
        }

        if i >= bytes.len() {
            break;
        }

        if is_newline(bytes[i]) {
            let start = i;
            i += 1;
            if bytes[start] == b'\r' && i < bytes.len() && bytes[i] == b'\n' {
                i += 1;
            }
            if line_code && delimiters.is_empty() {
                tokens.push(Token::new(TokenKind::Newline, Span { start, end: i }));
            }
            line_start = true;
            line_code = false;
            continue;
        }

        if bytes[i] == b'#' {
            while i < bytes.len() && !is_newline(bytes[i]) {
                i += 1;
            }
            continue;
        }

        match bytes[i] {
            b' ' => {
                i += 1;
            }
            b'\t' => {
                diagnostics.push(Diagnostic::new(
                    "tabs are not allowed in source",
                    Span {
                        start: i,
                        end: i + 1,
                    },
                ));
                i += 1;
            }
            b';' => {
                diagnostics.push(Diagnostic::new(
                    "semicolons are not allowed",
                    Span {
                        start: i,
                        end: i + 1,
                    },
                ));
                i += 1;
                line_code = true;
            }
            b'"' => {
                let start = i;
                if source[i..].starts_with("\"\"\"") {
                    let (end, value) = scan_triple_string(source, i, &mut diagnostics);
                    i = end;
                    tokens.push(Token::new(
                        TokenKind::TripleString(value),
                        Span { start, end },
                    ));
                } else {
                    let (end, value) = scan_string(source, i, &mut diagnostics);
                    i = end;
                    tokens.push(Token::new(TokenKind::String(value), Span { start, end }));
                }
                line_code = true;
            }
            b'_' | b'A'..=b'Z' | b'a'..=b'z' => {
                let start = i;
                i += 1;
                while i < bytes.len()
                    && matches!(bytes[i], b'_' | b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9')
                {
                    i += 1;
                }
                let word = &source[start..i];
                let kind = keyword(word)
                    .map(TokenKind::Keyword)
                    .unwrap_or_else(|| TokenKind::Name(word.to_owned()));
                tokens.push(Token::new(kind, Span { start, end: i }));
                line_code = true;
            }
            b'0'..=b'9' => {
                let start = i;
                let mut float = false;
                while i < bytes.len() && bytes[i].is_ascii_digit() {
                    i += 1;
                }
                if i < bytes.len() && bytes[i] == b'.' {
                    float = true;
                    i += 1;
                    while i < bytes.len() && bytes[i].is_ascii_digit() {
                        i += 1;
                    }
                }
                if i < bytes.len() && matches!(bytes[i], b'e' | b'E') {
                    float = true;
                    let exponent = i;
                    i += 1;
                    if i < bytes.len() && matches!(bytes[i], b'+' | b'-') {
                        i += 1;
                    }
                    let digits = i;
                    while i < bytes.len() && bytes[i].is_ascii_digit() {
                        i += 1;
                    }
                    if digits == i {
                        diagnostics.push(Diagnostic::new(
                            "malformed decimal exponent",
                            Span {
                                start: exponent,
                                end: i,
                            },
                        ));
                    }
                }
                let text = source[start..i].to_owned();
                let kind = if float {
                    TokenKind::Float(text)
                } else {
                    TokenKind::Integer(text)
                };
                tokens.push(Token::new(kind, Span { start, end: i }));
                line_code = true;
            }
            // Longest operators must be checked before their one-character
            // prefixes.
            b'=' if starts_with(bytes, i, b"==") => {
                tokens.push(simple(TokenKind::EqualEqual, i, i + 2));
                i += 2;
                line_code = true;
            }
            b'!' if starts_with(bytes, i, b"!=") => {
                tokens.push(simple(TokenKind::NotEqual, i, i + 2));
                i += 2;
                line_code = true;
            }
            b'<' if starts_with(bytes, i, b"<=") => {
                tokens.push(simple(TokenKind::LessEqual, i, i + 2));
                i += 2;
                line_code = true;
            }
            b'>' if starts_with(bytes, i, b">=") => {
                tokens.push(simple(TokenKind::GreaterEqual, i, i + 2));
                i += 2;
                line_code = true;
            }
            b'-' if starts_with(bytes, i, b"->") => {
                tokens.push(simple(TokenKind::Arrow, i, i + 2));
                i += 2;
                line_code = true;
            }
            b'=' if starts_with(bytes, i, b"=>") => {
                tokens.push(simple(TokenKind::FatArrow, i, i + 2));
                i += 2;
                line_code = true;
            }
            b'.' => {
                tokens.push(simple(TokenKind::Dot, i, i + 1));
                i += 1;
                line_code = true;
            }
            b',' => {
                tokens.push(simple(TokenKind::Comma, i, i + 1));
                i += 1;
                line_code = true;
            }
            b':' => {
                tokens.push(simple(TokenKind::Colon, i, i + 1));
                i += 1;
                line_code = true;
            }
            b'=' => {
                tokens.push(simple(TokenKind::Equal, i, i + 1));
                i += 1;
                line_code = true;
            }
            b'(' => {
                delimiters.push(b')');
                tokens.push(simple(TokenKind::LParen, i, i + 1));
                i += 1;
                line_code = true;
            }
            b')' => {
                pop_delimiter(&mut delimiters, b')');
                tokens.push(simple(TokenKind::RParen, i, i + 1));
                i += 1;
                line_code = true;
            }
            b'[' => {
                delimiters.push(b']');
                tokens.push(simple(TokenKind::LBracket, i, i + 1));
                i += 1;
                line_code = true;
            }
            b']' => {
                pop_delimiter(&mut delimiters, b']');
                tokens.push(simple(TokenKind::RBracket, i, i + 1));
                i += 1;
                line_code = true;
            }
            b'{' => {
                delimiters.push(b'}');
                tokens.push(simple(TokenKind::LBrace, i, i + 1));
                i += 1;
                line_code = true;
            }
            b'}' => {
                pop_delimiter(&mut delimiters, b'}');
                tokens.push(simple(TokenKind::RBrace, i, i + 1));
                i += 1;
                line_code = true;
            }
            b'+' => {
                tokens.push(simple(TokenKind::Plus, i, i + 1));
                i += 1;
                line_code = true;
            }
            b'-' => {
                tokens.push(simple(TokenKind::Minus, i, i + 1));
                i += 1;
                line_code = true;
            }
            b'*' => {
                tokens.push(simple(TokenKind::Star, i, i + 1));
                i += 1;
                line_code = true;
            }
            b'/' => {
                tokens.push(simple(TokenKind::Slash, i, i + 1));
                i += 1;
                line_code = true;
            }
            b'%' => {
                tokens.push(simple(TokenKind::Percent, i, i + 1));
                i += 1;
                line_code = true;
            }
            b'<' => {
                tokens.push(simple(TokenKind::Less, i, i + 1));
                i += 1;
                line_code = true;
            }
            b'>' => {
                tokens.push(simple(TokenKind::Greater, i, i + 1));
                i += 1;
                line_code = true;
            }
            b'@' => {
                tokens.push(simple(TokenKind::At, i, i + 1));
                i += 1;
                line_code = true;
            }
            b'!' => {
                diagnostics.push(Diagnostic::new(
                    "invalid character `!`",
                    Span {
                        start: i,
                        end: i + 1,
                    },
                ));
                i += 1;
                line_code = true;
            }
            _ => {
                let end = source[i..]
                    .chars()
                    .next()
                    .map(|ch| i + ch.len_utf8())
                    .unwrap_or(i + 1);
                diagnostics.push(Diagnostic::new("invalid character", Span { start: i, end }));
                i = end;
                line_code = true;
            }
        }
    }

    // A final physical line without a newline still terminates its logical
    // line. Delimiters suppress this just as they suppress physical newlines.
    if line_code && delimiters.is_empty() {
        tokens.push(Token::new(
            TokenKind::Newline,
            Span {
                start: bytes.len(),
                end: bytes.len(),
            },
        ));
    }
    while indent_stack.len() > 1 {
        indent_stack.pop();
        tokens.push(Token::new(
            TokenKind::Dedent,
            Span {
                start: bytes.len(),
                end: bytes.len(),
            },
        ));
    }
    tokens.push(Token::new(
        TokenKind::Eof,
        Span {
            start: bytes.len(),
            end: bytes.len(),
        },
    ));

    if diagnostics.is_empty() {
        Ok(tokens)
    } else {
        Err(diagnostics)
    }
}

fn simple(kind: TokenKind, start: usize, end: usize) -> Token {
    Token::new(kind, Span { start, end })
}

fn starts_with(bytes: &[u8], start: usize, expected: &[u8]) -> bool {
    bytes.get(start..start + expected.len()) == Some(expected)
}

fn is_newline(byte: u8) -> bool {
    byte == b'\n' || byte == b'\r'
}

fn pop_delimiter(delimiters: &mut Vec<u8>, closing: u8) {
    if delimiters.last().copied() == Some(closing) {
        delimiters.pop();
    }
}

fn keyword(word: &str) -> Option<Keyword> {
    Some(match word {
        "module" => Keyword::Module,
        "use" => Keyword::Use,
        "external" => Keyword::External,
        "type" => Keyword::Type,
        "alias" => Keyword::Alias,
        "newtype" => Keyword::Newtype,
        "where" => Keyword::Where,
        "struct" => Keyword::Struct,
        "enum" => Keyword::Enum,
        "trait" => Keyword::Trait,
        "impl" => Keyword::Impl,
        "for" => Keyword::For,
        "state" => Keyword::State,
        "const" => Keyword::Const,
        "fn" => Keyword::Fn,
        "self" => Keyword::SelfValue,
        "doc" => Keyword::Doc,
        "requires" => Keyword::Requires,
        "invariant" => Keyword::Invariant,
        "init" => Keyword::Init,
        "ensures" => Keyword::Ensures,
        "when" => Keyword::When,
        "effects" => Keyword::Effects,
        "modifies" => Keyword::Modifies,
        "old" => Keyword::Old,
        "error" => Keyword::Error,
        "true" => Keyword::True,
        "false" => Keyword::False,
        "and" => Keyword::And,
        "or" => Keyword::Or,
        "not" => Keyword::Not,
        "rule" => Keyword::Rule,
        "override" => Keyword::Override,
        "delete" => Keyword::Delete,
        "remove" => Keyword::Remove,
        _ => return None,
    })
}

fn scan_triple_string(
    source: &str,
    start: usize,
    diagnostics: &mut Vec<Diagnostic>,
) -> (usize, String) {
    let bytes = source.as_bytes();
    let mut i = start + 3;
    while i + 2 < bytes.len() {
        if bytes[i] == b'\t' {
            diagnostics.push(Diagnostic::new(
                "tabs are not allowed in source",
                Span {
                    start: i,
                    end: i + 1,
                },
            ));
        }
        if starts_with(bytes, i, b"\"\"\"") {
            let end = i + 3;
            return (end, source[start + 3..i].to_owned());
        }
        i += 1;
    }
    diagnostics.push(Diagnostic::new(
        "unterminated triple-quoted string",
        Span {
            start,
            end: bytes.len(),
        },
    ));
    (bytes.len(), source[start + 3..].to_owned())
}

fn scan_string(source: &str, start: usize, diagnostics: &mut Vec<Diagnostic>) -> (usize, String) {
    let bytes = source.as_bytes();
    let mut i = start + 1;
    let mut value = String::new();
    let mut malformed = false;

    while i < bytes.len() {
        match bytes[i] {
            b'"' => return (i + 1, value),
            b'\\' => {
                i += 1;
                if i >= bytes.len() {
                    malformed_string(diagnostics, start, bytes.len(), &mut malformed);
                    break;
                }
                match bytes[i] {
                    b'"' => {
                        value.push('"');
                        i += 1;
                    }
                    b'\\' => {
                        value.push('\\');
                        i += 1;
                    }
                    b'/' => {
                        value.push('/');
                        i += 1;
                    }
                    b'b' => {
                        value.push('\u{0008}');
                        i += 1;
                    }
                    b'f' => {
                        value.push('\u{000c}');
                        i += 1;
                    }
                    b'n' => {
                        value.push('\n');
                        i += 1;
                    }
                    b'r' => {
                        value.push('\r');
                        i += 1;
                    }
                    b't' => {
                        value.push('\t');
                        i += 1;
                    }
                    b'u' => {
                        let (after, code) = unicode_escape(source, i + 1);
                        i = after;
                        match code {
                            Some(high) if (0xD800..=0xDBFF).contains(&high) => {
                                if starts_with(bytes, i, b"\\u") {
                                    let (after_low, low) = unicode_escape(source, i + 2);
                                    if let Some(low) = low.filter(|v| (0xDC00..=0xDFFF).contains(v))
                                    {
                                        let scalar = 0x10000
                                            + ((high as u32 - 0xD800) << 10)
                                            + (low as u32 - 0xDC00);
                                        if let Some(ch) = char::from_u32(scalar) {
                                            value.push(ch);
                                            i = after_low;
                                        } else {
                                            malformed_string(diagnostics, start, i, &mut malformed);
                                        }
                                    } else {
                                        malformed_string(diagnostics, start, i, &mut malformed);
                                    }
                                } else {
                                    malformed_string(diagnostics, start, i, &mut malformed);
                                }
                            }
                            Some(code) if (0xDC00..=0xDFFF).contains(&code) => {
                                malformed_string(diagnostics, start, i, &mut malformed);
                            }
                            Some(code) => {
                                if let Some(ch) = char::from_u32(code as u32) {
                                    value.push(ch);
                                } else {
                                    malformed_string(diagnostics, start, i, &mut malformed);
                                }
                            }
                            None => malformed_string(diagnostics, start, i, &mut malformed),
                        }
                    }
                    _ => {
                        malformed_string(diagnostics, start, i + 1, &mut malformed);
                        i += 1;
                    }
                }
            }
            b'\n' | b'\r' => {
                malformed_string(diagnostics, start, i, &mut malformed);
                break;
            }
            b if b < 0x20 => {
                malformed_string(diagnostics, start, i + 1, &mut malformed);
                i += 1;
            }
            _ => {
                if let Some(ch) = source[i..].chars().next() {
                    value.push(ch);
                    i += ch.len_utf8();
                } else {
                    i += 1;
                }
            }
        }
    }

    malformed_string(diagnostics, start, bytes.len(), &mut malformed);
    (i, value)
}

fn unicode_escape(source: &str, start: usize) -> (usize, Option<u16>) {
    let bytes = source.as_bytes();
    let end = start.saturating_add(4).min(bytes.len());
    if end - start < 4 {
        return (end, None);
    }
    let mut value = 0u16;
    for &byte in &bytes[start..end] {
        let digit = match byte {
            b'0'..=b'9' => byte - b'0',
            b'a'..=b'f' => byte - b'a' + 10,
            b'A'..=b'F' => byte - b'A' + 10,
            _ => return (end, None),
        };
        value = (value << 4) | u16::from(digit);
    }
    (end, Some(value))
}

fn malformed_string(
    diagnostics: &mut Vec<Diagnostic>,
    start: usize,
    end: usize,
    emitted: &mut bool,
) {
    if !*emitted {
        diagnostics.push(Diagnostic::new(
            "malformed or unterminated string literal",
            Span { start, end },
        ));
        *emitted = true;
    }
}
