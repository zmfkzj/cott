use cott::ast::{
    BinaryOp, ClauseKind, Declaration, ExprKind, GenericArgKind, GenericParam, PatternKind,
    RuleClauseAction, UnaryOp,
};
use cott::parser::parse;

fn assert_rejected(source: &str) {
    let result = parse(source);
    assert!(
        result.is_err(),
        "source unexpectedly parsed successfully:\n{source}"
    );
    assert!(!result.unwrap_err().is_empty());
}

#[test]
fn parses_declarations_imports_docs_clauses_patterns_and_precedence() {
    let source = r#"module demo.core
use std.io
use std.collections.{Map, Set}

doc """A generic box"""
struct Box[T: Display + Clone, U]:
    value: T
    opaque: Opaque["tag"]

enum Maybe[T]:
    None
    Some(value: T)

trait Show[T]:
    fn render(self, value: T) -> String

fn evaluate[T](x: T, y: T) -> Result[Maybe[T], Error]:
    doc """Contract documentation"""
    requires x + y * 2 > 3 and not ready or done
    ensures Result.Ok(Some(value)) => value > 0
    error Error.Bad when x == y
    effects [IO, Log.Write]
"#;

    let file = parse(source).expect("valid declaration source should parse");
    assert_eq!(file.span.start, 0);
    assert_eq!(file.span.end, source.len());
    assert_eq!(file.module.path.segments, ["demo", "core"]);

    assert_eq!(file.uses.len(), 2);
    assert_eq!(file.uses[0].path.segments, ["std", "io"]);
    assert_eq!(file.uses[0].names, None);
    assert_eq!(file.uses[1].path.segments, ["std", "collections"]);
    let imported_names = file.uses[1].names.as_deref().expect("grouped import names");
    assert_eq!(imported_names, ["Map", "Set"]);

    assert_eq!(file.declarations.len(), 4);
    let structure = match &file.declarations[0] {
        Declaration::Struct(value) => value,
        other => panic!("expected struct first, got {other:?}"),
    };
    assert_eq!(structure.name, "Box");
    assert!(matches!(
        &structure.generics[..],
        [
            GenericParam::Type {
                name: first,
                bounds,
                ..
            },
            GenericParam::Type { name: second, .. },
        ] if first == "T"
            && second == "U"
            && matches!(&bounds[..], [first_bound, second_bound]
                if first_bound.path.segments == ["Display"]
                    && second_bound.path.segments == ["Clone"])
    ));
    assert_eq!(
        structure
            .fields
            .iter()
            .map(|field| field.name.as_str())
            .collect::<Vec<_>>(),
        ["value", "opaque"]
    );
    assert_eq!(
        structure.doc.as_ref().map(|doc| doc.text.as_str()),
        Some("A generic box")
    );
    let opaque = &structure.fields[1].ty;
    assert_eq!(opaque.path.segments, ["Opaque"]);
    assert_eq!(opaque.arguments.len(), 1);
    assert!(matches!(
        &opaque.arguments[0].kind,
        GenericArgKind::Const(_)
    ));

    let enumeration = match &file.declarations[1] {
        Declaration::Enum(value) => value,
        other => panic!("expected enum second, got {other:?}"),
    };
    assert_eq!(enumeration.name, "Maybe");
    assert!(matches!(
        &enumeration.generics[..],
        [GenericParam::Type { name, .. }] if name == "T"
    ));
    assert_eq!(
        enumeration
            .variants
            .iter()
            .map(|variant| variant.name.as_str())
            .collect::<Vec<_>>(),
        ["None", "Some"]
    );
    assert_eq!(enumeration.variants[1].parameters[0].name, "value");

    let trait_decl = match &file.declarations[2] {
        Declaration::Trait(value) => value,
        other => panic!("expected trait third, got {other:?}"),
    };
    assert_eq!(trait_decl.name, "Show");
    assert!(matches!(
        &trait_decl.generics[..],
        [GenericParam::Type { name, .. }] if name == "T"
    ));
    assert_eq!(trait_decl.methods.len(), 1);
    assert_eq!(trait_decl.methods[0].name, "render");
    assert_eq!(trait_decl.methods[0].parameters[0].name, "value");

    let function = match &file.declarations[3] {
        Declaration::Function(value) => value,
        other => panic!("expected function last, got {other:?}"),
    };
    assert_eq!(function.name, "evaluate");
    assert!(matches!(
        &function.generics[..],
        [GenericParam::Type { name, .. }] if name == "T"
    ));
    assert_eq!(
        function
            .parameters
            .iter()
            .map(|param| param.name.as_str())
            .collect::<Vec<_>>(),
        ["x", "y"]
    );
    assert_eq!(function.return_type.path.segments, ["Result"]);
    let clauses = match &function.body {
        cott::ast::FunctionBody::Clauses { clauses, .. } => clauses,
        other => panic!("expected function clauses, got {other:?}"),
    };
    assert_eq!(clauses.len(), 5);
    assert!(
        matches!(&clauses[0].kind, ClauseKind::Documentation(doc) if doc.text == "Contract documentation")
    );
    assert!(
        matches!(&clauses[3].kind, ClauseKind::Error { error, when: Some(_), .. } if error.segments == ["Error", "Bad"])
    );
    if let ClauseKind::Effects { effects } = &clauses[4].kind {
        assert_eq!(effects.len(), 2);
        assert_eq!(effects[0].segments, ["IO"]);
        assert_eq!(effects[1].segments, ["Log", "Write"]);
    } else {
        panic!("expected effects clause, got {:?}", clauses[4].kind);
    }

    let requires = match &clauses[1].kind {
        ClauseKind::Requires { condition, .. } => condition,
        other => panic!("expected requires clause, got {other:?}"),
    };
    let ExprKind::Binary {
        left: or_left,
        op: BinaryOp::Or,
        right: or_right,
    } = &requires.kind
    else {
        panic!("expected top-level or expression, got {:?}", requires.kind);
    };
    assert!(matches!(&or_right.kind, ExprKind::Name(_)));
    let ExprKind::Binary {
        left: and_left,
        op: BinaryOp::And,
        right: and_right,
    } = &or_left.kind
    else {
        panic!("expected and below or, got {:?}", or_left.kind);
    };
    assert!(matches!(
        &and_right.kind,
        ExprKind::Unary {
            op: UnaryOp::Not,
            ..
        }
    ));
    let ExprKind::Comparison { first, .. } = &and_left.kind else {
        panic!(
            "expected comparison in requires expression, got {:?}",
            and_left.kind
        );
    };
    let ExprKind::Binary {
        left: add_left,
        op: BinaryOp::Add,
        right: add_right,
    } = &first.kind
    else {
        panic!("expected addition below comparison, got {:?}", first.kind);
    };
    assert!(matches!(&add_left.kind, ExprKind::Name(_)));
    let ExprKind::Binary {
        op: BinaryOp::Multiply,
        ..
    } = &add_right.kind
    else {
        panic!(
            "expected multiplication to bind tighter than addition, got {:?}",
            add_right.kind
        );
    };

    let ensures_guard = match &clauses[2].kind {
        ClauseKind::Ensures {
            guard: Some(guard), ..
        } => guard,
        other => panic!("expected ensures match guard, got {other:?}"),
    };
    let PatternKind::Variant { path, arguments } = &ensures_guard.pattern.kind else {
        panic!(
            "expected outer variant pattern, got {:?}",
            ensures_guard.pattern.kind
        );
    };
    assert_eq!(path.segments, ["Result", "Ok"]);
    let PatternKind::Variant {
        path,
        arguments: nested,
    } = &arguments[0].kind
    else {
        panic!(
            "expected nested variant pattern, got {:?}",
            arguments[0].kind
        );
    };
    assert_eq!(path.segments, ["Some"]);
    assert!(matches!(&nested[0].kind, PatternKind::Binding(name) if name == "value"));
}

