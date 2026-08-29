use crate::ast::*;
use crate::diagnostics::{Diagnostic, Span};
use crate::syntax::{Cst, Keyword, Token, TokenKind};

pub fn parse(source: &str) -> Result<File, Vec<Diagnostic>> {
    parse_cst(&Cst::parse(source)?)
}

pub fn parse_cst(cst: &Cst) -> Result<File, Vec<Diagnostic>> {
    Parser::new(cst.tokens.clone()).file()
}

struct Parser {
    tokens: Vec<Token>,
    pos: usize,
    errors: Vec<Diagnostic>,
    allow_old: bool,
}

impl Parser {
    fn new(tokens: Vec<Token>) -> Self {
        Self {
            tokens,
            pos: 0,
            errors: Vec::new(),
            allow_old: false,
        }
    }
    fn current(&self) -> &Token {
        self.tokens
            .get(self.pos)
            .unwrap_or_else(|| self.tokens.last().unwrap())
    }
    fn at(&self, kind: &TokenKind) -> bool {
        &self.current().kind == kind
    }
    fn eof(&self) -> bool {
        matches!(self.current().kind.clone(), TokenKind::Eof)
    }
    fn bump(&mut self) -> Token {
        let t = self.current().clone();
        if !self.eof() {
            self.pos += 1;
        }
        t
    }
    fn span_here(&self) -> Span {
        self.current().span.clone()
    }
    fn error(&mut self, message: impl Into<String>, span: Span) {
        self.errors.push(Diagnostic::new(message, span));
    }
    fn expect(&mut self, kind: TokenKind, message: &str) -> Option<Token> {
        if self.at(&kind) {
            Some(self.bump())
        } else {
            let s = self.span_here();
            self.error(message, s);
            None
        }
    }
    fn keyword(&mut self, kw: Keyword) -> Option<Token> {
        if self.at(&TokenKind::Keyword(kw)) {
            Some(self.bump())
        } else {
            let s = self.span_here();
            self.error(format!("expected keyword {:?}", kw), s);
            None
        }
    }
    fn name(&mut self, what: &str) -> Option<(String, Span)> {
        match self.current().kind.clone() {
            TokenKind::Name(s) => {
                let t = self.bump();
                Some((s, t.span))
            }
            _ => {
                let s = self.span_here();
                self.error(format!("expected {what}"), s);
                None
            }
        }
    }
    fn string(&mut self, what: &str) -> Option<(String, Span)> {
        match self.current().kind.clone() {
            TokenKind::String(value) => {
                let token = self.bump();
                Some((value, token.span))
            }
            _ => {
                self.error(format!("expected {what}"), self.span_here());
                None
            }
        }
    }
    fn integer(&mut self, what: &str) -> Option<ScenarioInteger> {
        match self.current().kind.clone() {
            TokenKind::Integer(value) => {
                let token = self.bump();
                Some(ScenarioInteger {
                    span: token.span,
                    value,
                })
            }
            _ => {
                self.error(format!("expected {what}"), self.span_here());
                None
            }
        }
    }
    fn newline(&mut self) -> bool {
        if self.at(&TokenKind::Newline) {
            self.bump();
            true
        } else {
            self.error("expected end of line", self.span_here());
            false
        }
    }
    fn skip_newlines(&mut self) {
        while self.at(&TokenKind::Newline) {
            self.bump();
        }
    }
    fn recover_line(&mut self) {
        while !self.eof() && !self.at(&TokenKind::Newline) && !self.at(&TokenKind::Dedent) {
            self.bump();
        }
        if self.at(&TokenKind::Newline) {
            self.bump();
        } else if !self.eof() {
            // A recovery boundary is itself input; consume it so callers cannot
            // retry the same token forever.
            self.bump();
        }
    }
    fn join(a: Span, b: Span) -> Span {
        Span {
            start: a.start,
            end: b.end,
        }
    }
    fn file(mut self) -> Result<File, Vec<Diagnostic>> {
        self.skip_newlines();
        let module = match self.parse_module() {
            Some(v) => v,
            None => {
                self.recover_line();
                ModuleDecl {
                    span: self.span_here(),
                    path: QualifiedName::single(self.span_here(), ""),
                }
            }
        };
        let mut uses = Vec::new();
        self.skip_newlines();
        while self.at(&TokenKind::Keyword(Keyword::Use)) {
            if let Some(u) = self.parse_use() {
                uses.push(u);
            } else {
                self.recover_line();
            }
            self.skip_newlines();
        }
        let mut declarations = Vec::new();
        let mut docs = None;
        let mut annotations = Vec::new();
        while !self.eof() {
            if self.at(&TokenKind::Newline) {
                self.bump();
                continue;
            }
            if self.at(&TokenKind::At) {
                if let Some(ann) = self.parse_annotation() {
                    annotations.push(ann);
                } else {
                    self.recover_line();
                }
                continue;
            }
            if self.at(&TokenKind::Keyword(Keyword::Doc)) {
                let d = self.parse_doc();
                if docs.is_some() {
                    self.error(
                        "duplicate top-level documentation",
                        d.as_ref()
                            .map(|x| x.span.clone())
                            .unwrap_or_else(|| self.span_here()),
                    );
                }
                docs = d;
                continue;
            }
            if let Some(decl) =
                self.parse_declaration(std::mem::take(&mut annotations), docs.take())
            {
                declarations.push(decl);
            } else {
                self.recover_line();
            }
        }
        let end = self
            .tokens
            .last()
            .map(|t| t.span.end)
            .unwrap_or(module.span.end);
        if docs.is_some() {
            self.error("orphan top-level documentation", self.span_here());
        }
        if self.errors.is_empty() {
            Ok(File {
                span: Span {
                    start: module.span.start,
                    end,
                },
                module,
                uses,
                declarations,
            })
        } else {
            Err(self.errors)
        }
    }
    fn parse_module(&mut self) -> Option<ModuleDecl> {
        let start = self.keyword(Keyword::Module)?.span;
        let path = self.parse_qname()?;
        self.newline();
        Some(ModuleDecl {
            span: Self::join(start, path.span.clone()),
            path,
        })
    }
    fn parse_use(&mut self) -> Option<UseDecl> {
        let start = self.keyword(Keyword::Use)?.span;
        let path = self.parse_qname()?;
        let mut names = None;
        if self.at(&TokenKind::Dot) {
            self.bump();
            self.expect(TokenKind::LBrace, "expected `{` after use prefix")?;
            let mut ns = Vec::new();
            if !self.at(&TokenKind::RBrace) {
                loop {
                    let (n, _) = self.name("import name")?;
                    ns.push(n);
                    if self.at(&TokenKind::Comma) {
                        self.bump();
                        if self.at(&TokenKind::RBrace) {
                            break;
                        }
                    } else {
                        break;
                    }
                }
            }
            self.expect(TokenKind::RBrace, "expected `}` in grouped import")?;
            names = Some(ns);
        }
        self.newline();
        Some(UseDecl {
            span: Self::join(start, path.span.clone()),
            path,
            names,
        })
    }
    fn parse_annotation(&mut self) -> Option<Annotation> {
        let st = self.expect(TokenKind::At, "expected `@`")?.span;
        let (name, name_span) = match self.current().kind.clone() {
            TokenKind::Name(s) => {
                let t = self.bump();
                (s, t.span)
            }
            TokenKind::Keyword(kw) => {
                let t = self.bump();
                let s = match kw {
                    Keyword::External => "external",
                    Keyword::Type => "type",
                    Keyword::Module => "module",
                    Keyword::Use => "use",
                    Keyword::Alias => "alias",
                    Keyword::Newtype => "newtype",
                    Keyword::Struct => "struct",
                    Keyword::Enum => "enum",
                    Keyword::Trait => "trait",
                    Keyword::Impl => "impl",
                    Keyword::Specialize => "specialize",
                    Keyword::For => "for",
                    Keyword::State => "state",
                    Keyword::Resource => "resource",
                    Keyword::Initial => "initial",
                    Keyword::Terminal => "terminal",
                    Keyword::Transition => "transition",
                    Keyword::Transitions => "transitions",
                    Keyword::Rule => "rule",
                    Keyword::Const => "const",
                    Keyword::Fn => "fn",
                    Keyword::Async => "async",
                    Keyword::SelfValue => "self",
                    Keyword::Doc => "doc",
                    Keyword::Requires => "requires",
                    Keyword::Invariant => "invariant",
                    Keyword::Init => "init",
                    Keyword::Ensures => "ensures",
                    Keyword::Matches => "matches",
                    Keyword::With => "with",
                    Keyword::When => "when",
                    Keyword::Effects => "effects",
                    Keyword::Modifies => "modifies",
                    Keyword::Old => "old",
                    Keyword::Error => "error",
                    Keyword::Where => "where",
                    Keyword::Override => "override",
                    Keyword::Delete => "delete",
                    Keyword::Remove => "remove",
                    Keyword::Scenario => "scenario",
                    Keyword::Call => "call",
                    Keyword::Spawn => "spawn",
                    Keyword::Await => "await",
                    Keyword::Cancel => "cancel",
                    Keyword::Tick => "tick",
                    Keyword::Assert => "assert",
                    Keyword::As => "as",
                    Keyword::Cancelled => "cancelled",
                    Keyword::True => "true",
                    Keyword::False => "false",
                    Keyword::And => "and",
                    Keyword::Or => "or",
                    Keyword::Not => "not",
                };
                (s.to_owned(), t.span)
            }
            _ => {
                self.error("expected annotation name", self.span_here());
                return None;
            }
        };
        let (argument, end_span) = if self.at(&TokenKind::LParen) {
            self.bump();
            let arg = match self.current().kind.clone() {
                TokenKind::String(s) => {
                    self.bump();
                    Some(s)
                }
                TokenKind::Name(s) => {
                    self.bump();
                    Some(s)
                }
                _ => None,
            };
            let r = self.expect(TokenKind::RParen, "expected `)` after annotation argument")?;
            (arg, r.span)
        } else {
            (None, name_span)
        };
        self.newline();
        Some(Annotation {
            span: Self::join(st, end_span),
            name,
            argument,
        })
    }
    fn parse_declaration(
        &mut self,
        annotations: Vec<Annotation>,
        doc: Option<DocBlock>,
    ) -> Option<Declaration> {
        match self.current().kind.clone() {
            TokenKind::Keyword(Keyword::External) => Some(Declaration::ExternalType(
                self.parse_external_type(annotations, doc)?,
            )),
            TokenKind::Name(value) if value == "external" => Some(Declaration::ExternalType(
                self.parse_external_type(annotations, doc)?,
            )),
            TokenKind::Keyword(Keyword::Alias) => {
                Some(Declaration::Alias(self.parse_alias(annotations, doc)?))
            }
            TokenKind::Keyword(Keyword::Newtype) => {
                Some(Declaration::Newtype(self.parse_newtype(annotations, doc)?))
            }
            TokenKind::Keyword(Keyword::Struct) => {
                Some(Declaration::Struct(self.parse_struct(annotations, doc)?))
            }
            TokenKind::Keyword(Keyword::Enum) => {
                Some(Declaration::Enum(self.parse_enum(annotations, doc)?))
            }
            TokenKind::Keyword(Keyword::Trait) => {
                Some(Declaration::Trait(self.parse_trait(annotations, doc)?))
            }
            TokenKind::Keyword(Keyword::Resource) => Some(Declaration::Resource(
                self.parse_resource(annotations, doc)?,
            )),
            TokenKind::Keyword(Keyword::Const) => {
                Some(Declaration::Const(self.parse_const(annotations, doc)?))
            }
            TokenKind::Keyword(Keyword::Rule) => {
                Some(Declaration::Rule(self.parse_rule(annotations, doc)?))
            }
            TokenKind::Keyword(Keyword::Scenario) => Some(Declaration::Scenario(
                self.parse_scenario(annotations, doc)?,
            )),
            TokenKind::Keyword(Keyword::Async) => {
                if doc.is_some() {
                    self.error(
                        "top-level documentation must precede a type or constant declaration",
                        doc.unwrap().span,
                    );
                }
                let start = self.keyword(Keyword::Async)?.span;
                Some(Declaration::Function(self.parse_function(
                    annotations,
                    CallableKind::Async,
                    start,
                )?))
            }
            TokenKind::Keyword(Keyword::Fn) => {
                if doc.is_some() {
                    self.error(
                        "top-level documentation must precede a type or constant declaration",
                        doc.unwrap().span,
                    );
                }
                let start = self.span_here();
                Some(Declaration::Function(self.parse_function(
                    annotations,
                    CallableKind::Sync,
                    start,
                )?))
            }
            TokenKind::Keyword(Keyword::Impl) => {
                if let Some(doc) = doc {
                    self.error(
                        "top-level documentation must precede a type or constant declaration",
                        doc.span,
                    );
                }
                Some(Declaration::Impl(self.parse_impl(annotations)?))
            }
            TokenKind::Keyword(Keyword::Specialize) => {
                if let Some(doc) = doc {
                    self.error(
                        "top-level documentation must precede a type or constant declaration",
                        doc.span,
                    );
                }
                Some(Declaration::Specialize(self.parse_specialize(annotations)?))
            }
            _ => {
                self.error("expected declaration", self.span_here());
                None
            }
        }
    }
    fn parse_external_type(
        &mut self,
        annotations: Vec<Annotation>,
        doc: Option<DocBlock>,
    ) -> Option<ExternalTypeDecl> {
        let st = match self.current().kind.clone() {
            TokenKind::Keyword(Keyword::External) => self.bump().span,
            TokenKind::Name(value) if value == "external" => self.bump().span,
            _ => {
                self.error("expected `external`", self.span_here());
                return None;
            }
        };
        self.expect(
            TokenKind::Keyword(Keyword::Type),
            "expected `type` after `external`",
        )?;
        let (name, end) = self.name("type name")?;
        self.newline();
        Some(ExternalTypeDecl {
            span: Self::join(st, end),
            annotations,
            doc,
            name,
        })
    }

