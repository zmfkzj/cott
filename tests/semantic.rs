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
fn rejects_alias_and_named_type_cycles() {
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
        pattern: Some(ok), ..
    } = &result.contract.clauses[0].kind
    else {
        panic!("expected Result.Ok pattern");
    };
    let HirPatternKind::Variant {
        symbol: ok_symbol,
        arguments: ok_arguments,
    } = &ok.kind
    else {
        panic!("expected Result.Ok variant");
    };
    assert_eq!(ok_symbol.as_string(), "Result.Ok");
    assert_eq!(ok_arguments[0].ty, HirType::Primitive(PrimitiveType::I32));
    let HirClauseKind::Ensures {
        pattern: Some(err), ..
    } = &result.contract.clauses[1].kind
    else {
        panic!("expected Result.Err pattern");
    };
    let HirPatternKind::Variant {
        symbol: err_symbol,
        arguments: err_arguments,
    } = &err.kind
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
        pattern: Some(some),
        ..
    } = &option.contract.clauses[0].kind
    else {
        panic!("expected Option.Some pattern");
    };
    let HirPatternKind::Variant {
        symbol: some_symbol,
        arguments: some_arguments,
    } = &some.kind
    else {
        panic!("expected Option.Some variant");
    };
    assert_eq!(some_symbol.as_string(), "Option.Some");
    assert_eq!(some_arguments[0].ty, HirType::Primitive(PrimitiveType::I32));
    let HirClauseKind::Ensures {
        pattern: Some(nothing),
        ..
    } = &option.contract.clauses[1].kind
    else {
        panic!("expected Option.Nothing pattern");
    };
    let HirPatternKind::Variant {
        symbol: nothing_symbol,
        arguments: nothing_arguments,
    } = &nothing.kind
    else {
        panic!("expected Option.Nothing variant");
    };
    assert_eq!(nothing_symbol.as_string(), "Option.Nothing");
    assert!(nothing_arguments.is_empty());

    let nominal = function("nominal");
    let HirClauseKind::Ensures {
        pattern: Some(pair),
        ..
    } = &nominal.contract.clauses[0].kind
    else {
        panic!("expected Shape.Pair pattern");
    };
    let HirPatternKind::Variant {
        symbol: pair_symbol,
        arguments: pair_arguments,
    } = &pair.kind
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
    ensures Result.Ok(result) => true
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
        pattern: Some(pattern),
        ..
    } = &shape.contract.clauses[0].kind
    else {
        panic!("expected nominal pattern");
    };
    let HirPatternKind::Variant { symbol, arguments } = &pattern.kind else {
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
