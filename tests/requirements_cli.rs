//! Requirement reports through the real `cott` binary: `requirements` binds only fresh certified
//! evidence, and `verify` reports its own run without crediting an older record.

use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::dart::provenance::DartGenerationRecord;
use cott::kotlin::provenance::KotlinGenerationRecord;
use serde_json::{Value, json};

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-requirements-cli-{}-{number}",
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

fn cott(root: &Path, arguments: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(arguments)
        .arg("--project")
        .arg(root)
        .output()
        .expect("cott should run")
}

fn stderr(output: &Output) -> String {
    String::from_utf8_lossy(&output.stderr).into_owned()
}

fn succeed(root: &Path, arguments: &[&str]) -> Output {
    let output = cott(root, arguments);
    assert_eq!(
        output.status.code(),
        Some(0),
        "{arguments:?}: {}",
        stderr(&output)
    );
    output
}

/// The separate versioned report document from `cott requirements --format json`.
fn report(root: &Path) -> Value {
    let output = succeed(root, &["requirements", "--format", "json"]);
    let report: Value = serde_json::from_slice(&output.stdout).expect("requirement report JSON");
    assert_eq!(report["schema_version"], 1);
    assert_eq!(report["kind"], "cott.requirements");
    report
}

fn requirement<'a>(report: &'a Value, id: &str) -> &'a Value {
    report["requirements"]
        .as_array()
        .expect("requirement entries")
        .iter()
        .find(|entry| entry["id"] == id)
        .unwrap_or_else(|| panic!("missing requirement {id} in {report}"))
}

fn assert_nothing_credited(report: &Value, state: &str) {
    assert_eq!(report["evidence"]["state"], state, "{report}");
    assert_eq!(report["summary"]["observed"], 0, "{report}");
    for entry in report["requirements"].as_array().expect("entries") {
        assert_eq!(entry["status"], "unverified", "{report}");
        for check in entry["checks"].as_array().expect("checks") {
            assert_eq!(check["executed"], false, "{report}");
            assert_eq!(check["assertions_observed"], 0, "{report}");
        }
    }
}

/// The key=value summary line `verify` prints before the per-requirement lines.
fn verify_summary(output: &Output) -> String {
    String::from_utf8_lossy(&output.stdout)
        .lines()
        .find(|line| line.starts_with("requirements: "))
        .unwrap_or_else(|| panic!("verify printed no requirement report: {output:?}"))
        .to_owned()
}

const PYTHON_SOURCE: &str = r#"module app

fn run() -> I32

scenario returns_seven:
    call value = run()
    assert value == 7

requirement SEVEN for run:
    text "Run returns seven."
    checked_by returns_seven
    waiver "TICKET-1: temporary exception."

requirement DOCUMENTED for run:
    text "Run is documented."
"#;

