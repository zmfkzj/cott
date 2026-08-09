use crate::ast::File;
use crate::diagnostics::{Diagnostic, Span};
use crate::syntax::Cst;

/// Formats only representation the parser proves is trivia: newline encoding
/// and the final physical newline. Literal and comment bytes remain untouched.
pub fn format(cst: &Cst, _ast: &File) -> Result<Vec<u8>, Diagnostic> {
    let source = std::str::from_utf8(&cst.source).map_err(|_| {
        Diagnostic::error(
            crate::diagnostics::code::SYNTAX,
            "source is not UTF-8",
            Span::new(0, cst.source.len()),
        )
    })?;
    let mut rendered = source
        .replace("\r\n", "\n")
        .replace('\r', "\n")
        .into_bytes();
    while rendered.last() == Some(&b'\n') {
        rendered.pop();
    }
    rendered.push(b'\n');
    Ok(rendered)
}