#[test]
fn parses_grouped_use_before_declaration() {
    let source =
        "module demo.grouped\nuse alpha.beta.{Gamma, Delta}\nstruct Item:\n    value: Gamma\n";

    let file = parse(source).expect("grouped use should not corrupt later declarations");
    assert_eq!(file.uses.len(), 1);
    assert_eq!(file.uses[0].path.segments, ["alpha", "beta"]);
    assert_eq!(
        file.uses[0].names.as_deref().expect("grouped names"),
        ["Gamma", "Delta"]
    );
    assert!(matches!(&file.declarations[0], Declaration::Struct(value) if value.name == "Item"));
}

#[test]
fn rejects_malformed_grouped_use() {
    let valid = parse("module demo.grouped\nuse alpha.beta.{Gamma, }\n")
        .expect("a grouped use may have a trailing comma");
    assert_eq!(
        valid.uses[0].names.as_deref().expect("grouped names"),
        ["Gamma"]
    );

    assert_rejected(
        "module demo.grouped\nuse alpha.beta.{Gamma,, Delta}\nstruct Item:\n    value: Gamma\n",
    );
    assert_rejected(
        "module demo.grouped\nuse alpha.beta.{Gamma, Delta\nstruct Item:\n    value: Gamma\n",
    );
}

#[test]
fn rejects_top_level_doc_before_function() {
    assert_rejected("module demo.bad\n\ndoc \"\"\"orphan for function\"\"\"\nfn run() -> Unit\n");
}

