use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

use cott::binding::{resolve_bindings, resolve_implementations, validate_candidate};
use cott::compiler::{SourceFile, parse_project};
use cott::hir::lower;
use cott::ir::render;
use cott::manifest::ProjectConfig;
use cott::project::{ProjectPaths, load_config_with_paths};
use cott::provenance::{AgentRun, AgentStatus, GenerationRecord, GenerationSnapshot, StreamDigest};
use cott::python::artifact_plan::{PythonArtifactPlan, PythonCallableKind};

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
    fixture_sources(&[("api/service.cott", source)])
}

fn fixture_sources(sources: &[(&str, &str)]) -> Fixture {
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
    let parsed = parse_project(
        sources
            .iter()
            .map(|(path, source)| SourceFile::new(PathBuf::from(path), *source)),
    )
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

fn impl_fixture() -> Fixture {
    fixture(
        r#"module api.service

trait Reader:
    fn read(self, amount: I32) -> I32

trait Writer:
    fn read(self, amount: I32) -> I32

impl ReaderState for Reader:
    fn read(self, amount: I32) -> I32:
        ensures result == amount

impl WriterState for Writer:
    fn read(self, amount: I32) -> I32:
        ensures result == amount
"#,
    )
}

fn factory_fixture() -> Fixture {
    fixture_sources(&[
        (
            "api/models.cott",
            r#"module api.models

trait Order:
    fn id(self) -> I32

impl OrderState for Order:
    fn id(self) -> I32:
        ensures result >= 0
"#,
        ),
        (
            "api/service.cott",
            r#"module api.service

use api.models.{OrderState}

fn run(make: Factory[OrderState]) -> Unit
"#,
        ),
    ])
}

fn record_agent_provenance(fixture: &Fixture, symbol: &str, source: &PathBuf, bytes: &[u8]) {
    let content_hash = format!("sha256:{}", cott::hash::sha256_hex(bytes));
    let generated_relative = source
        .strip_prefix(&fixture.paths.python_source_dir)
        .expect("agent source is rooted at the Python source");
    let concrete = source
        .parent()
        .and_then(|path| path.file_name())
        .and_then(|name| name.to_str())
        .expect("agent method source has a concrete parent");
    let method = source
        .file_stem()
        .and_then(|name| name.to_str())
        .expect("agent method source has a name");
    let runtime_module = generated_relative
        .with_extension("")
        .to_string_lossy()
        .replace('/', ".");
    let mut record = GenerationRecord {
        schema_version: 1,
        current: GenerationSnapshot {
            generation_id: String::new(),
            verified: false,
            inputs: serde_json::json!({}),
            tools: serde_json::json!({}),
            ir: serde_json::json!({}),
            contract_surface: serde_json::json!({}),
            public_python_symbols: serde_json::json!({}),
            implementations: serde_json::json!([{
                "cott_symbol": symbol,
                "kind": "impl_method",
                "concrete": concrete,
                "method": method,
                "owner": "agent",
                "python_symbol": format!("{runtime_module}:_cott_impl_{concrete}_{method}"),
                "source_origin": source
                    .strip_prefix(&fixture.paths.root)
                    .expect("agent source is rooted at the fixture")
                    .to_string_lossy()
                    .replace('\\', "/"),
                "runtime_origin": format!(
                    "{}/{}",
                    std::path::Path::new(&fixture.config.python.generated)
                        .file_name()
                        .expect("generated root has a final component")
                        .to_string_lossy(),
                    generated_relative.to_string_lossy().replace('\\', "/")
                ),
                "content_hash": content_hash,
            }]),
            dependencies: serde_json::json!([]),
            managed_files: BTreeMap::new(),
            unresolved: Vec::new(),
            verification: serde_json::Value::Null,
            agent_runs: vec![AgentRun {
                symbol: symbol.to_owned(),
                adapter: "test".to_owned(),
                adapter_version: "1".to_owned(),
                argv_template: Vec::new(),
                executable: "test".to_owned(),
                executable_hash: "sha256:test".to_owned(),
                prompt_hash: "sha256:test".to_owned(),
                implementation_hash: content_hash.clone(),
                environment_names: Vec::new(),
                duration_ms: 0,
                status: AgentStatus {
                    exit_code: Some(0),
                    signal: None,
                    timed_out: false,
                    cancelled: false,
                },
                stdout: StreamDigest {
                    bytes: 0,
                    sha256: "sha256:test".to_owned(),
                    truncated: false,
                },
                stderr: StreamDigest {
                    bytes: 0,
                    sha256: "sha256:test".to_owned(),
                    truncated: false,
                },
            }],
        },
        last_verified: None,
    };
    record
        .current
        .compute_generation_id()
        .expect("test provenance identity must compute");
    let path = fixture
        .paths
        .generated_dir
        .parent()
        .expect("generated Python directory has a parent")
        .join("generation.json");
    fs::create_dir_all(path.parent().expect("generation record has a parent")).unwrap();
    fs::write(
        path,
        record
            .canonical_bytes()
            .expect("test provenance must serialize"),
    )
    .unwrap();
}

#[test]
fn accepts_cott_bindings_manifest_source_namespace() {
    let mut fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    fixture.config.python.implementations.insert(
        "api.service.run".to_owned(),
        "cott_bindings.api.service.run:run".to_owned(),
    );
    let path = fixture
        .paths
        .python_source_dir
        .join("cott_bindings/api/service/run.py");
    fs::create_dir_all(path.parent().expect("binding has parent")).unwrap();
    fs::write(&path, b"def run() -> object:\n    return None\n").unwrap();

    let bindings = resolve_bindings(&fixture.config, &fixture.paths, &fixture.plan)
        .expect("binding must resolve");
    assert_eq!(bindings.len(), 1);
    assert_eq!(bindings[0].module, "api.service");
    assert_eq!(bindings[0].function, "run");
    assert_eq!(bindings[0].cott_symbol, "api.service.run");
    assert_eq!(bindings[0].kind, PythonCallableKind::Function);
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
        "cott_bindings.api.service.run:run".to_owned(),
    );
    let path = fixture
        .paths
        .python_source_dir
        .join("cott_bindings/api/service/run.py");
    fs::create_dir_all(path.parent().expect("binding has parent")).unwrap();
    fs::write(&path, b"def run() -> object:\n    return None\n").unwrap();

    let resolution = resolve_implementations(&fixture.config, &fixture.paths, &fixture.plan)
        .expect("missing durable source is an unresolved result");
    assert_eq!(resolution.resolved.len(), 1);
    assert_eq!(resolution.unresolved.len(), 1);
    assert_eq!(resolution.unresolved[0].module, "api.service");
    assert_eq!(resolution.unresolved[0].function, "missing");
    assert_eq!(resolution.unresolved[0].cott_symbol, "api.service.missing");
    assert_eq!(resolution.unresolved[0].kind, PythonCallableKind::Function);
    assert_eq!(
        resolution.unresolved[0].expected_implementation_function,
        "missing"
    );
    assert_eq!(
        resolution.unresolved[0].source,
        fixture
            .paths
            .python_source_dir
            .join("_cott_impl/api/service/missing.py")
    );
}

