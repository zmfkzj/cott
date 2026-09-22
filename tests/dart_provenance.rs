use std::collections::{BTreeMap, BTreeSet};
use std::path::{Path, PathBuf};

use cott::compiler::{SourceFile, parse_project};
use cott::dart::DartOwner;
use cott::dart::provenance::{
    DART_GENERATION_SCHEMA_VERSION, DART_RUNTIME_ABI_VERSION, DartBindingRecord,
    DartGenerationRecord, DartGenerationSnapshot,
};
use cott::hir::lower;
use cott::ir::{load, render};
use cott::kotlin::KotlinOwner;
use cott::kotlin::provenance::{
    KOTLIN_GENERATION_SCHEMA_VERSION, KOTLIN_RUNTIME_ABI_VERSION, KotlinBindingRecord,
    KotlinGenerationRecord, KotlinGenerationSnapshot,
};
use cott::provenance::{AgentRun, AgentStatus, SemanticCoverage, StreamDigest};
use serde_json::{Value, json};

#[path = "support/snapshot.rs"]
mod snapshot_wire;

fn digest(byte: char) -> String {
    format!("sha256:{}", byte.to_string().repeat(64))
}

fn empty_dependencies() -> Value {
    json!({
        "schema_version": 1,
        "pubspec_hash": null,
        "lockfile_hash": null,
        "packages": []
    })
}

fn snapshot() -> DartGenerationSnapshot {
    let mut snapshot = DartGenerationSnapshot {
        target: "dart".to_owned(),
        generation_id: String::new(),
        verified: false,
        compiler_version: env!("CARGO_PKG_VERSION").to_owned(),
        canonical_ir_schema: cott::provenance::CANONICAL_IR_SCHEMA_VERSION,
        runtime_abi: DART_RUNTIME_ABI_VERSION,
        project_name: "sample_app".to_owned(),
        project_version: "1.2.3".to_owned(),
        inputs: BTreeMap::from([
            ("cott.toml".to_owned(), digest('a')),
            ("src/api.cott".to_owned(), digest('b')),
        ]),
        tools: json!({
            "compiler": {"version": env!("CARGO_PKG_VERSION")},
            "dart": {"version": "3.13.3"},
            "runtime": {"abi": DART_RUNTIME_ABI_VERSION}
        }),
        ir: BTreeMap::from([("api".to_owned(), digest('c'))]),
        contract_surface: json!({"api": {"declarations": []}}),
        public_symbols: BTreeMap::from([(
            "api".to_owned(),
            vec!["Payload".to_owned(), "run".to_owned()],
        )]),
        implementations: vec![DartBindingRecord {
            cott_symbol: "api.run".to_owned(),
            target_symbol: "bindings/api.dart:_run".to_owned(),
            source_origin: "dart/bindings/api.dart".to_owned(),
            runtime_origin: "dart/lib/src/cott_impl/api/run.dart".to_owned(),
            content_hash: digest('d'),
            owner: DartOwner::Manifest,
        }],
        dependencies: empty_dependencies(),
        managed_files: BTreeMap::from([
            ("dart/lib/modules/api.dart".to_owned(), digest('e')),
            (
                "dart/lib/src/cott_impl/api/run.dart".to_owned(),
                digest('d'),
            ),
        ]),
        unresolved: Vec::new(),
        verification: Value::Null,
        semantic_coverage: SemanticCoverage::default(),
        agent_runs: Vec::new(),
    };
    snapshot
        .compute_generation_id()
        .expect("fixture snapshot must have a valid identity");
    snapshot
}

fn record() -> DartGenerationRecord {
    DartGenerationRecord {
        schema_version: DART_GENERATION_SCHEMA_VERSION,
        current: snapshot(),
        last_verified: None,
    }
}

fn serialized(value: &Value) -> Vec<u8> {
    snapshot_wire::bytes(value)
}

