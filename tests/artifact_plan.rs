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

fn default_impl_fixture_ir() -> CanonicalIr {
    let parsed = parse_project([source(
        "src/api/service.cott",
        r#"module api.service

trait Reader:
    fn read(self, amount: I32) -> I32 = api.service.default_read
    fn label(self) -> Unit

fn default_read(receiver: Reader, amount: I32) -> I32

impl ReaderState for Reader:
    fn label(self) -> Unit:
        ensures true
"#,
    )])
    .expect("default impl fixture must parse");
    let project = lower(Path::new("src"), parsed).expect("default impl fixture must lower");
    render(&project).expect("default impl fixture must render")
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
fn default_impl_methods_keep_only_the_verified_free_facade_dependency() {
    let plan =
        PythonArtifactPlan::from_ir(&default_impl_fixture_ir()).expect("canonical bytes must load");
    let method = plan
        .callables()
        .into_iter()
        .find(|callable| callable.cott_symbol == "api.service.ReaderState.read")
        .expect("default impl method must remain a compiler dispatch slot");

    assert_eq!(method.declaration["selected"]["origin"], "default");
    assert_eq!(
        method.declaration["selected"]["function"],
        serde_json::json!({
            "module": "api.service",
            "symbol": "default_read",
            "verified_facade": "api.service.default_read",
        })
    );
}

#[test]
fn rejects_distinct_trait_defaults_for_one_multi_trait_impl() {
    let parsed = parse_project([source(
        "src/api/service.cott",
        r#"module api.service

trait Reader:
    fn read(self) -> I32 = api.service.reader_read
    fn label(self) -> Unit

trait Writer:
    fn read(self) -> I32 = api.service.writer_read
    fn label(self) -> Unit

fn reader_read(receiver: Reader) -> I32
fn writer_read(receiver: Writer) -> I32

impl State for Reader + Writer:
    fn label(self) -> Unit:
        ensures true
"#,
    )])
    .expect("default conflict fixture must parse");

    let errors = lower(Path::new("src"), parsed)
        .expect_err("distinct inherited trait defaults must be ambiguous");
    assert!(
        errors
            .iter()
            .any(|error| error.diagnostic.message.contains("ambiguous")),
        "expected a deterministic default ambiguity diagnostic: {errors:?}"
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

#[test]
fn rejects_impl_without_selected_method_metadata() {
    let mut ir = impl_fixture_ir();
    let module = ir
        .modules
        .iter_mut()
        .find(|module| module.module.as_string() == "a.mod")
        .expect("fixture module must exist");
    let mut value: serde_json::Value = serde_json::from_slice(&module.bytes).unwrap();
    value["declarations"]
        .as_array_mut()
        .unwrap()
        .iter_mut()
        .find(|declaration| declaration["kind"] == "impl")
        .unwrap()
        .as_object_mut()
        .unwrap()
        .remove("selected_methods");
    module.bytes = serde_json::to_vec(&value).unwrap();
    module.bytes.push(b'\n');

    let error = PythonArtifactPlan::from_ir(&ir).expect_err("selection metadata is required");
    assert!(matches!(
        error,
        PythonArtifactPlanError::InvalidModule { .. }
    ));
}

#[test]
fn rejects_explicit_method_absent_from_selected_slots() {
    let mut ir = impl_fixture_ir();
    let module = ir
        .modules
        .iter_mut()
        .find(|module| module.module.as_string() == "a.mod")
        .expect("fixture module must exist");
    let mut value: serde_json::Value = serde_json::from_slice(&module.bytes).unwrap();
    value["declarations"]
        .as_array_mut()
        .unwrap()
        .iter_mut()
        .find(|declaration| declaration["kind"] == "impl")
        .unwrap()["selected_methods"] = serde_json::json!([]);
    module.bytes = serde_json::to_vec(&value).unwrap();
    module.bytes.push(b'\n');

    PythonArtifactPlan::from_ir(&ir).expect_err("unselected method must reject");
}

#[test]
fn specialization_target_is_a_dependency_not_a_fake_impl_binding() {
    let parsed = parse_project([source(
        "src/api/service.cott",
        r#"module api.service


trait Reader:
    fn read(self, value: I32) -> I32 = api.service.default_read
    fn label(self) -> Unit

fn default_read(receiver: Reader, value: I32) -> I32
fn specialized_read(receiver: ReaderState, value: I32) -> I32

specialize ReaderState for Reader:
    read = api.service.specialized_read

impl ReaderState for Reader:
    fn label(self) -> Unit:
        ensures true
"#,
    )])
    .expect("specialization fixture must parse");
    let project = lower(Path::new("src"), parsed).expect("specialization fixture must lower");
    let mut ir = render(&project).expect("specialization fixture must render");
    let module = ir
        .modules
        .iter_mut()
        .find(|module| module.module.as_string() == "api.service")
        .expect("specialization module must exist");
    let mut value: serde_json::Value = serde_json::from_slice(&module.bytes).unwrap();
    value["declarations"]
        .as_array_mut()
        .expect("declarations must be an array")
        .iter_mut()
        .find(|declaration| declaration["name"] == "api.service.specialized_read")
        .expect("specialization target must exist")["public"] = serde_json::Value::Bool(false);
    module.bytes = serde_json::to_vec(&value).unwrap();
    module.bytes.push(b'\n');

    let plan = PythonArtifactPlan::from_ir(&ir).expect("specialization plan must load");
    let callables = plan.callables();
    let target = callables
        .iter()
        .find(|callable| callable.cott_symbol == "api.service.specialized_read")
        .expect("private specialization target must remain a free-function dependency");
    assert_eq!(target.kind, PythonCallableKind::Function);
    let dispatch = callables
        .iter()
        .find(|callable| callable.cott_symbol == "api.service.ReaderState.read")
        .expect("specialized dispatch slot must remain compiler-owned");
    assert_eq!(dispatch.declaration["selected"]["origin"], "specialization");
    assert_eq!(
        dispatch.declaration["selected"]["function"]["verified_facade"],
        "api.service.specialized_read"
    );
    assert!(
        !callables
            .iter()
            .any(|callable| callable.cott_symbol == "api.service.ReaderState.specialized_read")
    );
}