#[test]
fn unresolved_impl_methods_have_distinct_canonical_symbols_and_nested_sources() {
    let fixture = impl_fixture();

    let resolution = resolve_implementations(&fixture.config, &fixture.paths, &fixture.plan)
        .expect("absent impl methods are unresolved");
    assert_eq!(
        resolution
            .unresolved
            .iter()
            .map(|binding| (binding.cott_symbol.as_str(), binding.source.clone()))
            .collect::<Vec<_>>(),
        [
            (
                "api.service.ReaderState.read",
                fixture
                    .paths
                    .python_source_dir
                    .join("_cott_impl/api/service/ReaderState/read.py"),
            ),
            (
                "api.service.WriterState.read",
                fixture
                    .paths
                    .python_source_dir
                    .join("_cott_impl/api/service/WriterState/read.py"),
            ),
        ]
    );
    assert_eq!(
        resolution.unresolved[0].kind,
        PythonCallableKind::ImplMethod {
            concrete: "ReaderState".to_owned()
        }
    );
    assert_eq!(
        resolution.unresolved[0].expected_implementation_function,
        "_cott_impl_ReaderState_read"
    );
}

#[test]
fn resolves_provenance_backed_impl_methods_to_their_helper() {
    let fixture = impl_fixture();
    let path = fixture
        .paths
        .python_source_dir
        .join("_cott_impl/api/service/ReaderState/read.py");
    let bytes = b"from api.service import ReaderState\n\ndef _cott_impl_ReaderState_read(self: ReaderState, amount: int) -> int:\n    return amount\n";
    fs::create_dir_all(path.parent().expect("impl method has a parent")).unwrap();
    fs::write(&path, bytes).unwrap();
    record_agent_provenance(&fixture, "api.service.ReaderState.read", &path, bytes);
    let record: serde_json::Value = serde_json::from_slice(
        &fs::read(
            fixture
                .paths
                .generated_dir
                .parent()
                .expect("generated Python directory has a parent")
                .join("generation.json"),
        )
        .expect("method generation record"),
    )
    .expect("method generation record is JSON");
    let implementation = &record["current"]["implementations"][0];
    assert_eq!(implementation["kind"], "impl_method");
    assert_eq!(implementation["concrete"], "ReaderState");
    assert_eq!(implementation["method"], "read");
    assert_eq!(
        implementation["python_symbol"],
        "_cott_impl.api.service.ReaderState.read:_cott_impl_ReaderState_read"
    );
    assert_eq!(
        implementation["source_origin"],
        "python/_cott_impl/api/service/ReaderState/read.py"
    );
    assert_eq!(
        implementation["runtime_origin"],
        "python/_cott_impl/api/service/ReaderState/read.py"
    );
    assert_eq!(
        implementation["content_hash"],
        format!("sha256:{}", cott::hash::sha256_hex(bytes))
    );

    let resolution = resolve_implementations(&fixture.config, &fixture.paths, &fixture.plan)
        .expect("provenance-backed impl method must resolve");
    assert_eq!(resolution.resolved.len(), 1);
    assert_eq!(resolution.unresolved.len(), 1);
    let binding = &resolution.resolved[0];
    assert_eq!(
        binding.kind,
        PythonCallableKind::ImplMethod {
            concrete: "ReaderState".to_owned()
        }
    );
    assert_eq!(binding.cott_symbol, "api.service.ReaderState.read");
    assert_eq!(binding.source, path);
    assert_eq!(
        binding.generated_relative,
        PathBuf::from("_cott_impl/api/service/ReaderState/read.py")
    );
    assert_eq!(
        binding.implementation_module,
        "_cott_impl.api.service.ReaderState.read"
    );
    assert_eq!(
        binding.implementation_function,
        "_cott_impl_ReaderState_read"
    );
    assert_eq!(binding.owner, cott::binding::BindingOwner::Agent);
}
#[test]
fn rejects_malformed_impl_method_provenance_records() {
    let fixture = impl_fixture();
    let path = fixture
        .paths
        .python_source_dir
        .join("_cott_impl/api/service/ReaderState/read.py");
    let bytes = b"from api.service import ReaderState\n\ndef _cott_impl_ReaderState_read(self: ReaderState, amount: int) -> int:\n    return amount\n";
    fs::create_dir_all(path.parent().expect("impl method has a parent")).unwrap();
    fs::write(&path, bytes).unwrap();
    record_agent_provenance(&fixture, "api.service.ReaderState.read", &path, bytes);
    let generation = fixture
        .paths
        .generated_dir
        .parent()
        .expect("generated Python directory has a parent")
        .join("generation.json");
    let record: serde_json::Value =
        serde_json::from_slice(&fs::read(&generation).expect("method generation record"))
            .expect("method generation record is JSON");
    for missing in ["kind", "concrete", "method"] {
        let mut incomplete = record.clone();
        incomplete["current"]["implementations"][0]
            .as_object_mut()
            .expect("implementation is an object")
            .remove(missing);

        assert!(
            GenerationRecord::parse(
                &serde_json::to_vec(&incomplete).expect("malformed provenance serializes")
            )
            .is_err(),
            "generation provenance must reject an impl method record missing `{missing}`"
        );
    }
    let mut mismatched = record.clone();
    mismatched["current"]["implementations"][0]["method"] = serde_json::json!("other");
    assert!(
        GenerationRecord::parse(
            &serde_json::to_vec(&mismatched).expect("mismatched provenance serializes")
        )
        .is_err(),
        "generation provenance must reject a method record whose symbol does not match"
    );
}

