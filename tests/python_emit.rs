use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::binding::{ResolvedBinding, resolve_bindings};
use cott::compiler::parse_project;
use cott::hash::sha256_hex;
use cott::hir::lower;
use cott::ir::render;
use cott::project::{discover_sources, load_project};
use cott::python_emit::emit;
use cott::semantic::analyze_project;

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
source = "src"

[target.python]
generated = "generated/python"
entry = "app.run"
"#;

const SOURCE: &str = r#"module app

doc """A count returned by the entry point"""
alias Count = I32

fn run() -> Count
"#;

const BINDING: &[u8] = b"def run() -> int:\n    return 7\n";

struct Inputs {
    _temp: TempDir,
    project: cott::project::Project,
    semantic: cott::semantic::SemanticProject,
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
    let project = load_project(&temp.path).expect("manifest should load");
    let sources = discover_sources(&project).expect("source should be discovered");
    let parsed = parse_project(sources).expect("source should parse");
    let hir = lower(&project.source_dir, parsed.clone()).expect("source should lower");
    let semantic = analyze_project(&project.source_dir, parsed).expect("source should analyze");
    let bindings = resolve_bindings(&project, &semantic).expect("bindings should resolve");
    let ir = render(&hir).expect("source should render");

    Inputs {
        _temp: temp,
        project,
        semantic,
        ir,
        bindings,
    }
}

fn plan(inputs: &Inputs) -> cott::python_emit::Emission {
    emit(
        &inputs.project,
        &inputs.semantic,
        &inputs.ir,
        &inputs.bindings,
    )
    .expect("valid Profile-P inputs should emit")
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
    let first = plan(&inputs);
    let second = plan(&inputs);

    assert_eq!(first.entry_module.as_string(), "app");
    assert_eq!(first.entry_function, "run");
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
        "python/__main__.py",
        "stubs/app.pyi",
        "ir/app.json",
        "generation.json",
    ];
    for path in expected_paths {
        assert!(first.files.contains_key(Path::new(path)), "missing {path}");
        assert!(bytes(&first.files, path).ends_with(b"\n"));
        assert!(!bytes(&first.files, path).ends_with(b"\n\n"));
    }

    let runtime = bytes(&first.files, "python/cott_runtime/__init__.py");
    assert!(runtime.windows(10).any(|window| window == b"_cott_load"));
    let types = bytes(&first.files, "python/app_types.py");
    assert!(types.windows(9).any(|window| window == b"TypeAlias"));
    assert!(types.windows(5).any(|window| window == b"Count"));

    let facade = bytes(&first.files, "python/app.py");
    let facade_text = String::from_utf8_lossy(facade);
    assert!(facade_text.contains("_cott_load"));
    assert!(facade_text.contains("run"));
    assert!(!facade_text.contains("import _cott_impl"));
    assert!(!facade_text.contains("from _cott_impl"));

    let stub = String::from_utf8_lossy(bytes(&first.files, "stubs/app.pyi"));
    assert!(stub.contains("run"));
    assert!(stub.contains("def run"));

    let ir = String::from_utf8_lossy(bytes(&first.files, "ir/app.json"));
    assert!(ir.contains("\"module\":\"app\""));
    assert!(ir.contains("\"function\""));

    let generation = String::from_utf8_lossy(bytes(&first.files, "generation.json"));
    assert!(generation.contains("\"verified\""));
    assert!(generation.contains("false"));
    assert!(generation.contains("\"demo\""));
    assert!(generation.contains("\"app\""));
    assert!(generation.contains("\"run\""));
    assert!(generation.contains(&sha256_hex(BINDING)));
    let managed_files = generation
        .split_once("\"managed_files\":{")
        .and_then(|(_, rest)| rest.split_once("},\"project\""))
        .map(|(managed, _)| managed)
        .expect("generation metadata should contain managed_files");
    assert!(!managed_files.contains("\"generation.json\":"));
    for path in [
        "python/cott_runtime/__init__.py",
        "python/app.py",
        "python/_cott_impl/app/run.py",
    ] {
        let expected = format!("\"{path}\":\"{}\"", sha256_hex(bytes(&first.files, path)));
        assert!(
            managed_files.contains(&expected),
            "missing managed hash for {path}"
        );
    }

    assert_eq!(bytes(&first.files, "python/_cott_impl/app/run.py"), BINDING);

    let runner = String::from_utf8_lossy(bytes(&first.files, "python/__main__.py"));
    assert!(runner.contains("from app import"));
    assert!(runner.contains("run"));
    assert!(runner.contains("_cott_display"));
}

#[test]
fn rejects_missing_entry_with_diagnostic() {
    let inputs = inputs();
    let mut project = inputs.project.clone();
    project.entry = String::from("app.missing");

    let diagnostics = emit(&project, &inputs.semantic, &inputs.ir, &inputs.bindings)
        .expect_err("missing entry must be rejected");
    assert!(!diagnostics.is_empty());
    assert!(diagnostics.iter().any(|diagnostic| {
        diagnostic.message.contains("entry") || diagnostic.message.contains("missing")
    }));
}

#[test]
fn rejects_mismatched_resolved_binding_with_diagnostic() {
    let inputs = inputs();
    let mut bindings = inputs.bindings.clone();
    bindings[0].function = String::from("not_run");

    let diagnostics = emit(&inputs.project, &inputs.semantic, &inputs.ir, &bindings)
        .expect_err("mismatched binding must be rejected");
    assert!(!diagnostics.is_empty());
    assert!(diagnostics.iter().any(|diagnostic| {
        diagnostic.message.contains("binding") || diagnostic.message.contains("run")
    }));
}
