use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::path::{Path, PathBuf};
use std::sync::Mutex;

use tower_lsp::jsonrpc::Result;
use tower_lsp::lsp_types::*;
use tower_lsp::{Client, LanguageServer, LspService, Server};

use crate::ast::{self, Declaration, DocBlock};
use crate::compiler::{self, ParsedProject, SourceFile};
use crate::diagnostics::{Diagnostic as CompilerDiagnostic, Span};

const BUILTIN_TYPES: &[&str] = &[
    "Bool",
    "I8",
    "I16",
    "I32",
    "I64",
    "U8",
    "U16",
    "U32",
    "U64",
    "F32",
    "F64",
    "Str",
    "Bytes",
    "Path",
    "Unit",
    "JsonValue",
    "Never",
    "List",
    "Set",
    "Map",
    "Tuple",
    "Option",
    "Result",
    "Opaque",
    "Any",
    "Unknown",
    "Iterator",
    "Generator",
    "Factory",
];

struct Backend {
    client: Client,
    state: Mutex<State>,
}

#[derive(Default)]
struct State {
    documents: HashMap<Url, String>,
    published: HashSet<Url>,
}
impl State {
    fn snapshot(&self) -> Vec<(Url, String)> {
        self.documents
            .iter()
            .map(|(uri, text)| (uri.clone(), text.clone()))
            .collect()
    }

    fn close(&mut self, uri: &Url) {
        self.documents.remove(uri);
        self.published.remove(uri);
    }
}

fn active_documents(documents: &[(Url, String)]) -> HashSet<Url> {
    documents.iter().map(|(uri, _)| uri.clone()).collect()
}

#[derive(Clone)]
struct Symbol {
    name: String,
    module: Vec<String>,
    path: PathBuf,
    span: Span,
    signature: String,
    doc: Option<String>,
}

#[derive(Clone)]
struct Local {
    name: String,
    path: PathBuf,
    span: Span,
    scope: Span,
    signature: String,
}

#[derive(Clone)]
struct SourceInfo {
    path: PathBuf,
    module: Vec<String>,
    uses: Vec<ast::UseDecl>,
}

struct Analysis {
    root: PathBuf,
    texts: BTreeMap<PathBuf, String>,
    diagnostics: BTreeMap<PathBuf, Vec<CompilerDiagnostic>>,
    sources: Vec<SourceInfo>,
    symbols: Vec<Symbol>,
    locals: Vec<Local>,
}

impl Backend {
    fn new(client: Client) -> Self {
        Self {
            client,
            state: Mutex::new(State::default()),
        }
    }

    async fn refresh(&self) {
        let documents = self
            .state
            .lock()
            .expect("LSP state lock poisoned")
            .snapshot();
        let analysis = analyze_documents(&documents);
        let active = active_documents(&documents);
        let stale = {
            let mut state = self.state.lock().expect("LSP state lock poisoned");
            let stale = state
                .published
                .difference(&active)
                .cloned()
                .collect::<Vec<_>>();
            state.published = active.clone();
            stale
        };
        for uri in stale {
            self.client.publish_diagnostics(uri, Vec::new(), None).await;
        }
        for uri in active {
            let path = uri.to_file_path().ok();
            let diagnostics = path
                .as_ref()
                .and_then(|path| analysis_path(&analysis, path))
                .and_then(|path| analysis.texts.get(path).map(|text| (path, text)))
                .map(|(path, text)| {
                    analysis
                        .diagnostics
                        .get(path)
                        .into_iter()
                        .flatten()
                        .map(|diagnostic| lsp_diagnostic(diagnostic, text))
                        .collect()
                })
                .unwrap_or_default();
            self.client
                .publish_diagnostics(uri, diagnostics, None)
                .await;
        }
    }

    fn analysis(&self) -> Analysis {
        let documents = self
            .state
            .lock()
            .expect("LSP state lock poisoned")
            .snapshot();
        analyze_documents(&documents)
    }
}

