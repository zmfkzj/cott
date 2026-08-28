use std::path::{Path, PathBuf};

use cott::compiler::{ProjectDiagnostic, SourceFile, parse_project};
use cott::hir::{
    HirClauseKind, HirDeclaration, HirPatternKind, HirType, ModuleId, PrimitiveType, SymbolId,
    lower, lower_with_effects,
};

fn source(path: &str, text: &str) -> SourceFile {
    SourceFile::new(PathBuf::from(path), text)
}

fn lower_project(sources: impl IntoIterator<Item = SourceFile>) -> cott::hir::HirProject {
    let parsed = parse_project(sources).expect("owned fixture must parse");
    lower(Path::new("src"), parsed).expect("owned fixture must lower")
}

fn lower_diagnostics(sources: impl IntoIterator<Item = SourceFile>) -> Vec<ProjectDiagnostic> {
    let parsed = parse_project(sources).expect("owned fixture must parse");
    lower(Path::new("src"), parsed).expect_err("malformed owned fixture must be rejected")
}
fn diagnostics(sources: impl IntoIterator<Item = SourceFile>) -> Vec<ProjectDiagnostic> {
    let parsed = parse_project(sources).expect("HIR fixture must parse");
    lower(Path::new("src"), parsed).expect_err("HIR fixture must be rejected")
}

fn paths(errors: &[ProjectDiagnostic]) -> Vec<&Path> {
    errors.iter().map(|error| error.path.as_path()).collect()
}

#[test]
fn resolves_valid_multi_module_types_imports_and_declarations() {
    let project = lower_project([
        source(
            "src/types/core.cott",
            r#"module types.core

doc """A user identifier"""
newtype UserId(I32)

alias Count = U32

struct User:
    id: UserId
    status: Status

enum Status:
    Ready
    Failed(code: I32)

const LIMIT: U32 = 3

fn make() -> User
"#,
        ),
        source(
            "src/api/service.cott",
            r#"module api.service
use types.core.{User, UserId, Status}

alias MaybeUser = Option[User]
alias Outcome = Result[User, Status]

struct Envelope:
    user: MaybeUser
    id: UserId

fn run() -> Outcome
"#,
        ),
    ]);

    assert_eq!(project.modules.len(), 2);
    assert_eq!(
        project
            .modules
            .iter()
            .map(|module| module.id.segments.join("."))
            .collect::<Vec<_>>(),
        ["types.core", "api.service"]
    );
}

#[test]
fn rejects_module_path_mismatch() {
    let errors = diagnostics([source("src/actual.cott", "module declared\n")]);
    assert!(!errors.is_empty());
    assert!(
        errors
            .iter()
            .all(|error| error.path == Path::new("src/actual.cott"))
    );
}

#[test]
fn rejects_duplicate_and_prefix_module_ids() {
    let errors = diagnostics([
        source("src/foo.cott", "module foo\n"),
        source("src/other.cott", "module foo\n"),
        source("src/foo/bar.cott", "module foo.bar\n"),
    ]);
    assert!(
        errors
            .iter()
            .any(|error| error.path == Path::new("src/other.cott"))
    );
    assert!(
        errors
            .iter()
            .any(|error| error.path == Path::new("src/foo/bar.cott"))
    );
}

#[test]
fn rejects_import_collisions_and_unknown_symbols() {
    let errors = diagnostics([
        source(
            "src/base.cott",
            "module base\nstruct Thing:\n    value: I32\n",
        ),
        source(
            "src/consumer.cott",
            "module consumer\nuse base.{Thing, Missing}\nalias Thing = Bool\n",
        ),
    ]);
    assert!(
        errors
            .iter()
            .any(|error| error.path == Path::new("src/consumer.cott"))
    );
}

#[test]
fn rejects_invalid_option_and_result_arities() {
    let errors = diagnostics([source(
        "src/bad.cott",
        "module bad\nalias TooMany = Option[Bool, Bool]\nalias TooFew = Result[Bool]\n",
    )]);
    assert!(errors.len() >= 2);
    assert!(
        errors
            .iter()
            .all(|error| error.path == Path::new("src/bad.cott"))
    );
}

#[test]
fn rejects_result_with_non_enum_error_type() {
    let errors = diagnostics([source(
        "src/bad.cott",
        "module bad\nalias Invalid = Result[Bool, Str]\n",
    )]);
    assert!(!errors.is_empty());
    assert!(
        errors
            .iter()
            .all(|error| error.path == Path::new("src/bad.cott"))
    );
}

#[test]
fn rejects_alias_and_newtype_cycles() {
    let errors = diagnostics([source(
        "src/cycles.cott",
        "module cycles\nalias First = Second\nalias Second = First\nnewtype Left(Right)\nnewtype Right(Left)\n",
    )]);
    assert!(errors.len() >= 2);
    assert!(
        errors
            .iter()
            .all(|error| error.path == Path::new("src/cycles.cott"))
    );
}
#[test]
fn reports_malformed_condition_and_reference_in_direct_lowering() {
    let condition_errors = lower_diagnostics([source(
        "src/bad.cott",
        r#"module bad

fn check(value: I32) -> Unit:
    requires value
"#,
    )]);
    assert!(
        condition_errors
            .iter()
            .all(|error| error.path == Path::new("src/bad.cott"))
    );
    assert!(
        condition_errors
            .iter()
            .any(|error| error.diagnostic.message == "contract condition must be boolean")
    );

    let reference_errors = lower_diagnostics([source(
        "src/missing.cott",
        r#"module missing

fn check() -> Unit:
    error Missing.Bad when true
"#,
    )]);
    assert!(reference_errors.iter().any(|error| {
        error
            .diagnostic
            .message
            .contains("unknown type or declaration")
    }));
}

