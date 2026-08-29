use std::collections::BTreeMap;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir()
                .join(format!("cott-cli-tests-{}-{number}", std::process::id()));
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

fn file_snapshot(root: &Path) -> BTreeMap<PathBuf, Vec<u8>> {
    fn visit(root: &Path, current: &Path, files: &mut BTreeMap<PathBuf, Vec<u8>>) {
        for entry in fs::read_dir(current).expect("snapshot directory should be readable") {
            let entry = entry.expect("snapshot entry should be readable");
            let path = entry.path();
            let relative = path
                .strip_prefix(root)
                .expect("snapshot path should be rooted")
                .to_path_buf();
            if entry
                .file_type()
                .expect("snapshot entry type should be readable")
                .is_dir()
            {
                visit(root, &path, files);
            } else {
                files.insert(
                    relative,
                    fs::read(&path).expect("snapshot file should be readable"),
                );
            }
        }
    }

    let mut files = BTreeMap::new();
    visit(root, root, &mut files);
    files
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
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        for executable in [python, checker] {
            fs::set_permissions(executable, fs::Permissions::from_mode(0o755))
                .expect("make fake Python tool executable");
        }
    }
}

const NORMATIVE_MANIFEST: &str = r#"[project]
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

[target.python.implementations]
"app.run" = "cott_bindings.app.run:run"
"#;
const SOURCE: &str = "module app\n\nfn run() -> I32\n";
const BINDING: &str = "from cott_runtime import I32\n\n\ndef run() -> I32:\n    return 7\n";
const TARGET_METADATA: &str = "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14,<3.15\"\ndependencies = []\n";

fn write_target_metadata(root: &Path) {
    fs::create_dir_all(root.join("python")).expect("Python source directory");
    fs::write(root.join("python/pyproject.toml"), TARGET_METADATA)
        .expect("target project metadata should be writable");
}

fn project() -> TempDir {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), NORMATIVE_MANIFEST)
        .expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(temp.path.join("src/app.cott"), SOURCE).expect("source should be writable");
    write_target_metadata(&temp.path);
    fs::create_dir_all(temp.path.join("python/cott_bindings/app"))
        .expect("implementation directory should be writable");
    fs::write(temp.path.join("python/cott_bindings/app/run.py"), BINDING)
        .expect("binding should be writable");
    install_fake_python_tools(&temp.path);
    temp
}

fn make_unresolved(project: &TempDir) {
    fs::remove_file(project.path.join("python/cott_bindings/app/run.py"))
        .expect("binding should be removable");
    let manifest = fs::read_to_string(project.path.join("cott.toml")).expect("manifest");
    let manifest = manifest
        .split_once("\n[target.python.implementations]\n")
        .map_or(manifest.as_str(), |(base, _)| base);
    fs::write(project.path.join("cott.toml"), format!("{manifest}\n"))
        .expect("unresolved manifest should be writable");
}

fn method_project() -> TempDir {
    let temp = TempDir::new();
    let manifest = NORMATIVE_MANIFEST
        .split_once("\n[target.python.implementations]\n")
        .expect("normative manifest has implementations")
        .0;
    fs::write(temp.path.join("cott.toml"), format!("{manifest}\n"))
        .expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src/api")).expect("source directory should be writable");
    fs::write(
        temp.path.join("src/api/service.cott"),
        "module api.service\n\ntrait Reader:\n    fn read(self, amount: I32) -> I32\n\nimpl ReaderState for Reader:\n    state:\n        count: I32 = 0\n    init(count: I32):\n        requires count > 0\n        ensures self.count == count\n    fn read(self, amount: I32) -> I32:\n        ensures result == amount\n",
    )
    .expect("method source should be writable");
    write_target_metadata(&temp.path);
    install_fake_python_tools(&temp.path);
    temp
}

fn normative_project() -> TempDir {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), NORMATIVE_MANIFEST)
        .expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(temp.path.join("src/app.cott"), SOURCE).expect("source should be writable");
    write_target_metadata(&temp.path);
    temp
}

fn cott(root: &Path, arguments: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(arguments)
        .arg("--project")
        .arg(root)
        .output()
        .expect("cott should run")
}

#[test]
fn global_cli_flags_have_a_stable_process_contract() {
    let expected_version = format!("cott {}\n", env!("CARGO_PKG_VERSION"));
    for argument in ["--version", "-V"] {
        let output = Command::new(env!("CARGO_BIN_EXE_cott"))
            .arg(argument)
            .output()
            .expect("cott should run");
        assert_eq!(output.status.code(), Some(0), "{argument} should succeed");
        assert_eq!(output.stdout, expected_version.as_bytes());
        assert!(
            output.stderr.is_empty(),
            "{argument} should not write stderr"
        );
    }

    let help = Command::new(env!("CARGO_BIN_EXE_cott"))
        .arg("--help")
        .output()
        .expect("cott should run");
    assert_eq!(help.status.code(), Some(0));
    let help = String::from_utf8(help.stdout).expect("help should be UTF-8");
    assert!(help.contains("Cott"));
    assert!(help.contains("cott --version"));

    let invalid = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(["--version", "extra"])
        .output()
        .expect("cott should run");
    assert_eq!(invalid.status.code(), Some(2));
    assert!(String::from_utf8_lossy(&invalid.stderr).contains("Usage:"));
}