#[test]
fn rejects_manifest_bindings_for_impl_methods() {
    let mut fixture = impl_fixture();
    fixture.config.python.implementations.insert(
        "api.service.ReaderState.read".to_owned(),
        "cott_bindings.api.service.reader:read".to_owned(),
    );

    resolve_implementations(&fixture.config, &fixture.paths, &fixture.plan)
        .expect_err("impl methods must never be manifest-bindable");
}

#[test]
fn reports_stale_nested_impl_method_sources() {
    let fixture = impl_fixture();
    let stale = fixture
        .paths
        .python_source_dir
        .join("_cott_impl/api/service/ReaderState/removed.py");
    fs::create_dir_all(stale.parent().expect("stale method has a parent")).unwrap();
    fs::write(&stale, b"def removed() -> object:\n    return None\n").unwrap();

    let resolution = resolve_implementations(&fixture.config, &fixture.paths, &fixture.plan)
        .expect("unresolved methods do not make stale-source detection fail");
    assert_eq!(resolution.stale, [stale]);
}

#[test]
fn validates_impl_method_private_helpers_and_rejects_public_functions() {
    let fixture = impl_fixture();
    let valid = b"from api.service import ReaderState\n\ndef _normalize(value: int) -> int:\n    return value * 2\n\ndef _cott_impl_ReaderState_read(self: ReaderState, amount: int) -> int:\n    return _normalize(amount) // 2\n";
    validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "api.service.ReaderState.read",
        valid,
    )
    .expect("impl helper may contain a typed private top-level helper");

    let cases: &[(&[u8], &str)] = &[
        (
            b"from api.service import ReaderState\n\ndef _cott_impl_ReaderState_read(self: ReaderState | None, amount: int) -> int:\n    return amount\n",
            "must begin with `self: ReaderState`",
        ),
        (
            b"from api.service import ReaderState\n\ndef _cott_impl_ReaderState_read(self, amount: int) -> int:\n    return amount\n",
            "must begin with `self: ReaderState`",
        ),
        (
            b"class ReaderState:\n    pass\n\ndef _cott_impl_ReaderState_read(self: ReaderState, amount: int) -> int:\n    return amount\n",
            "class definitions are not allowed",
        ),
        (
            b"from api.service import ReaderState\n\ndef extra() -> None:\n    return None\n\ndef _cott_impl_ReaderState_read(self: ReaderState, amount: int) -> int:\n    return amount\n",
            "must have a single private",
        ),
    ];
    for (invalid, expected) in cases {
        let error = validate_candidate(
            &fixture.config,
            &fixture.paths,
            &fixture.plan,
            "api.service.ReaderState.read",
            invalid,
        )
        .expect_err("impl candidate must have only the exact helper signature");
        assert!(error.contains(expected), "{error}");
    }
}

