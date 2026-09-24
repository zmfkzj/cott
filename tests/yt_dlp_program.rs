//! External isolated-process regressions for `examples/real/yt-dlp`.
//!
//! These tests produce `external_program_regression` evidence only. They run one real program
//! tree (its generated public facade and authored `app.py`) inside Cott's existing sandbox with
//! isolated loopback, against a local 127.0.0.1 HTTP origin and scratch directories. They are not
//! Cott scenario observations, never write the example's generation record, and fail closed when
//! the sandbox or isolated loopback is unavailable: there is no host-network fallback.
//!
//! Run after `cott generate` and `cott verify` of the example:
//!
//! ```sh
//! cargo test --test yt_dlp_program -- --ignored --nocapture
//! ```

use std::collections::BTreeMap;
use std::fs;
use std::io;
use std::os::unix::fs::symlink;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::Mutex;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Duration;

use cott::hash::sha256_hex;
use cott::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxSpec, run};
use serde_json::Value;

const PROGRAM: &str = include_str!("support/yt_dlp_program.py");
const EVIDENCE_KIND: &str = "external_program_regression";
const CHECKS: [&str; 7] = [
    "import.public_facade",
    "execute.simulate_reports_discovered_media",
    "execute.download_writes_fixture_bytes",
    "execute.invalid_url_is_unsupported",
    "execute.missing_media_reports_http_status",
    "cli.run_downloads_and_prints_report",
    "cli.run_invalid_url_fails",
];

/// A hand-written, ABI-valid defect bound only in a throwaway copy of the example.
struct Defect {
    name: &'static str,
    symbol: &'static str,
    function: &'static str,
    source: &'static str,
    rejected: &'static [(&'static str, &'static str)],
}

static DEFECTS: [Defect; 4] = [
    Defect {
        name: "empty_execute",
        symbol: "real.yt_dlp.execute",
        function: "execute",
        source: include_str!("support/yt_dlp_defects/empty_execute.py"),
        rejected: &[
            (
                "execute.simulate_reports_discovered_media",
                "selected_mismatch",
            ),
            ("execute.download_writes_fixture_bytes", "files_mismatch"),
            ("execute.invalid_url_is_unsupported", "unexpected_success"),
            (
                "execute.missing_media_reports_http_status",
                "unexpected_success",
            ),
            ("cli.run_downloads_and_prints_report", "stdout_mismatch"),
            ("cli.run_invalid_url_fails", "exit_status"),
        ],
    },
    Defect {
        name: "wrong_content",
        symbol: "real.yt_dlp.execute",
        function: "execute",
        source: include_str!("support/yt_dlp_defects/wrong_content.py"),
        rejected: &[
            (
                "execute.simulate_reports_discovered_media",
                "selected_mismatch",
            ),
            ("execute.download_writes_fixture_bytes", "bytes_mismatch"),
            ("execute.invalid_url_is_unsupported", "unexpected_success"),
            (
                "execute.missing_media_reports_http_status",
                "unexpected_success",
            ),
            ("cli.run_downloads_and_prints_report", "stdout_mismatch"),
            ("cli.run_invalid_url_fails", "exit_status"),
        ],
    },
    Defect {
        name: "always_error",
        symbol: "real.yt_dlp.execute",
        function: "execute",
        source: include_str!("support/yt_dlp_defects/always_error.py"),
        rejected: &[
            (
                "execute.simulate_reports_discovered_media",
                "unexpected_error",
            ),
            ("execute.download_writes_fixture_bytes", "unexpected_error"),
            ("execute.invalid_url_is_unsupported", "error_mismatch"),
            (
                "execute.missing_media_reports_http_status",
                "error_mismatch",
            ),
            ("cli.run_downloads_and_prints_report", "exit_status"),
        ],
    },
    Defect {
        name: "skipped_run",
        symbol: "real.yt_dlp.run",
        function: "run",
        source: include_str!("support/yt_dlp_defects/skipped_run.py"),
        rejected: &[
            ("cli.run_downloads_and_prints_report", "stdout_mismatch"),
            ("cli.run_invalid_url_fails", "exit_status"),
        ],
    },
];

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);
static DEPLOYMENT_LOCK: Mutex<()> = Mutex::new(());

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new(label: &str) -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-yt-dlp-{label}-{}-{number}",
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

fn example() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("examples/real/yt-dlp")
}