#[test]
fn rejects_non_contiguous_use_block() {
    assert_rejected(
        "module demo.bad\nuse first.module\nstruct Item:\n    value: U32\nuse second.module\n",
    );
}

#[test]
fn rejects_invalid_function_clause_order() {
    assert_rejected("module demo.bad\nfn run() -> Unit:\n    effects []\n    requires true\n");
}

#[test]
fn rejects_malformed_or_unterminated_indentation() {
    assert_rejected("module demo.bad\nstruct Broken:\n    first: U32\n  second: U32\n");
    assert_rejected("module demo.bad\nstruct Broken:\n");
}

#[test]
fn rejects_invalid_expression_syntax() {
    assert_rejected("module demo.bad\nfn run() -> Unit:\n    requires true +\n");
}

#[test]
fn parses_compact_qualified_nested_contract() {
    let source = "module demo.progress\nfn check(value: Input.Value) -> Output.Result:\n    ensures Result.Ok(Some(value)) => value > 0\n";

    let file = parse(source).expect("qualified nested contract should parse");
    assert_eq!(file.declarations.len(), 1);
    let function = match &file.declarations[0] {
        Declaration::Function(value) => value,
        other => panic!("expected function declaration, got {other:?}"),
    };
    assert_eq!(function.return_type.path.segments, ["Output", "Result"]);
    let clauses = match &function.body {
        cott::ast::FunctionBody::Clauses { clauses, .. } => clauses,
        other => panic!("expected function clauses, got {other:?}"),
    };
    let ClauseKind::Ensures {
        guard: Some(guard), ..
    } = &clauses[0].kind
    else {
        panic!("expected ensures match guard, got {:?}", clauses[0].kind);
    };
    let PatternKind::Variant { path, arguments } = &guard.pattern.kind else {
        panic!(
            "expected qualified variant pattern, got {:?}",
            guard.pattern.kind
        );
    };
    assert_eq!(path.segments, ["Result", "Ok"]);
    let PatternKind::Variant {
        path,
        arguments: nested,
    } = &arguments[0].kind
    else {
        panic!(
            "expected nested variant pattern, got {:?}",
            arguments[0].kind
        );
    };
    assert_eq!(path.segments, ["Some"]);
    assert!(matches!(&nested[0].kind, PatternKind::Binding(name) if name == "value"));
}

#[test]
fn rejects_unknown_clause_at_eof() {
    assert_rejected(
        "module demo.progress\nfn check(value: Input.Value) -> Output.Result:\n    unexpected",
    );
}

#[test]
fn parses_rule_declarations_inheritance_and_clause_actions() {
    let source = r#"module demo.rules

rule BaseAssignmentRule:
    doc """Base assignment rule."""
    requires line.len > 0
    ensures Result.Ok(assignment) => assignment.name.len > 0
    error ParseAssignmentError.MissingEquals

rule StrictAssignmentRule(BaseAssignmentRule):
    doc """Strict assignment rule."""
    override ensures Result.Ok(assignment) => assignment.name.len > 1
    delete error ParseAssignmentError.MissingEquals
    ensures Result.Ok(assignment) => assignment.value.len > 0
    error ParseAssignmentError.EmptyName
"#;

    let file = parse(source).expect("rules should parse");
    assert_eq!(file.declarations.len(), 2);

    let base = match &file.declarations[0] {
        Declaration::Rule(value) => value,
        other => panic!("expected rule declaration, got {other:?}"),
    };
    assert_eq!(base.name, "BaseAssignmentRule");
    assert_eq!(base.base, None);
    assert_eq!(base.clauses.len(), 4);
    assert_eq!(base.clauses[0].action, RuleClauseAction::Add);
    assert!(matches!(base.clauses[0].kind, ClauseKind::Documentation(_)));
    assert_eq!(base.clauses[1].action, RuleClauseAction::Add);
    assert!(matches!(base.clauses[1].kind, ClauseKind::Requires { .. }));
    assert_eq!(base.clauses[2].action, RuleClauseAction::Add);
    assert!(matches!(base.clauses[2].kind, ClauseKind::Ensures { .. }));
    assert_eq!(base.clauses[3].action, RuleClauseAction::Add);
    assert!(matches!(base.clauses[3].kind, ClauseKind::Error { .. }));

    let child = match &file.declarations[1] {
        Declaration::Rule(value) => value,
        other => panic!("expected rule declaration, got {other:?}"),
    };
    assert_eq!(child.name, "StrictAssignmentRule");
    assert_eq!(
        child.base.as_ref().map(|b| b
            .path
            .segments
            .iter()
            .map(|s| s.as_str())
            .collect::<Vec<_>>()),
        Some(vec!["BaseAssignmentRule"])
    );
    assert_eq!(child.clauses.len(), 5);
    assert_eq!(child.clauses[0].action, RuleClauseAction::Add);
    assert_eq!(child.clauses[1].action, RuleClauseAction::Override);
    assert!(matches!(child.clauses[1].kind, ClauseKind::Ensures { .. }));
    assert_eq!(child.clauses[2].action, RuleClauseAction::Delete);
    assert!(matches!(child.clauses[2].kind, ClauseKind::Error { .. }));
    assert_eq!(child.clauses[3].action, RuleClauseAction::Add);
    assert!(matches!(child.clauses[3].kind, ClauseKind::Ensures { .. }));
    assert_eq!(child.clauses[4].action, RuleClauseAction::Add);
    assert!(matches!(child.clauses[4].kind, ClauseKind::Error { .. }));
}

