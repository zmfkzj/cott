use std::path::{Path, PathBuf};

use cott::compiler::{SourceFile, parse_project};
use cott::hir::lower;
use cott::ir::{CanonicalIr, render};
use cott::python::artifact_plan::{
    PythonArtifactPlan, PythonArtifactPlanError, PythonCallableKind,
};

fn source(path: &str, text: &str) -> SourceFile {
    SourceFile::new(PathBuf::from(path), text)
}

fn fixture_ir() -> CanonicalIr {
    let parsed = parse_project([
        source(
            "src/z/mod.cott",
            "module z.mod\n\nfn hidden() -> Unit\nfn run() -> Unit\n",
        ),
        source("src/a/mod.cott", "module a.mod\n\nfn check() -> Unit\n"),
    ])
    .expect("artifact fixture must parse");
    let project = lower(Path::new("src"), parsed).expect("artifact fixture must lower");
    render(&project).expect("artifact fixture must render")
}

fn impl_fixture_ir() -> CanonicalIr {
    let parsed = parse_project([
        source(
            "src/z/mod.cott",
            r#"module z.mod

trait Z:
    fn duplicate(self) -> Unit

impl ZState for Z:
    fn duplicate(self) -> Unit:
        ensures true

fn run() -> Unit
"#,
        ),
        source(
            "src/a/mod.cott",
            r#"module a.mod

fn free() -> Unit

trait A:
    fn duplicate(self) -> Unit
    fn first(self, value: I32) -> I32

impl AState for A:
    fn duplicate(self) -> Unit:
        ensures true
    fn first(self, value: I32) -> I32:
        ensures result == value
"#,
        ),
    ])
    .expect("impl artifact fixture must parse");
    let project = lower(Path::new("src"), parsed).expect("impl artifact fixture must lower");
    render(&project).expect("impl artifact fixture must render")
}

#[test]
fn enumerates_modules_and_functions_deterministically_from_canonical_bytes() {
    let ir = fixture_ir();
    let first = PythonArtifactPlan::from_ir(&ir).expect("canonical bytes must load");
    let mut reversed = ir.clone();
    reversed.modules.reverse();
    let second = PythonArtifactPlan::from_ir(&reversed).expect("canonical bytes must load");

    assert_eq!(first, second);
    assert_eq!(
        first
            .modules()
            .iter()
            .map(|module| module.module.as_str())
            .collect::<Vec<_>>(),
        ["a.mod", "z.mod"]
    );
    assert_eq!(
        first
            .callables()
            .iter()
            .map(|callable| callable.cott_symbol.as_str())
            .collect::<Vec<_>>(),
        ["a.mod.check", "z.mod.hidden", "z.mod.run"]
    );
    let free = first
        .callables()
        .into_iter()
        .find(|callable| callable.cott_symbol == "a.mod.check")
        .expect("free function must remain callable");
    assert_eq!(free.name, "check");
    assert_eq!(free.kind, PythonCallableKind::Function);
    assert!(free.owner.is_none());
}

#[test]
fn public_projection_keeps_only_public_canonical_declarations() {
    let mut ir = fixture_ir();
    let module = ir
        .modules
        .iter_mut()
        .find(|module| module.module.as_string() == "z.mod")
        .expect("fixture module must exist");
    let mut value: serde_json::Value = serde_json::from_slice(&module.bytes).unwrap();
    value["declarations"][0]["public"] = serde_json::Value::Bool(false);
    module.bytes = serde_json::to_vec(&value).unwrap();
    module.bytes.push(b'\n');

    let plan = PythonArtifactPlan::from_ir(&ir).expect("mutated canonical bytes remain valid");
    assert_eq!(
        plan.public_callables()
            .iter()
            .map(|callable| callable.cott_symbol.as_str())
            .collect::<Vec<_>>(),
        ["a.mod.check", "z.mod.run"]
    );
}

#[test]
fn enumerates_impl_methods_by_module_declaration_and_method_source_order() {
    let ir = impl_fixture_ir();
    let first = PythonArtifactPlan::from_ir(&ir).expect("canonical bytes must load");
    let mut reversed = ir.clone();
    reversed.modules.reverse();
    let second = PythonArtifactPlan::from_ir(&reversed).expect("canonical bytes must load");

    assert_eq!(first, second);
    assert_eq!(
        first
            .callables()
            .iter()
            .map(|callable| callable.cott_symbol.as_str())
            .collect::<Vec<_>>(),
        [
            "a.mod.free",
            "a.mod.AState.duplicate",
            "a.mod.AState.first",
            "z.mod.ZState.duplicate",
            "z.mod.run",
        ]
    );
    assert_eq!(
        first
            .public_callables()
            .iter()
            .map(|callable| callable.cott_symbol.as_str())
            .collect::<Vec<_>>(),
        [
            "a.mod.free",
            "a.mod.AState.duplicate",
            "a.mod.AState.first",
            "z.mod.ZState.duplicate",
            "z.mod.run",
        ]
    );

    let mut private_free = ir;
    let module = private_free
        .modules
        .iter_mut()
        .find(|module| module.module.as_string() == "a.mod")
        .expect("impl fixture module must exist");
    let mut value: serde_json::Value = serde_json::from_slice(&module.bytes).unwrap();
    value["declarations"]
        .as_array_mut()
        .expect("declarations must be an array")
        .iter_mut()
        .find(|declaration| declaration["name"] == "a.mod.free")
        .expect("free declaration must exist")["public"] = serde_json::Value::Bool(false);
    module.bytes = serde_json::to_vec(&value).unwrap();
    module.bytes.push(b'\n');
    let plan =
        PythonArtifactPlan::from_ir(&private_free).expect("mutated canonical bytes must load");
    assert_eq!(
        plan.public_callables()
            .iter()
            .map(|callable| callable.cott_symbol.as_str())
            .collect::<Vec<_>>(),
        [
            "a.mod.AState.duplicate",
            "a.mod.AState.first",
            "z.mod.ZState.duplicate",
            "z.mod.run",
        ]
    );
}

#[test]
fn impl_methods_keep_their_owner_and_concrete_identity() {
    let plan = PythonArtifactPlan::from_ir(&impl_fixture_ir()).expect("canonical bytes must load");
    let method = plan
        .callables()
        .into_iter()
        .find(|callable| callable.cott_symbol == "a.mod.AState.first")
        .expect("impl method must be callable");

    assert_eq!(method.module, "a.mod");
    assert_eq!(method.name, "first");
    assert_eq!(method.cott_symbol, "a.mod.AState.first");
    assert_eq!(
        method.kind,
        PythonCallableKind::ImplMethod {
            concrete: "AState".to_owned()
        }
    );
    assert_eq!(method.declaration["name"], "first");
    assert_eq!(
        method
            .owner
            .as_ref()
            .expect("impl method owns its declaration")["name"],
        "a.mod.AState"
    );
}

#[test]
fn rejects_malformed_canonical_declarations_with_structured_error() {
    let mut ir = fixture_ir();
    let module = &mut ir.modules[0];
    let mut value: serde_json::Value = serde_json::from_slice(&module.bytes).unwrap();
    value["declarations"][0]
        .as_object_mut()
        .unwrap()
        .remove("name");
    module.bytes = serde_json::to_vec(&value).unwrap();
    module.bytes.push(b'\n');

    let error = PythonArtifactPlan::from_ir(&ir).expect_err("missing declaration name must reject");
    assert!(matches!(
        error,
        PythonArtifactPlanError::InvalidModule { .. }
    ));
    assert!(error.to_string().contains("canonical module"));
}