fn agent_run() -> AgentRun {
    AgentRun {
        symbol: "api.run".to_owned(),
        adapter: "codex".to_owned(),
        adapter_version: "1.0.0".to_owned(),
        argv_template: vec!["codex".to_owned(), "{prompt}".to_owned()],
        executable: "/usr/bin/codex".to_owned(),
        executable_hash: digest('1'),
        prompt_hash: digest('2'),
        implementation_hash: digest('d'),
        environment_names: vec!["HOME".to_owned(), "PATH".to_owned()],
        duration_ms: 10,
        status: AgentStatus {
            exit_code: Some(0),
            signal: None,
            timed_out: false,
            cancelled: false,
        },
        stdout: StreamDigest {
            bytes: 0,
            sha256: digest('3'),
            truncated: false,
        },
        stderr: StreamDigest {
            bytes: 0,
            sha256: digest('4'),
            truncated: false,
        },
    }
}

fn agent_snapshot() -> DartGenerationSnapshot {
    let mut snapshot = snapshot();
    snapshot.implementations[0].owner = DartOwner::Agent;
    snapshot.tools["cott_intent"] = json!({
        "version": 1,
        "hashes": {"api.run": digest('5')}
    });
    snapshot.agent_runs = vec![agent_run()];
    snapshot
        .compute_generation_id()
        .expect("agent fixture must have authentic source provenance");
    snapshot
}

fn kotlin_record_bytes() -> Vec<u8> {
    let mut current = KotlinGenerationSnapshot {
        target: "kotlin".to_owned(),
        generation_id: String::new(),
        verified: false,
        compiler_version: env!("CARGO_PKG_VERSION").to_owned(),
        canonical_ir_schema: cott::provenance::CANONICAL_IR_SCHEMA_VERSION,
        runtime_abi: KOTLIN_RUNTIME_ABI_VERSION,
        project_name: "sample-app".to_owned(),
        project_version: "1.2.3".to_owned(),
        inputs: BTreeMap::from([("cott.toml".to_owned(), digest('a'))]),
        tools: json!({}),
        ir: BTreeMap::from([("api".to_owned(), digest('b'))]),
        contract_surface: json!({"api": {"declarations": []}}),
        public_symbols: BTreeMap::new(),
        implementations: vec![KotlinBindingRecord {
            cott_symbol: "api.run".to_owned(),
            target_symbol: "cott_impl.api.run".to_owned(),
            source_origin: "kotlin/cott_impl/api/run.kt".to_owned(),
            runtime_origin: "kotlin/cott_impl/api/run.kt".to_owned(),
            content_hash: digest('c'),
            owner: KotlinOwner::Manifest,
        }],
        managed_files: BTreeMap::new(),
        unresolved: Vec::new(),
        verification: Value::Null,
        semantic_coverage: SemanticCoverage::default(),
        agent_runs: Vec::new(),
    };
    current
        .compute_generation_id()
        .expect("Kotlin fixture must have a valid identity");
    KotlinGenerationRecord {
        schema_version: KOTLIN_GENERATION_SCHEMA_VERSION,
        current,
        last_verified: None,
    }
    .canonical_bytes()
    .expect("Kotlin fixture must serialize")
}

#[test]
fn dart_record_round_trips_canonical_bytes_and_rejects_other_backends() {
    let record = record();
    let bytes = record
        .canonical_bytes()
        .expect("valid Dart generation record must serialize");
    assert_eq!(bytes.last(), Some(&b'\n'));
    let parsed =
        DartGenerationRecord::parse(&bytes).expect("canonical Dart generation bytes must parse");
    assert_eq!(parsed, record);
    assert_eq!(parsed.canonical_bytes().unwrap(), bytes);

    assert!(DartGenerationRecord::parse(&kotlin_record_bytes()).is_err());
    let mut kotlin_shaped = snapshot_wire::expand(serde_json::to_value(&record).unwrap());
    kotlin_shaped["current"]["target"] = json!("kotlin");
    kotlin_shaped["current"]["public_kotlin_symbols"] = json!({"api": ["run"]});
    assert!(DartGenerationRecord::parse(&serialized(&kotlin_shaped)).is_err());
}