#[test]
fn parses_annotations_and_docstring_references() {
    let source = r#"module demo.annotated

@entity
@memo("User entity definition")
struct User:
    id: Str

@pure
@tag("lookup")
fn find_user(id: Str) -> Option[User]:
    doc """
    Looks up a {User} by identifier.
    """
    ensures Option.Some(u) => u.id.len > 0
"#;

    let file = parse(source).expect("annotated declarations should parse");
    assert_eq!(file.declarations.len(), 2);

    let structure = match &file.declarations[0] {
        Declaration::Struct(v) => v,
        other => panic!("expected struct, got {other:?}"),
    };
    assert_eq!(structure.annotations.len(), 2);
    assert_eq!(structure.annotations[0].name, "entity");
    assert_eq!(structure.annotations[0].argument, None);
    assert_eq!(structure.annotations[1].name, "memo");
    assert_eq!(
        structure.annotations[1].argument.as_deref(),
        Some("User entity definition")
    );

    let function = match &file.declarations[1] {
        Declaration::Function(v) => v,
        other => panic!("expected function, got {other:?}"),
    };
    assert_eq!(function.annotations.len(), 2);
    assert_eq!(function.annotations[0].name, "pure");
    assert_eq!(function.annotations[1].name, "tag");
    assert_eq!(function.annotations[1].argument.as_deref(), Some("lookup"));
}

#[test]
fn parses_stateful_impls_with_contracts_and_old_state() {
    let source = r#"module demo.impls

trait Reader:
    fn read(self) -> I32

trait Writer:
    fn write(self, value: I32) -> Unit

@entity
impl Counter for Reader + Writer:
    state:
        count: I32
        label: Str = "counter"
    invariant self.count >= 0
    invariant self.label.len > 0
    init(count: I32):
        doc """Initializes the counter."""
        requires count >= 0
        ensures self.count == count
    fn read(self) -> I32:
        doc """Reads the count."""
        requires self.count >= 0
        ensures old(self.count) == self.count
    fn write(self, value: I32) -> Unit:
        requires value >= 0
        modifies self.count, self.label
        ensures old(self.count) <= self.count
        error CounterError.BadValue when value == 13
        effects [Log.Write]
"#;

    let file = parse(source).expect("stateful impl should parse");
    let implementation = match &file.declarations[2] {
        Declaration::Impl(value) => value,
        other => panic!("expected impl, got {other:?}"),
    };
    assert_eq!(implementation.name, "Counter");
    assert_eq!(implementation.annotations.len(), 1);
    assert_eq!(implementation.annotations[0].name, "entity");
    assert_eq!(implementation.traits.len(), 2);
    assert_eq!(implementation.traits[0].path.segments, ["Reader"]);
    assert_eq!(implementation.traits[1].path.segments, ["Writer"]);
    assert_eq!(
        implementation
            .state
            .iter()
            .map(|field| field.name.as_str())
            .collect::<Vec<_>>(),
        ["count", "label"]
    );
    assert!(implementation.state[0].default.is_none());
    assert!(implementation.state[1].default.is_some());
    assert_eq!(implementation.invariants.len(), 2);

    let initializer = implementation
        .initializer
        .as_ref()
        .expect("required state field has explicit init");
    assert_eq!(initializer.parameters.len(), 1);
    assert_eq!(initializer.parameters[0].name, "count");
    assert!(matches!(
        initializer.clauses.as_slice(),
        [
            cott::ast::Clause {
                kind: ClauseKind::Documentation(_),
                ..
            },
            cott::ast::Clause {
                kind: ClauseKind::Requires { guard: None, .. },
                ..
            },
            cott::ast::Clause {
                kind: ClauseKind::Ensures { guard: None, .. },
                ..
            },
        ]
    ));

    assert_eq!(
        implementation
            .methods
            .iter()
            .map(|method| method.name.as_str())
            .collect::<Vec<_>>(),
        ["read", "write"]
    );
    let write = &implementation.methods[1];
    assert!(write.self_span.start < write.self_span.end);
    assert_eq!(write.parameters[0].name, "value");
    assert!(matches!(
        &write.clauses[1].kind,
        ClauseKind::Modifies { fields }
            if fields.iter().map(|field| field.name.as_str()).collect::<Vec<_>>()
                == ["count", "label"]
    ));
    let condition = match &write.clauses[2].kind {
        ClauseKind::Ensures { condition, .. } => condition,
        other => panic!("expected ensures after modifies, got {other:?}"),
    };
    assert!(matches!(
        &condition.kind,
        ExprKind::Comparison { first, .. }
            if matches!(
                &first.kind,
                ExprKind::OldStateField { field } if field.name == "count"
            )
    ));
}

