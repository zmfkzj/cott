use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use cott::binding::{resolve_bindings, resolve_implementations, validate_candidate};
use cott::compiler::{SourceFile, parse_project};
use cott::hir::lower;
use cott::ir::render;
use cott::project::Project;
use cott::python::artifact_plan::PythonArtifactPlan;

struct Fixture {
    project: Project,
    plan: PythonArtifactPlan,
    root: PathBuf,
}

impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}

fn fixture(source: &str) -> Fixture {
    let root = std::env::temp_dir().join(format!(
        "cott-binding-{}-{}",
        std::process::id(),
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("clock must be after epoch")
            .as_nanos()
    ));
    let implementation_dir = root.join("impl");
    fs::create_dir_all(&implementation_dir).expect("fixture directory must be creatable");
    let parsed = parse_project([SourceFile::new(
        PathBuf::from("src/api/service.cott"),
        source,
    )])
    .expect("fixture source must parse");
    let lowered = lower(Path::new("src"), parsed).expect("fixture source must lower");
    let ir = render(&lowered).expect("fixture source must render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("fixture IR must project");
    let project = Project {
        root: root.clone(),
        name: String::from("demo"),
        source_dir: root.join("src"),
        generated_dir: root.join("generated"),
        implementation_dir,
        entry: String::from("api.service.run"),
    };
    Fixture {
        project,
        plan,
        root,
    }
}

#[test]
fn resolves_canonical_planned_function_without_semantic_project() {
    let fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    let path = fixture
        .project
        .implementation_dir
        .join("api/service/run.py");
    fs::create_dir_all(path.parent().expect("binding has parent")).unwrap();
    fs::write(&path, b"def run() -> object:\n    return None\n").unwrap();

    let bindings = resolve_bindings(&fixture.project, &fixture.plan).expect("binding must resolve");
    assert_eq!(bindings.len(), 1);
    assert_eq!(bindings[0].module, "api.service");
    assert_eq!(bindings[0].function, "run");
    assert_eq!(bindings[0].source, path);
    assert_eq!(
        bindings[0].generated_relative,
        PathBuf::from("_cott_impl/api/service/run.py")
    );
}

#[test]
fn reports_unresolved_canonical_planned_function() {
    let fixture = fixture("module api.service\n\nfn run() -> Unit\nfn missing() -> Unit\n");
    let path = fixture
        .project
        .implementation_dir
        .join("api/service/run.py");
    fs::create_dir_all(path.parent().expect("binding has parent")).unwrap();
    fs::write(&path, b"def run() -> object:\n    return None\n").unwrap();

    let resolution = resolve_implementations(&fixture.project, &fixture.plan)
        .expect("missing durable source is an unresolved result");
    assert_eq!(resolution.resolved.len(), 1);
    assert_eq!(resolution.unresolved.len(), 1);
    assert_eq!(resolution.unresolved[0].module, "api.service");
    assert_eq!(resolution.unresolved[0].function, "missing");
    assert_eq!(
        resolution.unresolved[0].source,
        fixture
            .project
            .implementation_dir
            .join("api/service/missing.py")
    );
}

#[test]
fn candidate_validation_public_api_uses_only_the_canonical_plan() {
    let fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    validate_candidate(
        &fixture.project,
        &fixture.plan,
        "run",
        b"def run() -> object:\n    return None\n",
    )
    .expect("canonical plan candidate must validate");
}