#[test]
fn rejects_impl_concrete_imports_outside_its_exact_facade() {
    let fixture = impl_fixture();
    let cases: &[(&[u8], &str)] = &[
        (
            b"from api.service_types import ReaderState\n\ndef _cott_impl_ReaderState_read(self: ReaderState, amount: int) -> int:\n    return amount\n",
            "impl helper concrete `ReaderState` must be imported from facade `api.service`, not generated types `api.service_types`",
        ),
        (
            b"from api.service import ReaderState as State\n\ndef _cott_impl_ReaderState_read(self: State, amount: int) -> int:\n    return amount\n",
            "impl helper concrete `ReaderState` must be imported from facade `api.service` without an alias",
        ),
        (
            b"from api import ReaderState\n\ndef _cott_impl_ReaderState_read(self: ReaderState, amount: int) -> int:\n    return amount\n",
            "impl helper concrete `ReaderState` must be imported from facade `api.service`, not `api`",
        ),
        (
            b"def _cott_impl_ReaderState_read(self: ReaderState, amount: int) -> int:\n    return amount\n",
            "impl helper concrete `ReaderState` must be imported from facade `api.service`",
        ),
    ];

    for (source, expected) in cases {
        let error = validate_candidate(
            &fixture.config,
            &fixture.paths,
            &fixture.plan,
            "api.service.ReaderState.read",
            source,
        )
        .expect_err("impl helper must import its concrete from its exact facade");
        assert!(error.contains(expected), "{error}");
    }
}