    fn parse_alias(
        &mut self,
        annotations: Vec<Annotation>,
        doc: Option<DocBlock>,
    ) -> Option<AliasDecl> {
        let st = self.keyword(Keyword::Alias)?.span;
        let (name, _) = self.name("type name")?;
        self.expect(TokenKind::Equal, "expected `=` in alias")?;
        let target = self.parse_type()?;
        let end = target.span.clone();
        self.newline();
        Some(AliasDecl {
            span: Self::join(st, end),
            annotations,
            doc,
            name,
            target,
        })
    }
    fn parse_newtype(
        &mut self,
        annotations: Vec<Annotation>,
        doc: Option<DocBlock>,
    ) -> Option<NewtypeDecl> {
        let st = self.keyword(Keyword::Newtype)?.span;
        let (name, _) = self.name("type name")?;
        self.expect(TokenKind::LParen, "expected `(` in newtype")?;
        let underlying = self.parse_type()?;
        self.expect(TokenKind::RParen, "expected `)` in newtype")?;
        let end = underlying.span.clone();
        self.newline();
        let mut where_clause = None;
        if self.at(&TokenKind::Indent) {
            self.bump();
            self.keyword(Keyword::Where);
            where_clause = self.parse_expr();
            self.newline();
            self.expect(TokenKind::Dedent, "expected end of where block");
        }
        Some(NewtypeDecl {
            span: Self::join(st, end),
            annotations,
            doc,
            name,
            underlying,
            where_clause,
        })
    }
    fn parse_struct(
        &mut self,
        annotations: Vec<Annotation>,
        doc: Option<DocBlock>,
    ) -> Option<StructDecl> {
        let st = self.keyword(Keyword::Struct)?.span;
        let (name, _) = self.name("type name")?;
        let generics = self.parse_generics(true)?;
        self.expect(TokenKind::Colon, "expected `:` after struct")?;
        self.newline();
        self.expect(TokenKind::Indent, "expected indented struct fields")?;
        let mut fields = Vec::new();
        let mut invariants = Vec::new();
        let mut seen_invariant = false;
        self.skip_newlines();
        while !self.at(&TokenKind::Dedent) && !self.eof() {
            if self.at(&TokenKind::Keyword(Keyword::Invariant)) {
                seen_invariant = true;
                if let Some(invariant) = self.parse_struct_invariant() {
                    invariants.push(invariant);
                } else {
                    self.recover_line();
                }
            } else if seen_invariant {
                self.error("struct fields must precede invariants", self.span_here());
                self.recover_line();
            } else if let Some(field) = self.parse_field() {
                fields.push(field);
            } else {
                self.recover_line();
            }
            self.skip_newlines();
        }
        let end = self.bump().span;
        Some(StructDecl {
            span: Self::join(st, end),
            annotations,
            doc,
            name,
            generics,
            fields,
            invariants,
        })
    }
    fn parse_struct_invariant(&mut self) -> Option<StructInvariant> {
        let st = self.keyword(Keyword::Invariant)?.span;
        let (guard, condition) = self.parse_guarded_condition(false)?;
        let end = condition.span.clone();
        self.newline();
        Some(StructInvariant {
            span: Self::join(st, end),
            guard,
            condition,
        })
    }

    fn parse_scenario(
        &mut self,
        annotations: Vec<Annotation>,
        doc: Option<DocBlock>,
    ) -> Option<Scenario> {
        let st = self.keyword(Keyword::Scenario)?.span;
        let (name, _) = self.name("scenario name")?;
        let target = if self.at(&TokenKind::Keyword(Keyword::For)) {
            self.bump();
            Some(self.parse_qname()?)
        } else {
            None
        };
        self.expect(TokenKind::Colon, "expected `:` after scenario")?;
        self.newline();
        self.expect(TokenKind::Indent, "expected indented scenario body")?;
        self.skip_newlines();
        let fixtures = if matches!(&self.current().kind, TokenKind::Name(value) if value == "fixtures")
        {
            self.parse_scenario_fixtures()?
        } else {
            Vec::new()
        };
        self.skip_newlines();
        let mut steps = Vec::new();
        while !self.at(&TokenKind::Dedent) && !self.eof() {
            if let Some(step) = self.parse_scenario_step() {
                steps.push(step);
            } else {
                self.recover_line();
            }
            self.skip_newlines();
        }
        if steps.is_empty() {
            self.error("scenario requires at least one step", self.span_here());
        }
        let end = self
            .expect(TokenKind::Dedent, "expected end of scenario body")?
            .span;
        Some(Scenario {
            span: Self::join(st, end),
            annotations,
            doc,
            name,
            target,
            fixtures,
            steps,
        })
    }

    fn parse_scenario_fixtures(&mut self) -> Option<Vec<ScenarioFixture>> {
        self.name("`fixtures`")?;
        self.expect(TokenKind::Colon, "expected `:` after fixtures")?;
        self.newline();
        self.expect(TokenKind::Indent, "expected indented fixtures")?;
        self.skip_newlines();
        let mut fixtures = Vec::new();
        while !self.at(&TokenKind::Dedent) && !self.eof() {
            if let Some(fixture) = self.parse_scenario_fixture() {
                fixtures.push(fixture);
            } else {
                self.recover_line();
            }
            self.skip_newlines();
        }
        self.expect(TokenKind::Dedent, "expected end of fixtures")?;
        Some(fixtures)
    }

    fn parse_scenario_fixture(&mut self) -> Option<ScenarioFixture> {
        let (kind, start) = self.name("fixture kind")?;
        let (name, _) = self.name("fixture name")?;
        self.expect(TokenKind::Colon, "expected `:` after fixture name")?;
        self.newline();
        self.expect(TokenKind::Indent, "expected indented fixture configuration")?;
        self.skip_newlines();
        let config = match kind.as_str() {
            "fs" => self.parse_scenario_filesystem(start.clone())?,
            "http" => self.parse_scenario_http(start.clone())?,
            "clock" => self.parse_scenario_clock(start.clone())?,
            "failure" => self.parse_scenario_failure(start.clone())?,
            _ => {
                self.error("unknown scenario fixture kind", start);
                self.recover_line();
                return None;
            }
        };
        let end = self
            .expect(TokenKind::Dedent, "expected end of fixture configuration")?
            .span;
        Some(ScenarioFixture {
            span: Self::join(start, end),
            name,
            config,
        })
    }

    fn parse_scenario_filesystem(&mut self, span: Span) -> Option<ScenarioFixtureConfig> {
        let mut files = Vec::new();
        while !self.at(&TokenKind::Dedent) && !self.eof() {
            let st = self.span_here();
            let (keyword, _) = self.name("`file`")?;
            if keyword != "file" {
                self.error("expected `file` in filesystem fixture", st);
                return None;
            }
            let (path, path_span) = self.string("filesystem path")?;
            if !normalized_relative_path(&path) {
                self.error(
                    "fixture path must be normalized relative UTF-8 without symlinks",
                    path_span,
                );
            }
            let contents = self.parse_scenario_data()?;
            let end = contents.span.clone();
            self.newline();
            files.push(ScenarioFile {
                span: Self::join(st, end),
                path,
                contents,
            });
            self.skip_newlines();
        }
        Some(ScenarioFixtureConfig::Filesystem { span, files })
    }

    fn parse_scenario_http(&mut self, span: Span) -> Option<ScenarioFixtureConfig> {
        let mut routes = Vec::new();
        while !self.at(&TokenKind::Dedent) && !self.eof() {
            let st = self.span_here();
            let (keyword, _) = self.name("`route`")?;
            if keyword != "route" {
                self.error("expected `route` in http fixture", st);
                return None;
            }
            let (path, path_span) = self.string("route path")?;
            if !normalized_route_path(&path) {
                self.error("http route must be a normalized relative path", path_span);
            }
            self.expect(TokenKind::Arrow, "expected `->` after route path")?;
            let outcome = self.parse_scenario_http_outcome()?;
            let end = outcome_span(&outcome);
            self.newline();
            routes.push(ScenarioHttpRoute {
                span: Self::join(st, end),
                path,
                outcome,
            });
            self.skip_newlines();
        }
        Some(ScenarioFixtureConfig::Http { span, routes })
    }

    fn parse_scenario_clock(&mut self, span: Span) -> Option<ScenarioFixtureConfig> {
        let start_ms = self.parse_scenario_integer_field("start_ms")?;
        let tick_ms = self.parse_scenario_integer_field("tick_ms")?;
        Some(ScenarioFixtureConfig::Clock {
            span,
            start_ms,
            tick_ms,
        })
    }

    fn parse_scenario_failure(&mut self, span: Span) -> Option<ScenarioFixtureConfig> {
        let (point_name, point_span) = self.parse_scenario_qname_field("point")?;
        let point_kind = match point_name.segments.as_slice() {
            [file, operation] if file == "file" => match operation.as_str() {
                "open" => ScenarioFailurePointKind::FileOpen,
                "read" => ScenarioFailurePointKind::FileRead,
                "write" => ScenarioFailurePointKind::FileWrite,
                "flush" => ScenarioFailurePointKind::FileFlush,
                "replace" => ScenarioFailurePointKind::FileReplace,
                _ => {
                    self.error("unknown failure point", point_span);
                    return None;
                }
            },
            [http, operation] if http == "http" => match operation.as_str() {
                "connect" => ScenarioFailurePointKind::HttpConnect,
                "read" => ScenarioFailurePointKind::HttpRead,
                _ => {
                    self.error("unknown failure point", point_span);
                    return None;
                }
            },
            [clock, operation] if clock == "clock" && operation == "read" => {
                ScenarioFailurePointKind::ClockRead
            }
            _ => {
                self.error("unknown failure point", point_span);
                return None;
            }
        };
        let point = ScenarioFailurePoint {
            span: point_span,
            kind: point_kind,
        };
        let occurrence = self.parse_scenario_integer_field("occurrence")?;
        let (error_name, error_span) = self.parse_scenario_name_field("error")?;
        let error_kind = match error_name.as_str() {
            "permission_denied" => ScenarioFailureErrorKind::PermissionDenied,
            "not_found" => ScenarioFailureErrorKind::NotFound,
            "disk_full" => ScenarioFailureErrorKind::DiskFull,
            "timeout" => ScenarioFailureErrorKind::Timeout,
            "connection_reset" => ScenarioFailureErrorKind::ConnectionReset,
            _ => {
                self.error("unknown failure error", error_span);
                return None;
            }
        };
        let error = ScenarioFailureError {
            span: error_span,
            kind: error_kind,
        };
        Some(ScenarioFixtureConfig::Failure {
            span,
            point,
            occurrence,
            error,
        })
    }

