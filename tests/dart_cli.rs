use cott::dart::DartOwner;
use cott::dart::provenance::{DartBindingRecord, DartGenerationRecord};
use cott::hash::sha256_hex;
use cott::project::{discover_dart_contract_sources, load_dart_config_with_paths};
use cott::provenance::{AgentRun, AgentStatus, StreamDigest};
use cott::transaction::InputSnapshot;
#[cfg(unix)]
use std::ffi::CString;
use std::fs;
use std::io;
#[cfg(unix)]
use std::os::unix::ffi::OsStrExt;
use std::path::{Path, PathBuf};
#[cfg(unix)]
use std::process::Stdio;
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};
#[cfg(unix)]
use std::time::{Duration, Instant};

#[path = "support/snapshot.rs"]
mod snapshot_wire;

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-dart-cli-tests-{}-{number}",
                std::process::id()
            ));
            match fs::create_dir(&path) {
                Ok(()) => return Self { path },
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => number += 1,
                Err(error) => panic!("create temporary directory: {error}"),
            }
        }
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

fn run(root: &Path, arguments: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(arguments)
        .arg("--project")
        .arg(root)
        .output()
        .expect("cott should run")
}

#[cfg(unix)]
fn run_bounded(root: &Path, arguments: &[&str]) -> Output {
    let mut child = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(arguments)
        .arg("--project")
        .arg(root)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("cott should start");
    let deadline = Instant::now() + Duration::from_secs(10);
    loop {
        if child.try_wait().expect("inspect cott process").is_some() {
            return child.wait_with_output().expect("collect cott output");
        }
        if Instant::now() >= deadline {
            child.kill().expect("kill hung cott process");
            child.wait().expect("reap hung cott process");
            panic!("cott did not reject a non-regular generation record within 10 seconds");
        }
        std::thread::yield_now();
    }
}

fn digest(bytes: &[u8]) -> String {
    format!("sha256:{}", sha256_hex(bytes))
}

fn fixture_digest(byte: u8) -> String {
    format!("sha256:{}", format!("{byte:02x}").repeat(32))
}

fn dart_project(source: &str) -> TempDir {
    let temp = TempDir::new();
    fs::create_dir_all(temp.path.join("src/demo")).expect("contract source directory");
    fs::create_dir(temp.path.join("dart")).expect("Dart source directory");
    fs::write(
        temp.path.join("cott.toml"),
        r#"[project]
name = "demo"
version = "0.1.0"
source = "src"

[target.dart]
source = "dart"
generated = "generated/dart"
sdk = "definitely-missing-dart-sdk"
runtime_validation = "boundary"
"#,
    )
    .expect("Dart manifest");
    fs::write(temp.path.join("src/demo/main.cott"), source).expect("Cott source");
    temp
}

/// Re-create the previous IR8/strategy5 publication of the verified Flutter counter module.
/// Only the compiler-owned IR bytes, the schema markers and the generation identity that
/// covers them change; source, implementation, AgentRun and verification evidence stay
/// the authentic example bytes.
fn flutter_legacy_project() -> TempDir {
    let temp = TempDir::new();
    let original =
        Path::new(env!("CARGO_MANIFEST_DIR")).join("examples/integrations/flutter-counter");
    let generation = fs::read(original.join("generated/generation.json"))
        .expect("verified example Dart generation record");
    DartGenerationRecord::parse(&generation).expect("current verified example record");
    let mut wire = snapshot_wire::read(&generation);
    assert_eq!(wire["current"]["verified"], true);
    assert_eq!(wire["current"], wire["last_verified"]);
    let current = &wire["current"];
    let inputs = current["inputs"].as_object().expect("source inputs");
    let managed = current["managed_files"].as_object().expect("managed files");
    for name in inputs.keys().chain(managed.keys()) {
        let target = temp.path.join(name);
        fs::create_dir_all(target.parent().expect("relative fixture path"))
            .expect("create fixture directory");
        fs::copy(original.join(name), target).expect("copy authenticated fixture bytes");
    }

    let current = &mut wire["current"];
    let modules = current["ir"]
        .as_object()
        .expect("IR hashes")
        .keys()
        .cloned()
        .collect::<Vec<_>>();
    for module in modules {
        let path = format!("generated/ir/{}.json", module.replace('.', "/"));
        let mut ir: serde_json::Value =
            serde_json::from_slice(&fs::read(temp.path.join(&path)).expect("current IR"))
                .expect("IR JSON");
        assert_eq!(ir["schema_version"], 9);
        ir["schema_version"] = serde_json::json!(8);
        let mut bytes = serde_json::to_vec(&ir).expect("legacy IR JSON");
        bytes.push(b'\n');
        fs::write(temp.path.join(&path), &bytes).expect("legacy IR bytes");
        current["ir"][&module] = serde_json::json!(digest(&bytes));
        current["managed_files"][&path] = serde_json::json!(digest(&bytes));
    }
    current["canonical_ir_schema"] = serde_json::json!(8);
    for strategy in current["verification"]["contract_tests"]["strategies"]
        .as_array_mut()
        .expect("verified contract strategies")
    {
        assert_eq!(strategy["schema_version"], 6);
        strategy["schema_version"] = serde_json::json!(5);
    }
    let mut identity = current.clone();
    for field in [
        "generation_id",
        "verified",
        "verification",
        "semantic_coverage",
        "agent_runs",
    ] {
        identity
            .as_object_mut()
            .expect("snapshot object")
            .remove(field);
    }
    current["generation_id"] = serde_json::json!(
        cott::snapshot_record::digest(&serde_json::json!({
            "domain": "cott.dart.generation.v2",
            "schema_version": 2,
            "current": identity,
        }))
        .expect("seal legacy Dart generation identity")
    );
    wire["last_verified"] = wire["current"].clone();
    fs::write(
        temp.path.join("generated/generation.json"),
        snapshot_wire::bytes(&wire),
    )
    .expect("legacy provenance");
    temp
}