fn read_json(path: &Path) -> Value {
    let bytes = fs::read(path).unwrap_or_else(|error| panic!("read {}: {error}", path.display()));
    serde_json::from_slice(&bytes)
        .unwrap_or_else(|error| panic!("parse {}: {error}", path.display()))
}

fn current_snapshot(record: &Value) -> &Value {
    let current = record["current"]
        .as_str()
        .expect("generation record names its current snapshot");
    &record["snapshots"][current]
}

/// Refuses unverified or stale setup through the compiler-owned deployment gate. `cott deploy`
/// rejects an unverified, unresolved, stale-compiler, input-changed, managed-byte-modified or
/// coverage-failing snapshot, then copies exactly the verified runtime tree and adapters.
fn verified_deployment(root: &Path) -> PathBuf {
    let _guard = DEPLOYMENT_LOCK
        .lock()
        .expect("serialize the read-only project deployment gate");
    let project = example();
    let deployment = root.join("deployment");
    let deployed = Command::new(env!("CARGO_BIN_EXE_cott"))
        .arg("deploy")
        .arg("--output")
        .arg(&deployment)
        .arg("--project")
        .arg(&project)
        .output()
        .expect("run cott deploy");
    assert!(
        deployed.status.success(),
        "refusing unverified or stale examples/real/yt-dlp; run `cott generate` and `cott verify` first:\n{}",
        String::from_utf8_lossy(&deployed.stderr)
    );
    assert_eq!(
        fs::read(deployment.join("generation.json")).expect("read deployed generation record"),
        fs::read(project.join("generated/generation.json"))
            .expect("read example generation record"),
        "deployment must carry the unchanged verified generation record"
    );
    deployment
}

/// The verified record names the interpreter; its bytes must still match that evidence.
fn recorded_interpreter(record: &Path) -> PathBuf {
    let record = read_json(record);
    let python = &current_snapshot(&record)["tools"]["python"];
    let executable = PathBuf::from(
        python["executable"]
            .as_str()
            .expect("verified record names its Python interpreter"),
    );
    let bytes = fs::read(&executable).unwrap_or_else(|error| {
        panic!(
            "recorded interpreter {} is unavailable: {error}",
            executable.display()
        )
    });
    assert_eq!(
        Some(format!("sha256:{}", sha256_hex(&bytes)).as_str()),
        python["content_hash"].as_str(),
        "recorded interpreter {} changed since verification",
        executable.display()
    );
    executable
}

fn text(path: &Path) -> String {
    path.to_str()
        .unwrap_or_else(|| panic!("path is not UTF-8: {}", path.display()))
        .to_owned()
}

/// Runs the regression program in the existing sandbox with isolated loopback only.
fn run_program(
    interpreter: &Path,
    python_root: &Path,
    app: &Path,
    mut read_only: Vec<PathBuf>,
    work: &Path,
    subject: &str,
) -> Value {
    if !interpreter.starts_with("/usr") {
        read_only.push(
            interpreter
                .parent()
                .and_then(Path::parent)
                .expect("interpreter has an installation prefix")
                .to_path_buf(),
        );
    }
    let result = run(&SandboxSpec {
        program: interpreter.to_path_buf(),
        arguments: vec![
            "-c".to_owned(),
            PROGRAM.to_owned(),
            "--python-root".to_owned(),
            text(python_root),
            "--app".to_owned(),
            text(app),
            "--work".to_owned(),
            text(work),
            "--subject".to_owned(),
            subject.to_owned(),
        ],
        cwd: work.to_path_buf(),
        environment: BTreeMap::from([
            ("HOME".to_owned(), text(work)),
            ("PATH".to_owned(), "/usr/bin:/bin".to_owned()),
            ("PYTHONDONTWRITEBYTECODE".to_owned(), "1".to_owned()),
            ("PYTHONHASHSEED".to_owned(), "0".to_owned()),
            ("PYTHONPATH".to_owned(), text(python_root)),
            ("TMPDIR".to_owned(), text(work)),
        ]),
        stdin: Vec::new(),
        binds: BindMounts {
            read_only,
            writable: vec![work.to_path_buf()],
        },
        network: NetworkAccess::IsolatedLoopback,
        limits: ResourceLimits {
            cpu_time: Duration::from_secs(300),
            address_space_bytes: 2 * 1024 * 1024 * 1024,
            process_count: 64,
            open_files: 256,
            file_size_bytes: 16 * 1024 * 1024,
            wall_time: Duration::from_secs(600),
            stream_limit_bytes: 1024 * 1024,
            writable_bytes: 64 * 1024 * 1024,
        },
    });
    let completed = result.unwrap_or_else(|error| {
        panic!("{EVIDENCE_KIND} sandbox execution failed; no host-network fallback: {error}")
    });
    let stderr = String::from_utf8_lossy(&completed.stderr);
    let line = completed
        .stdout
        .rsplit(|byte| *byte == b'\n')
        .find(|line| !line.is_empty())
        .unwrap_or_else(|| {
            panic!(
                "{subject}: program produced no report (status {:?}):\n{stderr}",
                completed.status
            )
        });
    let report: Value = serde_json::from_slice(line)
        .unwrap_or_else(|error| panic!("{subject}: invalid report {error}:\n{stderr}"));
    println!("{}", String::from_utf8_lossy(line));
    assert_eq!(report["evidence_kind"], EVIDENCE_KIND);
    assert_eq!(report["cott_scenario_evidence"], false);
    assert_eq!(report["subject"], subject);
    assert_ne!(
        report["verdict"], "refused",
        "{subject}: program refused its setup: {}",
        report["refusal"]
    );
    assert!(
        report["subject_description"].is_string(),
        "{subject}: report must describe its program tree"
    );
    let expected_status = if report["verdict"] == "passed" { 0 } else { 1 };
    assert_eq!(
        completed.status,
        Some(expected_status),
        "{subject}: exit status disagrees with its report:\n{stderr}"
    );
    let ids = report["checks"]
        .as_array()
        .expect("report lists checks")
        .iter()
        .map(|check| check["id"].as_str().expect("check id").to_owned())
        .collect::<Vec<_>>();
    assert_eq!(
        ids, CHECKS,
        "{subject}: every regression check must run: {}",
        report["checks"]
    );
    report
}