#[test]
fn snapshot_references_deduplicate_certification_but_not_verification_history() {
    let pending = agent_snapshot();
    let mut certified = pending.clone();
    certified.verified = true;
    certified.verification = json!({"status": "passed"});
    certified.compute_generation_id().unwrap();
    assert_eq!(pending.generation_id, certified.generation_id);

    let certified_record = DartGenerationRecord {
        schema_version: DART_GENERATION_SCHEMA_VERSION,
        current: certified.clone(),
        last_verified: Some(certified.clone()),
    };
    let certified_wire = serde_json::to_value(&certified_record).unwrap();
    assert_eq!(certified_wire["current"], certified_wire["last_verified"]);
    assert_eq!(certified_wire["snapshots"].as_object().unwrap().len(), 1);
    assert_eq!(
        DartGenerationRecord::parse(&serde_json::to_vec(&certified_wire).unwrap()).unwrap(),
        certified_record
    );

    let pending_record = DartGenerationRecord {
        schema_version: DART_GENERATION_SCHEMA_VERSION,
        current: pending,
        last_verified: Some(certified),
    };
    let wire = serde_json::to_value(&pending_record).unwrap();
    assert_ne!(wire["current"], wire["last_verified"]);
    assert_eq!(wire["snapshots"].as_object().unwrap().len(), 2);
    assert_eq!(
        DartGenerationRecord::parse(&serde_json::to_vec(&wire).unwrap()).unwrap(),
        pending_record
    );

    for field in ["agent_runs", "verification"] {
        let mut tampered = wire.clone();
        let reference = tampered["last_verified"].as_str().unwrap().to_owned();
        if field == "agent_runs" {
            tampered["snapshots"][&reference]["agent_runs"][0]["duration_ms"] = json!(11);
        } else {
            tampered["snapshots"][&reference]["verification"]["status"] = json!("tampered");
        }
        assert!(
            DartGenerationRecord::parse(&serde_json::to_vec(&tampered).unwrap()).is_err(),
            "{field} changes must invalidate the snapshot reference even when generation_id is unchanged"
        );
    }
}

#[test]
fn certified_snapshots_require_exact_verification_evidence() {
    let mut current = snapshot();
    current.verified = true;
    current.verification = json!({"elapsed": 0.0});
    current.compute_generation_id().unwrap();
    let mut last_verified = current.clone();
    last_verified.verification["elapsed"] = json!(-0.0);
    let record = DartGenerationRecord {
        schema_version: DART_GENERATION_SCHEMA_VERSION,
        current,
        last_verified: Some(last_verified),
    };
    assert!(record.canonical_bytes().is_err());
    let wire = cott::snapshot_record::encode(
        DART_GENERATION_SCHEMA_VERSION,
        &serde_json::to_value(&record.current).unwrap(),
        Some(&serde_json::to_value(&record.last_verified).unwrap()),
    )
    .unwrap();
    assert!(DartGenerationRecord::parse(&serde_json::to_vec(&wire).unwrap()).is_err());
}

#[test]
fn dart_wire_rejects_legacy_records_dangling_and_unreachable_snapshots() {
    let wire = serde_json::to_value(record()).unwrap();
    let expanded = snapshot_wire::expand(wire.clone());
    assert!(DartGenerationRecord::parse(&serde_json::to_vec(&expanded).unwrap()).is_err());
    assert!(serde_json::from_value::<DartGenerationRecord>(expanded).is_err());

    let mut legacy_version = wire.clone();
    legacy_version["schema_version"] = json!(1);
    assert!(DartGenerationRecord::parse(&serde_json::to_vec(&legacy_version).unwrap()).is_err());

    let mut dangling = wire.clone();
    dangling["current"] = json!(digest('0'));
    assert!(DartGenerationRecord::parse(&serde_json::to_vec(&dangling).unwrap()).is_err());

    let mut unreachable = wire.clone();
    let mut other = snapshot();
    other.project_version = "1.2.4".to_owned();
    other.compute_generation_id().unwrap();
    let other = serde_json::to_value(other).unwrap();
    let reference = cott::snapshot_record::digest(&other).unwrap();
    unreachable["snapshots"][&reference] = other;
    assert!(DartGenerationRecord::parse(&serde_json::to_vec(&unreachable).unwrap()).is_err());

    let mut unknown = wire.clone();
    unknown["unexpected"] = json!(true);
    assert!(DartGenerationRecord::parse(&serde_json::to_vec(&unknown).unwrap()).is_err());

    let serialized = serde_json::to_string(&wire).unwrap();
    let duplicate = format!("{{\"schema_version\":2,{}", &serialized[1..]);
    assert!(DartGenerationRecord::parse(duplicate.as_bytes()).is_err());
    assert!(serde_json::from_str::<DartGenerationRecord>(&duplicate).is_err());
}