#[test]
fn parses_impls_with_implicit_initializers() {
    let source = r#"module demo.impls

trait Ready:
    fn ready(self) -> Bool

impl Empty for Ready:
    fn ready(self) -> Bool:
        ensures true

trait Versioned:
    fn version(self) -> I32

impl Defaults for Versioned:
    state:
        version: I32 = 1
    fn version(self) -> I32:
        ensures result >= 0
"#;

    let file = parse(source).expect("impl initializer forms should parse");
    let empty = match &file.declarations[1] {
        Declaration::Impl(value) => value,
        other => panic!("expected empty impl, got {other:?}"),
    };
    assert!(empty.state.is_empty());
    assert!(empty.initializer.is_none());

    let defaults = match &file.declarations[3] {
        Declaration::Impl(value) => value,
        other => panic!("expected default-state impl, got {other:?}"),
    };
    assert_eq!(defaults.state.len(), 1);
    assert!(defaults.state[0].default.is_some());
    assert!(defaults.initializer.is_none());
}

#[test]
fn rejects_malformed_impl_members_clauses_and_eof_recovery() {
    for source in [
        "module demo.bad\nimpl Counter:\n    fn read(self) -> I32:\n        ensures true\n",
        "module demo.bad\nimpl Counter for Reader:\n",
        "module demo.bad\nimpl Counter for Reader:\n    state:\n    fn read(self) -> I32:\n        ensures true\n",
        "module demo.bad\nimpl Counter for Reader:\n    init():\n    fn read(self) -> I32:\n        ensures true\n",
        "module demo.bad\nimpl Counter for Reader:\n    state:\n        count: I32\n",
        "module demo.bad\nimpl Counter for Reader:\n    state:\n        count: I32\n    state:\n        label: Str\n    fn read(self) -> I32:\n        ensures true\n",
        "module demo.bad\nimpl Counter for Reader:\n    init():\n        ensures true\n    init():\n        ensures true\n    fn read(self) -> I32:\n        ensures true\n",
        "module demo.bad\nimpl Counter for Reader:\n    invariant true\n    state:\n        count: I32\n    fn read(self) -> I32:\n        ensures true\n",
        "module demo.bad\nimpl Counter for Reader:\n    fn read(self) -> I32:\n        ensures true\n    init():\n        ensures true\n",
        "module demo.bad\nimpl Counter for Reader:\n    fn read(self) -> I32:\n        modifies self.count\n        requires true\n        ensures true\n",
        "module demo.bad\nimpl Counter for Reader:\n    fn read(self) -> I32:\n        requires true\n        ensures true\n        modifies self.count\n",
        "module demo.bad\nimpl Counter for Reader:\n    fn read(self) -> I32:\n        modifies self.count\n        modifies self.label\n        ensures true\n",
        "module demo.bad\nimpl Counter for Reader:\n    fn read(self) -> I32:\n        modifies count\n        ensures true\n",
        "module demo.bad\nimpl Counter for Reader:\n    fn read(self) -> I32:\n        ensures old(self.count + 1) == 0\n",
        "module demo.bad\nimpl Counter for Reader:\n    fn read(self) -> I32:\n        requires old(self.count) == 0\n",
        "module demo.bad\nimpl Counter for Reader:\n    fn read(self) -> I32:\n        ensures true\n  fn write(self) -> I32:\n        ensures true\n",
        "module demo.bad\nimpl Counter for Reader:\n    fn read(self) -> I32:\n        ensures old(self.count) ==\n",
    ] {
        assert_rejected(source);
    }
}