fn recompute_generation_id(snapshot: &mut serde_json::Value) {
    let mut current = snapshot.clone();
    let current = current
        .as_object_mut()
        .expect("generation snapshot is an object");
    for key in [
        "generation_id",
        "verified",
        "verification",
        "semantic_coverage",
        "agent_runs",
    ] {
        current.remove(key);
    }
    let identity = serde_json::json!({
        "domain": "cott.generation.v7",
        "schema_version": 7,
        "current": current,
    });
    let mut bytes = serde_json::to_vec(&identity).expect("canonical generation identity");
    bytes.push(b'\n');
    snapshot["generation_id"] =
        serde_json::json!(format!("sha256:{}", cott::hash::sha256_hex(&bytes)));
}
#[test]
fn source_commands_accept_the_normative_manifest_without_entry() {
    let project = normative_project();

    for arguments in [
        &["check", "--format", "json"][..],
        &["fmt"][..],
        &["emit", "ir"][..],
    ] {
        let output = cott(&project.path, arguments);
        assert!(
            output.status.success(),
            "{arguments:?}: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
    assert!(project.path.join("generated/ir/app.json").is_file());
}

fn retarget_generation_to_host_python(root: &Path) {
    let script = r#"import hashlib,json,pathlib,platform,sys,sysconfig
p=pathlib.Path("generated/generation.json")
r=json.loads(p.read_bytes())
e=pathlib.Path(sys.executable).resolve()
r["current"]["tools"]["python"]={"cache_tag":sys.implementation.cache_tag,"content_hash":"sha256:"+hashlib.sha256(e.read_bytes()).hexdigest(),"executable":str(e),"implementation":sys.implementation.name,"machine":platform.machine(),"os":sys.platform,"platform":sysconfig.get_platform(),"version":platform.python_version()}
i=dict(r["current"])
for k in ("generation_id","verified","verification","semantic_coverage","agent_runs"): i.pop(k,None)
i={"domain":"cott.generation.v7","schema_version":7,"current":i}
r["current"]["generation_id"]="sha256:"+hashlib.sha256(json.dumps(i,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode()+b"\n").hexdigest()
p.write_text(json.dumps(r,ensure_ascii=False,separators=(",",":"),sort_keys=True)+"\n")
"#;
    let output = Command::new("python3")
        .args(["-c", script])
        .current_dir(root)
        .output()
        .expect("host Python should retarget test provenance");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}

fn retarget_last_verified_python_symbol(root: &Path, python_symbol: &str) {
    let script = r#"import hashlib,json,pathlib,sys
p=pathlib.Path("generated/generation.json")
r=json.loads(p.read_bytes())
s=r["last_verified"]
s["implementations"][0]["python_symbol"]=sys.argv[1]
i=dict(s)
for k in ("generation_id","verified","verification","semantic_coverage","agent_runs"): i.pop(k,None)
i={"domain":"cott.generation.v7","schema_version":7,"current":i}
s["generation_id"]="sha256:"+hashlib.sha256(json.dumps(i,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode()+b"\n").hexdigest()
p.write_text(json.dumps(r,ensure_ascii=False,separators=(",",":"),sort_keys=True)+"\n")
"#;
    let output = Command::new("python3")
        .args(["-c", script, python_symbol])
        .current_dir(root)
        .output()
        .expect("host Python should retarget verified implementation provenance");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}

fn remove_free_function_callable_metadata(root: &Path) {
    let script = r#"import hashlib,json,pathlib
p=pathlib.Path("generated/generation.json")
r=json.loads(p.read_bytes())
i=r["current"]["implementations"][0]
for k in ("kind","callable_kind","concrete","method"): i.pop(k)
c=dict(r["current"])
for k in ("generation_id","verified","verification","semantic_coverage","agent_runs"): c.pop(k,None)
i={"domain":"cott.generation.v7","schema_version":7,"current":c}
r["current"]["generation_id"]="sha256:"+hashlib.sha256(json.dumps(i,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode()+b"\n").hexdigest()
p.write_text(json.dumps(r,ensure_ascii=False,separators=(",",":"),sort_keys=True)+"\n")
"#;
    let output = Command::new("python3")
        .args(["-c", script])
        .current_dir(root)
        .output()
        .expect("host Python should write incomplete generation provenance");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}

fn replace_generation_implementation_kind(path: &Path, kind: &str) -> (String, String) {
    let mut record: serde_json::Value =
        serde_json::from_slice(&fs::read(path).expect("generation record")).expect("valid JSON");
    let snapshot = record
        .get_mut("current")
        .expect("generation record has current snapshot");
    let before = snapshot["generation_id"]
        .as_str()
        .expect("generation snapshot identity")
        .to_owned();
    snapshot["implementations"][0]["kind"] = serde_json::json!(kind);
    snapshot["implementations"][0]["callable_kind"] =
        serde_json::json!(if kind.starts_with("async_") {
            "async"
        } else {
            "sync"
        });
    recompute_generation_id(snapshot);
    let after = snapshot["generation_id"]
        .as_str()
        .expect("updated generation snapshot identity")
        .to_owned();
    fs::write(
        path,
        serde_json::to_vec(&record).expect("generation record serialization"),
    )
    .expect("generation record should be writable");
    (before, after)
}

#[test]
fn emits_complete_tree_and_verifies_exact_bytes() {
    let project = project();
    let emitted = cott(&project.path, &["emit", "python"]);

    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    assert_eq!(
        String::from_utf8(emitted.stdout).expect("stdout must be UTF-8"),
        "generated/python\n"
    );
    for path in [
        "generated/python/app.py",
        "generated/python/app_types.py",
        "generated/python/cott_runtime/__init__.py",
        "generated/python/_cott_impl/app/run.py",
        "generated/stubs/app.pyi",
        "generated/ir/app.json",
        "generated/generation.json",
    ] {
        assert!(
            project.path.join(path).is_file(),
            "missing generated artifact {path}"
        );
    }
    assert!(!project.path.join("generated/python/__main__.py").exists());

    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
    assert_eq!(
        String::from_utf8(verified.stdout).expect("stdout must be UTF-8"),
        "verified generated/python\n"
    );
    let record: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("verified generation record"),
    )
    .expect("verified generation record is JSON");
    assert_eq!(
        record["current"]["verification"]["static"]["runtime_signatures"]["app.run"]["callable_kind"],
        "function"
    );

    fs::write(project.path.join("generated/python/app.py"), "tampered\n")
        .expect("generated artifact should be writable");
    let rejected = cott(&project.path, &["verify"]);
    assert_eq!(rejected.status.code(), Some(4));
    assert!(String::from_utf8_lossy(&rejected.stderr).contains("managed artifact differs"));
}

#[test]
fn verification_limits_reach_evidence_and_generated_strategies() {
    let project = project();
    let manifest = fs::read_to_string(project.path.join("cott.toml")).expect("manifest");
    fs::write(
        project.path.join("cott.toml"),
        format!(
            "{manifest}\n[verification]\nproof_node_limit = 17\nproof_branch_limit = 19\ncandidate_limit = 23\nlifecycle_limit = 29\n"
        ),
    )
    .expect("verification overrides should be writable");

    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let strategy: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/tests/generated/app/run.json"))
            .expect("generated contract strategy"),
    )
    .expect("generated contract strategy is JSON");
    assert_eq!(strategy["schema_version"], 5);
    assert_eq!(strategy["proof_node_limit"], 17);
    assert_eq!(strategy["proof_branch_limit"], 19);
    assert_eq!(strategy["candidate_limit"], 23);
    assert_eq!(strategy["lifecycle_limit"], 29);
    assert_eq!(strategy["node_limit"], 64);
    assert_eq!(strategy["container_length_limit"], 3);
    assert_eq!(strategy["json_depth_limit"], 4);

    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
    let record: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("verified generation record"),
    )
    .expect("verified generation record is JSON");
    assert_eq!(
        record["current"]["verification"]["limits"],
        serde_json::json!({
            "proof_node_limit": 17,
            "proof_branch_limit": 19,
            "candidate_limit": 23,
            "lifecycle_limit": 29,
        })
    );
}

#[test]
fn invalid_verification_limits_preserve_managed_tree() {
    let absent = project();
    let manifest = fs::read_to_string(absent.path.join("cott.toml")).expect("manifest");
    fs::write(
        absent.path.join("cott.toml"),
        format!("{manifest}\n[verification]\nproof_node_limit = 0\n"),
    )
    .expect("invalid manifest should be writable");
    let rejected = cott(&absent.path, &["emit", "python"]);
    assert!(!rejected.status.success());
    assert!(!absent.path.join("generated").exists());

    let project = project();
    assert!(cott(&project.path, &["emit", "python"]).status.success());
    let before = file_snapshot(&project.path.join("generated"));
    let manifest = fs::read_to_string(project.path.join("cott.toml")).expect("manifest");
    fs::write(
        project.path.join("cott.toml"),
        format!("{manifest}\n[verification]\ncandidate_limit = 1025\n"),
    )
    .expect("invalid manifest should be writable");
    let rejected = cott(&project.path, &["emit", "python"]);
    assert!(!rejected.status.success());
    assert_eq!(file_snapshot(&project.path.join("generated")), before);
}

#[test]
fn verify_records_no_baseline_implementation_comparison() {
    let project = project();
    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );

    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
    let record: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("verified generation record"),
    )
    .expect("verified generation record is JSON");
    let verification = &record["current"]["verification"];
    for key in [
        "contract_proofs",
        "contract_tests",
        "runtime_capability",
        "static",
        "implementation_comparison",
    ] {
        assert!(
            verification.get(key).is_some(),
            "missing verification evidence {key}"
        );
    }
    assert_eq!(
        verification["contract_proofs"]["algorithm"],
        "bounded-dnf-difference-constraints"
    );
    assert_eq!(
        verification, &record["last_verified"]["verification"],
        "verification evidence must be copied verbatim to last_verified"
    );
    assert_eq!(
        record["current"]["verification"]["implementation_comparison"],
        serde_json::json!({
            "baseline_generation_id": null,
            "status": "no_baseline",
            "entries": []
        })
    );
    assert_eq!(record["current"], record["last_verified"]);
    let compared = cott(&project.path, &["verify"]);

    assert!(
        compared.status.success(),
        "{}",
        String::from_utf8_lossy(&compared.stderr)
    );
    let stable = fs::read(project.path.join("generated/generation.json"))
        .expect("compared generation record");
    let repeated = cott(&project.path, &["verify"]);
    assert!(
        repeated.status.success(),
        "{}",
        String::from_utf8_lossy(&repeated.stderr)
    );
    assert_eq!(
        fs::read(project.path.join("generated/generation.json"))
            .expect("repeated generation record"),
        stable
    );
}
#[test]
fn verify_rejects_disproved_static_requires_without_mutating_generation_record() {
    let project = project();
    fs::write(
        project.path.join("src/app.cott"),
        "module app\n\nfn run(value: I8) -> I32:\n    requires value > 127\n",
    )
    .expect("source should be writable");
    fs::write(
        project.path.join("python/cott_bindings/app/run.py"),
        "from cott_runtime import I8, I32\n\n\ndef run(value: I8) -> I32:\n    return 7\n",
    )
    .expect("binding should be writable");
    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let generation = project.path.join("generated/generation.json");
    let before = fs::read(&generation).expect("unverified generation record");
    let rejected = cott(&project.path, &["verify"]);
    assert_eq!(rejected.status.code(), Some(3));
    assert!(
        String::from_utf8_lossy(&rejected.stderr).contains("static contract proof disproved"),
        "{}",
        String::from_utf8_lossy(&rejected.stderr)
    );
    assert_eq!(fs::read(&generation).expect("generation record"), before);
}

#[test]
fn verify_records_unsupported_static_requires_as_nonfatal_unknown() {
    let project = project();
    fs::write(
        project.path.join("src/app.cott"),
        "module app\n\nfn run(value: I8) -> I32:\n    requires value * value > 0\n",
    )
    .expect("source should be writable");
    fs::write(
        project.path.join("python/cott_bindings/app/run.py"),
        "from cott_runtime import I8, I32\n\n\ndef run(value: I8) -> I32:\n    return 7\n",
    )
    .expect("binding should be writable");
    assert!(cott(&project.path, &["emit", "python"]).status.success());
    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
    let record: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json")).expect("generation record"),
    )
    .expect("generation record is JSON");
    assert_eq!(
        record["current"]["verification"]["contract_proofs"]["contracts"][0]["status"],
        "unknown"
    );
    assert_eq!(
        record["current"]["verification"],
        record["last_verified"]["verification"]
    );
}

#[test]
fn emit_refreshes_stale_compiler_and_runtime_tool_versions() {
    let project = project();
    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
    let path = project.path.join("generated/generation.json");
    let mut record: serde_json::Value =
        serde_json::from_slice(&fs::read(&path).expect("verified generation record"))
            .expect("verified generation record is JSON");
    record["current"]["tools"]["compiler"] = serde_json::json!({
        "content_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "executable": "/old/cott",
        "version": "0.0.0"
    });
    record["current"]["tools"]["runtime"]["abi"] = serde_json::json!("0");
    record["current"]["tools"]["runtime"]["version"] = serde_json::json!("0.0.0");
    recompute_generation_id(&mut record["current"]);
    fs::write(
        &path,
        serde_json::to_vec(&record).expect("stale generation record serialization"),
    )
    .expect("stale generation record should be writable");

    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let regenerated: serde_json::Value =
        serde_json::from_slice(&fs::read(&path).expect("regenerated record"))
            .expect("regenerated record is JSON");
    assert_eq!(
        regenerated["current"]["tools"]["compiler"]["version"],
        env!("CARGO_PKG_VERSION")
    );
    assert_eq!(regenerated["current"]["tools"]["runtime"]["abi"], "7");
    assert_eq!(
        regenerated["current"]["tools"]["runtime"]["version"],
        env!("CARGO_PKG_VERSION")
    );
    let executable =
        fs::canonicalize(Path::new(env!("CARGO_BIN_EXE_cott"))).expect("canonical Cott executable");
    assert_eq!(
        regenerated["current"]["tools"]["compiler"]["executable"].as_str(),
        Some(executable.to_string_lossy().as_ref())
    );
    assert_eq!(
        regenerated["current"]["tools"]["compiler"]["content_hash"],
        format!(
            "sha256:{}",
            cott::hash::sha256_hex(&fs::read(&executable).expect("test executable"))
        )
    );

    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
    let diff = cott(&project.path, &["diff"]);
    assert!(
        diff.status.success(),
        "{}",
        String::from_utf8_lossy(&diff.stderr)
    );
    assert_eq!(
        String::from_utf8(diff.stdout).expect("diff output is UTF-8"),
        "NO CHANGE\n"
    );
}