#[test]
fn allows_factory_concrete_imports_from_generated_facades() {
    let fixture = factory_fixture();
    let valid = b"from api.models import OrderState\n\ndef run(make: type[OrderState]) -> object:\n    return None\n";
    validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "api.service.run",
        valid,
    )
    .expect("Factory may import its concrete exactly from the owning facade");
    let valid_module = b"from api.models import OrderState\nimport api.models\n\ndef run(make: type[OrderState]) -> object:\n    return api.models.OrderState\n";
    validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "api.service.run",
        valid_module,
    )
    .expect("Factory may reference its exact owning facade module");
    let valid_support =
        b"from api.service import OrderState\n\ndef run(make: type[OrderState]) -> object:\n    return OrderState\n";
    validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "api.service.run",
        valid_support,
    )
    .expect("Factory concrete may be imported through another generated facade");

    let cases: &[(&[u8], &str)] = &[
        (
            b"from api.models import OrderState as State\n\ndef run(make: type[State]) -> object:\n    return None\n",
            "factory concrete `OrderState` must be imported from facade `api.models` without an alias",
        ),
        (
            b"from api import OrderState\n\ndef run(make: type[OrderState]) -> object:\n    return None\n",
            "factory concrete `OrderState` must be imported from facade `api.models`, not `api`",
        ),
        (
            b"from api.models_types import OrderState\n\ndef run(make: type[OrderState]) -> object:\n    return None\n",
            "factory concrete `OrderState` must be imported from facade `api.models`, not generated types `api.models_types`",
        ),
    ];
    for (source, expected) in cases {
        let error = validate_candidate(
            &fixture.config,
            &fixture.paths,
            &fixture.plan,
            "api.service.run",
            source,
        )
        .expect_err("Factory facade imports must name only its exact concrete");
        assert!(error.contains(expected), "{error}");
    }
}

#[test]
fn candidate_validation_public_api_uses_only_the_canonical_plan() {
    let fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "run",
        b"from typing import Final\n\n_enabled: Final[bool] = True\n_count: Final[int] = 1\n_ratio: Final[float] = 1.5\n_label: Final[str] = \"cott\"\n_payload: Final[bytes] = b\"cott\"\n\ndef _normalize(value: object) -> object:\n    return value\n\ndef run() -> object:\n    return _normalize(None)\n",
    )
    .expect("canonical plan candidate may contain typed private helpers and constants");
}

