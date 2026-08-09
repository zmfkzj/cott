use std::path::PathBuf;

/// An in-memory Cott source file identified by its path.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SourceFile {
    pub path: PathBuf,
    pub text: String,
}

impl SourceFile {
    /// Creates a source file from a path and its in-memory text.
    pub fn new(path: impl Into<PathBuf>, text: impl Into<String>) -> Self {
        Self {
            path: path.into(),
            text: text.into(),
        }
    }
}

/// A parsed source file containing syntax only; no project semantics are checked.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ParsedSource {
    pub path: PathBuf,
    pub cst: crate::syntax::Cst,
    pub syntax: crate::ast::File,
}

/// A syntax diagnostic paired with the source path that produced it.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ProjectDiagnostic {
    pub path: PathBuf,
    pub diagnostic: crate::diagnostics::Diagnostic,
}

/// Successfully parsed project sources, in the order they were provided.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ParsedProject {
    pub sources: Vec<ParsedSource>,
}

/// Parses all provided sources and aggregates syntax errors without semantic validation.
pub fn parse_project(
    sources: impl IntoIterator<Item = SourceFile>,
) -> Result<ParsedProject, Vec<ProjectDiagnostic>> {
    let mut parsed = Vec::new();
    let mut errors = Vec::new();

    for SourceFile { path, text } in sources {
        let parsed_file = crate::syntax::Cst::parse(&text)
            .and_then(|cst| crate::parser::parse_cst(&cst).map(|syntax| (cst, syntax)));
        match parsed_file {
            Ok((cst, syntax)) => parsed.push(ParsedSource { path, cst, syntax }),
            Err(diagnostics) => {
                errors.extend(diagnostics.into_iter().map(|diagnostic| ProjectDiagnostic {
                    path: path.clone(),
                    diagnostic,
                }))
            }
        }
    }

    if errors.is_empty() {
        Ok(ParsedProject { sources: parsed })
    } else {
        Err(errors)
    }
}