#[tower_lsp::async_trait]
impl LanguageServer for Backend {
    async fn initialize(&self, _: InitializeParams) -> Result<InitializeResult> {
        Ok(InitializeResult {
            capabilities: ServerCapabilities {
                position_encoding: Some(PositionEncodingKind::UTF16),
                text_document_sync: Some(TextDocumentSyncCapability::Kind(
                    TextDocumentSyncKind::FULL,
                )),
                completion_provider: Some(CompletionOptions {
                    trigger_characters: Some(vec![".".to_owned()]),
                    ..CompletionOptions::default()
                }),
                hover_provider: Some(HoverProviderCapability::Simple(true)),
                definition_provider: Some(OneOf::Left(true)),
                ..ServerCapabilities::default()
            },
            server_info: Some(ServerInfo {
                name: "cott".to_owned(),
                version: None,
            }),
        })
    }

    async fn initialized(&self, _: InitializedParams) {}

    async fn shutdown(&self) -> Result<()> {
        Ok(())
    }

    async fn did_open(&self, params: DidOpenTextDocumentParams) {
        self.state
            .lock()
            .expect("LSP state lock poisoned")
            .documents
            .insert(params.text_document.uri, params.text_document.text);
        self.refresh().await;
    }

    async fn did_change(&self, params: DidChangeTextDocumentParams) {
        if let Some(change) = params.content_changes.into_iter().last() {
            self.state
                .lock()
                .expect("LSP state lock poisoned")
                .documents
                .insert(params.text_document.uri, change.text);
            self.refresh().await;
        }
    }

    async fn did_close(&self, params: DidCloseTextDocumentParams) {
        let uri = params.text_document.uri;
        {
            let mut state = self.state.lock().expect("LSP state lock poisoned");
            state.close(&uri);
        }
        self.client.publish_diagnostics(uri, Vec::new(), None).await;
        self.refresh().await;
    }

    async fn completion(&self, _: CompletionParams) -> Result<Option<CompletionResponse>> {
        let analysis = self.analysis();
        let mut items = BTreeMap::<String, CompletionItem>::new();
        for &keyword in all_keywords() {
            items.insert(
                keyword.to_owned(),
                CompletionItem {
                    label: keyword.to_owned(),
                    kind: Some(CompletionItemKind::KEYWORD),
                    ..CompletionItem::default()
                },
            );
        }
        for &ty in BUILTIN_TYPES {
            items.insert(
                ty.to_owned(),
                CompletionItem {
                    label: ty.to_owned(),
                    kind: Some(CompletionItemKind::CLASS),
                    detail: Some("built-in type".to_owned()),
                    ..CompletionItem::default()
                },
            );
        }
        for symbol in analysis.symbols {
            items.insert(
                symbol.name.clone(),
                CompletionItem {
                    label: symbol.name,
                    kind: Some(CompletionItemKind::REFERENCE),
                    detail: Some(symbol.signature),
                    documentation: symbol.doc.map(Documentation::String),
                    ..CompletionItem::default()
                },
            );
        }
        Ok(Some(CompletionResponse::Array(
            items.into_values().collect(),
        )))
    }

    async fn hover(&self, params: HoverParams) -> Result<Option<Hover>> {
        let position = params.text_document_position_params.position;
        let uri = params.text_document_position_params.text_document.uri;
        let analysis = self.analysis();
        let Some((path, text)) = source_for_uri(&analysis, &uri) else {
            return Ok(None);
        };
        let Some((name, span, qualified)) = word_at(text, position) else {
            return Ok(None);
        };
        let Some(symbol) = resolve(&analysis, path, &name, &qualified, &span) else {
            return Ok(builtin_hover(&name, text, span));
        };
        let mut value = format!("```cott\n{}\n```", symbol.signature);
        if let Some(doc) = symbol.doc {
            value.push_str("\n\n");
            value.push_str(&doc);
        }
        Ok(Some(Hover {
            contents: HoverContents::Markup(MarkupContent {
                kind: MarkupKind::Markdown,
                value,
            }),
            range: Some(range_for(text, span)),
        }))
    }