#[test]
fn generation_identity_hashes_all_durable_dart_and_dependency_identity() {
    let original = snapshot();
    let original_id = original.generation_id.clone();
    for changed in [
        {
            let mut value = original.clone();
            value.project_name = "other_app".to_owned();
            value
        },
        {
            let mut value = original.clone();
            value.tools["dart"]["version"] = json!("3.13.4");
            value
        },
        {
            let mut value = original.clone();
            value.contract_surface["api"]["declarations"] = json!([{"kind": "struct"}]);
            value
        },
        {
            let mut value = original.clone();
            value.implementations[0].content_hash = digest('f');
            value
        },
        {
            let mut value = original.clone();
            value.dependencies = json!({
                "schema_version": 1,
                "pubspec_hash": digest('6'),
                "lockfile_hash": digest('7'),
                "packages": [{
                    "name": "collection",
                    "version": "1.19.1",
                    "source": "hosted",
                    "source_identity": format!("https://pub.dev#{}", digest('8')),
                    "content_hash": digest('9'),
                    "dependencies": [],
                    "runtime": true
                }]
            });
            value
        },
    ] {
        let mut changed = changed;
        changed
            .compute_generation_id()
            .expect("changed durable identity remains structurally valid");
        assert_ne!(changed.generation_id, original_id);
    }

    let mut volatile = agent_snapshot();
    let volatile_id = volatile.generation_id.clone();
    volatile.agent_runs[0].duration_ms += 1;
    volatile.agent_runs[0].stdout.sha256 = digest('a');
    volatile
        .compute_generation_id()
        .expect("changed agent execution evidence remains authentic");
    assert_eq!(volatile.generation_id, volatile_id);
}

#[test]
fn parser_rejects_canonical_digest_tampering_and_backend_abi_swaps() {
    for (field, incompatible) in [
        ("compiler_version", json!("0.9.0")),
        ("canonical_ir_schema", json!(7)),
        ("runtime_abi", json!(1)),
    ] {
        let mut value = snapshot_wire::expand(serde_json::to_value(record()).unwrap());
        value["current"][field] = incompatible;
        assert!(
            DartGenerationRecord::parse(&serialized(&value)).is_err(),
            "incompatible {field} must fail closed"
        );
    }

    let mut value = snapshot_wire::expand(serde_json::to_value(record()).unwrap());
    value["current"]["managed_files"]["dart/lib/modules/api.dart"] = json!(digest('9'));
    assert!(DartGenerationRecord::parse(&serialized(&value)).is_err());

    let mut value = snapshot_wire::expand(serde_json::to_value(record()).unwrap());
    value["current"]["dependencies"]["unexpected"] = json!(true);
    assert!(DartGenerationRecord::parse(&serialized(&value)).is_err());
}

#[test]
fn certified_current_requires_verify_only_history_transition() {
    let mut missing_evidence = snapshot();
    missing_evidence.verified = true;
    assert!(missing_evidence.compute_generation_id().is_err());

    let mut unresolved = snapshot();
    unresolved.verified = true;
    unresolved.verification = json!({"status": "passed"});
    unresolved.unresolved.push("api.missing".to_owned());
    assert!(unresolved.compute_generation_id().is_err());

    let mut certified = snapshot();
    certified.verified = true;
    certified.verification = json!({"status": "passed"});
    certified.compute_generation_id().unwrap();

    let missing_history = DartGenerationRecord {
        schema_version: DART_GENERATION_SCHEMA_VERSION,
        current: certified.clone(),
        last_verified: None,
    };
    assert!(missing_history.canonical_bytes().is_err());
    let inconsistent_history = DartGenerationRecord {
        schema_version: DART_GENERATION_SCHEMA_VERSION,
        current: certified.clone(),
        last_verified: Some(snapshot()),
    };
    assert!(inconsistent_history.canonical_bytes().is_err());

    DartGenerationRecord {
        schema_version: DART_GENERATION_SCHEMA_VERSION,
        current: certified.clone(),
        last_verified: Some(certified.clone()),
    }
    .canonical_bytes()
    .expect("verify may atomically certify current and history");

    let mut pending = snapshot();
    pending.project_version = "1.2.4".to_owned();
    pending.implementations.clear();
    pending.unresolved.push("api.run".to_owned());
    pending
        .managed_files
        .remove("dart/lib/src/cott_impl/api/run.dart");
    pending.compute_generation_id().unwrap();
    DartGenerationRecord {
        schema_version: DART_GENERATION_SCHEMA_VERSION,
        current: pending,
        last_verified: Some(certified),
    }
    .canonical_bytes()
    .expect("an unverified current generation must retain verified history");
}

