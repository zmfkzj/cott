//! A Python production lock closure may contain distributions that no implementation imports.
//! The published record must still describe that whole closure, so `requirements`, `diff`, and a
//! repeated `verify` agree with the snapshot `verify` certified.

use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use serde_json::Value;

#[path = "support/snapshot.rs"]
mod snapshot;

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-python-lock-closure-{}-{number}",
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

fn succeed(root: &Path, arguments: &[&str]) -> Output {
    let output = cott(root, arguments);
    assert_eq!(
        output.status.code(),
        Some(0),
        "{arguments:?}: {}{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    output
}

const MANIFEST: &str = "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.python]\nsource = \"python\"\ngenerated = \"generated/python\"\nstubs = \"generated/stubs\"\nlockfile = \"python/uv.lock\"\ninterpreter = \".venv/bin/python\"\ntype_checker = \".venv/bin/basedpyright\"\nruntime_validation = \"boundary\"\n\n[target.python.implementations]\n\"app.run\" = \"cott_bindings.app.run:run\"\n";

const SOURCE: &str = r#"module app

fn run() -> I32

scenario returns_seven:
    call value = run()
    assert value == 7

requirement SEVEN for run:
    text "Run returns seven."
    checked_by returns_seven
"#;

/// `alpha` is imported by the implementation; `beta` is a locked production dependency that
/// no implementation imports.
const LOCK: &str = "version = 1\nrevision = 3\nrequires-python = \">=3.14,<3.15\"\n\n[[package]]\nname = \"demo\"\nversion = \"0.1.0\"\nsource = { virtual = \".\" }\ndependencies = [{ name = \"alpha\" }, { name = \"beta\" }]\n\n[[package]]\nname = \"alpha\"\nversion = \"1.0.0\"\nsource = { registry = \"https://pypi.org/simple\" }\nwheels = [{ hash = \"sha256:1111111111111111111111111111111111111111111111111111111111111111\" }]\n\n[[package]]\nname = \"beta\"\nversion = \"2.0.0\"\nsource = { registry = \"https://pypi.org/simple\" }\nwheels = [{ hash = \"sha256:2222222222222222222222222222222222222222222222222222222222222222\" }]\n";

fn write_exec(path: &Path, body: &str) {
    use std::os::unix::fs::PermissionsExt;
    fs::write(path, body).expect("write fake tool");
    fs::set_permissions(path, fs::Permissions::from_mode(0o755))
        .expect("make fake tool executable");
}

fn install_distribution(site: &Path, name: &str, version: &str, module: &str) {
    let package = site.join(name);
    fs::create_dir_all(&package).expect("distribution package");
    fs::write(package.join("__init__.py"), module).expect("distribution module");
    let info = site.join(format!("{name}-{version}.dist-info"));
    fs::create_dir_all(&info).expect("distribution metadata");
    fs::write(
        info.join("METADATA"),
        format!("Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"),
    )
    .expect("METADATA");
    fs::write(info.join("top_level.txt"), format!("{name}\n")).expect("top_level.txt");
    fs::write(
        info.join("RECORD"),
        format!(
            "{name}/__init__.py,,\n{name}-{version}.dist-info/METADATA,,\n{name}-{version}.dist-info/top_level.txt,,\n{name}-{version}.dist-info/RECORD,,\n"
        ),
    )
    .expect("RECORD");
}

fn locked_project() -> TempDir {
    let temp = TempDir::new();
    let root = &temp.path;
    fs::write(root.join("cott.toml"), MANIFEST).expect("manifest");
    fs::create_dir_all(root.join("src")).expect("source directory");
    fs::write(root.join("src/app.cott"), SOURCE).expect("contract");
    fs::create_dir_all(root.join("python/cott_bindings/app")).expect("binding directory");
    fs::write(
        root.join("python/pyproject.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14,<3.15\"\ndependencies = [\"alpha\", \"beta\"]\n",
    )
    .expect("target metadata");
    fs::write(root.join("python/uv.lock"), LOCK).expect("lockfile");
    fs::write(
        root.join("python/cott_bindings/app/run.py"),
        "import alpha\nfrom cott_runtime import I32\n\n\ndef run() -> I32:\n    return alpha.VALUE\n",
    )
    .expect("binding");
    let site = root.join(".venv/lib/python3.14/site-packages");
    install_distribution(&site, "alpha", "1.0.0", "VALUE = 7\n");
    install_distribution(&site, "beta", "2.0.0", "VALUE = 2\n");
    let bin = root.join(".venv/bin");
    fs::create_dir_all(&bin).expect("fake Python tool directory");
    write_exec(
        &bin.join("python"),
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
    );
    write_exec(
        &bin.join("basedpyright"),
        "#!/bin/sh\n[ \"$1\" = \"--version\" ] && printf 'basedpyright 1.39.9\\nbased on pyright 1.1.411\\n'\nexit 0\n",
    );
    temp
}

fn dependencies(root: &Path) -> Vec<Value> {
    let record = snapshot::read(&fs::read(root.join("generated/generation.json")).expect("record"));
    record["current"]["dependencies"]
        .as_array()
        .expect("dependency records")
        .clone()
}

#[test]
fn verified_lock_closure_with_unimported_distribution_stays_current() {
    let project = locked_project();
    let root = project.path.as_path();
    succeed(root, &["emit", "python"]);
    succeed(root, &["verify"]);
    let certified = dependencies(root);

    let report = succeed(root, &["requirements", "--format", "json"]);
    let report: Value = serde_json::from_slice(&report.stdout).expect("requirement report JSON");
    assert_eq!(report["evidence"]["state"], "current", "{report}");

    let diff = succeed(root, &["diff"]);
    assert_eq!(String::from_utf8_lossy(&diff.stdout), "NO CHANGE\n");

    succeed(root, &["verify"]);

    // The certified record keeps the whole production closure; only the imported
    // distribution carries observed installed evidence.
    let recorded = dependencies(root);
    assert_eq!(recorded, certified);
    let names = recorded
        .iter()
        .map(|dependency| dependency["name"].as_str().expect("dependency name"))
        .collect::<Vec<_>>();
    assert_eq!(names, ["alpha", "beta"], "{recorded:?}");
    assert!(
        recorded[0]["installed"]["origins"].is_array(),
        "{recorded:?}"
    );
    assert!(recorded[1].get("installed").is_none(), "{recorded:?}");
}
