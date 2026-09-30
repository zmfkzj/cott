use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

static NEXT: AtomicU64 = AtomicU64::new(0);

struct TempDir(PathBuf);

impl TempDir {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "cott-rust-cli-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&path).unwrap();
        Self(path)
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn cott(root: &Path, arguments: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_cott"))
        .current_dir(root)
        .args(arguments)
        .output()
        .unwrap()
}

fn success(output: Output) -> Output {
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    output
}

#[test]
fn rust_init_no_sync_atomically_creates_only_authored_project() {
    let temp = TempDir::new();
    success(cott(
        &temp.0,
        &[
            "init",
            "rust_project",
            "--target",
            "rust",
            "--name",
            "counter_app",
            "--no-sync",
        ],
    ));
    let root = temp.0.join("rust_project");
    let bytes = fs::read_to_string(root.join("cott.toml")).unwrap();
    let config = cott::manifest::RustProjectConfig::parse(&root.join("cott.toml"), &bytes).unwrap();
    assert_eq!(config.project.name, "counter_app");
    assert_eq!(config.rust.source, "rust");
    assert_eq!(config.rust.generated, "generated/rust");
    assert_eq!(config.rust.cargo, "cargo");
    assert_eq!(config.rust.rustc, "rustc");
    assert_eq!(
        fs::read_to_string(root.join("src/counter_app/main.cott")).unwrap(),
        "module counter_app.main\n"
    );
    assert!(root.join("rust").is_dir());
    assert!(!root.join("generated").exists());
    assert!(!root.join(".cott-init").exists());
    assert!(!fs::read_dir(&temp.0).unwrap().any(|entry| {
        entry
            .unwrap()
            .file_name()
            .to_string_lossy()
            .starts_with(".cott-rust-init-")
    }));
}

// requires merged Rust ABI/verify (binding and frozen dependencies), not target tools
#[test]
#[ignore = "requires merged Rust ABI/binding/dependencies"]
fn rust_check_audits_complete_target_surface_without_rust_tools() {
    let temp = TempDir::new();
    success(cott(
        &temp.0,
        &["init", "rust_project", "--target", "rust", "--no-sync"],
    ));
    let root = temp.0.join("rust_project");
    let bytes = fs::read_to_string(root.join("cott.toml")).unwrap();
    fs::write(
        root.join("cott.toml"),
        bytes
            .replace("cargo = \"cargo\"", "cargo = \"definitely-missing-cargo\"")
            .replace("rustc = \"rustc\"", "rustc = \"definitely-missing-rustc\""),
    )
    .unwrap();
    success(cott(&root, &["check"]));
}

#[test]
fn rust_init_toolchain_failure_discards_owned_staging_before_publication() {
    let temp = TempDir::new();
    let empty_path = temp.0.join("empty-bin");
    fs::create_dir(&empty_path).unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .current_dir(&temp.0)
        .env("PATH", &empty_path)
        .args(["init", "failed_project", "--target", "rust"])
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(2));
    assert!(!temp.0.join("failed_project").exists());
    assert!(!fs::read_dir(&temp.0).unwrap().any(|entry| {
        entry
            .unwrap()
            .file_name()
            .to_string_lossy()
            .starts_with(".cott-rust-init-")
    }));
}

#[test]
fn rust_init_refuses_existing_outputs_and_invalid_names_without_partial_scaffolds() {
    let temp = TempDir::new();
    fs::create_dir(temp.0.join("existing")).unwrap();
    fs::write(temp.0.join("existing/owned"), b"preserve").unwrap();
    assert_eq!(
        cott(
            &temp.0,
            &["init", "existing", "--target", "rust", "--no-sync"]
        )
        .status
        .code(),
        Some(2)
    );
    assert_eq!(
        fs::read(temp.0.join("existing/owned")).unwrap(),
        b"preserve"
    );
    for name in ["async", "9start", "has-dash"] {
        assert_eq!(
            cott(
                &temp.0,
                &[
                    "init",
                    "fresh",
                    "--target",
                    "rust",
                    "--name",
                    name,
                    "--no-sync"
                ]
            )
            .status
            .code(),
            Some(2)
        );
        assert!(!temp.0.join("fresh").exists());
    }
}