fn failures(report: &Value) -> BTreeMap<String, String> {
    report["checks"]
        .as_array()
        .expect("report lists checks")
        .iter()
        .filter(|check| check["passed"] != true)
        .map(|check| {
            (
                check["id"].as_str().expect("check id").to_owned(),
                check["reason"].as_str().expect("failure reason").to_owned(),
            )
        })
        .collect()
}

fn copy_tree(source: &Path, destination: &Path) {
    fs::create_dir_all(destination).expect("create fixture directory");
    for entry in fs::read_dir(source).expect("read example directory") {
        let entry = entry.expect("read example entry");
        let name = entry.file_name();
        if matches!(
            name.to_str(),
            Some(".venv" | ".cott" | "dist" | "__pycache__")
        ) || name.to_string_lossy().ends_with(".pyc")
        {
            continue;
        }
        let kind = entry.file_type().expect("inspect example entry");
        let target = destination.join(&name);
        if kind.is_dir() {
            copy_tree(&entry.path(), &target);
        } else if kind.is_file() {
            fs::copy(entry.path(), target).expect("copy example file");
        } else {
            panic!(
                "example contains a non-regular entry: {}",
                entry.path().display()
            );
        }
    }
}

/// Compiler-binds one defect in a throwaway copy through the supported manifest binding, so its
/// facade, wrapper and provenance come from real `cott emit`. The original lockfile and production
/// dependency selection stay intact; only the selected callable's implementation is replaced.
fn bind_defect(project: &Path, defect: &Defect, interpreter: &Path) {
    let manifest_path = project.join("cott.toml");
    let manifest = fs::read_to_string(&manifest_path).expect("read fixture manifest");
    assert!(
        !manifest.contains("[target.python.implementations]"),
        "examples/real/yt-dlp must not select manifest bindings"
    );
    let pyproject: toml::Value = toml::from_str(
        &fs::read_to_string(project.join("python/pyproject.toml")).expect("read pyproject"),
    )
    .expect("parse pyproject");
    assert_eq!(
        pyproject["project"]["dependencies"]
            .as_array()
            .map(Vec::len),
        Some(0),
        "defect fixtures require a runtime-dependency-free example"
    );
    fs::write(
        &manifest_path,
        format!(
            "{}\n[target.python.implementations]\n\"{}\" = \"cott_bindings.real.yt_dlp.{}:{}\"\n",
            manifest, defect.symbol, defect.name, defect.function
        ),
    )
    .expect("write fixture manifest");
    let bindings = project.join("python/cott_bindings");
    fs::create_dir_all(bindings.join("real/yt_dlp")).expect("create binding package");
    fs::write(bindings.join("__init__.py"), "").expect("write binding package");
    fs::write(bindings.join("real/__init__.py"), "").expect("write binding package");
    fs::write(
        bindings.join(format!("real/yt_dlp/{}.py", defect.name)),
        defect.source,
    )
    .expect("write defect binding");
    let bin = project.join(".venv/bin");
    fs::create_dir_all(&bin).expect("create fixture environment");
    symlink(interpreter, bin.join("python")).expect("link recorded interpreter");

    let emitted = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(["emit", "python", "--project"])
        .arg(project)
        .output()
        .expect("run cott emit python");
    assert!(
        emitted.status.success(),
        "{}: compiler binding failed:\n{}",
        defect.name,
        String::from_utf8_lossy(&emitted.stderr)
    );
    let record = read_json(&project.join("generated/generation.json"));
    let snapshot = current_snapshot(&record);
    assert_eq!(
        snapshot["verified"], false,
        "defect fixtures are never certified"
    );
    assert_eq!(
        snapshot["unresolved"].as_array().map(Vec::len),
        Some(0),
        "{}: defect fixture leaves callables unresolved: {}",
        defect.name,
        snapshot["unresolved"]
    );
    let binding = snapshot["implementations"]
        .as_array()
        .expect("implementations")
        .iter()
        .find(|implementation| implementation["cott_symbol"] == defect.symbol)
        .unwrap_or_else(|| panic!("{}: bound symbol is absent", defect.name));
    assert_eq!(binding["owner"], "manifest");
    assert_eq!(
        binding["source_origin"],
        format!("python/cott_bindings/real/yt_dlp/{}.py", defect.name)
    );
    assert_eq!(
        binding["content_hash"],
        format!("sha256:{}", sha256_hex(defect.source.as_bytes()))
    );
}

