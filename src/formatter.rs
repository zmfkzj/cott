use crate::ast::{
    BinaryOp, Clause, ClauseKind, CompareOp, ConstExpr, Declaration, DocBlock, Expr, ExprKind,
    File, FunctionBody, GenericParam, LiteralKind, Pattern, PatternKind, QualifiedName, Type,
    TypeArgKind, UnaryOp,
};
use crate::diagnostics::{Diagnostic, Span};
use crate::syntax::{Cst, TokenKind};

/// Renders the closed v0.1 grammar in one deterministic representation while
/// retaining literal spelling, decoded doc content, and comment attachment.
pub fn format(cst: &Cst, ast: &File) -> Result<Vec<u8>, Diagnostic> {
    let source = std::str::from_utf8(&cst.source).map_err(|_| {
        Diagnostic::error(
            crate::diagnostics::code::SYNTAX,
            "source is not UTF-8",
            Span::new(0, cst.source.len()),
        )
    })?;
    let mut printer = Printer::new(source, collect_comments(cst));
    printer.file(ast);
    Ok(printer.finish())
}

#[derive(Clone)]
struct Comment {
    offset: usize,
    line: usize,
    inline: bool,
    text: String,
}

fn collect_comments(cst: &Cst) -> Vec<Comment> {
    let source = &cst.source;
    let strings = cst
        .tokens
        .iter()
        .filter(|token| {
            matches!(
                token.kind,
                TokenKind::String(_) | TokenKind::TripleString(_)
            )
        })
        .map(|token| token.span.start..token.span.end)
        .collect::<Vec<_>>();
    let mut comments = Vec::new();
    let mut offset = 0;
    let mut line = 0;
    let mut line_start = 0;
    while offset < source.len() {
        if source[offset] == b'\n' {
            line += 1;
            offset += 1;
            line_start = offset;
            continue;
        }
        if source[offset] == b'#'
            && !strings
                .iter()
                .any(|range| range.start <= offset && offset < range.end)
        {
            let end = source[offset..]
                .iter()
                .position(|byte| *byte == b'\n' || *byte == b'\r')
                .map_or(source.len(), |length| offset + length);
            comments.push(Comment {
                offset,
                line,
                inline: source[line_start..offset]
                    .iter()
                    .any(|byte| !byte.is_ascii_whitespace()),
                text: String::from_utf8_lossy(&source[offset..end]).into_owned(),
            });
            offset = end;
        } else {
            offset += 1;
        }
    }
    comments
}

struct Printer<'a> {
    source: &'a str,
    line_starts: Vec<usize>,
    comments: Vec<Comment>,
    next_comment: usize,
    lines: Vec<String>,
}

impl<'a> Printer<'a> {
    fn new(source: &'a str, comments: Vec<Comment>) -> Self {
        let mut line_starts = vec![0];
        line_starts.extend(
            source
                .bytes()
                .enumerate()
                .filter_map(|(offset, byte)| (byte == b'\n').then_some(offset + 1)),
        );
        Self {
            source,
            line_starts,
            comments,
            next_comment: 0,
            lines: Vec::new(),
        }
    }

    fn finish(mut self) -> Vec<u8> {
        self.leading(usize::MAX, 0);
        while self.lines.last().is_some_and(String::is_empty) {
            self.lines.pop();
        }
        let mut bytes = self.lines.join("\n").into_bytes();
        bytes.push(b'\n');
        bytes
    }

    fn file(&mut self, file: &File) {
        self.leading(file.module.span.start, 0);
        self.push(0, format!("module {}", qname(&file.module.path)));
        self.inline_for(&file.module.span);
        self.blank();

        for use_decl in &file.uses {
            self.leading(use_decl.span.start, 0);
            if let Some(names) = &use_decl.names {
                self.comma_list(
                    0,
                    format!("use {}.{{", qname(&use_decl.path)),
                    names.clone(),
                    "}".to_owned(),
                );
            } else {
                self.push(0, format!("use {}", qname(&use_decl.path)));
            }
            self.inline_for(&use_decl.span);
        }
        if !file.uses.is_empty() {
            self.blank();
        }

        for (index, declaration) in file.declarations.iter().enumerate() {
            self.leading(declaration.span().start, 0);
            self.declaration(declaration);
            if index + 1 != file.declarations.len() {
                self.blank();
            }
        }
    }

