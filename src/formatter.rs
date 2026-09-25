use crate::ast::{
    Annotation, BinaryOp, CallableKind, Clause, ClauseKind, CompareOp, ConstExpr, Declaration,
    DocBlock, Expr, ExprKind, File, FunctionBody, GenericArgKind, GenericParam, Intrinsic,
    LiteralKind, MatchGuard, Pattern, PatternKind, QualifiedName, RequirementText, RuleClause,
    RuleClauseAction, ScenarioAwaitOutcome, ScenarioData, ScenarioDataKind, ScenarioFixture,
    ScenarioFixtureConfig, ScenarioHttpOutcome, ScenarioStep, Type, UnaryOp, Variance,
};
use crate::diagnostics::{Diagnostic, Span};
use crate::syntax::{Cst, TokenKind};
/// Renders the closed v0.5 grammar in one deterministic representation while
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
            Declaration::ExternalType(value) => {
                self.annotations(&value.annotations);
                self.doc(value.doc.as_ref(), 0);
                self.push(0, format!("external type {}", value.name));
                self.inline_for(&value.span);
            }
            Declaration::Alias(value) => {
                self.annotations(&value.annotations);
                self.doc(value.doc.as_ref(), 0);
                self.push(
                    0,
                    format!("alias {} = {}", value.name, self.ty(&value.target)),
                );
                self.inline_for(&value.span);
            }
            Declaration::Newtype(value) => {
                self.annotations(&value.annotations);
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
                self.annotations(&value.annotations);
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
                if !value.fields.is_empty() && !value.invariants.is_empty() {
                    self.blank();
                }
                for invariant in &value.invariants {
                    self.leading(invariant.span.start, 1);
                    self.guarded_expression_line(
                        1,
                        "invariant ",
                        invariant.guard.as_ref(),
                        &invariant.condition,
                    );
                    self.inline_for(&invariant.span);
                }
            }
            Declaration::Enum(value) => {
                self.annotations(&value.annotations);
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
                self.annotations(&value.annotations);
                self.doc(value.doc.as_ref(), 0);
                let parents = if value.parents.is_empty() {
                    String::new()
                } else {
                    format!(
                        " for {}",
                        value
                            .parents
                            .iter()
                            .map(|parent| self.ty(parent))
                            .collect::<Vec<_>>()
                            .join(" + ")
                    )
                };
                self.push(
                    0,
                    format!(
                        "trait {}{}{}:",
                        value.name,
                        self.generics(&value.generics),
                        parents
                    ),
                );
                self.inline_line(self.keyword_line(&value.span, "trait "));
                for associated in &value.associated_types {
                    self.leading(associated.span.start, 1);
                    let bounds = if associated.bounds.is_empty() {
                        String::new()
                    } else {
                        format!(
                            ": {}",
                            associated
                                .bounds
                                .iter()
                                .map(|bound| self.ty(bound))
                                .collect::<Vec<_>>()
                                .join(" + ")
                        )
                    };
                    self.push(1, format!("type {}{}", associated.name, bounds));
                    self.inline_for(&associated.span);
                }
                for method in &value.methods {
                    self.leading(method.span.start, 1);
                    let mut parameters = vec!["self".to_owned()];
                    parameters.extend(method.parameters.iter().map(|parameter| {
                        format!("{}: {}", parameter.name, self.ty(&parameter.ty))
                    }));
                    let suffix = format!(
                        ") -> {}{}",
                        self.ty(&method.return_type),
                        method
                            .default
                            .as_ref()
                            .map(|value| format!(" = {}", qname(value)))
                            .unwrap_or_default()
                    );
                    self.comma_list(
                        1,
                        format!(
                            "{}fn {}(",
                            if method.callable_kind == CallableKind::Async {
                                "async "
                            } else {
                                ""
                            },
                            method.name
                        ),
                        parameters,
                        suffix,
                    );
                    self.inline_for(&method.span);
                }
            }
            Declaration::Impl(value) => {
                self.annotations(&value.annotations);
                self.push(
                    0,
                    format!(
                        "impl {} for {}:",
                        value.name,
                        value
                            .traits
                            .iter()
                            .map(|trait_ref| self.ty(trait_ref))
                            .collect::<Vec<_>>()
                            .join(" + ")
                    ),
                );
                self.inline_line(self.keyword_line(&value.span, "impl "));
                let mut wrote_section = false;
                for associated in &value.associated_types {
                    self.leading(associated.span.start, 1);
                    self.push(
                        1,
                        format!("type {} = {}", associated.name, self.ty(&associated.ty)),
                    );
                    self.inline_for(&associated.span);
                }
                if !value.associated_types.is_empty() {
                    wrote_section = true;
                }
                if !value.state.is_empty() {
                    self.push(1, "state:".to_owned());
                    self.inline_line(self.keyword_line(&value.span, "state"));
                    for field in &value.state {
                        self.leading(field.span.start, 2);
                        let mut line = format!("{}: {}", field.name, self.ty(&field.ty));
                        if let Some(default) = &field.default {
                            line.push_str(" = ");
                            line.push_str(&self.const_expr(default));
                        }
                        self.push(2, line);
                        self.inline_for(&field.span);
                    }
                    wrote_section = true;
                }
                if !value.invariants.is_empty() {
                    if wrote_section {
                        self.blank();
                    }
                    for invariant in &value.invariants {
                        self.leading(invariant.span.start, 1);
                        self.guarded_expression_line(
                            1,
                            "invariant ",
                            invariant.guard.as_ref(),
                            &invariant.condition,
                        );
                        self.inline_for(&invariant.span);
                    }
                    wrote_section = true;
                }
                if let Some(initializer) = &value.initializer {
                    if wrote_section {
                        self.blank();
                    }
                    let parameters = initializer
                        .parameters
                        .iter()
                        .map(|parameter| format!("{}: {}", parameter.name, self.ty(&parameter.ty)))
                        .collect();
                    self.comma_list(1, "init(".to_owned(), parameters, "):".to_owned());
                    self.inline_line(self.keyword_line(&initializer.span, "init"));
                    self.impl_clauses(&initializer.clauses);
                    wrote_section = true;
                }
                for method in &value.methods {
                    if wrote_section {
                        self.blank();
                    }
                    let mut parameters = vec!["self".to_owned()];
                    parameters.extend(method.parameters.iter().map(|parameter| {
                        format!("{}: {}", parameter.name, self.ty(&parameter.ty))
                    }));
                    self.comma_list(
                        1,
                        format!(
                            "{}fn {}(",
                            if method.callable_kind == CallableKind::Async {
                                "async "
                            } else {
                                ""
                            },
                            method.name
                        ),
                        parameters,
                        format!(") -> {}:", self.ty(&method.return_type)),
                    );
                    self.inline_line(self.keyword_line(&method.span, "fn "));
                    self.impl_clauses(&method.clauses);
                    wrote_section = true;
                }
            }
            Declaration::Specialize(value) => {
                self.annotations(&value.annotations);
                self.push(
                    0,
                    format!("specialize {} for {}:", value.name, self.ty(&value.trait_)),
                );
                self.inline_line(self.keyword_line(&value.span, "specialize "));
                for entry in &value.entries {
                    self.leading(entry.span.start, 1);
                    self.push(1, format!("{} = {}", entry.name, qname(&entry.target)));
                    self.inline_for(&entry.span);
                }
            }
            Declaration::Resource(value) => {
                self.annotations(&value.annotations);
                self.doc(value.doc.as_ref(), 0);
                self.push(0, format!("resource {}:", value.name));
                self.inline_line(self.keyword_line(&value.span, "resource "));
                self.leading(value.initial.span.start, 1);
                self.push(1, format!("initial {}", value.initial.name));
                self.inline_for(&value.initial.span);
                for state in &value.states {
                    self.leading(state.span.start, 1);
                    self.push(1, format!("state {}", state.name));
                    self.inline_for(&state.span);
                }
                for terminal in &value.terminals {
                    self.leading(terminal.span.start, 1);
                    self.push(1, format!("terminal {}", terminal.name));
                    self.inline_for(&terminal.span);
                }
                for transition in &value.transitions {
                    self.leading(transition.span.start, 1);
                    self.push(
                        1,
                        format!(
                            "transition {} -> {}",
                            transition.from.name, transition.to.name
                        ),
                    );
                    self.inline_for(&transition.span);
                }
            }
            Declaration::Const(value) => {
                self.annotations(&value.annotations);
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
            Declaration::Rule(value) => {
                self.annotations(&value.annotations);
                self.doc(value.doc.as_ref(), 0);
                let base_str = value
                    .base
                    .as_ref()
                    .map(|b| format!("({})", self.ty(b)))
                    .unwrap_or_default();
                self.push(
                    0,
                    format!(
                        "rule {}{}{}:",
                        value.name,
                        self.generics(&value.generics),
                        base_str
                    ),
                );
                self.inline_line(self.keyword_line(&value.span, "rule "));
                let mut previous_group = None;
                for rule_clause in &value.clauses {
                    let group = rule_clause_group(rule_clause);
                    if previous_group.is_some_and(|previous| previous != group) {
                        self.blank();
                    }
                    self.leading(rule_clause.span.start, 1);
                    self.rule_clause(rule_clause);
                    self.inline_for(&rule_clause.span);
                    previous_group = Some(group);
                }
            }
            Declaration::Scenario(value) => {
                self.annotations(&value.annotations);
                self.doc(value.doc.as_ref(), 0);
                let target = value
                    .target
                    .as_ref()
                    .map(|target| format!(" for {}", qname(target)))
                    .unwrap_or_default();
                self.push(0, format!("scenario {}{target}:", value.name));
                self.inline_line(self.keyword_line(&value.span, "scenario "));
                if !value.fixtures.is_empty() {
                    self.push(1, "fixtures:".to_owned());
                    for fixture in &value.fixtures {
                        self.scenario_fixture(fixture);
                    }
                }
                for step in &value.steps {
                    self.scenario_step(step);
                }
            }
            Declaration::TestData(value) => {
                self.value_lines(
                    0,
                    &format!("data {}: {} = ", value.name, self.ty(&value.ty)),
                    &value.value,
                    "",
                );
                self.inline_for(&value.span);
            }
            Declaration::Requirement(value) => {
                self.annotations(&value.annotations);
                self.doc(value.doc.as_ref(), 0);
                self.push(
                    0,
                    format!("requirement {} for {}:", value.name, qname(&value.callable)),
                );
                self.inline_line(self.keyword_line(&value.span, "requirement "));
                self.requirement_text("text", &value.statement);
                for check in &value.checked_by {
                    self.leading(check.span.start, 1);
                    let assertion = check
                        .assertion
                        .as_ref()
                        .map(|assertion| format!(" assert {}", assertion.value))
                        .unwrap_or_default();
                    self.push(
                        1,
                        format!("checked_by {}{assertion}", qname(&check.scenario)),
                    );
                    self.inline_for(&check.span);
                }
                for assumption in &value.assumptions {
                    self.requirement_text("assumption", assumption);
                }
                for waiver in &value.waivers {
                    self.requirement_text("waiver", waiver);
                }
            }

            Declaration::Function(value) => {
                self.annotations(&value.annotations);
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
                    format!(
                        "{}fn {}{}(",
                        if value.callable_kind == CallableKind::Async {
                            "async "
                        } else {
                            ""
                        },
                        value.name,
                        self.generics(&value.generics)
                    ),
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
    fn scenario_fixture(&mut self, fixture: &ScenarioFixture) {
        match &fixture.config {
            ScenarioFixtureConfig::Filesystem { files, .. } => {
                self.push(2, format!("fs {}:", fixture.name));
                for file in files {
                    self.push(
                        3,
                        format!(
                            "file {} {}",
                            serde_json::to_string(&file.path).unwrap(),
                            self.scenario_data(&file.contents)
                        ),
                    );
                }
            }
            ScenarioFixtureConfig::Http { routes, .. } => {
                self.push(2, format!("http {}:", fixture.name));
                for route in routes {
                    self.push(
                        3,
                        format!(
                            "route {} -> {}",
                            serde_json::to_string(&route.path).unwrap(),
                            self.http_outcome(&route.outcome)
                        ),
                    );
                }
            }
            ScenarioFixtureConfig::Clock {
                start_ms, tick_ms, ..
            } => {
                self.push(2, format!("clock {}:", fixture.name));
                self.push(3, format!("start_ms: {}", start_ms.value));
                self.push(3, format!("tick_ms: {}", tick_ms.value));
            }
            ScenarioFixtureConfig::Failure {
                point,
                occurrence,
                error,
                ..
            } => {
                self.push(2, format!("failure {}:", fixture.name));
                self.push(3, format!("point: {}", failure_point(point.kind)));
                self.push(3, format!("occurrence: {}", occurrence.value));
                self.push(3, format!("error: {}", failure_error(error.kind)));
            }
        }
    }

    fn scenario_step(&mut self, step: &ScenarioStep) {
        match step {
            ScenarioStep::Call {
                binding,
                target,
                arguments,
                ..
            } => self.invocation_lines(
                &format!("call {} = {}(", binding.name, qname(target)),
                arguments,
            ),
            ScenarioStep::Init {
                binding,
                target,
                arguments,
                ..
            } => {
                let prefix = format!("call {} = {}(", binding.name, qname(target));
                let inline = arguments
                    .iter()
                    .map(|argument| {
                        let label = argument
                            .label
                            .as_ref()
                            .map(|label| format!("{}: ", self.expr(label, 0)))
                            .unwrap_or_default();
                        format!("{label}{}", self.expr(&argument.value, 0))
                    })
                    .collect::<Vec<_>>()
                    .join(", ");
                if 4 + prefix.chars().count() + inline.chars().count() + 1 <= 100 {
                    self.push(1, format!("{prefix}{inline})"));
                } else {
                    self.push(1, prefix);
                    for argument in arguments {
                        let label = argument
                            .label
                            .as_ref()
                            .map(|label| format!("{}: ", self.expr(label, 0)))
                            .unwrap_or_default();
                        self.value_lines(2, &label, &argument.value, ",");
                    }
                    self.push(1, ")".to_owned());
                }
            }
            ScenarioStep::Spawn {
                worker,
                target,
                arguments,
                ..
            } => self.invocation_lines(
                &format!("spawn {} = {}(", worker.name, qname(target)),
                arguments,
            ),
            ScenarioStep::Await {
                worker, outcome, ..
            } => match outcome {
                ScenarioAwaitOutcome::Value(binding) => {
                    self.push(1, format!("await {} as {}", worker.name, binding.name));
                }
                ScenarioAwaitOutcome::Cancelled { .. } => {
                    self.push(1, format!("await {} cancelled", worker.name));
                }
            },
            ScenarioStep::Cancel { worker, .. } => {
                self.push(1, format!("cancel {}", worker.name));
            }
            ScenarioStep::Tick { .. } => self.push(1, "tick".to_owned()),
            ScenarioStep::Assert { expression, .. } => {
                if contains_construct(expression) {
                    self.value_lines(1, "assert ", expression, "");
                } else {
                    self.expression_line(1, "assert ", expression);
                }
            }
            ScenarioStep::Data {
                binding, ty, value, ..
            } => self.value_lines(
                1,
                &format!("data {}: {} = ", binding.name, self.ty(ty)),
                value,
                "",
            ),
        }
    }

    /// Existing scalar call lines stay on one line; only invocations carrying
    /// constructed values break into one indented argument per line.
    fn invocation_lines(&mut self, prefix: &str, arguments: &[Expr]) {
        let inline = format!(
            "{prefix}{})",
            arguments
                .iter()
                .map(|argument| self.expr(argument, 0))
                .collect::<Vec<_>>()
                .join(", ")
        );
        if 4 + inline.chars().count() <= 100 || !arguments.iter().any(contains_construct) {
            self.push(1, inline);
            return;
        }
        self.push(1, prefix.to_owned());
        for argument in arguments {
            self.leading(argument.span.start, 2);
            self.value_lines(2, "", argument, ",");
            self.inline_for(&argument.span);
        }
        self.push(1, ")".to_owned());
    }

    /// Lays out a scenario value inline when it fits, otherwise one constructor
    /// argument per line with trailing commas, recursively.
    fn value_lines(&mut self, indent: usize, prefix: &str, value: &Expr, suffix: &str) {
        let inline = self.expr(value, 0);
        if indent * 4 + prefix.chars().count() + inline.chars().count() + suffix.chars().count()
            <= 100
        {
            self.push(indent, format!("{prefix}{inline}{suffix}"));
            return;
        }
        match &value.kind {
            ExprKind::Construct { path, arguments } if !arguments.is_empty() => {
                self.push(indent, format!("{prefix}{}(", qname(path)));
                for argument in arguments {
                    self.leading(argument.span.start, indent + 1);
                    let label = argument
                        .label
                        .as_ref()
                        .map(|label| format!("{}: ", self.expr(label, 0)))
                        .unwrap_or_default();
                    self.value_lines(indent + 1, &label, &argument.value, ",");
                    self.inline_for(&argument.span);
                }
                self.push(indent, format!("){suffix}"));
            }
            ExprKind::Comparison { first, rest }
                if rest.len() == 1 && contains_construct(&rest[0].1) =>
            {
                let prefix = format!(
                    "{prefix}{} {} ",
                    self.expr(first, expression_precedence(value)),
                    compare_operator(rest[0].0)
                );
                self.value_lines(indent, &prefix, &rest[0].1, suffix);
            }
            _ => self.push(indent, format!("{prefix}{inline}{suffix}")),
        }
    }

    fn scenario_data(&self, data: &ScenarioData) -> String {
        let (kind, value) = match &data.kind {
            ScenarioDataKind::Text(value) => ("text", value),
            ScenarioDataKind::Bytes(value) => ("bytes", value),
            ScenarioDataKind::Hex(value) => ("hex", value),
        };
        format!("{kind}({})", serde_json::to_string(value).unwrap())
    }

    fn http_outcome(&self, outcome: &ScenarioHttpOutcome) -> String {
        match outcome {
            ScenarioHttpOutcome::Response {
                status,
                body,
                encoding,
                ..
            } => format!(
                "response(status: {}, body: {}, encoding: {})",
                status.value,
                self.scenario_data(body),
                serde_json::to_string(encoding).unwrap()
            ),
            ScenarioHttpOutcome::Redirect {
                status, location, ..
            } => format!(
                "redirect(status: {}, location: {})",
                status.value,
                serde_json::to_string(location).unwrap()
            ),
            ScenarioHttpOutcome::Delay { milliseconds, .. } => {
                format!("delay(ms: {})", milliseconds.value)
            }
            ScenarioHttpOutcome::Disconnect { .. } => "disconnect()".to_owned(),
        }
    }

    fn clause(&mut self, clause: &Clause) {
        self.clause_at(clause, 1);
    }

    fn impl_clauses(&mut self, clauses: &[Clause]) {
        let mut previous_group = None;
        for clause in clauses {
            let group = clause_group(clause);
            if previous_group.is_some_and(|previous| previous != group) {
                self.blank();
            }
            self.leading(clause.span.start, 2);
            self.clause_at(clause, 2);
            self.inline_for(&clause.span);
            previous_group = Some(group);
        }
    }

    fn clause_at(&mut self, clause: &Clause, indent: usize) {
        match &clause.kind {
            ClauseKind::Documentation(doc) => self.doc(Some(doc), indent),
            ClauseKind::Rule { name } => self.push(indent, format!("rule {}", qname(name))),
            ClauseKind::Requires { guard, condition } => {
                self.guarded_expression_line(indent, "requires ", guard.as_ref(), condition)
            }
            ClauseKind::Transitions { transitions } => self.push(
                indent,
                format!(
                    "transitions {}",
                    transitions
                        .iter()
                        .map(|transition| format!(
                            "self.{}: {} -> {}",
                            transition.field.name,
                            qname(&transition.from),
                            qname(&transition.to)
                        ))
                        .collect::<Vec<_>>()
                        .join(", ")
                ),
            ),
            ClauseKind::Modifies { fields } => self.push(
                indent,
                format!(
                    "modifies {}",
                    fields
                        .iter()
                        .map(|field| format!("self.{}", field.name))
                        .collect::<Vec<_>>()
                        .join(", ")
                ),
            ),
            ClauseKind::Ensures { guard, condition } => {
                self.ensures_expression_line(indent, "ensures ", guard.as_ref(), condition);
            }
            ClauseKind::EnsuresTable { .. } | ClauseKind::EnsuresPreserves { .. } => {
                self.ensures_sugar(indent, "ensures ", &clause.kind);
            }
            ClauseKind::ErrorsComplete => self.push(indent, "errors complete".to_owned()),
            ClauseKind::Error { error, guard, when } => {
                let mut prefix = format!("error {}", qname(error));
                if let Some(guard) = guard {
                    prefix.push_str(&format!(
                        " with {} matches {}",
                        self.expr(&guard.scrutinee, 0),
                        self.pattern(&guard.pattern),
                    ));
                }
                if let Some(condition) = when {
                    prefix.push_str(" when ");
                    self.expression_line(indent, &prefix, condition);
                } else {
                    self.push(indent, prefix);
                }
            }
            ClauseKind::Effects { effects } => self.comma_list(
                indent,
                "effects [".to_owned(),
                effects.iter().map(qname).collect(),
                "]".to_owned(),
            ),
        }
    }

    fn rule_clause(&mut self, rule_clause: &RuleClause) {
        let prefix = match rule_clause.action {
            RuleClauseAction::Add => "",
            RuleClauseAction::Override => "override ",
            RuleClauseAction::Delete => "delete ",
        };
        match &rule_clause.kind {
            ClauseKind::Documentation(doc) => self.doc(Some(doc), 1),
            ClauseKind::Rule { name } => self.push(1, format!("{prefix}rule {}", qname(name))),
            ClauseKind::Requires { guard, condition } => {
                self.guarded_expression_line(
                    1,
                    &format!("{prefix}requires "),
                    guard.as_ref(),
                    condition,
                );
            }
            ClauseKind::Transitions { transitions } => self.push(
                1,
                format!(
                    "{prefix}transitions {}",
                    transitions
                        .iter()
                        .map(|transition| format!(
                            "self.{}: {} -> {}",
                            transition.field.name,
                            qname(&transition.from),
                            qname(&transition.to)
                        ))
                        .collect::<Vec<_>>()
                        .join(", ")
                ),
            ),
            ClauseKind::Modifies { fields } => self.push(
                1,
                format!(
                    "{prefix}modifies {}",
                    fields
                        .iter()
                        .map(|field| format!("self.{}", field.name))
                        .collect::<Vec<_>>()
                        .join(", ")
                ),
            ),
            ClauseKind::Ensures { guard, condition } => {
                self.ensures_expression_line(
                    1,
                    &format!("{prefix}ensures "),
                    guard.as_ref(),
                    condition,
                );
            }
            ClauseKind::EnsuresTable { .. } | ClauseKind::EnsuresPreserves { .. } => {
                self.ensures_sugar(1, &format!("{prefix}ensures "), &rule_clause.kind);
            }
            ClauseKind::ErrorsComplete => self.push(1, format!("{prefix}errors complete")),
            ClauseKind::Error { error, guard, when } => {
                let mut rendered = format!("{prefix}error {}", qname(error));
                if let Some(guard) = guard {
                    rendered.push_str(&format!(
                        " with {} matches {}",
                        self.expr(&guard.scrutinee, 0),
                        self.pattern(&guard.pattern),
                    ));
                }
                if let Some(condition) = when {
                    rendered.push_str(" when ");
                    self.expression_line(1, &rendered, condition);
                } else {
                    self.push(1, rendered);
                }
            }
            ClauseKind::Effects { effects } => self.comma_list(
                1,
                format!("{prefix}effects ["),
                effects.iter().map(qname).collect(),
                "]".to_owned(),
            ),
        }
    }
    fn annotations(&mut self, annotations: &[Annotation]) {
        for annotation in annotations {
            self.leading(annotation.span.start, 0);
            if let Some(arg) = &annotation.argument {
                self.push(0, format!("@{}(\"{}\")", annotation.name, arg));
            } else {
                self.push(0, format!("@{}", annotation.name));
            }
            self.inline_for(&annotation.span);
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

    fn requirement_text(&mut self, keyword: &str, text: &RequirementText) {
        self.leading(text.span.start, 1);
        if text.triple {
            self.push(1, format!("{keyword} \"\"\""));
            for line in text.text.split('\n') {
                self.push(1, line.to_owned());
            }
            self.push(1, "\"\"\"".to_owned());
        } else {
            self.push(
                1,
                format!("{keyword} {}", serde_json::to_string(&text.text).unwrap()),
            );
        }
        self.inline_for(&text.span);
    }

    fn generics(&self, generics: &[GenericParam]) -> String {
        if generics.is_empty() {
            return String::new();
        }
        format!(
            "[{}]",
            generics
                .iter()
                .map(|generic| match generic {
                    GenericParam::Type {
                        variance,
                        name,
                        bounds,
                        ..
                    } => {
                        let marker = match variance {
                            Variance::Invariant => "",
                            Variance::Covariant => "+",
                            Variance::Contravariant => "-",
                        };
                        if bounds.is_empty() {
                            format!("{marker}{name}")
                        } else {
                            format!(
                                "{marker}{name}: {}",
                                bounds
                                    .iter()
                                    .map(|bound| self.ty(bound))
                                    .collect::<Vec<_>>()
                                    .join(" + ")
                            )
                        }
                    }
                    GenericParam::Const { name, ty, .. } => {
                        format!("const {name}: {}", ty.name())
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
                        GenericArgKind::Type(ty) => self.ty(ty),
                        GenericArgKind::Const(value) | GenericArgKind::Ambiguous { value, .. } => {
                            self.const_expr(value)
                        }
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
            ConstExpr::Tuple { values, .. } => format!(
                "Tuple({})",
                values
                    .iter()
                    .map(|value| self.const_expr(value))
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
            ConstExpr::Array { values, .. } => format!(
                "Array({})",
                values
                    .iter()
                    .map(|value| self.const_expr(value))
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
            ConstExpr::Buffer { hex, .. } => format!(
                "Buffer({})",
                serde_json::to_string(hex).expect("string serialization")
            ),
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
            ExprKind::Binary { left, op, right } => {
                let (left_parent, right_parent) = if matches!(op, BinaryOp::Implies) {
                    (precedence + 1, precedence)
                } else {
                    (precedence, precedence + 1)
                };
                format!(
                    "{} {} {}",
                    self.expr(left, left_parent),
                    binary_operator(*op),
                    self.expr(right, right_parent)
                )
            }
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
            ExprKind::Intrinsic { kind, arguments } => format!(
                "{}({})",
                intrinsic_name(*kind),
                arguments
                    .iter()
                    .map(|argument| self.expr(argument, 0))
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
            ExprKind::FixturePath { fixture, path } => {
                format!("{fixture}.path({})", serde_json::to_string(path).unwrap())
            }
            ExprKind::FixtureUrl { fixture, path } => {
                format!("{fixture}.url({})", serde_json::to_string(path).unwrap())
            }
            ExprKind::OldStateField { field } => format!("old(self.{})", field.name),
            ExprKind::Construct { path, arguments } => format!(
                "{}({})",
                qname(path),
                arguments
                    .iter()
                    .map(|argument| match &argument.label {
                        Some(label) => {
                            format!("{}: {}", self.expr(label, 0), self.expr(&argument.value, 0))
                        }
                        None => self.expr(&argument.value, 0),
                    })
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
            ExprKind::Match {
                scrutinee,
                pattern,
                condition,
            } => {
                let mut rendered = format!(
                    "{} matches {}",
                    self.expr(scrutinee, 1),
                    self.pattern(pattern)
                );
                if let Some(condition) = condition {
                    rendered.push_str(" => ");
                    rendered.push_str(&self.expr(condition, 0));
                }
                rendered
            }
        };
        if precedence < parent_precedence {
            format!("({rendered})")
        } else {
            rendered
        }
    }

    fn ensures_sugar(&mut self, indent: usize, prefix: &str, kind: &ClauseKind) {
        match kind {
            ClauseKind::EnsuresTable { key, rows } => {
                self.push(indent, format!("{prefix}table {}:", self.expr(key, 0)));
                self.inline_for(&key.span);
                for row in rows {
                    self.leading(row.span.start, indent + 1);
                    self.expression_line(
                        indent + 1,
                        &format!("{} => ", self.pattern(&row.pattern)),
                        &row.value,
                    );
                    self.inline_for(&row.span);
                }
            }
            ClauseKind::EnsuresPreserves {
                result,
                source,
                except,
            } => {
                let mut rendered = format!(
                    "{prefix}preserves {} from {}",
                    self.expr(result, 0),
                    self.expr(source, 0),
                );
                if !except.is_empty() {
                    rendered.push_str(" except ");
                    rendered.push_str(
                        &except
                            .iter()
                            .map(|field| field.name.as_str())
                            .collect::<Vec<_>>()
                            .join(", "),
                    );
                }
                self.push(indent, rendered);
            }
            _ => unreachable!("only ensures sugar is formatted here"),
        }
    }

    fn ensures_expression_line(
        &mut self,
        indent: usize,
        prefix: &str,
        guard: Option<&MatchGuard>,
        condition: &Expr,
    ) {
        if let Some(guard) = guard.filter(|guard| {
            matches!(
                &guard.scrutinee.kind,
                ExprKind::Name(name) if name.segments.len() == 1 && name.segments[0] == "result"
            )
        }) {
            self.expression_line(
                indent,
                &format!("{prefix}{} => ", self.pattern(&guard.pattern)),
                condition,
            );
        } else {
            self.guarded_expression_line(indent, prefix, guard, condition);
        }
    }

    fn guarded_expression_line(
        &mut self,
        indent: usize,
        prefix: &str,
        guard: Option<&MatchGuard>,
        condition: &Expr,
    ) {
        let prefix = guard.map_or_else(
            || prefix.to_owned(),
            |guard| {
                format!(
                    "{}{} matches {} => ",
                    prefix,
                    self.expr(&guard.scrutinee, 0),
                    self.pattern(&guard.pattern),
                )
            },
        );
        self.expression_line(indent, &prefix, condition);
    }

    /// An overlong binary or chained-comparison expression is enclosed in
    /// parentheses on its own line. That parenthesized form is the formatter's
    /// fixed point: reparsing it yields a parenthesized expression, which is
    /// printed unchanged, so the first run already produces the final layout.
    fn expression_line(&mut self, indent: usize, prefix: &str, expression: &Expr) {
        let rendered = self.expr(expression, 0);
        let enclose = indent * 4 + prefix.chars().count() + rendered.chars().count() > 100
            && match &expression.kind {
                ExprKind::Binary { .. } => true,
                ExprKind::Comparison { rest, .. } => !rest.is_empty(),
                _ => false,
            };
        if enclose {
            self.push(indent, format!("{prefix}({rendered})"));
        } else {
            self.push(indent, format!("{prefix}{rendered}"));
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

const fn intrinsic_name(intrinsic: Intrinsic) -> &'static str {
    match intrinsic {
        Intrinsic::StartsWith => "starts_with",
        Intrinsic::EndsWith => "ends_with",
        Intrinsic::Contains => "contains",
        Intrinsic::UniqueBy => "unique_by",
        Intrinsic::DescendingBy => "descending_by",
        Intrinsic::AnyBlankBy => "any_blank_by",
        Intrinsic::UnknownDependencyBy => "unknown_dependency_by",
        Intrinsic::SelfDependencyBy => "self_dependency_by",
        Intrinsic::CyclicBy => "cyclic_by",
        Intrinsic::PermutationBy => "permutation_by",
        Intrinsic::DependencyOrderedBy => "dependency_ordered_by",
    }
}

const fn failure_point(point: crate::ast::ScenarioFailurePointKind) -> &'static str {
    match point {
        crate::ast::ScenarioFailurePointKind::FileOpen => "file.open",
        crate::ast::ScenarioFailurePointKind::FileRead => "file.read",
        crate::ast::ScenarioFailurePointKind::FileWrite => "file.write",
        crate::ast::ScenarioFailurePointKind::FileFlush => "file.flush",
        crate::ast::ScenarioFailurePointKind::FileReplace => "file.replace",
        crate::ast::ScenarioFailurePointKind::HttpConnect => "http.connect",
        crate::ast::ScenarioFailurePointKind::HttpRead => "http.read",
        crate::ast::ScenarioFailurePointKind::ClockRead => "clock.read",
    }
}

const fn failure_error(error: crate::ast::ScenarioFailureErrorKind) -> &'static str {
    match error {
        crate::ast::ScenarioFailureErrorKind::PermissionDenied => "permission_denied",
        crate::ast::ScenarioFailureErrorKind::NotFound => "not_found",
        crate::ast::ScenarioFailureErrorKind::DiskFull => "disk_full",
        crate::ast::ScenarioFailureErrorKind::Timeout => "timeout",
        crate::ast::ScenarioFailureErrorKind::ConnectionReset => "connection_reset",
    }
}

fn clause_group(clause: &Clause) -> u8 {
    match clause.kind {
        ClauseKind::Documentation(_) => 0,
        ClauseKind::Rule { .. } => 1,
        ClauseKind::Requires { .. } => 2,
        ClauseKind::Transitions { .. } => 3,
        ClauseKind::Modifies { .. } => 4,
        ClauseKind::Ensures { .. }
        | ClauseKind::EnsuresTable { .. }
        | ClauseKind::EnsuresPreserves { .. } => 5,
        ClauseKind::ErrorsComplete | ClauseKind::Error { .. } => 6,
        ClauseKind::Effects { .. } => 7,
    }
}

fn rule_clause_group(clause: &RuleClause) -> u8 {
    let action_offset = match clause.action {
        RuleClauseAction::Add => 0,
        RuleClauseAction::Override => 10,
        RuleClauseAction::Delete => 20,
    };
    action_offset
        + match clause.kind {
            ClauseKind::Documentation(_) => 0,
            ClauseKind::Rule { .. } => 1,
            ClauseKind::Requires { .. } => 2,
            ClauseKind::Transitions { .. } => 3,
            ClauseKind::Modifies { .. } => 4,
            ClauseKind::Ensures { .. }
            | ClauseKind::EnsuresTable { .. }
            | ClauseKind::EnsuresPreserves { .. } => 5,
            ClauseKind::ErrorsComplete | ClauseKind::Error { .. } => 6,
            ClauseKind::Effects { .. } => 7,
        }
}

fn expression_precedence(expression: &Expr) -> u8 {
    match &expression.kind {
        ExprKind::Binary { op, .. } => match op {
            BinaryOp::Implies => 0,
            BinaryOp::Or => 1,
            BinaryOp::And => 2,
            BinaryOp::Add | BinaryOp::Subtract => 4,
            BinaryOp::Multiply | BinaryOp::Divide | BinaryOp::Remainder => 5,
        },
        ExprKind::Match { .. } => 0,
        ExprKind::Comparison { .. } => 3,
        ExprKind::Unary { .. } => 6,
        ExprKind::Field { .. } => 7,
        _ => 8,
    }
}

fn contains_construct(expression: &Expr) -> bool {
    match &expression.kind {
        ExprKind::Construct { .. } => true,
        ExprKind::Parenthesized(value)
        | ExprKind::Unary { operand: value, .. }
        | ExprKind::Field { base: value, .. } => contains_construct(value),
        ExprKind::Binary { left, right, .. } => {
            contains_construct(left) || contains_construct(right)
        }
        ExprKind::Comparison { first, rest } => {
            contains_construct(first) || rest.iter().any(|(_, value)| contains_construct(value))
        }
        ExprKind::Intrinsic { arguments, .. } => arguments.iter().any(contains_construct),
        ExprKind::Match {
            scrutinee,
            condition,
            ..
        } => contains_construct(scrutinee) || condition.as_deref().is_some_and(contains_construct),
        ExprKind::Literal(_)
        | ExprKind::Name(_)
        | ExprKind::Unit
        | ExprKind::FixturePath { .. }
        | ExprKind::FixtureUrl { .. }
        | ExprKind::OldStateField { .. } => false,
    }
}

const fn binary_operator(operator: BinaryOp) -> &'static str {
    match operator {
        BinaryOp::Implies => "=>",
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
