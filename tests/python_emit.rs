use serde_json::Value;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};

use cott::binding::{BindingOwner, ResolvedBinding, resolve_bindings};
use cott::compiler::parse_project;
use cott::hash::sha256_hex;
use cott::hir::lower;
use cott::ir::render;
use cott::manifest::ProjectConfig;
use cott::project::{discover_sources_from_paths, load_config_with_paths};
use cott::python::artifact_plan::{PythonArtifactPlan, PythonCallableKind};
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

struct Payload:
    data: Count

fn run(data: Count) -> Payload:
    ensures result.data == data
"#;
const BINDING: &[u8] = b"def run(data: int) -> object:\n    return None\n";

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
    emit_sources_with_external_types_result(sources, &[])
}

fn emit_sources_with_external_types_result(
    sources: &[(&str, &str)],
    external_types: &[(&str, &str)],
) -> Result<std::collections::BTreeMap<PathBuf, Vec<u8>>, Vec<cott::python_emit::EmitDiagnostic>> {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    write_target_metadata(&temp.path);
    for (name, source) in sources {
        fs::write(temp.path.join("src").join(name), source).expect("source should be writable");
    }
    let (mut config, paths) = load_config_with_paths(&temp.path).expect("manifest should load");
    config.python.external_types = external_types
        .iter()
        .map(|(name, target)| ((*name).to_owned(), (*target).to_owned()))
        .collect();
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
fn emits_named_const_generic_specializations() {
    let files = emit_sources(&[(
        "matrix.cott",
        r#"module matrix

struct Matrix[T, const N: U32]:
    values: Array[T, N]

alias ByteMatrix = Matrix[U8, 2]
"#,
    )]);
    let types = String::from_utf8_lossy(bytes(&files, "python/matrix_types.py"));
    let stub = String::from_utf8_lossy(bytes(&files, "stubs/matrix.pyi"));
    assert!(
        types.contains("ByteMatrix: TypeAlias = Matrix[U8, Literal[2]]"),
        "{types}"
    );
    assert!(
        stub.contains("from matrix_types import ByteMatrix as ByteMatrix, Matrix as Matrix"),
        "{stub}"
    );
    assert!(!stub.contains("CottTuple2"), "{stub}");
}

#[test]
fn emits_composite_protocol_for_associated_type_bounds() {
    let files = emit_sources(&[
        (
            "traits.cott",
            "module traits\n\ntrait Comparable:\n    fn compare(self, other: I32) -> I32\n\ntrait Serializable:\n    fn serialize(self) -> I32\n",
        ),
        (
            "stream.cott",
            "module stream\nuse traits.{Comparable, Serializable}\n\ntrait Stream:\n    type Item: Comparable + Serializable\n    fn next(self) -> Stream.Item\n",
        ),
    ]);
    let types = String::from_utf8_lossy(bytes(&files, "python/stream_types.py"));
    assert!(
        types.contains("from traits_types import Comparable, Serializable"),
        "{types}"
    );
    let composite = "class _cott__cott_stream_Stream_stream_Stream_Item_Bounds(Comparable, Serializable, Protocol):\n    pass";
    assert!(types.contains(composite), "{types}");
    assert!(
        types.contains(
            "_cott_stream_Stream_stream_Stream_Item = TypeVar(\"_cott_stream_Stream_stream_Stream_Item\", bound=_cott__cott_stream_Stream_stream_Stream_Item_Bounds)"
        ),
        "{types}"
    );
}

#[test]
fn emits_resources_with_required_terminal_metadata() {
    let files = emit_sources(&[(
        "door.cott",
        "module door\n\nresource Door:\n    initial Open\n    state Open\n    state Closed\n    terminal Closed\n    transition Open -> Closed\n",
    )]);
    let types = String::from_utf8_lossy(bytes(&files, "python/door_types.py"));
    assert!(
        types.find("class Door_Open:").expect("open state")
            < types.find("class Door_Closed:").expect("closed state"),
        "{types}"
    );
}

#[test]
fn rejects_resource_terminal_metadata_that_is_not_exact() {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(
        temp.path.join("src/door.cott"),
        "module door\n\nresource Door:\n    initial Open\n    state Open\n    state Closed\n    terminal Closed\n    transition Open -> Closed\n",
    )
    .expect("source should be writable");
    write_target_metadata(&temp.path);
    let (config, paths) = load_config_with_paths(&temp.path).expect("manifest should load");
    let parsed =
        parse_project(discover_sources_from_paths(&paths).expect("sources should be discovered"))
            .expect("source should parse");
    let ir = render(&lower(&paths.source_dir, parsed).expect("source should lower"))
        .expect("source should render");
    let mut plan = PythonArtifactPlan::from_ir(&ir).expect("canonical plan should load");
    let terminals = plan.modules[0].declarations[0]
        .get_mut("terminals")
        .and_then(Value::as_array_mut)
        .expect("resource terminals should be present");
    terminals.push(terminals[0].clone());
    let diagnostics = emit(&config, &plan, &ir, &[]).expect_err("duplicate terminal must reject");
    assert!(diagnostics.iter().any(|diagnostic| {
        diagnostic
            .message
            .contains("resource terminal states must be unique")
    }));
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
    assert!(facade.contains("(_result).data == data"));
    let generation: serde_json::Value =
        serde_json::from_slice(bytes(&first.files, "generation.json"))
            .expect("generation record should be JSON");
    assert_eq!(generation["schema_version"], 5);
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
    let generation: serde_json::Value =
        serde_json::from_slice(bytes(&emitted.files, "generation.json"))
            .expect("generation record should be JSON");
    let unresolved = &generation["current"]["unresolved"][0];
    assert_eq!(unresolved["cott_symbol"], "app.run");
    assert_eq!(unresolved["kind"], "function");
    assert_eq!(
        unresolved["span"]
            .as_object()
            .expect("unresolved span should be an object")
            .keys()
            .collect::<Vec<_>>(),
        vec![
            "end_byte",
            "end_column",
            "end_line",
            "start_byte",
            "start_column",
            "start_line",
        ]
    );
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

#[test]
fn emits_rule_classes_and_facade_exports() {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(
        temp.path.join("src/app.cott"),
        r#"module app

rule BaseRule:
    doc """Base rule."""
    requires true

rule ChildRule(BaseRule):
    doc """Child rule."""
    override requires false
"#,
    )
    .expect("source should be writable");
    write_target_metadata(&temp.path);
    let (config, paths) = load_config_with_paths(&temp.path).expect("manifest should load");
    let parsed =
        parse_project(discover_sources_from_paths(&paths).expect("sources")).expect("parse");
    let ir = render(&lower(&paths.source_dir, parsed).expect("lower")).expect("render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("canonical plan should load");
    let emission = emit(&config, &plan, &ir, &[]).expect("rules should emit");

    let types_content = emission
        .files
        .get(&PathBuf::from("python/app_types.py"))
        .map(|b| std::str::from_utf8(b).unwrap())
        .expect("types file should exist");
    assert!(types_content.contains("class BaseRule:"));
    assert!(types_content.contains("class ChildRule(BaseRule):"));

    let facade_content = emission
        .files
        .get(&PathBuf::from("python/app.py"))
        .map(|b| std::str::from_utf8(b).unwrap())
        .expect("facade file should exist");
    assert!(facade_content.contains("\"BaseRule\""));
    assert!(facade_content.contains("\"ChildRule\""));
}

#[test]
fn emits_impl_class_with_locked_method_helper_and_provenance() {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(
        temp.path.join("src/app.cott"),
        r#"module app

external type Resource

trait Counter:
    fn advance(self, amount: I32) -> I32

impl CounterState for Counter:
    state:
        handle: Resource
        title: Str
        urgency: I32
        completed: Bool = false
        count: I32 = 0
    invariant self.count >= 0
    init(handle: Resource, title: Str, urgency: I32, count: I32):
        requires count >= 0
        ensures self.count == count
    fn advance(self, amount: I32) -> I32:
        modifies self.count
        ensures result == self.count
        ensures old(self.count) + amount == self.count
"#,
    )
    .expect("source should be writable");
    write_target_metadata(&temp.path);
    let (mut config, paths) = load_config_with_paths(&temp.path).expect("manifest should load");
    config.python.external_types.insert(
        "app.Resource".to_owned(),
        "vendor.resource:Resource".to_owned(),
    );
    let parsed =
        parse_project(discover_sources_from_paths(&paths).expect("sources")).expect("parse");
    let ir = render(&lower(&paths.source_dir, parsed).expect("lower")).expect("render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("canonical plan should load");
    let helper = b"def _cott_impl_CounterState_advance(self: CounterState, amount: int) -> int:\n    self.count += amount\n    return self.count\n";
    let binding = ResolvedBinding {
        module: "app".to_owned(),
        function: "advance".to_owned(),
        cott_symbol: "app.CounterState.advance".to_owned(),
        kind: PythonCallableKind::ImplMethod {
            concrete: "CounterState".to_owned(),
        },
        implementation_module: "_cott_impl.app.CounterState.advance".to_owned(),
        implementation_function: "_cott_impl_CounterState_advance".to_owned(),
        owner: BindingOwner::Agent,
        source: temp
            .path
            .join("python/_cott_impl/app/CounterState/advance.py"),
        generated_relative: PathBuf::from("_cott_impl/app/CounterState/advance.py"),
        bytes: helper.to_vec(),
        sha256: sha256_hex(helper),
    };
    let emission = emit(&config, &plan, &ir, &[binding]).expect("impl should emit");
    let facade = String::from_utf8_lossy(bytes(&emission.files, "python/app.py"));
    let stub = String::from_utf8_lossy(bytes(&emission.files, "stubs/app.pyi"));
    assert!(facade.contains("@final\nclass CounterState:"));
    assert!(facade.contains(
        "__slots__ = (\"handle\", \"title\", \"urgency\", \"completed\", \"count\", \"_cott_lock\",)"
    ));
    assert!(facade.contains(
        "    handle: Resource\n    title: str\n    urgency: I32\n    completed: bool\n    count: I32\n    __slots__"
    ));
    assert!(facade.contains("with self._cott_lock:"));
    assert!(facade.contains("_cott_old_count = self.count"));
    assert!(facade.contains("if self.handle is not _cott_old_handle:"));
    assert!(facade.contains("_cott_impl_CounterState_advance"));
    assert!(facade.contains("def advance(self: CounterState, amount: I32) -> I32:"));
    let init_ensure = "        if not (((self).count == count)):";
    let init_invariant = "        if not (((self).count >= 0)):";
    let method_invariant = "            if not (((self).count >= 0)):";
    assert_eq!(
        facade
            .lines()
            .filter(|line| *line == init_invariant)
            .count(),
        1,
        "init invariant must be inside __init__:\n{facade}"
    );
    assert_eq!(
        facade
            .lines()
            .filter(|line| *line == method_invariant)
            .count(),
        1,
        "method invariant must remain inside its lock:\n{facade}"
    );
    assert!(
        facade.find(init_ensure).unwrap() < facade.find(init_invariant).unwrap(),
        "init ensures must precede init invariants:\n{facade}"
    );
    assert!(stub.contains("@final\nclass CounterState:"));
    assert!(stub.contains(
        "    handle: Resource\n    title: str\n    urgency: I32\n    completed: bool\n    count: I32\n    def __init__"
    ));
    assert!(!stub.contains("_cott_lock"));
    assert!(stub.contains("def advance(self: CounterState, amount: I32) -> I32: ..."));
    let generation: serde_json::Value =
        serde_json::from_slice(bytes(&emission.files, "generation.json")).expect("generation JSON");
    let implementation = &generation["current"]["implementations"][0];
    assert_eq!(implementation["kind"], "impl_method");
    assert_eq!(implementation["concrete"], "CounterState");
    assert_eq!(implementation["method"], "advance");
    assert_eq!(implementation["callable_kind"], "sync");
    assert_eq!(
        implementation["selection"],
        serde_json::json!({"kind": "explicit", "trait_method": "app.Counter.advance"})
    );
    assert_eq!(
        generation["current"]["public_python_symbols"]["app"],
        serde_json::json!(["Counter", "CounterState", "Resource"])
    );
    assert!(
        generation["current"]["contract_surface"]["app"]["declarations"]
            .to_string()
            .contains("CounterState")
    );
    assert!(
        !generation["current"]["contract_surface"]["app"]["declarations"]
            .to_string()
            .contains("\"span\"")
    );
}

#[test]
fn rejects_resource_state_import_collision_before_rendering() {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(
        temp.path.join("src/lifecycle.cott"),
        r#"module lifecycle

resource Door:
    initial Open
    state Open
    state Closed
    terminal Closed
    transition Open -> Closed
"#,
    )
    .expect("resource source should be writable");
    fs::write(
        temp.path.join("src/other.cott"),
        r#"module other

enum Door:
    Open
"#,
    )
    .expect("other source should be writable");
    fs::write(
        temp.path.join("src/controller.cott"),
        r#"module controller
use lifecycle.{Door}

trait Controller:
    fn close(self) -> I32

impl DoorController for Controller:
    state:
        marker: other.Door
        door: Door
        count: I32 = 0
    init(marker: other.Door, door: Door):
        requires true
    fn close(self) -> I32:
        transitions self.door: Door.Open -> Door.Closed
        modifies self.count
        ensures self.marker == other.Door.Open
"#,
    )
    .expect("controller source should be writable");
    write_target_metadata(&temp.path);
    let (config, paths) = load_config_with_paths(&temp.path).expect("manifest should load");
    let parsed =
        parse_project(discover_sources_from_paths(&paths).expect("sources")).expect("parse");
    let ir = render(&lower(&paths.source_dir, parsed).expect("lower")).expect("render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("canonical plan should load");
    let helper = b"def _cott_impl_DoorController_close(self: DoorController) -> int:\n    self.count += 1\n    return self.count\n";
    let binding = ResolvedBinding {
        module: "controller".to_owned(),
        function: "close".to_owned(),
        cott_symbol: "controller.DoorController.close".to_owned(),
        kind: PythonCallableKind::ImplMethod {
            concrete: "DoorController".to_owned(),
        },
        implementation_module: "_cott_impl.controller.DoorController.close".to_owned(),
        implementation_function: "_cott_impl_DoorController_close".to_owned(),
        owner: BindingOwner::Agent,
        source: temp
            .path
            .join("python/_cott_impl/controller/DoorController/close.py"),
        generated_relative: PathBuf::from("_cott_impl/controller/DoorController/close.py"),
        bytes: helper.to_vec(),
        sha256: sha256_hex(helper),
    };
    let first = emit(&config, &plan, &ir, &[binding.clone()])
        .expect_err("resource state import collision must prevent rendering");
    let second = emit(&config, &plan, &ir, &[binding])
        .expect_err("resource state import collision must be deterministic");
    assert_eq!(first, second);
    assert!(
        first.iter().any(|diagnostic| diagnostic.message
            == "ambiguous cross-module Python import `Door_Open` from lifecycle, other"),
        "resource state collision must be reported: {first:#?}"
    );
}

#[test]
fn emits_cross_module_resource_transition_contracts() {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(
        temp.path.join("src/lifecycle.cott"),
        r#"module lifecycle

resource Door:
    initial Open
    state Open
    state Closed
    terminal Closed
    transition Open -> Closed
"#,
    )
    .expect("resource source should be writable");
    fs::write(
        temp.path.join("src/controller.cott"),
        r#"module controller
use lifecycle.{Door}

trait Controller:
    fn close(self) -> I32

impl DoorController for Controller:
    state:
        door: Door
        count: I32 = 0
    invariant self.count >= 0
    init(door: Door):
        requires true
    fn close(self) -> I32:
        transitions self.door: Door.Open -> Door.Closed
        modifies self.count
        ensures self.count == 1
"#,
    )
    .expect("controller source should be writable");
    write_target_metadata(&temp.path);
    let (config, paths) = load_config_with_paths(&temp.path).expect("manifest should load");
    let parsed =
        parse_project(discover_sources_from_paths(&paths).expect("sources")).expect("parse");
    let ir = render(&lower(&paths.source_dir, parsed).expect("lower")).expect("render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("canonical plan should load");
    let helper = b"from lifecycle_types import Door_Closed\n\ndef _cott_impl_DoorController_close(self: DoorController) -> int:\n    self.door = Door_Closed()\n    self.count = 1\n    return 1\n";
    let binding = ResolvedBinding {
        module: "controller".to_owned(),
        function: "close".to_owned(),
        cott_symbol: "controller.DoorController.close".to_owned(),
        kind: PythonCallableKind::ImplMethod {
            concrete: "DoorController".to_owned(),
        },
        implementation_module: "_cott_impl.controller.DoorController.close".to_owned(),
        implementation_function: "_cott_impl_DoorController_close".to_owned(),
        owner: BindingOwner::Agent,
        source: temp
            .path
            .join("python/_cott_impl/controller/DoorController/close.py"),
        generated_relative: PathBuf::from("_cott_impl/controller/DoorController/close.py"),
        bytes: helper.to_vec(),
        sha256: sha256_hex(helper),
    };
    let emission =
        emit(&config, &plan, &ir, &[binding.clone()]).expect("resource transition should emit");
    assert_eq!(
        emission.files,
        emit(&config, &plan, &ir, &[binding])
            .expect("repeat emission")
            .files,
        "resource transition emission must be byte-deterministic"
    );
    let facade = String::from_utf8_lossy(bytes(&emission.files, "python/controller.py"));
    let stub = String::from_utf8_lossy(bytes(&emission.files, "stubs/controller.pyi"));

    assert!(
        facade.contains("from lifecycle_types import Door, Door_Closed, Door_Open"),
        "facade must import the resource type and exact transition states:\n{facade}"
    );
    assert!(facade.contains("    door: Door"), "facade:\n{facade}");
    assert!(
        stub.contains("from lifecycle_types import Door, Door_Closed, Door_Open"),
        "stub must expose resource states:\n{stub}"
    );
    assert!(stub.contains("    door: Door"), "stub:\n{stub}");
    assert!(
        stub.contains("def close(self: DoorController) -> I32: ..."),
        "stub must expose the resolved method:\n{stub}"
    );

    let locked = facade
        .find("        with self._cott_lock:")
        .expect("method lock");
    let snapshot = facade
        .find("            _cott_old_door = self.door")
        .expect("resource snapshot");
    let abi = facade
        .find("            self.door = _cott_validate_abi(self.door, Door, path=\"$.door\")")
        .expect("resource ABI validation");
    let source = facade
        .find("            if _cott_old_door is not Door_Open():")
        .expect("exact transition source identity check");
    let target = facade
        .find("            if self.door is not Door_Closed():")
        .expect("exact transition target identity check");
    let ensures = facade
        .find("            if not (((self).count == 1)):")
        .expect("method ensures");
    let invariant = facade
        .find("            if not (((self).count >= 0)):")
        .expect("method invariant");
    assert!(
        locked < snapshot
            && snapshot < abi
            && abi < source
            && source < target
            && target < ensures
            && ensures < invariant,
        "resource transition checks must run under lock after ABI validation, before ensures and invariants:\n{facade}"
    );
    assert!(
        facade.contains(
            "raise CottContractViolation(\"resource transition source failed\", symbol=\"controller.DoorController.close\", phase=\"transitions\""
        ) && facade.contains(
            "raise CottContractViolation(\"resource transition target failed\", symbol=\"controller.DoorController.close\", phase=\"transitions\""
        ),
        "source and target must be mandatory transition checks:\n{facade}"
    );
}

#[test]
fn emits_option_nothing_state_default_with_zero_argument_constructor() {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(
        temp.path.join("src/app.cott"),
        r#"module app

trait Holder:
    fn value(self) -> Option[Any]

impl HolderState for Holder:
    state:
        value: Option[Any] = Option.Nothing
    fn value(self) -> Option[Any]:
        ensures Option.Nothing => true
"#,
    )
    .expect("source should be writable");
    write_target_metadata(&temp.path);
    let (config, paths) = load_config_with_paths(&temp.path).expect("manifest should load");
    let parsed =
        parse_project(discover_sources_from_paths(&paths).expect("sources")).expect("parse");
    let ir = render(&lower(&paths.source_dir, parsed).expect("lower")).expect("render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("canonical plan should load");
    let helper = b"def _cott_impl_HolderState_value(self: HolderState) -> Option[Any]:\n    return Nothing()\n";
    let binding = ResolvedBinding {
        module: "app".to_owned(),
        function: "value".to_owned(),
        cott_symbol: "app.HolderState.value".to_owned(),
        kind: PythonCallableKind::ImplMethod {
            concrete: "HolderState".to_owned(),
        },
        implementation_module: "_cott_impl.app.HolderState.value".to_owned(),
        implementation_function: "_cott_impl_HolderState_value".to_owned(),
        owner: BindingOwner::Agent,
        source: temp.path.join("python/_cott_impl/app/HolderState/value.py"),
        generated_relative: PathBuf::from("_cott_impl/app/HolderState/value.py"),
        bytes: helper.to_vec(),
        sha256: sha256_hex(helper),
    };
    let emission = emit(&config, &plan, &ir, &[binding]).expect("impl should emit");
    let facade = String::from_utf8_lossy(bytes(&emission.files, "python/app.py"));
    let stub = String::from_utf8_lossy(bytes(&emission.files, "stubs/app.pyi"));
    assert!(facade.contains(
        "def __init__(self) -> None:\n        self.value = _cott_validate_abi(Nothing(), Option[Any], path=\"$.value\")"
    ));
    assert!(stub.contains("def __init__(self) -> None: ..."));
}

#[test]
fn emits_manifest_projected_external_types_deterministically() {
    let sources = [
        (
            "providers.cott",
            r#"module providers

external type Remote
external type RemoteAgain
external type Class
"#,
        ),
        (
            "app.cott",
            r#"module app
use providers.{Remote}

alias Stream = Iterator[Generator[Any, Unknown, Remote]]

fn run(data: Iterator[Generator[Any, Unknown, Remote]]) -> Generator[Remote, Unknown, Any]
"#,
        ),
    ];
    let projections = [
        ("providers.Remote", "vendor.client:Remote.Inner"),
        ("providers.RemoteAgain", "vendor.client:Remote.Inner"),
        ("providers.Class", "module:Class"),
    ];
    let first =
        emit_sources_with_external_types_result(&sources, &projections).expect("valid projections");
    let second =
        emit_sources_with_external_types_result(&sources, &projections).expect("valid projections");
    assert_eq!(first, second);

    let provider_types = String::from_utf8_lossy(bytes(&first, "python/providers_types.py"));
    assert!(provider_types.contains("from vendor.client import Remote as _cott_external_Remote"));
    assert!(
        provider_types.contains("from vendor.client import Remote as _cott_external_RemoteAgain")
    );
    assert!(
        provider_types.contains(
            "Remote: TypeAlias = Annotated[_cott_external_Remote.Inner, CottExternal(\"vendor.client:Remote.Inner\")]"
        )
    );
    assert!(
        provider_types.contains(
            "RemoteAgain: TypeAlias = Annotated[_cott_external_RemoteAgain.Inner, CottExternal(\"vendor.client:Remote.Inner\")]"
        )
    );
    assert!(provider_types.contains("from module import Class as _cott_external_Class"));
    assert!(provider_types.contains(
        "Class: TypeAlias = Annotated[_cott_external_Class, CottExternal(\"module:Class\")]"
    ));

    let changed = emit_sources_with_external_types_result(
        &sources,
        &[
            ("providers.Remote", "vendor.client:Remote.Inner"),
            ("providers.RemoteAgain", "vendor.client:Remote.Inner"),
            ("providers.Class", "other.module:Class"),
        ],
    )
    .expect("valid changed projection");
    assert_ne!(
        bytes(&first, "python/providers_types.py"),
        bytes(&changed, "python/providers_types.py")
    );
    assert_eq!(
        bytes(&first, "ir/providers.json"),
        bytes(&changed, "ir/providers.json")
    );

    let app_types = String::from_utf8_lossy(bytes(&first, "python/app_types.py"));
    let facade = String::from_utf8_lossy(bytes(&first, "python/app.py"));
    let stub = String::from_utf8_lossy(bytes(&first, "stubs/app.pyi"));
    for output in [app_types.as_ref(), facade.as_ref(), stub.as_ref()] {
        assert_eq!(
            output
                .lines()
                .find(|line| *line == "from collections.abc import Generator, Iterator"),
            Some("from collections.abc import Generator, Iterator")
        );
        assert!(output.lines().any(|line| line.contains("Any")));
        assert!(output.contains("from providers_types import Remote"));
    }
}

#[test]
fn rejects_missing_stale_non_external_and_malformed_external_projections() {
    let external = [(
        "providers.cott",
        "module providers\n\nexternal type Remote\n",
    )];
    let missing = emit_sources_with_external_types_result(&external, &[])
        .expect_err("external declaration requires a projection");
    assert!(
        missing
            .iter()
            .any(|diagnostic| diagnostic.message.contains("has no Python projection"))
    );

    let stale = emit_sources_with_external_types_result(
        &external,
        &[("providers.Stale", "vendor.client:Remote")],
    )
    .expect_err("stale projection must fail");
    assert!(
        stale
            .iter()
            .any(|diagnostic| diagnostic.message.contains("is stale"))
    );

    let non_external = emit_sources_with_external_types_result(
        &[("providers.cott", "module providers\n\nalias Remote = I32\n")],
        &[("providers.Remote", "vendor.client:Remote")],
    )
    .expect_err("non-external projection must fail");
    assert!(
        non_external
            .iter()
            .any(|diagnostic| diagnostic.message.contains("is not an external type"))
    );

    let malformed = emit_sources_with_external_types_result(
        &external,
        &[("providers.Remote", "not a projection")],
    )
    .expect_err("malformed projection must fail");
    assert!(malformed.iter().any(|diagnostic| {
        diagnostic
            .message
            .contains("has malformed Python projection")
    }));
}

#[test]
fn emits_factory_annotations_from_concrete_facades() {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(
        temp.path.join("src/alpha.cott"),
        r#"module alpha

trait Alpha:
    fn value(self) -> I32

impl AlphaState for Alpha:
    state:
        value: I32
    init(value: I32):
        requires value >= 0
        ensures self.value == value
    fn value(self) -> I32:
        effects []
"#,
    )
    .expect("source should be writable");
    fs::write(
        temp.path.join("src/beta.cott"),
        r#"module beta

trait Beta:
    fn value(self) -> I32

impl BetaState for Beta:
    state:
        value: I32
    init(value: I32):
        requires value >= 0
        ensures self.value == value
    fn value(self) -> I32:
        effects []
"#,
    )
    .expect("source should be writable");
    fs::write(
        temp.path.join("src/app.cott"),
        r#"module app
use alpha.{AlphaState}
use beta.{BetaState}

trait App:
    fn value(self) -> I32

impl AppState for App:
    state:
        value: I32
    init(value: I32):
        requires value >= 0
        ensures self.value == value
    fn value(self) -> I32:
        effects []

alias AlphaFactory = Factory[AlphaState]

fn choose(
    local: Factory[AppState],
    beta: Factory[BetaState],
    alpha: AlphaFactory,
) -> Factory[AppState]
"#,
    )
    .expect("source should be writable");
    write_target_metadata(&temp.path);
    let (config, paths) = load_config_with_paths(&temp.path).expect("manifest should load");
    let parsed =
        parse_project(discover_sources_from_paths(&paths).expect("sources")).expect("parse");
    let ir = render(&lower(&paths.source_dir, parsed).expect("lower")).expect("render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("canonical plan should load");
    let helper =
        b"def choose(local: object, beta: object, alpha: object) -> object:\n    return local\n";
    let binding = ResolvedBinding {
        module: "app".to_owned(),
        function: "choose".to_owned(),
        cott_symbol: "app.choose".to_owned(),
        kind: PythonCallableKind::Function,
        implementation_module: "_cott_impl.app.choose".to_owned(),
        implementation_function: "choose".to_owned(),
        owner: BindingOwner::Agent,
        source: temp.path.join("python/_cott_impl/app/choose.py"),
        generated_relative: PathBuf::from("_cott_impl/app/choose.py"),
        bytes: helper.to_vec(),
        sha256: sha256_hex(helper),
    };
    let emission = emit(&config, &plan, &ir, &[binding]).expect("Factory should emit");
    let app_types = String::from_utf8_lossy(bytes(&emission.files, "python/app_types.py"));
    let facade = String::from_utf8_lossy(bytes(&emission.files, "python/app.py"));
    let stub = String::from_utf8_lossy(bytes(&emission.files, "stubs/app.pyi"));
    let alpha_stub = String::from_utf8_lossy(bytes(&emission.files, "stubs/alpha.pyi"));

    assert!(app_types.contains("from alpha import AlphaState\nfrom beta import BetaState\n"));
    assert!(app_types.contains("AlphaFactory: TypeAlias = type[AlphaState]"));
    for output in [facade.as_ref(), stub.as_ref()] {
        assert!(output.contains("from alpha import AlphaState\nfrom beta import BetaState\n"));
        assert!(!output.contains("from alpha_types import AlphaState"));
        assert!(!output.contains("from beta_types import BetaState"));
    }
    assert!(
        facade.contains(
            "def choose(local: type[AppState], beta: type[BetaState], alpha: type[AlphaState]) -> type[AppState]:"
        ),
        "{facade}"
    );
    assert!(
        stub.contains(
            "def choose(local: type[AppState], beta: type[BetaState], alpha: type[AlphaState]) -> type[AppState]: ..."
        ),
        "{stub}"
    );
    assert!(stub.contains("class AppState:"));
    assert!(stub.contains("def __init__(self, value: I32) -> None: ..."));
    assert!(alpha_stub.contains("class AlphaState:"));
    assert!(alpha_stub.contains("def __init__(self, value: I32) -> None: ..."));
}

#[test]
fn emits_fixed_tuple_array_and_buffer_abi() {
    let files = emit_sources(&[(
        "fixed.cott",
        r#"module fixed

const PAIR: Tuple[U8,U16] = Tuple(1, 2)
const VALUES: Array[U8,2] = Array(3, 4)
const BYTES: Buffer[2] = Buffer("00ff")
"#,
    )]);
    let types = String::from_utf8(bytes(&files, "python/fixed_types.py").to_vec())
        .expect("types are UTF-8");
    let stub = String::from_utf8(bytes(&files, "stubs/fixed.pyi").to_vec()).expect("stub is UTF-8");
    for annotation in [
        "PAIR: Final[tuple[U8, U16]] = (1, 2)",
        "VALUES: Final[CottArray[U8, Literal[2]]] = CottArray(values=(3, 4))",
        "BYTES: Final[CottBuffer[Literal[2]]] = CottBuffer(data=bytes.fromhex(\"00ff\"))",
    ] {
        assert!(types.contains(annotation), "{types}");
    }
    assert!(!types.contains("CottTuple2"), "{types}");
    assert!(!stub.contains("CottTuple2"), "{stub}");
    assert!(
        stub.contains("from fixed_types import BYTES as BYTES, PAIR as PAIR, VALUES as VALUES"),
        "{stub}"
    );
}

#[test]
fn concretizes_generic_trait_defaults_for_impl_abi() {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(
        temp.path.join("src/app.cott"),
        r#"module app

trait Reader[T]:
    fn read(self, value: T) -> T = app.default_read
    fn label(self) -> Unit

fn default_read[T](receiver: Reader[T], value: T) -> T

impl ReaderState for Reader[I32]:
    fn label(self) -> Unit:
        ensures true
"#,
    )
    .expect("source should be writable");
    write_target_metadata(&temp.path);
    let (config, paths) = load_config_with_paths(&temp.path).expect("manifest should load");
    let parsed =
        parse_project(discover_sources_from_paths(&paths).expect("sources should be discovered"))
            .expect("source should parse");
    let ir = render(&lower(&paths.source_dir, parsed).expect("source should lower"))
        .expect("source should render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("canonical plan should load");
    let implementation = b"def _cott_impl_default_read(receiver: object, value: object) -> object:\n    return value\n";
    let binding = ResolvedBinding {
        module: "app".to_owned(),
        function: "default_read".to_owned(),
        cott_symbol: "app.default_read".to_owned(),
        kind: PythonCallableKind::Function,
        implementation_module: "_cott_impl.app.default_read".to_owned(),
        implementation_function: "_cott_impl_default_read".to_owned(),
        owner: BindingOwner::Agent,
        source: temp.path.join("python/_cott_impl/app/default_read.py"),
        generated_relative: PathBuf::from("_cott_impl/app/default_read.py"),
        bytes: implementation.to_vec(),
        sha256: sha256_hex(implementation),
    };

    let emission = emit(&config, &plan, &ir, &[binding]).expect("default should emit");
    let facade = String::from_utf8_lossy(bytes(&emission.files, "python/app.py"));
    let stub = String::from_utf8_lossy(bytes(&emission.files, "stubs/app.pyi"));
    assert!(
        facade.contains("def read(self: ReaderState, value: I32) -> I32:"),
        "{facade}"
    );
    assert!(
        stub.contains("def read(self: ReaderState, value: I32) -> I32: ..."),
        "{stub}"
    );
    assert!(
        !facade.contains("def read(self: ReaderState, value: T)"),
        "{facade}"
    );
    assert!(
        !stub.contains("def read(self: ReaderState, value: T)"),
        "{stub}"
    );
}

#[test]
fn emits_async_free_function_facade_stub_and_provenance() {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest");
    fs::create_dir_all(temp.path.join("src")).expect("source");
    fs::write(
        temp.path.join("src/app.cott"),
        "module app\n\nasync fn run(value: I32) -> I32\n",
    )
    .expect("source");
    write_target_metadata(&temp.path);
    let (config, paths) = load_config_with_paths(&temp.path).expect("config");
    let parsed =
        parse_project(discover_sources_from_paths(&paths).expect("sources")).expect("parse");
    let ir = render(&lower(&paths.source_dir, parsed).expect("lower")).expect("render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("plan");
    let implementation = b"async def run(value: int) -> int:\n    return value\n";
    let binding = ResolvedBinding {
        module: "app".to_owned(),
        function: "run".to_owned(),
        cott_symbol: "app.run".to_owned(),
        kind: PythonCallableKind::AsyncFunction,
        implementation_module: "_cott_impl.app.run".to_owned(),
        implementation_function: "run".to_owned(),
        owner: BindingOwner::Agent,
        source: temp.path.join("python/_cott_impl/app/run.py"),
        generated_relative: PathBuf::from("_cott_impl/app/run.py"),
        bytes: implementation.to_vec(),
        sha256: sha256_hex(implementation),
    };
    let emission = emit(&config, &plan, &ir, &[binding]).expect("async emission");
    let facade = String::from_utf8_lossy(bytes(&emission.files, "python/app.py"));
    let stub = String::from_utf8_lossy(bytes(&emission.files, "stubs/app.pyi"));
    let generation: serde_json::Value =
        serde_json::from_slice(bytes(&emission.files, "generation.json")).expect("generation");
    assert!(facade.contains("async def run(value: I32) -> I32:"));
    assert!(facade.contains("_result = await _implementation(value)"));
    assert!(stub.contains("async def run(value: I32) -> I32: ..."));
    assert_eq!(
        generation["current"]["implementations"][0]["kind"],
        "async_function"
    );
    assert_eq!(
        generation["current"]["implementations"][0]["callable_kind"],
        "async"
    );
}

#[test]
fn emits_async_impl_methods_with_reentrant_lock_and_finalization() {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest");
    fs::create_dir_all(temp.path.join("src")).expect("source");
    fs::write(
        temp.path.join("src/app.cott"),
        "module app\n\ntrait Counter:\n    async fn advance(self, amount: I32) -> I32\n\nimpl CounterState for Counter:\n    state:\n        count: I32 = 0\n        stable: Bool = true\n    async fn advance(self, amount: I32) -> I32:\n        modifies self.count\n",
    )
    .expect("source");
    write_target_metadata(&temp.path);
    let (config, paths) = load_config_with_paths(&temp.path).expect("config");
    let parsed =
        parse_project(discover_sources_from_paths(&paths).expect("sources")).expect("parse");
    let ir = render(&lower(&paths.source_dir, parsed).expect("lower")).expect("render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("plan");
    let implementation = b"async def _cott_impl_CounterState_advance(self: CounterState, amount: int) -> int:\n    self.count += amount\n    return self.count\n";
    let binding = ResolvedBinding {
        module: "app".to_owned(),
        function: "advance".to_owned(),
        cott_symbol: "app.CounterState.advance".to_owned(),
        kind: PythonCallableKind::AsyncImplMethod {
            concrete: "CounterState".to_owned(),
        },
        implementation_module: "_cott_impl.app.CounterState.advance".to_owned(),
        implementation_function: "_cott_impl_CounterState_advance".to_owned(),
        owner: BindingOwner::Agent,
        source: temp
            .path
            .join("python/_cott_impl/app/CounterState/advance.py"),
        generated_relative: PathBuf::from("_cott_impl/app/CounterState/advance.py"),
        bytes: implementation.to_vec(),
        sha256: sha256_hex(implementation),
    };
    let emission = emit(&config, &plan, &ir, &[binding]).expect("async impl emission");
    let facade = String::from_utf8_lossy(bytes(&emission.files, "python/app.py"));
    let types = String::from_utf8_lossy(bytes(&emission.files, "python/app_types.py"));
    let stub = String::from_utf8_lossy(bytes(&emission.files, "stubs/app.pyi"));
    let generation: serde_json::Value =
        serde_json::from_slice(bytes(&emission.files, "generation.json")).expect("generation");
    assert!(types.contains("async def advance(self, amount: I32) -> I32:"));
    assert!(facade.contains("async def advance(self: CounterState, amount: I32) -> I32:"));
    assert!(facade.contains("async with self._cott_lock:"));
    assert!(facade.contains("_result = await _implementation(self, amount)"));
    assert!(facade.contains("except BaseException as _error:"));
    assert!(facade.contains("if isinstance(_error, _asyncio.CancelledError):"));
    assert!(facade.contains("validator=_cott_validate_abi"));
    assert!(facade.contains("exceptional frame clause failed"));
    assert!(facade.contains("if self.stable is not _cott_old_stable:"));
    assert!(stub.contains("async def advance(self: CounterState, amount: I32) -> I32: ..."));
    assert_eq!(
        generation["current"]["implementations"][0]["kind"],
        "async_impl_method"
    );
    assert_eq!(
        generation["current"]["implementations"][0]["callable_kind"],
        "async"
    );
    assert_eq!(
        generation["current"]["implementations"][0]["selection"],
        serde_json::json!({"kind": "explicit", "trait_method": "app.Counter.advance"})
    );
}

#[test]
fn qualifies_hidden_associated_typevars_by_canonical_trait_identity() {
    let files = emit_sources(&[
        (
            "alpha.cott",
            "module alpha\n\ntrait Reader:\n    type Item\n    fn read(self) -> Reader.Item\n",
        ),
        (
            "beta.cott",
            "module beta\n\ntrait Reader:\n    type Item\n    fn read(self) -> Reader.Item\n",
        ),
    ]);
    let alpha = String::from_utf8_lossy(bytes(&files, "python/alpha_types.py"));
    let beta = String::from_utf8_lossy(bytes(&files, "python/beta_types.py"));
    assert!(alpha.contains("_cott_alpha_Reader_alpha_Reader_Item = TypeVar"));
    assert!(beta.contains("_cott_beta_Reader_beta_Reader_Item = TypeVar"));
    assert!(!alpha.contains("_cott_beta_Reader_beta_Reader_Item"));
}

#[test]
fn emits_specialization_target_instead_of_trait_default() {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source should be writable");
    fs::write(
        temp.path.join("src/app.cott"),
        r#"module app


fn default_read(receiver: Reader, value: I32) -> I32
fn specialized_read(receiver: ReaderState, value: I32) -> I32

trait Reader:
    fn read(self, value: I32) -> I32 = app.default_read
    fn label(self) -> Unit

specialize ReaderState for Reader:
    read = app.specialized_read

impl ReaderState for Reader:
    fn label(self) -> Unit:
        ensures true
"#,
    )
    .expect("source should be writable");
    write_target_metadata(&temp.path);
    let (config, paths) = load_config_with_paths(&temp.path).expect("manifest should load");
    let parsed =
        parse_project(discover_sources_from_paths(&paths).expect("sources should be discovered"))
            .expect("source should parse");
    let ir = render(&lower(&paths.source_dir, parsed).expect("source should lower"))
        .expect("source should render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("canonical plan should load");
    let method = plan
        .callables()
        .into_iter()
        .find(|callable| callable.cott_symbol == "app.ReaderState.read")
        .expect("specialized dispatch slot should be callable");
    assert_eq!(method.declaration["selected"]["origin"], "specialization");
    assert_eq!(
        method.declaration["selected"]["function"]["verified_facade"],
        "app.specialized_read"
    );
    let implementation =
        b"def specialized_read(receiver: object, value: int) -> int:\n    return value\n";
    let binding = ResolvedBinding {
        module: "app".to_owned(),
        function: "specialized_read".to_owned(),
        cott_symbol: "app.specialized_read".to_owned(),
        kind: PythonCallableKind::Function,
        implementation_module: "_cott_impl.app.specialized_read".to_owned(),
        implementation_function: "specialized_read".to_owned(),
        owner: BindingOwner::Agent,
        source: temp.path.join("python/_cott_impl/app/specialized_read.py"),
        generated_relative: PathBuf::from("_cott_impl/app/specialized_read.py"),
        bytes: implementation.to_vec(),
        sha256: sha256_hex(implementation),
    };
    let emission = emit(&config, &plan, &ir, &[binding]).expect("specialization should emit");
    let facade = String::from_utf8_lossy(bytes(&emission.files, "python/app.py"));
    assert!(
        facade.contains("_cott_default_ReaderState_read = specialized_read"),
        "{facade}"
    );
    assert!(
        !facade.contains("_cott_default_ReaderState_read = default_read"),
        "{facade}"
    );
}

#[test]
fn inherited_cross_module_default_imports_parent_markers_and_dispatch() {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source should be writable");
    fs::write(
        temp.path.join("src/parent.cott"),
        r#"module parent

trait Parent:
    fn read(self, value: I32) -> I32 = parent.default_read

fn default_read(receiver: Parent, value: I32) -> I32
"#,
    )
    .expect("parent source should be writable");
    fs::write(
        temp.path.join("src/child.cott"),
        r#"module child

use parent.Parent

trait Child for Parent:
    fn label(self) -> Unit

impl ChildState for Child:
    fn label(self) -> Unit:
        ensures true
"#,
    )
    .expect("child source should be writable");
    write_target_metadata(&temp.path);
    let (config, paths) = load_config_with_paths(&temp.path).expect("manifest should load");
    let parsed =
        parse_project(discover_sources_from_paths(&paths).expect("sources should be discovered"))
            .expect("sources should parse");
    let ir = render(&lower(&paths.source_dir, parsed).expect("sources should lower"))
        .expect("sources should render");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("canonical plan should load");
    let implementation =
        b"def default_read(receiver: object, value: int) -> int:\n    return value\n";
    let binding = ResolvedBinding {
        module: "parent".to_owned(),
        function: "default_read".to_owned(),
        cott_symbol: "parent.default_read".to_owned(),
        kind: PythonCallableKind::Function,
        implementation_module: "_cott_impl.parent.default_read".to_owned(),
        implementation_function: "default_read".to_owned(),
        owner: BindingOwner::Agent,
        source: temp.path.join("python/_cott_impl/parent/default_read.py"),
        generated_relative: PathBuf::from("_cott_impl/parent/default_read.py"),
        bytes: implementation.to_vec(),
        sha256: sha256_hex(implementation),
    };
    let emission = emit(&config, &plan, &ir, &[binding]).expect("inherited default should emit");
    let facade = String::from_utf8_lossy(bytes(&emission.files, "python/child.py"));
    assert!(
        facade.contains("from parent_types import Parent"),
        "{facade}"
    );
    assert!(
        facade.contains("from parent import default_read as _cott_default_ChildState_read"),
        "{facade}"
    );
    assert!(
        facade.contains("_cott_traits = (Child, Parent,)"),
        "{facade}"
    );
}

#[test]
fn emits_bounded_distinct_associated_projections_and_imports_them() {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(
        temp.path.join("src/provider.cott"),
        r#"module provider

trait Comparable:
    fn compare(self, other: I32) -> I32

trait Serializable:
    fn serialize(self) -> I32

trait Reader:
    type Item: Comparable + Serializable
    fn read(self) -> Reader.Item
"#,
    )
    .expect("source should be writable");
    fs::write(
        temp.path.join("src/consumer.cott"),
        r#"module consumer
use provider.Reader

struct Named[T]:
    value: T

fn pair[T: Reader, U: Reader, A, B](left: T.Item, right: U.Item, named_a: T.Item, named_b: U.Item) -> Tuple[T.Item,U.Item]
"#,
    )
    .expect("source should be writable");
    write_target_metadata(&temp.path);
    let (config, paths) = load_config_with_paths(&temp.path).expect("manifest should load");
    let parsed =
        parse_project(discover_sources_from_paths(&paths).expect("sources should be discovered"))
            .expect("source should parse");
    let mut ir = render(&lower(&paths.source_dir, parsed).expect("source should lower"))
        .expect("source should render");
    let named_a_base = serde_json::json!({
        "args": [{"kind": "type", "type": {"kind": "type_parameter", "name": "A"}}],
        "kind": "named",
        "name": "consumer.Named",
    });
    let named_b_base = serde_json::json!({
        "args": [{"kind": "type", "type": {"kind": "type_parameter", "name": "B"}}],
        "kind": "named",
        "name": "consumer.Named",
    });
    let module = ir
        .modules
        .iter_mut()
        .find(|module| module.module.as_string() == "consumer")
        .expect("consumer module must exist");
    let mut value: Value = serde_json::from_slice(&module.bytes).expect("consumer IR must be JSON");
    let parameters = value["declarations"]
        .as_array_mut()
        .expect("consumer declarations must be an array")
        .iter_mut()
        .find(|declaration| declaration["name"] == "consumer.pair")
        .expect("pair declaration must exist")["parameters"]
        .as_array_mut()
        .expect("pair parameters must be an array");
    for (name, base) in [("named_a", &named_a_base), ("named_b", &named_b_base)] {
        parameters
            .iter_mut()
            .find(|parameter| parameter["name"] == name)
            .unwrap_or_else(|| panic!("{name} parameter must exist"))["type"] = serde_json::json!({
            "base": base,
            "kind": "associated_projection",
            "name": "Item",
            "trait": "provider.Reader",
        });
    }
    module.bytes = serde_json::to_vec(&value).expect("consumer IR should serialize");
    module.bytes.push(b'\n');
    let plan = PythonArtifactPlan::from_ir(&ir).expect("canonical plan should load");
    let implementation = b"def pair(left: object, right: object, named_a: object, named_b: object) -> object:\n    return (left, right)\n";
    let binding = ResolvedBinding {
        module: "consumer".to_owned(),
        function: "pair".to_owned(),
        cott_symbol: "consumer.pair".to_owned(),
        kind: PythonCallableKind::Function,
        implementation_module: "_cott_impl.consumer.pair".to_owned(),
        implementation_function: "pair".to_owned(),
        owner: BindingOwner::Agent,
        source: temp.path.join("python/_cott_impl/consumer/pair.py"),
        generated_relative: PathBuf::from("_cott_impl/consumer/pair.py"),
        bytes: implementation.to_vec(),
        sha256: sha256_hex(implementation),
    };
    let emission = emit(&config, &plan, &ir, &[binding]).expect("projections should emit");
    let provider_types =
        String::from_utf8_lossy(bytes(&emission.files, "python/provider_types.py"));
    let types = String::from_utf8_lossy(bytes(&emission.files, "python/consumer_types.py"));
    let facade = String::from_utf8_lossy(bytes(&emission.files, "python/consumer.py"));
    let stub = String::from_utf8_lossy(bytes(&emission.files, "stubs/consumer.pyi"));
    let associated_item = "_cott_provider_Reader_Item";
    let t_item = format!(
        "{associated_item}_{}",
        sha256_hex(br#"{"kind":"type_parameter","name":"T"}"#)
    );
    let u_item = format!(
        "{associated_item}_{}",
        sha256_hex(br#"{"kind":"type_parameter","name":"U"}"#)
    );
    let named_a_item = format!(
        "{associated_item}_{}",
        sha256_hex(&serde_json::to_vec(&named_a_base).expect("named A base should serialize"))
    );
    let named_b_item = format!(
        "{associated_item}_{}",
        sha256_hex(&serde_json::to_vec(&named_b_base).expect("named B base should serialize"))
    );
    let associated_declaration = "_cott_provider_Reader_provider_Reader_Item";
    let composite = format!(
        "class _cott_{associated_declaration}_Bounds(Comparable, Serializable, Protocol):\n    pass"
    );
    assert!(provider_types.contains(&composite), "{provider_types}");
    assert!(
        provider_types.contains(&format!(
            "{associated_declaration} = TypeVar(\"{associated_declaration}\", bound=_cott_{associated_declaration}_Bounds)"
        )),
        "{provider_types}"
    );
    assert!(
        types.contains("from provider_types import Comparable, Reader, Serializable"),
        "{types}"
    );
    for projection in [&t_item, &u_item, &named_a_item, &named_b_item] {
        assert!(
            types.contains(&format!(
                "class _cott_{projection}_Bounds(Comparable, Serializable, Protocol)"
            )),
            "{types}"
        );
        assert!(
            types.contains(&format!(
                "{projection} = TypeVar(\"{projection}\", bound=_cott_{projection}_Bounds)"
            )),
            "{types}"
        );
    }
    let signature = format!(
        "def pair(left: {t_item}, right: {u_item}, named_a: {named_a_item}, named_b: {named_b_item}) -> tuple[{t_item}, {u_item}]"
    );
    for output in [facade.as_ref(), stub.as_ref()] {
        assert!(output.contains("from consumer_types import"), "{output}");
        for projection in [&t_item, &u_item, &named_a_item, &named_b_item] {
            assert!(output.contains(projection), "{output}");
        }
        assert!(output.contains(&signature), "{output}");
    }
}

#[test]
fn imports_cross_module_methodless_closure_ancestor_markers() {
    let files = emit_sources(&[
        (
            "marker.cott",
            "module marker\n\ntrait Marker:\n    type Tag\n",
        ),
        (
            "parent.cott",
            "module parent\nuse marker.Marker\n\ntrait Parent for Marker:\n",
        ),
        (
            "child.cott",
            r#"module child
use parent.Parent

trait Child for Parent:
    fn read(self) -> I32

impl ChildState for Child:
    type Tag = I32
    fn read(self) -> I32:
        ensures true
"#,
        ),
    ]);
    let facade = String::from_utf8_lossy(bytes(&files, "python/child.py"));
    let stub = String::from_utf8_lossy(bytes(&files, "stubs/child.pyi"));
    assert!(
        facade.contains("from marker_types import Marker") && facade.contains("_cott_traits"),
        "{facade}"
    );
    assert!(stub.contains("class ChildState:"), "{stub}");
}

#[test]
fn preserves_cross_module_generic_inherited_trait_specs() {
    let files = emit_sources(&[
        (
            "parent.cott",
            r#"module parent

trait Parent[T]:
    fn parent(self, value: T) -> T
"#,
        ),
        (
            "child.cott",
            r#"module child
use parent.Parent

trait Child[U] for Parent[U]:
    fn child(self, value: U) -> U

impl ChildState for Child[I32]:
    fn parent(self, value: I32) -> I32:
        ensures result == value
    fn child(self, value: I32) -> I32:
        ensures result == value
"#,
        ),
    ]);
    let facade = String::from_utf8_lossy(bytes(&files, "python/child.py"));
    assert!(facade.contains("from child_types import Child"), "{facade}");
    assert!(
        facade.contains("from parent_types import Parent"),
        "{facade}"
    );
    assert!(
        facade.contains("_cott_traits = (Child, Parent,)")
            && facade.contains("_cott_trait_specs = (Child[I32], Parent[I32],)"),
        "{facade}"
    );
    assert!(
        !facade.contains("Child[U]") && !facade.contains("Parent[U]"),
        "{facade}"
    );
}

#[test]
fn imports_staged_local_traits_and_associated_bounds() {
    if Command::new("python3").arg("--version").output().is_err() {
        return;
    }
    let files = emit_sources(&[(
        "ordered.cott",
        r#"module ordered

trait Child for Parent:
    fn child(self) -> I32

trait Uses[T: Marker + Serializable]:
    fn apply(self, value: T) -> T

trait SelfBound[T: SelfBound[T]]:
    fn recurse(self, value: T) -> T

trait Left[T: Right[T]]:
    fn left(self, value: T) -> T

trait Right[T: Left[T]]:
    fn right(self, value: T) -> T

trait Comparable:
    fn compare(self, other: I32) -> I32

trait Marker:
    fn mark(self) -> I32

trait Serializable:
    fn serialize(self) -> I32

trait Parent:
    type One: Comparable
    type Both: Comparable + Serializable
    fn one(self) -> Parent.One
    fn both(self) -> Parent.Both
"#,
    )]);
    let temp = TempDir::new();
    for (relative, content) in &files {
        let path = temp.path.join(relative);
        fs::create_dir_all(path.parent().expect("generated artifact parent"))
            .expect("generated artifact parent should be writable");
        fs::write(path, content).expect("generated artifact should be writable");
    }
    let output = Command::new("python3")
        .arg("-c")
        .arg("import ordered, ordered_types; assert ordered_types.Parent in ordered_types.Child.__bases__")
        .current_dir(temp.path.join("python"))
        .output()
        .expect("python3 should import generated artifacts");
    assert!(
        output.status.success(),
        "generated staged trait imports failed:\n{}\n{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn preserves_empty_enum_hashes_and_rejects_payload_enum_hashes() {
    if Command::new("python3").arg("--version").output().is_err() {
        return;
    }
    let files = emit_sources(&[(
        "tree.cott",
        r#"module tree

enum Tree:
    Empty
    Branch(next: Option[Tree])
"#,
    )]);
    let types = String::from_utf8_lossy(bytes(&files, "python/tree_types.py"));
    assert!(
        types.contains("class Tree_Empty:\n    pass"),
        "payload-free variant lost its generated hash:\n{types}"
    );
    assert!(
        types.contains("class Tree_Branch:\n    __hash__ = None"),
        "payload variant must be unhashable:\n{types}"
    );
    let temp = TempDir::new();
    for (relative, content) in &files {
        let path = temp.path.join(relative);
        fs::create_dir_all(path.parent().expect("generated artifact parent"))
            .expect("generated artifact parent should be writable");
        fs::write(path, content).expect("generated artifact should be writable");
    }
    let output = Command::new("python3")
        .arg("-c")
        .arg("from tree_types import Tree_Branch, Tree_Empty; assert hash(Tree_Empty()); assert Tree_Branch.__hash__ is None")
        .current_dir(temp.path.join("python"))
        .output()
        .expect("python3 should import generated enum artifacts");
    assert!(
        output.status.success(),
        "generated enum hash behavior failed:\n{}\n{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}