#[test]
fn emit_rejects_stale_generation_compatibility_without_mutating_managed_tree() {
    let project = project();
    assert!(cott(&project.path, &["emit", "python"]).status.success());
    let path = project.path.join("generated/generation.json");
    let mut record: serde_json::Value =
        serde_json::from_slice(&fs::read(&path).expect("generation record"))
            .expect("generation record is JSON");
    record["current"]["compatibility"] = serde_json::json!({
        "generation_schema": 5,
        "canonical_ir_schema": 6,
        "runtime_abi": 5
    });
    recompute_generation_id(&mut record["current"]);
    fs::write(
        &path,
        serde_json::to_vec(&record).expect("stale generation record serialization"),
    )
    .expect("stale generation record should be writable");
    let before = file_snapshot(&project.path.join("generated"));

    let rejected = cott(&project.path, &["emit", "python"]);

    assert!(!rejected.status.success());
    assert!(
        String::from_utf8_lossy(&rejected.stderr).contains("invalid generation provenance"),
        "{}",
        String::from_utf8_lossy(&rejected.stderr)
    );
    assert_eq!(file_snapshot(&project.path.join("generated")), before);
}

#[test]
fn verify_compares_implementation_identity_without_importing_the_baseline() {
    let project = project();
    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let initial_verification = cott(&project.path, &["verify"]);
    assert!(
        initial_verification.status.success(),
        "{}",
        String::from_utf8_lossy(&initial_verification.stderr)
    );
    fs::copy(
        project.path.join("generated/generation.json"),
        project.path.join("baseline.json"),
    )
    .expect("verified generation record should be copyable");
    retarget_last_verified_python_symbol(&project.path, "effectful_baseline:run");
    let compared_generation_id: serde_json::Value = serde_json::from_slice::<serde_json::Value>(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("retargeted generation record"),
    )
    .expect("retargeted generation record is JSON")["last_verified"]["generation_id"]
        .clone();
    fs::write(
        project.path.join("python/cott_bindings/app/run.py"),
        "from cott_runtime import I32\n\n\ndef run() -> I32:\n    return 8\n",
    )
    .expect("updated implementation should be writable");

    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let diff = cott(&project.path, &["diff", "--baseline", "baseline.json"]);
    assert!(
        diff.status.success(),
        "{}",
        String::from_utf8_lossy(&diff.stderr)
    );
    assert!(
        String::from_utf8_lossy(&diff.stdout)
            .contains("- app.run implementation changed: content_hash"),
        "{}",
        String::from_utf8_lossy(&diff.stdout)
    );
    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
    let record: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("verified generation record"),
    )
    .expect("verified generation record is JSON");
    let comparison = &record["current"]["verification"]["implementation_comparison"];
    assert_eq!(comparison["status"], "compared");
    assert_eq!(comparison["baseline_generation_id"], compared_generation_id);
    let entries = comparison["entries"]
        .as_array()
        .expect("implementation comparison entries");
    assert_eq!(entries.len(), 1);
    assert_eq!(entries[0]["cott_symbol"], "app.run");
    assert_eq!(entries[0]["status"], "changed");
    let changed_fields = entries[0]["changed_fields"]
        .as_object()
        .expect("changed implementation fields");
    assert_eq!(
        changed_fields
            .keys()
            .map(String::as_str)
            .collect::<Vec<_>>(),
        ["content_hash", "python_symbol"]
    );
    assert_ne!(
        changed_fields["content_hash"]["before"],
        changed_fields["content_hash"]["after"]
    );
    assert_eq!(
        changed_fields["python_symbol"]["before"],
        "effectful_baseline:run"
    );
    assert_eq!(
        changed_fields["python_symbol"]["after"],
        "_cott_impl.app.run:run"
    );
    assert_eq!(record["current"], record["last_verified"]);
}

#[test]
fn diff_marks_callable_kind_only_changes_as_contract_breaking() {
    let project = project();
    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let baseline = project.path.join("callable-kind-baseline.json");
    fs::copy(project.path.join("generated/generation.json"), &baseline)
        .expect("generation record should be copyable");
    let (before, after) = replace_generation_implementation_kind(&baseline, "async_function");
    assert_ne!(
        before, after,
        "callable kind participates in generation identity"
    );

    let diff = cott(
        &project.path,
        &["diff", "--baseline", "callable-kind-baseline.json"],
    );

    assert!(
        diff.status.success(),
        "{}",
        String::from_utf8_lossy(&diff.stderr)
    );
    let stdout = String::from_utf8_lossy(&diff.stdout);
    assert!(stdout.contains("CONTRACT BREAKING:"), "{stdout}");
    assert!(
        stdout.contains("- app.run implementation changed: callable_kind, kind"),
        "{stdout}"
    );
}

#[test]
fn async_callable_kind_changes_generation_identity_and_breaks_contracts() {
    let project = project();
    let initial = cott(&project.path, &["emit", "python"]);
    assert!(
        initial.status.success(),
        "{}",
        String::from_utf8_lossy(&initial.stderr)
    );
    let baseline = project.path.join("sync-baseline.json");
    fs::copy(project.path.join("generated/generation.json"), &baseline)
        .expect("sync generation record should be copyable");
    let sync_record: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json")).expect("sync generation record"),
    )
    .expect("sync generation record is JSON");
    fs::write(
        project.path.join("src/app.cott"),
        "module app\n\nasync fn run() -> I32\n",
    )
    .expect("async source should be writable");
    fs::write(
        project.path.join("python/cott_bindings/app/run.py"),
        "from cott_runtime import I32\n\n\nasync def run() -> I32:\n    return 7\n",
    )
    .expect("async binding should be writable");

    let emitted = cott(&project.path, &["emit", "python"]);

    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let async_record: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json")).expect("async generation record"),
    )
    .expect("async generation record is JSON");
    assert_eq!(
        sync_record["current"]["implementations"][0]["kind"],
        "function"
    );
    assert_eq!(
        sync_record["current"]["implementations"][0]["callable_kind"],
        "sync"
    );
    assert_eq!(
        async_record["current"]["implementations"][0]["kind"],
        "async_function"
    );
    assert_eq!(
        async_record["current"]["implementations"][0]["callable_kind"],
        "async"
    );
    assert_ne!(
        sync_record["current"]["generation_id"],
        async_record["current"]["generation_id"]
    );

    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
    let verified_record: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("verified async generation record"),
    )
    .expect("verified async generation record is JSON");
    assert_eq!(
        verified_record["current"]["implementations"][0]["kind"],
        "async_function"
    );
    assert_eq!(
        verified_record["current"]["implementations"][0]["callable_kind"],
        "async"
    );
    assert_eq!(
        verified_record["current"]["verification"]["static"]["runtime_signatures"]["app.run"]["callable_kind"],
        "async_function"
    );

    let diff = cott(&project.path, &["diff", "--baseline", "sync-baseline.json"]);
    assert!(
        diff.status.success(),
        "{}",
        String::from_utf8_lossy(&diff.stderr)
    );
    let stdout = String::from_utf8_lossy(&diff.stdout);
    assert!(stdout.contains("CONTRACT BREAKING:"), "{stdout}");
    assert!(
        stdout.contains("- app.run implementation changed: callable_kind, content_hash, kind"),
        "{stdout}"
    );
}

#[test]
fn emit_rejects_async_callable_with_sync_binding() {
    let project = project();
    fs::write(
        project.path.join("src/app.cott"),
        "module app\n\nasync fn run() -> I32\n",
    )
    .expect("async source should be writable");

    let emitted = cott(&project.path, &["emit", "python"]);

    assert!(
        !emitted.status.success(),
        "async canonical callable accepted a sync binding: {}",
        String::from_utf8_lossy(&emitted.stderr)
    );
}

#[test]
fn verify_rejects_malformed_provenance_before_implementation_comparison() {
    let project = project();
    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    fs::write(project.path.join("generated/generation.json"), "{}\n")
        .expect("generation record should be writable");

    let rejected = cott(&project.path, &["verify"]);

    assert!(!rejected.status.success());
    assert!(
        String::from_utf8_lossy(&rejected.stderr).contains("invalid generation provenance"),
        "{}",
        String::from_utf8_lossy(&rejected.stderr)
    );
}

#[test]
fn verifier_uses_strict_basedpyright_with_compiler_owned_exceptions() {
    let project = project();
    let checker = project.path.join(".venv/bin/basedpyright");
    fs::write(
        &checker,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then
  printf 'basedpyright 1.39.9\nbased on pyright 1.1.411\n'
  exit 0
fi
config=$(cat "$2")
for setting in '"typeCheckingMode":"strict"' '"reportInvalidTypeVarUse":"none"' '"reportUnknownMemberType":"none"' '"reportUnusedFunction":"none"' '"reportPrivateUsage":"none"'; do
  case "$config" in *"$setting"*) ;; *) printf 'missing BasedPyright setting %s\n' "$setting" >&2; exit 1 ;; esac
done
remaining=$(printf '%s' "$config" | sed 's/"reportInvalidTypeVarUse":"none"//g; s/"reportUnknownMemberType":"none"//g; s/"reportUnusedFunction":"none"//g; s/"reportPrivateUsage":"none"//g')
case "$remaining" in
  *'"report'*':"none"'*)
    printf 'strict BasedPyright diagnostic disabled\n' >&2
    exit 1
    ;;
esac
"#,
    )
    .expect("asserting fake BasedPyright");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&checker, fs::Permissions::from_mode(0o755))
            .expect("make asserting fake BasedPyright executable");
    }

    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
}