#[test]
fn parses_expression_first_agent_types_and_external_declarations() {
    let source = r#"module agents.types

doc """Remote agent SDK type"""
external type Remote

alias Protected = Opaque["alias"]
newtype Handle(Opaque["newtype"])

struct Record:
    value: Opaque["field"]
    stream: Iterator[Any]

enum Response:
    Value(value: Opaque["variant"])

trait Service:
    fn stream(self, input: List[Opaque["container"]]) -> Generator[Opaque["yield"], Unknown, Any]

fn inspect(value: Map[Str, Opaque["map-value"]]) -> Unknown
"#;

    let file = parse(source).expect("expression-first agent types should parse");
    assert_eq!(file.declarations.len(), 7);

    let Declaration::ExternalType(external) = &file.declarations[0] else {
        panic!("expected external type declaration");
    };
    assert_eq!(external.name, "Remote");
    assert_eq!(
        external.doc.as_ref().map(|doc| doc.text.as_str()),
        Some("Remote agent SDK type")
    );

    let Declaration::Alias(alias) = &file.declarations[1] else {
        panic!("expected opaque alias");
    };
    assert_eq!(alias.target.path.segments, ["Opaque"]);
    assert!(matches!(
        &alias.target.arguments[0].kind,
        GenericArgKind::Const(_)
    ));

    let Declaration::Newtype(newtype) = &file.declarations[2] else {
        panic!("expected opaque newtype");
    };
    assert_eq!(newtype.underlying.path.segments, ["Opaque"]);
    assert!(matches!(
        &newtype.underlying.arguments[0].kind,
        GenericArgKind::Const(_)
    ));

    let Declaration::Struct(record) = &file.declarations[3] else {
        panic!("expected record struct");
    };
    assert_eq!(record.fields[0].ty.path.segments, ["Opaque"]);
    assert_eq!(record.fields[1].ty.path.segments, ["Iterator"]);
    assert!(matches!(
        &record.fields[1].ty.arguments[0].kind,
        GenericArgKind::Ambiguous { ty, .. } if ty.path.segments == ["Any"]
    ));

    let Declaration::Enum(response) = &file.declarations[4] else {
        panic!("expected response enum");
    };
    assert_eq!(
        response.variants[0].parameters[0].ty.path.segments,
        ["Opaque"]
    );

    let Declaration::Trait(service) = &file.declarations[5] else {
        panic!("expected service trait");
    };
    let method = &service.methods[0];
    assert_eq!(method.parameters[0].ty.path.segments, ["List"]);
    assert!(matches!(
        &method.parameters[0].ty.arguments[0].kind,
        GenericArgKind::Type(ty)
            if ty.path.segments == ["Opaque"]
                && matches!(&ty.arguments[0].kind, GenericArgKind::Const(_))
    ));
    assert_eq!(method.return_type.path.segments, ["Generator"]);
    assert_eq!(method.return_type.arguments.len(), 3);
    assert!(matches!(
        &method.return_type.arguments[0].kind,
        GenericArgKind::Type(ty) if ty.path.segments == ["Opaque"]
    ));
    assert!(matches!(
        &method.return_type.arguments[1].kind,
        GenericArgKind::Ambiguous { ty, .. } if ty.path.segments == ["Unknown"]
    ));
    assert!(matches!(
        &method.return_type.arguments[2].kind,
        GenericArgKind::Ambiguous { ty, .. } if ty.path.segments == ["Any"]
    ));

    let Declaration::Function(inspect) = &file.declarations[6] else {
        panic!("expected inspect function");
    };
    assert_eq!(inspect.parameters[0].ty.path.segments, ["Map"]);
    assert_eq!(inspect.parameters[0].ty.arguments.len(), 2);
    assert!(matches!(
        &inspect.parameters[0].ty.arguments[1].kind,
        GenericArgKind::Type(ty)
            if ty.path.segments == ["Opaque"]
                && matches!(&ty.arguments[0].kind, GenericArgKind::Const(_))
    ));
    assert_eq!(inspect.return_type.path.segments, ["Unknown"]);
}

#[test]
fn rejects_legacy_external_type_syntax() {
    for source in [
        "module agents.bad\nexternal python type Remote = \"vendor.client:Remote\"\n",
        "module agents.bad\nexternal rust type Remote = \"vendor.client:Remote\"\n",
        "module agents.bad\nexternal python Remote = \"vendor.client:Remote\"\n",
        "module agents.bad\nexternal type Remote = \"vendor.client:Remote\"\n",
        "module agents.bad\nexternal type Remote = vendor.client:Remote\n",
        "module agents.bad\nexternal type Remote \"vendor.client:Remote\"\n",
    ] {
        assert_rejected(source);
    }
}

#[test]
fn parses_factory_type_arguments() {
    let file = parse(
        "module factory\n\nstruct Handle:\n    maker: Factory[Concrete]\n\nfn create(factory: Factory[Concrete]) -> Factory[Concrete]\n",
    )
    .expect("Factory types should parse");
    let Declaration::Struct(handle) = &file.declarations[0] else {
        panic!("expected handle struct");
    };
    assert_eq!(handle.fields[0].ty.path.segments, ["Factory"]);
    assert!(matches!(
        &handle.fields[0].ty.arguments[..],
        [cott::ast::GenericArg {
            kind: GenericArgKind::Ambiguous { ty: instance, .. },
            ..
        }] if instance.path.segments == ["Concrete"]
    ));
    let Declaration::Function(create) = &file.declarations[1] else {
        panic!("expected create function");
    };
    assert_eq!(create.parameters[0].ty.path.segments, ["Factory"]);
    assert_eq!(create.return_type.path.segments, ["Factory"]);
}

