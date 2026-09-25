use cott::hash::sha256_hex;
use cott::kotlin::KotlinOwner;
use cott::kotlin::provenance::{
    KOTLIN_GENERATION_SCHEMA_VERSION, KotlinBindingRecord, KotlinGenerationRecord,
};
use cott::project::{discover_kotlin_contract_sources, load_kotlin_config_with_paths};
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
mod snapshot;

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-kotlin-cli-tests-{}-{number}",
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

fn kotlin_project(source: &str) -> TempDir {
    let temp = TempDir::new();
    fs::create_dir_all(temp.path.join("src/demo")).expect("contract source directory");
    fs::create_dir(temp.path.join("kotlin")).expect("Kotlin source directory");
    fs::write(
        temp.path.join("cott.toml"),
        r#"[project]
name = "demo"
version = "0.1.0"
source = "src"

[target.kotlin]
source = "kotlin"
generated = "generated/kotlin"
compiler = "kotlinc"
java = "java"
jvm_target = 17
runtime_validation = "boundary"
"#,
    )
    .expect("Kotlin manifest");
    fs::write(temp.path.join("src/demo/main.cott"), source).expect("Cott source");
    temp
}

#[test]
fn kotlin_init_is_module_only_and_needs_no_python_tooling() {
    let parent = TempDir::new();
    let target = parent.path.join("counter-module");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(["init", "--target", "kotlin", "--no-sync"])
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
    let manifest = fs::read_to_string(target.join("cott.toml")).expect("Kotlin manifest");
    assert!(manifest.contains("[target.kotlin]"));
    assert!(!manifest.contains("target.python"));
    assert_eq!(
        fs::read_to_string(target.join("src/counter_module/main.cott")).expect("contract"),
        "module counter_module.main\n\nfn main() -> Unit\n"
    );
    assert!(target.join("kotlin").is_dir());
    assert!(!target.join("python").exists());
    assert!(!target.join("settings.gradle.kts").exists());
    assert!(!target.join("app").exists());
    assert!(!target.join(".cott-init").exists());
}

#[test]
fn kotlin_ir_and_full_emit_record_truthful_pending_state() {
    let project = kotlin_project("module demo.main\n\nfn main() -> Unit\n");
    let ir = run(&project.path, &["emit", "ir"]);
    assert_eq!(
        ir.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&ir.stderr)
    );
    let generation = project.path.join("generated/generation.json");
    let published = fs::read(&generation).expect("generation record");
    let envelope: serde_json::Value = serde_json::from_slice(&published).expect("generation JSON");
    assert_eq!(envelope["schema_version"], 2);
    assert!(
        envelope["current"]
            .as_str()
            .is_some_and(|reference| envelope["snapshots"].get(reference).is_some()),
        "the published record must resolve its own current snapshot"
    );
    let record = snapshot::read(&published);
    assert_eq!(record["current"]["target"], "kotlin");
    assert_eq!(record["current"]["verified"], false);
    assert_eq!(record["last_verified"], serde_json::Value::Null);
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
    assert!(
        !project
            .path
            .join("generated/kotlin/demo/main/Facade.kt")
            .exists()
    );

    let kotlin = run(&project.path, &["emit", "kotlin"]);
    assert_eq!(
        kotlin.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&kotlin.stderr)
    );
    assert!(
        project
            .path
            .join("generated/kotlin/demo/main/Facade.kt")
            .is_file()
    );
    let record = snapshot::read(&fs::read(generation).expect("generation record"));
    assert_eq!(
        record["current"]["unresolved"],
        serde_json::json!(["demo.main.main"])
    );
    assert!(
        record["current"]["managed_files"]
            .as_object()
            .expect("managed files")
            .keys()
            .all(|path| !path.contains("python"))
    );
}

#[test]
fn kotlin_emit_refuses_unowned_output_without_deleting_it() {
    let project = kotlin_project("module demo.main\n\nfn main() -> Unit\n");
    let first = run(&project.path, &["emit", "ir"]);
    assert_eq!(first.status.code(), Some(0));
    let foreign = project.path.join("generated/foreign.bin");
    fs::write(&foreign, b"keep me").expect("foreign output");

    let rejected = run(&project.path, &["emit", "kotlin"]);
    assert_eq!(rejected.status.code(), Some(4));
    assert!(String::from_utf8_lossy(&rejected.stderr).contains("unowned Kotlin artifact"));
    assert_eq!(
        fs::read(&foreign).expect("foreign output retained"),
        b"keep me"
    );
    assert!(
        !project
            .path
            .join("generated/kotlin/demo/main/Facade.kt")
            .exists()
    );
}