#[test]
fn emit_rejects_incomplete_schema3_free_function_provenance() {
    let project = project();
    let initial = cott(&project.path, &["emit", "python"]);
    assert!(
        initial.status.success(),
        "{}",
        String::from_utf8_lossy(&initial.stderr)
    );
    remove_free_function_callable_metadata(&project.path);

    let legacy: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("incomplete generation record"),
    )
    .expect("incomplete generation record is JSON");
    let implementation = &legacy["current"]["implementations"][0];
    for field in ["kind", "callable_kind", "concrete", "method"] {
        assert!(implementation.get(field).is_none(), "missing `{field}`");
    }

    let emitted = cott(&project.path, &["emit", "python"]);
    assert_eq!(emitted.status.code(), Some(4));
    let stderr = String::from_utf8_lossy(&emitted.stderr);
    assert!(stderr.contains("invalid generation provenance"), "{stderr}");
    assert!(
        stderr.contains("\"kind\" is a required property"),
        "{stderr}"
    );
}

#[test]
fn syntax_errors_leave_existing_artifacts_untouched() {
    let project = project();
    fs::create_dir_all(project.path.join("generated/python"))
        .expect("existing artifact directory should be writable");
    let sentinel = project.path.join("generated/sentinel.txt");
    fs::write(&sentinel, "preserve me\n").expect("sentinel should be writable");
    fs::write(project.path.join("src/app.cott"), "module app\n\nfn run(\n")
        .expect("invalid source should be writable");

    let result = cott(&project.path, &["emit", "python"]);

    assert_eq!(result.status.code(), Some(3));
    assert!(String::from_utf8_lossy(&result.stderr).contains("app.cott"));
    assert_eq!(
        fs::read_to_string(sentinel).expect("sentinel should remain"),
        "preserve me\n"
    );
}

#[test]
fn permits_exact_generated_type_imports_in_bindings() {
    let project = project();
    fs::write(
        project.path.join("src/app.cott"),
        "module app\n\nstruct Card:\n    title: Str\n\nfn run() -> Card\n",
    )
    .expect("typed source should be writable");
    fs::write(
        project.path.join("python/cott_bindings/app/run.py"),
        "from app_types import Card\n\n\ndef run() -> Card:\n    return Card(title=\"typed\")\n",
    )
    .expect("typed binding should be writable");

    let emitted = cott(&project.path, &["emit", "python"]);

    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    assert!(project.path.join("generated/python/app_types.py").is_file());
}

#[test]
fn generate_requires_an_agent_only_for_unresolved_callables() {
    let project = project();
    make_unresolved(&project);

    let output = cott(&project.path, &["generate", "--target", "python"]);

    assert_eq!(output.status.code(), Some(2));
    assert!(
        String::from_utf8_lossy(&output.stderr).contains("requires `--agent codex|claude|omp`")
    );
}

#[test]
fn generate_promotes_a_sandboxed_omp_function_candidate_with_artifacts() {
    let project = project();
    make_unresolved(&project);
    fs::write(
        project.path.join("cott.toml"),
        format!(
            "{}\n[target.python.external_types]\n\"app.Widget\" = \"io:StringIO\"\n",
            fs::read_to_string(project.path.join("cott.toml")).expect("manifest")
        ),
    )
    .expect("manifest should be writable");
    fs::write(
        project.path.join("src/app.cott"),
        "module app\n\nexternal type Widget\n\nfn run() -> I32\n",
    )
    .expect("source should be writable");
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(
        &omp,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
message=
for message; do :; done
case "$message" in
  @*) prompt=$(cat "${message#@}") || exit 64 ;;
  *) printf '%s\n' 'missing @prompt-file argument' >&2; exit 64 ;;
esac
case "$prompt" in
  *'Symbol: app.run'*) ;;
  *) printf '%s\n' 'missing prompt fragment: Symbol: app.run' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'PYTHON EXTERNAL TYPE PROJECTIONS'*) ;;
  *) printf '%s\n' 'missing prompt fragment: PYTHON EXTERNAL TYPE PROJECTIONS' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'app.Widget = io:StringIO'*) ;;
  *) printf '%s\n' 'missing prompt fragment: app.Widget = io:StringIO' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'For other modules import public generated symbols only through `from app import name` and generated value types only through `from app_types import Type`.'*) ;;
  *) printf '%s\n' 'missing prompt fragment: module facade/type import guidance' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars.'*) ;;
  *) printf '%s\n' 'missing prompt fragment: private implementation policy' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'Each constant MUST have a single-leading-underscore name that is neither dunder nor reserved `_cott_`'*) ;;
  *) printf '%s\n' 'missing prompt fragment: private Final constant policy' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'Use contract containers directly: CottList(values=xs), CottSet(values=xs), FrozenMap(values={}), CottArray(values=xs), and CottBuffer(data=xs); Cott Tuple uses native `tuple[...]` annotations and `(a, b)` values.'*) ;;
  *) printf '%s\n' 'missing prompt fragment: contract containers' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'For Result returns import top-level Ok and Err from cott_runtime and return Ok(value=...) or Err(error=...); never use Result.Ok/Result.Err'*) ;;
  *) printf '%s\n' 'missing prompt fragment: top-level result constructors' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'`Unit` is the annotation and `UNIT` is its only value; return `Ok(value=UNIT)` for Result[Unit, E].'*) ;;
  *) printf '%s\n' 'missing prompt fragment: Unit singleton ABI' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'For Option annotations use the top-level `Some(value=...)` and `Nothing()` variants, never `Option.Some` or `Option.Nothing`; narrow an Option with structural `match` before reading a Some payload.'*) ;;
  *) printf '%s\n' 'missing prompt fragment: Option variant ABI' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'`typing.cast` MAY be used only from a concrete external SDK return to its declared external projection when upstream stubs are incompatible; never cast Cott-owned values.'*) ;;
  *) printf '%s\n' 'missing prompt fragment: external projection cast policy' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'Generated payload enum aliases have no members: import and construct top-level `<Enum>_<Variant>` from the exact `app_types` module, never `<Enum>.<Variant>`.'*) ;;
  *) printf '%s\n' 'missing prompt fragment: top-level payload enum variants' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'"external_types"'*) printf '%s\n' 'unexpected prompt fragment: "external_types"' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'EXISTING IMPLEMENTATION'*'VALIDATION FAILURE'*'missing_distribution'*'Fix the existing implementation and change nothing outside the target file.'*)
    printf 'from cott_runtime import I32\n\n\ndef run() -> I32:\n    return 7\n' > implementation.py
    ;;
  *'EXISTING IMPLEMENTATION'*)
    printf '%s\n' 'retry prompt omitted validation feedback' >&2
    exit 64
    ;;
  *)
    printf 'import missing_distribution\nfrom cott_runtime import I32\n\n\ndef run() -> I32:\n    return 7\n' > implementation.py
    ;;
esac
"#,
    )
    .expect("write fake OMP");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&omp, fs::Permissions::from_mode(0o755))
            .expect("make fake OMP executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "--agent",
            "omp",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        fs::read_to_string(project.path.join("python/_cott_impl/app/run.py"))
            .expect("durable candidate"),
        "from cott_runtime import I32\n\n\ndef run() -> I32:\n    return 7\n"
    );
    assert!(project.path.join("generated/python/app.py").is_file());
}

#[test]
fn generate_promotes_a_direct_claude_function_candidate_with_provenance() {
    let project = project();
    make_unresolved(&project);
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let claude = tools.join("claude");
    fs::write(
        &claude,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then
  [ "$#" -eq 1 ] || { printf '%s\n' 'unexpected Claude version argv' >&2; exit 64; }
  [ "${ANTHROPIC_API_KEY+x}" != x ] || { printf '%s\n' 'forwarded API key during version probe' >&2; exit 64; }
  printf '%s\n' '2.1.89'
  exit 0
fi
expected='--bare --print --input-format text --output-format json --permission-mode dontAsk --tools Read,Write --allowedTools Read,Write --disallowedTools Bash,Edit,Glob,Grep,WebFetch,WebSearch,Task,mcp__* --no-session-persistence'
[ "$*" = "$expected" ] || { printf '%s\n' "unexpected Claude argv: $*" >&2; exit 64; }
[ "${ANTHROPIC_API_KEY-}" = 'test-api-key' ] || { printf '%s\n' 'missing API key' >&2; exit 64; }
[ "${ANTHROPIC_AUTH_TOKEN+x}" = x ] && { printf '%s\n' 'forwarded auth token' >&2; exit 64; }
[ "${ANTHROPIC_BASE_URL+x}" = x ] && { printf '%s\n' 'forwarded base URL' >&2; exit 64; }
[ "${CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC-}" = 1 ] || exit 64
[ "${DISABLE_TELEMETRY-}" = 1 ] || exit 64
[ "${DISABLE_ERROR_REPORTING-}" = 1 ] || exit 64
prompt=$(cat) || exit 64
case "$prompt" in
  *'Symbol: app.run'*) ;;
  *) printf '%s\n' 'missing stdin prompt' >&2; exit 64 ;;
esac
printf '%s' 'from cott_runtime import I32


def run() -> I32:
    return 7