#[test]
fn accepts_numeric_operands_in_owned_contract_conditions() {
    let project = lower_project([source(
        "src/conditions.cott",
        r#"module conditions

fn check(value: I32) -> Unit:
    requires value > 0
    ensures value > 0
"#,
    )]);
    assert_eq!(project.modules.len(), 1);
}

#[test]
fn accepts_generics_and_containers_in_owned_hir() {
    let project = lower_project([source(
        "src/supported.cott",
        r#"module supported

struct Box[T]:
    value: T

alias Values = List[Bool]

fn generic[T](value: T) -> Values
"#,
    )]);
    let module = &project.modules[0];
    assert_eq!(
        module
            .declarations
            .iter()
            .map(|declaration| declaration.id().as_string())
            .collect::<Vec<_>>(),
        ["supported.Box", "supported.Values", "supported.generic"]
    );
    let HirDeclaration::Struct(container) = &module.declarations[0] else {
        panic!("expected generic container");
    };
    assert_eq!(
        container.fields[0].ty,
        HirType::TypeParameter { name: "T".into() }
    );
    let HirDeclaration::Alias(values) = &module.declarations[1] else {
        panic!("expected container alias");
    };
    assert_eq!(
        values.target,
        HirType::List {
            item: Box::new(HirType::Primitive(PrimitiveType::Bool))
        }
    );
}

#[test]
fn accepts_nonempty_contracts_and_effects_in_owned_hir() {
    let project = lower_project([source(
        "src/contracts.cott",
        r#"module contracts

enum Error:
    Bad

fn guarded(value: I32) -> Result[I32, Error]:
    requires value > 0
    ensures value > 1
    error Error.Bad when value == 0
    effects [network]
"#,
    )]);
    let HirDeclaration::Function(function) = &project.modules[0].declarations[1] else {
        panic!("expected guarded function");
    };
    assert_eq!(function.contract.clauses.len(), 3);
    assert!(matches!(
        &function.contract.clauses[0].kind,
        HirClauseKind::Requires { .. }
    ));
    assert!(matches!(
        &function.contract.clauses[1].kind,
        HirClauseKind::Ensures { .. }
    ));
    assert!(matches!(
        &function.contract.clauses[2].kind,
        HirClauseKind::Error { .. }
    ));
    assert_eq!(function.contract.effects[0].key, "network");
}

#[test]
fn accepts_cross_module_impl_trait_union() {
    let project = lower_project([
        source(
            "src/api.cott",
            "module api\n\ntrait Reader:\n    fn read(self) -> I32\n",
        ),
        source(
            "src/service.cott",
            "module service\nuse api.Reader\n\nimpl Store for Reader:\n    fn read(self) -> I32:\n        ensures result == 1\n",
        ),
    ]);
    assert!(matches!(
        project.modules[1].declarations[0],
        HirDeclaration::Impl(_)
    ));
}

#[test]
fn reports_cross_file_diagnostics_in_input_order() {
    let errors = diagnostics([
        source("src/zeta.cott", "module zeta\nalias Z = Missing\n"),
        source("src/alpha.cott", "module alpha\nalias A = Missing\n"),
    ]);
    assert_eq!(
        paths(&errors),
        [Path::new("src/zeta.cott"), Path::new("src/alpha.cott"),]
    );
}

#[test]
fn effects_are_closed_except_for_manifest_registered_keys() {
    let text = "module custom_effect\n\nfn run() -> Unit:\n    effects [engine.compute]\n";
    let errors = lower_diagnostics([source("src/custom_effect.cott", text)]);
    assert!(
        errors
            .iter()
            .any(|error| error.diagnostic.message == "unknown effect `engine.compute`")
    );

    let parsed = parse_project([source("src/custom_effect.cott", text)]).expect("effect source");
    let custom = std::collections::BTreeSet::from(["engine.compute".to_owned()]);
    lower_with_effects(Path::new("src"), parsed, &custom)
        .expect("manifest-registered effect should lower");
}

