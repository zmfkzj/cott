use std::collections::BTreeMap;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::provenance::{
    ClauseCoverage, CoverageStatus, CoverageViolation, GenerationRecord, SourceSpan,
};

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir()
                .join(format!("cott-deploy-tests-{}-{number}", std::process::id()));
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

const MANIFEST: &str = r#"[project]
name = "demo"
version = "0.1.0"
source = "src"

[target.python]
source = "python"
generated = "generated/python"
stubs = "generated/stubs"
interpreter = ".venv/bin/python"
type_checker = ".venv/bin/basedpyright"
runtime_validation = "boundary"
"#;
const IMPLEMENTATION_BINDING: &str =
    "\n[target.python.implementations]\n\"api.service.run\" = \"cott_bindings.api.service:run\"\n";
const SOURCE: &str = "module api.service\n\nfn run() -> I32:\n    ensures result > 0\n";
const BINDING: &str = "from cott_runtime import I32\n\n\ndef run() -> I32:\n    return 7\n";
const CLI_ADAPTER: &str =
    "from api.service import run\n\n\ndef main() -> int:\n    return int(run())\n";
const CLI_ENTRYPOINT: &str =
    "from demo_cli import main\n\n\nif __name__ == \"__main__\":\n    raise SystemExit(main())\n";
const EXCLUDED_MARKER: &[u8] = b"EXCLUDED_DEPLOY_FIXTURE = True\n";

fn write_file(root: &Path, relative: &str, bytes: impl AsRef<[u8]>) {
    let path = root.join(relative);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).expect("fixture parent directory should be creatable");
    }
    fs::write(path, bytes).expect("fixture file should be writable");
}

fn project(with_binding: bool) -> TempDir {
    let temp = TempDir::new();
    let mut manifest = MANIFEST.to_owned();
    if with_binding {
        manifest.push_str(IMPLEMENTATION_BINDING);
    }
    write_file(&temp.path, "cott.toml", manifest);
    write_file(&temp.path, "src/api/service.cott", SOURCE);
    write_file(
        &temp.path,
        "python/pyproject.toml",
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14.6,<3.15\"\ndependencies = []\n",
    );
    write_file(&temp.path, "python/demo_cli/__init__.py", CLI_ADAPTER);
    write_file(&temp.path, "python/demo_cli/__main__.py", CLI_ENTRYPOINT);
    if with_binding {
        write_file(&temp.path, "python/cott_bindings/api/service.py", BINDING);
    }
    temp
}

