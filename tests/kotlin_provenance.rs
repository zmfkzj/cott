use std::collections::{BTreeMap, BTreeSet};
use std::path::{Path, PathBuf};

use cott::compiler::{SourceFile, parse_project};
use cott::hir::lower;
use cott::ir::{load, render};
use cott::kotlin::KotlinOwner;
use cott::kotlin::provenance::{
    KOTLIN_GENERATION_SCHEMA_VERSION, KOTLIN_RUNTIME_ABI_VERSION, KotlinBindingRecord,
    KotlinGenerationRecord, KotlinGenerationSnapshot,
};
use cott::provenance::{
    AgentRun, AgentStatus, ClauseCoverage, CoverageStatus, CoverageSummary,
    GENERATION_SCHEMA_VERSION, GenerationCompatibility, GenerationRecord as PythonGenerationRecord,
    GenerationSnapshot as PythonGenerationSnapshot, SemanticCoverage, SourceSpan, StreamDigest,
};
use serde_json::{Value, json};

fn digest(byte: char) -> String {
    format!("sha256:{}", byte.to_string().repeat(64))
}

fn snapshot() -> KotlinGenerationSnapshot {
    let mut snapshot = KotlinGenerationSnapshot {
        target: "kotlin".to_owned(),
        generation_id: String::new(),
        verified: false,
        compiler_version: env!("CARGO_PKG_VERSION").to_owned(),
        canonical_ir_schema: cott::provenance::CANONICAL_IR_SCHEMA_VERSION,
        runtime_abi: KOTLIN_RUNTIME_ABI_VERSION,
        project_name: "sample".to_owned(),
        project_version: "1.2.3".to_owned(),
        inputs: BTreeMap::from([
            ("cott.toml".to_owned(), digest('a')),
            ("src/api.cott".to_owned(), digest('b')),
        ]),
        tools: json!({
            "compiler": {"version": env!("CARGO_PKG_VERSION")},
            "kotlin": {"version": "2.2.10"},
            "runtime": {"abi": KOTLIN_RUNTIME_ABI_VERSION}
        }),
        ir: BTreeMap::from([("api".to_owned(), digest('c'))]),
        contract_surface: json!({"api": {"declarations": []}}),
        public_symbols: BTreeMap::from([(
            "api".to_owned(),
            vec!["Payload".to_owned(), "run".to_owned()],
        )]),
        implementations: vec![KotlinBindingRecord {
            cott_symbol: "api.run".to_owned(),
            target_symbol: "cott_impl.api.run".to_owned(),
            source_origin: "kotlin/cott_impl/api/run.kt".to_owned(),
            runtime_origin: "kotlin/cott_impl/api/run.kt".to_owned(),
            content_hash: digest('d'),
            owner: KotlinOwner::Agent,
        }],
        managed_files: BTreeMap::from([
            (
                "build/generated/kotlin/api/Facade.kt".to_owned(),
                digest('e'),
            ),
            (
                "build/generated/kotlin/cott_impl/api/run.kt".to_owned(),
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

fn record() -> KotlinGenerationRecord {
    KotlinGenerationRecord {
        schema_version: KOTLIN_GENERATION_SCHEMA_VERSION,
        current: snapshot(),
        last_verified: None,
    }
}

fn python_record_bytes() -> Vec<u8> {
    let mut current = PythonGenerationSnapshot {
        generation_id: String::new(),
        verified: false,
        project_version: "1.2.3".to_owned(),
        compatibility: GenerationCompatibility::current(),
        inputs: json!({}),
        tools: json!({}),
        ir: json!({}),
        contract_surface: json!({}),
        public_python_symbols: json!({}),
        implementations: json!([]),
        dependencies: json!([]),
        managed_files: BTreeMap::new(),
        unresolved: Vec::new(),
        verification: Value::Null,
        semantic_coverage: SemanticCoverage::default(),
        agent_runs: Vec::new(),
    };
    current
        .compute_generation_id()
        .expect("Python record fixture must have a valid identity");
    PythonGenerationRecord {
        schema_version: GENERATION_SCHEMA_VERSION,
        current,
        last_verified: None,
    }
    .canonical_bytes()
    .expect("Python record fixture must serialize")
}

fn serialized(value: &Value) -> Vec<u8> {
    let mut bytes = serde_json::to_vec(value).expect("JSON fixture must serialize");
    bytes.push(b'\n');
    bytes
}

#[test]
fn kotlin_record_round_trips_canonical_bytes() {
    let record = record();
    let bytes = record
        .canonical_bytes()
        .expect("valid Kotlin generation record must serialize");
    assert_eq!(bytes.last(), Some(&b'\n'));

    let parsed = KotlinGenerationRecord::parse(&bytes)
        .expect("canonical Kotlin generation bytes must parse");
    assert_eq!(parsed, record);
    assert_eq!(
        parsed
            .canonical_bytes()
            .expect("parsed record must remain canonical"),
        bytes
    );
}

#[test]
fn generation_identity_hashes_every_durable_kotlin_identity() {
    let original = snapshot();
    let original_id = original.generation_id.clone();

    let mut changed_project = original.clone();
    changed_project.project_name = "other".to_owned();
    changed_project
        .compute_generation_id()
        .expect("changed project remains structurally valid");
    assert_ne!(changed_project.generation_id, original_id);

    let mut changed_tools = original.clone();
    changed_tools.tools["kotlin"]["version"] = json!("2.3.0");
    changed_tools
        .compute_generation_id()
        .expect("changed tools remain structurally valid");
    assert_ne!(changed_tools.generation_id, original_id);

    let mut changed_contract = original.clone();
    changed_contract.contract_surface["api"]["declarations"] = json!([{"kind": "struct"}]);
    changed_contract
        .compute_generation_id()
        .expect("changed contract remains structurally valid");
    assert_ne!(changed_contract.generation_id, original_id);

    let mut changed_binding = original.clone();
    changed_binding.implementations[0].content_hash = digest('f');
    changed_binding
        .compute_generation_id()
        .expect("changed binding remains structurally valid");
    assert_ne!(changed_binding.generation_id, original_id);

    let mut changed_managed_file = original.clone();
    changed_managed_file
        .managed_files
        .insert("build/generated/kotlin/sample.jar".to_owned(), digest('1'));
    changed_managed_file
        .compute_generation_id()
        .expect("changed managed files remain structurally valid");
    assert_ne!(changed_managed_file.generation_id, original_id);

    let mut volatile = original;
    volatile.verified = true;
    volatile.verification = json!({"status": "passed"});
    volatile.semantic_coverage = SemanticCoverage {
        clauses: vec![ClauseCoverage {
            symbol: "api.run".to_owned(),
            clause_id: "requires:0".to_owned(),
            span: SourceSpan {
                start_byte: 0,
                end_byte: 1,
                start_line: 1,
                start_column: 1,
                end_line: 1,
                end_column: 2,
            },
            status: CoverageStatus::Observed,
            evidence: vec![json!({"runner": "kotlin"})],
        }],
        summary: CoverageSummary {
            observed: 1,
            ..CoverageSummary::default()
        },
        policy: Default::default(),
    };
    volatile.agent_runs.push(AgentRun {
        symbol: "api.run".to_owned(),
        adapter: "test".to_owned(),
        adapter_version: "1".to_owned(),
        argv_template: vec!["agent".to_owned(), "{prompt}".to_owned()],
        executable: "/usr/bin/agent".to_owned(),
        executable_hash: digest('2'),
        prompt_hash: digest('3'),
        implementation_hash: digest('4'),
        environment_names: vec!["HOME".to_owned(), "PATH".to_owned()],
        duration_ms: 1,
        status: AgentStatus {
            exit_code: Some(0),
            signal: None,
            timed_out: false,
            cancelled: false,
        },
        stdout: StreamDigest {
            bytes: 0,
            sha256: digest('5'),
            truncated: false,
        },
        stderr: StreamDigest {
            bytes: 0,
            sha256: digest('6'),
            truncated: false,
        },
    });
    volatile
        .compute_generation_id()
        .expect("verification evidence remains structurally valid");
    assert_eq!(volatile.generation_id, original_id);
}

#[test]
fn parser_rejects_hash_drift_in_relevant_identity_fields() {
    let mut value = serde_json::to_value(record()).expect("record fixture must serialize");
    value["current"]["project_version"] = json!("1.2.4");
    assert!(KotlinGenerationRecord::parse(&serialized(&value)).is_err());

    let mut value = serde_json::to_value(record()).expect("record fixture must serialize");
    value["current"]["managed_files"]["build/generated/kotlin/api/Facade.kt"] = json!(digest('9'));
    assert!(KotlinGenerationRecord::parse(&serialized(&value)).is_err());
}

#[test]
fn parser_rejects_python_unknown_and_incompatible_records() {
    assert!(KotlinGenerationRecord::parse(&python_record_bytes()).is_err());

    let mut python_shaped = serde_json::to_value(record()).expect("record fixture must serialize");
    python_shaped["current"]["target"] = json!("python");
    python_shaped["current"]["public_python_symbols"] = json!({"api": ["run"]});
    assert!(KotlinGenerationRecord::parse(&serialized(&python_shaped)).is_err());

    let mut unknown_record = serde_json::to_value(record()).expect("record fixture must serialize");
    unknown_record["unexpected"] = json!(true);
    assert!(KotlinGenerationRecord::parse(&serialized(&unknown_record)).is_err());

    let mut python_binding = serde_json::to_value(record()).expect("record fixture must serialize");
    python_binding["current"]["implementations"][0]["python_symbol"] = json!("cott_impl.api:run");
    assert!(KotlinGenerationRecord::parse(&serialized(&python_binding)).is_err());

    for (field, incompatible) in [
        ("schema_version", json!(7)),
        ("compiler_version", json!("0.9.0")),
        ("canonical_ir_schema", json!(7)),
        ("runtime_abi", json!(7)),
    ] {
        let mut value = serde_json::to_value(record()).expect("record fixture must serialize");
        if field == "schema_version" {
            value[field] = incompatible;
        } else {
            value["current"][field] = incompatible;
        }
        assert!(
            KotlinGenerationRecord::parse(&serialized(&value)).is_err(),
            "incompatible {field} must fail closed"
        );
    }
}

#[test]
fn malformed_intent_and_unsafe_project_names_cannot_receive_an_identity() {
    for intent in [
        json!("not-an-object"),
        json!({"version": 2, "hashes": {}}),
        json!({"version": 1, "hashes": {"api.run": "sha256:not-a-digest"}}),
        json!({"version": 1, "hashes": {}, "python_symbol": "forbidden"}),
    ] {
        let mut malformed = snapshot();
        malformed.tools["cott_intent"] = intent;
        assert!(malformed.compute_generation_id().is_err());
    }

    let mut unsafe_names = vec![
        "Sample".to_owned(),
        "sample_name".to_owned(),
        "-sample".to_owned(),
        "sample-".to_owned(),
        "sample--app".to_owned(),
        "sample/../other".to_owned(),
    ];
    unsafe_names.push("a".repeat(65));
    for name in unsafe_names {
        let mut malformed = snapshot();
        malformed.project_name = name;
        assert!(malformed.compute_generation_id().is_err());
    }
}

#[test]
fn malformed_origins_and_unsorted_symbols_cannot_receive_an_identity() {
    for source in [
        "../escape.kt",
        "/absolute.kt",
        "kotlin//api/run.kt",
        "api/run.py",
    ] {
        let mut malformed = snapshot();
        malformed.implementations[0].source_origin = source.to_owned();
        assert!(
            malformed.compute_generation_id().is_err(),
            "malformed source origin {source:?} must be rejected before hashing"
        );
    }

    for runtime in [
        "../escape.kt",
        "/absolute.kt",
        "cott_impl/api/run.kt",
        "kotlin/api/run.py",
    ] {
        let mut malformed = snapshot();
        malformed.implementations[0].runtime_origin = runtime.to_owned();
        assert!(
            malformed.compute_generation_id().is_err(),
            "malformed runtime origin {runtime:?} must be rejected before hashing"
        );
    }

    let mut duplicate_public = snapshot();
    duplicate_public
        .public_symbols
        .get_mut("api")
        .unwrap()
        .push("run".to_owned());
    assert!(duplicate_public.compute_generation_id().is_err());

    let mut unsorted_public = snapshot();
    unsorted_public.public_symbols.insert(
        "api".to_owned(),
        vec!["run".to_owned(), "Payload".to_owned()],
    );
    assert!(unsorted_public.compute_generation_id().is_err());

    let mut duplicate_implementation = snapshot();
    duplicate_implementation
        .implementations
        .push(duplicate_implementation.implementations[0].clone());
    assert!(duplicate_implementation.compute_generation_id().is_err());

    let mut keyword_target = snapshot();
    keyword_target.implementations[0].target_symbol = "cott_impl.when.fun".to_owned();
    keyword_target
        .compute_generation_id()
        .expect("raw target identity may contain Kotlin keywords");

    let mut unicode_target = snapshot();
    unicode_target.implementations[0].target_symbol = "cott_impl.δοκιμή.τρέξε".to_owned();
    unicode_target
        .compute_generation_id()
        .expect("raw target identity may use Unicode Kotlin identifiers");
}

#[test]
fn certified_current_and_last_verified_move_together() {
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
    certified
        .compute_generation_id()
        .expect("certified snapshot must retain its generation identity");

    let missing_history = KotlinGenerationRecord {
        schema_version: KOTLIN_GENERATION_SCHEMA_VERSION,
        current: certified.clone(),
        last_verified: None,
    };
    assert!(missing_history.canonical_bytes().is_err());

    let inconsistent_history = KotlinGenerationRecord {
        schema_version: KOTLIN_GENERATION_SCHEMA_VERSION,
        current: certified.clone(),
        last_verified: Some(snapshot()),
    };
    assert!(inconsistent_history.canonical_bytes().is_err());
    let mut other_project = certified.clone();
    other_project.project_name = "other".to_owned();
    other_project
        .compute_generation_id()
        .expect("other project snapshot remains internally valid");
    let foreign_history = KotlinGenerationRecord {
        schema_version: KOTLIN_GENERATION_SCHEMA_VERSION,
        current: snapshot(),
        last_verified: Some(other_project),
    };
    assert!(foreign_history.canonical_bytes().is_err());

    let certified_record = KotlinGenerationRecord {
        schema_version: KOTLIN_GENERATION_SCHEMA_VERSION,
        current: certified.clone(),
        last_verified: Some(certified),
    };
    certified_record
        .canonical_bytes()
        .expect("certified current and history snapshots may be published together");
}

#[test]
fn planner_preserves_canonical_declarations_and_expanded_callables() {
    let parsed = parse_project([SourceFile::new(
        PathBuf::from("src/api/service.cott"),
        r#"module api.service

trait Reader:
    fn read(self, amount: I32) -> I32 = api.service.default_read
    fn label(self) -> Unit

fn default_read(receiver: Reader, amount: I32) -> I32
fn run(amount: I32) -> I32

impl ReaderState for Reader:
    fn label(self) -> Unit:
        ensures true
"#,
    )])
    .expect("planner fixture must parse");
    let project = lower(Path::new("src"), parsed).expect("planner fixture must lower");
    let ir = render(&project).expect("planner fixture must render");
    let canonical = load(&ir.modules[0].bytes).expect("canonical fixture must load");

    let plan = cott::kotlin::KotlinPlan::from_ir(&ir).expect("Kotlin plan must load canonical IR");
    assert_eq!(plan.ir, ir);
    assert_eq!(plan.modules.len(), 1);
    assert_eq!(plan.modules[0].name, "api.service");
    assert_eq!(
        serde_json::to_value(&plan.modules[0].imports).unwrap(),
        canonical["imports"]
    );
    assert_eq!(
        serde_json::to_value(&plan.modules[0].declarations).unwrap(),
        canonical["declarations"]
    );
    let callables = plan
        .callables()
        .into_iter()
        .map(|callable| (callable.symbol.clone(), callable))
        .collect::<BTreeMap<_, _>>();
    assert_eq!(
        callables
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>(),
        BTreeSet::from([
            "api.service.default_read",
            "api.service.run",
            "api.service.ReaderState.read",
            "api.service.ReaderState.label",
        ])
    );
    for symbol in ["api.service.default_read", "api.service.run"] {
        let callable = &callables[symbol];
        assert!(callable.owner.is_none());
        assert_eq!(callable.declaration["name"], symbol);
    }
    let default = &callables["api.service.ReaderState.read"];
    assert!(default.owner.is_some());
    assert_eq!(default.declaration["selected"]["origin"], "default");
    assert_eq!(
        default.declaration["receiver_type"]["name"],
        "api.service.ReaderState"
    );
    let explicit = &callables["api.service.ReaderState.label"];
    assert!(explicit.owner.is_some());
    assert_eq!(explicit.declaration["selected"]["origin"], "explicit");
    assert_eq!(
        explicit.declaration["receiver_type"]["name"],
        "api.service.ReaderState"
    );
}