#[test]
fn legacy_flutter_emit_preserves_authenticated_agent_sources_and_decertifies() {
    let project = flutter_legacy_project();
    let generation = project.path.join("generated/generation.json");
    let old_bytes = fs::read(&generation).expect("legacy record");
    let old = snapshot_wire::read(&old_bytes);

    for command in [
        &["check"][..],
        &["verify"][..],
        &["diff"][..],
        &["requirements"][..],
        &["deploy"][..],
        &["prompt", "example.counter.increment"][..],
    ] {
        let rejected = run(&project.path, command);
        assert_ne!(
            rejected.status.code(),
            Some(0),
            "old Dart record unexpectedly accepted by {command:?}"
        );
        assert_eq!(fs::read(&generation).unwrap(), old_bytes);
    }

    let emitted = run(&project.path, &["emit", "dart"]);
    assert_eq!(
        emitted.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let converted = DartGenerationRecord::parse(&fs::read(&generation).unwrap())
        .expect("emit must publish a fully authenticated current record");
    assert_eq!(
        converted.current.canonical_ir_schema,
        cott::provenance::CANONICAL_IR_SCHEMA_VERSION
    );
    assert!(!converted.current.verified);
    assert!(converted.last_verified.is_none());
    let original_runs: Vec<AgentRun> =
        serde_json::from_value(old["current"]["agent_runs"].clone()).unwrap();
    let original_implementations: Vec<DartBindingRecord> =
        serde_json::from_value(old["current"]["implementations"].clone()).unwrap();
    assert_eq!(converted.current.agent_runs, original_runs);
    assert_eq!(converted.current.implementations, original_implementations);
    for (name, expected) in old["current"]["inputs"].as_object().unwrap() {
        assert_eq!(
            digest(&fs::read(project.path.join(name)).unwrap()),
            expected.as_str().unwrap()
        );
    }
}

#[test]
fn legacy_flutter_emit_rejects_broken_snapshot_and_changed_source() {
    let project = flutter_legacy_project();
    let generation = project.path.join("generated/generation.json");
    let original = fs::read(&generation).unwrap();
    let mut tampered: serde_json::Value = serde_json::from_slice(&original).unwrap();
    let current = tampered["current"].as_str().unwrap().to_owned();
    tampered["snapshots"][&current]["agent_runs"][0]["duration_ms"] = serde_json::json!(12);
    let tampered = serde_json::to_vec(&tampered).unwrap();
    fs::write(&generation, &tampered).unwrap();
    assert_eq!(run(&project.path, &["emit", "dart"]).status.code(), Some(4));
    assert_eq!(fs::read(&generation).unwrap(), tampered);
    let mut resealed = snapshot_wire::read(&original);
    resealed["current"]["project_name"] = serde_json::json!("forged");
    resealed["last_verified"]["project_name"] = serde_json::json!("forged");
    let resealed = snapshot_wire::bytes(&resealed);
    fs::write(&generation, &resealed).unwrap();
    assert_eq!(run(&project.path, &["emit", "dart"]).status.code(), Some(4));
    assert_eq!(fs::read(&generation).unwrap(), resealed);
    let mut wrong_strategy = snapshot_wire::read(&original);
    for snapshot in ["current", "last_verified"] {
        wrong_strategy[snapshot]["verification"]["contract_tests"]["strategies"][0]["schema_version"] =
            serde_json::json!(6);
    }
    let wrong_strategy = snapshot_wire::bytes(&wrong_strategy);
    fs::write(&generation, &wrong_strategy).unwrap();
    assert_eq!(run(&project.path, &["emit", "dart"]).status.code(), Some(4));
    assert_eq!(fs::read(&generation).unwrap(), wrong_strategy);

    fs::write(&generation, &original).unwrap();
    let source = project
        .path
        .join("dart/cott_impl/example/counter/increment.dart");
    let mut changed_source = fs::read(&source).unwrap();
    changed_source.extend_from_slice(b"\n// drift\n");
    fs::write(&source, changed_source).unwrap();
    assert_eq!(run(&project.path, &["emit", "dart"]).status.code(), Some(4));
    assert_eq!(fs::read(&generation).unwrap(), original);
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart SDK"]
fn legacy_flutter_emit_then_real_verify_certifies_new_schema() {
    let project = flutter_legacy_project();
    let emitted = run(&project.path, &["emit", "dart"]);
    assert_eq!(
        emitted.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let dart =
        PathBuf::from(std::env::var_os("COTT_DART").expect("provisioned Dart SDK executable"));
    let mut path = vec![dart.parent().expect("Dart SDK bin directory").to_path_buf()];
    path.extend(std::env::split_paths(
        &std::env::var_os("PATH").unwrap_or_default(),
    ));
    let verified = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(["verify", "--project"])
        .arg(&project.path)
        .env("PATH", std::env::join_paths(path).unwrap())
        .output()
        .expect("native Dart verify should run");
    assert_eq!(
        verified.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
    let record = DartGenerationRecord::parse(
        &fs::read(project.path.join("generated/generation.json")).unwrap(),
    )
    .unwrap();
    assert!(record.current.verified);
    assert_eq!(record.last_verified, Some(record.current));
}

#[test]
fn dart_init_is_module_only_and_atomic_without_tooling() {
    let parent = TempDir::new();
    let target = parent.path.join("counter_module");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(["init", "--target", "dart", "--no-sync"])
        .arg(&target)
        .env_clear()
        .output()
        .expect("cott init should run");
    assert_eq!(
        output.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let manifest = fs::read_to_string(target.join("cott.toml")).expect("Dart manifest");
    assert!(manifest.contains("[target.dart]"));
    assert!(manifest.contains("sdk = \"dart\""));
    assert!(!manifest.contains("target.python"));
    assert!(!manifest.contains("target.kotlin"));
    assert_eq!(
        fs::read_to_string(target.join("src/counter_module/main.cott")).expect("contract"),
        "module counter_module.main\n"
    );
    assert!(target.join("dart").is_dir());
    assert!(!target.join("flutter").exists());
    assert!(!target.join("python").exists());
    assert!(!target.join("kotlin").exists());
    assert!(!target.join(".cott-init").exists());

    fs::write(target.join("keep"), b"unchanged").expect("sentinel");
    let repeated = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(["init", "--target", "dart", "--no-sync"])
        .arg(&target)
        .output()
        .expect("second cott init should run");
    assert_eq!(repeated.status.code(), Some(2));
    assert_eq!(
        fs::read(target.join("keep")).expect("sentinel retained"),
        b"unchanged"
    );
}

#[test]
fn dart_ir_and_full_emit_record_truthful_pending_state() {
    let project = dart_project("module demo.main\n\nfn main() -> Unit\n");
    let ir = run(&project.path, &["emit", "ir"]);
    assert_eq!(
        ir.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&ir.stderr)
    );
    let generation = project.path.join("generated/generation.json");
    let record = snapshot_wire::read(&fs::read(&generation).expect("generation record"));
    assert_eq!(record["schema_version"], 2);
    assert_eq!(record["current"]["target"], "dart");
    assert_eq!(record["current"]["verified"], false);
    assert_eq!(
        record["current"]["unresolved"],
        serde_json::json!(["demo.main.main"])
    );
    assert!(
        record["current"]["public_symbols"]
            .get("demo.main")
            .is_some()
    );
    assert!(record["current"].get("public_python_symbols").is_none());
    assert!(project.path.join("generated/ir/demo/main.json").is_file());
    assert!(!project.path.join("generated/dart/pubspec.yaml").exists());

    let dart = run(&project.path, &["emit", "dart"]);
    assert_eq!(
        dart.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&dart.stderr)
    );
    assert!(project.path.join("generated/dart/pubspec.yaml").is_file());
    assert!(
        project
            .path
            .join("generated/dart/lib/modules/demo/main.dart")
            .is_file()
    );
    let record = snapshot_wire::read(&fs::read(generation).expect("generation record"));
    assert_eq!(
        record["current"]["unresolved"],
        serde_json::json!(["demo.main.main"])
    );
    assert!(record["current"]["dependencies"].is_object());
    assert!(
        record["current"]["managed_files"]
            .as_object()
            .expect("managed files")
            .keys()
            .all(|path| !path.contains("python") && !path.contains("kotlin"))
    );
}

#[test]
fn dart_emit_refuses_unowned_output_without_deleting_it() {
    let project = dart_project("module demo.main\n\nfn main() -> Unit\n");
    assert_eq!(run(&project.path, &["emit", "ir"]).status.code(), Some(0));
    let foreign = project.path.join("generated/foreign.bin");
    fs::write(&foreign, b"keep me").expect("foreign output");

    let rejected = run(&project.path, &["emit", "dart"]);
    assert_eq!(rejected.status.code(), Some(4));
    assert!(String::from_utf8_lossy(&rejected.stderr).contains("unowned Dart artifact"));
    assert_eq!(
        fs::read(&foreign).expect("foreign output retained"),
        b"keep me"
    );
    assert!(!project.path.join("generated/dart/pubspec.yaml").exists());
}

#[test]
fn dart_source_paths_and_format_drift_are_checked_without_an_sdk() {
    let project = dart_project("module demo.main\n\nfn main( ) -> Unit\n");
    let check = run(&project.path, &["fmt", "--check"]);
    assert_eq!(check.status.code(), Some(8));
    assert!(String::from_utf8_lossy(&check.stderr).contains("formatting differs"));

    let formatted = run(&project.path, &["fmt"]);
    assert_eq!(
        formatted.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&formatted.stderr)
    );
    assert_eq!(
        fs::read_to_string(project.path.join("src/demo/main.cott")).expect("formatted source"),
        "module demo.main\n\nfn main() -> Unit\n"
    );

    let escaped = run(&project.path, &["check", "../outside.cott"]);
    assert_eq!(escaped.status.code(), Some(2));
    assert!(String::from_utf8_lossy(&escaped.stderr).contains("invalid check source"));
}

#[test]
fn dart_format_does_not_require_resolvable_implementations() {
    let project = dart_project("module demo.main\n\nfn answer( ) -> Unit\n");
    fs::create_dir_all(project.path.join("dart/cott_impl/demo/main"))
        .expect("durable agent directory");
    fs::write(
        project.path.join("dart/cott_impl/demo/main/answer.dart"),
        "void _cott_demo_main_answer() {}\n",
    )
    .expect("durable agent source");

    let rejected = run(&project.path, &["check"]);
    assert_eq!(
        rejected.status.code(),
        Some(4),
        "{}",
        String::from_utf8_lossy(&rejected.stderr)
    );

    let formatted = run(&project.path, &["fmt"]);
    assert_eq!(
        formatted.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&formatted.stderr)
    );
    assert_eq!(
        fs::read_to_string(project.path.join("src/demo/main.cott")).expect("formatted source"),
        "module demo.main\n\nfn answer() -> Unit\n"
    );
}

#[test]
fn consumed_manifest_and_contract_bytes_cannot_be_refreshed() {
    let project = dart_project("module demo.main\n\nfn main() -> Unit\n");
    let (_, paths, manifest_source) =
        load_dart_config_with_paths(&project.path).expect("Dart project");
    assert_eq!(
        manifest_source.as_bytes(),
        fs::read(&paths.manifest).expect("manifest bytes")
    );
    fs::write(
        &paths.manifest,
        format!("{manifest_source}\n# replaced after parsing\n"),
    )
    .expect("replace manifest");
    assert!(
        InputSnapshot::capture_expected(
            &paths.root,
            [(
                PathBuf::from("cott.toml"),
                digest(manifest_source.as_bytes())
            )],
            std::iter::empty(),
        )
        .is_err()
    );

    fs::write(&paths.manifest, &manifest_source).expect("restore manifest");
    let sources = discover_dart_contract_sources(&paths).expect("consumed Cott sources");
    let source = sources
        .iter()
        .find(|source| source.path == Path::new("demo/main.cott"))
        .expect("main Cott source");
    let source_path = paths.source_dir.join(&source.path);
    fs::write(&source_path, "module demo.main\n\nfn main() -> I32\n")
        .expect("replace Cott source after parsing");
    assert!(
        InputSnapshot::capture_expected(
            &paths.root,
            [(
                source_path
                    .strip_prefix(&paths.root)
                    .expect("project-relative source")
                    .to_path_buf(),
                digest(source.text.as_bytes()),
            )],
            std::iter::empty(),
        )
        .is_err()
    );
}

#[test]
fn missing_accepted_agent_source_becomes_pending_without_losing_verified_history() {
    let project = dart_project("module demo.main\n\nfn main(value: I32) -> I32\n");
    let initial = run(&project.path, &["emit", "dart"]);
    assert_eq!(
        initial.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&initial.stderr)
    );

    let generation = project.path.join("generated/generation.json");
    let mut record =
        DartGenerationRecord::parse(&fs::read(&generation).expect("generation record"))
            .expect("valid Dart generation record");
    let source_origin = "dart/cott_impl/demo/main/main.dart".to_owned();
    let accepted_source = b"int _cott_demo_main_main(int value) {\n  return value;\n}\n";
    let implementation_hash = digest(accepted_source);
    record
        .current
        .inputs
        .insert(source_origin.clone(), implementation_hash.clone());
    record.current.implementations = vec![DartBindingRecord {
        cott_symbol: "demo.main.main".to_owned(),
        target_symbol: "cott_impl/demo/main/main.dart:_cott_demo_main_main".to_owned(),
        source_origin: source_origin.clone(),
        runtime_origin: "dart/lib/src/cott_impl/demo/main/main.dart".to_owned(),
        content_hash: implementation_hash.clone(),
        owner: DartOwner::Agent,
    }];
    record.current.unresolved.clear();
    record.current.agent_runs = vec![AgentRun {
        symbol: "demo.main.main".to_owned(),
        adapter: "codex".to_owned(),
        adapter_version: "fixture".to_owned(),
        argv_template: vec!["codex".to_owned()],
        executable: "/fixture/agent".to_owned(),
        executable_hash: fixture_digest(1),
        prompt_hash: fixture_digest(2),
        implementation_hash: implementation_hash.clone(),
        environment_names: Vec::new(),
        duration_ms: 1,
        status: AgentStatus {
            exit_code: Some(0),
            signal: None,
            timed_out: false,
            cancelled: false,
        },
        stdout: StreamDigest {
            bytes: 0,
            sha256: fixture_digest(3),
            truncated: false,
        },
        stderr: StreamDigest {
            bytes: 0,
            sha256: fixture_digest(4),
            truncated: false,
        },
    }];
    record.current.verified = true;
    record.current.verification = serde_json::json!({"fixture": "accepted"});
    record
        .current
        .compute_generation_id()
        .expect("accepted snapshot identity");
    let accepted = record.current.clone();
    record.last_verified = Some(accepted.clone());
    fs::write(
        &generation,
        record
            .canonical_bytes()
            .expect("accepted generation record"),
    )
    .expect("write accepted generation record");

    let source_path = project.path.join(&source_origin);
    fs::create_dir_all(source_path.parent().expect("agent source parent"))
        .expect("agent source parent");
    fs::write(
        &source_path,
        b"int _cott_demo_main_main(int value) {\n  return value + 1;\n}\n",
    )
    .expect("changed agent source");
    let accepted_record_bytes = fs::read(&generation).expect("accepted generation bytes");
    let changed = run(&project.path, &["emit", "dart"]);
    assert_eq!(changed.status.code(), Some(4));
    assert_eq!(
        fs::read(&generation).expect("generation remains accepted"),
        accepted_record_bytes
    );

    fs::remove_file(&source_path).expect("remove accepted agent source");
    let repaired = run(&project.path, &["emit", "dart"]);
    assert_eq!(
        repaired.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&repaired.stderr)
    );
    let pending =
        DartGenerationRecord::parse(&fs::read(&generation).expect("pending generation record"))
            .expect("valid pending Dart record");
    assert!(!pending.current.verified);
    assert_eq!(
        pending.current.unresolved,
        vec!["demo.main.main".to_owned()]
    );
    assert!(!pending.current.inputs.contains_key(&source_origin));
    assert!(pending.current.implementations.is_empty());
    assert!(pending.current.agent_runs.is_empty());
    assert_eq!(pending.last_verified, Some(accepted));
}

