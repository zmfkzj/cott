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
fn runtime_authenticates_namespace_import_origins_before_execution() {
    let temp = TempDir::new();
    write_runtime(&temp.path);
    let script = r#"
import copy
import hashlib
from pathlib import Path
import sys
from cott_runtime import CottContractViolation, _cott_validate_dependencies

root = Path.cwd()
def install(name, files):
    metadata = f"Metadata-Version: 2.4\nName: {name}\nVersion: 1.0.0\n\n"
    info = root / (name.replace("-", "_") + "-1.0.0.dist-info")
    info.mkdir()
    (info / "METADATA").write_text(metadata)
    (info / "top_level.txt").write_text("cott_test_namespace\n")
    (info / "RECORD").write_text("".join(f"{path},,\n" for path in files))
    origins = []
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        origins.append({"path": relative, "content_hash": "sha256:" + hashlib.sha256(content.encode()).hexdigest()})
    return {"name": name, "version": "1.0.0", "installed": {"version": "1.0.0", "metadata_hash": "sha256:" + hashlib.sha256(metadata.encode()).hexdigest(), "origins": origins, "imports": ["cott_test_namespace"]}}

initializer = "raise RuntimeError('unauthenticated package initializer ran')\n"
sdk = install("selected-driver", {
    "cott_test_namespace/sdk/__init__.py": initializer,
    "cott_test_namespace/sdk/client.py": "value = 42\n",
})
other = install("unselected-driver", {"cott_test_namespace/other/__init__.py": "value = 99\n"})
source = b"from cott_test_namespace import sdk\nfrom cott_test_namespace.sdk.client import value\n"
_cott_validate_dependencies([sdk], source, {})
assert "cott_test_namespace.sdk" not in sys.modules

def rejected(dependencies, source):
    try:
        _cott_validate_dependencies(dependencies, source, {})
    except CottContractViolation:
        return
    raise AssertionError("unauthenticated external import was accepted")

rejected([sdk], b"from cott_test_namespace import other\n")
rejected([sdk], b"import cott_test_namespace\n")
# A production lock identity without installed evidence is accepted beside the imports it does
# not serve, but never authorizes an import that needs observed provenance.
_cott_validate_dependencies([sdk, {"name": "unimported-driver", "version": "3.0.0"}], source, {})
rejected([{"name": "selected-driver", "version": "1.0.0"}], source)
import types
fake = types.ModuleType("cott_test_namespace.sdk")
fake.__file__ = str(root / "untrusted.py")
sys.modules[fake.__name__] = fake
rejected([sdk], source)
del sys.modules[fake.__name__]
missing_parent = copy.deepcopy(sdk)
missing_parent["installed"]["origins"] = missing_parent["installed"]["origins"][1:]
rejected([missing_parent], source)
path = root / "cott_test_namespace/sdk/client.py"
path.write_text("value = 43\n")
rejected([sdk], source)
path.write_text("value = 42\n")
conflict = install("conflicting-driver", {"cott_test_namespace/sdk/client.py": "value = 42\n"})
rejected([sdk, conflict], source)
"#;
    let output = match Command::new("python3")
        .args(["-c", script])
        .current_dir(&temp.path)
        .output()
    {
        Ok(output) => output,
        Err(error) if error.kind() == io::ErrorKind::NotFound => return,
        Err(error) => panic!("failed to execute runtime ownership regression: {error}"),
    };
    assert!(
        output.status.success(),
        "runtime dependency ownership failed:\n{}",
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn snapshot_digests_match_rust_for_all_json_types() {
    let temp = TempDir::new();
    write_runtime(&temp.path);
    let values = [
        serde_json::json!(null),
        serde_json::json!(false),
        serde_json::json!(true),
        serde_json::json!(i64::MIN),
        serde_json::json!(u64::MAX),
        serde_json::json!(0),
        serde_json::json!(0.0),
        serde_json::json!(-0.0),
        serde_json::json!(1.0),
        serde_json::json!(1e-200),
        serde_json::json!(1e200),
        serde_json::json!(f64::from_bits(1)),
        serde_json::json!({"é": ["λ", "😀", "\0", -17, 0.125], "a": {}}),
    ];
    let vectors = values
        .iter()
        .map(|value| {
            serde_json::json!({
                "value": value,
                "digest": cott::snapshot_record::digest(value).expect("valid snapshot value"),
            })
        })
        .collect::<Vec<_>>();
    let output = match Command::new("python3")
        .args([
            "-c",
            "import json, sys, cott_runtime\nfor vector in json.loads(sys.argv[1]):\n    actual = cott_runtime._cott_snapshot_digest(vector['value'])\n    assert actual == vector['digest'], (vector, actual)\n",
            &serde_json::to_string(&vectors).expect("digest vectors JSON"),
        ])
        .current_dir(&temp.path)
        .output()
    {
        Ok(output) => output,
        Err(error) if error.kind() == io::ErrorKind::NotFound => return,
        Err(error) => panic!("failed to execute Python digest vectors: {error}"),
    };
    assert!(
        output.status.success(),
        "Python snapshot digest mismatch:\n{}",
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn rust_generation_with_float_tool_metadata_loads_in_python() {
    use cott::provenance::{
        GENERATION_SCHEMA_VERSION, GenerationCompatibility, GenerationRecord, GenerationSnapshot,
        SemanticCoverage,
    };

    let temp = TempDir::new();
    write_runtime(&temp.path);
    let probe = match Command::new("python3")
        .args([
            "-c",
            "import json, platform, sys, sysconfig; print(json.dumps(dict(implementation=sys.implementation.name,version=platform.python_version(),cache_tag=sys.implementation.cache_tag,os=sys.platform,machine=platform.machine(),platform=sysconfig.get_platform())))",
        ])
        .output()
    {
        Ok(output) => output,
        Err(error) if error.kind() == io::ErrorKind::NotFound => return,
        Err(error) => panic!("failed to probe Python identity: {error}"),
    };
    assert!(probe.status.success(), "Python identity probe failed");
    let python: serde_json::Value = serde_json::from_slice(&probe.stdout).expect("Python identity");
    let source = b"def run():\n    return 42\n";
    let digest = sha256_hex(source);
    let implementation = temp.path.join("_cott_impl/demo/run.py");
    fs::create_dir_all(implementation.parent().unwrap()).expect("implementation parent");
    fs::write(&implementation, source).expect("implementation source");
    let mut current = GenerationSnapshot {
        generation_id: String::new(),
        verified: false,
        project_version: "0.3.0".to_owned(),
        compatibility: GenerationCompatibility::current(),
        inputs: serde_json::json!({}),
        tools: serde_json::json!({
            "python": python,
            "runtime": {"abi": "7", "version": env!("CARGO_PKG_VERSION")},
            "numeric_metadata": [1e-7, 1e20, -0.0, f64::from_bits(1), i64::MIN, u64::MAX],
        }),
        ir: serde_json::json!({}),
        contract_surface: serde_json::json!({}),
        public_python_symbols: serde_json::json!({"demo": ["run"]}),
        implementations: serde_json::json!([{
            "cott_symbol": "demo.run", "kind": "function", "callable_kind": "sync",
            "concrete": null, "method": null, "selection": null, "owner": "manifest",
            "python_symbol": "_cott_impl.demo.run:run",
            "source_origin": "python/cott_bindings/demo/run.py",
            "runtime_origin": "_cott_impl/demo/run.py", "content_hash": format!("sha256:{digest}"),
        }]),
        dependencies: serde_json::json!([]),
        managed_files: Default::default(),
        unresolved: vec![],
        verification: serde_json::Value::Null,
        semantic_coverage: SemanticCoverage::default(),
        agent_runs: vec![],
    };
    current
        .compute_generation_id()
        .expect("structural generation identity");
    let record = GenerationRecord {
        schema_version: GENERATION_SCHEMA_VERSION,
        current,
        last_verified: None,
    };
    fs::write(
        temp.path.join("generation.json"),
        record.canonical_bytes().expect("Rust generation record"),
    )
    .expect("generation file");
    let output = Command::new("python3")
        .args([
            "-c",
            "import sys; from cott_runtime import _cott_load; assert _cott_load('_cott_impl/demo/run.py', sys.argv[1], 'run', 'demo', expected_cott_symbol='demo.run')() == 42",
            &digest,
        ])
        .current_dir(&temp.path)
        .output()
        .expect("Python generation loader");
    assert!(
        output.status.success(),
        "Python rejected Rust floating-point generation metadata:\n{}",
        String::from_utf8_lossy(&output.stderr)
    );
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
import asyncio
import dataclasses
import hashlib
import json
import platform
import sys
import sysconfig
from collections.abc import AsyncGenerator as _PyAsyncGenerator, AsyncIterator as _PyAsyncIterator, Generator, Iterator
from typing import Annotated, Any, Generic, Literal, Protocol, TypeVar, Union

import cott_runtime as _runtime
from cott_runtime import *
from cott_runtime import _cott_load, _cott_normalize_f32_abi, _cott_normalize_scalar, _cott_validate_abi, _cott_wrap_async_protocol
assert set(_runtime.__all__) == {{
    "AsyncGenerator", "AsyncIterator", "CottArray", "CottBuffer", "CottContractViolation", "CottExternal", "CottFloat", "CottInt", "CottList", "CottSet", "Dyn", "Err", "F32", "F64", "FrozenMap",
    "I8", "I16", "I32", "I64", "JsonArray", "JsonBoolean", "JsonFloat", "JsonInteger", "JsonNull", "JsonObject", "JsonString", "JsonValue",
    "Never", "Nothing", "Ok", "Opaque", "Option", "PROJECT_NAME", "PROJECT_VERSION", "Result", "Some", "U8", "U16", "U32", "U64", "UNIT", "Unit",
}}
assert "_cott_fixture_activate" not in _runtime.__all__
assert _runtime.PROJECT_VERSION == "0.3.0"
try:
    __import__("_cott_impl.demo.run")
except ModuleNotFoundError:
    pass
else:
    raise AssertionError("private implementation package was importable")
assert _runtime._cott_coverage_key("demo.State", "modifies:demo.State.value") == ("demo.State", 3, 0, "demo.State.value")
assert _runtime._cott_coverage_key("demo.State", "modifies:demo..value") is None


_T = TypeVar("_T")
_N = TypeVar("_N")
assert _runtime._cott_substitute_type(CottBuffer[Literal[_N]], {{_N: Literal[4]}}) == CottBuffer[Literal[4]]
@dataclasses.dataclass(frozen=True)
class Box(Generic[_T]):
    value: _T
normalized = _cott_normalize_f32_abi(Box(1.234567), Box[F32])
assert normalized.value == _runtime._cott_normalize_f32(1.234567)

@dataclasses.dataclass(frozen=True)
class Node:
    value: F32
    next: "Option[Node]"

@dataclasses.dataclass(frozen=True)
class Pair:
    left: "Option[Node]"
    right: "Option[Node]"

_leaf = Node(1.234567, Nothing())
_finite = Node(1.234567, Some(value=_leaf))
_normalized_finite = _cott_validate_abi(_finite, Node)
assert _normalized_finite.value == _runtime._cott_normalize_f32(1.234567)
assert _normalized_finite.next.value.value == _runtime._cott_normalize_f32(1.234567)
_shared = Pair(Some(value=_leaf), Some(value=_leaf))
_normalized_shared = _cott_normalize_f32_abi(_shared, Pair)
assert _normalized_shared.left.value is _normalized_shared.right.value
_cyclic = Node(1.0, Nothing())
object.__setattr__(_cyclic, "next", Some(value=_cyclic))
for _traverse in (_cott_validate_abi, _cott_normalize_f32_abi):
    try:
        _traverse(_cyclic, Node)
    except CottContractViolation as error:
        assert "active value cycle" in error.message
        assert "$.next.value" in error.message
    else:
        raise AssertionError("cyclic recursive value was accepted")
_deep = Node(1.0, Nothing())
for _ in range(70):
    _deep = Node(1.0, Some(value=_deep))
try:
    _cott_validate_abi(_deep, Node)
except CottContractViolation as error:
    assert "depth 64" in error.message
else:
    raise AssertionError("deep recursive value was accepted")
_many = CottList(values=range(1025))
try:
    _cott_validate_abi(_many, CottList[I32])
except CottContractViolation as error:
    assert "node limit 1024" in error.message
else:
    raise AssertionError("wide ABI value was accepted")
for _key in ("active value cycle", "exceeds ABI traversal"):
    _map = FrozenMap(values={{_key: "ok"}})
    assert _cott_validate_abi(_map, FrozenMap[str, Union[bytes, str]]) == _map
_json_cycle = JsonArray(value=CottList(values=[JsonNull()]))
object.__setattr__(_json_cycle, "value", CottList(values=[_json_cycle]))
try:
    _runtime._cott_validate_json(_json_cycle)
except CottContractViolation as error:
    assert "active value cycle" in error.message
else:
    raise AssertionError("cyclic JsonValue was accepted")

_good = dict(cott_symbol="demo.run", kind="function", callable_kind="sync", concrete=None, method=None, selection=None, owner="manifest", python_symbol="_cott_impl.demo.run:run", source_origin="python/cott_bindings/demo/run.py", runtime_origin="_cott_impl/demo/run.py", content_hash="sha256:{good_hash}")
_bad = dict(cott_symbol="demo.bad", kind="function", callable_kind="sync", concrete=None, method=None, selection=None, owner="manifest", python_symbol="_cott_impl.demo.bad:bad", source_origin="python/cott_bindings/demo/bad.py", runtime_origin="_cott_impl/demo/bad.py", content_hash="sha256:{bad_hash}")
_external = dict(cott_symbol="demo.external", kind="function", callable_kind="sync", concrete=None, method=None, selection=None, owner="manifest", python_symbol="_cott_impl.demo.external:external", source_origin="python/cott_bindings/demo/external.py", runtime_origin="_cott_impl/demo/external.py", content_hash="sha256:{external_hash}")
_method = dict(cott_symbol="demo.CounterState.advance", kind="impl_method", callable_kind="sync", concrete="CounterState", method="advance", selection=dict(kind="explicit", trait_method="demo.Counter.advance"), owner="agent", python_symbol="_cott_impl.demo.CounterState.advance:_cott_impl_CounterState_advance", source_origin="python/_cott_impl/demo/CounterState/advance.py", runtime_origin="_cott_impl/demo/CounterState/advance.py", content_hash="sha256:{method_hash}")
_async = dict(cott_symbol="demo.async_run", kind="async_function", callable_kind="async", concrete=None, method=None, selection=None, owner="agent", python_symbol="_cott_impl.demo.async_run:async_run", source_origin="python/cott_bindings/demo/async_run.py", runtime_origin="_cott_impl/demo/async_run.py", content_hash="sha256:{good_hash}")
_unresolved = dict(cott_symbol="demo.missing", kind="async_function", callable_kind="async", span=dict(start_byte=1, end_byte=2, start_line=1, start_column=1, end_line=1, end_column=2))
def _generation_id(current: dict) -> str:
    identity = dict(current)
    for key in ("generation_id", "verified", "verification", "semantic_coverage", "agent_runs"):
        identity.pop(key)
    payload = dict(domain="cott.generation.v8", schema_version=8, current=identity)
    return _runtime._cott_snapshot_digest(payload)

# Expanded views are test-only conveniences; every loader input uses the wire table.
def _pack_record(view: dict) -> dict:
    current = _runtime._cott_snapshot_digest(view["current"])
    snapshots = {{current: view["current"]}}
    last = view["last_verified"]
    last_verified = None if last is None else _runtime._cott_snapshot_digest(last)
    if last is not None:
        snapshots[last_verified] = last
    return dict(schema_version=view["schema_version"], current=current, last_verified=last_verified, snapshots=snapshots)

def _read_record(text: str) -> dict:
    wire = json.loads(text)
    current, last = _runtime._cott_resolve_generation_record(wire)
    return dict(schema_version=wire["schema_version"], current=current, last_verified=last)

_current = dict(generation_id="", verified=True, project_version="0.3.0", compatibility=dict(
    generation_schema=8, canonical_ir_schema=9, runtime_abi=7, contract_strategy_schema=6,
), inputs={{}}, tools=dict(
    python=dict(implementation=sys.implementation.name, version=platform.python_version(), cache_tag=sys.implementation.cache_tag, os=sys.platform, machine=platform.machine(), platform=sysconfig.get_platform(), executable=str(Path(sys.executable).resolve()), content_hash="sha256:"+hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest()),
    runtime=dict(abi=_runtime._COTT_RUNTIME_ABI, version=_runtime._COTT_RUNTIME_VERSION),
), ir={{}}, contract_surface={{}}, public_python_symbols={{"demo":["CounterState","bad","external","run"],"support":["helper"]}}, implementations=[_good, _bad, _external, _method, _async], dependencies=[], managed_files={{}}, unresolved=[_unresolved], verification=None, semantic_coverage=dict(clauses=[], summary=dict(observed=0, unobserved=0, trust_declaration=0, unknown=0), policy=dict(selected=0, passed=True, violations=[])), agent_runs=[])
_current["generation_id"] = _generation_id(_current)
_wire = _pack_record(dict(schema_version=8, current=_current, last_verified=_current))
assert _wire["current"] == _wire["last_verified"]
assert list(_wire["snapshots"]) == [_wire["current"]]
Path("generation.json").write_text(json.dumps(_wire, sort_keys=True, separators=(",", ":")) + "\n")
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

class _AsyncYieldOnce:
    def __init__(self):
        self.emitted = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.emitted:
            raise StopAsyncIteration
        await asyncio.sleep(0)
        self.emitted = True
        return 1.234567


class _AsyncValue:
    def __init__(self, value):
        self.value = value
        self.emitted = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.emitted:
            raise StopAsyncIteration
        self.emitted = True
        return self.value

async def _raw_async_generator():
    sent = yield 1.234567
    yield sent


class _GatedAsyncGenerator(_PyAsyncGenerator):
    def __init__(self, operation):
        self.operation = operation
        self.entered = asyncio.Event()
        self.release = asyncio.Event()

    async def _wait(self, operation):
        assert operation == self.operation
        self.entered.set()
        await self.release.wait()
        return 1.234567

    async def __anext__(self):
        return await self._wait("__anext__")

    async def asend(self, value):
        return await self._wait("asend")

    async def athrow(self, *args):
        return await self._wait("athrow")

    async def aclose(self):
        await self._wait("aclose")


class _CancelledThenValueIterator(_PyAsyncIterator):
    def __init__(self):
        self.calls = 0
        self.entered = asyncio.Event()

    async def __anext__(self):
        self.calls += 1
        if self.calls == 1:
            self.entered.set()
            await asyncio.Event().wait()
        return 1.234567


class _ExceptionThenValueIterator(_PyAsyncIterator):
    def __init__(self, error):
        self.calls = 0
        self.error = error

    async def __anext__(self):
        self.calls += 1
        if self.calls == 1:
            raise self.error
        return 1.234567


class _CloseRetryIterator(_PyAsyncIterator):
    def __init__(self, fail_first):
        self.fail_first = fail_first
        self.close_calls = 0
        self.error = RuntimeError("close failed")

    async def __anext__(self):
        raise StopAsyncIteration

    async def aclose(self):
        self.close_calls += 1
        if self.fail_first and self.close_calls == 1:
            raise self.error


async def _complete_async_generator():
    if False:
        yield 1.234567


async def _athrow_yields_invalid_value():
    try:
        yield 1.234567
    except ValueError:
        yield "not a float"

async def _exercise_async_runtime():
    lock = _runtime._CottAsyncRLock()
    entered = asyncio.Event()
    release = asyncio.Event()
    order = []

    async def holder():
        async with lock:
            async with lock:
                order.append("reentrant")
            entered.set()
            await release.wait()
            order.append("holder")

    async def contender():
        await entered.wait()
        async with lock:
            order.append("contender")

    async def unlock():
        await entered.wait()
        await asyncio.sleep(0)
        release.set()

    await asyncio.gather(holder(), contender(), unlock())
    assert order == ["reentrant", "holder", "contender"]

    raw_iterator = _AsyncYieldOnce()
    iterator = _cott_wrap_async_protocol(raw_iterator, AsyncIterator[F32])
    assert not raw_iterator.emitted
    results = await asyncio.gather(iterator.__anext__(), iterator.__anext__(), return_exceptions=True)
    assert any(isinstance(result, CottContractViolation) for result in results)
    assert any(result == _runtime._cott_normalize_f32(1.234567) for result in results if type(result) is float)
    await iterator.aclose()

    generator = _cott_wrap_async_protocol(_raw_async_generator(), AsyncGenerator[F32, F32])
    first = await generator.__anext__()
    second = await generator.asend(1.234567)
    assert first == _runtime._cott_normalize_f32(1.234567)
    assert second == _runtime._cott_normalize_f32(1.234567)
    await generator.aclose()

    async def assert_concurrency_guard(operation):
        raw = _GatedAsyncGenerator(operation)
        wrapped = _cott_wrap_async_protocol(raw, AsyncGenerator[F32, I32])
        if operation == "__anext__":
            pending = asyncio.create_task(wrapped.__anext__())
        elif operation == "asend":
            pending = asyncio.create_task(wrapped.asend(None))
        elif operation == "athrow":
            pending = asyncio.create_task(wrapped.athrow(ValueError))
        else:
            pending = asyncio.create_task(wrapped.aclose())
        await raw.entered.wait()
        try:
            await wrapped.asend("not an integer")
        except CottContractViolation as error:
            assert error.phase == "async-lifecycle"
        else:
            raise AssertionError(f"concurrent {{operation}} was accepted")
        raw.release.set()
        result = await pending
        if operation == "aclose":
            assert result is None
        else:
            assert result == _runtime._cott_normalize_f32(1.234567)

    for operation in ("__anext__", "asend", "athrow", "aclose"):
        await assert_concurrency_guard(operation)

    cancelled_raw = _CancelledThenValueIterator()
    cancelled = _cott_wrap_async_protocol(cancelled_raw, AsyncIterator[F32])
    pending = asyncio.create_task(cancelled.__anext__())
    await cancelled_raw.entered.wait()
    pending.cancel()
    try:
        await pending
    except asyncio.CancelledError:
        pass
    else:
        raise AssertionError("cancelled async iteration completed")
    assert await cancelled.__anext__() == _runtime._cott_normalize_f32(1.234567)

    ordinary_error = RuntimeError("ordinary async failure")
    ordinary = _cott_wrap_async_protocol(_ExceptionThenValueIterator(ordinary_error), AsyncIterator[F32])
    try:
        await ordinary.__anext__()
    except RuntimeError as error:
        assert error is ordinary_error
    else:
        raise AssertionError("ordinary async exception was not preserved")
    assert await ordinary.__anext__() == _runtime._cott_normalize_f32(1.234567)

    terminal = _cott_wrap_async_protocol(_complete_async_generator(), AsyncGenerator[F32, I32])
    try:
        await terminal.__anext__()
    except StopAsyncIteration:
        pass
    else:
        raise AssertionError("completed async generator yielded a value")
    for advance in (terminal.__anext__, lambda: terminal.asend(None), lambda: terminal.athrow(ValueError)):
        try:
            await advance()
        except StopAsyncIteration:
            pass
        else:
            raise AssertionError("completed async generator advanced")

    invalid_throw = _cott_wrap_async_protocol(_athrow_yields_invalid_value(), AsyncGenerator[F32, I32])
    assert await invalid_throw.__anext__() == _runtime._cott_normalize_f32(1.234567)
    try:
        await invalid_throw.athrow(ValueError)
    except CottContractViolation as error:
        assert error.phase == "validation"
    else:
        raise AssertionError("athrow yielded an invalid ABI value")
    await invalid_throw.aclose()

    retry_raw = _CloseRetryIterator(True)
    retry = _cott_wrap_async_protocol(retry_raw, AsyncIterator[F32])
    try:
        await retry.aclose()
    except RuntimeError as error:
        assert error is retry_raw.error
    else:
        raise AssertionError("failing close completed")
    await retry.aclose()
    assert retry_raw.close_calls == 2

    close_raw = _CloseRetryIterator(False)
    close_once = _cott_wrap_async_protocol(close_raw, AsyncIterator[F32])
    await close_once.aclose()
    await close_once.aclose()
    assert close_raw.close_calls == 1

    nested = _cott_wrap_async_protocol(Some(value=_AsyncValue(1.234567)), Option[AsyncIterator[F32]])
    assert await nested.value.__anext__() == _runtime._cott_normalize_f32(1.234567)
    boxed = _cott_wrap_async_protocol(
        Box(Some(value=_AsyncValue(1.234567))),
        Box[Option[AsyncIterator[F32]]],
    )
    assert await boxed.value.value.__anext__() == _runtime._cott_normalize_f32(1.234567)
    off = _cott_wrap_async_protocol(_AsyncValue(1.0), AsyncIterator[F32], validator=_cott_normalize_f32_abi)
    assert _cott_wrap_async_protocol(off, AsyncIterator[F32]) is not off
    assert await off.__anext__() == 1.0

    initial_send = _cott_wrap_async_protocol(_raw_async_generator(), AsyncGenerator[F32, I32])
    assert await initial_send.asend(None) == _runtime._cott_normalize_f32(1.234567)
    try:
        await initial_send.asend("not an integer")
    except CottContractViolation as error:
        assert error.phase == "validation"
    else:
        raise AssertionError("invalid async send was accepted")
    await initial_send.aclose()


asyncio.run(_exercise_async_runtime())


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
def _reject_wire_text(text: str, label: str, expected: str | None = None) -> None:
    Path("generation.json").write_text(text)
    try:
        _cott_load("_cott_impl/demo/bad.py", "{bad_hash}", "bad", "demo")
    except CottContractViolation as error:
        assert error.phase == "provenance", (label, error.phase)
        if expected is not None:
            assert expected in error.message, (label, error.message)
    else:
        raise AssertionError(f"{{label}} generation record was accepted")
    finally:
        Path("generation.json").write_text(_original_generation)

def _reject_generation(record: object, label: str, expected: str | None = None) -> None:
    _reject_wire_text(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n", label, expected)

_original_generation = Path("generation.json").read_text()
_v1 = json.loads(_original_generation)
_v1["schema_version"] = 1
_reject_generation(_v1, "v1")
_old_expanded = _read_record(_original_generation)
_old_expanded["schema_version"] = 7
_reject_generation(_old_expanded, "old expanded format", "record is malformed")
_unknown_root = json.loads(_original_generation)
_unknown_root["extra"] = None
_reject_generation(_unknown_root, "unknown root field", "record is malformed")
_dangling = json.loads(_original_generation)
del _dangling["snapshots"][_dangling["current"]]
_reject_generation(_dangling, "dangling snapshot", "dangling or unreferenced")
_unreferenced = json.loads(_original_generation)
_spare = dict(_current, verified=False)
_unreferenced["snapshots"][_runtime._cott_snapshot_digest(_spare)] = _spare
_reject_generation(_unreferenced, "unreferenced snapshot", "dangling or unreferenced")
_mutated_blob = json.loads(_original_generation)
_mutated_blob["snapshots"][_mutated_blob["current"]]["verification"] = dict(forged=True)
_reject_generation(_mutated_blob, "mutated snapshot evidence", "snapshot digest mismatch")
_forged_verified = _pack_record(dict(schema_version=8, current=dict(_current, verified=False), last_verified=None))
_forged_verified["snapshots"][_forged_verified["current"]]["verified"] = True
_reject_generation(_forged_verified, "forged verified flag", "snapshot digest mismatch")
_invalid_ref = json.loads(_original_generation)
_invalid_ref["current"] = "sha256:INVALID"
_reject_generation(_invalid_ref, "invalid snapshot reference", "record is malformed")
_reject_wire_text('{{"schema_version":8,' + _original_generation[1:], "duplicate root key", "duplicate JSON object key")
_reject_wire_text(_original_generation.replace('"verified":true', '"verified":true,"verified":false'), "duplicate snapshot key", "duplicate JSON object key")
_nonfinite = json.loads(_original_generation)
_nonfinite["snapshots"][_nonfinite["current"]]["verification"] = float("nan")
_reject_generation(_nonfinite, "nonfinite JSON constant", "nonfinite JSON constant")
_negative_zero = _read_record(_original_generation)
_negative_zero["current"]["tools"]["numeric_probe"] = 0
_negative_zero["current"]["generation_id"] = _generation_id(_negative_zero["current"])
_negative_zero_text = json.dumps(_pack_record(_negative_zero), sort_keys=True, separators=(",", ":")).replace('"numeric_probe":0', '"numeric_probe":-0')
_reject_wire_text(_negative_zero_text, "noncanonical negative integer zero", "noncanonical JSON integer zero")
_overflow_integer = json.loads(_original_generation)
_overflow_integer["snapshots"][_overflow_integer["current"]]["verification"] = 1 << 64
_reject_generation(_overflow_integer, "overflow JSON integer", "outside the snapshot integer range")
_missing = _read_record(_original_generation)
del _missing["current"]["project_version"]
_reject_generation(_pack_record(_missing), "missing", "snapshot is malformed")
_extra = _read_record(_original_generation)
_extra["current"]["unexpected"] = None
_reject_generation(_pack_record(_extra), "extra", "snapshot is malformed")
_incompatible = _read_record(_original_generation)
_incompatible["current"]["compatibility"]["runtime_abi"] = 1
_incompatible["current"]["generation_id"] = _generation_id(_incompatible["current"])
_reject_generation(_pack_record(_incompatible), "compatibility", "compatibility is incompatible")
_runtime_version_mismatch = _read_record(_original_generation)
_runtime_version_mismatch["current"]["tools"]["runtime"]["version"] = "0.0.0"
_runtime_version_mismatch["current"]["generation_id"] = _generation_id(_runtime_version_mismatch["current"])
_reject_generation(_pack_record(_runtime_version_mismatch), "runtime package version")
_version_mismatch = _read_record(_original_generation)
_version_mismatch["current"]["project_version"] = "0.3.1"
_version_mismatch["current"]["generation_id"] = _generation_id(_version_mismatch["current"])
_reject_generation(_pack_record(_version_mismatch), "project version", "project version mismatch")
_original_generation = Path("generation.json").read_text()
_mutated = _read_record(_original_generation)
_mutated["current"]["tools"]["python"]["version"] = "0.0.0"
_mutated["current"]["generation_id"] = _generation_id(_mutated["current"])
Path("generation.json").write_text(json.dumps(_pack_record(_mutated), sort_keys=True, separators=(",", ":")) + "\n")
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
_fixture_root = Path("fixture-root")
_fixture_root.mkdir()
try:
    _runtime._cott_fixture_now()
except CottContractViolation as error:
    assert error.phase == "fixture"
else:
    raise AssertionError("inactive fixture adapter was usable")
with _runtime._cott_fixture_activate(
    _runtime._cott_fixture_runner_token(),
    root=_fixture_root,
    http_url=None,
    clock=17,
    failures={{"clock.read": {{"occurrence": 2, "error": "clock stopped"}}}},
    transcript_limit=16,
):
    _runtime._cott_fixture_write(Path("nested/value"), b"old")
    assert _runtime._cott_fixture_read("nested/value") == b"old"
    _runtime._cott_fixture_replace(Path("nested/value"), b"new")
    assert _runtime._cott_fixture_read(Path("nested/value")) == b"new"
    assert _runtime._cott_fixture_now() == 17
    try:
        _runtime._cott_fixture_now()
    except OSError as error:
        assert str(error) == "clock stopped"
    else:
        raise AssertionError("configured fixture failure did not fire")
    _events = _runtime._cott_fixture_transcript()
    assert [event["kind"] for event in _events] == ["filesystem.write", "filesystem.read", "filesystem.replace", "filesystem.read", "clock.read", "failure"]
    assert all(str(_fixture_root) not in repr(event) for event in _events)
    for unsafe_path in (Path("../escape"), Path("/etc/passwd")):
        try:
            _runtime._cott_fixture_read(unsafe_path)
        except CottContractViolation as error:
            assert error.phase == "fixture"
        else:
            raise AssertionError("Path ABI bypassed fixture confinement")
with _runtime._cott_fixture_activate(
    _runtime._cott_fixture_runner_token(),
    root=_fixture_root,
    http_url=None,
    clock=None,
    failures={{}},
    transcript_limit=16_384,
):
    try:
        _runtime._cott_fixture_now()
    except CottContractViolation as error:
        assert error.phase == "fixture" and error.message == "fixture clock is unavailable"
    else:
        raise AssertionError("missing fixture clock was usable")
try:
    _runtime._cott_fixture_read("nested/value")
except CottContractViolation as error:
    assert error.phase == "fixture"
else:
    raise AssertionError("fixture adapter survived cleanup")
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

/// The Python OUTPUT RULES promise agents these exact fixture file adapter outcomes.
#[test]
fn fixture_file_adapters_raise_the_failures_the_output_rules_promise() {
    if Command::new("python3").arg("--version").output().is_err() {
        return;
    }

    let temp = TempDir::new();
    write_runtime(&temp.path);
    let script = r#"
import os
from pathlib import Path
import cott_runtime as _runtime
from cott_runtime import CottContractViolation

def raised(call):
    try:
        call()
    except BaseException as error:
        return error
    raise AssertionError("fixture adapter call did not fail")

for call in (
    lambda: _runtime._cott_fixture_read("inactive.txt"),
    lambda: _runtime._cott_fixture_write("inactive.txt", b"data"),
    lambda: _runtime._cott_fixture_replace("inactive.txt", b"data"),
    lambda: _runtime._cott_fixture_write(Path("/escape"), "not bytes"),
):
    error = raised(call)
    assert type(error) is CottContractViolation, error
    assert error.message == "fixture adapters are inactive", error.message
    assert str(error) == "fixture adapters are inactive [phase=fixture]", str(error)
assert not Path("inactive.txt").exists()

root = Path("fixture-root")
root.mkdir()
def active(failures, action):
    with _runtime._cott_fixture_activate(
        _runtime._cott_fixture_runner_token(),
        root=root,
        http_url=None,
        clock=None,
        failures={point: {"occurrence": 1, "error": "injected " + point} for point in failures},
        transcript_limit=64,
    ):
        return action()

missing = active((), lambda: raised(lambda: _runtime._cott_fixture_read("absent.txt")))
assert type(missing) is CottContractViolation and type(missing.__cause__) is FileNotFoundError, repr(missing)

if os.geteuid() != 0:
    (root / "locked.txt").write_bytes(b"secret")
    (root / "locked.txt").chmod(0)
    denied = active((), lambda: raised(lambda: _runtime._cott_fixture_read("locked.txt")))
    assert type(denied) is CottContractViolation and type(denied.__cause__) is PermissionError, repr(denied)

for point, call in (
    ("file.open", lambda: _runtime._cott_fixture_read("value.txt")),
    ("file.read", lambda: _runtime._cott_fixture_read("value.txt")),
    ("file.write", lambda: _runtime._cott_fixture_write("value.txt", b"new")),
    ("file.write", lambda: _runtime._cott_fixture_replace("value.txt", b"new")),
):
    (root / "value.txt").write_bytes(b"old")
    injected = active((point,), lambda: raised(call))
    assert type(injected) is OSError and str(injected) == "injected " + point, repr(injected)
    assert (root / "value.txt").read_bytes() == b"old"

for point, call, keeps_previous in (
    ("file.flush", lambda: _runtime._cott_fixture_write("value.txt", b"new"), False),
    ("file.flush", lambda: _runtime._cott_fixture_replace("value.txt", b"new"), True),
    ("file.replace", lambda: _runtime._cott_fixture_replace("value.txt", b"new"), True),
):
    (root / "value.txt").write_bytes(b"old")
    wrapped = active((point,), lambda: raised(call))
    assert type(wrapped) is CottContractViolation, repr(wrapped)
    assert type(wrapped.__cause__) is OSError and str(wrapped.__cause__) == "injected " + point, repr(wrapped.__cause__)
    if keeps_previous:
        assert (root / "value.txt").read_bytes() == b"old"
    assert [path.name for path in root.iterdir() if path.name.startswith(".")] == []

unsafe = active((), lambda: raised(lambda: _runtime._cott_fixture_write("../escape", b"data")))
assert type(unsafe) is CottContractViolation and unsafe.__cause__ is None, repr(unsafe)
not_bytes = active((), lambda: raised(lambda: _runtime._cott_fixture_replace("value.txt", "text")))
assert type(not_bytes) is CottContractViolation and not_bytes.__cause__ is None, repr(not_bytes)

active((), lambda: _runtime._cott_fixture_replace(Path("nested/deeper/value.txt"), b"replaced"))
assert (root / "nested/deeper/value.txt").read_bytes() == b"replaced"
assert [path.name for path in (root / "nested/deeper").iterdir()] == ["value.txt"]
"#;
    let output = Command::new("python3")
        .arg("-c")
        .arg(script)
        .current_dir(&temp.path)
        .output()
        .expect("python3 should execute generated runtime");
    assert!(
        output.status.success(),
        "fixture adapter contract failed:\n{}\n{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn generated_runtime_imports_async_protocol_support() {
    if Command::new("python3").arg("--version").output().is_err() {
        return;
    }
    let temp = TempDir::new();
    write_runtime(&temp.path);
    let output = Command::new("python3")
        .arg("-c")
        .arg(
            "from cott_runtime import AsyncGenerator, AsyncIterator, _CottAsyncRLock, _cott_wrap_async_protocol; assert AsyncGenerator and AsyncIterator and _CottAsyncRLock and _cott_wrap_async_protocol",
        )
        .current_dir(&temp.path)
        .output()
        .expect("python3 should import generated runtime");
    assert!(
        output.status.success(),
        "generated runtime import failed:\n{}",
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn generated_runtime_validates_generic_dyn_exactly() {
    if Command::new("python3").arg("--version").output().is_err() {
        return;
    }
    let temp = TempDir::new();
    write_runtime(&temp.path);
    let script = r#"
from typing import Protocol, TypeVar

import cott_runtime as _runtime
from cott_runtime import CottContractViolation, Dyn, I32, U32, _cott_validate_abi

_Item = TypeVar("_Item")


class Reader(Protocol[_Item]):
    _cott_trait = True

    def read(self, value: _Item) -> _Item: ...

class Parent(Protocol[_Item]):
    _cott_trait = True

    def parent(self, value: _Item) -> _Item: ...


class OtherReader(Protocol[_Item]):
    _cott_trait = True

    def read(self, value: _Item) -> _Item: ...


class Concrete:
    _cott_traits = (Reader,)

    def read(self, value: int) -> int:
        return value

class ParentConcrete:
    _cott_traits = (Parent,)

    def parent(self, value: int) -> int:
        return value


class StructuralReader:
    def read(self, value: int) -> int:
        return value


reader_i32 = Reader[I32]
Concrete._cott_trait_specs = (reader_i32,)
value = Dyn(value=Concrete(), trait=reader_i32)
assert value.trait is reader_i32
assert value.value.read(7) == 7
assert _cott_validate_abi(value, Dyn[Reader[I32]]) is value
parent_i32 = Parent[I32]
ParentConcrete._cott_trait_specs = (parent_i32,)
parent_value = Dyn(value=ParentConcrete(), trait=parent_i32)
assert _cott_validate_abi(parent_value, Dyn[Parent[I32]]) is parent_value
try:
    _cott_validate_abi(parent_value, Dyn[Parent[str]])
except CottContractViolation as error:
    assert error.phase == "validation"
else:
    raise AssertionError("Dyn accepted Parent with the wrong generic argument")
for annotation in (Dyn[Reader[str]], Dyn[Reader[U32]], Dyn[OtherReader[I32]]):
    try:
        _cott_validate_abi(value, annotation)
    except CottContractViolation as error:
        assert error.phase == "validation"
    else:
        raise AssertionError("Dyn accepted the wrong full trait alias")
for candidate, trait in ((Concrete(), Reader[str]), (Concrete(), OtherReader[I32]), (StructuralReader(), reader_i32)):
    try:
        Dyn(value=candidate, trait=trait)
    except CottContractViolation as error:
        assert error.phase == "validation"
    else:
        raise AssertionError("Dyn accepted a non-exact trait carrier")

def _forged_dyn(value, trait, sealed=False):
    forged = object.__new__(Dyn)
    object.__setattr__(forged, "value", value)
    object.__setattr__(forged, "trait", trait)
    if sealed:
        object.__setattr__(forged, "_seal", _runtime._COTT_DYN_SEAL)
    return forged

for forged in (
    _forged_dyn(Concrete(), reader_i32),
    _forged_dyn(Concrete(), Reader[str], sealed=True),
    _forged_dyn(StructuralReader(), reader_i32, sealed=True),
):
    try:
        _cott_validate_abi(forged, Dyn[Reader[I32]])
    except CottContractViolation as error:
        assert error.phase == "validation"
    else:
        raise AssertionError("forged Dyn passed boundary validation")
"#;
    let output = Command::new("python3")
        .arg("-c")
        .arg(script)
        .current_dir(&temp.path)
        .output()
        .expect("python3 should execute generated runtime");
    assert!(
        output.status.success(),
        "generated runtime Dyn validation failed:\n{}\n{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn contract_observer_context_cannot_expose_or_redirect_mutable_evidence() {
    if Command::new("python3").arg("--version").output().is_err() {
        return;
    }
    let temp = TempDir::new();
    write_runtime(&temp.path);
    let script = r#"import asyncio
import contextvars
from cott_runtime import CottContractViolation, _cott_contract_condition, _cott_observe_contracts

with _cott_observe_contracts() as events:
    for variable, value in contextvars.copy_context().items():
        if isinstance(value, list):
            value.append(("model.same", "ensures:0", True))
assert events == [], events

with _cott_observe_contracts() as outer:
    with _cott_observe_contracts() as inner:
        _cott_contract_condition(True, "model.same", "ensures:0")
    _cott_contract_condition(True, "model.same", "requires:0")
assert inner == [("model.same", "ensures:0", True)]
assert outer == [("model.same", "requires:0", True)]

try:
    with _cott_observe_contracts() as events:
        variable = next(variable for variable in contextvars.copy_context()
                        if variable.name == "_cott_contract_observer")
        changed = variable.set(object())
        try:
            _cott_contract_condition(True, "model.same", "ensures:0")
        except CottContractViolation as error:
            assert error.phase == "evidence"
        finally:
            variable.reset(changed)
except CottContractViolation as error:
    assert error.phase == "evidence"
else:
    raise AssertionError("restoring a replaced observation token hid tampering")
assert events == []

try:
    with _cott_observe_contracts() as outer:
        variable, identity = next((variable, value) for variable, value
                                  in contextvars.copy_context().items()
                                  if variable.name == "_cott_contract_observer")
        try:
            with _cott_observe_contracts() as inner:
                changed = variable.set(identity)
                try:
                    _cott_contract_condition(True, "model.same", "ensures:0")
                finally:
                    variable.reset(changed)
        except CottContractViolation:
            pass
except CottContractViolation as error:
    assert error.phase == "evidence"
else:
    raise AssertionError("nested observation accepted an outer invocation token")
assert outer == [] and inner == []

async def exercise_async():
    ready = asyncio.Event()
    arrivals = 0
    async def observe(clause):
        nonlocal arrivals
        with _cott_observe_contracts() as events:
            arrivals += 1
            if arrivals == 2:
                ready.set()
            await ready.wait()
            _cott_contract_condition(True, "model.same", clause)
        return events
    first, second = await asyncio.gather(observe("requires:0"), observe("ensures:0"))
    assert first == [("model.same", "requires:0", True)]
    assert second == [("model.same", "ensures:0", True)]

    async def inherited():
        await asyncio.sleep(0)
        _cott_contract_condition(True, "model.same", "ensures:0")
    with _cott_observe_contracts() as events:
        await asyncio.create_task(inherited())
    assert events == [("model.same", "ensures:0", True)]

    entered = asyncio.Event()
    async def cancelled():
        with _cott_observe_contracts():
            entered.set()
            await asyncio.Future()
    task = asyncio.create_task(cancelled())
    await entered.wait()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    local = contextvars.ContextVar("application-local", default=0)
    with _cott_observe_contracts() as events:
        token = local.set(7)
        await asyncio.sleep(0)
        assert local.get() == 7
        local.reset(token)
        _cott_contract_condition(True, "model.same", "ensures:0")
    assert events == [("model.same", "ensures:0", True)]

asyncio.run(exercise_async())
"#;
    let output = Command::new("python3")
        .args(["-c", script])
        .current_dir(&temp.path)
        .output()
        .expect("python3 should execute observer regression");
    assert!(
        output.status.success(),
        "observer authority regression:\n{}\n{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}
