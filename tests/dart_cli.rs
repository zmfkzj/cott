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
    let record: serde_json::Value =
        serde_json::from_slice(&fs::read(&generation).expect("generation record"))
            .expect("generation JSON");
    assert_eq!(record["schema_version"], 1);
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
    let record: serde_json::Value =
        serde_json::from_slice(&fs::read(generation).expect("generation record"))
            .expect("generation JSON");
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
