use std::collections::BTreeMap;

use cott::kotlin::KotlinOwner;
use cott::kotlin::provenance::{
    KOTLIN_GENERATION_SCHEMA_VERSION, KOTLIN_RUNTIME_ABI_VERSION, KotlinBindingRecord,
    KotlinGenerationRecord, KotlinGenerationSnapshot,
};
use cott::provenance::{AgentRun, AgentStatus, SemanticCoverage, StreamDigest};
use cott::rust::RustOwner;
use cott::rust::provenance::{
    RUST_GENERATION_SCHEMA_VERSION, RUST_RUNTIME_ABI_VERSION, RustBindingRecord,
    RustGenerationRecord, RustGenerationSnapshot,
};
use serde_json::{Value, json};

#[path = "support/snapshot.rs"]
mod snapshot_wire;

fn digest(byte: char) -> String {
    format!("sha256:{}", byte.to_string().repeat(64))
}

fn empty_dependencies() -> Value {
    json!({
        "schema_version": 1,
        "cargo_manifest_hash": null,
        "lockfile_hash": null,
        "packages": []
    })
}

fn snapshot() -> RustGenerationSnapshot {
    let mut snapshot = RustGenerationSnapshot {
        target: "rust".to_owned(),
        generation_id: String::new(),
        verified: false,
        compiler_version: env!("CARGO_PKG_VERSION").to_owned(),
        canonical_ir_schema: cott::provenance::CANONICAL_IR_SCHEMA_VERSION,
        runtime_abi: RUST_RUNTIME_ABI_VERSION,
        project_name: "sample_app".to_owned(),
        project_version: "1.2.3".to_owned(),
        inputs: BTreeMap::from([
            ("cott.toml".to_owned(), digest('a')),
            ("src/api.cott".to_owned(), digest('b')),
        ]),
        tools: json!({
            "compiler": {"version": env!("CARGO_PKG_VERSION")},
            "rust": {"version": "3.13.3"},
            "runtime": {"abi": RUST_RUNTIME_ABI_VERSION}
        }),
        ir: BTreeMap::from([("api".to_owned(), digest('c'))]),
        contract_surface: json!({"api": {"declarations": []}}),
        public_symbols: BTreeMap::from([(
            "api".to_owned(),
            vec!["Payload".to_owned(), "run".to_owned()],
        )]),
        implementations: vec![RustBindingRecord {
            cott_symbol: "api.run".to_owned(),
            target_symbol: "bindings/api.rs:run".to_owned(),
            source_origin: "rust/bindings/api.rs".to_owned(),
            runtime_origin: "rust/src/cott_impl/api/run.rs".to_owned(),
            content_hash: digest('d'),
            owner: RustOwner::Manifest,
        }],
        dependencies: empty_dependencies(),
        managed_files: BTreeMap::from([
            ("rust/src/modules/api.rs".to_owned(), digest('e')),
            ("rust/src/cott_impl/api/run.rs".to_owned(), digest('d')),
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

fn record() -> RustGenerationRecord {
    RustGenerationRecord {
        schema_version: RUST_GENERATION_SCHEMA_VERSION,
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

fn agent_snapshot() -> RustGenerationSnapshot {
    let mut snapshot = snapshot();
    snapshot.implementations[0].owner = RustOwner::Agent;
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
fn rust_record_round_trips_canonical_bytes_and_rejects_other_backends() {
    let record = record();
    let bytes = record
        .canonical_bytes()
        .expect("valid Rust generation record must serialize");
    assert_eq!(bytes.last(), Some(&b'\n'));
    let parsed =
        RustGenerationRecord::parse(&bytes).expect("canonical Rust generation bytes must parse");
    assert_eq!(parsed, record);
    assert_eq!(parsed.canonical_bytes().unwrap(), bytes);

    assert!(RustGenerationRecord::parse(&kotlin_record_bytes()).is_err());
    let mut kotlin_shaped = snapshot_wire::expand(serde_json::to_value(&record).unwrap());
    kotlin_shaped["current"]["target"] = json!("kotlin");
    kotlin_shaped["current"]["public_kotlin_symbols"] = json!({"api": ["run"]});
    assert!(RustGenerationRecord::parse(&serialized(&kotlin_shaped)).is_err());
}

#[test]
fn snapshot_references_deduplicate_certification_but_not_verification_history() {
    let pending = agent_snapshot();
    let mut certified = pending.clone();
    certified.verified = true;
    certified.verification = json!({"status": "passed"});
    certified.compute_generation_id().unwrap();
    assert_eq!(pending.generation_id, certified.generation_id);

    let certified_record = RustGenerationRecord {
        schema_version: RUST_GENERATION_SCHEMA_VERSION,
        current: certified.clone(),
        last_verified: Some(certified.clone()),
    };
    let certified_wire = serde_json::to_value(&certified_record).unwrap();
    assert_eq!(certified_wire["current"], certified_wire["last_verified"]);
    assert_eq!(certified_wire["snapshots"].as_object().unwrap().len(), 1);
    assert_eq!(
        RustGenerationRecord::parse(&serde_json::to_vec(&certified_wire).unwrap()).unwrap(),
        certified_record
    );

    let pending_record = RustGenerationRecord {
        schema_version: RUST_GENERATION_SCHEMA_VERSION,
        current: pending,
        last_verified: Some(certified),
    };
    let wire = serde_json::to_value(&pending_record).unwrap();
    assert_ne!(wire["current"], wire["last_verified"]);
    assert_eq!(wire["snapshots"].as_object().unwrap().len(), 2);
    assert_eq!(
        RustGenerationRecord::parse(&serde_json::to_vec(&wire).unwrap()).unwrap(),
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
            RustGenerationRecord::parse(&serde_json::to_vec(&tampered).unwrap()).is_err(),
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
    let record = RustGenerationRecord {
        schema_version: RUST_GENERATION_SCHEMA_VERSION,
        current,
        last_verified: Some(last_verified),
    };
    assert!(record.canonical_bytes().is_err());
    let wire = cott::snapshot_record::encode(
        RUST_GENERATION_SCHEMA_VERSION,
        &serde_json::to_value(&record.current).unwrap(),
        Some(&serde_json::to_value(&record.last_verified).unwrap()),
    )
    .unwrap();
    assert!(RustGenerationRecord::parse(&serde_json::to_vec(&wire).unwrap()).is_err());
}

#[test]
fn rust_wire_rejects_legacy_records_dangling_and_unreachable_snapshots() {
    let wire = serde_json::to_value(record()).unwrap();
    let expanded = snapshot_wire::expand(wire.clone());
    assert!(RustGenerationRecord::parse(&serde_json::to_vec(&expanded).unwrap()).is_err());
    assert!(serde_json::from_value::<RustGenerationRecord>(expanded).is_err());

    let mut legacy_version = wire.clone();
    legacy_version["schema_version"] = json!(2);
    assert!(RustGenerationRecord::parse(&serde_json::to_vec(&legacy_version).unwrap()).is_err());

    let mut dangling = wire.clone();
    dangling["current"] = json!(digest('0'));
    assert!(RustGenerationRecord::parse(&serde_json::to_vec(&dangling).unwrap()).is_err());

    let mut unreachable = wire.clone();
    let mut other = snapshot();
    other.project_version = "1.2.4".to_owned();
    other.compute_generation_id().unwrap();
    let other = serde_json::to_value(other).unwrap();
    let reference = cott::snapshot_record::digest(&other).unwrap();
    unreachable["snapshots"][&reference] = other;
    assert!(RustGenerationRecord::parse(&serde_json::to_vec(&unreachable).unwrap()).is_err());

    let mut unknown = wire.clone();
    unknown["unexpected"] = json!(true);
    assert!(RustGenerationRecord::parse(&serde_json::to_vec(&unknown).unwrap()).is_err());

    let serialized = serde_json::to_string(&wire).unwrap();
    let duplicate = format!("{{\"schema_version\":2,{}", &serialized[1..]);
    assert!(RustGenerationRecord::parse(duplicate.as_bytes()).is_err());
    assert!(serde_json::from_str::<RustGenerationRecord>(&duplicate).is_err());
}

#[test]
fn generation_identity_hashes_all_durable_rust_and_dependency_identity() {
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
            value.tools["rust"]["version"] = json!("3.13.4");
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
                "cargo_manifest_hash": digest('6'),
                "lockfile_hash": digest('7'),
                "packages": [{
                    "name": "collection",
                    "version": "1.19.1",
                    "source": "registry",
                    "source_identity": format!("registry+https://github.com/rust-lang/crates.io-index#{}", digest('8')),
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
        ("runtime_abi", json!(2)),
    ] {
        let mut value = snapshot_wire::expand(serde_json::to_value(record()).unwrap());
        value["current"][field] = incompatible;
        assert!(
            RustGenerationRecord::parse(&serialized(&value)).is_err(),
            "incompatible {field} must fail closed"
        );
    }

    let mut value = snapshot_wire::expand(serde_json::to_value(record()).unwrap());
    value["current"]["managed_files"]["rust/src/modules/api.rs"] = json!(digest('9'));
    assert!(RustGenerationRecord::parse(&serialized(&value)).is_err());

    let mut value = snapshot_wire::expand(serde_json::to_value(record()).unwrap());
    value["current"]["dependencies"]["unexpected"] = json!(true);
    assert!(RustGenerationRecord::parse(&serialized(&value)).is_err());
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

    let missing_history = RustGenerationRecord {
        schema_version: RUST_GENERATION_SCHEMA_VERSION,
        current: certified.clone(),
        last_verified: None,
    };
    assert!(missing_history.canonical_bytes().is_err());
    let inconsistent_history = RustGenerationRecord {
        schema_version: RUST_GENERATION_SCHEMA_VERSION,
        current: certified.clone(),
        last_verified: Some(snapshot()),
    };
    assert!(inconsistent_history.canonical_bytes().is_err());

    RustGenerationRecord {
        schema_version: RUST_GENERATION_SCHEMA_VERSION,
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
        .remove("rust/src/cott_impl/api/run.rs");
    pending.compute_generation_id().unwrap();
    RustGenerationRecord {
        schema_version: RUST_GENERATION_SCHEMA_VERSION,
        current: pending,
        last_verified: Some(certified),
    }
    .canonical_bytes()
    .expect("an unverified current generation must retain verified history");
}

#[test]
fn paths_and_origins_are_normalized_and_bound_to_the_callable_identity() {
    for target in [
        "/absolute.rs:_run",
        "../escape.rs:_run",
        "bindings/api.py:_run",
        "bindings/api.rs:fn",
        "bindings/api.rs:run:extra",
    ] {
        let mut malformed = snapshot();
        malformed.implementations[0].target_symbol = target.to_owned();
        assert!(malformed.compute_generation_id().is_err(), "{target}");
    }
    for source in [
        "../escape.rs",
        "/absolute.rs",
        "rust//bindings/api.rs",
        "rust/bindings/other.rs",
        "rust/bindings/api.py",
    ] {
        let mut malformed = snapshot();
        malformed.implementations[0].source_origin = source.to_owned();
        assert!(malformed.compute_generation_id().is_err(), "{source}");
    }
    for runtime in [
        "../escape.rs",
        "/absolute.rs",
        "lib/src/cott_impl/api/run.rs",
        "rust/src/cott_impl/api/other.rs",
        "rust/src/cott_impl/api/run.py",
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
        "cargo_manifest_hash": digest('1'),
        "lockfile_hash": digest('2'),
        "packages": [
            {
                "name": "async",
                "version": "2.13.0",
                "source": "registry",
                "source_identity": format!("registry+https://github.com/rust-lang/crates.io-index#{}", digest('3')),
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
        serde_json::to_value(RustGenerationRecord {
            schema_version: RUST_GENERATION_SCHEMA_VERSION,
            current: agent_snapshot(),
            last_verified: None,
        })
        .unwrap(),
    );
    unknown_run_field["current"]["agent_runs"][0]["python_symbol"] = json!("forbidden");
    assert!(RustGenerationRecord::parse(&serialized(&unknown_run_field)).is_err());
}

#[test]
fn rust_records_are_isolated_from_every_foreign_backend() {
    let bytes = record().canonical_bytes().unwrap();
    assert!(cott::dart::provenance::DartGenerationRecord::parse(&bytes).is_err());
    assert!(cott::kotlin::provenance::KotlinGenerationRecord::parse(&bytes).is_err());
    assert!(cott::provenance::GenerationRecord::parse(&bytes).is_err());
    for target in ["python", "kotlin", "dart"] {
        let mut wire = snapshot_wire::expand(serde_json::to_value(record()).unwrap());
        wire["current"]["target"] = json!(target);
        assert!(RustGenerationRecord::parse(&serialized(&wire)).is_err());
    }
}

#[test]
fn cargo_package_and_edge_names_preserve_hyphens_case_and_boundaries() {
    for name in ["pin-project-lite", "Mixed_Case-Name", &"x".repeat(64)] {
        let mut current = snapshot();
        current.dependencies = json!({
            "schema_version": 1,
            "cargo_manifest_hash": digest('1'),
            "lockfile_hash": digest('2'),
            "packages": [
                {"name": "consumer", "version": "1.0.0", "source": "path",
                 "source_identity": "deps/consumer", "content_hash": digest('3'),
                 "dependencies": [name], "runtime": true},
                {"name": name, "version": "0.2.17", "source": "registry",
                 "source_identity": format!("registry+https://github.com/rust-lang/crates.io-index#{}", digest('4')),
                 "content_hash": digest('5'), "dependencies": [], "runtime": true}
            ]
        });
        current.dependencies["packages"]
            .as_array_mut()
            .unwrap()
            .sort_by(|a, b| a["name"].as_str().cmp(&b["name"].as_str()));
        current.compute_generation_id().unwrap();
        let valid = RustGenerationRecord {
            schema_version: RUST_GENERATION_SCHEMA_VERSION,
            current,
            last_verified: None,
        };
        assert_eq!(
            RustGenerationRecord::parse(&valid.canonical_bytes().unwrap()).unwrap(),
            valid
        );
    }
}

#[test]
fn cargo_dependency_names_reject_invalid_package_names_and_edges() {
    for name in [
        "",
        "9start",
        "contains.dot",
        "has space",
        "naïve",
        "slash/name",
        &"x".repeat(65),
    ] {
        for edge in [false, true] {
            let mut current = snapshot();
            current.dependencies = json!({
                "schema_version": 1, "cargo_manifest_hash": digest('1'),
                "lockfile_hash": digest('2'),
                "packages": [{"name": if edge { "consumer" } else { name },
                    "version": "1.0.0", "source": "path", "source_identity": "deps/consumer",
                    "content_hash": digest('3'), "dependencies": if edge { json!([name]) } else { json!([]) },
                    "runtime": true}]
            });
            assert!(
                current.compute_generation_id().is_err(),
                "{name:?}, edge={edge}"
            );
        }
    }
}

#[test]
fn rust_binding_records_accept_canonical_raw_keyword_functions_and_reject_invalid_spellings() {
    for function in [
        "r#gen", "r#loop", "r#box", "r#type", "r#async", "r#fn", "self_", "Self_", "super_",
        "crate_", "self__", "Self__", "super__", "crate__",
    ] {
        let mut current = snapshot();
        current.implementations[0].target_symbol = format!("bindings/api.rs:{function}");
        current.compute_generation_id().unwrap();
        let record = RustGenerationRecord {
            schema_version: RUST_GENERATION_SCHEMA_VERSION,
            current,
            last_verified: None,
        };
        assert_eq!(
            RustGenerationRecord::parse(&record.canonical_bytes().unwrap()).unwrap(),
            record,
            "{function}"
        );
    }
    for function in [
        "r#self", "r#Self", "r#super", "r#crate", "r#_", "r#run", "r#Loop", "r#", "r#r#loop",
        "loop", "gen", "self", "Self", "super", "crate",
    ] {
        let mut current = snapshot();
        current.implementations[0].target_symbol = format!("bindings/api.rs:{function}");
        assert!(current.compute_generation_id().is_err(), "{function}");
    }
}

#[test]
fn agent_run_adapter_enum_is_closed_and_includes_pi() {
    for adapter in ["claude", "codex", "omp", "pi"] {
        let mut current = agent_snapshot();
        current.agent_runs[0].adapter = adapter.to_owned();
        current.compute_generation_id().expect(adapter);
        let record = RustGenerationRecord {
            schema_version: RUST_GENERATION_SCHEMA_VERSION,
            current,
            last_verified: None,
        };
        let bytes = record.canonical_bytes().expect(adapter);
        assert_eq!(RustGenerationRecord::parse(&bytes).expect(adapter), record);
    }
    for adapter in ["pie", "PI", "pi-coding-agent", "oh-my-pi", ""] {
        let mut current = agent_snapshot();
        current.agent_runs[0].adapter = adapter.to_owned();
        assert!(current.compute_generation_id().is_err(), "{adapter}");
        let mut wire = snapshot_wire::expand(
            serde_json::to_value(RustGenerationRecord {
                schema_version: RUST_GENERATION_SCHEMA_VERSION,
                current: agent_snapshot(),
                last_verified: None,
            })
            .unwrap(),
        );
        wire["current"]["agent_runs"][0]["adapter"] = json!(adapter);
        assert!(
            RustGenerationRecord::parse(&serialized(&wire)).is_err(),
            "{adapter}"
        );
    }
}