#[test]
fn paths_and_origins_are_normalized_and_bound_to_the_callable_identity() {
    for target in [
        "/absolute.dart:_run",
        "../escape.dart:_run",
        "bindings/api.py:_run",
        "bindings/api.dart:run",
        "bindings/api.dart:_run:extra",
    ] {
        let mut malformed = snapshot();
        malformed.implementations[0].target_symbol = target.to_owned();
        assert!(malformed.compute_generation_id().is_err(), "{target}");
    }
    for source in [
        "../escape.dart",
        "/absolute.dart",
        "dart//bindings/api.dart",
        "dart/bindings/other.dart",
        "dart/bindings/api.py",
    ] {
        let mut malformed = snapshot();
        malformed.implementations[0].source_origin = source.to_owned();
        assert!(malformed.compute_generation_id().is_err(), "{source}");
    }
    for runtime in [
        "../escape.dart",
        "/absolute.dart",
        "lib/src/cott_impl/api/run.dart",
        "dart/lib/src/cott_impl/api/other.dart",
        "dart/lib/src/cott_impl/api/run.py",
    ] {
        let mut malformed = snapshot();
        malformed.implementations[0].runtime_origin = runtime.to_owned();
        assert!(malformed.compute_generation_id().is_err(), "{runtime}");
    }

    let mut missing_manifest = snapshot();
    missing_manifest.inputs.remove("cott.toml");
    assert!(missing_manifest.compute_generation_id().is_err());
    let mut escaped_source = snapshot();
    escaped_source
        .inputs
        .insert("src/../api.cott".to_owned(), digest('a'));
    assert!(escaped_source.compute_generation_id().is_err());
    let mut mismatched_surface = snapshot();
    mismatched_surface.contract_surface = json!({"other": {"declarations": []}});
    assert!(mismatched_surface.compute_generation_id().is_err());
}

#[test]
fn dependency_closure_is_closed_paired_and_source_authenticated() {
    let valid = json!({
        "schema_version": 1,
        "pubspec_hash": digest('1'),
        "lockfile_hash": digest('2'),
        "packages": [
            {
                "name": "async",
                "version": "2.13.0",
                "source": "hosted",
                "source_identity": format!("https://pub.dev#{}", digest('3')),
                "content_hash": digest('4'),
                "dependencies": ["collection"],
                "runtime": true
            },
            {
                "name": "collection",
                "version": "1.19.1",
                "source": "path",
                "source_identity": "vendor/collection",
                "content_hash": digest('5'),
                "dependencies": [],
                "runtime": true
            }
        ]
    });
    let mut with_dependencies = snapshot();
    with_dependencies.dependencies = valid.clone();
    with_dependencies
        .compute_generation_id()
        .expect("closed verified package closure must be accepted");

    for invalid in [
        {
            let mut value = valid.clone();
            value["lockfile_hash"] = Value::Null;
            value
        },
        {
            let mut value = valid.clone();
            value["packages"][0]["source_identity"] = json!("http://pub.dev#sha256:bad");
            value
        },
        {
            let mut value = valid.clone();
            value["packages"][0]["dependencies"] = json!(["missing"]);
            value
        },
        {
            let mut value = valid;
            value["packages"][0]["kotlin_coordinate"] = json!("forbidden");
            value
        },
    ] {
        let mut malformed = snapshot();
        malformed.dependencies = invalid;
        assert!(malformed.compute_generation_id().is_err());
    }
}

