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
        "#!/bin/sh\n[ \"$1\" = \"--version\" ] && echo 'basedpyright 1.39.9'\nexit 0\n",
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
for k in ("generation_id","verified","verification","agent_runs"): i.pop(k,None)
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

    fs::write(project.path.join("generated/python/app.py"), "tampered\n")
        .expect("generated artifact should be writable");
    let rejected = cott(&project.path, &["verify"]);
    assert_eq!(rejected.status.code(), Some(4));
    assert!(String::from_utf8_lossy(&rejected.stderr).contains("managed artifact differs"));
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
fn generate_requires_an_agent_only_for_unresolved_functions() {
    let project = project();
    make_unresolved(&project);

    let output = cott(&project.path, &["generate", "--target", "python"]);

    assert_eq!(output.status.code(), Some(2));
    assert!(String::from_utf8_lossy(&output.stderr).contains("requires `--agent codex|omp`"));
}

#[test]
fn generate_promotes_a_sandboxed_omp_candidate_with_artifacts() {
    let project = project();
    make_unresolved(&project);
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(&omp, "#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo omp/17.2.12; exit 0; fi\nprintf 'from cott_runtime import I32\\n\\n\\ndef run() -> I32:\\n    return 7\\n' > implementation.py\n")
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
fn process_bar_generation_records_unresolved_and_verified_transitions() {
    let fixture = Path::new(env!("CARGO_MANIFEST_DIR")).join("examples/complex/process-bar");
    let project = TempDir::new();
    fs::copy(fixture.join("cott.toml"), project.path.join("cott.toml"))
        .expect("process-bar manifest should be copied");
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
    assert_eq!(
        initial["current"]["unresolved"],
        serde_json::json!([
            "foo.bar.build_output",
            "foo.bar.process_bar",
            "foo.bar.process_payload_bytes",
            "foo.bar.validate_payload"
        ])
    );
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
case "$*" in
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
                    implementation["owner"].as_str().expect("owner"),
                )
            })
            .collect::<Vec<_>>(),
        [
            ("foo.bar.build_output", "agent"),
            ("foo.bar.process_bar", "agent"),
            ("foo.bar.process_payload_bytes", "agent"),
            ("foo.bar.validate_payload", "agent"),
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
fn init_scaffolds_a_normative_project_with_pinned_uv() {
    let temp = TempDir::new();
    let tools = temp.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let uv = tools.join("uv");
    fs::write(
        &uv,
        r#"#!/bin/sh
if [ "$1" = "--no-config" ]; then shift; fi
case "$1" in
  --version) echo 'uv 0.12.3' ;;
  python)
    managed="$(dirname "$0")/managed"
    if [ "$2" = "dir" ]; then
      mkdir -p "$managed"
      printf '%s\n' '#!/bin/sh' 'echo "cpython 3.14.6"' > "$managed/python"
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
    printf '%s\n' '#!/bin/sh' 'echo "cpython 3.14.6"' > "$UV_PROJECT_ENVIRONMENT/bin/python"
    printf '%s\n' '#!/bin/sh' 'echo "basedpyright 1.39.9"' > "$UV_PROJECT_ENVIRONMENT/bin/basedpyright"
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