#[test]
fn rust_target_mismatch_fails_before_target_tools_or_publication() {
    let temp = TempDir::new();
    success(cott(
        &temp.0,
        &["init", "rust_project", "--target", "rust", "--no-sync"],
    ));
    let root = temp.0.join("rust_project");
    for target in ["python", "kotlin", "dart"] {
        let output = cott(&root, &["emit", target, "--format", "json"]);
        assert_eq!(output.status.code(), Some(2));
        let report: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
        assert_eq!(report["diagnostics"][0]["code"], "COTT-C001");
        assert!(!root.join("generated").exists());
    }
    assert_eq!(
        cott(&root, &["generate", "--target", "python", "--agent", "omp"])
            .status
            .code(),
        Some(2)
    );
}

fn native_project() -> TempDir {
    let cargo = PathBuf::from(
        std::env::var_os("COTT_CARGO").expect("set COTT_CARGO to an absolute cargo path"),
    );
    assert!(cargo.is_absolute());
    let rustc = std::env::var_os("COTT_RUSTC")
        .map(PathBuf::from)
        .unwrap_or_else(|| cargo.with_file_name("rustc"));
    let temp = TempDir::new();
    fs::create_dir_all(temp.0.join("src/demo")).unwrap();
    fs::create_dir_all(temp.0.join("rust/cott_bindings")).unwrap();
    let cargo = toml::Value::String(cargo.to_str().unwrap().to_owned()).to_string();
    let rustc = toml::Value::String(rustc.to_str().unwrap().to_owned()).to_string();
    fs::write(temp.0.join("cott.toml"), format!("[project]\nname = \"demo_rust\"\nversion = \"0.1.0\"\nsource = \"src\"\n[target.rust]\nsource = \"rust\"\ngenerated = \"generated/rust\"\ncargo = {cargo}\nrustc = {rustc}\nruntime_validation = \"boundary\"\n[target.rust.implementations]\n\"demo.counter.increment\" = \"cott_bindings/increment.rs:increment\"\n")).unwrap();
    fs::write(temp.0.join("src/demo/counter.cott"), "module demo.counter\n\nfn increment(value: I64) -> I64:\n    requires value < 9223372036854775807\n    ensures result == value + 1\n").unwrap();
    fs::write(
        temp.0.join("rust/cott_bindings/increment.rs"),
        "pub(crate) fn increment(value: i64) -> i64 { value + 1 }\n",
    )
    .unwrap();
    temp
}

fn record(root: &Path) -> cott::rust::provenance::RustGenerationRecord {
    cott::rust::provenance::RustGenerationRecord::parse(
        &fs::read(root.join("generated/generation.json")).unwrap(),
    )
    .unwrap()
}

// requires merged Rust ABI/verify
#[test]
#[ignore = "requires merged Rust ABI/verify and COTT_CARGO"]
fn rust_emit_verify_and_ir_only_publication_preserve_certified_history_without_blessing_drift() {
    let project = native_project();
    success(cott(&project.0, &["emit", "rust"]));
    let pending = record(&project.0);
    assert!(!pending.current.verified);
    assert!(pending.last_verified.is_none());
    success(cott(&project.0, &["verify"]));
    let certified = record(&project.0);
    assert_eq!(certified.last_verified.as_ref(), Some(&certified.current));
    let library = fs::read(project.0.join("generated/rust/src/lib.rs")).unwrap();
    let contract = project.0.join("src/demo/counter.cott");
    let changed = fs::read_to_string(&contract)
        .unwrap()
        .replace("value < 9223372036854775807", "value < 9223372036854775806");
    fs::write(contract, changed).unwrap();
    success(cott(&project.0, &["emit", "ir"]));
    let ir = record(&project.0);
    assert!(!ir.current.verified);
    assert_eq!(ir.last_verified, certified.last_verified);
    assert_eq!(
        fs::read(project.0.join("generated/rust/src/lib.rs")).unwrap(),
        library
    );
    assert_eq!(
        ir.current.managed_files["generated/rust/src/lib.rs"],
        certified.current.managed_files["generated/rust/src/lib.rs"]
    );
    fs::write(
        project.0.join("generated/rust/src/lib.rs"),
        b"tampered facade",
    )
    .unwrap();
    assert!(!cott(&project.0, &["emit", "ir"]).status.success());
    assert_eq!(record(&project.0), ir);
}