#[test]
fn rejects_extra_top_level_definitions_for_public_functions() {
    let fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    let cases: &[(&[u8], &str)] = &[
        (
            b"def extra() -> None:\n    return None\n\ndef run() -> object:\n    return None\n",
            "must have a single private",
        ),
        (
            b"class Run:\n    pass\n\ndef run() -> object:\n    return None\n",
            "class definitions are not allowed",
        ),
    ];

    for (source, expected) in cases {
        let error = validate_candidate(
            &fixture.config,
            &fixture.paths,
            &fixture.plan,
            "api.service.run",
            source,
        )
        .expect_err("public candidate must have only its exact top-level function");
        assert!(error.contains(expected), "{error}");
    }
}

#[test]
fn rejects_invalid_private_helpers_and_extra_contract_functions() {
    let fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    let cases: &[(&[u8], &str)] = &[
        (
            b"def normalize(value: int) -> int:\n    return value\n\ndef run() -> object:\n    return None\n",
            "must have a single private",
        ),
        (
            b"def _cott_x(value: int) -> int:\n    return value\n\ndef run() -> object:\n    return None\n",
            "must have a single private",
        ),
        (
            b"def __x(value: int) -> int:\n    return value\n\ndef run() -> object:\n    return None\n",
            "must have a single private",
        ),
        (
            b"def _normalize(value: int) -> int:\n    return value\n\ndef _normalize(value: int) -> int:\n    return value\n\ndef run() -> object:\n    return None\n",
            "must not define duplicate function '_normalize'",
        ),
        (
            b"def _normalize(value) -> int:\n    return value\n\ndef run() -> object:\n    return None\n",
            "parameter `value` must have one concrete annotation",
        ),
        (
            b"def _normalize(value: int):\n    return value\n\ndef run() -> object:\n    return None\n",
            "function '_normalize' must have a return annotation",
        ),
        (
            b"@decorator\ndef _normalize(value: int) -> int:\n    return value\n\ndef run() -> object:\n    return None\n",
            "function '_normalize' must not be decorated",
        ),
        (
            b"_state: list[int] = []\n\ndef run() -> object:\n    return None\n",
            "executable top-level statement",
        ),
        (
            b"from typing import Final\n\nvisible: Final[int] = 1\n\ndef run() -> object:\n    return None\n",
            "executable top-level statement",
        ),
        (
            b"def run() -> object:\n    return None\n\ndef run() -> object:\n    return None\n",
            "must define exactly one top-level function 'run'",
        ),
    ];

    for (source, expected) in cases {
        let error = validate_candidate(
            &fixture.config,
            &fixture.paths,
            &fixture.plan,
            "api.service.run",
            source,
        )
        .expect_err("candidate must preserve the closed implementation contract");
        assert!(error.contains(expected), "{error}");
    }
}

#[test]
fn allows_ellipsis_in_a_local_tuple_annotation() {
    let fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "run",
        b"def run() -> object:\n    values: tuple[int, ...] = ()\n    return None\n",
    )
    .expect("type ellipsis is not a placeholder");
}

#[test]
fn rejects_an_ellipsis_placeholder_statement() {
    let fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    let error = validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "run",
        b"def run() -> object:\n    ...\n",
    )
    .expect_err("placeholder must fail");
    assert!(error.contains("ellipsis placeholder"));
}

#[test]
fn allows_public_function_imports_from_the_exact_canonical_facade() {
    let mut fixture = fixture("module api.service\n\nfn helper() -> Unit\nfn run() -> Unit\n");
    let source = b"from api.service import helper\n\ndef run() -> object:\n    return helper()\n";

    validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "api.service.run",
        source,
    )
    .expect("agent candidate may import a declared sibling function");
    let module_source =
        b"import api.service as service\n\ndef run() -> object:\n    return service.helper()\n";
    validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "api.service.run",
        module_source,
    )
    .expect("agent candidate may import an exact generated facade module");
    let parent_source =
        b"from api import service as service\n\ndef run() -> object:\n    return service.helper()\n";
    validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "api.service.run",
        parent_source,
    )
    .expect("agent candidate may import an exact facade from its parent package");
    let value_source =
        b"from api.service import Count, LIMIT\n\ndef run() -> object:\n    return (Count, LIMIT)\n";
    validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "api.service.run",
        value_source,
    )
    .expect("generated facade values may be imported directly");

    fixture.config.python.implementations.insert(
        "api.service.run".to_owned(),
        "cott_bindings.api.service.run:run".to_owned(),
    );
    let path = fixture
        .paths
        .python_source_dir
        .join("cott_bindings/api/service/run.py");
    fs::create_dir_all(path.parent().unwrap()).unwrap();
    fs::write(&path, source).unwrap();
    let resolution = resolve_implementations(&fixture.config, &fixture.paths, &fixture.plan)
        .expect("manifest binding may import a declared sibling function");
    assert_eq!(resolution.resolved.len(), 1);
    assert_eq!(resolution.resolved[0].function, "run");
}

