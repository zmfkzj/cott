use std::collections::BTreeMap;
use std::path::PathBuf;

use serde::Serialize;

pub mod code {
    pub const CLI_USAGE: &str = "COTT-C001";
    pub const SYNTAX: &str = "COTT-S001";
    pub const NAME: &str = "COTT-N001";
    pub const INCOMPATIBLE_NOMINAL_TYPES: &str = "COTT-T102";
    pub const CONTRACT: &str = "COTT-K001";
    pub const PYTHON: &str = "COTT-P001";
    pub const AGENT: &str = "COTT-A001";
    pub const FILESYSTEM: &str = "COTT-F001";
    pub const INTERNAL: &str = "COTT-I001";
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct FileId(pub u32);

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct Span {
    pub start: usize,
    pub end: usize,
}

impl Span {
    pub const fn new(start: usize, end: usize) -> Self {
        Self { start, end }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
pub struct SourceSpan {
    pub file: FileId,
    pub start_byte: usize,
    pub end_byte: usize,
}

#[derive(Clone, Debug, Default)]
pub struct SourceMap {
    files: Vec<SourceFile>,
}

#[derive(Clone, Debug)]
struct SourceFile {
    path: PathBuf,
    bytes: Vec<u8>,
    line_starts: Vec<usize>,
}

impl SourceMap {
    pub fn add(&mut self, path: PathBuf, bytes: Vec<u8>) -> FileId {
        let mut line_starts = vec![0];
        line_starts.extend(
            bytes
                .iter()
                .enumerate()
                .filter_map(|(index, byte)| (*byte == b'\n').then_some(index + 1)),
        );
        let id = FileId(self.files.len() as u32);
        self.files.push(SourceFile {
            path,
            bytes,
            line_starts,
        });
        id
    }

    pub fn path(&self, id: FileId) -> Option<&PathBuf> {
        self.files.get(id.0 as usize).map(|file| &file.path)
    }

    pub fn location(&self, span: SourceSpan) -> Option<RenderedSpan> {
        let file = self.files.get(span.file.0 as usize)?;
        let start = location(file, span.start_byte)?;
        let end = location(file, span.end_byte)?;
        Some(RenderedSpan {
            path: file.path.to_string_lossy().replace('\\', "/"),
            start_byte: span.start_byte,
            end_byte: span.end_byte,
            start_line: start.0,
            start_column: start.1,
            end_line: end.0,
            end_column: end.1,
        })
    }
}

fn location(file: &SourceFile, offset: usize) -> Option<(usize, usize)> {
    (offset <= file.bytes.len()).then(|| {
        let line = file.line_starts.partition_point(|start| *start <= offset);
        let line_start = file.line_starts[line - 1];
        let column = std::str::from_utf8(&file.bytes[line_start..offset])
            .map_or(1, |text| text.chars().count() + 1);
        (line, column)
    })
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct RenderedSpan {
    pub path: String,
    pub start_byte: usize,
    pub end_byte: usize,
    pub start_line: usize,
    pub start_column: usize,
    pub end_line: usize,
    pub end_column: usize,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct RelatedDiagnostic {
    pub message: String,
    pub span: Option<SourceSpan>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct Diagnostic {
    pub code: String,
    pub severity: Severity,
    pub message: String,
    #[serde(skip)]
    pub span: Span,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub source_span: Option<SourceSpan>,
    pub expected: Option<String>,
    pub actual: Option<String>,
    pub reason: Option<String>,
    pub help: Vec<String>,
    pub related: Vec<RelatedDiagnostic>,
    pub source_order: usize,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Severity {
    Error,
    Warning,
}

impl Diagnostic {
    pub fn new(message: impl Into<String>, span: Span) -> Self {
        Self::error(code::SYNTAX, message, span)
    }

    pub fn error(code: impl Into<String>, message: impl Into<String>, span: Span) -> Self {
        Self {
            code: code.into(),
            severity: Severity::Error,
            message: message.into(),
            span,
            source_span: None,
            expected: None,
            actual: None,
            reason: None,
            help: Vec::new(),
            related: Vec::new(),
            source_order: 0,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DiagnosticReport {
    pub diagnostics: Vec<Diagnostic>,
}

impl DiagnosticReport {
    pub fn canonical_json(&self, sources: &SourceMap) -> Result<Vec<u8>, serde_json::Error> {
        let diagnostics = self
            .diagnostics
            .iter()
            .map(|diagnostic| {
                let mut object = BTreeMap::new();
                object.insert("actual", serde_json::json!(diagnostic.actual));
                object.insert("code", serde_json::json!(diagnostic.code));
                object.insert("expected", serde_json::json!(diagnostic.expected));
                object.insert("help", serde_json::json!(diagnostic.help));
                object.insert("message", serde_json::json!(diagnostic.message));
                object.insert(
                    "related",
                    serde_json::json!(
                        diagnostic
                            .related
                            .iter()
                            .map(|related| serde_json::json!({
                                "message": related.message,
                                "span": related.span.and_then(|span| sources.location(span)),
                            }))
                            .collect::<Vec<_>>()
                    ),
                );
                object.insert("reason", serde_json::json!(diagnostic.reason));
                object.insert("severity", serde_json::json!(diagnostic.severity));
                object.insert(
                    "span",
                    serde_json::json!(
                        diagnostic
                            .source_span
                            .and_then(|span| sources.location(span))
                    ),
                );
                object.insert("source_order", serde_json::json!(diagnostic.source_order));
                serde_json::Value::Object(
                    object
                        .into_iter()
                        .map(|(key, value)| (key.to_owned(), value))
                        .collect(),
                )
            })
            .collect::<Vec<_>>();
        let mut bytes = serde_json::to_vec(&serde_json::json!({
            "schema_version": 1,
            "diagnostics": diagnostics,
        }))?;
        bytes.push(b'\n');
        Ok(bytes)
    }
}