fn python_project() -> TempDir {
    let temp = TempDir::new();
    fs::write(
        temp.path.join("cott.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.python]\nsource = \"python\"\ngenerated = \"generated/python\"\nstubs = \"generated/stubs\"\ninterpreter = \".venv/bin/python\"\ntype_checker = \".venv/bin/basedpyright\"\nruntime_validation = \"boundary\"\n\n[target.python.implementations]\n\"app.run\" = \"cott_bindings.app.run:run\"\n",
    )
    .expect("manifest");
    fs::create_dir_all(temp.path.join("src")).expect("source directory");
    fs::write(temp.path.join("src/app.cott"), PYTHON_SOURCE).expect("contract");
    fs::create_dir_all(temp.path.join("python/cott_bindings/app")).expect("binding directory");
    fs::write(
        temp.path.join("python/pyproject.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14,<3.15\"\ndependencies = []\n",
    )
    .expect("target metadata");
    write_python_binding(&temp.path, 7);
    install_fake_python_tools(&temp.path);
    temp
}

fn write_python_binding(root: &Path, value: i32) {
    fs::write(
        root.join("python/cott_bindings/app/run.py"),
        format!("from cott_runtime import I32\n\n\ndef run() -> I32:\n    return {value}\n"),
    )
    .expect("binding");
}

fn install_fake_python_tools(root: &Path) {
    let bin = root.join(".venv/bin");
    fs::create_dir_all(&bin).expect("fake Python tool directory");
    let python = bin.join("python");
    fs::write(
        &python,
        r#"#!/bin/sh
if [ "$1" = "-c" ]; then
  case "$2" in
    *"sysconfig; print(json.dumps"*)
      printf '%s\n' '{"cache_tag":"cpython-314","implementation":"cpython","machine":"x86_64","os":"linux","platform":"linux-x86_64","version":"3.14.6"}'
      exit 0
      ;;
  esac
fi
exec /usr/bin/python3 "$@"
"#,
    )
    .expect("fake Python interpreter");
    let checker = bin.join("basedpyright");
    fs::write(
        &checker,
        "#!/bin/sh\n[ \"$1\" = \"--version\" ] && printf 'basedpyright 1.39.9\\nbased on pyright 1.1.411\\n'\nexit 0\n",
    )
    .expect("fake BasedPyright");
    use std::os::unix::fs::PermissionsExt;
    for executable in [python, checker] {
        fs::set_permissions(executable, fs::Permissions::from_mode(0o755))
            .expect("make fake Python tool executable");
    }
}

#[test]
fn verify_then_requirements_keeps_dev_only_lock_dependencies_out_of_runtime_evidence() {
    let project = python_project();
    let root = &project.path;
    let manifest = fs::read_to_string(root.join("cott.toml")).expect("manifest");
    fs::write(
        root.join("cott.toml"),
        manifest.replace(
            "source = \"python\"\n",
            "source = \"python\"\nlockfile = \"python/uv.lock\"\n",
        ),
    )
    .expect("select frozen lock");
    fs::write(
        root.join("python/uv.lock"),
        "version = 1\nrevision = 3\nrequires-python = \">=3.14,<3.15\"\n\n[[package]]\nname = \"demo\"\nversion = \"0.1.0\"\nsource = { virtual = \".\" }\n[package.dev-dependencies]\ndev = [{ name = \"checker-only\" }]\n\n[[package]]\nname = \"checker-only\"\nversion = \"1.0.0\"\nsource = { registry = \"https://pypi.org/simple\" }\nwheels = [{ hash = \"sha256:0000000000000000000000000000000000000000000000000000000000000000\" }]\n",
    )
    .expect("dev-only lock");
    succeed(root, &["emit", "python"]);
    succeed(root, &["verify"]);
    let first = report(root);
    assert_eq!(first["evidence"]["state"], "current", "{first}");
    assert_eq!(
        requirement(&first, "app.requirement.SEVEN")["status"],
        "observed"
    );
    // Inspection and repeated verification must agree on the very same production closure.
    succeed(root, &["verify"]);
    let second = report(root);
    assert_eq!(second["evidence"]["state"], "current", "{second}");
    assert_eq!(
        requirement(&second, "app.requirement.SEVEN")["status"],
        "observed"
    );
}

#[test]
fn python_requirement_report_binds_only_the_fresh_verified_run() {
    let project = python_project();
    let root = project.path.as_path();

    // No record, then an emitted but uncertified record: nothing is credited.
    let absent = report(root);
    assert_nothing_credited(&absent, "absent");
    assert_eq!(absent["summary"]["total"], 2);
    succeed(root, &["emit", "python"]);
    assert_nothing_credited(&report(root), "stale");

    let verified = succeed(root, &["verify"]);
    assert!(
        verify_summary(&verified).contains("evidence=current"),
        "{verified:?}"
    );

    let current = report(root);
    assert_eq!(current["evidence"]["state"], "current", "{current}");
    let seven = requirement(&current, "app.requirement.SEVEN");
    assert_eq!(seven["status"], "observed", "{current}");
    assert_eq!(seven["checks"][0]["executed"], true);
    assert_eq!(
        seven["checks"][0]["assertions_observed"],
        seven["checks"][0]["assertions_declared"]
    );
    assert!(!seven["waivers"].as_array().expect("waivers").is_empty());
    // An unlinked requirement stays unverified even beside fresh observed evidence.
    let documented = requirement(&current, "app.requirement.DOCUMENTED");
    assert_eq!(documented["status"], "unverified");
    assert!(documented["checks"].as_array().expect("checks").is_empty());
    assert_eq!(current["summary"]["waived"], 1);

    // JSON verify keeps the closed diagnostics document and carries the report as notes.
    let json_verify = succeed(root, &["verify", "--format", "json"]);
    let diagnostics: Value =
        serde_json::from_slice(&json_verify.stdout).expect("closed diagnostics JSON");
    assert!(
        diagnostics["diagnostics"]
            .as_array()
            .expect("diagnostics")
            .iter()
            .any(|diagnostic| diagnostic["severity"] == "note"
                && diagnostic["message"]
                    .as_str()
                    .is_some_and(|message| message.contains("app.requirement.SEVEN"))),
        "{diagnostics}"
    );

    // An input outside the Canonical IR changes: the certified record no longer describes the
    // current inputs, so its observation must not be credited.
    let binding = root.join("python/cott_bindings/app/run.py");
    let mut edited = fs::read_to_string(&binding).expect("binding");
    edited.push_str("# unrelated edit\n");
    fs::write(&binding, edited).expect("edited binding");
    assert_nothing_credited(&report(root), "stale");

    // A failing verify of emitted current inputs reports its own linked scenario failure,
    // never the older observed record.
    write_python_binding(root, 8);
    succeed(root, &["emit", "python"]);
    let failed = cott(root, &["verify"]);
    assert!(!failed.status.success(), "{}", stderr(&failed));
    let summary = verify_summary(&failed);
    assert!(
        summary.contains("evidence=failed") && summary.contains("observed=0"),
        "{summary}"
    );
    assert!(
        String::from_utf8_lossy(&failed.stdout)
            .lines()
            .any(
                |line| line.starts_with("requirement app.requirement.SEVEN ")
                    && line.contains(": failed")
            ),
        "{failed:?}"
    );
    assert_nothing_credited(&report(root), "stale");
}

const BACKEND_SOURCE: &str = r#"module demo.main

fn run(value: I32) -> I32

scenario echoes:
    call echoed = run(7)
    assert echoed == 7

requirement ECHO for run:
    text "Run echoes its input."
    checked_by echoes
    waiver "TICKET-1: temporary exception."

requirement DOCUMENTED for run:
    text "Run is documented."
"#;

const ECHO: &str = "demo.main.requirement.ECHO";
const ECHO_SCENARIO: &str = "demo.main.scenario.echoes";

fn backend_project(target: &str, binding: (&str, &str, &str)) -> TempDir {
    let temp = TempDir::new();
    let (entry, path, source) = binding;
    fs::create_dir_all(temp.path.join("src/demo")).expect("contract directory");
    fs::write(temp.path.join("src/demo/main.cott"), BACKEND_SOURCE).expect("contract");
    let file = temp.path.join(target).join(path);
    fs::create_dir_all(file.parent().expect("binding parent")).expect("binding directory");
    fs::write(file, source).expect("binding");
    let toolchain = match target {
        // Missing tools make verification fail deterministically before certification.
        "kotlin" => {
            "compiler = \"definitely-missing-kotlinc\"\njava = \"definitely-missing-java\"\njvm_target = 17\n"
        }
        _ => "sdk = \"definitely-missing-dart-sdk\"\n",
    };
    fs::write(
        temp.path.join("cott.toml"),
        format!(
            "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.{target}]\nsource = \"{target}\"\ngenerated = \"generated/{target}\"\n{toolchain}runtime_validation = \"boundary\"\n\n[target.{target}.implementations]\n\"demo.main.run\" = \"{entry}\"\n"
        ),
    )
    .expect("manifest");
    temp
}

fn contract_tests(status: &str) -> Value {
    json!({
        "contract_tests": {
            "scenarios": [{"scenario_id": ECHO_SCENARIO, "status": status, "assertions": 1}],
            "unavailable": {},
        }
    })
}

/// Stand in for a certified runner record of the current inputs; the toolchains are absent.
fn certify_kotlin(root: &Path, status: &str) {
    let path = root.join("generated/generation.json");
    let mut record = KotlinGenerationRecord::parse(&fs::read(&path).expect("record"))
        .expect("valid Kotlin record");
    record.current.verified = true;
    record.current.verification = contract_tests(status);
    record
        .current
        .compute_generation_id()
        .expect("generation identity");
    record.last_verified = Some(record.current.clone());
    fs::write(&path, record.canonical_bytes().expect("record bytes")).expect("write record");
}

fn certify_dart(root: &Path, status: &str) {
    let path = root.join("generated/generation.json");
    let mut record =
        DartGenerationRecord::parse(&fs::read(&path).expect("record")).expect("valid Dart record");
    record.current.verified = true;
    record.current.verification = contract_tests(status);
    record
        .current
        .compute_generation_id()
        .expect("generation identity");
    record.last_verified = Some(record.current.clone());
    fs::write(&path, record.canonical_bytes().expect("record bytes")).expect("write record");
}

fn exercise_backend(project: &TempDir, target: &str, certify: fn(&Path, &str)) {
    let root = project.path.as_path();
    let absent = report(root);
    assert_eq!(absent["evidence"]["target"], target);
    assert_nothing_credited(&absent, "absent");
    succeed(root, &["emit", target]);
    assert_nothing_credited(&report(root), "stale");

    certify(root, "passed");
    let current = report(root);
    assert_eq!(current["evidence"]["state"], "current", "{current}");
    let echo = requirement(&current, ECHO);
    assert_eq!(echo["status"], "observed", "{current}");
    assert_eq!(echo["checks"][0]["executed"], true);
    assert_eq!(echo["checks"][0]["assertions_observed"], 1);
    assert_eq!(
        requirement(&current, "demo.main.requirement.DOCUMENTED")["status"],
        "unverified"
    );

    // Verification of the current inputs fails before certification; the report is that
    // failure, not the observed record left on disk.
    let failed = cott(root, &["verify"]);
    assert!(!failed.status.success(), "{}", stderr(&failed));
    let summary = verify_summary(&failed);
    assert!(
        summary.contains("evidence=failed") && summary.contains("observed=0"),
        "{summary}"
    );

    // A failed linked scenario stays failed despite the waiver.
    certify(root, "failed");
    let failing = report(root);
    assert_eq!(failing["evidence"]["state"], "current", "{failing}");
    assert_eq!(requirement(&failing, ECHO)["status"], "failed", "{failing}");
    assert_eq!(failing["summary"]["failed"], 1);
    assert_eq!(failing["summary"]["waived"], 1);

    // A contract input edit makes the certified record stale; nothing is credited.
    certify(root, "passed");
    let contract = root.join("src/demo/main.cott");
    let mut edited = fs::read_to_string(&contract).expect("contract");
    edited.push_str("\n# unrelated edit\n");
    fs::write(&contract, edited).expect("edited contract");
    assert_nothing_credited(&report(root), "stale");
}

#[test]
fn kotlin_requirement_report_never_credits_stale_or_failed_runs() {
    let project = backend_project(
        "kotlin",
        (
            "cott_bindings.main.run",
            "cott_bindings/main/run.kt",
            "package cott_bindings.main\n\ninternal fun run(value: kotlin.Int): kotlin.Int {\n    return value\n}\n",
        ),
    );
    exercise_backend(&project, "kotlin", certify_kotlin);
}

#[test]
fn dart_requirement_report_never_credits_stale_or_failed_runs() {
    let project = backend_project(
        "dart",
        (
            "bindings/run.dart:_run",
            "bindings/run.dart",
            "int _run(int value) {\n  return value;\n}\n",
        ),
    );
    exercise_backend(&project, "dart", certify_dart);
}

#[test]
fn requirements_command_is_closed_and_needs_a_project() {
    let project = TempDir::new();
    let unknown = cott(&project.path, &["requirements", "--target", "kotlin"]);
    assert_eq!(unknown.status.code(), Some(2));
    let missing = cott(&project.path, &["requirements", "--format", "json"]);
    assert!(!missing.status.success());
    assert!(
        missing.stdout.is_empty(),
        "failures never print a report document"
    );
}