#[test]
fn rejects_aliased_private_and_non_facade_imports() {
    let fixture = fixture(
        "module api.service\n\nalias Count = I32\nconst LIMIT: I32 = 1\nfn helper() -> Unit\nfn run() -> Unit\n",
    );
    let cases: &[(&[u8], &str)] = &[
        (
            b"from api.service import helper as renamed\n\ndef run() -> object:\n    return renamed()\n",
            "import aliases are not allowed",
        ),
        (
            b"from api import helper\n\ndef run() -> object:\n    return None\n",
            "project-local import 'api' is not allowed",
        ),
        (
            b"from .service import helper\n\ndef run() -> object:\n    return helper()\n",
            "relative imports are not allowed",
        ),
        (
            b"from api.service import *\n\ndef run() -> object:\n    return None\n",
            "star imports are not allowed",
        ),
        (
            b"from api.service import _cott_load\n\ndef run() -> object:\n    return None\n",
            "private generated facade import 'api.service._cott_load' is not allowed",
        ),
        (
            b"from _cott_impl.api.service.run import run\n\ndef run() -> object:\n    return None\n",
            "project-local import '_cott_impl.api.service.run' is not allowed",
        ),
        (
            b"from cott_bindings.api.service.helper import helper\n\ndef run() -> object:\n    return helper()\n",
            "project-local import 'cott_bindings.api.service.helper' is not allowed",
        ),
    ];
    for (source, expected) in cases {
        let error = validate_candidate(
            &fixture.config,
            &fixture.paths,
            &fixture.plan,
            "api.service.run",
            source,
        )
        .unwrap_err();
        assert!(error.contains(expected), "{error}");
    }
}

#[test]
fn manifest_binding_precedes_the_agent_path() {
    let mut fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    fixture.config.python.implementations.insert(
        "api.service.run".to_owned(),
        "cott_bindings.api.service.run:execute".to_owned(),
    );
    let manifest_path = fixture
        .paths
        .python_source_dir
        .join("cott_bindings/api/service/run.py");
    fs::create_dir_all(manifest_path.parent().unwrap()).unwrap();
    let bytes = b"def execute() -> object:\n    return None\n";
    fs::write(&manifest_path, bytes).unwrap();
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
    assert_eq!(
        resolution.resolved[0].implementation_module,
        "cott_bindings.api.service.run"
    );
    assert_eq!(resolution.resolved[0].implementation_function, "execute");
    assert_eq!(
        resolution.resolved[0].owner,
        cott::binding::BindingOwner::Manifest
    );
    assert_eq!(
        resolution.resolved[0].generated_relative,
        PathBuf::from("_cott_impl/api/service/run.py")
    );
    assert_eq!(resolution.resolved[0].bytes, bytes);
    assert_eq!(resolution.resolved[0].sha256, cott::hash::sha256_hex(bytes));
}