#[test]
fn kotlin_source_paths_and_format_drift_are_checked_without_a_toolchain() {
    let project = kotlin_project("module demo.main\n\nfn main( ) -> Unit\n");
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
fn kotlin_format_does_not_require_resolvable_implementations() {
    let project = kotlin_project("module demo.main\n\nfn answer( ) -> Unit\n");
    fs::create_dir_all(project.path.join("kotlin/cott_impl/demo/main"))
        .expect("durable agent directory");
    fs::write(
        project.path.join("kotlin/cott_impl/demo/main/answer.kt"),
        "package cott_impl.demo.main\n\ninternal fun answer() {}\n",
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
fn consumed_manifest_and_contract_bytes_refuse_later_replacements() {
    let project = kotlin_project("module demo.main\n\nfn main() -> Unit\n");
    let (_, paths, manifest_source) =
        load_kotlin_config_with_paths(&project.path).expect("Kotlin project");
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
                digest(manifest_source.as_bytes()),
            )],
            std::iter::empty(),
        )
        .is_err(),
        "the final snapshot must reject bytes different from the parsed manifest"
    );

    fs::write(&paths.manifest, &manifest_source).expect("restore manifest");
    let sources = discover_kotlin_contract_sources(&paths).expect("consumed Cott sources");
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
        .is_err(),
        "the final snapshot must reject bytes different from the parsed SourceFile"
    );
    let relative_source = source_path
        .strip_prefix(&paths.root)
        .expect("project-relative source")
        .to_path_buf();
    let replacement_hash = digest(&fs::read(&source_path).expect("replacement Cott source bytes"));
    assert!(
        InputSnapshot::capture_expected(
            &paths.root,
            [
                (relative_source.clone(), digest(source.text.as_bytes())),
                (relative_source.clone(), replacement_hash.clone()),
            ],
            std::iter::empty(),
        )
        .is_err(),
        "a later duplicate hash must not replace the consumed source identity"
    );
    assert!(
        InputSnapshot::capture_expected(
            &paths.root,
            [
                (relative_source.clone(), replacement_hash.clone()),
                (relative_source, replacement_hash),
            ],
            std::iter::empty(),
        )
        .is_ok(),
        "agreeing duplicate discoveries retain one authoritative identity"
    );
}