// requires merged Rust ABI/verify
#[test]
#[ignore = "requires merged Rust ABI/verify and COTT_CARGO"]
fn rust_deployment_is_consumable_without_compiler_vendor_runtime_copies() {
    let project = native_project();
    success(cott(&project.0, &["emit", "rust"]));
    success(cott(&project.0, &["verify"]));
    let before = fs::read(project.0.join("generated/generation.json")).unwrap();
    success(cott(&project.0, &["deploy", "--output", "release"]));
    let release = project.0.join("release");
    assert_eq!(fs::read(release.join("generation.json")).unwrap(), before);
    assert!(!release.join("vendor").exists());
    assert!(!release.join("verification").exists());
    assert!(!release.join(".cargo").exists());
    let manifest: toml::Value =
        toml::from_str(&fs::read_to_string(release.join("Cargo.toml")).unwrap()).unwrap();
    let tokio = &manifest["dependencies"]["tokio"];
    assert_eq!(
        tokio
            .get("version")
            .and_then(toml::Value::as_str)
            .or_else(|| tokio.as_str()),
        Some("=1.53.1")
    );
    assert!(tokio.get("path").is_none());
    let consumer = project.0.join("consumer");
    fs::create_dir_all(consumer.join("src")).unwrap();
    fs::write(consumer.join("Cargo.toml"), "[package]\nname = \"consumer\"\nversion = \"0.1.0\"\nedition = \"2024\"\n[dependencies]\ndemo_rust = { path = \"../release\" }\n").unwrap();
    fs::write(
        consumer.join("src/main.rs"),
        "fn main() { println!(\"{}\", demo_rust::modules::demo::counter::increment(1)); }\n",
    )
    .unwrap();
    let cargo = std::env::var_os("COTT_CARGO").unwrap();
    let rustc = std::env::var_os("COTT_RUSTC")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from(&cargo).with_file_name("rustc"));
    let output = Command::new(cargo)
        .env("RUSTC", rustc)
        .current_dir(&consumer)
        .args(["run", "--offline", "--quiet"])
        .output()
        .unwrap();
    let output = success(output);
    assert_eq!(output.stdout, b"2\n");
    assert_eq!(
        fs::read(project.0.join("generated/generation.json")).unwrap(),
        before
    );
}

#[test]
fn rust_requirement_reports_use_the_closed_rust_target_and_honest_absent_evidence() {
    let parsed = cott::compiler::parse_project([cott::compiler::SourceFile::new(
        PathBuf::from("counter.cott"),
        "module counter\n\nfn increment(value: I64) -> I64\n\nrequirement INCREMENT for increment:\n    text \"The value is incremented.\"\n",
    )]).unwrap();
    let hir = cott::hir::lower(Path::new("src"), parsed).unwrap();
    let ir = cott::ir::render(&hir).unwrap();
    let model = cott::requirements::RequirementModel::from_ir(&ir).unwrap();
    let report = model.report(
        cott::manifest::TargetLanguage::Rust,
        cott::requirements::Evidence::Absent("no publication"),
    );
    let wire = report.to_json().unwrap();
    assert_eq!(wire["evidence"]["target"], "rust");
    assert_eq!(wire["evidence"]["state"], "absent");
    assert_eq!(wire["requirements"][0]["status"], "unverified");
    assert_eq!(wire["summary"]["observed"], 0);
}

