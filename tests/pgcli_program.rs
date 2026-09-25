//! External-process regressions of verified pgcli against scratch PostgreSQL on a Unix socket.
//! Run with COTT_POSTGRES_BIN=/path/to/16/bin /tmp/cott-ex/cargox test --test pgcli_program -- --ignored --nocapture
use cott::hash::sha256_hex;
use cott::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxSpec, run};
use serde_json::Value;
use std::collections::BTreeMap;
use std::fs;
use std::io;
use std::os::unix::fs::symlink;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::Mutex;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Duration;

const PROGRAM: &str = include_str!("support/pgcli_program.py");
const KIND: &str = "external_program_regression";
const CHECKS: [&str; 7] = [
    "database.connect",
    "database.query_transactions",
    "database.catalog_refresh",
    "database.import_export",
    "database.notifications",
    "cli.run_exit_codes",
    "cli.interactive",
];
const DEFECT: &str = "from typing import Never\nfrom cott_runtime import CottList\n\ndef run(arguments: CottList[str]) -> Never:\n    raise SystemExit(0)\n";
static NEXT_DIR: AtomicU64 = AtomicU64::new(0);
static DEPLOYMENT_LOCK: Mutex<()> = Mutex::new(());

struct Scratch(PathBuf);
impl Scratch {
    fn new(label: &str) -> Self {
        let mut n = NEXT_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path =
                std::env::temp_dir().join(format!("cott-pgcli-{label}-{}-{n}", std::process::id()));
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
    Path::new(env!("CARGO_MANIFEST_DIR")).join("examples/real/pgcli")
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
    let _guard = DEPLOYMENT_LOCK
        .lock()
        .expect("serialize example deployment");
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
        "refusing stale/unverified pgcli: {}",
        String::from_utf8_lossy(&result.stderr)
    );
    assert_eq!(
        fs::read(output.join("generation.json")).unwrap(),
        fs::read(example().join("generated/generation.json")).unwrap()
    );
    output
}
fn packages() -> PathBuf {
    example().join(".venv/lib/python3.14/site-packages")
}
fn postgres() -> PathBuf {
    let bin = PathBuf::from(std::env::var_os("COTT_POSTGRES_BIN").expect("set COTT_POSTGRES_BIN to a PostgreSQL bin directory; PostgreSQL binaries are not installed system-wide"));
    assert!(bin.is_absolute(), "COTT_POSTGRES_BIN must be absolute");
    for name in ["initdb", "postgres"] {
        assert!(
            bin.join(name).is_file(),
            "missing {}",
            bin.join(name).display()
        );
    }
    bin
}
fn program(
    interpreter: &Path,
    root: &Path,
    app: &Path,
    read_only: Vec<PathBuf>,
    work: &Path,
    subject: &str,
    bin: &Path,
) -> Value {
    assert!(
        packages().is_dir(),
        "install example locked dependencies before running external regressions"
    );
    let prefix = bin.ancestors().nth(5).expect("PostgreSQL package root");
    assert!(
        prefix.join("usr/share/postgresql/16").is_dir(),
        "relocated PostgreSQL share directory missing"
    );
    let mut read_only = read_only;
    read_only.push(packages());
    read_only.push(prefix.to_path_buf());
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
            "--postgres-bin".into(),
            str_path(bin),
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
            (
                "LD_LIBRARY_PATH".into(),
                str_path(&prefix.join("usr/lib/x86_64-linux-gnu")),
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
            address_space_bytes: 2 * 1024 * 1024 * 1024,
            process_count: 64,
            open_files: 256,
            file_size_bytes: 16 * 1024 * 1024,
            wall_time: Duration::from_secs(360),
            stream_limit_bytes: 1024 * 1024,
            writable_bytes: 256 * 1024 * 1024,
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
fn copy_tree(source: &Path, destination: &Path) {
    fs::create_dir_all(destination).unwrap();
    for entry in fs::read_dir(source).unwrap() {
        let entry = entry.unwrap();
        let name = entry.file_name();
        if matches!(
            name.to_str(),
            Some(".venv" | ".cott" | "dist" | "__pycache__")
        ) || name.to_string_lossy().ends_with(".pyc")
        {
            continue;
        }
        let target = destination.join(&name);
        if entry.file_type().unwrap().is_dir() {
            copy_tree(&entry.path(), &target);
        } else {
            assert!(entry.file_type().unwrap().is_file());
            fs::copy(entry.path(), target).unwrap();
        }
    }
}
#[test]
#[ignore = "external_program_regression: needs generated+verified examples/real/pgcli, locked Python dependencies, COTT_POSTGRES_BIN and Linux sandbox"]
fn verified_pgcli_program_passes() {
    let bin = postgres();
    let before = fs::read(example().join("generated/generation.json")).unwrap();
    let temp = Scratch::new("verified");
    let deployment = deploy(&temp.0);
    let python = interpreter(&deployment.join("generation.json"));
    let work = temp.0.join("work");
    fs::create_dir(&work).unwrap();
    let report = program(
        &python,
        &deployment.join("python"),
        &deployment.join("python/pgcli_cli.py"),
        vec![deployment],
        &work,
        "verified-deployment",
        &bin,
    );
    assert_eq!(failures(&report), BTreeMap::new());
    assert_eq!(
        fs::read(example().join("generated/generation.json")).unwrap(),
        before
    );
}
#[test]
#[ignore = "external_program_regression: needs generated+verified examples/real/pgcli, locked Python dependencies, COTT_POSTGRES_BIN and Linux sandbox"]
fn external_regression_rejects_bound_skipped_run() {
    let bin = postgres();
    let temp = Scratch::new("defect");
    let deployment = deploy(&temp.0);
    let python = interpreter(&deployment.join("generation.json"));
    let fixture = temp.0.join("fixture");
    copy_tree(&example(), &fixture);
    let manifest = fixture.join("cott.toml");
    let original = fs::read_to_string(&manifest).unwrap();
    assert!(!original.contains("[target.python.implementations]"));
    fs::write(&manifest, format!("{original}\n[target.python.implementations]\n\"real.pgcli.run\" = \"cott_bindings.real.pgcli_defect:run\"\n")).unwrap();
    let bindings = fixture.join("python/cott_bindings/real");
    fs::create_dir_all(&bindings).unwrap();
    fs::write(fixture.join("python/cott_bindings/__init__.py"), "").unwrap();
    fs::write(bindings.join("pgcli_defect.py"), DEFECT).unwrap();
    fs::create_dir_all(fixture.join(".venv/bin")).unwrap();
    symlink(&python, fixture.join(".venv/bin/python")).unwrap();
    fs::copy(
        example().join(".venv/pyvenv.cfg"),
        fixture.join(".venv/pyvenv.cfg"),
    )
    .unwrap();
    copy_tree(
        &packages(),
        &fixture.join(".venv/lib/python3.14/site-packages"),
    );
    let emitted = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(["emit", "python", "--project"])
        .arg(&fixture)
        .output()
        .unwrap();
    assert!(
        emitted.status.success(),
        "compiler rejected type-valid defect: {}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let data = record(&fixture.join("generated/generation.json"));
    let snapshot = &data["snapshots"][data["current"].as_str().unwrap()];
    assert_eq!(snapshot["verified"], false);
    assert_eq!(snapshot["unresolved"].as_array().map(Vec::len), Some(0));
    let binding = snapshot["implementations"]
        .as_array()
        .unwrap()
        .iter()
        .find(|v| v["cott_symbol"] == "real.pgcli.run")
        .unwrap();
    assert_eq!(binding["owner"], "manifest");
    assert_eq!(
        binding["source_origin"],
        "python/cott_bindings/real/pgcli_defect.py"
    );
    assert_eq!(
        binding["content_hash"],
        format!("sha256:{}", sha256_hex(DEFECT.as_bytes()))
    );
    let work = temp.0.join("work");
    fs::create_dir(&work).unwrap();
    let report = program(
        &python,
        &fixture.join("generated/python"),
        &fixture.join("python/pgcli_cli.py"),
        vec![fixture.join("generated"), fixture.join("python")],
        &work,
        "defect-fixture:skipped_run",
        &bin,
    );
    assert_eq!(report["verdict"], "failed");
    assert_eq!(
        failures(&report)
            .get("cli.run_exit_codes")
            .map(String::as_str),
        Some("usage_text")
    );
}
