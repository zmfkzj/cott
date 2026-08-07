use std::path::{Path, PathBuf};

use cott::compiler::{ProjectDiagnostic, SourceFile, parse_project};
use cott::semantic::analyze_project;

fn source(path: &str, text: &str) -> SourceFile {
    SourceFile::new(PathBuf::from(path), text)
}

fn analyze(sources: impl IntoIterator<Item = SourceFile>) -> cott::semantic::SemanticProject {
    let parsed = parse_project(sources).expect("semantic fixture must parse");
    analyze_project(Path::new("src"), parsed).expect("semantic fixture must validate")
}

fn diagnostics(sources: impl IntoIterator<Item = SourceFile>) -> Vec<ProjectDiagnostic> {
    let parsed = parse_project(sources).expect("semantic fixture must parse");
    analyze_project(Path::new("src"), parsed).expect_err("semantic fixture must be rejected")
}

fn paths(errors: &[ProjectDiagnostic]) -> Vec<&Path> {
    errors.iter().map(|error| error.path.as_path()).collect()
}

#[test]
fn resolves_valid_multi_module_types_imports_and_declarations() {
    let project = analyze([
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
fn rejects_traits_generics_and_containers() {
    let errors = diagnostics([source(
        "src/unsupported.cott",
        r#"module unsupported

trait Nope:
    fn run(self) -> Unit

struct Box[T]:
    value: T

alias Values = List[Bool]

fn generic[T]() -> Unit
"#,
    )]);
    assert!(!errors.is_empty());
    assert!(
        errors
            .iter()
            .all(|error| error.path == Path::new("src/unsupported.cott"))
    );
}

#[test]
fn rejects_nonempty_contracts_and_effects() {
    let errors = diagnostics([source(
        "src/contracts.cott",
        "module contracts\nfn guarded() -> Unit:\n    requires true\n    effects [IO]\n",
    )]);
    assert!(!errors.is_empty());
    assert!(
        errors
            .iter()
            .all(|error| error.path == Path::new("src/contracts.cott"))
    );
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