fn cott_emit_python(root: &Path) {
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(["emit", "python", "--project"])
        .arg(root)
        .output()
        .expect("cott emit python should run");
    assert!(
        output.status.success(),
        "cott emit python failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(root.join("generated/generation.json").is_file());
}

fn store_record(root: &Path, record: &GenerationRecord) {
    let bytes = record
        .canonical_bytes()
        .expect("deploy gate fixture should remain a valid generation record");
    fs::write(root.join("generated/generation.json"), bytes)
        .expect("generation record should be writable");
}

fn certify_emitted_record(root: &Path) -> GenerationRecord {
    let path = root.join("generated/generation.json");
    let mut record = GenerationRecord::parse(
        &fs::read(&path).expect("real emitted generation record should be readable"),
    )
    .expect("real emitted generation record should parse");

    // This only creates a certified fixture for independently exercising deploy's
    // gates. It is not evidence that `cott verify` ran or that verification passed.
    record.current.verified = true;
    record.last_verified = Some(record.current.clone());
    store_record(root, &record);
    record
}

fn emit_and_certify(root: &Path) -> Vec<u8> {
    cott_emit_python(root);
    let record = certify_emitted_record(root);
    let bytes = fs::read(root.join("generated/generation.json"))
        .expect("certified generation bytes should be readable");
    GenerationRecord::parse(&bytes).expect("certified generation bytes should parse");
    assert_eq!(bytes, record.canonical_bytes().expect("canonical record"));
    bytes
}

fn deploy(root: &Path, output: Option<&Path>, cwd: &Path, json: bool) -> Output {
    let mut command = Command::new(env!("CARGO_BIN_EXE_cott"));
    command.arg("deploy");
    if let Some(output) = output {
        command.arg("--output").arg(output);
    }
    command.arg("--project").arg(root);
    if json {
        command.args(["--format", "json"]);
    }
    command
        .current_dir(cwd)
        .output()
        .expect("cott deploy should run")
}

fn assert_success_json(output: &Output) {
    assert!(
        output.status.success(),
        "cott deploy failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("deploy success should report JSON");
    let diagnostics = report["diagnostics"]
        .as_array()
        .expect("deploy JSON should use the diagnostic envelope");
    assert!(
        diagnostics
            .iter()
            .any(|diagnostic| diagnostic["severity"] == "note")
    );
    assert!(
        diagnostics
            .iter()
            .all(|diagnostic| diagnostic["severity"] != "error")
    );
}

fn assert_rejected_json(output: &Output, absent_output: &Path) {
    assert!(!output.status.success(), "deploy should have been rejected");
    let report: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("deploy rejection should report JSON");
    assert!(
        report["diagnostics"]
            .as_array()
            .expect("deploy JSON should use the diagnostic envelope")
            .iter()
            .any(|diagnostic| diagnostic["severity"] == "error")
    );
    assert!(
        !absent_output.exists(),
        "rejected deployment must not publish output"
    );
}

fn file_snapshot(root: &Path) -> BTreeMap<PathBuf, Vec<u8>> {
    fn visit(root: &Path, directory: &Path, files: &mut BTreeMap<PathBuf, Vec<u8>>) {
        let mut entries = fs::read_dir(directory)
            .expect("snapshot directory should be readable")
            .collect::<Result<Vec<_>, _>>()
            .expect("snapshot entries should be readable");
        entries.sort_by_key(|entry| entry.file_name());
        for entry in entries {
            let path = entry.path();
            if entry
                .file_type()
                .expect("snapshot entry type should be readable")
                .is_dir()
            {
                visit(root, &path, files);
            } else {
                files.insert(
                    path.strip_prefix(root)
                        .expect("snapshot file should remain below root")
                        .to_path_buf(),
                    fs::read(path).expect("snapshot file should be readable"),
                );
            }
        }
    }

    let mut files = BTreeMap::new();
    visit(root, root, &mut files);
    files
}

fn add_excluded_authored_files(root: &Path) {
    for path in [
        "python/_cott_impl/copied.py",
        "python/tests/test_cli.py",
        "python/dev/tool.py",
        "python/.cache/hidden.py",
        "python/.venv/ignored.py",
        "python/__pycache__/ignored.py",
        "python/test_probe.py",
    ] {
        write_file(root, path, EXCLUDED_MARKER);
    }
    write_file(root, "python/cache.pyc", EXCLUDED_MARKER);
    write_file(root, "python/api/service.pyi", EXCLUDED_MARKER);
    write_file(root, "python/runtime.txt", EXCLUDED_MARKER);
}

fn bytes_contain(bytes: &[u8], needle: &[u8]) -> bool {
    !needle.is_empty() && bytes.windows(needle.len()).any(|window| window == needle)
}

#[test]
fn deploy_relocates_only_runtime_files_and_preserves_generation_bytes() {
    let project = project(true);
    let generation = emit_and_certify(&project.path);
    add_excluded_authored_files(&project.path);
    let invocation = TempDir::new();
    let relative_output = Path::new("release");

    let output = deploy(&project.path, Some(relative_output), &invocation.path, true);
    assert_success_json(&output);

    let bundle = invocation.path.join(relative_output);
    assert!(bundle.is_dir());
    assert!(!project.path.join(relative_output).exists());
    assert_eq!(
        fs::read(bundle.join("python/demo_cli/__init__.py")).expect("runtime CLI adapter"),
        CLI_ADAPTER.as_bytes()
    );
    assert_eq!(
        fs::read(bundle.join("python/demo_cli/__main__.py")).expect("runtime CLI entry point"),
        CLI_ENTRYPOINT.as_bytes()
    );
    for generated in [
        "api/service.py",
        "api/service_types.py",
        "_cott_impl/api/service/run.py",
        "cott_runtime/__init__.py",
    ] {
        assert_eq!(
            fs::read(bundle.join("python").join(generated))
                .unwrap_or_else(|error| panic!("deployed generated file {generated}: {error}")),
            fs::read(project.path.join("generated/python").join(generated))
                .expect("real generated source should be readable")
        );
    }
    assert_eq!(
        fs::read(bundle.join("generation.json")).expect("deployed generation record"),
        generation
    );
    assert_eq!(
        fs::read(project.path.join("generated/generation.json")).expect("source generation record"),
        generation
    );
    assert_eq!(
        fs::read(bundle.join(".python-version")).expect("deployed Python version"),
        b"3.14.6\n"
    );
    assert_eq!(
        fs::read(bundle.join("requirements.txt")).expect("deployed requirements"),
        b""
    );

    let files = file_snapshot(&bundle);
    for excluded in [
        "python/cott_bindings/api/service.py",
        "python/_cott_impl/copied.py",
        "python/tests/test_cli.py",
        "python/dev/tool.py",
        "python/.cache/hidden.py",
        "python/.venv/ignored.py",
        "python/__pycache__/ignored.py",
        "python/test_probe.py",
        "python/cache.pyc",
        "python/api/service.pyi",
        "python/runtime.txt",
        "src/api/service.cott",
        "ir/api/service.json",
        "stubs/api/service.pyi",
        "generated/python/api/service.py",
    ] {
        assert!(
            !files.contains_key(Path::new(excluded)),
            "development-only file leaked into bundle: {excluded}"
        );
    }
    assert!(
        files
            .values()
            .all(|bytes| !bytes_contain(bytes, EXCLUDED_MARKER)),
        "excluded authored bytes must not be repackaged under another path"
    );

    let default_output = project.path.join("dist/demo-0.1.0");
    let default = deploy(&project.path, None, &invocation.path, false);
    assert!(
        default.status.success(),
        "default deploy failed: {}",
        String::from_utf8_lossy(&default.stderr)
    );
    assert!(default_output.is_dir());
}

#[test]
fn deploy_rejects_recorded_input_and_managed_artifact_byte_drift() {
    let project = project(true);
    emit_and_certify(&project.path);

    let input = project.path.join("src/api/service.cott");
    let original_input = fs::read(&input).expect("recorded input");
    let mut changed_input = original_input.clone();
    changed_input.extend_from_slice(b"\n");
    fs::write(&input, changed_input).expect("recorded input should be mutable");
    let input_output = project.path.join("deploy-input-drift");
    let rejected = deploy(&project.path, Some(&input_output), &project.path, true);
    assert_rejected_json(&rejected, &input_output);
    fs::write(&input, original_input).expect("recorded input should be restorable");

    let managed = project.path.join("generated/python/api/service.py");
    let mut changed_managed = fs::read(&managed).expect("managed generated facade");
    changed_managed.extend_from_slice(b"# byte drift\n");
    fs::write(&managed, changed_managed).expect("managed generated facade should be mutable");
    let managed_output = project.path.join("deploy-managed-drift");
    let rejected = deploy(&project.path, Some(&managed_output), &project.path, true);
    assert_rejected_json(&rejected, &managed_output);
}

#[derive(Clone, Copy, Debug)]
enum RejectedGate {
    Unverified,
    Pending,
    FailedCoveragePolicy,
}

#[test]
fn deploy_rejects_independent_certification_gates() {
    for gate in [
        RejectedGate::Unverified,
        RejectedGate::Pending,
        RejectedGate::FailedCoveragePolicy,
    ] {
        let project = project(!matches!(gate, RejectedGate::Pending));
        cott_emit_python(&project.path);
        let mut record = certify_emitted_record(&project.path);

        match gate {
            RejectedGate::Unverified => {
                assert!(record.current.unresolved.is_empty());
                assert!(record.current.semantic_coverage.policy.passed);
                record.current.verified = false;
            }
            RejectedGate::Pending => {
                assert!(record.current.verified);
                assert!(!record.current.unresolved.is_empty());
                assert!(record.current.semantic_coverage.policy.passed);
            }
            RejectedGate::FailedCoveragePolicy => {
                assert!(record.current.verified);
                assert!(record.current.unresolved.is_empty());
                let span = SourceSpan {
                    start_byte: 38,
                    end_byte: 56,
                    start_line: 4,
                    start_column: 5,
                    end_line: 4,
                    end_column: 23,
                };
                record.current.semantic_coverage.clauses = vec![ClauseCoverage {
                    symbol: "api.service.run".to_owned(),
                    clause_id: "ensures:0".to_owned(),
                    span: span.clone(),
                    status: CoverageStatus::Unobserved,
                    evidence: Vec::new(),
                }];
                record.current.semantic_coverage.summary.unobserved = 1;
                record.current.semantic_coverage.policy.selected = 1;
                record.current.semantic_coverage.policy.passed = false;
                record.current.semantic_coverage.policy.violations = vec![CoverageViolation {
                    symbol: "api.service.run".to_owned(),
                    clause_id: "ensures:0".to_owned(),
                    span,
                    status: CoverageStatus::Unobserved,
                    reason: "fixture policy selection was not observed".to_owned(),
                }];
            }
        }
        store_record(&project.path, &record);

        let output_path = project.path.join(format!("rejected-{gate:?}"));
        let rejected = deploy(&project.path, Some(&output_path), &project.path, true);
        assert_rejected_json(&rejected, &output_path);
    }
}

#[test]
fn deploy_refuses_preexisting_default_output_without_changing_user_content() {
    let project = project(true);
    emit_and_certify(&project.path);
    let output_path = project.path.join("dist/demo-0.1.0");
    write_file(&output_path, "user/note.txt", b"keep me\n");
    let before = file_snapshot(&output_path);

    let rejected = deploy(&project.path, None, &project.path, true);

    assert!(!rejected.status.success());
    let report: serde_json::Value =
        serde_json::from_slice(&rejected.stdout).expect("deploy rejection should report JSON");
    assert!(
        report["diagnostics"]
            .as_array()
            .expect("deploy JSON should use the diagnostic envelope")
            .iter()
            .any(|diagnostic| diagnostic["severity"] == "error")
    );
    assert_eq!(file_snapshot(&output_path), before);
}

#[cfg(unix)]
#[test]
fn deploy_refuses_symlink_output_without_changing_its_target() {
    use std::os::unix::fs::symlink;

    let project = project(true);
    emit_and_certify(&project.path);
    let invocation = TempDir::new();
    let victim = invocation.path.join("user-content");
    write_file(&victim, "note.txt", b"keep me\n");
    let before = file_snapshot(&victim);
    let output_path = invocation.path.join("release");
    symlink(&victim, &output_path).expect("output symlink should be creatable");

    let rejected = deploy(
        &project.path,
        Some(Path::new("release")),
        &invocation.path,
        false,
    );

    assert!(!rejected.status.success());
    assert!(
        fs::symlink_metadata(&output_path)
            .expect("output symlink should remain")
            .file_type()
            .is_symlink()
    );
    assert_eq!(file_snapshot(&victim), before);
}