#[test]
fn parses_v02_const_generics_variadic_tuples_and_fixed_containers() {
    let source = r#"module v02.types

struct Matrix[T, const N: U32]:
    values: Array[T, N]
    bytes: Buffer[N]

fn collect[T](items: Tuple[T, Str]) -> Tuple[T, I32, Bool]

const PAIR: Tuple[U8, U8] = Tuple(1, 2)
const VALUES: Array[U8, 2] = Array(1, 2)
const BYTES: Buffer[2] = Buffer("00ff")
"#;
    parse(source).expect("v0.2 generic and fixed-container surface should parse");
}

#[test]
fn parses_named_qualified_forwarded_and_arithmetic_const_arguments() {
    let file = parse(
        r#"module foo.consumer

const THREE: U32 = 3

struct Page[T, const N: U32]:
    items: Array[T, N]

struct Batch[const N: U32]:
    page: Page[U8, N]

struct Holder:
    literal: Page[U8, 1 + 2]
    named: Page[U8, THREE]
    qualified: Page[U8, foo.sizes.THREE]
    arithmetic: Page[U8, THREE + 1]
"#,
    )
    .expect("const generic arguments should parse as expressions");
    let Declaration::Struct(batch) = &file.declarations[2] else {
        panic!("expected Batch declaration");
    };
    assert!(matches!(
        &batch.fields[0].ty.arguments[1].kind,
        GenericArgKind::Ambiguous {
            value: cott::ast::ConstExpr::Expression(expr),
            ..
        } if matches!(&expr.kind, ExprKind::Name(path) if path.segments == ["N"])
    ));
    let Declaration::Struct(holder) = &file.declarations[3] else {
        panic!("expected Holder declaration");
    };
    assert!(matches!(
        &holder.fields[0].ty.arguments[1].kind,
        GenericArgKind::Const(cott::ast::ConstExpr::Expression(expr))
            if matches!(&expr.kind, ExprKind::Binary { op: BinaryOp::Add, .. })
    ));
    assert!(matches!(
        &holder.fields[1].ty.arguments[1].kind,
        GenericArgKind::Ambiguous {
            value: cott::ast::ConstExpr::Expression(expr),
            ..
        } if matches!(&expr.kind, ExprKind::Name(path) if path.segments == ["THREE"])
    ));
    assert!(matches!(
        &holder.fields[2].ty.arguments[1].kind,
        GenericArgKind::Ambiguous {
            value: cott::ast::ConstExpr::Expression(expr),
            ..
        } if matches!(&expr.kind, ExprKind::Name(path) if path.segments == ["foo", "sizes", "THREE"])
    ));
    assert!(matches!(
        &holder.fields[3].ty.arguments[1].kind,
        GenericArgKind::Const(cott::ast::ConstExpr::Expression(expr))
            if matches!(&expr.kind, ExprKind::Binary { op: BinaryOp::Add, .. })
    ));
}

#[test]
fn rejects_malformed_v02_const_generic_and_container_syntax() {
    for source in [
        "module v02.bad\nstruct Missing[const N]:\n    value: U8\n",
        "module v02.bad\nstruct Signed[const N: I32]:\n    value: U8\n",
        "module v02.bad\nstruct MissingColon[const N U32]:\n    value: U8\n",
        "module v02.bad\nstruct Unclosed[T, const N: U32:\n    value: T\n",
        "module v02.bad\nfn broken[T const N: U32](value: T) -> T\n",
        "module v02.bad\nconst VALUES: Array[U8, 2] = Array(1, 2\n",
        "module v02.bad\nconst BYTES: Buffer[2] = Buffer(\"00ff\"\n",
        "module v02.bad\nfn empty_tuple() -> Tuple[]\n",
        "module v02.bad\nconst BYTES: Buffer[2] = Buffer(\"0F\")\n",
    ] {
        assert_rejected(source);
    }
}