    async fn goto_definition(
        &self,
        params: GotoDefinitionParams,
    ) -> Result<Option<GotoDefinitionResponse>> {
        let position = params.text_document_position_params.position;
        let uri = params.text_document_position_params.text_document.uri;
        let analysis = self.analysis();
        let Some((path, text)) = source_for_uri(&analysis, &uri) else {
            return Ok(None);
        };
        let Some((name, span, qualified)) = word_at(text, position) else {
            return Ok(None);
        };
        let Some(symbol) = resolve(&analysis, path, &name, &qualified, &span) else {
            return Ok(None);
        };
        let Some(target_uri) = uri_for(&symbol.path, &analysis.root) else {
            return Ok(None);
        };
        let Some(target_text) = analysis.texts.get(&symbol.path) else {
            return Ok(None);
        };
        Ok(Some(GotoDefinitionResponse::Scalar(Location {
            uri: target_uri,
            range: range_for(target_text, symbol.span),
        })))
    }
}

/// Starts the stdio language server. No messages are written to stdout outside JSON-RPC.
pub fn run() -> i32 {
    let runtime = match tokio::runtime::Builder::new_multi_thread()
        .enable_io()
        .build()
    {
        Ok(runtime) => runtime,
        Err(_) => return 1,
    };
    runtime.block_on(async {
        let (service, socket) = LspService::new(Backend::new);
        Server::new(tokio::io::stdin(), tokio::io::stdout(), socket)
            .serve(service)
            .await;
    });
    0
}

fn analyze_documents(documents: &[(Url, String)]) -> Analysis {
    let mut documents = documents
        .iter()
        .filter_map(|(uri, text)| uri.to_file_path().ok().map(|path| (path, text.clone())))
        .collect::<Vec<_>>();
    documents.sort_by(|left, right| left.0.cmp(&right.0));
    let project = documents
        .iter()
        .find_map(|(path, _)| discover_project(path));
    if let Some((config, paths)) = project {
        if let Ok(mut sources) = crate::project::discover_sources_from_paths(&paths) {
            for (path, text) in &documents {
                let Ok(path) = path.strip_prefix(&paths.source_dir) else {
                    continue;
                };
                if let Some(source) = sources.iter_mut().find(|source| source.path == path) {
                    source.text = text.clone();
                } else if path
                    .extension()
                    .is_some_and(|extension| extension == "cott")
                {
                    sources.push(SourceFile::new(path, text));
                }
            }
            sources.sort_by(|left, right| left.path.cmp(&right.path));
            let effects = config.effects.keys().cloned().collect();
            return analyze_sources(sources, Some(paths.source_dir), effects);
        }
    }
    analyze_sources(
        documents
            .into_iter()
            .filter(|(path, _)| {
                path.extension()
                    .is_some_and(|extension| extension == "cott")
            })
            .map(|(path, text)| SourceFile::new(path, text))
            .collect(),
        None,
        BTreeSet::new(),
    )
}

fn discover_project(
    path: &Path,
) -> Option<(crate::manifest::ProjectConfig, crate::project::ProjectPaths)> {
    path.parent()?.ancestors().find_map(|root| {
        root.join("cott.toml")
            .is_file()
            .then(|| crate::project::load_config_with_paths(root).ok())
            .flatten()
    })
}

fn source_root_from_modules(parsed: &ParsedProject) -> Option<PathBuf> {
    let mut roots = parsed.sources.iter().filter_map(|source| {
        let mut root = source.path.parent()?.to_path_buf();
        for _ in 1..source.syntax.module.path.segments.len() {
            root.pop();
        }
        Some(root)
    });
    let mut root = roots.next()?;
    for candidate in roots {
        while !candidate.starts_with(&root) {
            root.pop();
        }
    }
    Some(root)
}