#[cfg(unix)]
#[test]
fn nonregular_generation_record_is_rejected_without_blocking() {
    let project = dart_project("module demo.main\n\nfn main() -> Unit\n");
    let generated = project.path.join("generated");
    fs::create_dir(&generated).expect("artifact root");
    let generation = generated.join("generation.json");
    let fifo = CString::new(generation.as_os_str().as_bytes())
        .expect("temporary FIFO path should not contain NUL");
    assert_eq!(unsafe { libc::mkfifo(fifo.as_ptr(), 0o600) }, 0);

    let fifo_output = run_bounded(&project.path, &["check"]);
    assert_eq!(fifo_output.status.code(), Some(6));
    assert!(String::from_utf8_lossy(&fifo_output.stderr).contains("regular non-symlink"));
    fs::remove_file(&generation).expect("remove FIFO");

    let target = project.path.join("foreign-generation.json");
    fs::write(&target, b"{}").expect("symlink target");
    std::os::unix::fs::symlink(&target, &generation).expect("generation symlink");
    let symlink_output = run_bounded(&project.path, &["check"]);
    assert_eq!(symlink_output.status.code(), Some(6));
    assert!(String::from_utf8_lossy(&symlink_output.stderr).contains("generation record"));
    fs::remove_file(&generation).expect("remove generation symlink");
    let emitted = run(&project.path, &["emit", "ir"]);
    assert_eq!(
        emitted.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let second_link = project.path.join("generation-hardlink.json");
    fs::hard_link(&generation, &second_link).expect("generation hard link");
    let hardlink_output = run_bounded(&project.path, &["check"]);
    assert_eq!(hardlink_output.status.code(), Some(6));
    assert!(String::from_utf8_lossy(&hardlink_output.stderr).contains("single-link"));
}

#[test]
fn manifest_binding_keeps_original_identity_separate_from_managed_private_part() {
    let project = dart_project("module demo.main\n\nfn main(value: I32) -> I32\n");
    let manifest_path = project.path.join("cott.toml");
    let mut manifest = fs::read_to_string(&manifest_path).expect("manifest");
    manifest.push_str(
        "\n[target.dart.implementations]\n\"demo.main.main\" = \"bindings/main.dart:_main\"\n",
    );
    fs::write(&manifest_path, manifest).expect("manifest implementation");
    let authored = b"import 'dart:math' as math;\n\nint _main(int value) {\n  return math.min(value, value);\n}\n";
    fs::create_dir_all(project.path.join("dart/bindings")).expect("binding directory");
    fs::write(project.path.join("dart/bindings/main.dart"), authored).expect("binding");

    let emitted = run(&project.path, &["emit", "dart"]);
    assert_eq!(
        emitted.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let record = DartGenerationRecord::parse(
        &fs::read(project.path.join("generated/generation.json")).expect("generation record"),
    )
    .expect("valid Dart generation record");
    let implementation = record
        .current
        .implementations
        .iter()
        .find(|implementation| implementation.cott_symbol == "demo.main.main")
        .expect("manifest implementation identity");
    assert_eq!(implementation.owner, DartOwner::Manifest);
    assert_eq!(implementation.content_hash, digest(authored));
    assert_eq!(
        implementation.runtime_origin,
        "dart/lib/src/cott_impl/demo/main/main.dart"
    );

    let managed_path = project
        .path
        .join("generated/dart/lib/src/cott_impl/demo/main/main.dart");
    let managed = fs::read(&managed_path).expect("managed private part");
    assert_ne!(managed, authored);
    let managed_key = "generated/dart/lib/src/cott_impl/demo/main/main.dart";
    assert_eq!(
        record.current.managed_files.get(managed_key),
        Some(&digest(&managed))
    );
    assert_ne!(
        record.current.managed_files.get(managed_key),
        Some(&implementation.content_hash)
    );
}

#[test]
fn removing_a_manifest_binding_leaves_the_callable_unresolved() {
    let project = dart_project("module demo.main\n\nfn main(value: I32) -> I32\n");
    let manifest_path = project.path.join("cott.toml");
    let unbound = fs::read_to_string(&manifest_path).expect("manifest");
    fs::write(
        &manifest_path,
        format!(
            "{unbound}\n[target.dart.implementations]\n\"demo.main.main\" = \"bindings/main.dart:_main\"\n"
        ),
    )
    .expect("manifest implementation");
    fs::create_dir_all(project.path.join("dart/bindings")).expect("binding directory");
    fs::write(
        project.path.join("dart/bindings/main.dart"),
        b"int _main(int value) {\n  return value;\n}\n",
    )
    .expect("binding");
    let bound = run(&project.path, &["emit", "dart"]);
    assert_eq!(
        bound.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&bound.stderr)
    );

    fs::write(&manifest_path, unbound).expect("remove manifest binding");
    fs::remove_dir_all(project.path.join("dart/bindings")).expect("remove binding source");
    let emitted = run(&project.path, &["emit", "dart"]);
    assert_eq!(
        emitted.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let record = DartGenerationRecord::parse(
        &fs::read(project.path.join("generated/generation.json")).expect("generation record"),
    )
    .expect("valid Dart generation record");
    assert!(record.current.implementations.is_empty());
    assert_eq!(record.current.unresolved, ["demo.main.main"]);
}

#[test]
fn deploy_publishes_only_the_verified_portable_dart_package_without_overwrite() {
    let project = dart_project("module demo.main\n\nfn main(value: I32) -> I32\n");
    let manifest_path = project.path.join("cott.toml");
    let mut manifest = fs::read_to_string(&manifest_path).expect("manifest");
    manifest.push_str(
        "pubspec = \"dart_package/pubspec.yaml\"\nlockfile = \"dart_package/pubspec.lock\"\n\n[target.dart.implementations]\n\"demo.main.main\" = \"bindings/main.dart:_main\"\n",
    );
    fs::write(&manifest_path, manifest).expect("manifest implementation");
    let authored = b"int _main(int value) {\n  return value;\n}\n";
    fs::create_dir_all(project.path.join("dart/bindings")).expect("binding directory");
    fs::write(project.path.join("dart/bindings/main.dart"), authored).expect("binding");
    fs::create_dir_all(project.path.join("dart_package")).expect("metadata directory");
    fs::write(
        project.path.join("dart_package/pubspec.yaml"),
        "name: demo\nversion: 0.1.0\nenvironment:\n  sdk: \">=3.13.3 <4.0.0\"\ndependencies:\n  selected_dep:\n    path: ../third_party/selected_dep\n",
    )
    .expect("authored pubspec");
    fs::write(
        project.path.join("dart_package/pubspec.lock"),
        "packages:\n  selected_dep:\n    dependency: \"direct main\"\n    description:\n      path: \"../third_party/selected_dep\"\n      relative: true\n    source: path\n    version: \"1.2.3\"\nsdks:\n  dart: \">=3.13.3 <4.0.0\"\n",
    )
    .expect("authored lockfile");
    fs::create_dir_all(project.path.join("third_party/selected_dep/lib")).expect("path dependency");
    let dependency_pubspec =
        b"name: selected_dep\nversion: 1.2.3\nenvironment:\n  sdk: \">=3.13.3 <4.0.0\"\n";
    let dependency_library = b"int selectedIdentity(int value) => value;\n";
    fs::write(
        project.path.join("third_party/selected_dep/pubspec.yaml"),
        dependency_pubspec,
    )
    .expect("path dependency pubspec");
    fs::write(
        project
            .path
            .join("third_party/selected_dep/lib/selected_dep.dart"),
        dependency_library,
    )
    .expect("path dependency library");
    let emitted = run(&project.path, &["emit", "dart"]);
    assert_eq!(
        emitted.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );

    let generation_path = project.path.join("generated/generation.json");
    let mut record =
        DartGenerationRecord::parse(&fs::read(&generation_path).expect("generation record"))
            .expect("valid Dart generation record");
    let mut dependencies =
        serde_json::to_vec(&record.current.dependencies).expect("dependency record");
    dependencies.push(b'\n');
    let dependencies_path = project.path.join("generated/dart/dependencies.json");
    fs::write(&dependencies_path, &dependencies).expect("verified dependency material");
    record.current.managed_files.insert(
        "generated/dart/dependencies.json".to_owned(),
        digest(&dependencies),
    );
    let vendor = project.path.join("generated/dart/vendor/selected_dep");
    fs::create_dir_all(vendor.join("lib")).expect("verified vendor package");
    fs::write(vendor.join("pubspec.yaml"), dependency_pubspec).expect("verified vendor pubspec");
    fs::write(vendor.join("lib/selected_dep.dart"), dependency_library)
        .expect("verified vendor library");
    record.current.managed_files.insert(
        "generated/dart/vendor/selected_dep/pubspec.yaml".to_owned(),
        digest(dependency_pubspec),
    );
    record.current.managed_files.insert(
        "generated/dart/vendor/selected_dep/lib/selected_dep.dart".to_owned(),
        digest(dependency_library),
    );
    let kernel = b"fixture Dart kernel";
    let kernel_path = project
        .path
        .join("generated/dart/verification/cott-module.dill");
    fs::create_dir_all(kernel_path.parent().expect("kernel parent"))
        .expect("verification directory");
    fs::write(&kernel_path, kernel).expect("verified kernel");
    record.current.managed_files.insert(
        "generated/dart/verification/cott-module.dill".to_owned(),
        digest(kernel),
    );
    record.current.verified = true;
    record.current.verification = serde_json::json!({"fixture": "portable-package"});
    record
        .current
        .compute_generation_id()
        .expect("verified generation identity");
    record.last_verified = Some(record.current.clone());
    let generation_bytes = record
        .canonical_bytes()
        .expect("verified generation record");
    fs::write(&generation_path, &generation_bytes).expect("verified generation record");

    let deployed = run(&project.path, &["deploy"]);
    assert_eq!(
        deployed.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&deployed.stderr)
    );
    let output = project.path.join("dist/demo-0.1.0");
    assert_eq!(
        fs::read(output.join("generation.json")).expect("deployed generation"),
        generation_bytes
    );
    assert_eq!(
        fs::read(output.join("dependencies.json")).expect("deployed dependency closure"),
        dependencies
    );
    let deployed_dependencies: serde_json::Value =
        serde_json::from_slice(&dependencies).expect("deployed dependency JSON");
    assert_eq!(deployed_dependencies["packages"][0]["name"], "selected_dep");
    assert_eq!(
        deployed_dependencies["packages"][0]["source_identity"],
        "third_party/selected_dep"
    );
    assert_eq!(
        fs::read(output.join("vendor/selected_dep/lib/selected_dep.dart"))
            .expect("vendored dependency library"),
        dependency_library
    );
    assert!(
        fs::read_to_string(output.join("pubspec.yaml"))
            .expect("deployed pubspec")
            .contains("vendor/selected_dep")
    );
    assert!(output.join("pubspec.yaml").is_file());
    assert!(output.join("lib/cott_runtime.dart").is_file());
    assert!(
        output
            .join("lib/src/cott_impl/demo/main/main.dart")
            .is_file()
    );
    assert!(!output.join("ir").exists());
    assert!(!output.join("verification").exists());
    assert!(!output.join("src").exists());
    assert!(!output.join("dart/bindings/main.dart").exists());
    assert!(!output.join("pubspec.lock").exists());

    let runtime_before =
        fs::read(output.join("lib/cott_runtime.dart")).expect("deployed runtime bytes");
    let repeated = run(&project.path, &["deploy"]);
    assert_eq!(repeated.status.code(), Some(6));
    assert_eq!(
        fs::read(output.join("lib/cott_runtime.dart")).expect("runtime retained"),
        runtime_before
    );

    fs::write(output.join("stale.txt"), b"old tree\n").expect("stale marker");
    let replaced = run(&project.path, &["deploy", "--replace"]);
    assert_eq!(
        replaced.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&replaced.stderr)
    );
    assert!(!output.join("stale.txt").exists());
    assert_eq!(
        fs::read(output.join("lib/cott_runtime.dart")).expect("replaced runtime"),
        runtime_before
    );
    let dist = output.parent().expect("deployment parent");
    let leftovers = fs::read_dir(dist)
        .expect("dist should be readable")
        .filter_map(|entry| entry.ok())
        .filter(|entry| {
            entry
                .file_name()
                .to_string_lossy()
                .starts_with(".cott-deploy")
        })
        .map(|entry| entry.path())
        .collect::<Vec<_>>();
    assert!(
        leftovers.is_empty(),
        "Dart replace left temporary directories: {leftovers:?}"
    );

    // A valid record for another project is not ownership evidence for demo,
    // even when its target and version match.
    let mut foreign_record = record.clone();
    foreign_record.current.project_name = "foreign".to_owned();
    foreign_record
        .current
        .compute_generation_id()
        .expect("foreign fixture identity");
    foreign_record.last_verified = Some(foreign_record.current.clone());
    let foreign_bytes = foreign_record
        .canonical_bytes()
        .expect("foreign fixture record");
    fs::write(output.join("generation.json"), &foreign_bytes).expect("foreign deployment record");
    let rejected = run(&project.path, &["deploy", "--replace"]);
    assert_eq!(rejected.status.code(), Some(6));
    assert_eq!(
        fs::read(output.join("generation.json")).unwrap(),
        foreign_bytes
    );
    assert_eq!(
        fs::read(output.join("lib/cott_runtime.dart")).unwrap(),
        runtime_before
    );
    fs::write(output.join("generation.json"), &generation_bytes)
        .expect("restore deployment record");

    #[cfg(unix)]
    {
        let alias = project.path.join("linked-dist");
        std::os::unix::fs::symlink(dist, &alias).expect("deployment ancestor symlink");
        let alias_output = alias.join("demo-0.1.0");
        let rejected = run(
            &project.path,
            &[
                "deploy",
                "--replace",
                "--output",
                alias_output.to_str().unwrap(),
            ],
        );
        assert_eq!(rejected.status.code(), Some(6));
        assert_eq!(
            fs::read(output.join("generation.json")).unwrap(),
            generation_bytes
        );

        let retained = project.path.join("retained-generation.json");
        fs::rename(output.join("generation.json"), &retained).expect("retain deployment record");
        std::os::unix::fs::symlink(&retained, output.join("generation.json"))
            .expect("generation symlink");
        let rejected = run_bounded(&project.path, &["deploy", "--replace"]);
        assert_eq!(rejected.status.code(), Some(6));
        assert_eq!(fs::read(&retained).unwrap(), generation_bytes);
        fs::remove_file(output.join("generation.json")).expect("remove test symlink");
        fs::rename(retained, output.join("generation.json")).expect("restore deployment record");
    }

    fs::write(
        project
            .path
            .join("generated/dart/lib/src/cott_impl/demo/main/main.dart"),
        b"drift",
    )
    .expect("managed drift");
    let drifted = run(&project.path, &["deploy"]);
    assert_eq!(drifted.status.code(), Some(4));
    assert_eq!(
        fs::read(output.join("lib/cott_runtime.dart")).expect("deployed runtime unchanged"),
        runtime_before
    );
}

#[test]
fn dart_diff_and_unresolved_verify_keep_exit_codes_and_json_diagnostics() {
    let missing = dart_project("module demo.main\n\nfn main() -> Unit\n");
    let diff = run(&missing.path, &["diff", "--format", "json"]);
    assert_eq!(diff.status.code(), Some(2));
    assert!(diff.stderr.is_empty());
    let report: serde_json::Value =
        serde_json::from_slice(&diff.stdout).expect("Dart diff JSON diagnostic");
    assert_eq!(report["schema_version"], 1);
    assert_eq!(report["diagnostics"][0]["code"], "COTT-C001");

    let verify = run(&missing.path, &["verify", "--format", "json"]);
    assert_eq!(verify.status.code(), Some(4));
    assert!(verify.stderr.is_empty());
    let report: serde_json::Value =
        serde_json::from_slice(&verify.stdout).expect("Dart verify JSON diagnostic");
    assert_eq!(report["schema_version"], 1);
    assert_eq!(report["diagnostics"][0]["code"], "COTT-D201");
}
