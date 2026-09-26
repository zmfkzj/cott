//! External-process regressions for the verified Harlequin deployment; never Cott scenario evidence.
//! Run: cargo test --test harlequin_program -- --ignored --nocapture
use std::collections::BTreeMap;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Duration;

use cott::hash::sha256_hex;
use cott::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxSpec, run};
use serde_json::Value;

const PROGRAM: &str = include_str!("support/harlequin_program.py");
const KIND: &str = "external_program_regression";
const CHECKS: [&str; 5] = [
    "hsql.sqlite_csv",
    "hsql.duckdb_csv",
    "hsql.stdin_sql",
    "hsql.error_statuses",
    "hsql.machine_spec",
];
static NEXT_DIR: AtomicU64 = AtomicU64::new(0);

struct Scratch(PathBuf);
impl Scratch {
    fn new(label: &str) -> Self {
        let mut n = NEXT_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir()
                .join(format!("cott-harlequin-{label}-{}-{n}", std::process::id()));
            match fs::create_dir(&path) {
                Ok(()) => return Self(path),
                Err(e) if e.kind() == io::ErrorKind::AlreadyExists => n += 1,
                Err(e) => panic!("create scratch: {e}"),
            }
        }
    }
}
impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}
fn example() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("examples/real/harlequin")
}
fn str_path(path: &Path) -> String {
    path.to_str().expect("UTF-8 path").to_owned()
}
fn record(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).expect("generation record")).expect("JSON record")
}
fn interpreter(path: &Path) -> PathBuf {
    let data = record(path);
    let tool = &data["snapshots"][data["current"].as_str().expect("current")]["tools"]["python"];
    let executable = PathBuf::from(tool["executable"].as_str().expect("interpreter"));
    assert_eq!(
        tool["content_hash"],
        format!(
            "sha256:{}",
            sha256_hex(&fs::read(&executable).expect("interpreter bytes"))
        )
    );
    executable
}
fn deploy(root: &Path) -> PathBuf {
    let output = root.join("deployment");
    let result = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(["deploy", "--output"])
        .arg(&output)
        .arg("--project")
        .arg(example())
        .output()
        .expect("cott deploy");
    assert!(
        result.status.success(),
        "refusing stale/unverified Harlequin: {}",
        String::from_utf8_lossy(&result.stderr)
    );
    output
}
fn packages() -> PathBuf {
    example().join(".venv/lib/python3.14/site-packages")
}
fn program(
    interpreter: &Path,
    root: &Path,
    app: &Path,
    read_only: Vec<PathBuf>,
    work: &Path,
    subject: &str,
) -> Value {
    assert!(
        packages().is_dir(),
        "install example locked dependencies before running external regressions"
    );
    let mut read_only = read_only;
    read_only.push(packages());
    if !interpreter.starts_with("/usr") {
        read_only.push(
            interpreter
                .parent()
                .unwrap()
                .parent()
                .unwrap()
                .to_path_buf(),
        );
    }
    let result = run(&SandboxSpec {
        program: interpreter.to_path_buf(),
        arguments: vec![
            "-c".into(),
            PROGRAM.into(),
            "--python-root".into(),
            str_path(root),
            "--app".into(),
            str_path(app),
            "--work".into(),
            str_path(work),
            "--subject".into(),
            subject.into(),
        ],
        cwd: work.to_path_buf(),
        environment: BTreeMap::from([
            ("HOME".into(), str_path(work)),
            ("PATH".into(), "/usr/bin:/bin".into()),
            (
                "PYTHONPATH".into(),
                format!("{}:{}", root.display(), packages().display()),
            ),
            ("PYTHONDONTWRITEBYTECODE".into(), "1".into()),
            ("PYTHONHASHSEED".into(), "0".into()),
            ("TMPDIR".into(), str_path(work)),
        ]),
        stdin: Vec::new(),
        binds: BindMounts {
            read_only,
            writable: vec![work.to_path_buf()],
        },
        network: NetworkAccess::Disabled,
        limits: ResourceLimits {
            cpu_time: Duration::from_secs(180),
            address_space_bytes: 4 * 1024 * 1024 * 1024,
            // RLIMIT_NPROC counts all tasks owned by this UID, not just this sandbox.
            process_count: 1024,
            open_files: 256,
            file_size_bytes: 16 * 1024 * 1024,
            wall_time: Duration::from_secs(360),
            stream_limit_bytes: 1024 * 1024,
            writable_bytes: 64 * 1024 * 1024,
        },
    })
    .unwrap_or_else(|e| panic!("{KIND} sandbox refused; no unsandboxed fallback: {e}"));
    let line = result
        .stdout
        .rsplit(|byte| *byte == b'\n')
        .find(|line| !line.is_empty())
        .unwrap_or_else(|| {
            panic!(
                "{subject} produced no report; status {:?}; stderr {}",
                result.status,
                String::from_utf8_lossy(&result.stderr)
            )
        });
    let report: Value = serde_json::from_slice(line).unwrap_or_else(|e| {
        panic!(
            "invalid report: {e}; stderr {}",
            String::from_utf8_lossy(&result.stderr)
        )
    });
    println!("{}", String::from_utf8_lossy(line));
    assert_eq!(report["evidence_kind"], KIND);
    assert_eq!(report["cott_scenario_evidence"], false);
    assert_eq!(report["subject"], subject);
    assert_ne!(report["verdict"], "refused", "{}", report["refusal"]);
    assert!(report["subject_description"].is_string());
    assert_eq!(
        result.status,
        Some(if report["verdict"] == "passed" { 0 } else { 1 })
    );
    let ids: Vec<_> = report["checks"]
        .as_array()
        .expect("checks")
        .iter()
        .map(|v| v["id"].as_str().unwrap())
        .collect();
    assert_eq!(ids, CHECKS);
    report
}
fn failures(report: &Value) -> BTreeMap<String, String> {
    report["checks"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|c| c["passed"] != true)
        .map(|c| {
            (
                c["id"].as_str().unwrap().into(),
                c["reason"].as_str().unwrap().into(),
            )
        })
        .collect()
}

#[test]
#[ignore = "external_program_regression: needs generated+verified examples/real/harlequin and its locked CPython dependencies and Linux sandbox"]
fn verified_harlequin_program_passes() {
    let temp = Scratch::new("verified");
    let deployment = deploy(&temp.0);
    let python = interpreter(&deployment.join("generation.json"));
    let work = temp.0.join("work");
    fs::create_dir(&work).unwrap();
    let report = program(
        &python,
        &deployment.join("python"),
        &deployment.join("python/hsql_cli.py"),
        vec![deployment],
        &work,
        "verified-deployment",
    );
    assert_eq!(failures(&report), BTreeMap::new());
}