    fn declaration(&mut self, declaration: &Declaration) {
        match declaration {
            Declaration::Alias(value) => {
                self.doc(value.doc.as_ref(), 0);
                self.push(
                    0,
                    format!("alias {} = {}", value.name, self.ty(&value.target)),
                );
                self.inline_for(&value.span);
            }
            Declaration::Newtype(value) => {
                self.doc(value.doc.as_ref(), 0);
                self.push(
                    0,
                    format!("newtype {}({})", value.name, self.ty(&value.underlying)),
                );
                self.inline_line(self.keyword_line(&value.span, "newtype "));
                if let Some(condition) = &value.where_clause {
                    self.leading(condition.span.start, 1);
                    self.expression_line(1, "where ", condition);
                    self.inline_for(&condition.span);
                }
            }
            Declaration::Struct(value) => {
                self.doc(value.doc.as_ref(), 0);
                self.push(
                    0,
                    format!("struct {}{}:", value.name, self.generics(&value.generics)),
                );
                self.inline_line(self.keyword_line(&value.span, "struct "));
                for field in &value.fields {
                    self.leading(field.span.start, 1);
                    let mut line = format!("{}: {}", field.name, self.ty(&field.ty));
                    if let Some(default) = &field.default {
                        line.push_str(" = ");
                        line.push_str(&self.const_expr(default));
                    }
                    self.push(1, line);
                    self.inline_for(&field.span);
                }
            }
            Declaration::Enum(value) => {
                self.doc(value.doc.as_ref(), 0);
                self.push(
                    0,
                    format!("enum {}{}:", value.name, self.generics(&value.generics)),
                );
                self.inline_line(self.keyword_line(&value.span, "enum "));
                for variant in &value.variants {
                    self.leading(variant.span.start, 1);
                    if variant.parameters.is_empty() {
                        self.push(1, variant.name.clone());
                    } else {
                        self.comma_list(
                            1,
                            format!("{}(", variant.name),
                            variant
                                .parameters
                                .iter()
                                .map(|parameter| {
                                    format!("{}: {}", parameter.name, self.ty(&parameter.ty))
                                })
                                .collect(),
                            ")".to_owned(),
                        );
                    }
                    self.inline_for(&variant.span);
                }
            }
            Declaration::Trait(value) => {
                self.doc(value.doc.as_ref(), 0);
                self.push(
                    0,
                    format!("trait {}{}:", value.name, self.generics(&value.generics)),
                );
                self.inline_line(self.keyword_line(&value.span, "trait "));
                for method in &value.methods {
                    self.leading(method.span.start, 1);
                    let mut parameters = vec!["self".to_owned()];
                    parameters.extend(method.parameters.iter().map(|parameter| {
                        format!("{}: {}", parameter.name, self.ty(&parameter.ty))
                    }));
                    self.comma_list(
                        1,
                        format!("fn {}(", method.name),
                        parameters,
                        format!(") -> {}", self.ty(&method.return_type)),
                    );
                    self.inline_for(&method.span);
                }
            }
            Declaration::Const(value) => {
                self.doc(value.doc.as_ref(), 0);
                self.push(
                    0,
                    format!(
                        "const {}: {} = {}",
                        value.name,
                        self.ty(&value.ty),
                        self.const_expr(&value.value)
                    ),
                );
                self.inline_for(&value.span);
            }
            Declaration::Function(value) => {
                let parameters = value
                    .parameters
                    .iter()
                    .map(|parameter| format!("{}: {}", parameter.name, self.ty(&parameter.ty)))
                    .collect::<Vec<_>>();
                let suffix = format!(
                    ") -> {}{}",
                    self.ty(&value.return_type),
                    if matches!(value.body, FunctionBody::Clauses { .. }) {
                        ":"
                    } else {
                        ""
                    }
                );
                self.comma_list(
                    0,
                    format!("fn {}{}(", value.name, self.generics(&value.generics)),
                    parameters,
                    suffix,
                );
                self.inline_line(self.keyword_line(&value.span, "fn "));
                if let FunctionBody::Clauses { clauses, .. } = &value.body {
                    let mut previous_group = None;
                    for clause in clauses {
                        let group = clause_group(clause);
                        if previous_group.is_some_and(|previous| previous != group) {
                            self.blank();
                        }
                        self.leading(clause.span.start, 1);
                        self.clause(clause);
                        self.inline_for(&clause.span);
                        previous_group = Some(group);
                    }
                }
            }
        }
    }