    fn parse_scenario_http_outcome(&mut self) -> Option<ScenarioHttpOutcome> {
        let (kind, st) = self.name("http outcome")?;
        self.expect(TokenKind::LParen, "expected `(` after http outcome")?;
        let outcome = match kind.as_str() {
            "response" => {
                let status = self.parse_scenario_integer_argument("status")?;
                self.expect(TokenKind::Comma, "expected `,` after response status")?;
                let body = self.parse_scenario_data_argument("body")?;
                self.expect(TokenKind::Comma, "expected `,` after response body")?;
                let encoding = self.parse_scenario_string_argument("encoding")?;
                let end = self
                    .expect(TokenKind::RParen, "expected `)` after response")?
                    .span;
                ScenarioHttpOutcome::Response {
                    span: Self::join(st, end),
                    status,
                    body,
                    encoding,
                }
            }
            "redirect" => {
                let status = self.parse_scenario_integer_argument("status")?;
                self.expect(TokenKind::Comma, "expected `,` after redirect status")?;
                let (location, location_span) =
                    self.parse_scenario_string_argument_span("location")?;
                if !normalized_route_path(&location) {
                    self.error(
                        "redirect location must be relative to compiler-owned endpoint",
                        location_span,
                    );
                }
                let end = self
                    .expect(TokenKind::RParen, "expected `)` after redirect")?
                    .span;
                ScenarioHttpOutcome::Redirect {
                    span: Self::join(st, end),
                    status,
                    location,
                }
            }
            "delay" => {
                let milliseconds = self.parse_scenario_integer_argument("ms")?;
                let end = self
                    .expect(TokenKind::RParen, "expected `)` after delay")?
                    .span;
                ScenarioHttpOutcome::Delay {
                    span: Self::join(st, end),
                    milliseconds,
                }
            }
            "disconnect" => {
                let end = self
                    .expect(TokenKind::RParen, "expected `)` after disconnect")?
                    .span;
                ScenarioHttpOutcome::Disconnect {
                    span: Self::join(st, end),
                }
            }
            _ => {
                self.error("unknown http route outcome", st);
                return None;
            }
        };
        Some(outcome)
    }

    fn parse_scenario_step(&mut self) -> Option<ScenarioStep> {
        match self.current().kind.clone() {
            TokenKind::Keyword(Keyword::Call) => {
                let st = self.bump().span;
                let (name, span) = self.name("call result binding")?;
                self.expect(TokenKind::Equal, "expected `=` after call result binding")?;
                let (target, arguments, end) = self.parse_scenario_invocation()?;
                self.newline();
                Some(ScenarioStep::Call {
                    span: Self::join(st, end),
                    binding: ScenarioBinding { span, name },
                    target,
                    arguments,
                })
            }
            TokenKind::Keyword(Keyword::Spawn) => {
                let st = self.bump().span;
                let (name, span) = self.name("worker binding")?;
                self.expect(TokenKind::Equal, "expected `=` after worker binding")?;
                let (target, arguments, end) = self.parse_scenario_invocation()?;
                self.newline();
                Some(ScenarioStep::Spawn {
                    span: Self::join(st, end),
                    worker: ScenarioWorker { span, name },
                    target,
                    arguments,
                })
            }
            TokenKind::Keyword(Keyword::Await) => {
                let st = self.bump().span;
                let (name, span) = self.name("worker name")?;
                let worker = ScenarioWorkerRef { span, name };
                let outcome = if self.at(&TokenKind::Keyword(Keyword::As)) {
                    self.bump();
                    let (name, span) = self.name("await result binding")?;
                    ScenarioAwaitOutcome::Value(ScenarioBinding { span, name })
                } else if self.at(&TokenKind::Keyword(Keyword::Cancelled)) {
                    ScenarioAwaitOutcome::Cancelled {
                        span: self.bump().span,
                    }
                } else {
                    self.error(
                        "expected `as` or `cancelled` after worker",
                        self.span_here(),
                    );
                    return None;
                };
                let end = match &outcome {
                    ScenarioAwaitOutcome::Value(binding) => binding.span.clone(),
                    ScenarioAwaitOutcome::Cancelled { span } => span.clone(),
                };
                self.newline();
                Some(ScenarioStep::Await {
                    span: Self::join(st, end),
                    worker,
                    outcome,
                })
            }
            TokenKind::Keyword(Keyword::Cancel) => {
                let st = self.bump().span;
                let (name, span) = self.name("worker name")?;
                self.newline();
                Some(ScenarioStep::Cancel {
                    span: Self::join(st, span.clone()),
                    worker: ScenarioWorkerRef { span, name },
                })
            }
            TokenKind::Keyword(Keyword::Tick) => {
                let span = self.bump().span;
                self.newline();
                Some(ScenarioStep::Tick { span })
            }
            TokenKind::Keyword(Keyword::Assert) => {
                let st = self.bump().span;
                let expression = self.parse_expr()?;
                let end = expression.span.clone();
                self.newline();
                Some(ScenarioStep::Assert {
                    span: Self::join(st, end),
                    expression,
                })
            }
            _ => {
                self.error("expected scenario step", self.span_here());
                None
            }
        }
    }

    fn parse_scenario_invocation(&mut self) -> Option<(QualifiedName, Vec<Expr>, Span)> {
        let target = self.parse_qname()?;
        self.expect(
            TokenKind::LParen,
            "expected `(` after scenario facade target",
        )?;
        let mut arguments = Vec::new();
        if !self.at(&TokenKind::RParen) {
            loop {
                arguments.push(self.parse_scenario_value()?);
                if self.at(&TokenKind::Comma) {
                    self.bump();
                } else {
                    break;
                }
            }
        }
        let end = self
            .expect(
                TokenKind::RParen,
                "expected `)` after scenario call arguments",
            )?
            .span;
        Some((target, arguments, end))
    }

    fn parse_scenario_value(&mut self) -> Option<Expr> {
        let save = self.pos;
        if let TokenKind::Name(fixture) = self.current().kind.clone() {
            let fixture_span = self.bump().span;
            if self.at(&TokenKind::Dot) {
                self.bump();
                if let Some((accessor, _)) = self.name("fixture accessor") {
                    if (accessor == "path" || accessor == "url") && self.at(&TokenKind::LParen) {
                        self.bump();
                        let (path, path_span) = self.string("fixture path")?;
                        let end = self
                            .expect(TokenKind::RParen, "expected `)` after fixture reference")?
                            .span;
                        let span = Self::join(fixture_span, end);
                        if accessor == "path" {
                            if !normalized_relative_path(&path) {
                                self.error(
                                    "fixture path must be normalized relative UTF-8 without symlinks",
                                    path_span,
                                );
                            }
                            return Some(Expr {
                                span,
                                kind: ExprKind::FixturePath { fixture, path },
                            });
                        }
                        if !normalized_route_path(&path) {
                            self.error(
                                "fixture url must be relative to compiler-owned endpoint",
                                path_span,
                            );
                        }
                        return Some(Expr {
                            span,
                            kind: ExprKind::FixtureUrl { fixture, path },
                        });
                    }
                }
            }
        }
        self.pos = save;
        self.parse_expr()
    }