' > implementation.py
printf '%s\n' '{"type":"result","subtype":"success","is_error":false,"result":"done"}'
"#,
    )
    .expect("write fake Claude");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&claude, fs::Permissions::from_mode(0o755))
            .expect("make fake Claude executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .env_clear()
        .args([
            "generate",
            "--agent",
            "claude",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", path)
        .env("ANTHROPIC_API_KEY", "test-api-key")
        .env("ANTHROPIC_AUTH_TOKEN", "must-not-forward")
        .env("ANTHROPIC_BASE_URL", "https://must-not-forward.example")
        .output()
        .expect("cott should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        fs::read_to_string(project.path.join("python/_cott_impl/app/run.py"))
            .expect("durable candidate"),
        "from cott_runtime import I32\n\n\ndef run() -> I32:\n    return 7\n"
    );
    let record: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json")).expect("generation record"),
    )
    .expect("generation record is JSON");
    let run = &record["current"]["agent_runs"][0];
    assert_eq!(run["symbol"], "app.run");
    assert_eq!(run["adapter"], "claude");
    assert_eq!(run["adapter_version"], "2.1.89");
    assert_eq!(
        run["argv_template"],
        serde_json::json!([
            "--bare",
            "--print",
            "--input-format",
            "text",
            "--output-format",
            "json",
            "--permission-mode",
            "dontAsk",
            "--tools",
            "Read,Write",
            "--allowedTools",
            "Read,Write",
            "--disallowedTools",
            "Bash,Edit,Glob,Grep,WebFetch,WebSearch,Task,mcp__*",
            "--no-session-persistence"
        ])
    );
    assert_eq!(
        run["environment_names"],
        serde_json::json!([
            "ANTHROPIC_API_KEY",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC",
            "DISABLE_ERROR_REPORTING",
            "DISABLE_TELEMETRY",
            "HOME",
            "PATH",
            "PYTHONDONTWRITEBYTECODE",
            "TMPDIR"
        ])
    );
    for field in ["executable_hash", "prompt_hash", "implementation_hash"] {
        assert!(
            run[field]
                .as_str()
                .is_some_and(|hash| hash.starts_with("sha256:")),
            "missing {field}"
        );
    }
    assert_eq!(run["status"]["exit_code"], 0);
    assert_eq!(run["status"]["timed_out"], false);
}

#[test]
fn generate_agent_prompt_grants_exact_factory_facade_imports() {
    let project = method_project();
    fs::write(
        project.path.join("src/app.cott"),
        "module app\nuse api.service.ReaderState\n\nfn run(factory: Factory[ReaderState]) -> I32\n",
    )
    .expect("Factory source should be writable");
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(
        &omp,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
message=
for message; do :; done
case "$message" in
  @*) prompt=$(cat "${message#@}") || exit 64 ;;
  *) printf '%s\n' 'missing @prompt-file argument' >&2; exit 64 ;;
esac
case "$prompt" in
  *'Symbol: app.run'*'Exact generated Cott facade modules MAY be imported directly or from their parent package, with an optional alias, for module-qualified access. Import generated value types for annotations through `from module_types import Type`, and do not import any other project-local module.'*'Factory annotations require these exact concrete public-facade imports; do not substitute them or import from `*_types`:'*'from api.service import ReaderState'*'Use each listed `from module import Concrete` line for annotations. The same exact generated facade may also be imported under the general module-import rule when its class object is needed.'*'`Factory[Concrete]` maps to `type[Concrete]`'*'Constructor calls MUST match `Concrete`'\''s inferred Cott init signature.'*'Validation MUST NOT construct or invoke a Factory value.'*)
    printf '%s\n' 'from api.service import ReaderState' 'from cott_runtime import I32' '' '' 'def run(factory: type[ReaderState]) -> I32:' '    return 7' > implementation.py
    ;;
  *) exit 64 ;;
esac
"#,
    )
    .expect("write fake OMP");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&omp, fs::Permissions::from_mode(0o755))
            .expect("make fake OMP executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "app.run",
            "--agent",
            "omp",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn generate_promotes_an_impl_method_helper_without_agent_class_shell() {
    let project = method_project();
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(
        &omp,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
message=
for message; do :; done
case "$message" in
  @*) prompt=$(cat "${message#@}") || exit 64 ;;
  *) printf '%s\n' 'missing @prompt-file argument' >&2; exit 64 ;;
esac
case "$prompt" in
  *'Symbol: api.service.ReaderState.read'*'Define exactly one canonical private top-level function `_cott_impl_ReaderState_read`.'*'You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars.'*'The compiler owns the public class `ReaderState` and binds this helper as its method;'*'Import `ReaderState` from `api.service` only for the required `self: ReaderState` annotation.'*)
    printf '%s\n' 'from api.service import ReaderState' 'from cott_runtime import I32' '' '' 'def _cott_impl_ReaderState_read(self: ReaderState, amount: I32) -> I32:' '    return amount' > implementation.py
    ;;
  *) exit 64 ;;
esac
"#,
    )
    .expect("write fake OMP");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&omp, fs::Permissions::from_mode(0o755))
            .expect("make fake OMP executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "api.service.ReaderState.read",
            "--agent",
            "omp",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        fs::read_to_string(
            project
                .path
                .join("python/_cott_impl/api/service/ReaderState/read.py")
        )
        .expect("durable method helper"),
        "from api.service import ReaderState\nfrom cott_runtime import I32\n\n\ndef _cott_impl_ReaderState_read(self: ReaderState, amount: I32) -> I32:\n    return amount\n"
    );
    let record: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json")).expect("generated method record"),
    )
    .expect("generated method record is JSON");
    let implementation = &record["current"]["implementations"][0];
    assert_eq!(implementation["kind"], "impl_method");
    assert_eq!(implementation["concrete"], "ReaderState");
    assert_eq!(implementation["method"], "read");
    let facade = fs::read_to_string(project.path.join("generated/python/api/service.py"))
        .expect("generated method facade");
    assert!(facade.contains("class ReaderState"));
    assert!(
        !project
            .path
            .join("python/_cott_impl/api/service/read.py")
            .exists()
    );
}

#[test]
fn generate_impl_agent_prompt_grants_exact_factory_facade_imports() {
    let project = method_project();
    fs::write(
        project.path.join("src/models.cott"),
        "module models\n\ntrait Builder:\n    fn build(self, amount: I32) -> I32\n\nimpl FactoryConcrete for Builder:\n    state:\n        count: I32 = 0\n    init(count: I32):\n        requires count > 0\n        ensures self.count == count\n    fn build(self, amount: I32) -> I32:\n        ensures result == amount\n",
    )
    .expect("Factory concrete source should be writable");
    fs::write(
        project.path.join("src/api/service.cott"),
        "module api.service\nuse models.FactoryConcrete\n\ntrait Reader:\n    fn read(self, factory: Factory[FactoryConcrete]) -> I32\n\nimpl ReaderState for Reader:\n    state:\n        count: I32 = 0\n    init(count: I32):\n        requires count > 0\n        ensures self.count == count\n    fn read(self, factory: Factory[FactoryConcrete]) -> I32:\n        ensures result == self.count\n",
    )
    .expect("Factory method source should be writable");
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(
        &omp,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
message=
for message; do :; done
case "$message" in
  @*) prompt=$(cat "${message#@}") || exit 64 ;;
  *) printf '%s\n' 'missing @prompt-file argument' >&2; exit 64 ;;
esac
case "$prompt" in
  *'Symbol: api.service.ReaderState.read'*'Factory annotations require these exact concrete public-facade imports; do not substitute them or import from `*_types`:'*'from models import FactoryConcrete'*'`Factory[Concrete]` maps to `type[Concrete]`'*)
    printf '%s\n' 'from api.service import ReaderState' 'from models import FactoryConcrete' 'from cott_runtime import I32' '' '' 'def _cott_impl_ReaderState_read(self: ReaderState, factory: type[FactoryConcrete]) -> I32:' '    return self.count' > implementation.py
    ;;
  *) exit 64 ;;
esac
"#,
    )
    .expect("write fake OMP");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&omp, fs::Permissions::from_mode(0o755))
            .expect("make fake OMP executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "api.service.ReaderState.read",
            "--agent",
            "omp",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn generate_scoped_free_function_does_not_run_unrelated_initializers() {
    let project = method_project();
    fs::write(
        project.path.join("src/api/service.cott"),
        "module api.service\n\nfn run() -> I32\n\ntrait Reader:\n    fn read(self) -> I32\n\nimpl ReaderState for Reader:\n    state:\n        count: I32 = 0\n    invariant false\n    init(count: I32):\n        requires count > 0\n    fn read(self) -> I32:\n        ensures result == self.count\n",
    )
    .expect("scoped free-function source should be writable");
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(
        &omp,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
message=
for message; do :; done
case "$message" in
  @*) prompt=$(cat "${message#@}") || exit 64 ;;
  *) printf '%s\n' 'missing @prompt-file argument' >&2; exit 64 ;;
esac
case "$prompt" in
  *"Symbol: api.service.run"*)
    printf '%s\n' 'from cott_runtime import I32' '' '' 'def run() -> I32:' '    return 7' > implementation.py
    ;;
  *) exit 64 ;;