    fn clause(&mut self, clause: &Clause) {
        match &clause.kind {
            ClauseKind::Documentation(doc) => self.doc(Some(doc), 1),
            ClauseKind::Requires { condition } => self.expression_line(1, "requires ", condition),
            ClauseKind::Ensures { pattern, condition } => {
                let prefix = pattern.as_ref().map_or_else(
                    || "ensures ".to_owned(),
                    |pattern| format!("ensures {} => ", self.pattern(pattern)),
                );
                self.expression_line(1, &prefix, condition);
            }
            ClauseKind::Error { error, when } => {
                if let Some(condition) = when {
                    self.expression_line(1, &format!("error {} when ", qname(error)), condition);
                } else {
                    self.push(1, format!("error {}", qname(error)));
                }
            }
            ClauseKind::Effects { effects } => self.comma_list(
                1,
                "effects [".to_owned(),
                effects.iter().map(qname).collect(),
                "]".to_owned(),
            ),
        }
    }

    fn doc(&mut self, doc: Option<&DocBlock>, indent: usize) {
        let Some(doc) = doc else { return };
        self.leading(doc.span.start, indent);
        self.push(indent, "doc \"\"\"".to_owned());
        for line in doc.text.split('\n') {
            self.push(indent, line.to_owned());
        }
        self.push(indent, "\"\"\"".to_owned());
        self.inline_for(&doc.span);
    }

    fn generics(&self, generics: &[GenericParam]) -> String {
        if generics.is_empty() {
            return String::new();
        }
        format!(
            "[{}]",
            generics
                .iter()
                .map(|generic| {
                    if generic.bounds.is_empty() {
                        generic.name.clone()
                    } else {
                        format!(
                            "{}: {}",
                            generic.name,
                            generic
                                .bounds
                                .iter()
                                .map(|bound| self.ty(bound))
                                .collect::<Vec<_>>()
                                .join(" + ")
                        )
                    }
                })
                .collect::<Vec<_>>()
                .join(", ")
        )
    }

    fn ty(&self, ty: &Type) -> String {
        let mut rendered = qname(&ty.path);
        if !ty.arguments.is_empty() {
            rendered.push('[');
            rendered.push_str(
                &ty.arguments
                    .iter()
                    .map(|argument| match &argument.kind {
                        TypeArgKind::Type(ty) => self.ty(ty),
                        TypeArgKind::String(value) => self
                            .slice(&argument.span)
                            .map(str::to_owned)
                            .unwrap_or_else(|| serde_json::to_string(value).unwrap()),
                    })
                    .collect::<Vec<_>>()
                    .join(", "),
            );
            rendered.push(']');
        }
        rendered
    }

    fn const_expr(&self, expression: &ConstExpr) -> String {
        match expression {
            ConstExpr::Expression(expression) => self.expr(expression, 0),
            ConstExpr::Constructor { path, argument, .. } => {
                format!("{}({})", qname(path), self.const_expr(argument))
            }
        }
    }

