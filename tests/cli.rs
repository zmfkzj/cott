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

const MANIFEST: &str = r#"[project]
name = "demo"
source = "src"

[target.python]
generated = "generated/python"
entry = "app.run"
"#;

const SOURCE: &str = "module app\n\nfn run() -> I32\n";
const BINDING: &str = "def run() -> int:\n    return 7\n";

fn project() -> TempDir {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(temp.path.join("src/app.cott"), SOURCE).expect("source should be writable");
    fs::create_dir_all(temp.path.join("python/_cott_impl/app"))
        .expect("implementation directory should be writable");
    fs::write(temp.path.join("python/_cott_impl/app/run.py"), BINDING)
        .expect("binding should be writable");
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
        "generated/python/__main__.py",
        "generated/stubs/app.pyi",
        "generated/ir/app.json",
        "generated/generation.json",
    ] {
        assert!(
            project.path.join(path).is_file(),
            "missing generated artifact {path}"
        );
    }

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
        project.path.join("python/_cott_impl/app/run.py"),
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
    fs::remove_file(project.path.join("python/_cott_impl/app/run.py"))
        .expect("binding should be removable");

    let output = cott(&project.path, &["generate", "--target", "python"]);

    assert_eq!(output.status.code(), Some(2));
    assert!(String::from_utf8_lossy(&output.stderr).contains("requires `--agent codex|omp`"));
}

#[test]
fn generate_promotes_a_sandboxed_omp_candidate_with_artifacts() {
    let project = project();
    fs::remove_file(project.path.join("python/_cott_impl/app/run.py"))
        .expect("binding should be removable");
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(&omp, "#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo omp/17.2.12; exit 0; fi\nprintf 'def run() -> int:\\n    return 7\\n' > implementation.py\n")
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
        "def run() -> int:\n    return 7\n"
    );
    assert!(project.path.join("generated/python/app.py").is_file());
}

#[test]
fn generate_promotes_a_sandboxed_codex_candidate_with_artifacts() {
    let project = project();
    fs::remove_file(project.path.join("python/_cott_impl/app/run.py"))
        .expect("binding should be removable");
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let codex = tools.join("codex");
    fs::write(&codex, "#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo codex-cli 0.147.0; exit 0; fi\ncat >/dev/null\nprintf 'def run() -> int:\\n    return 7\\n' > implementation.py\n")
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
        "def run() -> int:\n    return 7\n"
    );
}

#[test]
fn init_scaffolds_a_normative_project_with_pinned_uv() {
    let temp = TempDir::new();
    let tools = temp.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let uv = tools.join("uv");
    fs::write(&uv, "#!/bin/sh\necho 'uv 0.12.3'\n").expect("write fake uv");
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
}
#[test]
fn runs_generated_entry_module_when_python3_is_available() {
    let usable_python = Command::new("python3")
        .args([
            "-c",
            "import sys; raise SystemExit(sys.version_info < (3, 10))",
        ])
        .status()
        .is_ok_and(|status| status.success());
    if !usable_python {
        return;
    }

    let project = project();
    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let output = Command::new("python3")
        .args(["-m", "app"])
        .current_dir(project.path.join("generated/python"))
        .output()
        .expect("generated entry module should run");

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