#[test]
fn accepts_builtin_and_nominal_ensures_patterns_with_canonical_bindings() {
    let project = lower_project([source(
        "src/patterns.cott",
        r#"module patterns

enum Failure:
    Bad

enum Shape:
    Pair(left: I32, right: Bool)
    Empty

fn result(value: I32) -> Result[I32, Failure]:
    ensures Result.Ok(ok) => ok > 0
    ensures Result.Err(failure) => true

fn option(value: I32) -> Option[I32]:
    ensures Option.Some(item) => item > 0
    ensures Option.Nothing => true

fn nominal() -> Shape:
    ensures Shape.Pair(left, right) => left > 0
    ensures Shape.Empty => true
"#,
    )]);

    let function = |name: &str| {
        project.modules[0]
            .declarations
            .iter()
            .find_map(|declaration| match declaration {
                HirDeclaration::Function(value) if value.id.name == name => Some(value),
                _ => None,
            })
            .expect("function should lower")
    };
    let result = function("result");
    let HirClauseKind::Ensures {
        guard: Some(ok), ..
    } = &result.contract.clauses[0].kind
    else {
        panic!("expected Result.Ok pattern");
    };
    let HirPatternKind::Variant {
        symbol: ok_symbol,
        arguments: ok_arguments,
    } = &ok.pattern.kind
    else {
        panic!("expected Result.Ok variant");
    };
    assert_eq!(ok_symbol.as_string(), "Result.Ok");
    assert_eq!(ok_arguments[0].ty, HirType::Primitive(PrimitiveType::I32));
    let HirClauseKind::Ensures {
        guard: Some(err), ..
    } = &result.contract.clauses[1].kind
    else {
        panic!("expected Result.Err pattern");
    };
    let HirPatternKind::Variant {
        symbol: err_symbol,
        arguments: err_arguments,
    } = &err.pattern.kind
    else {
        panic!("expected Result.Err variant");
    };
    assert_eq!(err_symbol.as_string(), "Result.Err");
    assert_eq!(
        err_arguments[0].ty,
        HirType::Named {
            symbol: SymbolId::new(ModuleId::new(vec!["patterns".into()]), "Failure"),
            args: Vec::new(),
        }
    );

    let option = function("option");
    let HirClauseKind::Ensures {
        guard: Some(some), ..
    } = &option.contract.clauses[0].kind
    else {
        panic!("expected Option.Some pattern");
    };
    let HirPatternKind::Variant {
        symbol: some_symbol,
        arguments: some_arguments,
    } = &some.pattern.kind
    else {
        panic!("expected Option.Some variant");
    };
    assert_eq!(some_symbol.as_string(), "Option.Some");
    assert_eq!(some_arguments[0].ty, HirType::Primitive(PrimitiveType::I32));
    let HirClauseKind::Ensures {
        guard: Some(nothing),
        ..
    } = &option.contract.clauses[1].kind
    else {
        panic!("expected Option.Nothing pattern");
    };
    let HirPatternKind::Variant {
        symbol: nothing_symbol,
        arguments: nothing_arguments,
    } = &nothing.pattern.kind
    else {
        panic!("expected Option.Nothing variant");
    };
    assert_eq!(nothing_symbol.as_string(), "Option.Nothing");
    assert!(nothing_arguments.is_empty());

    let nominal = function("nominal");
    let HirClauseKind::Ensures {
        guard: Some(pair), ..
    } = &nominal.contract.clauses[0].kind
    else {
        panic!("expected Shape.Pair pattern");
    };
    let HirPatternKind::Variant {
        symbol: pair_symbol,
        arguments: pair_arguments,
    } = &pair.pattern.kind
    else {
        panic!("expected Shape.Pair variant");
    };
    assert_eq!(pair_symbol.as_string(), "patterns.Shape.Pair");
    assert_eq!(pair_arguments.len(), 2);
    assert_eq!(pair_arguments[0].ty, HirType::Primitive(PrimitiveType::I32));
    assert_eq!(
        pair_arguments[1].ty,
        HirType::Primitive(PrimitiveType::Bool)
    );
}

#[test]
fn rejects_error_clauses_with_invalid_result_or_variant_identity() {
    let errors = lower_diagnostics([source(
        "src/bad_clauses.cott",
        r#"module bad_clauses

enum Failure:
    Bad

enum Other:
    Bad

fn not_result() -> I32:
    error Failure.Bad

fn unrelated() -> Result[I32, Failure]:
    error Other.Bad

fn missing() -> Result[I32, Failure]:
    error Failure.Missing
"#,
    )]);
    assert!(errors.len() >= 3);
    assert!(errors.iter().all(|error| {
        error.path == Path::new("src/bad_clauses.cott")
            && error.diagnostic.span.start < error.diagnostic.span.end
    }));
}
#[test]
fn preserves_cross_module_clause_variant_identity() {
    let project = lower_project([
        source(
            "src/base.cott",
            r#"module base

enum Failure:
    Bad

enum Shape:
    Value(number: I32)
"#,
        ),
        source(
            "src/consumer.cott",
            r#"module consumer
use base.{Failure, Shape}

fn run(value: I32) -> Result[Shape, Failure]:
    ensures Result.Ok(output) => true
    error Failure.Bad

fn shape() -> Shape:
    ensures Shape.Value(number) => number > 0
"#,
        ),
    ]);

    let run = project.modules[1]
        .declarations
        .iter()
        .find_map(|declaration| match declaration {
            HirDeclaration::Function(value) if value.id.name == "run" => Some(value),
            _ => None,
        })
        .expect("run function should lower");
    let HirClauseKind::Error { variant, .. } = &run.contract.clauses[1].kind else {
        panic!("expected error clause");
    };
    assert_eq!(variant.as_string(), "base.Failure.Bad");

    let shape = project.modules[1]
        .declarations
        .iter()
        .find_map(|declaration| match declaration {
            HirDeclaration::Function(value) if value.id.name == "shape" => Some(value),
            _ => None,
        })
        .expect("shape function should lower");
    let HirClauseKind::Ensures {
        guard: Some(guard), ..
    } = &shape.contract.clauses[0].kind
    else {
        panic!("expected nominal pattern");
    };
    let HirPatternKind::Variant { symbol, arguments } = &guard.pattern.kind else {
        panic!("expected nominal variant");
    };
    assert_eq!(symbol.as_string(), "base.Shape.Value");
    assert_eq!(arguments[0].ty, HirType::Primitive(PrimitiveType::I32));
}

#[test]
fn rejects_ensures_patterns_with_wrong_shape_or_payload_arity() {
    let errors = lower_diagnostics([source(
        "src/bad_patterns.cott",
        r#"module bad_patterns

enum Failure:
    Bad

enum Shape:
    Pair(left: I32, right: Bool)
    Empty

fn wrong_builtin() -> Result[I32, Failure]:
    ensures Option.Some(value) => true
    ensures Result.Ok(first, second) => true
    ensures Result.Err() => true

fn wrong_nominal() -> Shape:
    ensures Shape.Pair(value) => true
    ensures Shape.Empty(extra) => true
    ensures Shape.Unknown => true
"#,
    )]);
    assert!(errors.len() >= 6);
    assert!(errors.iter().all(|error| {
        error.path == Path::new("src/bad_patterns.cott")
            && error.diagnostic.span.start < error.diagnostic.span.end
    }));
}