    fn pattern(&self, pattern: &Pattern) -> String {
        match &pattern.kind {
            PatternKind::Wildcard => "_".to_owned(),
            PatternKind::Binding(name) => name.clone(),
            PatternKind::Variant { path, arguments } => {
                if arguments.is_empty() {
                    qname(path)
                } else {
                    format!(
                        "{}({})",
                        qname(path),
                        arguments
                            .iter()
                            .map(|argument| self.pattern(argument))
                            .collect::<Vec<_>>()
                            .join(", ")
                    )
                }
            }
        }
    }

    fn expr(&self, expression: &Expr, parent_precedence: u8) -> String {
        let precedence = expression_precedence(expression);
        let rendered = match &expression.kind {
            ExprKind::Literal(literal) => self
                .slice(&literal.span)
                .map(str::to_owned)
                .unwrap_or_else(|| match &literal.kind {
                    LiteralKind::Bool(true) => "true".to_owned(),
                    LiteralKind::Bool(false) => "false".to_owned(),
                    LiteralKind::Integer(value) | LiteralKind::Float(value) => value.clone(),
                    LiteralKind::String(value) => serde_json::to_string(value).unwrap(),
                }),
            ExprKind::Name(name) => qname(name),
            ExprKind::Unit => "()".to_owned(),
            ExprKind::Parenthesized(inner) => format!("({})", self.expr(inner, 0)),
            ExprKind::Unary { op, operand } => match op {
                UnaryOp::Not => format!("not {}", self.expr(operand, precedence)),
                UnaryOp::Plus => format!("+{}", self.expr(operand, precedence)),
                UnaryOp::Minus => format!("-{}", self.expr(operand, precedence)),
            },
            ExprKind::Binary { left, op, right } => format!(
                "{} {} {}",
                self.expr(left, precedence),
                binary_operator(*op),
                self.expr(right, precedence + 1)
            ),
            ExprKind::Comparison { first, rest } => {
                let mut rendered = self.expr(first, precedence);
                for (operator, expression) in rest {
                    rendered.push(' ');
                    rendered.push_str(compare_operator(*operator));
                    rendered.push(' ');
                    rendered.push_str(&self.expr(expression, precedence + 1));
                }
                rendered
            }
            ExprKind::Field { base, name } => {
                format!("{}.{}", self.expr(base, precedence), name)
            }
        };
        if precedence < parent_precedence {
            format!("({rendered})")
        } else {
            rendered
        }
    }

    fn expression_line(&mut self, indent: usize, prefix: &str, expression: &Expr) {
        let rendered = self.expr(expression, 0);
        if indent * 4 + prefix.chars().count() + rendered.chars().count() <= 100 {
            self.push(indent, format!("{prefix}{rendered}"));
            return;
        }
        if let Some(parts) = self.break_expression(expression) {
            self.push(indent, format!("{prefix}("));
            for (index, (operator, value)) in parts.into_iter().enumerate() {
                let line = if index == 0 {
                    value
                } else {
                    format!("{} {value}", operator.unwrap_or_default())
                };
                self.push(indent + 1, line);
            }
            self.push(indent, ")".to_owned());
        } else {
            self.push(indent, format!("{prefix}{rendered}"));
        }
    }

    fn break_expression(&self, expression: &Expr) -> Option<Vec<(Option<&'static str>, String)>> {
        match &expression.kind {
            ExprKind::Binary { left, op, right } => Some(vec![
                (None, self.expr(left, 0)),
                (Some(binary_operator(*op)), self.expr(right, 0)),
            ]),
            ExprKind::Comparison { first, rest } if !rest.is_empty() => {
                let mut parts = vec![(None, self.expr(first, 0))];
                parts.extend(rest.iter().map(|(operator, expression)| {
                    (Some(compare_operator(*operator)), self.expr(expression, 0))
                }));
                Some(parts)
            }
            _ => None,
        }
    }

