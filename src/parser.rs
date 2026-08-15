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
}

impl Parser {
    fn new(tokens: Vec<Token>) -> Self {
        Self {
            tokens,
            pos: 0,
            errors: Vec::new(),
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
                    Keyword::Module => "module",
                    Keyword::Use => "use",
                    Keyword::Alias => "alias",
                    Keyword::Newtype => "newtype",
                    Keyword::Struct => "struct",
                    Keyword::Enum => "enum",
                    Keyword::Trait => "trait",
                    Keyword::Rule => "rule",
                    Keyword::Const => "const",
                    Keyword::Fn => "fn",
                    Keyword::SelfValue => "self",
                    Keyword::Doc => "doc",
                    Keyword::Requires => "requires",
                    Keyword::Ensures => "ensures",
                    Keyword::When => "when",
                    Keyword::Effects => "effects",
                    Keyword::Error => "error",
                    Keyword::Where => "where",
                    Keyword::Override => "override",
                    Keyword::Delete => "delete",
                    Keyword::Remove => "remove",
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
            TokenKind::Keyword(Keyword::Const) => {
                Some(Declaration::Const(self.parse_const(annotations, doc)?))
            }
            TokenKind::Keyword(Keyword::Rule) => {
                Some(Declaration::Rule(self.parse_rule(annotations, doc)?))
            }
            TokenKind::Keyword(Keyword::Fn) => {
                if doc.is_some() {
                    self.error(
                        "top-level documentation must precede a type or constant declaration",
                        doc.unwrap().span,
                    );
                }
                Some(Declaration::Function(self.parse_function(annotations)?))
            }
            _ => {
                self.error("expected declaration", self.span_here());
                None
            }
        }
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
        let generics = self.parse_generics()?;
        self.expect(TokenKind::Colon, "expected `:` after struct")?;
        self.newline();
        self.expect(TokenKind::Indent, "expected indented struct fields")?;
        let mut fields = Vec::new();
        self.skip_newlines();
        while !self.at(&TokenKind::Dedent) && !self.eof() {
            if let Some(f) = self.parse_field() {
                fields.push(f);
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
        })
    }
    fn parse_enum(
        &mut self,
        annotations: Vec<Annotation>,
        doc: Option<DocBlock>,
    ) -> Option<EnumDecl> {
        let st = self.keyword(Keyword::Enum)?.span;
        let (name, _) = self.name("type name")?;
        let generics = self.parse_generics()?;
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
        let generics = self.parse_generics()?;
        self.expect(TokenKind::Colon, "expected `:` after trait")?;
        self.newline();
        self.expect(TokenKind::Indent, "expected indented trait methods")?;
        let mut methods = Vec::new();
        self.skip_newlines();
        while !self.at(&TokenKind::Dedent) && !self.eof() {
            if let Some(m) = self.parse_trait_method() {
                methods.push(m);
            } else {
                self.recover_line();
            }
            self.skip_newlines();
        }
        let end = self.bump().span;
        Some(TraitDecl {
            span: Self::join(st, end),
            annotations,
            doc,
            name,
            generics,
            methods,
        })
    }
    fn parse_rule(
        &mut self,
        annotations: Vec<Annotation>,
        doc: Option<DocBlock>,
    ) -> Option<RuleDecl> {
        let st = self.keyword(Keyword::Rule)?.span;
        let (name, _) = self.name("rule name")?;
        let generics = self.parse_generics()?;
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
    fn parse_trait_method(&mut self) -> Option<TraitMethod> {
        let st = self.keyword(Keyword::Fn)?.span;
        let (name, _) = self.name("function name")?;
        self.expect(TokenKind::LParen, "expected `(`")?;
        let self_tok = self.keyword(Keyword::SelfValue)?;
        let mut params = Vec::new();
        if self.at(&TokenKind::Comma) {
            self.bump();
            params = self.parse_parameters(true)?;
        }
        let rparen = self.expect(TokenKind::RParen, "expected `)`")?;
        self.expect(TokenKind::Arrow, "expected `->`")?;
        let ret = self.parse_type()?;
        self.newline();
        Some(TraitMethod {
            span: Self::join(st, rparen.span),
            name,
            self_span: self_tok.span,
            parameters: params,
            return_type: ret,
        })
    }
    fn parse_function(&mut self, annotations: Vec<Annotation>) -> Option<FunctionDecl> {
        let st = self.keyword(Keyword::Fn)?.span;
        let (name, _) = self.name("function name")?;
        let generics = self.parse_generics()?;
        self.expect(TokenKind::LParen, "expected `(`")?;
        let params = self.parse_parameters(true)?;
        self.expect(TokenKind::RParen, "expected `)`")?;
        self.expect(TokenKind::Arrow, "expected `->`")?;
        let ret = self.parse_type()?;
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
            body,
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
            let condition = self.parse_expr()?;
            let end = condition.span.clone();
            self.newline();
            return Some(Clause {
                span: Self::join(st, end),
                kind: ClauseKind::Requires { condition },
            });
        }
        if self.at(&TokenKind::Keyword(Keyword::Ensures)) {
            let st = self.bump().span;
            let save = self.pos;
            let mut pattern = None;
            if let Some(p) = self.parse_pattern() {
                if self.at(&TokenKind::FatArrow) {
                    self.bump();
                    pattern = Some(p);
                } else {
                    self.pos = save;
                }
            }
            let condition = self.parse_expr()?;
            let end = condition.span.clone();
            self.newline();
            return Some(Clause {
                span: Self::join(st, end),
                kind: ClauseKind::Ensures { pattern, condition },
            });
        }
        if self.at(&TokenKind::Keyword(Keyword::Error)) {
            let st = self.bump().span;
            let error = self.parse_qname()?;
            let when = if self.at(&TokenKind::Keyword(Keyword::When)) {
                self.bump();
                Some(self.parse_expr()?)
            } else {
                None
            };
            let end = when
                .as_ref()
                .map(|x| x.span.clone())
                .unwrap_or(error.span.clone());
            self.newline();
            return Some(Clause {
                span: Self::join(st, end),
                kind: ClauseKind::Error { error, when },
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
        self.newline();
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
    fn parse_generics(&mut self) -> Option<Vec<GenericParam>> {
        if !self.at(&TokenKind::LBracket) {
            return Some(Vec::new());
        }
        self.bump();
        let mut out = Vec::new();
        if !self.at(&TokenKind::RBracket) {
            loop {
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
                let end = bounds.last().map(|x| x.span.clone()).unwrap_or(ns.clone());
                out.push(GenericParam {
                    span: Self::join(ns, end),
                    name,
                    bounds,
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
        self.expect(TokenKind::RBracket, "expected `]` after generic parameters")?;
        Some(out)
    }
    fn parse_type(&mut self) -> Option<Type> {
        let path = self.parse_qname()?;
        let mut args = Vec::new();
        if self.at(&TokenKind::LBracket) {
            self.bump();
            if !self.at(&TokenKind::RBracket) {
                loop {
                    let arg = if matches!(self.current().kind.clone(), TokenKind::String(_)) {
                        let t = self.bump();
                        let value = match t.kind {
                            TokenKind::String(s) => s,
                            _ => String::new(),
                        };
                        TypeArg {
                            span: t.span.clone(),
                            kind: TypeArgKind::String(value),
                        }
                    } else {
                        let ty = self.parse_type()?;
                        TypeArg {
                            span: ty.span.clone(),
                            kind: TypeArgKind::Type(ty),
                        }
                    };
                    args.push(arg);
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
            self.expect(TokenKind::RBracket, "expected `]` after type arguments")?;
        }
        let end = args
            .last()
            .map(|x| x.span.clone())
            .unwrap_or(path.span.clone());
        Some(Type {
            span: Self::join(path.span.clone(), end),
            path,
            arguments: args,
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
                    let arg = self.parse_const_expr()?;
                    let r = self.expect(TokenKind::RParen, "expected `)` in constructor")?;
                    return Some(ConstExpr::Constructor {
                        span: Self::join(path.span.clone(), r.span),
                        path,
                        argument: Box::new(arg),
                    });
                }
                self.pos = save;
            }
        }
        Some(ConstExpr::Expression(self.parse_expr()?))
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
                if q.segments.last().map(|s| s == "len").unwrap_or(false) && q.segments.len() > 1 {
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