fn analyze_sources(
    sources: Vec<SourceFile>,
    root: Option<PathBuf>,
    effects: BTreeSet<String>,
) -> Analysis {
    let texts = sources
        .iter()
        .map(|source| (source.path.clone(), source.text.clone()))
        .collect::<BTreeMap<_, _>>();
    let mut analysis = Analysis {
        root: root.clone().unwrap_or_default(),
        texts,
        diagnostics: BTreeMap::new(),
        sources: Vec::new(),
        symbols: Vec::new(),
        locals: Vec::new(),
    };
    let parsed = match compiler::parse_project(sources) {
        Ok(parsed) => parsed,
        Err(diagnostics) => {
            for diagnostic in diagnostics {
                analysis
                    .diagnostics
                    .entry(diagnostic.path)
                    .or_default()
                    .push(diagnostic.diagnostic);
            }
            return analysis;
        }
    };
    if root.is_none()
        && parsed
            .sources
            .iter()
            .all(|source| source.path.is_absolute())
    {
        analysis.root = source_root_from_modules(&parsed).unwrap_or(analysis.root.clone());
    }
    collect_symbols(&parsed, &mut analysis);
    if let Err(diagnostics) = crate::hir::lower_with_effects(&analysis.root, parsed, &effects) {
        for diagnostic in diagnostics {
            analysis
                .diagnostics
                .entry(diagnostic.path)
                .or_default()
                .push(diagnostic.diagnostic);
        }
    }
    analysis
}
fn collect_symbols(parsed: &ParsedProject, analysis: &mut Analysis) {
    for source in &parsed.sources {
        let module = source.syntax.module.path.segments.clone();
        analysis.sources.push(SourceInfo {
            path: source.path.clone(),
            module: module.clone(),
            uses: source.syntax.uses.clone(),
        });
        let Some(text) = analysis.texts.get(&source.path) else {
            continue;
        };
        for declaration in &source.syntax.declarations {
            let Some((name, doc)) = declaration_name_and_doc(declaration) else {
                continue;
            };
            let Some(span) = name_span(&source.cst, declaration.span(), name) else {
                continue;
            };
            analysis.symbols.push(Symbol {
                name: name.to_owned(),
                module: module.clone(),
                path: source.path.clone(),
                span,
                signature: declaration_signature(text, declaration.span()),
                doc: doc.map(|doc| doc.text.clone()),
            });
            collect_locals(
                declaration,
                &source.cst,
                &source.path,
                text,
                &mut analysis.locals,
            );
        }
    }
    analysis.symbols.sort_by(|left, right| {
        (&left.module, &left.name, &left.path, left.span.start).cmp(&(
            &right.module,
            &right.name,
            &right.path,
            right.span.start,
        ))
    });
}

fn declaration_name_and_doc(declaration: &Declaration) -> Option<(&str, Option<&DocBlock>)> {
    match declaration {
        Declaration::ExternalType(value) => Some((&value.name, value.doc.as_ref())),
        Declaration::Alias(value) => Some((&value.name, value.doc.as_ref())),
        Declaration::Newtype(value) => Some((&value.name, value.doc.as_ref())),
        Declaration::Struct(value) => Some((&value.name, value.doc.as_ref())),
        Declaration::Enum(value) => Some((&value.name, value.doc.as_ref())),
        Declaration::Trait(value) => Some((&value.name, value.doc.as_ref())),
        Declaration::Const(value) => Some((&value.name, value.doc.as_ref())),
        Declaration::Function(value) => Some((&value.name, None)),
        Declaration::Impl(value) => Some((&value.name, None)),
        Declaration::Rule(value) => Some((&value.name, value.doc.as_ref())),
    }
}

fn collect_locals(
    declaration: &Declaration,
    cst: &crate::syntax::Cst,
    path: &Path,
    text: &str,
    locals: &mut Vec<Local>,
) {
    let (scope, parameters): (&Span, Vec<&ast::Parameter>) = match declaration {
        Declaration::Function(value) => (&value.span, value.parameters.iter().collect()),
        _ => return,
    };
    for parameter in parameters {
        if let Some(span) = name_span(cst, &parameter.span, &parameter.name) {
            locals.push(Local {
                name: parameter.name.clone(),
                path: path.to_path_buf(),
                span,
                scope: scope.clone(),
                signature: declaration_signature(text, &parameter.span),
            });
        }
    }
}

