use std::fs;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

use cott::binding::{resolve_bindings, resolve_implementations, validate_candidate};
use cott::compiler::{SourceFile, parse_project};
use cott::hir::lower;
use cott::ir::render;
use cott::manifest::ProjectConfig;
use cott::project::{ProjectPaths, load_config_with_paths};
use cott::python::artifact_plan::PythonArtifactPlan;

struct Fixture {
    config: ProjectConfig,
    paths: ProjectPaths,
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
    fs::create_dir_all(root.join("src")).expect("source directory must be creatable");
    fs::create_dir_all(root.join("python")).expect("Python source directory must be creatable");
    fs::write(
        root.join("cott.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.python]\nsource = \"python\"\ngenerated = \"generated/python\"\nstubs = \"generated/stubs\"\ninterpreter = \".venv/bin/python\"\ntype_checker = \".venv/bin/basedpyright\"\nruntime_validation = \"boundary\"\n",
    )
    .expect("manifest must be writable");
    let (config, paths) = load_config_with_paths(&root).expect("manifest must load");
    let parsed = parse_project([SourceFile::new(PathBuf::from("api/service.cott"), source)])
        .expect("fixture source must parse");
    let lowered = lower(&paths.source_dir, parsed).expect("fixture source must lower");
    let ir = render(&lowered).expect("fixture source must render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("fixture IR must project");
    Fixture {
        config,
        paths,
        plan,
        root,
    }
}

#[test]
fn resolves_canonical_planned_function_without_semantic_project() {
    let fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    let path = fixture
        .paths
        .python_source_dir
        .join("_cott_impl/api/service/run.py");
    fs::create_dir_all(path.parent().expect("binding has parent")).unwrap();
    fs::write(&path, b"def run() -> object:\n    return None\n").unwrap();

    let bindings = resolve_bindings(&fixture.config, &fixture.paths, &fixture.plan)
        .expect("binding must resolve");
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
        .paths
        .python_source_dir
        .join("_cott_impl/api/service/run.py");
    fs::create_dir_all(path.parent().expect("binding has parent")).unwrap();
    fs::write(&path, b"def run() -> object:\n    return None\n").unwrap();

    let resolution = resolve_implementations(&fixture.config, &fixture.paths, &fixture.plan)
        .expect("missing durable source is an unresolved result");
    assert_eq!(resolution.resolved.len(), 1);
    assert_eq!(resolution.unresolved.len(), 1);
    assert_eq!(resolution.unresolved[0].module, "api.service");
    assert_eq!(resolution.unresolved[0].function, "missing");
    assert_eq!(
        resolution.unresolved[0].source,
        fixture
            .paths
            .python_source_dir
            .join("_cott_impl/api/service/missing.py")
    );
}

#[test]
fn candidate_validation_public_api_uses_only_the_canonical_plan() {
    let fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "run",
        b"def run() -> object:\n    return None\n",
    )
    .expect("canonical plan candidate must validate");
}