esac
"#,
    )
    .expect("write fake OMP");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&omp, fs::Permissions::from_mode(0o755))
            .expect("make fake OMP executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "api.service.run",
            "--agent",
            "omp",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn generate_rejects_an_agent_owned_impl_class_shell() {
    let project = method_project();
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(
        &omp,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
printf '%s\n' 'class ReaderState:' '    def read(self, amount: int) -> int:' '        return amount' > implementation.py
"#,
    )
    .expect("write fake OMP");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&omp, fs::Permissions::from_mode(0o755))
            .expect("make fake OMP executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "api.service.ReaderState.read",
            "--agent",
            "omp",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert_eq!(output.status.code(), Some(5));
    assert!(String::from_utf8_lossy(&output.stderr).contains("agent generation"));
    assert!(
        !project
            .path
            .join("python/_cott_impl/api/service/ReaderState/read.py")
            .exists()
    );
}
#[test]
fn process_bar_generation_records_unresolved_and_verified_transitions() {
    let fixture = Path::new(env!("CARGO_MANIFEST_DIR")).join("examples/complex/process-bar");
    let project = TempDir::new();
    fs::copy(fixture.join("cott.toml"), project.path.join("cott.toml"))
        .expect("process-bar manifest should be copied");
    fs::copy(
        fixture.join("GENERATOR_RULES.txt"),
        project.path.join("GENERATOR_RULES.txt"),
    )
    .expect("process-bar generator rules should be copied");
    fs::create_dir_all(project.path.join("src/foo")).expect("fixture source directory");
    fs::copy(
        fixture.join("src/foo/bar.cott"),
        project.path.join("src/foo/bar.cott"),
    )
    .expect("process-bar source should be copied");
    fs::create_dir(project.path.join("python")).expect("target source directory");
    fs::copy(
        fixture.join("python/pyproject.toml"),
        project.path.join("python/pyproject.toml"),
    )
    .expect("target project metadata should be copied");
    install_fake_python_tools(&project.path);

    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    for implementation in [
        "build_output.py",
        "process_bar.py",
        "process_payload_bytes.py",
        "validate_payload.py",
    ] {
        for root in [
            "python/_cott_impl/foo/bar",
            "generated/python/_cott_impl/foo/bar",
        ] {
            assert!(
                !project.path.join(root).join(implementation).exists(),
                "{implementation} must begin unresolved under {root}"
            );
        }
    }
    let initial: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("initial generation record"),
    )
    .expect("initial generation JSON");
    assert_eq!(initial["current"]["verified"], false);
    assert_eq!(initial["current"]["implementations"], serde_json::json!([]));
    let unresolved = initial["current"]["unresolved"]
        .as_array()
        .expect("typed unresolved records");
    assert_eq!(
        unresolved
            .iter()
            .map(|record| record["cott_symbol"]
                .as_str()
                .expect("canonical Cott symbol"))
            .collect::<Vec<_>>(),
        [
            "foo.bar.build_output",
            "foo.bar.process_bar",
            "foo.bar.process_payload_bytes",
            "foo.bar.validate_payload"
        ]
    );
    for record in unresolved {
        assert_eq!(record["kind"], "function");
        let span = record["span"].as_object().expect("source span");
        for field in [
            "start_byte",
            "end_byte",
            "start_line",
            "start_column",
            "end_line",
            "end_column",
        ] {
            assert!(span[field].is_u64(), "{field} must be typed");
        }
    }
    assert_eq!(initial["current"]["agent_runs"], serde_json::json!([]));
    assert!(initial["last_verified"].is_null());

    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(
        &omp,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then
  echo omp/17.2.12
  exit 0
fi
message=
for message; do :; done
case "$message" in
  @*) prompt=$(cat "${message#@}") || exit 64 ;;
  *) printf '%s\n' 'missing @prompt-file argument' >&2; exit 64 ;;
esac
case "$prompt" in
  *"Symbol: foo.bar.build_output"*)
    printf '%s\n' 'from foo.bar_types import OutputPayload, PayloadFormat, PayloadSize' '' '' 'def build_output(data: bytes, source_size: PayloadSize, format: PayloadFormat) -> OutputPayload:' '    return OutputPayload(data=data, source_size=source_size, format=format)' > implementation.py
    printf '%s\n' 'agent-run=build_output'
    ;;
  *"Symbol: foo.bar.process_bar"*)
    printf '%s\n' 'from cott_runtime import Err, Ok, Result' 'from foo.bar import build_output, process_payload_bytes, validate_payload' 'from foo.bar_types import BarError, BarOptions, InputPayload, OutputPayload' '' '' 'def process_bar(data: InputPayload, options: BarOptions) -> Result[OutputPayload, BarError]:' '    validated = validate_payload(data)' '    if isinstance(validated, Err):' '        return Err(error=validated.error)' '    processed = process_payload_bytes(validated.value.data, options)' '    if isinstance(processed, Err):' '        return Err(error=processed.error)' '    return Ok(' '        value=build_output(' '            processed.value,' '            validated.value.declared_size,' '            validated.value.format,' '        )' '    )' > implementation.py
    printf '%s\n' 'agent-run=process_bar'
    ;;
  *"Symbol: foo.bar.process_payload_bytes"*)
    printf '%s\n' 'from cott_runtime import Ok, Result' 'from foo.bar_types import BarError, BarOptions' '' '' 'def process_payload_bytes(data: bytes, options: BarOptions) -> Result[bytes, BarError]:' '    return Ok(value=data)' > implementation.py
    printf '%s\n' 'agent-run=process_payload_bytes'
    ;;
  *"Symbol: foo.bar.validate_payload"*)
    printf '%s\n' 'from cott_runtime import Err, Ok, Result' 'from foo.bar_types import BarError, BarError_InvalidPayload, InputPayload' '' '' 'def validate_payload(data: InputPayload) -> Result[InputPayload, BarError]:' '    if len(data.data) == 0:' '        return Err(error=BarError_InvalidPayload(reason="empty payload"))' '    return Ok(value=data)' > implementation.py
    printf '%s\n' 'agent-run=validate_payload'
    ;;
  *)
    printf '%s\n' 'unexpected process-bar agent prompt' >&2
    exit 64
    ;;
esac
"#,
    )
    .expect("write fake OMP");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&omp, fs::Permissions::from_mode(0o755))
            .expect("make fake OMP executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let before_generate = file_snapshot(&project.path);
    let generated_all = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "--agent",
            "omp",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", &path)
        .output()
        .expect("unscoped generate should run");
    assert!(
        generated_all.status.success(),
        "{}",
        String::from_utf8_lossy(&generated_all.stderr)
    );

    let expected_bindings = [
        (
            "python/_cott_impl/foo/bar/build_output.py",
            "from foo.bar_types import OutputPayload, PayloadFormat, PayloadSize\n\n\ndef build_output(data: bytes, source_size: PayloadSize, format: PayloadFormat) -> OutputPayload:\n    return OutputPayload(data=data, source_size=source_size, format=format)\n",
        ),
        (
            "python/_cott_impl/foo/bar/process_bar.py",
            "from cott_runtime import Err, Ok, Result\nfrom foo.bar import build_output, process_payload_bytes, validate_payload\nfrom foo.bar_types import BarError, BarOptions, InputPayload, OutputPayload\n\n\ndef process_bar(data: InputPayload, options: BarOptions) -> Result[OutputPayload, BarError]:\n    validated = validate_payload(data)\n    if isinstance(validated, Err):\n        return Err(error=validated.error)\n    processed = process_payload_bytes(validated.value.data, options)\n    if isinstance(processed, Err):\n        return Err(error=processed.error)\n    return Ok(\n        value=build_output(\n            processed.value,\n            validated.value.declared_size,\n            validated.value.format,\n        )\n    )\n",
        ),
        (
            "python/_cott_impl/foo/bar/process_payload_bytes.py",
            "from cott_runtime import Ok, Result\nfrom foo.bar_types import BarError, BarOptions\n\n\ndef process_payload_bytes(data: bytes, options: BarOptions) -> Result[bytes, BarError]:\n    return Ok(value=data)\n",
        ),
        (
            "python/_cott_impl/foo/bar/validate_payload.py",
            "from cott_runtime import Err, Ok, Result\nfrom foo.bar_types import BarError, BarError_InvalidPayload, InputPayload\n\n\ndef validate_payload(data: InputPayload) -> Result[InputPayload, BarError]:\n    if len(data.data) == 0:\n        return Err(error=BarError_InvalidPayload(reason=\"empty payload\"))\n    return Ok(value=data)\n",
        ),
    ];
    for (relative, expected) in expected_bindings {
        assert_eq!(
            fs::read_to_string(project.path.join(relative))
                .unwrap_or_else(|error| panic!("durable helper {relative}: {error}")),
            expected
        );
    }

    let generated: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("generated generation record"),
    )
    .expect("generated generation JSON");
    assert_eq!(generated["current"]["verified"], false);
    assert_eq!(generated["current"]["unresolved"], serde_json::json!([]));
    assert_eq!(
        generated["current"]["implementations"]
            .as_array()
            .expect("generated implementations")
            .iter()
            .map(|implementation| {
                (
                    implementation["cott_symbol"].as_str().expect("Cott symbol"),
                    implementation["kind"].as_str().expect("callable kind"),
                    implementation["concrete"].is_null(),
                    implementation["method"].is_null(),
                    implementation["owner"].as_str().expect("owner"),
                )
            })
            .collect::<Vec<_>>(),
        [
            ("foo.bar.build_output", "function", true, true, "agent"),
            ("foo.bar.process_bar", "function", true, true, "agent"),
            (
                "foo.bar.process_payload_bytes",
                "function",
                true,
                true,
                "agent",
            ),
            ("foo.bar.validate_payload", "function", true, true, "agent"),
        ]
    );
    assert!(generated["last_verified"].is_null());
    let agent_runs = generated["current"]["agent_runs"].clone();
    let run_summaries = agent_runs
        .as_array()
        .expect("agent runs")
        .iter()
        .map(|run| {
            serde_json::json!({
                "symbol": run["symbol"],
                "adapter": run["adapter"],
                "adapter_version": run["adapter_version"],
                "status": run["status"],
                "stdout_bytes": run["stdout"]["bytes"],
                "stderr_bytes": run["stderr"]["bytes"],
            })
        })
        .collect::<Vec<_>>();
    assert_eq!(
        serde_json::Value::Array(run_summaries),
        serde_json::json!([
            {
                "symbol": "foo.bar.build_output",
                "adapter": "omp",
                "adapter_version": "17.2.12",
                "status": {
                    "exit_code": 0,
                    "signal": null,
                    "timed_out": false,
                    "cancelled": false
                },
                "stdout_bytes": 23,
                "stderr_bytes": 0
            },
            {
                "symbol": "foo.bar.process_bar",
                "adapter": "omp",
                "adapter_version": "17.2.12",
                "status": {
                    "exit_code": 0,
                    "signal": null,
                    "timed_out": false,
                    "cancelled": false
                },
                "stdout_bytes": 22,
                "stderr_bytes": 0
            },
            {
                "symbol": "foo.bar.process_payload_bytes",
                "adapter": "omp",
                "adapter_version": "17.2.12",
                "status": {
                    "exit_code": 0,
                    "signal": null,
                    "timed_out": false,
                    "cancelled": false
                },
                "stdout_bytes": 32,
                "stderr_bytes": 0
            },
            {
                "symbol": "foo.bar.validate_payload",
                "adapter": "omp",
                "adapter_version": "17.2.12",
                "status": {
                    "exit_code": 0,
                    "signal": null,
                    "timed_out": false,
                    "cancelled": false
                },
                "stdout_bytes": 27,
                "stderr_bytes": 0
            }
        ])
    );

    let after_generate = file_snapshot(&project.path);
    let mut changed = before_generate
        .keys()
        .chain(after_generate.keys())
        .filter(|path| before_generate.get(*path) != after_generate.get(*path))
        .cloned()
        .collect::<std::collections::BTreeSet<_>>();
    let managed = generated["current"]["managed_files"]
        .as_object()
        .expect("managed files");
    let mut expected = managed
        .keys()
        .map(PathBuf::from)
        .collect::<std::collections::BTreeSet<_>>();
    expected.insert(PathBuf::from("generated/generation.json"));
    for implementation in [
        "build_output.py",
        "process_bar.py",
        "process_payload_bytes.py",
        "validate_payload.py",
    ] {
        let implementation = PathBuf::from("python/_cott_impl/foo/bar").join(implementation);
        expected.insert(implementation.clone());
        assert!(changed.remove(&implementation));
    }
    assert!(
        changed.iter().all(|path| expected.contains(path)),
        "unexpected changed files: {changed:?}"
    );

    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
    let verified_record: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("verified generation record"),
    )
    .expect("verified generation JSON");
    assert_eq!(verified_record["current"]["verified"], true);
    assert_eq!(verified_record["current"], verified_record["last_verified"]);
    assert_eq!(
        verified_record["current"]["implementations"],
        generated["current"]["implementations"]
    );
    assert_eq!(verified_record["current"]["agent_runs"], agent_runs);

    let diff = cott(&project.path, &["diff"]);
    assert!(
        diff.status.success(),
        "{}",
        String::from_utf8_lossy(&diff.stderr)
    );
    assert_eq!(
        String::from_utf8(diff.stdout).expect("diff output should be UTF-8"),
        "NO CHANGE\n"
    );
}

