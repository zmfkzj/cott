use std::path::{Path, PathBuf};

use cott::compiler::{ProjectDiagnostic, SourceFile, parse_project};
use cott::hir::{HirClauseKind, HirDeclaration, HirType, PrimitiveType, lower};

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
    state: Status

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

fn guarded(value: I32) -> Unit:
    requires value > 0
    ensures value > 1
    error Error.Bad when value == 0
    effects [IO]
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
    assert_eq!(function.contract.effects[0].key, "IO");
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
