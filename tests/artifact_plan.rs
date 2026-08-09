use std::path::{Path, PathBuf};

use cott::compiler::{SourceFile, parse_project};
use cott::hir::lower;
use cott::ir::{CanonicalIr, render};
use cott::python::artifact_plan::{PythonArtifactPlan, PythonArtifactPlanError};

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
            .callable_functions()
            .iter()
            .map(|function| function.function.as_str())
            .collect::<Vec<_>>(),
        ["a.mod.check", "z.mod.hidden", "z.mod.run"]
    );
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
        plan.public_callable_functions()
            .iter()
            .map(|function| function.function.as_str())
            .collect::<Vec<_>>(),
        ["a.mod.check", "z.mod.run"]
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