#[test]
fn diff_enforces_version_compatibility_and_emits_closed_json() {
    let project = project();
    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    fs::copy(
        project.path.join("generated/generation.json"),
        project.path.join("baseline.json"),
    )
    .expect("baseline should be copyable");
    let baseline: serde_json::Value =
        serde_json::from_slice(&fs::read(project.path.join("baseline.json")).expect("baseline"))
            .expect("baseline should be JSON");
    assert_eq!(baseline["schema_version"], 7);
    assert_eq!(baseline["current"]["project_version"], "0.1.0");
    assert_eq!(
        baseline["current"]["compatibility"],
        serde_json::json!({
            "generation_schema": 7,
            "canonical_ir_schema": 8,
            "runtime_abi": 7,
            "contract_strategy_schema": 5
        })
    );
    let manifest = fs::read_to_string(project.path.join("cott.toml")).expect("manifest");
    fs::write(
        project.path.join("cott.toml"),
        manifest.replace("version = \"0.1.0\"", "version = \"0.2.0\""),
    )
    .expect("manifest version should be writable");
    let metadata =
        fs::read_to_string(project.path.join("python/pyproject.toml")).expect("target metadata");
    fs::write(
        project.path.join("python/pyproject.toml"),
        metadata.replace("version = \"0.1.0\"", "version = \"0.2.0\""),
    )
    .expect("target metadata version should be writable");
    fs::write(
        project.path.join("src/app.cott"),
        "module app\n\nfn run() -> I64\n",
    )
    .expect("changed source should be writable");
    fs::write(
        project.path.join("python/cott_bindings/app/run.py"),
        BINDING.replace("I32", "I64"),
    )
    .expect("changed binding should be writable");

    let text = cott(
        &project.path,
        &["diff", "--baseline", "baseline.json", "--exit-code"],
    );
    assert_eq!(text.status.code(), Some(7));
    let text = String::from_utf8(text.stdout).expect("diff text should be UTF-8");
    assert!(text.contains("CONTRACT BREAKING:\n- app.run contract changed"));
    assert!(!text.contains("VERSION INCOMPATIBLE"));

    let json = cott(
        &project.path,
        &[
            "diff",
            "--baseline",
            "baseline.json",
            "--exit-code",
            "--format",
            "json",
        ],
    );
    assert!(json.stderr.is_empty());
    assert_eq!(json.status.code(), Some(7));
    let report: serde_json::Value =
        serde_json::from_slice(&json.stdout).expect("diff JSON must be one report document");
    assert_eq!(report["breaking"], true);
    assert_eq!(report["version_compatible"], true);
    assert_eq!(report["required_version_bump"], "minor");
    assert!(
        report["changes"]
            .as_array()
            .expect("changes")
            .iter()
            .any(|change| {
                change["class"] == "breaking"
                    && change["kind"] == "semantic_changed"
                    && change["subject"] == "app.run"
            })
    );

    let manifest = fs::read_to_string(project.path.join("cott.toml")).expect("manifest");
    fs::write(
        project.path.join("cott.toml"),
        manifest.replace("version = \"0.2.0\"", "version = \"0.1.0\""),
    )
    .expect("manifest version should be writable");
    let metadata =
        fs::read_to_string(project.path.join("python/pyproject.toml")).expect("target metadata");
    fs::write(
        project.path.join("python/pyproject.toml"),
        metadata.replace("version = \"0.2.0\"", "version = \"0.1.0\""),
    )
    .expect("target metadata version should be writable");
    let incompatible = cott(
        &project.path,
        &["diff", "--baseline", "baseline.json", "--exit-code"],
    );

    assert_eq!(incompatible.status.code(), Some(7));
    assert!(String::from_utf8_lossy(&incompatible.stdout).contains("VERSION INCOMPATIBLE"));

    let bad = fs::read_to_string(project.path.join("baseline.json")).expect("baseline");
    fs::write(
        project.path.join("bad-baseline.json"),
        bad.replace("\"runtime_abi\":7", "\"runtime_abi\":1"),
    )
    .expect("invalid baseline should be writable");
    let rejected = cott(&project.path, &["diff", "--baseline", "bad-baseline.json"]);
    assert_eq!(rejected.status.code(), Some(2));
    assert!(rejected.stdout.is_empty());
    assert!(String::from_utf8_lossy(&rejected.stderr).contains("invalid diff baseline"));
}
#[test]
fn diff_reports_target_local_drift_only_for_matching_platform() {
    let project = project();
    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let baseline_path = project.path.join("baseline.json");
    let mut baseline: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json")).expect("generation record"),
    )
    .expect("generation record is JSON");
    baseline["current"]["tools"]["python"]["version"] = serde_json::json!("3.14.7");
    baseline["current"]["tools"]["basedpyright"] = serde_json::json!({
        "content_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "executable": "/other/basedpyright",
        "version": "9.9.9"
    });
    baseline["current"]["tools"]["compiler"] = serde_json::json!({
        "content_hash": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "executable": "/other/cott",
        "version": env!("CARGO_PKG_VERSION")
    });
    let artifact = baseline["current"]["managed_files"]
        .as_object()
        .expect("managed files")
        .keys()
        .next()
        .cloned()
        .expect("managed artifact");
    baseline["current"]["managed_files"][artifact.as_str()] = serde_json::json!(
        "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
    );
    recompute_generation_id(&mut baseline["current"]);
    fs::write(
        &baseline_path,
        serde_json::to_vec(&baseline).expect("baseline serialization"),
    )
    .expect("baseline should be writable");

    let same_target = cott(
        &project.path,
        &["diff", "--baseline", "baseline.json", "--format", "json"],
    );
    assert!(
        same_target.status.success(),
        "{}",
        String::from_utf8_lossy(&same_target.stderr)
    );
    let report: serde_json::Value = serde_json::from_slice(&same_target.stdout).expect("diff JSON");
    let changes = report["changes"].as_array().expect("diff changes");
    for subject in ["python", "basedpyright", "compiler"] {
        assert!(changes.iter().any(|change| {
            change["class"] == "toolchain"
                && change["kind"] == "toolchain_changed"
                && change["subject"] == subject
        }));
    }
    assert!(changes.iter().any(|change| {
        change["class"] == "artifact"
            && change["kind"] == "artifact_changed"
            && change["subject"] == artifact
    }));

    baseline["current"]["tools"]["python"]["machine"] = serde_json::json!("other-machine");
    recompute_generation_id(&mut baseline["current"]);
    fs::write(
        &baseline_path,
        serde_json::to_vec(&baseline).expect("cross-target baseline serialization"),
    )
    .expect("cross-target baseline should be writable");
    let cross_target = cott(
        &project.path,
        &["diff", "--baseline", "baseline.json", "--format", "json"],
    );
    assert!(
        cross_target.status.success(),
        "{}",
        String::from_utf8_lossy(&cross_target.stderr)
    );
    let report: serde_json::Value =
        serde_json::from_slice(&cross_target.stdout).expect("cross-target diff JSON");
    let changes = report["changes"]
        .as_array()
        .expect("cross-target diff changes");
    assert!(
        !changes
            .iter()
            .any(|change| change["class"] == "toolchain" || change["class"] == "artifact")
    );
}

#[test]
fn generate_promotes_a_sandboxed_codex_candidate_with_artifacts() {
    let project = project();
    make_unresolved(&project);
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let codex = tools.join("codex");
    fs::write(&codex, "#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo codex-cli 0.147.0; exit 0; fi\ncat >/dev/null\nprintf 'from cott_runtime import I32\\n\\n\\ndef run() -> I32:\\n    return 7\\n' > implementation.py\n")
        .expect("write fake Codex");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&codex, fs::Permissions::from_mode(0o755))
            .expect("make fake Codex executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "--agent",
            "codex",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        fs::read_to_string(project.path.join("python/_cott_impl/app/run.py"))
            .expect("durable candidate"),
        "from cott_runtime import I32\n\n\ndef run() -> I32:\n    return 7\n"
    );
}