fn name_span(cst: &crate::syntax::Cst, enclosing: &Span, name: &str) -> Option<Span> {
    cst.tokens.iter().find_map(|token| {
        (token.span.start >= enclosing.start
            && token.span.end <= enclosing.end
            && matches!(&token.kind, crate::syntax::TokenKind::Name(value) if value == name))
        .then(|| token.span.clone())
    })
}

fn declaration_signature(text: &str, span: &Span) -> String {
    text.get(span.start..span.end)
        .and_then(|source| source.lines().find(|line| !line.trim().is_empty()))
        .map(str::trim)
        .unwrap_or_default()
        .to_owned()
}

fn source_for_uri<'a>(analysis: &'a Analysis, uri: &Url) -> Option<(&'a PathBuf, &'a str)> {
    let path = uri.to_file_path().ok()?;
    let path = analysis_path(analysis, &path)?;
    analysis.texts.get(path).map(|text| (path, text.as_str()))
}

fn analysis_path<'a>(analysis: &'a Analysis, path: &Path) -> Option<&'a PathBuf> {
    analysis
        .texts
        .keys()
        .find(|candidate| path_for(candidate, &analysis.root) == path)
}

fn path_for(path: &Path, root: &Path) -> PathBuf {
    if path.is_absolute() {
        path.to_path_buf()
    } else {
        root.join(path)
    }
}

fn uri_for(path: &Path, root: &Path) -> Option<Url> {
    Url::from_file_path(path_for(path, root)).ok()
}

fn resolve(
    analysis: &Analysis,
    path: &Path,
    name: &str,
    qualified: &[String],
    reference: &Span,
) -> Option<Symbol> {
    if qualified.len() == 1 {
        if let Some(local) = analysis.locals.iter().find(|local| {
            local.path == path
                && local.name == name
                && local.scope.start <= reference.start
                && reference.end <= local.scope.end
        }) {
            return Some(Symbol {
                name: local.name.clone(),
                module: Vec::new(),
                path: local.path.clone(),
                span: local.span.clone(),
                signature: local.signature.clone(),
                doc: None,
            });
        }
    }
    let source = analysis.sources.iter().find(|source| source.path == path)?;
    let module = if qualified.len() > 1 {
        qualified[..qualified.len() - 1].to_vec()
    } else if let Some(module) = source
        .uses
        .iter()
        .find_map(|use_decl| match &use_decl.names {
            Some(names) if names.iter().any(|import| import == name) => {
                Some(use_decl.path.segments.clone())
            }
            None if use_decl
                .path
                .segments
                .last()
                .is_some_and(|import| import == name) =>
            {
                Some(use_decl.path.segments[..use_decl.path.segments.len() - 1].to_vec())
            }
            _ => None,
        })
    {
        module
    } else {
        source.module.clone()
    };
    analysis
        .symbols
        .iter()
        .find(|symbol| symbol.name == name && symbol.module == module)
        .cloned()
}

fn word_at(text: &str, position: Position) -> Option<(String, Span, Vec<String>)> {
    let offset = offset_for(text, position)?;
    let bytes = text.as_bytes();
    let mut start = offset.min(bytes.len());
    while start > 0 && identifier_byte(bytes[start - 1]) {
        start -= 1;
    }
    let mut end = offset.min(bytes.len());
    while end < bytes.len() && identifier_byte(bytes[end]) {
        end += 1;
    }
    (start != end).then(|| {
        let mut qualified_start = start;
        while qualified_start >= 2
            && bytes[qualified_start - 1] == b'.'
            && identifier_byte(bytes[qualified_start - 2])
        {
            qualified_start -= 1;
            while qualified_start > 0 && identifier_byte(bytes[qualified_start - 1]) {
                qualified_start -= 1;
            }
        }
        let mut qualified_end = end;
        while qualified_end + 1 < bytes.len()
            && bytes[qualified_end] == b'.'
            && identifier_byte(bytes[qualified_end + 1])
        {
            qualified_end += 1;
            while qualified_end < bytes.len() && identifier_byte(bytes[qualified_end]) {
                qualified_end += 1;
            }
        }
        let name = text[start..end].to_owned();
        let qualified = text[qualified_start..qualified_end]
            .split('.')
            .map(str::to_owned)
            .collect();
        (name, Span { start, end }, qualified)
    })
}

