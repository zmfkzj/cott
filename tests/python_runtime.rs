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
    fs::write(
        temp.path.join("support.py"),
        b"def helper() -> int:\n    return 6\n",
    )
    .expect("generated facade should be writable");
    let good = b"from support import helper\n\n\ndef run() -> int:\n    return helper() + 1\n";
    let bad = b"raise ValueError('ordinary failure')\n";
    let external =
        b"from cott_missing_types import value\n\n\ndef external() -> object:\n    return value\n";
    fs::write(implementation_dir.join("run.py"), good).expect("binding should be writable");
    fs::write(implementation_dir.join("bad.py"), bad).expect("bad binding should be writable");
    fs::write(implementation_dir.join("external.py"), external)
        .expect("external binding should be writable");
    let good_hash = sha256_hex(good);
    let bad_hash = sha256_hex(bad);
    let external_hash = sha256_hex(external);

    let script = format!(
        r#"from pathlib import Path
import dataclasses
import hashlib
import json
import platform
import sys
import sysconfig
from typing import Generic, Literal, TypeVar

import cott_runtime as _runtime
from cott_runtime import *
from cott_runtime import _cott_load, _cott_normalize_f32_abi, _cott_normalize_scalar, _cott_validate_abi

_T = TypeVar("_T")
@dataclasses.dataclass(frozen=True)
class Box(Generic[_T]):
    value: _T
normalized = _cott_normalize_f32_abi(Box(1.234567), Box[F32])
assert normalized.value == _runtime._cott_normalize_f32(1.234567)

_good = dict(cott_symbol="demo.run", owner="manifest", python_symbol="_cott_impl.demo.run:run", source_origin="python/cott_bindings/demo/run.py", runtime_origin="_cott_impl/demo/run.py", content_hash="sha256:{good_hash}")
_bad = dict(cott_symbol="demo.bad", owner="manifest", python_symbol="_cott_impl.demo.bad:bad", source_origin="python/cott_bindings/demo/bad.py", runtime_origin="_cott_impl/demo/bad.py", content_hash="sha256:{bad_hash}")
_external = dict(cott_symbol="demo.external", owner="manifest", python_symbol="_cott_impl.demo.external:external", source_origin="python/cott_bindings/demo/external.py", runtime_origin="_cott_impl/demo/external.py", content_hash="sha256:{external_hash}")
_current = dict(generation_id="", verified=True, inputs={{}}, tools=dict(
    python=dict(implementation=sys.implementation.name, version=platform.python_version(), cache_tag=sys.implementation.cache_tag, os=sys.platform, machine=platform.machine(), platform=sysconfig.get_platform(), executable=str(Path(sys.executable).resolve()), content_hash="sha256:"+hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest()),
    runtime=dict(abi=_runtime._COTT_RUNTIME_ABI, version=_runtime._COTT_RUNTIME_VERSION),
), ir={{}}, contract_surface={{}}, public_python_symbols={{"demo":["bad","external","run"],"support":["helper"]}}, implementations=[_good, _bad, _external], dependencies=[], managed_files={{}}, unresolved=[], verification=None, agent_runs=[])
_identity = dict(_current)
for _key in ("generation_id", "verified", "verification", "agent_runs"):
    _identity.pop(_key)
_current["generation_id"] = "sha256:" + hashlib.sha256(json.dumps(_identity, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode() + b"\n").hexdigest()
Path("generation.json").write_text(json.dumps(dict(schema_version=1, current=_current, last_verified=None), sort_keys=True, separators=(",", ":")) + "\n")

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
assert _cott_validate_abi(Path("/tmp"), Path) == Path("/tmp")
assert _cott_validate_abi(Opaque(tag="token", value=object()), Opaque[Literal["token"]]).tag == "token"
try:
    _cott_validate_abi(Opaque(tag="other", value=object()), Opaque[Literal["token"]])
except CottContractViolation as error:
    assert error.phase == "validation"
else:
    raise AssertionError("mismatched Opaque tag was accepted")
class DerivedPath(type(Path())):
    pass
try:
    _cott_validate_abi(DerivedPath("/tmp"), Path)
except CottContractViolation:
    pass
else:
    raise AssertionError("Path subclass was accepted")

run = _cott_load("_cott_impl/demo/run.py", "{good_hash}", "run", "demo")
assert run() == 7
try:
    _cott_load("_cott_impl/demo/external.py", "{external_hash}", "external", "demo")
except CottContractViolation as error:
    assert error.phase == "provenance"
else:
    raise AssertionError("unrecorded external dependency was accepted")
try:
    _cott_load("_cott_impl/demo/run.py", "{good_hash}", "run", "other")
except CottContractViolation as error:
    assert error.phase == "facade-import"
else:
    raise AssertionError("project mismatch was accepted")
_original_generation = Path("generation.json").read_text()
_mutated = json.loads(_original_generation)
_mutated["current"]["tools"]["python"]["version"] = "0.0.0"
_mutated_identity = dict(_mutated["current"])
for _key in ("generation_id", "verified", "verification", "agent_runs"):
    _mutated_identity.pop(_key)
_mutated["current"]["generation_id"] = "sha256:" + hashlib.sha256(json.dumps(_mutated_identity, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode() + b"\n").hexdigest()
Path("generation.json").write_text(json.dumps(_mutated, sort_keys=True, separators=(",", ":")) + "\n")
try:
    _cott_load("_cott_impl/demo/bad.py", "{bad_hash}", "bad", "demo")
except CottContractViolation as error:
    assert error.phase == "provenance"
else:
    raise AssertionError("runtime identity mismatch was accepted")
finally:
    Path("generation.json").write_text(_original_generation)
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
        external_hash = external_hash,
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