#[test]
fn lowers_rule_inheritance_and_clause_actions() {
    let project = lower_project([source(
        "src/rules.cott",
        r#"module rules

struct Assignment:
    name: Str
    value: Str

enum ParseAssignmentError:
    MissingEquals
    EmptyName

rule BaseAssignmentRule:
    doc """Base assignment rule."""
    ensures Result.Ok(assignment) => assignment.name.len > 0
    error ParseAssignmentError.MissingEquals

rule StrictAssignmentRule(BaseAssignmentRule):
    doc """Strict assignment rule."""
    override ensures Result.Ok(assignment) => assignment.name.len > 1
    delete error ParseAssignmentError.MissingEquals
    ensures Result.Ok(assignment) => assignment.value.len > 0
    error ParseAssignmentError.EmptyName
"#,
    )]);

    assert_eq!(project.modules.len(), 1);
    let module = &project.modules[0];
    assert_eq!(module.declarations.len(), 4);

    let base_rule = match &module.declarations[2] {
        HirDeclaration::Rule(r) => r,
        other => panic!("expected base rule, got {other:?}"),
    };
    assert_eq!(base_rule.id.name, "BaseAssignmentRule");
    assert_eq!(base_rule.base, None);
    assert_eq!(base_rule.contract.clauses.len(), 2);

    let strict_rule = match &module.declarations[3] {
        HirDeclaration::Rule(r) => r,
        other => panic!("expected strict rule, got {other:?}"),
    };
    assert_eq!(strict_rule.id.name, "StrictAssignmentRule");
    assert_eq!(
        strict_rule.base.as_ref().map(|s| s.name.as_str()),
        Some("BaseAssignmentRule")
    );
    assert_eq!(strict_rule.contract.clauses.len(), 3);

    assert!(matches!(
        strict_rule.contract.clauses[0].kind,
        HirClauseKind::Ensures { .. }
    ));
    assert!(matches!(
        strict_rule.contract.clauses[1].kind,
        HirClauseKind::Ensures { .. }
    ));
    let HirClauseKind::Error { variant, .. } = &strict_rule.contract.clauses[2].kind else {
        panic!("expected Error clause at index 2");
    };
    assert_eq!(variant.name, "ParseAssignmentError.EmptyName");
}

#[test]
fn accepts_v02_const_generics_variadic_tuples_and_fixed_containers() {
    let project = lower_project([source(
        "src/v02_types.cott",
        r#"module v02_types

struct Matrix[T, const N: U32]:
    values: Array[T, N]
    bytes: Buffer[N]

alias Triple = Tuple[U8, Str, Bool]
alias ByteMatrix = Matrix[U8, 2]

const PAIR: Tuple[U8, U8] = Tuple(1, 2)
const VALUES: Array[U8, 2] = Array(1, 2)
const BYTES: Buffer[2] = Buffer("00ff")
"#,
    )]);
    assert_eq!(project.modules.len(), 1);
}

#[test]
fn rejects_v02_const_generic_argument_and_fixed_container_errors() {
    let errors = lower_diagnostics([source(
        "src/v02_bad_types.cott",
        r#"module v02_bad_types

struct Matrix[T, const N: U32]:
    values: Array[T, N]

alias ConstInTypeSlot = Matrix[2, U8]
alias TypeInConstSlot = Matrix[U8, Str]
alias NegativeArray = Array[U8, -1]
alias LegacyTuple2 = Tuple2[U8, U8]

const WRONG_ARRAY: Array[U8, 2] = Array(1)
const WRONG_BUFFER: Buffer[2] = Buffer("00")
"#,
    )]);
    assert!(errors.iter().all(|error| {
        error.path == Path::new("src/v02_bad_types.cott")
            && error.diagnostic.span.start < error.diagnostic.span.end
    }));
    for expected in [
        "generic argument kind must match its type parameter",
        "generic argument kind must match its const parameter",
        "const argument must evaluate to an unsigned integer",
        "unknown type or declaration",
    ] {
        assert!(
            errors
                .iter()
                .any(|error| error.diagnostic.message.contains(expected)),
            "missing diagnostic containing `{expected}`: {errors:#?}"
        );
    }
    for container in ["Array", "Buffer"] {
        assert!(errors.iter().any(|error| {
            error.diagnostic.message.contains(container)
                && error.diagnostic.message.contains("length")
        }));
    }
}

#[test]
fn accepts_v02_generalized_match_guards_and_clause_local_bindings() {
    let project = lower_project([source(
        "src/v02_guards.cott",
        r#"module v02_guards

enum Failure:
    Bad

enum State:
    Ready(value: I32)

trait Reader:
    fn read(self) -> I32

impl Controller for Reader:
    state:
        current: State
    invariant self.current matches State.Ready(item) => item > 0
    init(current: State):
        requires true
    fn read(self) -> I32:
        ensures result > 0

fn guarded(value: Option[I32]) -> Result[I32, Failure]:
    requires value matches Option.Some(input) => input > 0
    ensures result matches Result.Ok(output) => output > 0
    error Failure.Bad with value matches Option.Some(error_value) when error_value == 0

fn legacy(value: I32) -> Result[I32, Failure]:
    ensures Result.Ok(item) => item > 0
"#,
    )]);
    assert_eq!(project.modules.len(), 1);
}

#[test]
fn rejects_v02_match_guard_bindings_outside_their_clause() {
    let errors = lower_diagnostics([source(
        "src/v02_guard_scope.cott",
        r#"module v02_guard_scope

fn leaks(value: Option[I32]) -> Unit:
    requires value matches Option.Some(item) => item > 0
    ensures item > 0
"#,
    )]);
    assert!(errors.iter().any(|error| {
        error.path == Path::new("src/v02_guard_scope.cott")
            && error.diagnostic.message.contains("item")
    }));
}