#[test]
fn agent_owned_source_requires_matching_intent_and_successful_run_identity() {
    agent_snapshot();
    let mut pending = agent_snapshot();
    pending.unresolved.push("api.run".to_owned());
    pending
        .compute_generation_id()
        .expect("unverified pending source may retain authentic repair provenance");
    pending.implementations.clear();
    assert!(
        pending.compute_generation_id().is_err(),
        "a successful source run without its binding identity is not current evidence"
    );

    let mut no_run = agent_snapshot();
    no_run.agent_runs.clear();
    assert!(no_run.compute_generation_id().is_err());

    let mut no_intent = agent_snapshot();
    no_intent
        .tools
        .as_object_mut()
        .unwrap()
        .remove("cott_intent");
    assert!(no_intent.compute_generation_id().is_err());

    let mut tampered = agent_snapshot();
    tampered.agent_runs[0].implementation_hash = digest('e');
    assert!(tampered.compute_generation_id().is_err());

    let mut failed = agent_snapshot();
    failed.agent_runs[0].status.exit_code = Some(1);
    assert!(failed.compute_generation_id().is_err());
    for malformed_intent in [
        json!("not-an-object"),
        json!({"version": 2, "hashes": {}}),
        json!({"version": 1, "hashes": {"api.run": "sha256:bad"}}),
        json!({"version": 1, "hashes": {}, "python_symbol": "forbidden"}),
    ] {
        let mut malformed = snapshot();
        malformed.tools["cott_intent"] = malformed_intent;
        assert!(malformed.compute_generation_id().is_err());
    }

    let mut unknown_run_field = snapshot_wire::expand(
        serde_json::to_value(DartGenerationRecord {
            schema_version: DART_GENERATION_SCHEMA_VERSION,
            current: agent_snapshot(),
            last_verified: None,
        })
        .unwrap(),
    );
    unknown_run_field["current"]["agent_runs"][0]["python_symbol"] = json!("forbidden");
    assert!(DartGenerationRecord::parse(&serialized(&unknown_run_field)).is_err());
}

#[test]
fn planner_preserves_source_order_and_default_specialization_inventory() {
    let parsed = parse_project([SourceFile::new(
        PathBuf::from("src/api/service.cott"),
        r#"module api.service

trait Reader:
    fn read(self, amount: I32) -> I32 = api.service.default_read
    fn label(self) -> Unit

fn default_read(receiver: Reader, amount: I32) -> I32
fn specialized_read(receiver: ReaderState, amount: I32) -> I32
fn run(amount: I32) -> I32

specialize ReaderState for Reader:
    read = api.service.specialized_read

impl ReaderState for Reader:
    fn label(self) -> Unit:
        ensures true
"#,
    )])
    .expect("planner fixture must parse");
    let project = lower(Path::new("src"), parsed).expect("planner fixture must lower");
    let mut ir = render(&project).expect("planner fixture must render");
    let module = &mut ir.modules[0];
    let mut canonical = load(&module.bytes).expect("canonical fixture must load");
    canonical["declarations"]
        .as_array_mut()
        .unwrap()
        .iter_mut()
        .find(|declaration| declaration["name"] == "api.service.specialized_read")
        .unwrap()["public"] = json!(false);
    module.bytes = serde_json::to_vec(&canonical).unwrap();
    module.bytes.push(b'\n');

    let plan = cott::dart::DartPlan::from_ir(&ir).expect("Dart plan must load canonical IR");

    let symbols = plan
        .callables()
        .iter()
        .map(|callable| callable.symbol.as_str())
        .collect::<Vec<_>>();
    assert_eq!(
        &symbols[..3],
        &[
            "api.service.default_read",
            "api.service.specialized_read",
            "api.service.run",
        ]
    );
    let callables = plan
        .callables()
        .iter()
        .map(|callable| (callable.symbol.as_str(), callable))
        .collect::<BTreeMap<_, _>>();
    assert_eq!(
        callables["api.service.ReaderState.read"].declaration["selected"]["origin"],
        "specialization"
    );
    assert_eq!(
        callables["api.service.ReaderState.read"].declaration["selected"]["function"]["verified_facade"],
        "api.service.specialized_read"
    );
    assert_eq!(
        callables["api.service.ReaderState.label"].declaration["selected"]["origin"],
        "explicit"
    );
    assert!(callables["api.service.specialized_read"].owner.is_none());
    assert_eq!(
        callables.keys().copied().collect::<BTreeSet<_>>(),
        BTreeSet::from([
            "api.service.default_read",
            "api.service.specialized_read",
            "api.service.run",
            "api.service.ReaderState.read",
            "api.service.ReaderState.label",
        ])
    );
}
