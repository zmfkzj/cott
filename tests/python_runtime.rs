use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};

use cott::python_runtime::render_runtime;

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-python-runtime-{}-{number}",
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

fn write_runtime(root: &Path) {
    for (relative, bytes) in render_runtime("demo") {
        let path = root.join(relative);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).expect("runtime parent should be writable");
        }
        fs::write(path, bytes).expect("runtime file should be writable");
    }
}

fn sha256_hex(bytes: &[u8]) -> String {
    use sha2::{Digest, Sha256};
    format!("{:x}", Sha256::digest(bytes))
}

#[test]
fn generated_runtime_exercises_abi_and_provenance_loader() {
    let python = match Command::new("python3").arg("--version").output() {
        Ok(output) if output.status.success() => output,
        Err(error) if error.kind() == io::ErrorKind::NotFound => return,
        Ok(output) => panic!(
            "python3 is unavailable: {}",
            String::from_utf8_lossy(&output.stderr)
        ),
        Err(error) => panic!("failed to probe python3: {error}"),
    };
    drop(python);

    let temp = TempDir::new();
    write_runtime(&temp.path);
    let implementation_dir = temp.path.join("_cott_impl/demo");
    fs::create_dir_all(&implementation_dir).expect("implementation directory should be writable");
    let good = b"def run() -> int:\n    return 7\n";
    let bad = b"raise ValueError('ordinary failure')\n";
    fs::write(implementation_dir.join("run.py"), good).expect("binding should be writable");
    fs::write(implementation_dir.join("bad.py"), bad).expect("bad binding should be writable");
    let good_hash = sha256_hex(good);
    let bad_hash = sha256_hex(bad);

    let script = format!(
        r#"from cott_runtime import *
from cott_runtime import _cott_load, _cott_normalize_scalar

assert I8.__metadata__[0] == CottInt("signed", 8)
assert U64.__metadata__[0] == CottInt("unsigned", 64)
assert _cott_normalize_scalar(1.25, F32) == 1.25
assert CottList(values=[1, 2]) != [1, 2]
assert CottSet(values=[1, 2]) != {{1, 2}}
assert FrozenMap(values={{"a": 1}}) != {{"a": 1}}
assert CottTuple2(first=1, second="x")[0] == 1
assert hash(CottTuple2(first=1, second="x"))
assert Unit() is UNIT
assert Nothing() == Nothing()

run = _cott_load("_cott_impl/demo/run.py", "{good_hash}", "run", "demo")
assert run() == 7
try:
    _cott_load("_cott_impl/demo/run.py", "{good_hash}", "run", "other")
except CottContractViolation as error:
    assert error.phase == "facade-import"
else:
    raise AssertionError("project mismatch was accepted")
try:
    _cott_load("_cott_impl/demo/run.py", "{{:064x}}", "run", "demo")
except CottContractViolation as error:
    assert error.phase == "provenance"
else:
    raise AssertionError("tampered hash was accepted")
try:
    _cott_load("_cott_impl/demo/bad.py", "{bad_hash}", "bad", "demo")
except CottContractViolation as error:
    assert error.phase == "implementation-load"
    assert isinstance(error.__cause__, ValueError)
else:
    raise AssertionError("ordinary implementation failure was not wrapped")
"#,
        good_hash = good_hash,
        bad_hash = bad_hash,
    );
    let output = Command::new("python3")
        .arg("-c")
        .arg(script)
        .current_dir(&temp.path)
        .output()
        .expect("python3 should execute generated runtime");
    assert!(
        output.status.success(),
        "generated runtime failed:\n{}\n{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}