#[test]
fn rejects_result_reference_in_guarded_ensures_condition() {
    let errors = lower_diagnostics([source(
        "src/v02_guarded_result.cott",
        r#"module v02_guarded_result

fn choose(value: Option[U32]) -> U32:
    ensures value matches Option.Some(item) => result == item
"#,
    )]);
    assert!(errors.iter().any(|error| {
        error.path == Path::new("src/v02_guarded_result.cott")
            && error.diagnostic.message.contains("result")
            && error.diagnostic.span.start < error.diagnostic.span.end
    }));
}

#[test]
fn accepts_v02_trait_default_references_and_rejects_invalid_targets() {
    let project = lower_project([source(
        "src/v02_defaults.cott",
        r#"module v02_defaults

fn fallback(receiver: Reader, value: I32) -> I32

trait Reader:
    fn read(self, value: I32) -> I32 = fallback
"#,
    )]);
    assert_eq!(project.modules.len(), 1);

    let errors = lower_diagnostics([source(
        "src/v02_bad_defaults.cott",
        r#"module v02_bad_defaults

fn incompatible(receiver: Reader) -> I32

trait Reader:
    fn missing(self) -> I32 = absent
    fn wrong(self, value: I32) -> I32 = incompatible
"#,
    )]);
    assert!(errors.iter().all(|error| {
        error.path == Path::new("src/v02_bad_defaults.cott")
            && error.diagnostic.span.start < error.diagnostic.span.end
    }));
    assert!(
        errors
            .iter()
            .any(|error| error.diagnostic.message.contains("absent"))
    );
    assert!(
        errors
            .iter()
            .any(|error| error.diagnostic.message.contains("exactly match"))
    );
}

#[test]
fn accepts_v03_associated_type_assignment_and_projection_substitution() {
    let project = lower_project([source(
        "src/v03_associated.cott",
        r#"module v03_associated

trait Stream:
    type Item
    fn next(self) -> Stream.Item

impl NumberStream for Stream:
    type Item = I32
    fn next(self) -> I32:
        ensures true
"#,
    )]);
    assert_eq!(project.modules.len(), 1);
}

#[test]
fn rejects_v03_associated_type_duplicates_unknown_ambiguous_and_cyclic_uses() {
    let errors = diagnostics([source(
        "src/v03_associated_bad.cott",
        r#"module v03_associated_bad

trait Single:
    type Item

trait Left:
    type Item

trait Right:
    type Item

impl Duplicate for Single:
    type Item = I32
    type Item = I32
    fn unused(self) -> Unit:
        ensures true

impl Unknown for Single:
    type Missing = I32
    fn unused(self) -> Unit:
        ensures true

impl Ambiguous for Left + Right:
    type Item = I32
    fn unused(self) -> Unit:
        ensures true

impl Cyclic for Single:
    type Item = Single.Item
    fn unused(self) -> Unit:
        ensures true

fn unknown_projection[T: Single](value: T.Missing) -> Unit
fn ambiguous_projection[T: Left + Right](value: T.Item) -> Unit
"#,
    )]);
    assert!(errors.iter().all(|error| {
        error.path == Path::new("src/v03_associated_bad.cott")
            && error.diagnostic.span.start < error.diagnostic.span.end
    }));
    for expected in [
        "duplicate associated type assignment `Item`",
        "unknown associated type `Missing`",
        "associated type assignment `Item` is ambiguous",
        "associated type assignment must not be cyclic",
        "associated projection `T.Missing` is not declared by its trait bounds",
        "associated projection `T.Item` is ambiguous",
    ] {
        assert!(
            errors
                .iter()
                .any(|error| error.diagnostic.message.contains(expected)),
            "missing diagnostic containing `{expected}`: {errors:#?}"
        );
    }
}

#[test]
fn accepts_v03_resource_graph_and_multiple_resource_field_transitions() {
    let project = lower_project([source(
        "src/v03_resource.cott",
        r#"module v03_resource

trait Controller:
    fn close(self) -> Unit

resource Door:
    initial Open
    state Open
    state Closed
    terminal Closed
    transition Open -> Closed

impl DoorController for Controller:
    state:
        primary: Door
        backup: Door
        audit: I32 = 0
    init(primary: Door, backup: Door):
        requires true
    fn close(self) -> Unit:
        requires true
        transitions self.primary: Door.Open -> Door.Closed, self.backup: Door.Open -> Door.Closed
        modifies self.audit
        ensures true
"#,
    )]);
    assert_eq!(project.modules.len(), 1);
}

