use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::binding::{ResolvedBinding, resolve_bindings};
use cott::compiler::parse_project;
use cott::hash::sha256_hex;
use cott::hir::lower;
use cott::ir::render;
use cott::manifest::ProjectConfig;
use cott::project::{discover_sources_from_paths, load_config_with_paths};
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

[target.python.implementations]
"app.run" = "cott_bindings.app.run:run"
"#;
const SOURCE: &str = r#"module app

doc """A count returned by the entry point"""
alias Count = I32

fn run() -> Count
"#;
const BINDING: &[u8] = b"def run() -> int:\n    return 7\n";

fn write_target_metadata(root: &Path) {
    fs::create_dir_all(root.join("python")).expect("Python source directory");
    fs::write(
        root.join("python/pyproject.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14,<3.15\"\ndependencies = []\n",
    )
    .expect("target project metadata should be writable");
}

struct Inputs {
    _temp: TempDir,
    config: ProjectConfig,
    plan: PythonArtifactPlan,
    ir: cott::ir::CanonicalIr,
    bindings: Vec<ResolvedBinding>,
}
fn inputs() -> Inputs {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::create_dir_all(temp.path.join("python/cott_bindings/app"))
        .expect("binding directory should be writable");
    fs::write(temp.path.join("src/app.cott"), SOURCE).expect("source should be writable");
    fs::write(temp.path.join("python/cott_bindings/app/run.py"), BINDING)
        .expect("binding should be writable");
    write_target_metadata(&temp.path);
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
fn emit_sources(sources: &[(&str, &str)]) -> std::collections::BTreeMap<PathBuf, Vec<u8>> {
    emit_sources_result(sources).expect("valid source should emit")
}

fn emit_sources_result(
    sources: &[(&str, &str)],
) -> Result<std::collections::BTreeMap<PathBuf, Vec<u8>>, Vec<cott::python_emit::EmitDiagnostic>> {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    write_target_metadata(&temp.path);
    for (name, source) in sources {
        fs::write(temp.path.join("src").join(name), source).expect("source should be writable");
    }
    let (config, paths) = load_config_with_paths(&temp.path).expect("manifest should load");
    let parsed =
        parse_project(discover_sources_from_paths(&paths).expect("sources should be discovered"))
            .expect("sources should parse");
    let ir = render(&lower(&paths.source_dir, parsed).expect("sources should lower"))
        .expect("source should render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("canonical plan should load");
    emit(&config, &plan, &ir, &[]).map(|emission| emission.files)
}

#[test]
fn imports_cross_module_parameter_and_struct_field_types() {
    let files = emit_sources(&[
        (
            "leaf.cott",
            "module leaf\n\nstruct Marker:\n    value: I32\n",
        ),
        (
            "types.cott",
            "module types\nuse leaf.{Marker}\n\nstruct Payload:\n    marker: Marker\n",
        ),
        (
            "api.cott",
            "module api\nuse types.{Payload}\n\nfn accept(value: Payload) -> Unit\n",
        ),
    ]);
    let types = String::from_utf8_lossy(bytes(&files, "python/types_types.py"));
    let facade = String::from_utf8_lossy(bytes(&files, "python/api.py"));
    let stub = String::from_utf8_lossy(bytes(&files, "stubs/api.pyi"));
    assert!(
        types.contains("from leaf_types import Marker"),
        "types output:\n{types}"
    );
    assert!(
        facade.contains("from types_types import Payload"),
        "facade output:\n{facade}"
    );
    assert!(
        stub.contains("from types_types import Payload"),
        "stub output:\n{stub}"
    );
}

#[test]
fn imports_cross_module_contract_constants() {
    let files = emit_sources(&[
        ("limits.cott", "module limits\n\nconst MAX: I32 = 3\n"),
        (
            "api.cott",
            "module api\nuse limits.{MAX}\n\nfn check(value: I32) -> Unit:\n    requires value < MAX\n",
        ),
    ]);
    let facade = String::from_utf8_lossy(bytes(&files, "python/api.py"));
    assert!(
        facade.contains("from limits_types import MAX"),
        "facade output:\n{facade}"
    );
}

#[test]
fn emits_single_and_multiple_generic_trait_bounds() {
    let files = emit_sources(&[
        (
            "traits.cott",
            "module traits\n\ntrait Comparable:\n    fn compare(self, other: I32) -> I32\n\ntrait Serializable:\n    fn serialize(self) -> I32\n",
        ),
        (
            "api.cott",
            "module api\nuse traits.{Comparable, Serializable}\n\nfn one[T: Comparable](value: T) -> T\nfn many[U: Comparable + Serializable](value: U) -> U\n",
        ),
    ]);
    let types = String::from_utf8_lossy(bytes(&files, "python/api_types.py"));
    let facade = String::from_utf8_lossy(bytes(&files, "python/api.py"));
    let stub = String::from_utf8_lossy(bytes(&files, "stubs/api.pyi"));
    let composite = "class _cott_U_Bounds(Comparable, Serializable, Protocol):\n    pass";
    assert!(types.contains(composite));
    assert!(facade.contains("from api_types import _cott_U_Bounds"));
    assert!(stub.contains(composite));
    for output in [facade.as_ref(), stub.as_ref()] {
        assert!(output.contains("from traits_types import Comparable, Serializable"));
        assert!(output.contains("T = TypeVar(\"T\", bound=Comparable)"));
        assert!(output.contains("U = TypeVar(\"U\", bound=_cott_U_Bounds)"));
    }
}

#[test]
fn disambiguates_same_generic_name_with_different_bounds() {
    let files = emit_sources(&[
        (
            "traits.cott",
            "module traits\n\ntrait Comparable:\n    fn compare(self, other: I32) -> I32\n\ntrait Serializable:\n    fn serialize(self) -> I32\n",
        ),
        (
            "api.cott",
            "module api\nuse traits.{Comparable, Serializable}\n\nfn first[T: Comparable](value: T) -> T\nfn second[T: Serializable](value: T) -> T\n",
        ),
    ]);
    let stub = String::from_utf8_lossy(bytes(&files, "stubs/api.pyi"));
    assert!(stub.contains("_cott_first_T = TypeVar(\"_cott_first_T\", bound=Comparable)"));
    assert!(stub.contains("_cott_second_T = TypeVar(\"_cott_second_T\", bound=Serializable)"));
    assert!(stub.contains("def first(value: _cott_first_T) -> _cott_first_T: ..."));
    assert!(stub.contains("def second(value: _cott_second_T) -> _cott_second_T: ..."));
}

#[test]
fn emits_complete_deterministic_python_artifact_tree() {
    let inputs = inputs();
    let first = emit(&inputs.config, &inputs.plan, &inputs.ir, &inputs.bindings)
        .expect("valid HIR inputs should emit");
    let second = emit(&inputs.config, &inputs.plan, &inputs.ir, &inputs.bindings)
        .expect("valid HIR inputs should emit");
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
    let generation: serde_json::Value =
        serde_json::from_slice(bytes(&first.files, "generation.json"))
            .expect("generation record should be JSON");
    assert_eq!(generation["schema_version"], 1);
    assert_eq!(generation["current"]["verified"], false);
    assert!(generation["current"].get("project").is_none());
    assert!(generation["current"].get("entry").is_none());
    let implementation = &generation["current"]["implementations"][0];
    assert_eq!(implementation["cott_symbol"], "app.run");
    assert_eq!(implementation["owner"], "manifest");
    assert_eq!(implementation["python_symbol"], "_cott_impl.app.run:run");
    assert_eq!(
        implementation["source_origin"],
        "python/cott_bindings/app/run.py"
    );
    assert_eq!(
        implementation["runtime_origin"],
        "python/_cott_impl/app/run.py"
    );
    assert_ne!(
        implementation["source_origin"],
        implementation["runtime_origin"]
    );
    assert_eq!(
        implementation["content_hash"],
        format!("sha256:{}", sha256_hex(BINDING))
    );
    assert_eq!(bytes(&first.files, "python/_cott_impl/app/run.py"), BINDING);
    assert!(
        !first
            .files
            .contains_key(Path::new("python/cott_bindings/app/run.py"))
    );
}

#[test]
fn unresolved_functions_are_omitted_from_facade_exports() {
    let inputs = inputs();
    let emitted = emit(&inputs.config, &inputs.plan, &inputs.ir, &[])
        .expect("unresolved bindings do not block emission");
    let facade = String::from_utf8_lossy(bytes(&emitted.files, "python/app.py"));
    assert!(facade.contains("_cott_load"));
    assert!(!facade.contains("\"run\""));
    assert!(!facade.contains("def run"));
    let stub = String::from_utf8_lossy(bytes(&emitted.files, "stubs/app.pyi"));
    assert!(stub.contains("def run"));
}

#[test]
fn rejects_mismatched_resolved_binding_with_diagnostic() {
    let inputs = inputs();
    let mut bindings = inputs.bindings.clone();
    bindings[0].function = String::from("not_run");
    let diagnostics = emit(&inputs.config, &inputs.plan, &inputs.ir, &bindings)
        .expect_err("mismatched binding must be rejected");
    assert!(
        diagnostics
            .iter()
            .any(|diagnostic| diagnostic.message.contains("binding")
                || diagnostic.message.contains("run"))
    );
}

#[test]
fn rejects_colliding_public_python_symbol_projection() {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(
        temp.path.join("src/app.cott"),
        "module app\n\nenum Foo:\n    Bar\n\nconst Foo_Bar: I32 = 1\n",
    )
    .expect("source should be writable");
    write_target_metadata(&temp.path);
    let (config, paths) = load_config_with_paths(&temp.path).expect("manifest should load");
    let parsed =
        parse_project(discover_sources_from_paths(&paths).expect("sources")).expect("parse");
    let ir = render(&lower(&paths.source_dir, parsed).expect("lower")).expect("render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("canonical plan should load");
    let diagnostics =
        emit(&config, &plan, &ir, &[]).expect_err("colliding Python symbols must fail");
    assert!(
        diagnostics
            .iter()
            .any(|diagnostic| diagnostic.message.contains("Foo_Bar")
                && diagnostic.message.contains("collides"))
    );
}
