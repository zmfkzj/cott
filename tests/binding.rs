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
    fs::write(
        root.join("python/pyproject.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14,<3.15\"\ndependencies = []\n",
    )
    .expect("target project metadata must be writable");
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
    let mut fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    fixture.config.python.implementations.insert(
        "api.service.run".to_owned(),
        "_cott_impl.api.service.run:run".to_owned(),
    );
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
fn rejects_unmapped_implementation_without_agent_provenance() {
    let fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    let path = fixture
        .paths
        .python_source_dir
        .join("_cott_impl/api/service/run.py");
    fs::create_dir_all(path.parent().unwrap()).unwrap();
    fs::write(&path, b"def run() -> object:\n    return None\n").unwrap();
    let diagnostics =
        resolve_implementations(&fixture.config, &fixture.paths, &fixture.plan).unwrap_err();
    assert!(diagnostics[0].message.contains("matching agent provenance"));
}

#[test]
fn reports_unresolved_canonical_planned_function() {
    let mut fixture = fixture("module api.service\n\nfn run() -> Unit\nfn missing() -> Unit\n");
    fixture.config.python.implementations.insert(
        "api.service.run".to_owned(),
        "_cott_impl.api.service.run:run".to_owned(),
    );
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

#[test]
fn manifest_binding_precedes_the_agent_path() {
    let mut fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    fixture.config.python.implementations.insert(
        "api.service.run".to_owned(),
        "adapters.service:execute".to_owned(),
    );
    let manifest_path = fixture.paths.python_source_dir.join("adapters/service.py");
    fs::create_dir_all(manifest_path.parent().unwrap()).unwrap();
    fs::write(
        &manifest_path,
        b"def execute() -> object:\n    return None\n",
    )
    .unwrap();
    let agent_path = fixture
        .paths
        .python_source_dir
        .join("_cott_impl/api/service/run.py");
    fs::create_dir_all(agent_path.parent().unwrap()).unwrap();
    fs::write(&agent_path, b"pass\n").unwrap();

    let resolution =
        resolve_implementations(&fixture.config, &fixture.paths, &fixture.plan).unwrap();
    assert_eq!(resolution.resolved.len(), 1);
    assert_eq!(resolution.resolved[0].source, manifest_path);
    assert_eq!(resolution.resolved[0].implementation_function, "execute");
    assert_eq!(
        resolution.resolved[0].owner,
        cott::binding::BindingOwner::Manifest
    );
    assert_eq!(
        resolution.resolved[0].generated_relative,
        PathBuf::from("adapters/service.py")
    );
}

#[test]
fn reports_unreferenced_durable_implementations_as_stale() {
    let mut fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    fixture.config.python.implementations.insert(
        "api.service.run".to_owned(),
        "_cott_impl.api.service.run:run".to_owned(),
    );
    let run = fixture
        .paths
        .python_source_dir
        .join("_cott_impl/api/service/run.py");
    let stale = fixture
        .paths
        .python_source_dir
        .join("_cott_impl/api/service/old.py");
    fs::create_dir_all(run.parent().unwrap()).unwrap();
    fs::write(&run, b"def run() -> object:\n    return None\n").unwrap();
    fs::write(&stale, b"def old() -> object:\n    return None\n").unwrap();

    let resolution =
        resolve_implementations(&fixture.config, &fixture.paths, &fixture.plan).unwrap();
    assert_eq!(resolution.stale, [stale]);
}

#[test]
fn rejects_stale_manifest_binding_keys() {
    let mut fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    fixture.config.python.implementations.insert(
        "api.service.removed".to_owned(),
        "adapters.service:execute".to_owned(),
    );

    let diagnostics =
        resolve_implementations(&fixture.config, &fixture.paths, &fixture.plan).unwrap_err();
    assert!(
        diagnostics[0]
            .message
            .contains("does not name a public function")
    );
}

#[test]
fn validates_parameter_names_and_kinds_against_canonical_ir() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "api.service.run",
        b"def run(value: int) -> int:\n    return value\n",
    )
    .unwrap();
    let error = validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "api.service.run",
        b"def run(other: int) -> int:\n    return other\n",
    )
    .unwrap_err();
    assert!(error.contains("parameters do not match"));
}

#[test]
fn accepts_only_import_roots_selected_in_uv_lock() {
    let mut fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    let lockfile = fixture.root.join("uv.lock");
    fs::write(
        &lockfile,
        "[[package]]\nname = \"demo\"\ndependencies = [{ name = \"locked-package\" }]\n\n[[package]]\nname = \"locked-package\"\n",
    )
    .unwrap();
    fixture.paths.lockfile = Some(lockfile);

    validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "api.service.run",
        b"import locked_package\n\ndef run() -> object:\n    return None\n",
    )
    .expect("selected lockfile import must validate");
    let error = validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "api.service.run",
        b"import unlocked_package\n\ndef run() -> object:\n    return None\n",
    )
    .unwrap_err();
    assert_eq!(
        error,
        "external distribution import 'unlocked_package' is not selected in uv.lock"
    );
}