#[test]
fn rejects_v03_invalid_resource_graphs_and_transitions() {
    let errors = diagnostics([source(
        "src/v03_resource_bad.cott",
        r#"module v03_resource_bad

trait Controller:
    fn wrong_owner(self) -> Unit
    fn wrong_field(self) -> Unit
    fn missing_edge(self) -> Unit
    fn overlap(self) -> Unit
    fn without_transition(self) -> Unit

resource Door:
    initial Open
    state Open
    state Closed
    terminal Closed
    transition Open -> Closed

resource Other:
    initial Open
    state Open
    state Closed
    terminal Closed
    transition Open -> Closed

resource Broken:
    initial Open
    state Open
    state Closed
    terminal Closed
    transition Open -> Missing

resource Cyclic:
    initial Open
    state Open
    state Closed
    terminal Closed
    transition Open -> Open

impl InvalidController for Controller:
    state:
        primary: Door
        count: I32 = 0
    init(primary: Door):
        requires true
    fn wrong_owner(self) -> Unit:
        requires true
        transitions self.primary: Other.Open -> Other.Closed
        modifies self.count
        ensures true
    fn wrong_field(self) -> Unit:
        requires true
        transitions self.count: Door.Open -> Door.Closed
        modifies self.count
        ensures true
    fn missing_edge(self) -> Unit:
        requires true
        transitions self.primary: Door.Closed -> Door.Open
        modifies self.count
        ensures true
    fn overlap(self) -> Unit:
        requires true
        transitions self.primary: Door.Open -> Door.Closed
        modifies self.primary
        ensures true
    fn without_transition(self) -> Unit:
        requires true
        modifies self.primary
        ensures true
"#,
    )]);
    assert!(errors.iter().all(|error| {
        error.path == Path::new("src/v03_resource_bad.cott")
            && error.diagnostic.span.start < error.diagnostic.span.end
    }));
    for expected in [
        "resource edge state must be declared",
        "resource state must be reachable from its initial state",
        "transition states must belong to the field resource",
        "transitions field must be a resource state field",
        "transition must match a declared resource edge",
        "transitions field cannot overlap modifies",
        "resource state fields must use transitions, not modifies",
    ] {
        assert!(
            errors
                .iter()
                .any(|error| error.diagnostic.message.contains(expected)),
            "missing diagnostic containing `{expected}`: {errors:#?}"
        );
    }
}

#[test]
fn accepts_v04_async_trait_impl_methods_with_exact_async_default() {
    let project = lower_project([source(
        "src/v04_async.cott",
        r#"module v04_async

async fn fallback(receiver: Reader, value: I32) -> I32

trait Reader:
    async fn read(self, value: I32) -> I32 = fallback
    async fn items(self) -> AsyncIterator[I32]
    async fn conversation(self) -> AsyncGenerator[I32, Unit]

impl BufferedReader for Reader:
    async fn read(self, value: I32) -> I32:
        requires true
        ensures true
    async fn items(self) -> AsyncIterator[I32]:
        ensures true
    async fn conversation(self) -> AsyncGenerator[I32, Unit]:
        ensures true

alias Items = AsyncIterator[I32]
alias Conversation = AsyncGenerator[I32, Unit]
"#,
    )]);
    assert_eq!(project.modules.len(), 1);
}

#[test]
fn rejects_v04_default_and_impl_callable_kind_mismatches() {
    let errors = diagnostics([source(
        "src/v04_callable_kind_bad.cott",
        r#"module v04_callable_kind_bad

fn sync_default(receiver: AsyncReader, value: I32) -> I32
async fn async_default(receiver: SyncReader, value: I32) -> I32
async fn wrong_signature(receiver: SignatureReader) -> I32

trait AsyncReader:
    async fn read(self, value: I32) -> I32 = sync_default

trait SyncReader:
    fn read(self, value: I32) -> I32 = async_default

trait SignatureReader:
    async fn read(self, value: I32) -> I32 = wrong_signature

trait AsyncWriter:
    async fn write(self, value: I32) -> I32

impl WrongAsyncReader for AsyncReader:
    fn read(self, value: I32) -> I32:
        ensures true

impl ExactAsyncReader for SignatureReader:
    async fn read(self, value: I32) -> I32:
        ensures true

impl Duplex for SyncReader + AsyncWriter:
    fn read(self, value: I32) -> I32:
        ensures true
    async fn write(self, value: I32) -> I32:
        ensures true
"#,
    )]);
    assert!(errors.iter().all(|error| {
        error.path == Path::new("src/v04_callable_kind_bad.cott")
            && error.diagnostic.span.start < error.diagnostic.span.end
    }));
    for expected in [
        "trait default must reference an async free function",
        "trait default must reference a sync free function",
        "trait default must take the trait receiver first and exactly match the method signature",
        "impl method signature and callable kind must exactly match its trait method",
        "impl effective methods must all have the same callable kind",
    ] {
        assert!(
            errors
                .iter()
                .any(|error| error.diagnostic.message.contains(expected)),
            "missing diagnostic containing `{expected}`: {errors:#?}"
        );
    }
}

#[test]
fn rejects_v04_protocol_arity_and_legacy_async_generator_shortcuts() {
    let errors = diagnostics([source(
        "src/v04_protocol_bad.cott",
        r#"module v04_protocol_bad

alias MissingIteratorItem = AsyncIterator
alias ExtraIteratorItem = AsyncIterator[I32, U32]
alias MissingGeneratorSend = AsyncGenerator[I32, Unit]
alias ExtraGeneratorArgument = AsyncGenerator[I32, Unit, U32]

trait NativeProtocol:
    async fn iterator(self) -> Iterator[I32]
    async fn generator(self) -> Generator[I32, Unit, I32]

impl NativeProtocolImpl for NativeProtocol:
    async fn iterator(self) -> Iterator[I32]:
        ensures true
    async fn generator(self) -> Generator[I32, Unit, I32]:
        ensures true
"#,
    )]);
    assert!(
        errors.len() >= 6,
        "expected protocol arity and legacy async-return diagnostics: {errors:#?}"
    );
    assert!(errors.iter().all(|error| {
        error.path == Path::new("src/v04_protocol_bad.cott")
            && error.diagnostic.span.start < error.diagnostic.span.end
    }));
    assert!(errors.iter().any(|error| {
        error.diagnostic.message.contains("AsyncIterator") && error.diagnostic.message.contains("1")
    }));
    assert!(errors.iter().any(|error| {
        error.diagnostic.message.contains("AsyncGenerator")
            && error.diagnostic.message.contains("2")
    }));
    assert!(errors.iter().any(|error| {
        error.diagnostic.message.contains("Iterator")
            && error.diagnostic.message.contains("Generator")
            && error.diagnostic.message.contains("Never")
    }));
}