    fn keyword_line(&self, span: &Span, keyword: &str) -> usize {
        let start = self.line_of(span.start);
        let end = self.line_of(span.end.saturating_sub(1));
        (start..=end)
            .find(|line| {
                let line_start = self.line_starts[*line];
                let line_end = self
                    .line_starts
                    .get(*line + 1)
                    .copied()
                    .unwrap_or(self.source.len());
                self.source[line_start..line_end]
                    .trim_start()
                    .starts_with(keyword)
            })
            .unwrap_or(start)
    }
    fn comma_list(&mut self, indent: usize, prefix: String, items: Vec<String>, suffix: String) {
        let single = format!("{prefix}{}{suffix}", items.join(", "));
        if indent * 4 + single.chars().count() <= 100 || items.is_empty() {
            self.push(indent, single);
            return;
        }
        self.push(indent, prefix);
        for item in items {
            self.push(indent + 1, format!("{item},"));
        }
        self.push(indent, suffix);
    }

    fn slice(&self, span: &Span) -> Option<&str> {
        self.source.get(span.start..span.end)
    }

    fn line_of(&self, offset: usize) -> usize {
        self.line_starts
            .partition_point(|start| *start <= offset)
            .saturating_sub(1)
    }

    fn leading(&mut self, before: usize, indent: usize) {
        while self
            .comments
            .get(self.next_comment)
            .is_some_and(|comment| comment.offset < before)
        {
            let comment = self.comments[self.next_comment].clone();
            self.push(indent, comment.text);
            self.next_comment += 1;
        }
    }

    fn inline_for(&mut self, span: &Span) {
        self.inline_line(self.line_of(span.end.saturating_sub(1)));
    }

    fn inline_line(&mut self, source_line: usize) {
        while let Some(comment) = self.comments.get(self.next_comment) {
            if !comment.inline || comment.line != source_line {
                break;
            }
            if let Some(line) = self.lines.last_mut() {
                line.push_str("  ");
                line.push_str(&comment.text);
            }
            self.next_comment += 1;
        }
    }

    fn push(&mut self, indent: usize, text: String) {
        self.lines.push(format!("{}{text}", "    ".repeat(indent)));
    }

    fn blank(&mut self) {
        if self.lines.last().is_some_and(|line| !line.is_empty()) {
            self.lines.push(String::new());
        }
    }
}

fn qname(name: &QualifiedName) -> String {
    name.segments.join(".")
}

fn clause_group(clause: &Clause) -> u8 {
    match clause.kind {
        ClauseKind::Documentation(_) => 0,
        ClauseKind::Requires { .. } => 1,
        ClauseKind::Ensures { .. } => 2,
        ClauseKind::Error { .. } => 3,
        ClauseKind::Effects { .. } => 4,
    }
}

fn expression_precedence(expression: &Expr) -> u8 {
    match &expression.kind {
        ExprKind::Binary { op, .. } => match op {
            BinaryOp::Or => 1,
            BinaryOp::And => 2,
            BinaryOp::Add | BinaryOp::Subtract => 4,
            BinaryOp::Multiply | BinaryOp::Divide | BinaryOp::Remainder => 5,
        },
        ExprKind::Comparison { .. } => 3,
        ExprKind::Unary { .. } => 6,
        ExprKind::Field { .. } => 7,
        _ => 8,
    }
}

const fn binary_operator(operator: BinaryOp) -> &'static str {
    match operator {
        BinaryOp::Or => "or",
        BinaryOp::And => "and",
        BinaryOp::Add => "+",
        BinaryOp::Subtract => "-",
        BinaryOp::Multiply => "*",
        BinaryOp::Divide => "/",
        BinaryOp::Remainder => "%",
    }
}

const fn compare_operator(operator: CompareOp) -> &'static str {
    match operator {
        CompareOp::Equal => "==",
        CompareOp::NotEqual => "!=",
        CompareOp::Less => "<",
        CompareOp::LessEqual => "<=",
        CompareOp::Greater => ">",
        CompareOp::GreaterEqual => ">=",
    }
}