fn defect_failures(defect: &Defect, interpreter: &Path) -> BTreeMap<String, String> {
    let fixture = TempDir::new(defect.name);
    let project = fixture.path.join("project");
    copy_tree(&example(), &project);
    bind_defect(&project, defect, interpreter);
    let work = fixture.path.join("work");
    fs::create_dir(&work).expect("create regression work directory");
    let python_root = project.join("generated/python");
    let report = run_program(
        interpreter,
        &python_root,
        &project.join("python/app.py"),
        vec![project.join("generated"), project.join("python")],
        &work,
        &format!("defect-fixture:{}", defect.name),
    );
    assert_eq!(
        report["verdict"], "failed",
        "{}: defect was accepted",
        defect.name
    );
    failures(&report)
}

#[test]
#[ignore = "external_program_regression: needs generated+verified examples/real/yt-dlp, its recorded CPython and Linux isolated loopback"]
fn verified_yt_dlp_program_passes_external_regressions() {
    let record_path = example().join("generated/generation.json");
    let record_before = fs::read(&record_path).expect("read example generation record");
    let root = TempDir::new("verified");
    let deployment = verified_deployment(&root.path);
    let interpreter = recorded_interpreter(&deployment.join("generation.json"));
    let work = root.path.join("work");
    fs::create_dir(&work).expect("create regression work directory");
    let python_root = deployment.join("python");
    let report = run_program(
        &interpreter,
        &python_root,
        &python_root.join("app.py"),
        vec![deployment.clone()],
        &work,
        "verified-deployment",
    );
    assert_eq!(
        failures(&report),
        BTreeMap::new(),
        "verified yt-dlp program failed its external regressions"
    );
    assert_eq!(
        fs::read(&record_path).expect("reread example generation record"),
        record_before,
        "external regressions must not change the example generation record"
    );
}

#[test]
#[ignore = "external_program_regression: needs generated+verified examples/real/yt-dlp, its recorded CPython and Linux isolated loopback"]
fn external_regressions_reject_compiler_bound_defects() {
    let root = TempDir::new("defects");
    let deployment = verified_deployment(&root.path);
    let interpreter = recorded_interpreter(&deployment.join("generation.json"));
    let interpreter = interpreter.as_path();
    // Each fixed fixture owns several bounded processes; avoid multiplying their
    // resource envelopes just to collect four independent behavioral verdicts.
    for defect in &DEFECTS {
        let failures = defect_failures(defect, interpreter);
        let expected = defect
            .rejected
            .iter()
            .map(|(check, reason)| ((*check).to_owned(), (*reason).to_owned()))
            .collect::<BTreeMap<_, _>>();
        assert_eq!(
            failures, expected,
            "{}: defect must be rejected for exactly its behavioral reasons",
            defect.name
        );
    }
}