fn identifier_byte(byte: u8) -> bool {
    byte.is_ascii_alphanumeric() || byte == b'_'
}

fn offset_for(text: &str, position: Position) -> Option<usize> {
    let mut line_start = 0;
    for _ in 0..position.line {
        line_start += text.get(line_start..)?.find('\n')? + 1;
    }
    let line_end = text[line_start..]
        .find('\n')
        .map(|offset| line_start + offset)
        .unwrap_or(text.len());
    let line = &text[line_start..line_end];
    let mut units = 0;
    for (offset, character) in line.char_indices() {
        if units >= position.character {
            return Some(line_start + offset);
        }
        units += character.len_utf16() as u32;
        if units >= position.character {
            return Some(line_start + offset + character.len_utf8());
        }
    }
    (units == position.character).then_some(line_end)
}

fn range_for(text: &str, span: Span) -> Range {
    Range {
        start: position_for(text, span.start),
        end: position_for(text, span.end),
    }
}

fn position_for(text: &str, offset: usize) -> Position {
    let offset = offset.min(text.len());
    let line_start = text[..offset].rfind('\n').map_or(0, |index| index + 1);
    Position {
        line: text[..line_start]
            .bytes()
            .filter(|byte| *byte == b'\n')
            .count() as u32,
        character: text[line_start..offset]
            .chars()
            .map(|character| character.len_utf16() as u32)
            .sum(),
    }
}

fn lsp_diagnostic(diagnostic: &CompilerDiagnostic, text: &str) -> Diagnostic {
    Diagnostic {
        range: range_for(text, diagnostic.span.clone()),
        severity: Some(match diagnostic.severity {
            crate::diagnostics::Severity::Error => DiagnosticSeverity::ERROR,
            crate::diagnostics::Severity::Warning => DiagnosticSeverity::WARNING,
            crate::diagnostics::Severity::Note => DiagnosticSeverity::INFORMATION,
        }),
        code: Some(NumberOrString::String(diagnostic.code.clone())),
        source: Some("cott".to_owned()),
        message: diagnostic.message.clone(),
        ..Diagnostic::default()
    }
}

fn builtin_hover(name: &str, text: &str, span: Span) -> Option<Hover> {
    BUILTIN_TYPES.contains(&name).then(|| Hover {
        contents: HoverContents::Markup(MarkupContent {
            kind: MarkupKind::Markdown,
            value: match name {
                "Factory" => "```cott\nFactory[Concrete]\n```\n\nBuilt-in type for the exact generated `Concrete` class object; `Concrete` must be an impl declaration.".to_owned(),
                _ => format!("```cott\n{name}\n```\n\nBuilt-in type"),
            },
        }),
        range: Some(range_for(text, span)),
    })
}