#[test]
fn reports_unreferenced_durable_implementations_as_stale() {
    let mut fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    fixture.config.python.implementations.insert(
        "api.service.run".to_owned(),
        "cott_bindings.api.service.run:run".to_owned(),
    );
    let run = fixture
        .paths
        .python_source_dir
        .join("cott_bindings/api/service/run.py");
    let stale = fixture
        .paths
        .python_source_dir
        .join("_cott_impl/api/service/old.py");
    fs::create_dir_all(run.parent().unwrap()).unwrap();
    fs::create_dir_all(stale.parent().unwrap()).unwrap();
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
        "cott_bindings.api.service.removed:execute".to_owned(),
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

#[test]
fn rejects_reserved_and_non_authored_manifest_module_roots() {
    let mut fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    let lockfile = fixture.root.join("uv.lock");
    fs::write(
        &lockfile,
        "[[package]]\nname = \"demo\"\ndependencies = [{ name = \"locked-package\" }]\n\n[[package]]\nname = \"locked-package\"\n",
    )
    .unwrap();
    fixture.paths.lockfile = Some(lockfile);

    let cases = [
        (
            "_cott_impl.api.service.run:run",
            "root `_cott_impl` is reserved",
        ),
        (
            "cott_runtime.binding:run",
            "root `cott_runtime` is reserved",
        ),
        ("api.service:run", "root `api` is a public Cott facade"),
        (
            "api.service_types:run",
            "generated `*_types` modules cannot own",
        ),
        (
            "pathlib.binding:run",
            "root `pathlib` is reserved for the Python standard library",
        ),
        (
            "locked_package.binding:run",
            "root `locked_package` is selected as a locked distribution",
        ),
        ("adapters.service:run", "must be below `cott_bindings`"),
    ];
    for (target, expected) in cases {
        fixture
            .config
            .python
            .implementations
            .insert("api.service.run".to_owned(), target.to_owned());
        let diagnostics =
            resolve_implementations(&fixture.config, &fixture.paths, &fixture.plan).unwrap_err();
        assert!(
            diagnostics[0].message.contains(expected),
            "{}",
            diagnostics[0].message
        );
    }
}

#[test]
fn nested_opaque_functions_remain_agent_eligible() {
    let fixture = fixture(
        r#"module api.service

fn transform(values: List[Opaque["payload"]]) -> Iterator[Opaque["result"]]
"#,
    );

    let resolution = resolve_implementations(&fixture.config, &fixture.paths, &fixture.plan)
        .expect("nested Opaque must not require a manifest binding");
    assert_eq!(
        resolution
            .unresolved
            .iter()
            .map(|binding| binding.cott_symbol.as_str())
            .collect::<Vec<_>>(),
        ["api.service.transform"]
    );
}

#[test]
fn accepts_generator_implementations_with_yield() {
    let fixture = fixture("module api.service\n\nfn stream() -> Generator[I32, Unknown, Unit]\n");

    validate_candidate(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        "api.service.stream",
        b"from collections.abc import Generator\n\ndef stream() -> Generator[int, object, object]:\n    yield 1\n",
    )
    .expect("generator implementations may yield");
}

#[test]
fn retains_unsafe_source_rejections() {
    let fixture = fixture("module api.service\n\nfn run() -> Unit\n");
    let cases: &[(&[u8], &str)] = &[
        (
            b"async def run() -> object:\n    return None\n",
            "async implementation is not allowed",
        ),
        (
            b"def run() -> object:\n    return __import__(\"pathlib\")\n",
            "dynamic imports are not allowed",
        ),
        (
            b"def run() -> object:\n    return __file__\n",
            "runtime reflection `__file__` is not allowed",
        ),
        (
            b"from pathlib import *\n\ndef run() -> object:\n    return None\n",
            "star imports are not allowed",
        ),
        (
            b"from .service import helper\n\ndef run() -> object:\n    return helper()\n",
            "relative imports are not allowed",
        ),
        (
            b"import unlocked_package\n\ndef run() -> object:\n    return None\n",
            "external distribution import 'unlocked_package' is not selected in uv.lock",
        ),
    ];

    for (source, expected) in cases {
        let error = validate_candidate(
            &fixture.config,
            &fixture.paths,
            &fixture.plan,
            "api.service.run",
            source,
        )
        .expect_err("unsafe candidate must fail");
        assert!(error.contains(expected), "{error}");
    }
}