#[test]
fn parses_v02_generalized_match_guards_and_legacy_ensures_pattern() {
    let source = r#"module v02.guards

enum Failure:
    Bad

enum State:
    Ready(value: I32)

trait Reader:
    fn read(self) -> I32 = defaults.read

impl Controller for Reader:
    state:
        current: State = State.Ready(1)
    invariant self.current matches State.Ready(item) => item > 0
    fn read(self) -> I32:
        ensures result > 0

fn guarded(value: Option[I32]) -> Result[I32, Failure]:
    requires value matches Option.Some(input) => input > 0
    ensures result matches Result.Ok(output) => output > 0
    error Failure.Bad with value matches Option.Some(error_value) when error_value == 0

fn legacy(value: I32) -> Result[I32, Failure]:
    ensures Result.Ok(item) => item > 0
"#;
    parse(source).expect("all v0.2 match-guard spellings should parse");
}

#[test]
fn rejects_non_declaration_trait_defaults() {
    for source in [
        "module v02.bad\ntrait Reader:\n    fn read(self) -> I32 = defaults.read()\n",
        "module v02.bad\ntrait Reader:\n    fn read(self) -> I32 = 1\n",
        "module v02.bad\nfn read() -> I32 = fallback\n",
        "module v02.bad\ntrait Reader:\n    fn read(self) -> I32\nimpl Controller for Reader:\n    fn read(self) -> I32 = fallback\n",
        "module v02.bad\ntrait Reader:\n    fn read(self) -> I32 = defaults.read:\n",
    ] {
        assert_rejected(source);
    }
}

#[test]
fn parses_v03_explicit_async_associated_types_projections_and_resource_transitions() {
    parse(
        r#"module v03.surface

trait Stream[T]:
    type Item: Display + Clone
    fn next(self) -> T.Item

trait Controller:
    fn close(self) -> Unit

resource Door:
    initial Open
    state Open
    state Closed
    terminal Closed
    transition Open -> Closed

impl DoorController for Controller:
    type Item = I32
    state:
        primary: Door
        backup: Door
        audit: I32
    fn close(self) -> Unit:
        requires true
        transitions self.primary: Door.Open -> Door.Closed, self.backup: Door.Open -> Door.Closed
        modifies self.audit
        ensures true

async fn fetch() -> I32:
    effects [IO]

fn inspect[T](value: T.Item) -> T.Item

fn completes() -> Never
"#,
    )
    .expect("v0.3 public syntax should parse");
}

#[test]
fn rejects_v03_forbidden_async_returns_associated_ordering_and_resource_forms() {
    for source in [
        "module v03.bad\nasync trait Stream:\n    fn next(self) -> I32\n",
        "module v03.bad\ntrait Stream:\n    async fn next(self) -> I32\n",
        "module v03.bad\ntrait Stream:\n    fn next(self) -> I32\n    type Item\n",
        "module v03.bad\ntrait Stream:\n    type Item\n    fn next(self) -> I32\nimpl Reader for Stream:\n    state:\n        value: I32 = 0\n    type Item = I32\n    fn next(self) -> I32:\n        ensures true\n",
        "module v03.bad\nimpl Reader for Stream:\n    async fn next(self) -> I32:\n        ensures true\n",
        "module v03.bad\nasync fn stream() -> Iterator[I32]\n",
        "module v03.bad\nasync fn generate() -> Generator[I32, Unit, Unit]\n",
        "module v03.bad\nasync fn never() -> Never\n",
        "module v03.bad\ntrait Stream:\n    type Item = I32\n",
        "module v03.bad\nresource Door:\n    state Open\n    terminal Closed\n    transition Open -> Closed\n",
        "module v03.bad\nresource Door:\n    initial Open\n    initial Open\n    state Open\n    state Closed\n    terminal Closed\n    transition Open -> Closed\n",
        "module v03.bad\nresource Door:\n    initial Open\n    state Open\n    state Closed\n    terminal Closed\n    transition Open -> Closed\n    state Reopened\n",
        "module v03.bad\nresource Door:\n    initial Open\n    state Open\n    state Closed\n    terminal Closed\n    transition Open Closed\n",
        "module v03.bad\nresource Door:\n    initial Open\n    state state\n    terminal Closed\n    transition Open -> Closed\n",
        "module v03.bad\nresource Door:\n    initial Open\n    state resource\n    terminal Closed\n    transition Open -> Closed\n",
        "module v03.bad\nresource Door:\n    initial Open\n    state initial\n    terminal Closed\n    transition Open -> Closed\n",
        "module v03.bad\nresource Door:\n    initial Open\n    state terminal\n    terminal Closed\n    transition Open -> Closed\n",
        "module v03.bad\nresource Door:\n    initial Open\n    state transition\n    terminal Closed\n    transition Open -> Closed\n",
        "module v03.bad\nresource Door:\n    initial Open\n    state transitions\n    terminal Closed\n    transition Open -> Closed\n",
        "module v03.bad\nresource Door:\n    initial Open\n    state async\n    terminal Closed\n    transition Open -> Closed\n",
    ] {
        assert_rejected(source);
    }
}