    fn parse_scenario_data(&mut self) -> Option<ScenarioData> {
        let (kind, st) = self.name("fixture data literal")?;
        self.expect(TokenKind::LParen, "expected `(` after fixture data kind")?;
        let (value, _) = self.string("fixture data")?;
        let end = self
            .expect(TokenKind::RParen, "expected `)` after fixture data")?
            .span;
        let kind = match kind.as_str() {
            "text" => ScenarioDataKind::Text(value),
            "bytes" => ScenarioDataKind::Bytes(value),
            "hex" => ScenarioDataKind::Hex(value),
            _ => {
                self.error(
                    "fixture data must be text(...), bytes(...), or hex(...)",
                    st,
                );
                return None;
            }
        };
        if let ScenarioDataKind::Hex(value) = &kind {
            if value.len() % 2 != 0 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
                self.error(
                    "fixture hex data must contain an even number of hex digits",
                    st.clone(),
                );
            }
        }
        Some(ScenarioData {
            span: Self::join(st, end),
            kind,
        })
    }

    fn parse_scenario_integer_field(&mut self, expected: &str) -> Option<ScenarioInteger> {
        self.parse_scenario_field_name(expected)?;
        let integer = self.integer("fixture integer")?;
        self.newline();
        Some(integer)
    }

    fn parse_scenario_qname_field(&mut self, expected: &str) -> Option<(QualifiedName, Span)> {
        self.parse_scenario_field_name(expected)?;
        let value = self.parse_qname()?;
        let span = value.span.clone();
        self.newline();
        Some((value, span))
    }

    fn parse_scenario_name_field(&mut self, expected: &str) -> Option<(String, Span)> {
        self.parse_scenario_field_name(expected)?;
        let value = self.name(expected)?;
        self.newline();
        Some(value)
    }

    fn parse_scenario_field_name(&mut self, expected: &str) -> Option<()> {
        let (name, span) = match self.current().kind.clone() {
            TokenKind::Name(name) => {
                let token = self.bump();
                (name, token.span)
            }
            TokenKind::Keyword(Keyword::Error) if expected == "error" => {
                let token = self.bump();
                ("error".to_owned(), token.span)
            }
            _ => {
                self.error(
                    format!("expected `{expected}` fixture field"),
                    self.span_here(),
                );
                return None;
            }
        };
        if name != expected {
            self.error(format!("expected `{expected}` fixture field"), span);
            return None;
        }
        self.expect(TokenKind::Colon, "expected `:` after fixture field")?;
        Some(())
    }

    fn parse_scenario_integer_argument(&mut self, expected: &str) -> Option<ScenarioInteger> {
        self.parse_scenario_field_name(expected)?;
        self.integer("fixture integer")
    }

    fn parse_scenario_data_argument(&mut self, expected: &str) -> Option<ScenarioData> {
        self.parse_scenario_field_name(expected)?;
        self.parse_scenario_data()
    }

    fn parse_scenario_string_argument(&mut self, expected: &str) -> Option<String> {
        self.parse_scenario_string_argument_span(expected)
            .map(|(value, _)| value)
    }

    fn parse_scenario_string_argument_span(&mut self, expected: &str) -> Option<(String, Span)> {
        self.parse_scenario_field_name(expected)?;
        self.string(expected)
    }
    fn parse_enum(
        &mut self,
        annotations: Vec<Annotation>,
        doc: Option<DocBlock>,
    ) -> Option<EnumDecl> {
        let st = self.keyword(Keyword::Enum)?.span;
        let (name, _) = self.name("type name")?;
        let generics = self.parse_generics(true)?;
        self.expect(TokenKind::Colon, "expected `:` after enum")?;
        self.newline();
        self.expect(TokenKind::Indent, "expected indented enum variants")?;
        let mut variants = Vec::new();
        self.skip_newlines();
        while !self.at(&TokenKind::Dedent) && !self.eof() {
            if let Some(v) = self.parse_variant() {
                variants.push(v);
            } else {
                self.recover_line();
            }
            self.skip_newlines();
        }
        let end = self.bump().span;
        Some(EnumDecl {
            span: Self::join(st, end),
            annotations,
            doc,
            name,
            generics,
            variants,
        })
    }
    fn parse_trait(
        &mut self,
        annotations: Vec<Annotation>,
        doc: Option<DocBlock>,
    ) -> Option<TraitDecl> {
        let st = self.keyword(Keyword::Trait)?.span;
        let (name, _) = self.name("trait name")?;
        let generics = self.parse_generics(true)?;
        let mut parents = Vec::new();
        if self.at(&TokenKind::Keyword(Keyword::For)) {
            self.bump();
            parents.push(self.parse_type()?);
            while self.at(&TokenKind::Plus) {
                self.bump();
                parents.push(self.parse_type()?);
            }
        }
        self.expect(TokenKind::Colon, "expected `:` after trait")?;
        self.newline();
        if !self.at(&TokenKind::Indent) {
            if parents.is_empty() {
                self.error("expected indented trait members", self.span_here());
                return None;
            }
            let end = self.tokens[self.pos - 1].span.clone();
            return Some(TraitDecl {
                span: Self::join(st, end),
                annotations,
                doc,
                name,
                generics,
                parents,
                associated_types: Vec::new(),
                methods: Vec::new(),
            });
        }
        self.expect(TokenKind::Indent, "expected indented trait members")?;
        let mut associated_types = Vec::new();
        let mut methods = Vec::new();
        let mut saw_method = false;
        self.skip_newlines();
        while !self.at(&TokenKind::Dedent) && !self.eof() {
            match self.current().kind.clone() {
                TokenKind::Keyword(Keyword::Type) => {
                    let associated = self.parse_associated_type_decl()?;
                    if saw_method {
                        self.error(
                            "trait associated types must precede methods",
                            associated.span.clone(),
                        );
                    }
                    associated_types.push(associated);
                }
                TokenKind::Keyword(Keyword::Fn) => {
                    saw_method = true;
                    methods.push(self.parse_trait_method(CallableKind::Sync)?);
                }
                TokenKind::Keyword(Keyword::Async) => {
                    saw_method = true;
                    methods.push(self.parse_trait_method(CallableKind::Async)?);
                }
                _ => {
                    self.error("expected trait associated type or method", self.span_here());
                    self.recover_line();
                }
            }
            self.skip_newlines();
        }
        if parents.is_empty() && associated_types.is_empty() && methods.is_empty() {
            self.error("trait requires a member or direct parent", self.span_here());
        }
        let end = self.bump().span;
        Some(TraitDecl {
            span: Self::join(st, end),
            annotations,
            doc,
            name,
            generics,
            parents,
            associated_types,
            methods,
        })
    }

    fn parse_associated_type_decl(&mut self) -> Option<AssociatedTypeDecl> {
        let st = self.keyword(Keyword::Type)?.span;
        let (name, name_span) = self.name("associated type name")?;
        let mut bounds = Vec::new();
        if self.at(&TokenKind::Colon) {
            self.bump();
            bounds.push(self.parse_type()?);
            while self.at(&TokenKind::Plus) {
                self.bump();
                bounds.push(self.parse_type()?);
            }
        }
        let end = bounds
            .last()
            .map(|bound| bound.span.clone())
            .unwrap_or(name_span);
        self.newline();
        Some(AssociatedTypeDecl {
            span: Self::join(st, end),
            name,
            bounds,
        })
    }
    fn parse_resource(
        &mut self,
        annotations: Vec<Annotation>,
        doc: Option<DocBlock>,
    ) -> Option<ResourceDecl> {
        let st = self.keyword(Keyword::Resource)?.span;
        let (name, _) = self.name("resource name")?;
        self.expect(TokenKind::Colon, "expected `:` after resource")?;
        self.newline();
        self.expect(TokenKind::Indent, "expected indented resource entries")?;
        let mut initial = None;
        let mut states = Vec::new();
        let mut terminals = Vec::new();
        let mut transitions = Vec::new();
        let mut phase = 0u8;
        self.skip_newlines();
        while !self.at(&TokenKind::Dedent) && !self.eof() {
            let rank = match self.current().kind.clone() {
                TokenKind::Keyword(Keyword::Initial) => 0,
                TokenKind::Keyword(Keyword::State) => 1,
                TokenKind::Keyword(Keyword::Terminal) => 2,
                TokenKind::Keyword(Keyword::Transition) => 3,
                _ => {
                    self.error("expected resource entry", self.span_here());
                    self.recover_line();
                    self.skip_newlines();
                    continue;
                }
            };
            if rank < phase {
                self.error("resource entries are out of order", self.span_here());
            }
            phase = phase.max(rank);
            match rank {
                0 => {
                    let entry = self.keyword(Keyword::Initial)?.span;
                    let (state, state_span) = self.name("initial resource state")?;
                    self.newline();
                    if initial.is_some() {
                        self.error("resource requires exactly one initial state", entry);
                    }
                    initial = Some(ResourceStateRef {
                        span: state_span,
                        name: state,
                    });
                }
                1 => {
                    let entry = self.keyword(Keyword::State)?.span;
                    let (state, state_span) = self.name("resource state name")?;
                    self.newline();
                    if states
                        .iter()
                        .any(|value: &ResourceState| value.name == state)
                    {
                        self.error("duplicate resource state", entry.clone());
                    }
                    states.push(ResourceState {
                        span: Self::join(entry, state_span),
                        name: state,
                    });
                }
                2 => {
                    let entry = self.keyword(Keyword::Terminal)?.span;
                    let (state, state_span) = self.name("terminal resource state")?;
                    self.newline();
                    if terminals
                        .iter()
                        .any(|value: &ResourceStateRef| value.name == state)
                    {
                        self.error("duplicate terminal resource state", entry);
                    }
                    terminals.push(ResourceStateRef {
                        span: state_span,
                        name: state,
                    });
                }
                _ => {
                    let entry = self.keyword(Keyword::Transition)?.span;
                    let (from, from_span) = self.name("resource transition source state")?;
                    self.expect(TokenKind::Arrow, "expected `->` in resource transition")?;
                    let (to, to_span) = self.name("resource transition target state")?;
                    self.newline();
                    if transitions.iter().any(|value: &ResourceTransition| {
                        value.from.name == from && value.to.name == to
                    }) {
                        self.error("duplicate resource transition", entry.clone());
                    }
                    transitions.push(ResourceTransition {
                        span: Self::join(entry, to_span.clone()),
                        from: ResourceStateRef {
                            span: from_span,
                            name: from,
                        },
                        to: ResourceStateRef {
                            span: to_span,
                            name: to,
                        },
                    });
                }
            }
            self.skip_newlines();
        }
        let end = self
            .expect(TokenKind::Dedent, "expected end of resource entries")?
            .span;
        let initial = match initial {
            Some(value) => value,
            None => {
                self.error("resource requires exactly one initial state", end.clone());
                return None;
            }
        };
        if states.is_empty() {
            self.error("resource requires at least one state", initial.span.clone());
        }
        if terminals.is_empty() {
            self.error(
                "resource requires at least one terminal state",
                initial.span.clone(),
            );
        }
        if transitions.is_empty() {
            self.error(
                "resource requires at least one transition",
                initial.span.clone(),
            );
        }
        Some(ResourceDecl {
            span: Self::join(st, end),
            annotations,
            doc,
            name,
            initial,
            states,
            terminals,
            transitions,
        })
    }

    fn parse_rule(
        &mut self,
        annotations: Vec<Annotation>,
        doc: Option<DocBlock>,
    ) -> Option<RuleDecl> {
        let st = self.keyword(Keyword::Rule)?.span;
        let (name, _) = self.name("rule name")?;
        let generics = self.parse_generics(false)?;
        let base = if self.at(&TokenKind::LParen) {
            self.bump();
            let b = self.parse_type()?;
            self.expect(TokenKind::RParen, "expected `)` after base rule")?;
            Some(b)
        } else {
            None
        };
        self.expect(TokenKind::Colon, "expected `:` after rule")?;
        self.newline();
        self.expect(TokenKind::Indent, "expected indented rule clauses")?;
        let mut clauses = Vec::new();
        self.skip_newlines();
        while !self.at(&TokenKind::Dedent) && !self.eof() {
            if let Some(c) = self.parse_rule_clause() {
                clauses.push(c);
            } else {
                self.recover_line();
            }
            self.skip_newlines();
        }
        let end = self.bump().span;
        Some(RuleDecl {
            span: Self::join(st, end),
            annotations,
            doc,
            name,
            generics,
            base,
            clauses,
        })
    }
    fn parse_rule_clause(&mut self) -> Option<RuleClause> {
        let (action, action_span) = if self.at(&TokenKind::Keyword(Keyword::Override)) {
            let tok = self.bump();
            (RuleClauseAction::Override, Some(tok.span))
        } else if self.at(&TokenKind::Keyword(Keyword::Delete))
            || self.at(&TokenKind::Keyword(Keyword::Remove))
        {
            let tok = self.bump();
            (RuleClauseAction::Delete, Some(tok.span))
        } else {
            (RuleClauseAction::Add, None)
        };
        let clause = self.parse_clause()?;
        let span = if let Some(start) = action_span {
            Self::join(start, clause.span.clone())
        } else {
            clause.span.clone()
        };
        Some(RuleClause {
            span,
            action,
            kind: clause.kind,
        })
    }
    fn parse_const(
        &mut self,
        annotations: Vec<Annotation>,
        doc: Option<DocBlock>,
    ) -> Option<ConstDecl> {
        let st = self.keyword(Keyword::Const)?.span;
        let (name, _) = self.name("constant name")?;
        self.expect(TokenKind::Colon, "expected `:` after constant")?;
        let ty = self.parse_type()?;
        self.expect(TokenKind::Equal, "expected `=` in constant")?;
        let value = self.parse_const_expr()?;
        let end = value.span().clone();
        self.newline();
        Some(ConstDecl {
            span: Self::join(st, end),
            annotations,
            doc,
            name,
            ty,
            value,
        })
    }
    fn parse_field(&mut self) -> Option<Field> {
        let (name, ns) = self.name("field name")?;
        self.expect(TokenKind::Colon, "expected `:` after field name")?;
        let ty = self.parse_type()?;
        let default = if self.at(&TokenKind::Equal) {
            self.bump();
            Some(self.parse_const_expr()?)
        } else {
            None
        };
        let end = default
            .as_ref()
            .map(|x| x.span().clone())
            .unwrap_or_else(|| ty.span.clone());
        self.newline();
        Some(Field {
            span: Self::join(ns, end),
            name,
            ty,
            default,
        })
    }
    fn parse_variant(&mut self) -> Option<Variant> {
        let (name, ns) = self.name("variant name")?;
        let mut parameters = Vec::new();
        let mut end = ns.clone();
        if self.at(&TokenKind::LParen) {
            self.bump();
            parameters = self.parse_parameters(false)?;
            let r = self.expect(TokenKind::RParen, "expected `)` after variant parameters")?;
            end = r.span;
        }
        self.newline();
        Some(Variant {
            span: Self::join(ns, end),
            name,
            parameters,
        })
    }
    fn parse_trait_method(&mut self, callable_kind: CallableKind) -> Option<TraitMethod> {
        let st = if callable_kind == CallableKind::Async {
            self.keyword(Keyword::Async)?.span
        } else {
            self.span_here()
        };
        self.keyword(Keyword::Fn)?;
        let (name, _) = self.name("function name")?;
        self.expect(TokenKind::LParen, "expected `(`")?;
        let self_tok = self.keyword(Keyword::SelfValue)?;
        let mut params = Vec::new();
        if self.at(&TokenKind::Comma) {
            self.bump();
            params = self.parse_parameters(true)?;
        }
        self.expect(TokenKind::RParen, "expected `)`")?;
        self.expect(TokenKind::Arrow, "expected `->`")?;
        let ret = self.parse_type()?;
        let default = if self.at(&TokenKind::Equal) {
            self.bump();
            Some(self.parse_qname()?)
        } else {
            None
        };
        let end = default
            .as_ref()
            .map(|value| value.span.clone())
            .unwrap_or_else(|| ret.span.clone());
        self.newline();
        Some(TraitMethod {
            span: Self::join(st, end),
            name,
            self_span: self_tok.span,
            parameters: params,
            return_type: ret,
            callable_kind,
            default,
        })
    }
    fn parse_function(
        &mut self,
        annotations: Vec<Annotation>,
        callable_kind: CallableKind,
        st: Span,
    ) -> Option<FunctionDecl> {
        self.keyword(Keyword::Fn)?;
        let (name, _) = self.name("function name")?;
        let generics = self.parse_generics(false)?;
        self.expect(TokenKind::LParen, "expected `(`")?;
        let params = self.parse_parameters(true)?;
        self.expect(TokenKind::RParen, "expected `)`")?;
        self.expect(TokenKind::Arrow, "expected `->`")?;
        let ret = self.parse_type()?;
        if callable_kind == CallableKind::Async
            && matches!(
                ret.path.segments.as_slice(),
                [name] if matches!(name.as_str(), "Iterator" | "Generator" | "Never")
            )
        {
            self.error(
                "top-level functions may not return Iterator, Generator, or Never",
                ret.span.clone(),
            );
        }
        let body = if self.at(&TokenKind::Newline) {
            let n = self.bump();
            FunctionBody::Signature { span: n.span }
        } else {
            self.expect(
                TokenKind::Colon,
                "expected `:` or end of line after function signature",
            )?;
            self.newline();
            self.expect(TokenKind::Indent, "expected indented function clauses")?;
            let mut clauses = Vec::new();
            let mut seen_doc = false;
            let mut phase = 0u8;
            self.skip_newlines();
            while !self.at(&TokenKind::Dedent) && !self.eof() {
                let c = self.parse_clause()?;
                let rank = match &c.kind {
                    ClauseKind::Documentation(_) => 0,
                    ClauseKind::Rule { .. } => 1,
                    ClauseKind::Requires { .. } => 2,
                    ClauseKind::Modifies { .. } => 3,
                    ClauseKind::Transitions { .. } => 3,
                    ClauseKind::Ensures { .. } => 3,
                    ClauseKind::Error { .. } => 4,
                    ClauseKind::Effects { .. } => 5,
                };
                if rank == 0 {
                    if seen_doc || phase > 0 {
                        self.error(
                            "function documentation must be the first clause and may occur once",
                            c.span.clone(),
                        );
                    }
                    seen_doc = true;
                } else {
                    if rank < phase {
                        self.error("function clauses are out of order", c.span.clone());
                    }
                    if rank == 5 && phase == 5 {
                        self.error("function may have only one effects clause", c.span.clone());
                    }
                    phase = phase.max(rank);
                }
                clauses.push(c);
                self.skip_newlines();
            }
            let d = self.expect(TokenKind::Dedent, "expected end of function clauses")?;
            FunctionBody::Clauses {
                span: d.span,
                clauses,
            }
        };
        let end = match &body {
            FunctionBody::Signature { span } | FunctionBody::Clauses { span, .. } => span.clone(),
        };
        Some(FunctionDecl {
            span: Self::join(st, end),
            annotations,
            name,
            generics,
            parameters: params,
            return_type: ret,
            callable_kind,
            body,
        })
    }
    fn parse_impl(&mut self, annotations: Vec<Annotation>) -> Option<ImplDecl> {
        let st = self.keyword(Keyword::Impl)?.span;
        let (name, _) = self.name("impl type name")?;
        self.keyword(Keyword::For)?;
        let mut traits = vec![self.parse_type()?];
        while self.at(&TokenKind::Plus) {
            self.bump();
            traits.push(self.parse_type()?);
        }
        self.expect(TokenKind::Colon, "expected `:` after impl traits")?;
        self.newline();
        self.expect(TokenKind::Indent, "expected indented impl body")?;
        self.skip_newlines();
        let mut associated_types = Vec::new();
        while self.at(&TokenKind::Keyword(Keyword::Type)) {
            associated_types.push(self.parse_associated_type_assignment()?);
            self.skip_newlines();
        }

        let state = if self.at(&TokenKind::Keyword(Keyword::State)) {
            self.parse_state_block()?
        } else {
            Vec::new()
        };
        self.skip_newlines();
        let mut invariants = Vec::new();
        while self.at(&TokenKind::Keyword(Keyword::Invariant)) {
            let invariant = self.parse_impl_invariant()?;
            invariants.push(invariant);
            self.skip_newlines();
        }
        let initializer = if self.at(&TokenKind::Keyword(Keyword::Init)) {
            let initializer = self.parse_impl_initializer()?;
            self.skip_newlines();
            Some(initializer)
        } else {
            None
        };
        let mut methods = Vec::new();
        while self.at(&TokenKind::Keyword(Keyword::Fn))
            || self.at(&TokenKind::Keyword(Keyword::Async))
        {
            let callable_kind = if self.at(&TokenKind::Keyword(Keyword::Async)) {
                CallableKind::Async
            } else {
                CallableKind::Sync
            };
            methods.push(self.parse_impl_method(callable_kind)?);
            self.skip_newlines();
        }
        while self.at(&TokenKind::Keyword(Keyword::Type)) {
            let associated = self.parse_associated_type_assignment()?;
            self.error(
                "impl associated type assignments must precede state",
                associated.span.clone(),
            );
            associated_types.push(associated);
            self.skip_newlines();
        }
        if methods.is_empty() {
            self.error("impl requires at least one method", self.span_here());
        }
        let end = self
            .expect(TokenKind::Dedent, "expected end of impl body")?
            .span;
        Some(ImplDecl {
            span: Self::join(st, end),
            annotations,
            name,
            traits,
            state,
            associated_types,
            invariants,
            initializer,
            methods,
        })
    }

    fn parse_associated_type_assignment(&mut self) -> Option<AssociatedTypeAssignment> {
        let st = self.keyword(Keyword::Type)?.span;
        let (name, _) = self.name("associated type name")?;
        self.expect(
            TokenKind::Equal,
            "expected `=` in associated type assignment",
        )?;
        let ty = self.parse_type()?;

        self.newline();
        Some(AssociatedTypeAssignment {
            span: Self::join(st, ty.span.clone()),
            name,
            ty,
        })
    }
    fn parse_specialize(&mut self, annotations: Vec<Annotation>) -> Option<SpecializeDecl> {
        let st = self.keyword(Keyword::Specialize)?.span;
        let (name, _) = self.name("specialized concrete type name")?;
        self.keyword(Keyword::For)?;
        let trait_ = self.parse_type()?;
        self.expect(TokenKind::Colon, "expected `:` after specialized trait")?;
        self.newline();
        self.expect(
            TokenKind::Indent,
            "expected indented specialization entries",
        )?;
        let mut entries = Vec::new();
        self.skip_newlines();
        while !self.at(&TokenKind::Dedent) && !self.eof() {
            let start = self.span_here();
            let Some((name, _)) = self.name("specialized method name") else {
                self.recover_line();
                self.skip_newlines();
                continue;
            };
            self.expect(TokenKind::Equal, "expected `=` in specialization entry")?;
            let target = match self.parse_qname() {
                Some(target) => target,
                None => {
                    self.recover_line();
                    self.skip_newlines();
                    continue;
                }
            };
            self.newline();
            entries.push(SpecializeEntry {
                span: Self::join(start, target.span.clone()),
                name,
                target,
            });
            self.skip_newlines();
        }
        if entries.is_empty() {
            self.error(
                "specialization requires at least one method entry",
                self.span_here(),
            );
        }
        let end = self
            .expect(TokenKind::Dedent, "expected end of specialization entries")?
            .span;
        Some(SpecializeDecl {
            span: Self::join(st, end),
            annotations,
            name,
            trait_,
            entries,
        })
    }

    fn parse_state_block(&mut self) -> Option<Vec<Field>> {
        self.keyword(Keyword::State)?;
        self.expect(TokenKind::Colon, "expected `:` after state")?;
        self.newline();
        self.expect(TokenKind::Indent, "expected indented state fields")?;
        self.skip_newlines();
        let mut fields = Vec::new();
        while !self.at(&TokenKind::Dedent) && !self.eof() {
            if let Some(field) = self.parse_field() {
                fields.push(field);
            } else {
                self.recover_line();
            }
            self.skip_newlines();
        }
        if fields.is_empty() {
            self.error(
                "state block must contain at least one field",
                self.span_here(),
            );
        }
        self.expect(TokenKind::Dedent, "expected end of state block")?;
        Some(fields)
    }
    fn parse_impl_invariant(&mut self) -> Option<ImplInvariant> {
        let st = self.keyword(Keyword::Invariant)?.span;
        let (guard, condition) = self.parse_guarded_condition(false)?;
        let end = condition.span.clone();
        self.newline();
        Some(ImplInvariant {
            span: Self::join(st, end),
            guard,
            condition,
        })
    }
    fn parse_impl_initializer(&mut self) -> Option<ImplInitializer> {
        let st = self.keyword(Keyword::Init)?.span;
        self.expect(TokenKind::LParen, "expected `(` after init")?;
        let parameters = self.parse_parameters(true)?;
        self.expect(TokenKind::RParen, "expected `)` after init parameters")?;
        self.expect(TokenKind::Colon, "expected `:` after init signature")?;
        self.newline();
        self.expect(TokenKind::Indent, "expected indented init clauses")?;
        let clauses = self.parse_impl_clauses(false)?;
        let end = self
            .expect(TokenKind::Dedent, "expected end of init clauses")?
            .span;
        Some(ImplInitializer {
            span: Self::join(st, end),
            parameters,
            clauses,
        })
    }
    fn parse_impl_method(&mut self, callable_kind: CallableKind) -> Option<ImplMethod> {
        let st = if callable_kind == CallableKind::Async {
            self.keyword(Keyword::Async)?.span
        } else {
            self.span_here()
        };
        self.keyword(Keyword::Fn)?;
        let (name, _) = self.name("method name")?;
        self.expect(TokenKind::LParen, "expected `(` after method name")?;
        let self_span = self.keyword(Keyword::SelfValue)?.span;
        let parameters = if self.at(&TokenKind::Comma) {
            self.bump();
            self.parse_parameters(true)?
        } else {
            Vec::new()
        };
        self.expect(TokenKind::RParen, "expected `)` after method parameters")?;
        self.expect(TokenKind::Arrow, "expected `->` after method parameters")?;
        let return_type = self.parse_type()?;
        self.expect(TokenKind::Colon, "expected `:` after method signature")?;
        self.newline();
        self.expect(TokenKind::Indent, "expected indented method clauses")?;
        let clauses = self.parse_impl_clauses(true)?;
        let end = self
            .expect(TokenKind::Dedent, "expected end of method clauses")?
            .span;
        Some(ImplMethod {
            span: Self::join(st, end),
            name,
            self_span,
            parameters,
            return_type,
            callable_kind,
            clauses,
        })
    }
    fn parse_impl_clauses(&mut self, method: bool) -> Option<Vec<Clause>> {
        let mut clauses = Vec::new();
        let mut seen_doc = false;
        let mut seen_modifies = false;
        let mut seen_transitions = false;
        let mut phase = 0u8;
        self.skip_newlines();
        while !self.at(&TokenKind::Dedent) && !self.eof() {
            let clause = if method {
                self.parse_method_clause()?
            } else {
                self.parse_init_clause()?
            };
            let rank = match &clause.kind {
                ClauseKind::Documentation(_) => 0,
                ClauseKind::Requires { .. } => 1,
                ClauseKind::Transitions { .. } => 2,
                ClauseKind::Modifies { .. } => 3,
                ClauseKind::Ensures { .. } => 4,
                ClauseKind::Error { .. } => 5,
                ClauseKind::Effects { .. } => 6,
                ClauseKind::Rule { .. } => unreachable!(),
            };
            if !method && rank > 4 {
                self.error(
                    "init clauses may contain only doc, requires, and ensures",
                    clause.span.clone(),
                );
            }
            if rank == 0 {
                if seen_doc || phase > 0 {
                    self.error(
                        "impl documentation must be the first clause and may occur once",
                        clause.span.clone(),
                    );
                }
                seen_doc = true;
            } else {
                if (!method && rank == 3) || rank < phase {
                    self.error("impl clauses are out of order", clause.span.clone());
                }
                if rank == 2 && seen_transitions {
                    self.error(
                        "method may have only one transitions clause",
                        clause.span.clone(),
                    );
                }
                if rank == 2 {
                    seen_transitions = true;
                }
                if rank == 3 && seen_modifies {
                    self.error(
                        "method may have only one modifies clause",
                        clause.span.clone(),
                    );
                }
                if rank == 3 {
                    seen_modifies = true;
                }
                if rank == 6 && phase == 6 {
                    self.error(
                        "impl method may have only one effects clause",
                        clause.span.clone(),
                    );
                }
                phase = phase.max(rank);
            }
            clauses.push(clause);
            self.skip_newlines();
        }
        if clauses.is_empty() {
            self.error("impl clause block must not be empty", self.span_here());
        }
        Some(clauses)
    }
    fn parse_init_clause(&mut self) -> Option<Clause> {
        if self.at(&TokenKind::Keyword(Keyword::Doc)) {
            let doc = self.parse_doc()?;
            return Some(Clause {
                span: doc.span.clone(),
                kind: ClauseKind::Documentation(doc),
            });
        }
        if self.at(&TokenKind::Keyword(Keyword::Requires)) {
            let st = self.bump().span;
            let (guard, condition) = self.parse_guarded_condition(false)?;
            let end = condition.span.clone();
            self.newline();
            return Some(Clause {
                span: Self::join(st, end),
                kind: ClauseKind::Requires { guard, condition },
            });
        }
        if self.at(&TokenKind::Keyword(Keyword::Ensures)) {
            let st = self.bump().span;
            let (guard, condition) = self.parse_ensures_condition(false)?;
            let end = condition.span.clone();
            self.newline();
            return Some(Clause {
                span: Self::join(st, end),
                kind: ClauseKind::Ensures { guard, condition },
            });
        }
        self.error("expected init clause", self.span_here());
        None
    }
    fn parse_method_clause(&mut self) -> Option<Clause> {
        if self.at(&TokenKind::Keyword(Keyword::Transitions)) {
            let st = self.bump().span;
            let mut transitions = Vec::new();
            loop {
                let field = self.parse_modified_field()?;
                self.expect(TokenKind::Colon, "expected `:` after transition field")?;
                let from = self.parse_qname()?;
                self.expect(TokenKind::Arrow, "expected `->` in method transition")?;
                let to = self.parse_qname()?;
                transitions.push(MethodTransition {
                    span: Self::join(field.span.clone(), to.span.clone()),
                    field,
                    from,
                    to,
                });
                if self.at(&TokenKind::Comma) {
                    self.bump();
                } else {
                    break;
                }
            }
            let end = transitions
                .last()
                .map(|transition| transition.span.clone())
                .unwrap_or(st.clone());
            self.newline();
            return Some(Clause {
                span: Self::join(st, end),
                kind: ClauseKind::Transitions { transitions },
            });
        }
        if self.at(&TokenKind::Keyword(Keyword::Modifies)) {
            let st = self.bump().span;
            let mut fields = vec![self.parse_modified_field()?];
            while self.at(&TokenKind::Comma) {
                self.bump();
                fields.push(self.parse_modified_field()?);
            }
            let end = fields
                .last()
                .map(|field| field.span.clone())
                .unwrap_or(st.clone());
            self.newline();
            return Some(Clause {
                span: Self::join(st, end),
                kind: ClauseKind::Modifies { fields },
            });
        }
        if self.at(&TokenKind::Keyword(Keyword::Ensures)) {
            let st = self.bump().span;
            let (guard, condition) = self.parse_ensures_condition(true)?;
            let end = condition.span.clone();
            self.newline();
            return Some(Clause {
                span: Self::join(st, end),
                kind: ClauseKind::Ensures { guard, condition },
            });
        }
        if self.at(&TokenKind::Keyword(Keyword::Doc))
            || self.at(&TokenKind::Keyword(Keyword::Requires))
            || self.at(&TokenKind::Keyword(Keyword::Error))
            || self.at(&TokenKind::Keyword(Keyword::Effects))
        {
            return self.parse_clause();
        }
        self.error("expected method clause", self.span_here());
        None
    }
    fn parse_guarded_condition(&mut self, allow_old: bool) -> Option<(Option<MatchGuard>, Expr)> {
        let previous = std::mem::replace(&mut self.allow_old, allow_old);
        let parsed = (|| {
            let scrutinee = self.parse_expr()?;
            if !self.at(&TokenKind::Keyword(Keyword::Matches)) {
                return Some((None, scrutinee));
            }
            self.bump();
            let pattern = self.parse_pattern()?;
            let end = pattern.span.clone();
            self.expect(TokenKind::FatArrow, "expected `=>` after match pattern")?;
            let condition = self.parse_expr()?;
            Some((
                Some(MatchGuard {
                    span: Self::join(scrutinee.span.clone(), end),
                    scrutinee,
                    pattern,
                }),
                condition,
            ))
        })();
        self.allow_old = previous;
        parsed
    }

    fn parse_ensures_condition(&mut self, allow_old: bool) -> Option<(Option<MatchGuard>, Expr)> {
        let save = self.pos;
        if matches!(self.current().kind, TokenKind::Name(_)) {
            if let Some(pattern) = self.parse_pattern() {
                if self.at(&TokenKind::FatArrow) {
                    self.bump();
                    let previous = std::mem::replace(&mut self.allow_old, allow_old);
                    let condition = self.parse_expr();
                    self.allow_old = previous;
                    let condition = condition?;
                    let result = Expr {
                        span: pattern.span.clone(),
                        kind: ExprKind::Name(QualifiedName::single(pattern.span.clone(), "result")),
                    };
                    return Some((
                        Some(MatchGuard {
                            span: pattern.span.clone(),
                            scrutinee: result,
                            pattern,
                        }),
                        condition,
                    ));
                }
            }
            self.pos = save;
        }
        self.parse_guarded_condition(allow_old)
    }

    fn parse_modified_field(&mut self) -> Option<ModifiedField> {
        let self_span = self.keyword(Keyword::SelfValue)?.span;
        self.expect(TokenKind::Dot, "expected `.` after self")?;
        let (name, field_span) = self.name("state field name")?;
        Some(ModifiedField {
            span: Self::join(self_span, field_span),
            name,
        })
    }
    fn parse_clause(&mut self) -> Option<Clause> {
        if self.at(&TokenKind::Keyword(Keyword::Doc)) {
            let d = self.parse_doc()?;
            let s = d.span.clone();
            return Some(Clause {
                span: s.clone(),
                kind: ClauseKind::Documentation(d),
            });
        }
        if self.at(&TokenKind::Keyword(Keyword::Rule)) {
            let st = self.bump().span;
            let name = self.parse_qname()?;
            let end = name.span.clone();
            self.newline();
            return Some(Clause {
                span: Self::join(st, end),
                kind: ClauseKind::Rule { name },
            });
        }
        if self.at(&TokenKind::Keyword(Keyword::Requires)) {
            let st = self.bump().span;
            let (guard, condition) = self.parse_guarded_condition(false)?;
            let end = condition.span.clone();
            self.newline();
            return Some(Clause {
                span: Self::join(st, end),
                kind: ClauseKind::Requires { guard, condition },
            });
        }
        if self.at(&TokenKind::Keyword(Keyword::Ensures)) {
            let st = self.bump().span;
            let (guard, condition) = self.parse_ensures_condition(false)?;
            let end = condition.span.clone();
            self.newline();
            return Some(Clause {
                span: Self::join(st, end),
                kind: ClauseKind::Ensures { guard, condition },
            });
        }
        if self.at(&TokenKind::Keyword(Keyword::Error)) {
            let st = self.bump().span;
            let error = self.parse_qname()?;
            let guard = if self.at(&TokenKind::Keyword(Keyword::With)) {
                self.bump();
                let scrutinee = self.parse_expr()?;
                self.keyword(Keyword::Matches)?;
                let pattern = self.parse_pattern()?;
                Some(MatchGuard {
                    span: Self::join(scrutinee.span.clone(), pattern.span.clone()),
                    scrutinee,
                    pattern,
                })
            } else {
                None
            };
            let when = if self.at(&TokenKind::Keyword(Keyword::When)) {
                self.bump();
                Some(self.parse_expr()?)
            } else {
                None
            };
            let end = when
                .as_ref()
                .map(|value| value.span.clone())
                .or_else(|| guard.as_ref().map(|value| value.span.clone()))
                .unwrap_or(error.span.clone());
            self.newline();
            return Some(Clause {
                span: Self::join(st, end),
                kind: ClauseKind::Error { error, guard, when },
            });
        }
        if self.at(&TokenKind::Keyword(Keyword::Effects)) {
            let st = self.bump().span;
            self.expect(TokenKind::LBracket, "expected `[` after effects")?;
            let mut effects = Vec::new();
            if !self.at(&TokenKind::RBracket) {
                loop {
                    effects.push(self.parse_qname()?);
                    if self.at(&TokenKind::Comma) {
                        self.bump();
                        if self.at(&TokenKind::RBracket) {
                            break;
                        }
                    } else {
                        break;
                    }
                }
            }
            let r = self.expect(TokenKind::RBracket, "expected `]` after effects")?;
            self.newline();
            return Some(Clause {
                span: Self::join(st, r.span),
                kind: ClauseKind::Effects { effects },
            });
        }
        self.error("expected function clause", self.span_here());
        None
    }
    fn parse_doc(&mut self) -> Option<DocBlock> {
        let st = self.keyword(Keyword::Doc)?.span;
        let t = match self.current().kind.clone() {
            TokenKind::TripleString(_) => self.bump(),
            _ => {
                self.error(
                    "expected triple-quoted documentation string",
                    self.span_here(),
                );
                return None;
            }
        };
        let text = match t.kind.clone() {
            TokenKind::TripleString(s) => s,
            _ => String::new(),
        };
        Some(DocBlock {
            span: Self::join(st, t.span.clone()),
            text: normalize_doc(&text),
        })
    }
    fn parse_qname(&mut self) -> Option<QualifiedName> {
        let (first, fs) = self.name("identifier")?;
        let mut segs = vec![first];
        let mut end = fs.clone();
        while self.at(&TokenKind::Dot) {
            if matches!(
                self.tokens.get(self.pos + 1).map(|t| &t.kind),
                Some(TokenKind::Name(_))
            ) {
                self.bump();
                let (s, sp) = self.name("identifier after `.`")?;
                segs.push(s);
                end = sp;
            } else if matches!(
                self.tokens.get(self.pos + 1).map(|t| &t.kind),
                Some(TokenKind::LBrace)
            ) {
                break;
            } else {
                self.bump();
                let (s, sp) = self.name("identifier after `.`")?;
                segs.push(s);
                end = sp;
            }
        }
        Some(QualifiedName::new(Self::join(fs, end), segs))
    }
    fn parse_generics(&mut self, allow_variance: bool) -> Option<Vec<GenericParam>> {
        if !self.at(&TokenKind::LBracket) {
            return Some(Vec::new());
        }
        self.bump();
        let mut out = Vec::new();
        if !self.at(&TokenKind::RBracket) {
            loop {
                let (variance, marker_span) = match self.current().kind.clone() {
                    TokenKind::Plus => (Variance::Covariant, Some(self.bump().span)),
                    TokenKind::Minus => (Variance::Contravariant, Some(self.bump().span)),
                    _ => (Variance::Invariant, None),
                };
                if marker_span.is_some()
                    && !allow_variance
                    && !self.at(&TokenKind::Keyword(Keyword::Const))
                {
                    self.error(
                        "variance markers are allowed only on struct, enum, and trait type parameters",
                        marker_span.clone().unwrap(),
                    );
                }
                if self.at(&TokenKind::Keyword(Keyword::Const)) {
                    let const_span = self.bump().span;
                    if let Some(marker_span) = marker_span {
                        self.error(
                            "variance marker is not allowed on const generic parameters",
                            marker_span,
                        );
                    }
                    let (name, _) = self.name("const generic parameter")?;
                    self.expect(
                        TokenKind::Colon,
                        "expected `:` after const generic parameter",
                    )?;
                    let (kind_name, kind_span) = self.name("const generic parameter kind")?;
                    let ty = match kind_name.as_str() {
                        "U8" => ConstKind::U8,
                        "U16" => ConstKind::U16,
                        "U32" => ConstKind::U32,
                        "U64" => ConstKind::U64,
                        _ => {
                            self.error(
                                "const generic parameter kind must be U8, U16, U32, or U64",
                                kind_span.clone(),
                            );
                            ConstKind::U8
                        }
                    };
                    out.push(GenericParam::Const {
                        span: Self::join(const_span, kind_span),
                        name,
                        ty,
                    });
                } else {
                    let (name, ns) = self.name("generic parameter")?;
                    let mut bounds = Vec::new();
                    if self.at(&TokenKind::Colon) {
                        self.bump();
                        bounds.push(self.parse_type()?);
                        while self.at(&TokenKind::Plus) {
                            self.bump();
                            bounds.push(self.parse_type()?);
                        }
                    }
                    let end = bounds
                        .last()
                        .map(|value| value.span.clone())
                        .unwrap_or(ns.clone());
                    out.push(GenericParam::Type {
                        span: Self::join(marker_span.unwrap_or(ns), end),
                        variance,
                        name,
                        bounds,
                    });
                }
                if self.at(&TokenKind::Comma) {
                    self.bump();
                    if self.at(&TokenKind::RBracket) {
                        break;
                    }
                } else {
                    break;
                }
            }
        }
        self.expect(TokenKind::RBracket, "expected `]` after generic parameters")?;
        Some(out)
    }

    fn parse_type(&mut self) -> Option<Type> {
        let path = self.parse_qname()?;
        let mut arguments = Vec::new();
        let mut end = path.span.clone();
        if self.at(&TokenKind::LBracket) {
            self.bump();
            let special = (path.segments.len() == 1).then(|| path.segments[0].as_str());
            match special {
                Some("Tuple") => {
                    if self.at(&TokenKind::RBracket) {
                        self.error("Tuple requires at least one element type", self.span_here());
                    } else {
                        loop {
                            let element = self.parse_type()?;
                            arguments.push(GenericArg {
                                span: element.span.clone(),
                                kind: GenericArgKind::Type(element),
                            });
                            if self.at(&TokenKind::Comma) {
                                self.bump();
                                if self.at(&TokenKind::RBracket) {
                                    break;
                                }
                            } else {
                                break;
                            }
                        }
                    }
                }
                Some("Array") => {
                    let element = self.parse_type()?;
                    arguments.push(GenericArg {
                        span: element.span.clone(),
                        kind: GenericArgKind::Type(element),
                    });
                    self.expect(TokenKind::Comma, "expected `,` before Array length")?;
                    let length = self.parse_const_expr()?;
                    arguments.push(GenericArg {
                        span: length.span().clone(),
                        kind: GenericArgKind::Const(length),
                    });
                }
                Some("Buffer") => {
                    let length = self.parse_const_expr()?;
                    arguments.push(GenericArg {
                        span: length.span().clone(),
                        kind: GenericArgKind::Const(length),
                    });
                }
                _ => {
                    if !self.at(&TokenKind::RBracket) {
                        loop {
                            let argument = self.parse_generic_arg()?;
                            arguments.push(argument);
                            if self.at(&TokenKind::Comma) {
                                self.bump();
                                if self.at(&TokenKind::RBracket) {
                                    break;
                                }
                            } else {
                                break;
                            }
                        }
                    }
                }
            }
            let right = self.expect(TokenKind::RBracket, "expected `]` after type arguments")?;
            end = right.span;
        }
        Some(Type {
            span: Self::join(path.span.clone(), end),
            path,
            arguments,
        })
    }

    fn parse_generic_arg(&mut self) -> Option<GenericArg> {
        let aggregate = matches!(
            &self.current().kind,
            TokenKind::Name(name) if matches!(name.as_str(), "Tuple" | "Array" | "Buffer")
        ) && matches!(
            self.tokens.get(self.pos + 1).map(|token| &token.kind),
            Some(TokenKind::LParen)
        );
        if aggregate
            || matches!(
                self.current().kind,
                TokenKind::Integer(_)
                    | TokenKind::Float(_)
                    | TokenKind::String(_)
                    | TokenKind::Keyword(Keyword::True | Keyword::False)
            )
        {
            let value = self.parse_const_expr()?;
            return Some(GenericArg {
                span: value.span().clone(),
                kind: GenericArgKind::Const(value),
            });
        }
        if matches!(self.current().kind, TokenKind::Name(_)) {
            let save = self.pos;
            let ty = self.parse_type()?;
            if self.at(&TokenKind::Comma) || self.at(&TokenKind::RBracket) {
                if ty.arguments.is_empty() {
                    let value = ConstExpr::Expression(Expr {
                        span: ty.span.clone(),
                        kind: ExprKind::Name(ty.path.clone()),
                    });
                    return Some(GenericArg {
                        span: ty.span.clone(),
                        kind: GenericArgKind::Ambiguous { ty, value },
                    });
                }
                return Some(GenericArg {
                    span: ty.span.clone(),
                    kind: GenericArgKind::Type(ty),
                });
            }
            self.pos = save;
            let value = self.parse_const_expr()?;
            return Some(GenericArg {
                span: value.span().clone(),
                kind: GenericArgKind::Const(value),
            });
        }
        let ty = self.parse_type()?;
        Some(GenericArg {
            span: ty.span.clone(),
            kind: GenericArgKind::Type(ty),
        })
    }
    fn parse_parameters(&mut self, trailing: bool) -> Option<Vec<Parameter>> {
        let mut out = Vec::new();
        if self.at(&TokenKind::RParen) {
            return Some(out);
        }
        loop {
            let (name, ns) = self.name("parameter name")?;
            self.expect(TokenKind::Colon, "expected `:` after parameter name")?;
            let ty = self.parse_type()?;
            out.push(Parameter {
                span: Self::join(ns, ty.span.clone()),
                name,
                ty,
            });
            if self.at(&TokenKind::Comma) {
                self.bump();
                if self.at(&TokenKind::RParen) {
                    break;
                }
            } else {
                break;
            }
        }
        let _ = trailing;
        Some(out)
    }
    fn parse_const_expr(&mut self) -> Option<ConstExpr> {
        if matches!(self.current().kind, TokenKind::Name(_)) {
            let save = self.pos;
            if let Some(path) = self.parse_qname() {
                if self.at(&TokenKind::LParen) {
                    self.bump();
                    if path.segments.len() == 1 && path.segments[0] == "Tuple" {
                        let (values, end) = self.parse_const_values(true, "Tuple")?;
                        return Some(ConstExpr::Tuple {
                            span: Self::join(path.span.clone(), end),
                            values,
                        });
                    }
                    if path.segments.len() == 1 && path.segments[0] == "Array" {
                        let (values, end) = self.parse_const_values(false, "Array")?;
                        return Some(ConstExpr::Array {
                            span: Self::join(path.span.clone(), end),
                            values,
                        });
                    }
                    if path.segments.len() == 1 && path.segments[0] == "Buffer" {
                        let token = match self.current().kind.clone() {
                            TokenKind::String(_) => self.bump(),
                            _ => {
                                self.error(
                                    "Buffer constant requires a lowercase hexadecimal string",
                                    self.span_here(),
                                );
                                return None;
                            }
                        };
                        let hex = match token.kind {
                            TokenKind::String(value) => value,
                            _ => String::new(),
                        };
                        if hex.len() % 2 != 0
                            || !hex
                                .bytes()
                                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
                        {
                            self.error(
                                "Buffer constant must contain lowercase hexadecimal bytes",
                                token.span.clone(),
                            );
                        }
                        let end = self
                            .expect(TokenKind::RParen, "expected `)` after Buffer constant")?
                            .span;
                        return Some(ConstExpr::Buffer {
                            span: Self::join(path.span.clone(), end),
                            hex,
                        });
                    }
                    let argument = self.parse_const_expr()?;
                    let end = self
                        .expect(TokenKind::RParen, "expected `)` in constructor")?
                        .span;
                    return Some(ConstExpr::Constructor {
                        span: Self::join(path.span.clone(), end),
                        path,
                        argument: Box::new(argument),
                    });
                }
                self.pos = save;
            }
        }
        Some(ConstExpr::Expression(self.parse_expr()?))
    }

    fn parse_const_values(
        &mut self,
        require_one: bool,
        aggregate: &str,
    ) -> Option<(Vec<ConstExpr>, Span)> {
        let mut values = Vec::new();
        if self.at(&TokenKind::RParen) && require_one {
            self.error(
                format!("{aggregate} constant requires at least one value"),
                self.span_here(),
            );
        }
        while !self.at(&TokenKind::RParen) {
            values.push(self.parse_const_expr()?);
            if self.at(&TokenKind::Comma) {
                self.bump();
                if self.at(&TokenKind::RParen) {
                    break;
                }
            } else {
                break;
            }
        }
        let end = self.expect(
            TokenKind::RParen,
            &format!("expected `)` after {aggregate} constant"),
        )?;
        Some((values, end.span))
    }
    fn parse_pattern(&mut self) -> Option<Pattern> {
        if let TokenKind::Name(n) = self.current().kind.clone() {
            let t = self.bump();
            if n == "_" {
                return Some(Pattern {
                    span: t.span,
                    kind: PatternKind::Wildcard,
                });
            }
            let path = self.parse_qname_after(n, t.span.clone());
            let mut args = Vec::new();
            if self.at(&TokenKind::LParen) {
                self.bump();
                if !self.at(&TokenKind::RParen) {
                    loop {
                        let p = self.parse_pattern()?;
                        args.push(p);
                        if self.at(&TokenKind::Comma) {
                            self.bump();
                            if self.at(&TokenKind::RParen) {
                                break;
                            }
                        } else {
                            break;
                        }
                    }
                }
                let r = self.expect(TokenKind::RParen, "expected `)` in pattern")?;
                return Some(Pattern {
                    span: Self::join(path.span.clone(), r.span),
                    kind: PatternKind::Variant {
                        path,
                        arguments: args,
                    },
                });
            }
            if path.segments.len() == 1 {
                Some(Pattern {
                    span: path.span.clone(),
                    kind: PatternKind::Binding(path.segments[0].clone()),
                })
            } else {
                Some(Pattern {
                    span: path.span.clone(),
                    kind: PatternKind::Variant {
                        path,
                        arguments: args,
                    },
                })
            }
        } else {
            self.error("expected pattern", self.span_here());
            None
        }
    }
    fn parse_qname_after(&mut self, first: String, fs: Span) -> QualifiedName {
        let mut segs = vec![first];
        let mut end = fs.clone();
        while self.at(&TokenKind::Dot) {
            self.bump();
            if let Some((s, sp)) = self.name("identifier after `.`") {
                segs.push(s);
                end = sp;
            } else {
                break;
            }
        }
        QualifiedName::new(Self::join(fs, end), segs)
    }
    fn parse_expr(&mut self) -> Option<Expr> {
        self.parse_or()
    }
    fn parse_or(&mut self) -> Option<Expr> {
        self.binary(Self::parse_and, &[Keyword::Or], BinaryOp::Or)
    }
    fn parse_and(&mut self) -> Option<Expr> {
        self.binary(Self::parse_not, &[Keyword::And], BinaryOp::And)
    }
    fn parse_not(&mut self) -> Option<Expr> {
        if self.at(&TokenKind::Keyword(Keyword::Not)) {
            let st = self.bump().span;
            let operand = self.parse_not_or_compare()?;
            let span = Self::join(st, operand.span.clone());
            Some(Expr {
                span,
                kind: ExprKind::Unary {
                    op: UnaryOp::Not,
                    operand: Box::new(operand),
                },
            })
        } else {
            self.parse_compare()
        }
    }
    fn parse_not_or_compare(&mut self) -> Option<Expr> {
        self.parse_compare()
    }
    fn binary(
        &mut self,
        next: fn(&mut Parser) -> Option<Expr>,
        kws: &[Keyword],
        op: BinaryOp,
    ) -> Option<Expr> {
        let mut left = next(self)?;
        while kws.iter().any(|k| self.at(&TokenKind::Keyword(*k))) {
            self.bump();
            let right = next(self)?;
            let span = Self::join(left.span.clone(), right.span.clone());
            left = Expr {
                span,
                kind: ExprKind::Binary {
                    left: Box::new(left),
                    op,
                    right: Box::new(right),
                },
            };
        }
        Some(left)
    }
    fn parse_compare(&mut self) -> Option<Expr> {
        let first = self.parse_add()?;
        let mut rest = Vec::new();
        while let Some(op) = self.compare_op() {
            self.bump();
            let rhs = self.parse_add()?;
            rest.push((op, rhs));
        }
        if rest.is_empty() {
            Some(first)
        } else {
            let end = rest
                .last()
                .map(|(_, e)| e.span.clone())
                .unwrap_or(first.span.clone());
            Some(Expr {
                span: Self::join(first.span.clone(), end),
                kind: ExprKind::Comparison {
                    first: Box::new(first),
                    rest,
                },
            })
        }
    }
    fn compare_op(&self) -> Option<CompareOp> {
        Some(match self.current().kind.clone() {
            TokenKind::EqualEqual => CompareOp::Equal,
            TokenKind::NotEqual => CompareOp::NotEqual,
            TokenKind::Less => CompareOp::Less,
            TokenKind::LessEqual => CompareOp::LessEqual,
            TokenKind::Greater => CompareOp::Greater,
            TokenKind::GreaterEqual => CompareOp::GreaterEqual,
            _ => return None,
        })
    }
    fn parse_add(&mut self) -> Option<Expr> {
        let mut left = self.parse_mul()?;
        loop {
            let op = match self.current().kind.clone() {
                TokenKind::Plus => BinaryOp::Add,
                TokenKind::Minus => BinaryOp::Subtract,
                _ => break,
            };
            self.bump();
            let right = self.parse_mul()?;
            let span = Self::join(left.span.clone(), right.span.clone());
            left = Expr {
                span,
                kind: ExprKind::Binary {
                    left: Box::new(left),
                    op,
                    right: Box::new(right),
                },
            };
        }
        Some(left)
    }
    fn parse_mul(&mut self) -> Option<Expr> {
        let mut left = self.parse_sign()?;
        loop {
            let op = match self.current().kind.clone() {
                TokenKind::Star => BinaryOp::Multiply,
                TokenKind::Slash => BinaryOp::Divide,
                TokenKind::Percent => BinaryOp::Remainder,
                _ => break,
            };
            self.bump();
            let right = self.parse_sign()?;
            let span = Self::join(left.span.clone(), right.span.clone());
            left = Expr {
                span,
                kind: ExprKind::Binary {
                    left: Box::new(left),
                    op,
                    right: Box::new(right),
                },
            };
        }
        Some(left)
    }
    fn parse_sign(&mut self) -> Option<Expr> {
        if self.at(&TokenKind::Plus) || self.at(&TokenKind::Minus) {
            let t = self.bump();
            let operand = self.parse_sign()?;
            let op = if t.kind == TokenKind::Plus {
                UnaryOp::Plus
            } else {
                UnaryOp::Minus
            };
            Some(Expr {
                span: Self::join(t.span, operand.span.clone()),
                kind: ExprKind::Unary {
                    op,
                    operand: Box::new(operand),
                },
            })
        } else {
            self.parse_primary()
        }
    }
    fn parse_primary(&mut self) -> Option<Expr> {
        let mut expr = match self.current().kind.clone() {
            TokenKind::Integer(v) => {
                let t = self.bump();
                Expr {
                    span: t.span.clone(),
                    kind: ExprKind::Literal(Literal {
                        span: t.span,
                        kind: LiteralKind::Integer(v),
                    }),
                }
            }
            TokenKind::Float(v) => {
                let t = self.bump();
                Expr {
                    span: t.span.clone(),
                    kind: ExprKind::Literal(Literal {
                        span: t.span,
                        kind: LiteralKind::Float(v),
                    }),
                }
            }
            TokenKind::String(v) => {
                let t = self.bump();
                Expr {
                    span: t.span.clone(),
                    kind: ExprKind::Literal(Literal {
                        span: t.span,
                        kind: LiteralKind::String(v),
                    }),
                }
            }
            TokenKind::Keyword(Keyword::True) | TokenKind::Keyword(Keyword::False) => {
                let t = self.bump();
                let b = t.kind == TokenKind::Keyword(Keyword::True);
                Expr {
                    span: t.span.clone(),
                    kind: ExprKind::Literal(Literal {
                        span: t.span,
                        kind: LiteralKind::Bool(b),
                    }),
                }
            }
            TokenKind::Keyword(Keyword::Old) => {
                let st = self.bump().span;
                self.expect(TokenKind::LParen, "expected `(` after old")?;
                let self_span = self.keyword(Keyword::SelfValue)?.span;
                self.expect(TokenKind::Dot, "expected `.` after self in old")?;
                let (name, field_span) = self.name("state field name")?;
                let end = self
                    .expect(TokenKind::RParen, "expected `)` after old state field")?
                    .span;
                if !self.allow_old {
                    self.error("old is only allowed in impl method ensures", st.clone());
                }
                Expr {
                    span: Self::join(st, end),
                    kind: ExprKind::OldStateField {
                        field: ModifiedField {
                            span: Self::join(self_span, field_span),
                            name,
                        },
                    },
                }
            }
            TokenKind::LParen => {
                let l = self.bump();
                if self.at(&TokenKind::RParen) {
                    let r = self.bump();
                    Expr {
                        span: Self::join(l.span, r.span),
                        kind: ExprKind::Unit,
                    }
                } else {
                    let inner = self.parse_expr()?;
                    let r = self.expect(TokenKind::RParen, "expected `)`")?;
                    Expr {
                        span: Self::join(l.span, r.span),
                        kind: ExprKind::Parenthesized(Box::new(inner)),
                    }
                }
            }
            TokenKind::Keyword(Keyword::SelfValue) => {
                let token = self.bump();
                Expr {
                    span: token.span.clone(),
                    kind: ExprKind::Name(QualifiedName::new(token.span, vec!["self".to_owned()])),
                }
            }
            TokenKind::Name(n) => {
                let t = self.bump();
                let q = self.parse_qname_after(n, t.span.clone());
                if self.at(&TokenKind::LParen) {
                    let Some(kind) = intrinsic(&q) else {
                        self.error(
                            "function calls are limited to closed invariant intrinsics",
                            q.span.clone(),
                        );
                        return None;
                    };
                    self.bump();
                    let mut arguments = Vec::new();
                    if !self.at(&TokenKind::RParen) {
                        loop {
                            arguments.push(self.parse_expr()?);
                            if self.at(&TokenKind::Comma) {
                                self.bump();
                            } else {
                                break;
                            }
                        }
                    }
                    let end = self
                        .expect(TokenKind::RParen, "expected `)` after intrinsic arguments")?
                        .span;
                    if arguments.len() != 2 {
                        self.error(
                            "closed invariant intrinsics require exactly two arguments",
                            q.span.clone(),
                        );
                    }
                    Expr {
                        span: Self::join(q.span, end),
                        kind: ExprKind::Intrinsic { kind, arguments },
                    }
                } else if q.segments.last().map(|s| s == "len").unwrap_or(false)
                    && q.segments.len() > 1
                {
                    let base_q = QualifiedName::new(
                        Span {
                            start: q.span.start,
                            end: q.span.end - 4,
                        },
                        q.segments[..q.segments.len() - 1].to_vec(),
                    );
                    let base = Expr {
                        span: base_q.span.clone(),
                        kind: ExprKind::Name(base_q),
                    };
                    Expr {
                        span: q.span.clone(),
                        kind: ExprKind::Field {
                            base: Box::new(base),
                            name: "len".to_owned(),
                        },
                    }
                } else {
                    Expr {
                        span: q.span.clone(),
                        kind: ExprKind::Name(q),
                    }
                }
            }
            _ => {
                self.error("expected expression", self.span_here());
                return None;
            }
        };
        loop {
            if !self.at(&TokenKind::Dot) {
                break;
            }
            self.bump();
            let (name, ns) = self.name("field name")?;
            let span = Self::join(expr.span.clone(), ns);
            expr = Expr {
                span,
                kind: ExprKind::Field {
                    base: Box::new(expr),
                    name,
                },
            };
        }
        Some(expr)
    }
}