#[test]
fn missing_accepted_agent_source_becomes_repairable_without_losing_history() {
    let project = kotlin_project("module demo.main\n\nfn main() -> Unit\n");
    let initial = run(&project.path, &["emit", "kotlin"]);
    assert_eq!(
        initial.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&initial.stderr)
    );

    let generation = project.path.join("generated/generation.json");
    let mut record =
        KotlinGenerationRecord::parse(&fs::read(&generation).expect("generation record"))
            .expect("valid Kotlin generation record");
    let source_origin = "kotlin/cott_impl/demo/main/main.kt".to_owned();
    let accepted_source =
        b"package cott_impl.demo.main\n\ninternal fun main(): kotlin.Unit = kotlin.Unit\n";
    let implementation_hash = digest(accepted_source);
    record
        .current
        .inputs
        .insert(source_origin.clone(), implementation_hash.clone());
    record.current.implementations = vec![KotlinBindingRecord {
        cott_symbol: "demo.main.main".to_owned(),
        target_symbol: "cott_impl.demo.main.main".to_owned(),
        source_origin: source_origin.clone(),
        runtime_origin: "kotlin/cott_impl/demo/main/main.kt".to_owned(),
        content_hash: implementation_hash.clone(),
        owner: KotlinOwner::Agent,
    }];
    record.current.unresolved.clear();
    record.current.agent_runs = vec![AgentRun {
        symbol: "demo.main.main".to_owned(),
        adapter: "fixture".to_owned(),
        adapter_version: "1".to_owned(),
        argv_template: Vec::new(),
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
        b"package cott_impl.demo.main\n\ninternal fun main(): kotlin.Unit { return kotlin.Unit }\n",
    )
    .expect("changed agent source");
    let accepted_record_bytes = fs::read(&generation).expect("accepted generation bytes");
    let changed = run(&project.path, &["emit", "kotlin"]);
    assert_eq!(changed.status.code(), Some(4));
    assert_eq!(
        fs::read(&generation).expect("generation remains accepted"),
        accepted_record_bytes,
        "present changed source must not rewrite accepted provenance"
    );

    fs::remove_file(&source_path).expect("remove accepted agent source");
    for arguments in [
        &["emit", "kotlin"][..],
        &["emit", "ir"][..],
        &["emit", "kotlin"][..],
        &["diff"][..],
    ] {
        let output = run(&project.path, arguments);
        assert_eq!(
            output.status.code(),
            Some(0),
            "{arguments:?}: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
    let pending =
        KotlinGenerationRecord::parse(&fs::read(&generation).expect("pending generation record"))
            .expect("valid pending Kotlin record");
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
    let project = kotlin_project("module demo.main\n\nfn main() -> Unit\n");
    let generated = project.path.join("generated");
    fs::create_dir(&generated).expect("artifact root");
    let generation = generated.join("generation.json");
    let fifo = CString::new(generation.as_os_str().as_bytes())
        .expect("temporary FIFO path should not contain NUL");
    assert_eq!(unsafe { libc::mkfifo(fifo.as_ptr(), 0o600) }, 0);

    let fifo_output = run_bounded(&project.path, &["check"]);
    assert_eq!(
        fifo_output.status.code(),
        Some(6),
        "{}",
        String::from_utf8_lossy(&fifo_output.stderr)
    );
    assert!(String::from_utf8_lossy(&fifo_output.stderr).contains("regular non-symlink"));
    fs::remove_file(&generation).expect("remove FIFO");

    let target = project.path.join("foreign-generation.json");
    fs::write(&target, b"{}").expect("symlink target");
    std::os::unix::fs::symlink(&target, &generation).expect("generation symlink");
    let symlink_output = run_bounded(&project.path, &["check"]);
    assert_eq!(
        symlink_output.status.code(),
        Some(6),
        "{}",
        String::from_utf8_lossy(&symlink_output.stderr)
    );
    assert!(String::from_utf8_lossy(&symlink_output.stderr).contains("generation record"));
}

const LEGACY_KOTLIN_AGENT_SOURCE: &[u8] =
    b"package cott_impl.demo.main\n\ninternal fun main(): cott_runtime.CottUnit = cott_runtime.CottUnit\n";

/// A verified previous IR8/strategy5 Kotlin record with one authentic agent source; returns
/// the project, its sealed legacy record bytes and the recorded AgentRun.
fn sealed_legacy_kotlin_project() -> (TempDir, Vec<u8>, AgentRun) {
    let project = kotlin_project("module demo.main\n\nfn main() -> Unit\n");
    let compiler = std::env::var_os("COTT_KOTLIN_HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("/tmp/cott-kotlin-toolchain/kotlinc"))
        .join("bin/kotlinc");
    let java = std::env::var_os("JAVA_HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("/tmp/cott-kotlin-toolchain/jdk"))
        .join("bin/java");
    let manifest_path = project.path.join("cott.toml");
    let manifest = fs::read_to_string(&manifest_path).expect("Kotlin manifest");
    fs::write(
        &manifest_path,
        manifest
            .replace(
                "compiler = \"kotlinc\"",
                &format!("compiler = {compiler:?}"),
            )
            .replace("java = \"java\"", &format!("java = {java:?}")),
    )
    .expect("pin test toolchain");
    let initial = run(&project.path, &["emit", "kotlin"]);
    assert!(
        initial.status.success(),
        "{}",
        String::from_utf8_lossy(&initial.stderr)
    );

    let generation = project.path.join("generated/generation.json");
    let mut record =
        KotlinGenerationRecord::parse(&fs::read(&generation).expect("generation record"))
            .expect("valid initial generation record");
    let source_origin = "kotlin/cott_impl/demo/main/main.kt".to_owned();
    let source_path = project.path.join(&source_origin);
    fs::create_dir_all(source_path.parent().expect("agent source parent"))
        .expect("agent source directory");
    fs::write(&source_path, LEGACY_KOTLIN_AGENT_SOURCE).expect("durable agent source");
    let source_hash = digest(LEGACY_KOTLIN_AGENT_SOURCE);
    record
        .current
        .inputs
        .insert(source_origin.clone(), source_hash.clone());
    record.current.implementations = vec![KotlinBindingRecord {
        cott_symbol: "demo.main.main".to_owned(),
        target_symbol: "cott_impl.demo.main.main".to_owned(),
        source_origin,
        runtime_origin: "kotlin/cott_impl/demo/main/main.kt".to_owned(),
        content_hash: source_hash.clone(),
        owner: KotlinOwner::Agent,
    }];
    record.current.unresolved.clear();
    record.current.agent_runs = vec![AgentRun {
        symbol: "demo.main.main".to_owned(),
        adapter: "fixture".to_owned(),
        adapter_version: "1".to_owned(),
        argv_template: Vec::new(),
        executable: "/fixture/agent".to_owned(),
        executable_hash: fixture_digest(1),
        prompt_hash: fixture_digest(2),
        implementation_hash: source_hash,
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
    record.current.canonical_ir_schema = 8;
    record.current.verified = true;
    record.current.verification =
        serde_json::json!({"contract_tests": {"strategies": [{"schema_version": 5}]}});
    let mut identity = serde_json::to_value(&record.current).expect("legacy snapshot JSON");
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
    record.current.generation_id = cott::snapshot_record::digest(&serde_json::json!({
        "domain": "cott.kotlin.generation.v2",
        "schema_version": KOTLIN_GENERATION_SCHEMA_VERSION,
        "current": identity,
    }))
    .expect("seal prior Kotlin generation identity");
    let old_run = record.current.agent_runs[0].clone();
    record.last_verified = Some(record.current.clone());
    let legacy_bytes = serde_json::to_vec(&record).expect("seal legacy full snapshot envelope");
    fs::write(&generation, &legacy_bytes).expect("publish legacy fixture record");
    (project, legacy_bytes, old_run)
}

#[test]
fn sealed_legacy_kotlin_record_requires_explicit_emit() {
    let (project, legacy_bytes, old_run) = sealed_legacy_kotlin_project();
    let generation = project.path.join("generated/generation.json");
    let source_path = project.path.join("kotlin/cott_impl/demo/main/main.kt");

    for command in [
        &["check"][..],
        &["verify"][..],
        &["requirements"][..],
        &["deploy"][..],
        &["diff"][..],
        &["emit", "ir"][..],
        &["generate", "--agent", "omp", "--target", "kotlin"][..],
    ] {
        let result = run(&project.path, command);
        assert!(
            !result.status.success(),
            "{command:?} must reject legacy evidence before explicit target emit"
        );
        assert_eq!(
            fs::read(&generation).expect("legacy record unchanged"),
            legacy_bytes,
            "{command:?} must not silently migrate the legacy record"
        );
    }

    let mut tampered: serde_json::Value =
        serde_json::from_slice(&legacy_bytes).expect("legacy JSON");
    let current = tampered["current"]
        .as_str()
        .expect("snapshot reference")
        .to_owned();
    tampered["snapshots"][&current]["project_version"] = serde_json::json!("9.9.9");
    fs::write(
        &generation,
        serde_json::to_vec(&tampered).expect("tampered legacy JSON"),
    )
    .expect("tamper snapshot bytes");
    let rejected = run(&project.path, &["emit", "kotlin"]);
    assert!(
        !rejected.status.success(),
        "tampered snapshot must not convert"
    );
    fs::write(&generation, &legacy_bytes).expect("restore sealed snapshot");
    fs::write(&source_path, b"package cott_impl.demo.main\n// changed\n")
        .expect("tamper implementation bytes");
    let rejected = run(&project.path, &["emit", "kotlin"]);
    assert!(
        !rejected.status.success(),
        "tampered agent source must not convert"
    );
    assert_eq!(
        fs::read(&generation).expect("legacy record remains sealed"),
        legacy_bytes
    );
    fs::write(&source_path, LEGACY_KOTLIN_AGENT_SOURCE)
        .expect("restore authenticated agent source");

    let emitted = run(&project.path, &["emit", "kotlin"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let converted =
        KotlinGenerationRecord::parse(&fs::read(&generation).expect("converted record"))
            .expect("current-schema Kotlin record");
    assert_eq!(converted.current.canonical_ir_schema, 9);
    assert!(!converted.current.verified);
    assert!(converted.last_verified.is_none());
    assert_eq!(converted.current.agent_runs, vec![old_run]);
    assert_eq!(converted.current.implementations.len(), 1);
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn legacy_kotlin_emit_then_real_verify_certifies_new_schema() {
    let (project, _, _) = sealed_legacy_kotlin_project();
    let generation = project.path.join("generated/generation.json");
    let emitted = run(&project.path, &["emit", "kotlin"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let verified = run(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
    let certified = KotlinGenerationRecord::parse(&fs::read(generation).expect("verified record"))
        .expect("verified current-schema record");
    assert!(certified.current.verified);
    assert!(
        certified
            .current_is_last_verified()
            .expect("certified snapshot digest")
    );
}
