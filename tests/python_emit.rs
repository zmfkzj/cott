use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::binding::{ResolvedBinding, resolve_bindings};
use cott::compiler::parse_project;
use cott::hir::lower;
use cott::ir::render;
use cott::manifest::ProjectConfig;
use cott::project::{ProjectPaths, discover_sources_from_paths, load_config_with_paths};
use cott::python::artifact_plan::PythonArtifactPlan;
use cott::python_emit::emit;

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);
struct TempDir {
    path: PathBuf,
}
impl TempDir {
    fn new() -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-python-emit-tests-{}-{number}",
                std::process::id()
            ));
            match fs::create_dir(&path) {
                Ok(()) => return Self { path },
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => number += 1,
                Err(error) => panic!("failed to create temporary directory: {error}"),
            }
        }
    }
}
impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

const MANIFEST: &str = r#"[project]
name = "demo"
version = "0.1.0"
source = "src"

[target.python]
source = "python"
generated = "generated/python"
stubs = "generated/stubs"
interpreter = ".venv/bin/python"
type_checker = ".venv/bin/basedpyright"
runtime_validation = "boundary"
"#;
const SOURCE: &str = r#"module app

doc """A count returned by the entry point"""
alias Count = I32

fn run() -> Count
"#;
const BINDING: &[u8] = b"def run() -> int:\n    return 7\n";

struct Inputs {
    _temp: TempDir,
    config: ProjectConfig,
    paths: ProjectPaths,
    plan: PythonArtifactPlan,
    ir: cott::ir::CanonicalIr,
    bindings: Vec<ResolvedBinding>,
}
fn inputs() -> Inputs {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::create_dir_all(temp.path.join("python/_cott_impl/app"))
        .expect("binding directory should be writable");
    fs::write(temp.path.join("src/app.cott"), SOURCE).expect("source should be writable");
    fs::write(temp.path.join("python/_cott_impl/app/run.py"), BINDING)
        .expect("binding should be writable");
    let (config, paths) = load_config_with_paths(&temp.path).expect("manifest should load");
    let sources = discover_sources_from_paths(&paths).expect("source should be discovered");
    let parsed = parse_project(sources).expect("source should parse");
    let hir = lower(&paths.source_dir, parsed).expect("source should lower");
    let ir = render(&hir).expect("source should render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("canonical plan should load");
    let bindings = resolve_bindings(&config, &paths, &plan).expect("bindings should resolve");
    Inputs {
        _temp: temp,
        config,
        paths,
        plan,
        ir,
        bindings,
    }
}
fn bytes<'a>(files: &'a std::collections::BTreeMap<PathBuf, Vec<u8>>, path: &str) -> &'a [u8] {
    files
        .get(Path::new(path))
        .unwrap_or_else(|| panic!("missing artifact {path}"))
        .as_slice()
}

#[test]
fn emits_complete_deterministic_python_artifact_tree() {
    let inputs = inputs();
    let first = emit(
        &inputs.config.project.name,
        &inputs.plan,
        &inputs.ir,
        &inputs.bindings,
    )
    .expect("valid Profile-P inputs should emit");
    let second = emit(
        &inputs.config.project.name,
        &inputs.plan,
        &inputs.ir,
        &inputs.bindings,
    )
    .expect("valid Profile-P inputs should emit");
    assert_eq!(first.files, second.files);
    let expected_paths = [
        "python/__init__.py",
        "python/_cott_impl/__init__.py",
        "python/_cott_impl/app/__init__.py",
        "python/cott_runtime/__init__.py",
        "python/cott_runtime/py.typed",
        "python/app_types.py",
        "python/app.py",
        "python/_cott_impl/app/run.py",
        "stubs/app.pyi",
        "ir/app.json",
        "generation.json",
    ];
    for path in expected_paths {
        assert!(first.files.contains_key(Path::new(path)), "missing {path}");
        assert!(bytes(&first.files, path).ends_with(b"\n"));
        assert!(!bytes(&first.files, path).ends_with(b"\n\n"));
    }
    assert!(!first.files.contains_key(Path::new("python/__main__.py")));
    let facade = String::from_utf8_lossy(bytes(&first.files, "python/app.py"));
    assert!(facade.contains("_cott_load"));
    assert!(facade.contains("run"));
    assert!(facade.contains("__all__"));
    let generation = String::from_utf8_lossy(bytes(&first.files, "generation.json"));
    assert!(generation.contains("\"verified\":false"));
    assert!(generation.contains("\"project\":\"demo\""));
    assert!(!generation.contains("\"entry\""));
    assert_eq!(bytes(&first.files, "python/_cott_impl/app/run.py"), BINDING);
}

#[test]
fn unresolved_functions_are_omitted_from_facade_exports() {
    let inputs = inputs();
    let emitted = emit(&inputs.config.project.name, &inputs.plan, &inputs.ir, &[])
        .expect("unresolved bindings do not block emission");
    let facade = String::from_utf8_lossy(bytes(&emitted.files, "python/app.py"));
    assert!(facade.contains("from cott_runtime import _cott_load"));
    assert!(!facade.contains("\"run\""));
    assert!(!facade.contains("run ="));
    let stub = String::from_utf8_lossy(bytes(&emitted.files, "stubs/app.pyi"));
    assert!(stub.contains("def run"));
}

#[test]
fn rejects_mismatched_resolved_binding_with_diagnostic() {
    let inputs = inputs();
    let mut bindings = inputs.bindings.clone();
    bindings[0].function = String::from("not_run");
    let diagnostics = emit(
        &inputs.config.project.name,
        &inputs.plan,
        &inputs.ir,
        &bindings,
    )
    .expect_err("mismatched binding must be rejected");
    assert!(
        diagnostics
            .iter()
            .any(|diagnostic| diagnostic.message.contains("binding")
                || diagnostic.message.contains("run"))
    );
}
