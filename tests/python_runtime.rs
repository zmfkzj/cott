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
    for (relative, bytes) in render_runtime("demo", "0.3.0") {
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
    let method_dir = implementation_dir.join("CounterState");
    fs::create_dir_all(&method_dir).expect("method helper directory should be writable");
    let method = b"def _cott_impl_CounterState_advance(self: object, amount: int) -> int:\n    return amount\n";
    fs::write(method_dir.join("advance.py"), method).expect("method helper should be writable");
    let good_hash = sha256_hex(good);
    let bad_hash = sha256_hex(bad);
    let external_hash = sha256_hex(external);
    let method_hash = sha256_hex(method);

    let script = format!(
        r#"from pathlib import Path
import dataclasses
import hashlib
import json
import platform
import sys
import sysconfig
from collections.abc import Generator, Iterator
from typing import Annotated, Any, Generic, Literal, Protocol, TypeVar

import cott_runtime as _runtime
from cott_runtime import *
from cott_runtime import _cott_load, _cott_normalize_f32_abi, _cott_normalize_scalar, _cott_validate_abi
assert "CottExternal" in _runtime.__all__
assert _runtime.PROJECT_VERSION == "0.3.0"


_T = TypeVar("_T")
@dataclasses.dataclass(frozen=True)
class Box(Generic[_T]):
    value: _T
normalized = _cott_normalize_f32_abi(Box(1.234567), Box[F32])
assert normalized.value == _runtime._cott_normalize_f32(1.234567)

_good = dict(cott_symbol="demo.run", kind="function", concrete=None, method=None, owner="manifest", python_symbol="_cott_impl.demo.run:run", source_origin="python/cott_bindings/demo/run.py", runtime_origin="_cott_impl/demo/run.py", content_hash="sha256:{good_hash}")
_bad = dict(cott_symbol="demo.bad", kind="function", concrete=None, method=None, owner="manifest", python_symbol="_cott_impl.demo.bad:bad", source_origin="python/cott_bindings/demo/bad.py", runtime_origin="_cott_impl/demo/bad.py", content_hash="sha256:{bad_hash}")
_external = dict(cott_symbol="demo.external", kind="function", concrete=None, method=None, owner="manifest", python_symbol="_cott_impl.demo.external:external", source_origin="python/cott_bindings/demo/external.py", runtime_origin="_cott_impl/demo/external.py", content_hash="sha256:{external_hash}")
_method = dict(cott_symbol="demo.CounterState.advance", kind="impl_method", concrete="CounterState", method="advance", owner="agent", python_symbol="_cott_impl.demo.CounterState.advance:_cott_impl_CounterState_advance", source_origin="python/_cott_impl/demo/CounterState/advance.py", runtime_origin="_cott_impl/demo/CounterState/advance.py", content_hash="sha256:{method_hash}")
_async = dict(cott_symbol="demo.async_run", kind="async_function", concrete=None, method=None, owner="agent", python_symbol="_cott_impl.demo.async_run:async_run", source_origin="python/cott_bindings/demo/async_run.py", runtime_origin="_cott_impl/demo/async_run.py", content_hash="sha256:{good_hash}")
_unresolved = dict(cott_symbol="demo.missing", kind="async_function", span=dict(start_byte=1, end_byte=2, start_line=1, start_column=1, end_line=1, end_column=2))
def _generation_id(current: dict) -> str:
    identity = dict(current)
    for key in ("generation_id", "verified", "verification", "agent_runs"):
        identity.pop(key)
    payload = dict(domain="cott.generation.v2", schema_version=2, current=identity)
    return "sha256:" + hashlib.sha256(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode() + b"\n").hexdigest()

_current = dict(generation_id="", verified=True, project_version="0.3.0", compatibility=dict(
    generation_schema=2, canonical_ir_schema=5, runtime_abi=2,
), inputs={{}}, tools=dict(
    python=dict(implementation=sys.implementation.name, version=platform.python_version(), cache_tag=sys.implementation.cache_tag, os=sys.platform, machine=platform.machine(), platform=sysconfig.get_platform(), executable=str(Path(sys.executable).resolve()), content_hash="sha256:"+hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest()),
    runtime=dict(abi=_runtime._COTT_RUNTIME_ABI, version=_runtime._COTT_RUNTIME_VERSION),
), ir={{}}, contract_surface={{}}, public_python_symbols={{"demo":["CounterState","bad","external","run"],"support":["helper"]}}, implementations=[_good, _bad, _external, _method, _async], dependencies=[], managed_files={{}}, unresolved=[_unresolved], verification=None, agent_runs=[])
_current["generation_id"] = _generation_id(_current)
Path("generation.json").write_text(json.dumps(dict(schema_version=2, current=_current, last_verified=None), sort_keys=True, separators=(",", ":")) + "\n")
assert _runtime._cott_validate_generation_snapshot(_current, "current") is _current
_invalid_unresolved = dict(_current)
_invalid_unresolved["unresolved"] = [dict(_unresolved, span=dict(_unresolved["span"], end_line=0))]
try:
    _runtime._cott_validate_generation_snapshot(_invalid_unresolved, "invalid unresolved")
except CottContractViolation:
    pass
else:
    raise AssertionError("invalid unresolved record was accepted")
_legacy = dict(_current)
_legacy["implementations"] = [dict(_good)]
del _legacy["implementations"][0]["kind"]
try:
    _runtime._cott_validate_generation_snapshot(_legacy, "legacy")
except CottContractViolation:
    pass
else:
    raise AssertionError("legacy implementation record was accepted")

assert I8.__metadata__[0] == CottInt("signed", 8)
assert U64.__metadata__[0] == CottInt("unsigned", 64)
assert _cott_normalize_scalar(1.25, F32) == 1.25
assert CottList(values=[1, 2]) != [1, 2]
assert CottSet(values=[1, 2]) != {{1, 2}}
assert FrozenMap(values={{"a": 1}}) != {{"a": 1}}
_tuple = (1, "x")
assert _cott_validate_abi(_tuple, tuple[I32, str]) == _tuple
assert hash(_tuple)
assert Unit() is UNIT
assert Nothing() == Nothing()
assert _cott_validate_abi(Path("/tmp"), Path) == Path("/tmp")
_client_session_value: U64 = 1
_client_session: Opaque[Literal["client_session"]] = Opaque(tag="client_session", value=_client_session_value)
assert Opaque.__annotations__["value"] == "object"
assert _client_session.unwrap() is _client_session_value
assert _cott_validate_abi(Opaque(tag="token", value=object()), Opaque[Literal["token"]]).tag == "token"
try:
    _cott_validate_abi(Opaque(tag="other", value=object()), Opaque[Literal["token"]])
except CottContractViolation as error:
    assert error.phase == "validation"
else:
    raise AssertionError("mismatched Opaque tag was accepted")
class _PoisonIterator:
    def __iter__(self):
        return self

    def __next__(self):
        raise AssertionError("ABI traversal advanced an iterator")


def _poison_generator():
    raise AssertionError("ABI traversal advanced a generator")
    yield None


_poison_iterator = _PoisonIterator()
assert _cott_validate_abi(_poison_iterator, Iterator[int]) is _poison_iterator
assert _cott_normalize_f32_abi(_poison_iterator, Iterator[F32]) is _poison_iterator
_poison_generator_value = _poison_generator()
assert _cott_validate_abi(_poison_generator_value, Generator[int, None, None]) is _poison_generator_value
assert _cott_normalize_f32_abi(_poison_generator_value, Generator[F32, None, None]) is _poison_generator_value


class _External:
    pass


_external_metadata = CottExternal("support:_External")
try:
    _external_metadata.path = "other:_External"
except dataclasses.FrozenInstanceError:
    pass
else:
    raise AssertionError("CottExternal metadata is mutable")
_external_value = _External()
_external_annotation = Annotated[_External, _external_metadata]
assert _cott_validate_abi(_external_value, _external_annotation) is _external_value
assert _cott_normalize_f32_abi(_external_value, _external_annotation) is _external_value
try:
    _cott_validate_abi(object(), _external_annotation)
except CottContractViolation as error:
    assert error.phase == "validation"
else:
    raise AssertionError("wrong external class was accepted")
class _ExternalProtocol(Protocol):
    def required(self) -> None: ...


_static_external = object()
assert _cott_validate_abi(_static_external, Annotated[_ExternalProtocol, CottExternal("support:_ExternalProtocol")]) is _static_external

_untyped = object()
assert _cott_validate_abi(_untyped, Any) is _untyped
assert _cott_normalize_f32_abi(_untyped, Any) is _untyped
assert _cott_validate_abi(_untyped, object) is _untyped
assert _cott_normalize_f32_abi(_untyped, object) is _untyped

class _FactoryConcrete:
    def __init__(self):
        raise AssertionError("Factory validation constructed the concrete class")


class _FactorySubclass(_FactoryConcrete):
    pass


_factory_annotation = type[_FactoryConcrete]
assert _cott_validate_abi(_FactoryConcrete, _factory_annotation) is _FactoryConcrete
for _invalid_factory in (
    object.__new__(_FactoryConcrete),
    _FactorySubclass,
    str,
    lambda: _FactoryConcrete,
):
    try:
        _cott_validate_abi(_invalid_factory, _factory_annotation)
    except CottContractViolation as error:
        assert error.phase == "validation"
    else:
        raise AssertionError("invalid Factory value was accepted")

_nested_opaque = Opaque(tag="token", value=object())
assert _cott_validate_abi(Box(_nested_opaque), Box[Opaque[Literal["token"]]]).value is _nested_opaque
try:
    _cott_validate_abi(Box(Opaque(tag="other", value=object())), Box[Opaque[Literal["token"]]])
except CottContractViolation as error:
    assert error.phase == "validation"
else:
    raise AssertionError("nested mismatched Opaque tag was accepted")
class DerivedPath(type(Path())):
    pass
try:
    _cott_validate_abi(DerivedPath("/tmp"), Path)
except CottContractViolation:
    pass
else:
    raise AssertionError("Path subclass was accepted")

method_helper = _cott_load("_cott_impl/demo/CounterState/advance.py", "{method_hash}", "_cott_impl_CounterState_advance", "demo", expected_cott_symbol="demo.CounterState.advance")
assert method_helper(object(), 2) == 2
run = _cott_load("_cott_impl/demo/run.py", "{good_hash}", "run", "demo")
assert run() == 7
_reader = _runtime._cott_regular_file_bytes
def _unexpected_read(*args: object) -> bytes:
    raise AssertionError("cached loader read a file")
_runtime._cott_regular_file_bytes = _unexpected_read
assert _cott_load("_cott_impl/demo/run.py", "{good_hash}", "run", "demo") is run
_runtime._cott_regular_file_bytes = _reader
_dependency_source = Path("dependency-source.bin").resolve()
_dependency_link = Path("dependency-link.bin").resolve()
_dependency_source.write_bytes(b"dependency")
_dependency_link.hardlink_to(_dependency_source)
assert _runtime._cott_dependency_file_bytes(_dependency_link, "dependency file") == b"dependency"
try:
    _runtime._cott_regular_file_bytes(_dependency_link, "managed file")
except CottContractViolation:
    pass
else:
    raise AssertionError("managed hardlink was accepted")
_run_path = Path("_cott_impl/demo/run.py")
_run_path.write_bytes(_run_path.read_bytes() + b'\x23 changed\n')
try:
    _cott_load("_cott_impl/demo/run.py", "{good_hash}", "run", "demo")
except CottContractViolation as error:
    assert error.phase == "provenance"
else:
    raise AssertionError("modified cached implementation was accepted")
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
def _reject_generation(record: object, label: str) -> None:
    Path("generation.json").write_text(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    try:
        _cott_load("_cott_impl/demo/bad.py", "{bad_hash}", "bad", "demo")
    except CottContractViolation as error:
        assert error.phase == "provenance", (label, error.phase)
    else:
        raise AssertionError(f"{{label}} generation record was accepted")
    finally:
        Path("generation.json").write_text(_original_generation)
_original_generation = Path("generation.json").read_text()
_v1 = json.loads(_original_generation)
_v1["schema_version"] = 1
_reject_generation(_v1, "v1")
_missing = json.loads(_original_generation)
del _missing["current"]["project_version"]
_reject_generation(_missing, "missing")
_extra = json.loads(_original_generation)
_extra["current"]["unexpected"] = None
_reject_generation(_extra, "extra")
_incompatible = json.loads(_original_generation)
_incompatible["current"]["compatibility"]["runtime_abi"] = 1
_incompatible["current"]["generation_id"] = _generation_id(_incompatible["current"])
_reject_generation(_incompatible, "compatibility")
_version_mismatch = json.loads(_original_generation)
_version_mismatch["current"]["project_version"] = "0.3.1"
_version_mismatch["current"]["generation_id"] = _generation_id(_version_mismatch["current"])
_reject_generation(_version_mismatch, "project version")
_original_generation = Path("generation.json").read_text()
_mutated = json.loads(_original_generation)
_mutated["current"]["tools"]["python"]["version"] = "0.0.0"
_mutated["current"]["generation_id"] = _generation_id(_mutated["current"])
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
        method_hash = method_hash,
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

#[test]
fn generated_runtime_strictly_validates_variadic_tuples_arrays_and_buffers() {
    if Command::new("python3").arg("--version").output().is_err() {
        return;
    }

    let temp = TempDir::new();
    write_runtime(&temp.path);
    let script = r#"
from typing import Literal
from cott_runtime import CottArray, CottBuffer, CottContractViolation, I32, _cott_validate_abi

array = CottArray(values=(1, 2))
assert tuple(array) == (1, 2)
assert _cott_validate_abi(array, CottArray[I32, Literal[2]]) == array
for value in ((1, 2), CottArray(values=(1, 2, 3)), CottArray(values=(1, "two"))):
    try:
        _cott_validate_abi(value, CottArray[I32, Literal[2]])
    except CottContractViolation:
        pass
    else:
        raise AssertionError("array ABI accepted an invalid value")

assert _cott_validate_abi((1, "two"), tuple[I32, str]) == (1, "two")
for value in ((), (1, 2), (1, "two", 3)):
    try:
        _cott_validate_abi(value, tuple[I32, str])
    except CottContractViolation:
        pass
    else:
        raise AssertionError("positional tuple ABI accepted an invalid value")

buffer = CottBuffer(data=b"\x00\xff")
assert _cott_validate_abi(buffer, CottBuffer[Literal[2]]) == buffer
for value in (b"\x00\xff", CottBuffer(data=b"\x00")):
    try:
        _cott_validate_abi(value, CottBuffer[Literal[2]])
    except CottContractViolation:
        pass
    else:
        raise AssertionError("buffer ABI accepted an invalid value")
try:
    CottBuffer(data="not-bytes")
except CottContractViolation:
    pass
else:
    raise AssertionError("buffer constructor accepted non-bytes")
"#;
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