// requires merged Rust ABI/verify
#[test]
#[ignore = "requires merged Rust ABI/verify and COTT_CARGO"]
fn rust_init_default_probes_and_emits_before_atomic_publication() {
    let temp = TempDir::new();
    let cargo = PathBuf::from(
        std::env::var_os("COTT_CARGO").expect("set COTT_CARGO to an absolute cargo path"),
    );
    assert!(cargo.is_absolute());
    let mut paths = vec![cargo.parent().unwrap().to_path_buf()];
    paths.extend(std::env::split_paths(
        &std::env::var_os("PATH").unwrap_or_default(),
    ));
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .current_dir(&temp.0)
        .env("PATH", std::env::join_paths(paths).unwrap())
        .args(["init", "counter", "--target", "rust"])
        .output()
        .unwrap();
    success(output);
    let root = temp.0.join("counter");
    assert!(root.join("generated/rust/src/lib.rs").is_file());
    assert!(root.join("generated/rust/Cargo.toml").is_file());
    let record = record(&root);
    assert!(!record.current.verified);
    assert!(record.last_verified.is_none());
    assert!(!root.join(".cott-init").exists());
    assert!(!fs::read_dir(&temp.0).unwrap().any(|entry| {
        entry
            .unwrap()
            .file_name()
            .to_string_lossy()
            .starts_with(".cott-rust-init-")
    }));
}

// requires merged Rust ABI/verify
#[test]
#[ignore = "requires merged Rust ABI/verify and COTT_CARGO"]
fn rust_requirements_and_diff_are_read_only_snapshot_bound_reports() {
    let project = native_project();
    let contract = project.0.join("src/demo/counter.cott");
    let mut source = fs::read_to_string(&contract).unwrap();
    source.push_str(
        "\nrequirement INCREMENT for increment:\n    text \"The value is incremented.\"\n",
    );
    fs::write(&contract, source).unwrap();
    let absent = success(cott(&project.0, &["requirements", "--format", "json"]));
    let absent: serde_json::Value = serde_json::from_slice(&absent.stdout).unwrap();
    assert_eq!(absent["evidence"]["target"], "rust");
    assert_eq!(absent["evidence"]["state"], "absent");
    assert!(!project.0.join("generated").exists());
    success(cott(&project.0, &["emit", "rust"]));
    success(cott(&project.0, &["verify"]));
    let before = fs::read(project.0.join("generated/generation.json")).unwrap();
    let current = success(cott(&project.0, &["requirements", "--format", "json"]));
    let current: serde_json::Value = serde_json::from_slice(&current.stdout).unwrap();
    assert_eq!(current["evidence"]["state"], "current");
    assert_eq!(current["requirements"][0]["status"], "unverified");
    let diff = success(cott(
        &project.0,
        &["diff", "--format", "json", "--exit-code"],
    ));
    let diff: serde_json::Value = serde_json::from_slice(&diff.stdout).unwrap();
    assert_eq!(diff["target"], "rust");
    assert_eq!(diff["breaking"], false);
    assert_eq!(
        fs::read(project.0.join("generated/generation.json")).unwrap(),
        before
    );
    let source = fs::read_to_string(&contract)
        .unwrap()
        .replace("value < 9223372036854775807", "value < 9223372036854775806");
    fs::write(&contract, source).unwrap();
    let diff = cott(&project.0, &["diff", "--format", "json", "--exit-code"]);
    assert_eq!(diff.status.code(), Some(7));
    let diff: serde_json::Value = serde_json::from_slice(&diff.stdout).unwrap();
    assert_eq!(diff["breaking"], true);
    assert_eq!(diff["version_compatible"], false);
    assert_eq!(
        fs::read(project.0.join("generated/generation.json")).unwrap(),
        before
    );
}