fn normalize_doc(raw: &str) -> String {
    let mut lines: Vec<&str> = raw.split('\n').collect();
    if lines.first().map(|s| s.trim().is_empty()).unwrap_or(false) {
        lines.remove(0);
    }
    if lines.last().map(|s| s.trim().is_empty()).unwrap_or(false) {
        lines.pop();
    }
    let indent = lines
        .iter()
        .filter(|s| !s.trim().is_empty())
        .map(|s| s.len() - s.trim_start().len())
        .min()
        .unwrap_or(0);
    lines
        .into_iter()
        .map(|s| s.get(indent.min(s.len())..).unwrap_or(""))
        .collect::<Vec<_>>()
        .join("\n")
}

fn normalized_relative_path(path: &str) -> bool {
    !path.is_empty()
        && !path.starts_with('/')
        && !path.contains('\\')
        && path
            .split('/')
            .all(|part| !part.is_empty() && part != "." && part != "..")
}

fn normalized_route_path(path: &str) -> bool {
    path.starts_with('/')
        && !path.starts_with("//")
        && !path.contains('\\')
        && path[1..]
            .split('/')
            .all(|part| !part.is_empty() && part != "." && part != "..")
}

fn outcome_span(outcome: &ScenarioHttpOutcome) -> Span {
    match outcome {
        ScenarioHttpOutcome::Response { span, .. }
        | ScenarioHttpOutcome::Redirect { span, .. }
        | ScenarioHttpOutcome::Delay { span, .. }
        | ScenarioHttpOutcome::Disconnect { span } => span.clone(),
    }
}

fn intrinsic(name: &QualifiedName) -> Option<Intrinsic> {
    match name.segments.as_slice() {
        [name] => Some(match name.as_str() {
            "starts_with" => Intrinsic::StartsWith,
            "ends_with" => Intrinsic::EndsWith,
            "contains" => Intrinsic::Contains,
            "unique_by" => Intrinsic::UniqueBy,
            "descending_by" => Intrinsic::DescendingBy,
            _ => return None,
        }),
        _ => None,
    }
}