#[test]
fn init_scaffolds_a_normative_project_with_supported_uv() {
    let temp = TempDir::new();
    let tools = temp.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let uv = tools.join("uv");
    fs::write(
        &uv,
        r#"#!/bin/sh
if [ "$1" = "--no-config" ]; then shift; fi
case "$1" in
  --version) echo 'uv 0.12.4' ;;
  python)
    managed="$(dirname "$0")/managed"
    if [ "$2" = "dir" ]; then
      mkdir -p "$managed"
      printf '%s\n' '#!/bin/sh' 'echo "cpython 3.14.7"' > "$managed/python"
      chmod +x "$managed/python"
      echo "$managed"
    elif [ "$2" = "find" ]; then
      echo "$managed/python"
    fi
    ;;
  lock)
    touch python/uv.lock
    ;;
  venv|sync)
    mkdir -p "$UV_PROJECT_ENVIRONMENT/bin"
    printf '%s\n' '#!/bin/sh' 'echo "cpython 3.14.7"' > "$UV_PROJECT_ENVIRONMENT/bin/python"
    printf '%s\n' '#!/bin/sh' 'echo "basedpyright 1.40.0"' > "$UV_PROJECT_ENVIRONMENT/bin/basedpyright"
    chmod +x "$UV_PROJECT_ENVIRONMENT/bin/python" "$UV_PROJECT_ENVIRONMENT/bin/basedpyright"
    ;;
esac
"#,
    )
    .expect("write fake uv");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&uv, fs::Permissions::from_mode(0o755))
            .expect("make fake uv executable");
    }
    let target = temp.path.join("new-app");
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(["init"])
        .arg(&target)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(target.join("src/new_app/main.cott").is_file());
    let manifest = fs::read_to_string(target.join("cott.toml")).expect("manifest");
    assert!(manifest.contains("version = \"0.1.0\""));
    assert!(manifest.contains("runtime_validation = \"boundary\""));
    assert!(manifest.contains("lockfile = \"python/uv.lock\""));
    assert!(target.join("python/uv.lock").is_file());
    let pyproject = fs::read_to_string(target.join("python/pyproject.toml")).expect("pyproject");
    assert!(pyproject.contains("requires-python = \">=3.14.6,<3.15\""));
    assert!(pyproject.contains("basedpyright>=1.39.9"));
    assert_eq!(
        fs::read_to_string(target.join(".gitignore")).expect("gitignore"),
        ".cott/\n.venv/\ngenerated/generation.json\n__pycache__/\n*.py[cod]\n"
    );
}
#[test]
fn json_mode_returns_one_closed_diagnostic_document_with_source_spans() {
    let project = project();
    fs::write(
        project.path.join("src/app.cott"),
        "module app\n\nfn run( -> I32\n",
    )
    .expect("source should be writable");

    let output = cott(&project.path, &["check", "--format", "json"]);
    assert_eq!(output.status.code(), Some(3));
    assert!(output.stderr.is_empty());
    let report: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("stdout should be one JSON document");
    assert_eq!(report["schema_version"], 1);
    let diagnostic = &report["diagnostics"][0];
    assert_eq!(diagnostic["severity"], "error");
    assert_eq!(diagnostic["span"]["path"], "src/app.cott");
    assert!(diagnostic["span"]["end_byte"].as_u64().is_some());
}

#[test]
fn runs_generated_facade_when_python3_is_available() {
    let probe = match Command::new("python3")
        .args([
            "-c",
            "import pathlib,platform,sys; print(platform.python_version()); print(pathlib.Path(sys.executable).resolve())",
        ])
        .output()
    {
        Ok(output) if output.status.success() => output,
        _ => return,
    };
    let probe = String::from_utf8(probe.stdout).expect("Python probe must be UTF-8");
    let mut lines = probe.lines();
    if lines.next() != Some("3.14.6") {
        return;
    }
    let interpreter = PathBuf::from(lines.next().expect("Python probe executable"));
    let project = project();
    fs::copy(&interpreter, project.path.join(".venv/bin/python"))
        .expect("install matching target Python");
    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let output = Command::new(&interpreter)
        .args(["-c", "from app import run; print(run())"])
        .current_dir(project.path.join("generated/python"))
        .output()
        .expect("generated facade should run");

    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        String::from_utf8(output.stdout).expect("stdout must be UTF-8"),
        "7\n"
    );
    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
}
#[test]
fn generated_facades_enforce_contextual_and_exit_contracts() {
    let project = TempDir::new();
    fs::write(
        project.path.join("cott.toml"),
        r#"[project]
name = "contract-e2e"
version = "0.1.0"
source = "src"

[target.python]
source = "python"
generated = "generated/python"
stubs = "generated/stubs"
interpreter = ".venv/bin/python"
type_checker = ".venv/bin/basedpyright"
runtime_validation = "boundary"

[target.python.implementations]
"app.bounded" = "cott_bindings.app.bounded:bounded"
"app.guarded" = "cott_bindings.app.guarded:guarded"
"app.terminate" = "cott_bindings.app.terminate:terminate"
"app.abort" = "cott_bindings.app.abort:abort"
"#,
    )
    .expect("manifest should be writable");
    fs::create_dir_all(project.path.join("src")).expect("source directory should be writable");
    fs::write(
        project.path.join("src/app.cott"),
        r#"module app

enum GateError:
    Rejected

newtype Key(U64)
newtype Labels(List[Str])

struct Boxed:
    value: I32

enum Mixed:
    Empty
    Full(value: I32)

fn bounded(value: F32) -> F32:
    requires value + 0.5 <= 1.0

fn guarded(value: I32) -> Result[I32, GateError]:
    ensures Result.Ok(output) => output == value
    error GateError.Rejected when value < 0
fn terminate(code: I32) -> Never:
    effects [process.exit]

fn abort(code: I32) -> Unit:
    effects [process.exit]
"#,
    )
    .expect("source should be writable");
    fs::create_dir_all(project.path.join("python")).expect("Python source directory");
    fs::write(
        project.path.join("python/pyproject.toml"),
        "[project]\nname = \"contract-e2e\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14,<3.15\"\ndependencies = []\n",
    )
    .expect("target project metadata should be writable");
    let implementations = [
        (
            "bounded",
            "from cott_runtime import F32


def bounded(value: F32) -> F32:
    return value
",
        ),
        (
            "guarded",
            "from app_types import GateError, GateError_Rejected
from cott_runtime import Err, I32, Ok, Result


def guarded(value: I32) -> Result[I32, GateError]:
    if value < 0:
        return Err(error=GateError_Rejected())
    return Ok(value=value)
",
        ),
        (
            "terminate",
            "from typing import Never

from cott_runtime import I32


def terminate(code: I32) -> Never:
    raise SystemExit(code)
",
        ),
        (
            "abort",
            "from cott_runtime import I32, Unit


def abort(code: I32) -> Unit:
    raise SystemExit(code)
",
        ),
    ];
    for (function, source) in implementations {
        let path = project
            .path
            .join("python/cott_bindings/app")
            .join(format!("{function}.py"));
        fs::create_dir_all(path.parent().expect("implementation parent"))
            .expect("implementation directory should be writable");
        fs::write(path, source).expect("implementation should be writable");
    }
    install_fake_python_tools(&project.path);

    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    retarget_generation_to_host_python(&project.path);

    let script = r#"
import json

from app import abort, bounded, guarded, terminate
from cott_runtime import CottContractViolation, Err, Ok
from app_types import Boxed, Key, Labels, Mixed_Empty, Mixed_Full

bounded_value = bounded(0.25)
assert bounded_value == 0.25
guarded_ok = guarded(3)
assert isinstance(guarded_ok, Ok) and guarded_ok.value == 3
guarded_error = guarded(-1)
assert isinstance(guarded_error, Err)
assert type(guarded_error.error).__name__ == "GateError_Rejected"
assert Boxed.__hash__ is None
assert Labels.__hash__ is None
assert Mixed_Full.__hash__ is None
assert isinstance(hash(Key(value=1)), int)
assert isinstance(hash(Mixed_Empty()), int)

try:
    bounded(0.75)
except CottContractViolation as error:
    requires = {
        "symbol": error.symbol,
        "phase": error.phase,
        "span": error.span,
        "expected": error.expected,
        "actual": error.actual,
    }
else:
    raise AssertionError("bounded requires should fail")

try:
    terminate(7)
except SystemExit as error:
    never_exit = error.code
else:
    raise AssertionError("declared Never process.exit should propagate")

try:
    abort(9)
except CottContractViolation as error:
    system_exit_violation = {
        "symbol": error.symbol,
        "phase": error.phase,
        "expected": error.expected,
        "actual": error.actual,
    }
else:
    raise AssertionError("non-Never SystemExit should violate the contract")

print(json.dumps({
    "bounded": bounded_value,
    "guarded_ok": guarded_ok.value,
    "guarded_error": type(guarded_error.error).__name__,
    "requires": requires,
    "never_exit": never_exit,
    "system_exit_violation": system_exit_violation,
}))
"#;
    let output = Command::new("/usr/bin/python3")
        .args(["-c", script])
        .current_dir(project.path.join("generated/python"))
        .output()
        .expect("generated facades should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );

    let report: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("facade report should be JSON");
    assert_eq!(report["bounded"], 0.25);
    assert_eq!(report["guarded_ok"], 3);
    assert_eq!(report["guarded_error"], "GateError_Rejected");
    let requires = &report["requires"];
    assert_eq!(requires["symbol"], "app.bounded");
    assert_eq!(requires["phase"], "requires");
    assert!(requires["span"].is_object());
    assert!(requires["span"]["start_line"].as_u64().is_some());
    assert_eq!(requires["expected"], "true");
    assert_eq!(requires["actual"], "false");
    assert_eq!(report["never_exit"], 7);
    assert_eq!(report["system_exit_violation"]["symbol"], "app.abort");
    assert_eq!(
        report["system_exit_violation"]["phase"],
        "implementation-call"
    );
    assert_eq!(
        report["system_exit_violation"]["expected"],
        "ordinary return or declared Never process.exit"
    );
    assert_eq!(report["system_exit_violation"]["actual"], "SystemExit");
}