#[test]
fn lowers_v05_order_independent_inheritance_and_coalesced_diamonds() {
    lower_project([source(
        "src/v05/inheritance.cott",
        r#"module v05.inheritance

trait Child[T] for Left[T] + Right[T]:
    fn child(self) -> T

trait Left[T] for Root[T]:
    fn left(self) -> T

trait Right[T] for Root[T]:
    fn right(self) -> T

trait Root[T]:
    fn value(self) -> T
"#,
    )]);
}

#[test]
fn rejects_v05_inheritance_cycles_and_conflicting_diamond_members() {
    let errors = diagnostics([source(
        "src/v05/inheritance_bad.cott",
        r#"module v05.inheritance_bad

trait First for Second:
    fn first(self) -> I32

trait Second for First:
    fn second(self) -> I32

trait Left:
    fn read(self) -> I32

trait Right:
    fn read(self) -> Bool

trait Conflict for Left + Right:
    fn own(self) -> Unit
"#,
    )]);
    assert!(errors.iter().all(|error| {
        error.path == Path::new("src/v05/inheritance_bad.cott")
            && error.diagnostic.span.start < error.diagnostic.span.end
    }));
    assert!(
        errors.len() >= 2,
        "expected cycle and diamond-conflict diagnostics: {errors:#?}"
    );
}

#[test]
fn lowers_v05_specializations_below_explicit_implementations() {
    lower_project([source(
        "src/v05/specialization.cott",
        r#"module v05.specialization

struct Concrete:
    id: I32

fn fallback(receiver: Concrete, value: I32) -> I32

trait Reader:
    fn read(self, value: I32) -> I32

specialize Concrete for Reader:
    read = v05.specialization.fallback

impl Concrete for Reader:
    fn read(self, value: I32) -> I32:
        ensures true
"#,
    )]);
}

#[test]
fn rejects_v05_duplicate_and_kind_mismatched_specializations() {
    let duplicate_errors = diagnostics([source(
        "src/v05/specialization_duplicate.cott",
        r#"module v05.specialization_duplicate

struct Concrete:
    id: I32

fn fallback(receiver: Concrete) -> I32

trait Reader:
    fn read(self) -> I32

specialize Concrete for Reader:
    read = v05.specialization_duplicate.fallback

specialize Concrete for Reader:
    read = v05.specialization_duplicate.fallback
"#,
    )]);
    assert!(duplicate_errors.iter().all(|error| {
        error.path == Path::new("src/v05/specialization_duplicate.cott")
            && error.diagnostic.span.start < error.diagnostic.span.end
    }));

    let kind_errors = diagnostics([source(
        "src/v05/specialization_kind.cott",
        r#"module v05.specialization_kind

struct Concrete:
    id: I32

async fn fallback(receiver: Concrete) -> I32

trait Reader:
    fn read(self) -> I32

specialize Concrete for Reader:
    read = v05.specialization_kind.fallback
"#,
    )]);
    assert!(kind_errors.iter().all(|error| {
        error.path == Path::new("src/v05/specialization_kind.cott")
            && error.diagnostic.span.start < error.diagnostic.span.end
    }));
}

#[test]
fn lowers_v05_valid_variance_and_rejects_invalid_polarity() {
    lower_project([source(
        "src/v05/variance.cott",
        r#"module v05.variance

struct Producer[+T]:
    value: T

enum Choice[+T]:
    Value(value: T)

trait Source[+T]:
    fn get(self) -> T

trait Sink[-T]:
    fn put(self, value: T) -> Unit
"#,
    )]);

    let errors = diagnostics([source(
        "src/v05/variance_bad.cott",
        r#"module v05.variance_bad

struct Invariant[T]:
    value: T

trait InvalidOutput[-T]:
    fn get(self) -> T

trait InvalidInput[+T]:
    fn put(self, value: T) -> Unit

trait HiddenByInvariantContainer[+T]:
    fn get(self) -> Invariant[T]
"#,
    )]);
    assert!(errors.iter().all(|error| {
        error.path == Path::new("src/v05/variance_bad.cott")
            && error.diagnostic.span.start < error.diagnostic.span.end
    }));
    assert!(
        errors.len() >= 3,
        "expected polarity and invariant-container diagnostics: {errors:#?}"
    );
}

#[test]
fn lowers_v05_nominal_dyn_and_rejects_invalid_dyn_targets() {
    lower_project([source(
        "src/v05/dyn.cott",
        r#"module v05.dyn

struct Concrete:
    id: I32

trait Reader:
    fn read(self) -> I32

impl Concrete for Reader:
    fn read(self) -> I32:
        ensures true

alias Object = Dyn[Reader]
"#,
    )]);

    let errors = diagnostics([source(
        "src/v05/dyn_bad.cott",
        r#"module v05.dyn_bad

struct NotATrait:
    id: I32

trait Reader:
    fn read(self) -> I32

alias Missing = Dyn
alias Extra = Dyn[Reader, I32]
alias Structural = Dyn[NotATrait]
"#,
    )]);
    assert!(errors.iter().all(|error| {
        error.path == Path::new("src/v05/dyn_bad.cott")
            && error.diagnostic.span.start < error.diagnostic.span.end
    }));
    assert!(
        errors.len() >= 3,
        "expected Dyn arity and non-trait target diagnostics: {errors:#?}"
    );
}