fn all_keywords() -> &'static [&'static str] {
    &[
        "module",
        "use",
        "alias",
        "newtype",
        "struct",
        "enum",
        "trait",
        "impl",
        "for",
        "state",
        "fn",
        "const",
        "where",
        "requires",
        "invariant",
        "init",
        "ensures",
        "error",
        "when",
        "modifies",
        "old",
        "effects",
        "doc",
        "self",
        "true",
        "false",
        "and",
        "or",
        "not",
        "rule",
        "override",
        "delete",
        "remove",
        "external",
        "type",
    ]
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn source(path: &str, text: &str) -> SourceFile {
        SourceFile::new(path, text)
    }

    #[test]
    fn converts_utf8_spans_to_utf16_positions() {
        let text = "a😀b\n";
        assert_eq!(position_for(text, 1), Position::new(0, 1));
        assert_eq!(position_for(text, 5), Position::new(0, 3));
        assert_eq!(offset_for(text, Position::new(0, 3)), Some(5));
    }

    #[test]
    fn reports_syntax_and_hir_diagnostics() {
        let syntax = analyze_sources(
            vec![source("bad.cott", "module bad\nfn broken( -> Unit:\n")],
            Some(PathBuf::new()),
            BTreeSet::new(),
        );
        assert!(
            !syntax
                .diagnostics
                .get(Path::new("bad.cott"))
                .unwrap()
                .is_empty()
        );
        let hir = analyze_sources(
            vec![source(
                "invalid.cott",
                "module invalid\n\nfn check(left: I32, right: U32) -> Unit:\n    requires left < right\n",
            )],
            Some(PathBuf::new()),
            BTreeSet::new(),
        );
        assert!(
            !hir.diagnostics
                .get(Path::new("invalid.cott"))
                .unwrap()
                .is_empty()
        );
    }

    #[test]
    fn completes_declarations_and_static_vocabulary() {
        let analysis = analyze_sources(
            vec![source(
                "demo.cott",
                "module demo\n\nexternal type PyWidget\n\nstruct Widget:\n    value: I32\n",
            )],
            Some(PathBuf::new()),
            BTreeSet::new(),
        );
        assert!(
            analysis
                .symbols
                .iter()
                .any(|symbol| symbol.name == "Widget")
        );
        let external = analysis
            .symbols
            .iter()
            .find(|symbol| symbol.name == "PyWidget")
            .unwrap();
        assert_eq!(external.signature, "external type PyWidget");
        assert!(all_keywords().contains(&"effects"));
        assert!(all_keywords().contains(&"external"));
        assert!(all_keywords().contains(&"type"));
        assert!(!all_keywords().contains(&"Factory"));
        assert!(BUILTIN_TYPES.contains(&"Any"));
        assert!(BUILTIN_TYPES.contains(&"Unknown"));
        assert!(BUILTIN_TYPES.contains(&"Iterator"));
        assert!(BUILTIN_TYPES.contains(&"Generator"));
        assert!(BUILTIN_TYPES.contains(&"Result"));
        assert!(BUILTIN_TYPES.contains(&"Factory"));
    }

    #[test]
    fn hovers_documented_declaration() {
        let text =
            "module demo\n\ndoc \"\"\"widget documentation\"\"\"\nstruct Widget:\n    value: I32\n";
        let analysis = analyze_sources(
            vec![source("demo.cott", text)],
            Some(PathBuf::new()),
            BTreeSet::new(),
        );
        let symbol = analysis
            .symbols
            .iter()
            .find(|symbol| symbol.name == "Widget")
            .unwrap();
        assert_eq!(symbol.signature, "struct Widget:");
        assert_eq!(symbol.doc.as_deref(), Some("widget documentation"));
    }

    #[test]
    fn resolves_same_file_and_imported_definitions() {
        let first = "module first\n\nstruct Thing:\n    value: I32\n\nfn local(value: I32) -> Unit:\n    requires value == value\n";
        let second = "module second\n\nuse first.{Thing}\n\nalias Other = Thing\n";
        let analysis = analyze_sources(
            vec![source("first.cott", first), source("second.cott", second)],
            Some(PathBuf::new()),
            BTreeSet::new(),
        );
        let local_start = first.rfind("value ==").unwrap();
        let local = resolve(
            &analysis,
            Path::new("first.cott"),
            "value",
            &["value".to_owned()],
            &Span {
                start: local_start,
                end: local_start + 5,
            },
        )
        .unwrap();
        assert_eq!(local.path, PathBuf::from("first.cott"));
        let imported_start = second.rfind("Thing").unwrap();
        let imported = resolve(
            &analysis,
            Path::new("second.cott"),
            "Thing",
            &["Thing".to_owned()],
            &Span {
                start: imported_start,
                end: imported_start + 5,
            },
        )
        .unwrap();
        assert_eq!(imported.path, PathBuf::from("first.cott"));
    }

    #[test]
    fn resolves_ungrouped_import_for_hover_and_definition() {
        let root = PathBuf::from("/tmp/cott-lsp-ungrouped-import");
        let first_path = root.join("first.cott");
        let second_path = root.join("second.cott");
        let first = "module first\n\nstruct Thing:\n    value: I32\n";
        let second = "module second\n\nuse first.Thing\n\nalias Other = Thing\n";
        let analysis = analyze_sources(
            vec![
                source(first_path.to_str().unwrap(), first),
                source(second_path.to_str().unwrap(), second),
            ],
            Some(root),
            BTreeSet::new(),
        );
        let start = second.rfind("Thing").unwrap();
        let imported = resolve(
            &analysis,
            &second_path,
            "Thing",
            &["Thing".to_owned()],
            &Span {
                start,
                end: start + "Thing".len(),
            },
        )
        .unwrap();

        assert_eq!(imported.signature, "struct Thing:");
        assert_eq!(
            uri_for(&imported.path, &analysis.root),
            Url::from_file_path(&first_path).ok()
        );
        assert_eq!(
            range_for(first, imported.span),
            Range::new(Position::new(2, 7), Position::new(2, 12))
        );
    }

    #[test]
    fn closing_buffer_restores_disk_source_for_open_document_analysis() {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let root =
            std::env::temp_dir().join(format!("cott-lsp-close-{}-{nonce}", std::process::id()));
        let source_dir = root.join("src");
        fs::create_dir_all(&source_dir).unwrap();
        fs::create_dir_all(root.join("python")).unwrap();
        fs::write(
            root.join("cott.toml"),
            "[project]\nname = \"close\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.python]\nsource = \"python\"\ngenerated = \"generated/python\"\nstubs = \"generated/stubs\"\ninterpreter = \"python\"\ntype_checker = \"pyright\"\nruntime_validation = \"boundary\"\n",
        )
        .unwrap();
        fs::write(
            root.join("python/pyproject.toml"),
            "[project]\nname = \"close\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14.6,<3.15\"\ndependencies = []\n",
        )
        .unwrap();
        let first_path = source_dir.join("first.cott");
        let second_path = source_dir.join("second.cott");
        fs::write(
            &first_path,
            "module first\n\nstruct Thing:\n    value: I32\n",
        )
        .unwrap();

        let first_uri = Url::from_file_path(&first_path).unwrap();
        let second_uri = Url::from_file_path(&second_path).unwrap();
        let mut state = State::default();
        state.documents.insert(
            first_uri.clone(),
            "module first\n\nstruct Other:\n    value: I32\n".to_owned(),
        );
        state.documents.insert(
            second_uri.clone(),
            "module second\n\nuse first.Thing\n\nalias Alias = Thing\n".to_owned(),
        );
        state.published.insert(first_uri.clone());
        state.published.insert(second_uri.clone());

        let overridden = analyze_documents(&state.snapshot());
        assert!(
            overridden
                .diagnostics
                .get(Path::new("second.cott"))
                .is_some_and(|diagnostics| !diagnostics.is_empty())
        );

        state.close(&first_uri);
        assert!(!state.documents.contains_key(&first_uri));
        assert!(!state.published.contains(&first_uri));
        let restored = analyze_documents(&state.snapshot());
        assert_eq!(
            restored
                .sources
                .iter()
                .find(|source| source.path == Path::new("first.cott"))
                .map(|source| source.module.as_slice()),
            Some(["first".to_owned()].as_slice())
        );
        assert_eq!(
            path_for(
                analysis_path(&restored, &second_uri.to_file_path().unwrap()).unwrap(),
                &restored.root,
            ),
            second_path
        );
        assert_eq!(
            active_documents(&state.snapshot()),
            HashSet::from([second_uri.clone()])
        );
        assert!(
            restored
                .diagnostics
                .get(Path::new("second.cott"))
                .is_none_or(Vec::is_empty)
        );
        fs::remove_dir_all(root).unwrap();
    }
}