#[test]
fn accepts_v06_guarded_self_mutual_generic_and_enum_recursion() {
    lower_project([source(
        "src/recursive.cott",
        r#"module recursive

struct Chain[T]:
    value: T
    next: Option[Chain[T]]

struct Left:
    right: Option[Right]

struct Right:
    left: Result[Left, Stop]

enum Stop:
    Done

struct Nested:
    next: Option[Result[Nested, Stop]]

enum Tree:
    Empty
    Branch(left: Tree, right: Tree)
"#,
    )]);
}

#[test]
fn accepts_v06_zero_length_array_recursion() {
    lower_project([source(
        "src/recursive_arrays.cott",
        r#"module recursive_arrays

struct ArrayLoop:
    children: Array[ArrayLoop, 0]
"#,
    )]);
}

#[test]
fn accepts_v06_zero_length_array_const_expressions() {
    lower_project([source(
        "src/recursive_array_consts.cott",
        r#"module recursive_array_consts

const ZERO: U32 = 0

struct Local:
    children: Array[Local, ZERO]

struct Arithmetic:
    children: Array[Arithmetic, (1 - 1)]
"#,
    )]);

    lower_project([
        source("src/sizes.cott", "module sizes\nconst ZERO: U32 = 0\n"),
        source(
            "src/recursive_qualified.cott",
            r#"module recursive_qualified
use sizes.ZERO

struct Qualified:
    children: Array[Qualified, sizes.ZERO]
"#,
        ),
    ]);
}

#[test]
fn accepts_v06_composite_bound_outside_an_unrelated_generic_cycle() {
    lower_project([source(
        "src/recursive_bounds.cott",
        r#"module recursive_bounds

trait Owner[T: A + B, U: CycleA[U]]:
    fn owner(self) -> Unit
trait A:
    fn a(self) -> Unit
trait B:
    fn b(self) -> Unit
trait CycleA[V: CycleB[V]]:
    fn cycle_a(self) -> Unit
trait CycleB[V: Owner[Any, V]]:
    fn cycle_b(self) -> Unit
"#,
    )]);
}

#[test]
fn rejects_v06_nonempty_array_recursion() {
    let errors = diagnostics([source(
        "src/recursive_array_bad.cott",
        r#"module recursive_array_bad

struct Loop:
    children: Array[Loop, 1]
"#,
    )]);

    assert!(
        errors
            .iter()
            .any(|error| error.diagnostic.message.contains("unproductive type cycle")),
        "expected nonempty array recursion to be rejected: {errors:#?}"
    );
}

#[test]
fn rejects_v06_recursion_through_iterators_and_generators() {
    for ty in [
        "Iterator[Loop]",
        "AsyncIterator[Loop]",
        "Generator[Loop, Unknown, Unit]",
        "AsyncGenerator[Loop, Unknown]",
    ] {
        let source_text =
            format!("module recursive_stream_bad\n\nstruct Loop:\n    stream: {ty}\n");
        let errors = diagnostics([source("src/recursive_stream_bad.cott", &source_text)]);
        assert!(
            errors
                .iter()
                .any(|error| error.diagnostic.message.contains("unproductive type cycle")),
            "expected recursion through {ty} to be rejected: {errors:#?}"
        );
    }
}

#[test]
fn rejects_v06_unproductive_struct_cycles() {
    let errors = diagnostics([source(
        "src/recursive_bad.cott",
        r#"module recursive_bad

struct Direct:
    next: Direct

struct First:
    second: Second

struct Second:
    first: First
"#,
    )]);

    assert!(
        errors
            .iter()
            .any(|error| error.diagnostic.message.contains("unproductive type cycle")),
        "expected unproductive recursion diagnostics: {errors:#?}"
    );
    assert!(
        errors
            .iter()
            .all(|error| error.path == Path::new("src/recursive_bad.cott"))
    );
}

#[test]
fn rejects_v06_result_recursion_without_a_finite_error_branch() {
    let errors = diagnostics([source(
        "src/recursive_result_bad.cott",
        r#"module recursive_result_bad

enum Loop:
    Again(next: Result[Loop, Loop])
"#,
    )]);

    assert!(
        errors
            .iter()
            .any(|error| error.diagnostic.message.contains("unproductive type cycle")),
        "expected Result recursion without a finite error branch to be rejected: {errors:#?}"
    );
}

#[test]
fn rejects_v06_result_recursion_with_never_error_alternatives() {
    for (path, source_text) in [
        (
            "src/recursive_never.cott",
            r#"module recursive_never

enum Loop:
    Again(next: Result[Loop, Never])
"#,
        ),
        (
            "src/recursive_alias_never.cott",
            r#"module recursive_alias_never

alias NoValue = Never

enum Loop:
    Again(next: Result[Loop, NoValue])
"#,
        ),
        (
            "src/recursive_newtype_never.cott",
            r#"module recursive_newtype_never

newtype NoValue(Never)

enum Loop:
    Again(next: Result[Loop, NoValue])
"#,
        ),
    ] {
        let errors = diagnostics([source(path, source_text)]);
        assert!(
            errors
                .iter()
                .any(|error| error.diagnostic.message.contains("unproductive type cycle")),
            "expected a Never error alternative to leave the recursion unproductive: {errors:#?}"
        );
    }
}
#[test]
fn rejects_v06_cross_module_nominal_recursion() {
    let errors = diagnostics([
        source(
            "src/left.cott",
            r#"module left
use right.Right

struct Left:
    right: Option[Right]
"#,
        ),
        source(
            "src/right.cott",
            r#"module right
use left.Left

struct Right:
    left: Option[Left]
"#,
        ),
    ]);

    assert!(
        errors.iter().any(|error| {
            error
                .diagnostic
                .message
                .contains("type cycle cannot cross module boundaries")
        }),
        "expected cross-module recursion diagnostic: {errors:#?}"
    );
}
