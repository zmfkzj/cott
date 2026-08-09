use std::collections::BTreeMap;
use std::path::PathBuf;

const RUNTIME_INIT_TEMPLATE: &str = r#"# Cott's compiler-owned Python runtime.
# This module intentionally depends only on Python's standard library.
from __future__ import annotations

import hashlib as _hashlib
import math as _math
import os as _os
import stat as _stat
import struct as _struct
import sys as _sys
import threading as _threading
import types as _types
from collections.abc import Iterable, Mapping, Sequence, Set
from dataclasses import dataclass
from pathlib import Path as _Path
from typing import Annotated, Any, Generic, Literal, Never, TypeAlias, TypeVar, Union, get_args as _get_args, get_origin as _get_origin, final as _final


# The compiler embeds this value in every generated runtime.
PROJECT_NAME = __COTT_PROJECT_NAME_LITERAL__
_COTT_PROJECT_NAME = PROJECT_NAME
_COTT_RUNTIME_ABI = "1"


_T = TypeVar("_T")
_E = TypeVar("_E")
_K = TypeVar("_K")
_V = TypeVar("_V")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")


@_final
@dataclass(frozen=True, slots=True)
class CottInt:
    sign: str
    bits: int

    def __post_init__(self) -> None:
        if self.sign not in ("signed", "unsigned") or self.bits not in (8, 16, 32, 64):
            raise ValueError("invalid CottInt metadata")


@_final
@dataclass(frozen=True, slots=True)
class CottFloat:
    bits: int

    def __post_init__(self) -> None:
        if self.bits not in (32, 64):
            raise ValueError("invalid CottFloat metadata")


I8: TypeAlias = Annotated[int, CottInt("signed", 8)]
I16: TypeAlias = Annotated[int, CottInt("signed", 16)]
I32: TypeAlias = Annotated[int, CottInt("signed", 32)]
I64: TypeAlias = Annotated[int, CottInt("signed", 64)]
U8: TypeAlias = Annotated[int, CottInt("unsigned", 8)]
U16: TypeAlias = Annotated[int, CottInt("unsigned", 16)]
U32: TypeAlias = Annotated[int, CottInt("unsigned", 32)]
U64: TypeAlias = Annotated[int, CottInt("unsigned", 64)]
F32: TypeAlias = Annotated[float, CottFloat(32)]
F64: TypeAlias = Annotated[float, CottFloat(64)]


def _cott_normalize_int(value: object, metadata: CottInt) -> int:
    if type(value) is not int:
        raise CottContractViolation("expected an exact int", phase="validation")
    if metadata.sign == "signed":
        low, high = -(1 << (metadata.bits - 1)), (1 << (metadata.bits - 1)) - 1
    else:
        low, high = 0, (1 << metadata.bits) - 1
    if not low <= value <= high:
        raise CottContractViolation(f"integer outside {metadata.sign} {metadata.bits}-bit range", phase="validation")
    return value


def _cott_normalize_f32(value: object) -> float:
    if type(value) is not float or not _math.isfinite(value):
        raise CottContractViolation("expected a finite exact float", phase="validation")
    normalized = _struct.unpack("!f", _struct.pack("!f", value))[0]
    if not _math.isfinite(normalized):
        raise CottContractViolation("float is outside binary32 range", phase="validation")
    return normalized


def _cott_normalize_scalar(value: object, annotation: object) -> object:
    metadata = next((item for item in _get_args(annotation)[1:] if isinstance(item, (CottInt, CottFloat))), None)
    if isinstance(metadata, CottInt):
        return _cott_normalize_int(value, metadata)
    if isinstance(metadata, CottFloat):
        return _cott_normalize_f32(value) if metadata.bits == 32 else value
    return value


@_final
@dataclass(frozen=True, slots=True, kw_only=True)
class Ok(Generic[_T]):
    value: _T
    __hash__ = None


@_final
@dataclass(frozen=True, slots=True, kw_only=True)
class Err(Generic[_E]):
    error: _E
    __hash__ = None


@_final
@dataclass(frozen=True, slots=True, kw_only=True)
class Some(Generic[_T]):
    value: _T
    __hash__ = None


@_final
@dataclass(frozen=True, slots=True, kw_only=True, repr=False)
class Nothing:
    __hash__ = None

    def __repr__(self) -> str:
        return "Nothing()"


Result: TypeAlias = Union[Ok[_T], Err[_E]]
Option: TypeAlias = Union[Some[_T], Nothing]


@_final
class Unit:
    __slots__ = ()
    _instance: Unit | None = None
    __hash__ = None

    def __new__(cls) -> Unit:
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNIT"

    def __eq__(self, other: object) -> bool:
        return type(other) is Unit


UNIT = Unit()


@_final
class CottList(Sequence[_T], Generic[_T]):
    __slots__ = ("_values",)
    __hash__ = None

    def __init__(self, *, values: Iterable[_T]) -> None:
        self._values = values._values if type(values) is CottList else tuple(values)

    def __len__(self) -> int:
        return len(self._values)

    def __getitem__(self, index: int | slice) -> _T | tuple[_T, ...]:
        return self._values[index]

    def __iter__(self):
        return iter(self._values)

    def __eq__(self, other: object) -> bool:
        return type(other) is CottList and self._values == other._values

    def __repr__(self) -> str:
        return f"CottList(values={self._values!r})"


@_final
class CottSet(Set[_T], Generic[_T]):
    __slots__ = ("_values",)
    __hash__ = None

    def __init__(self, *, values: Iterable[_T]) -> None:
        self._values = values._values if type(values) is CottSet else frozenset(values)

    def __len__(self) -> int:
        return len(self._values)

    def __contains__(self, value: object) -> bool:
        return value in self._values

    def __iter__(self):
        return iter(self._values)

    def __eq__(self, other: object) -> bool:
        return type(other) is CottSet and self._values == other._values

    def __repr__(self) -> str:
        return f"CottSet(values={self._values!r})"


@_final
class FrozenMap(Mapping[_K, _V], Generic[_K, _V]):
    __slots__ = ("_values",)
    __hash__ = None

    def __init__(self, *, values: Mapping[_K, _V]) -> None:
        from types import MappingProxyType as _MappingProxyType
        self._values = values._values if type(values) is FrozenMap else _MappingProxyType(dict(values))

    def __len__(self) -> int:
        return len(self._values)

    def __iter__(self):
        return iter(self._values)

    def __getitem__(self, key: _K) -> _V:
        return self._values[key]

    def __eq__(self, other: object) -> bool:
        return type(other) is FrozenMap and dict(self._values) == dict(other._values)

    def __repr__(self) -> str:
        return f"FrozenMap(values={dict(self._values)!r})"


@_final
class CottTuple2(Sequence[_T1], Generic[_T1, _T2]):
    __slots__ = ("_values",)
    def __hash__(self) -> int:
        return hash(self._values)

    def __init__(self, *, first: _T1, second: _T2) -> None:
        self._values = (first, second)

    @property
    def first(self) -> _T1:
        return self._values[0]

    @property
    def second(self) -> _T2:
        return self._values[1]

    def __len__(self) -> Literal[2]:
        return 2

    def __getitem__(self, index: int | slice) -> _T1 | _T2 | tuple[_T1 | _T2, ...]:
        return self._values[index]

    def __iter__(self):
        return iter(self._values)

    def __eq__(self, other: object) -> bool:
        return type(other) is CottTuple2 and self._values == other._values

    def __repr__(self) -> str:
        return f"CottTuple2(first={self.first!r}, second={self.second!r})"


@_final
class Opaque(Generic[_T]):
    __slots__ = ("tag", "value")
    __hash__ = None

    def __init__(self, *, tag: str, value: _T) -> None:
        if type(tag) is not str or not tag:
            raise CottContractViolation("opaque tag must be a non-empty str", phase="validation")
        self.tag, self.value = tag, value

    def __eq__(self, other: object) -> bool:
        return type(other) is Opaque and self.tag == other.tag and self.value == other.value

    def __repr__(self) -> str:
        return f"Opaque(tag={self.tag!r}, value={self.value!r})"


@_final
@dataclass(frozen=True, slots=True, kw_only=True, repr=False)
class JsonNull:
    __hash__ = None

    def __repr__(self) -> str:
        return "JsonNull()"


@_final
@dataclass(frozen=True, slots=True, kw_only=True)
class JsonBoolean:
    value: bool
    __hash__ = None

    def __post_init__(self) -> None:
        if type(self.value) is not bool:
            raise CottContractViolation("JsonBoolean.value must be bool", phase="validation")


@_final
@dataclass(frozen=True, slots=True, kw_only=True)
class JsonInteger:
    value: int
    __hash__ = None

    def __post_init__(self) -> None:
        if type(self.value) is not int or not -(1 << 63) <= self.value < (1 << 63):
            raise CottContractViolation("JsonInteger.value must be an I64", phase="validation")


@_final
@dataclass(frozen=True, slots=True, kw_only=True)
class JsonFloat:
    value: float
    __hash__ = None

    def __post_init__(self) -> None:
        if type(self.value) is not float or not _math.isfinite(self.value):
            raise CottContractViolation("JsonFloat.value must be a finite F64", phase="validation")


@_final
@dataclass(frozen=True, slots=True, kw_only=True)
class JsonString:
    value: str
    __hash__ = None

    def __post_init__(self) -> None:
        if type(self.value) is not str or any(0xD800 <= ord(char) <= 0xDFFF for char in self.value):
            raise CottContractViolation("JsonString.value must contain no surrogates", phase="validation")


@_final
@dataclass(frozen=True, slots=True, kw_only=True)
class JsonArray:
    value: CottList[JsonValue]
    __hash__ = None

    def __post_init__(self) -> None:
        if type(self.value) is not CottList:
            raise CottContractViolation("JsonArray.value must be CottList", phase="validation")
        for item in self.value:
            _cott_validate_json(item)

@_final
@dataclass(frozen=True, slots=True, kw_only=True)
class JsonObject:
    value: FrozenMap[str, JsonValue]
    __hash__ = None

    def __post_init__(self) -> None:
        if type(self.value) is not FrozenMap:
            raise CottContractViolation("JsonObject.value must be FrozenMap", phase="validation")
        for key, item in self.value.items():
            if type(key) is not str:
                raise CottContractViolation("JsonObject keys must be str", phase="validation")
            _cott_validate_json(item)

JsonValue: TypeAlias = Union[JsonNull, JsonBoolean, JsonInteger, JsonFloat, JsonString, JsonArray, JsonObject]


def _cott_validate_json(value: object) -> None:
    if type(value) in (JsonNull, JsonBoolean, JsonInteger, JsonFloat, JsonString):
        return
    if type(value) is JsonArray:
        if type(value.value) is not CottList:
            raise CottContractViolation("JsonArray.value must be CottList", phase="validation")
        for item in value.value:
            _cott_validate_json(item)
        return
    if type(value) is JsonObject:
        if type(value.value) is not FrozenMap:
            raise CottContractViolation("JsonObject.value must be FrozenMap", phase="validation")
        for key, item in value.value.items():
            if type(key) is not str:
                raise CottContractViolation("JsonObject keys must be str", phase="validation")
            _cott_validate_json(item)
        return
    raise CottContractViolation("value is not a JsonValue", phase="validation")


def _cott_validate_abi(value: object, annotation: object, *, path: str = "$") -> object:
    """Validate an ABI value recursively and normalize concrete numeric aliases."""
    origin = _get_origin(annotation)
    args = _get_args(annotation)
    if origin is Annotated:
        normalized = _cott_normalize_scalar(value, annotation)
        return _cott_validate_abi(normalized, args[0], path=path)
    if origin in (Union,):
        for candidate in args:
            try:
                return _cott_validate_abi(value, candidate, path=path)
            except CottContractViolation:
                pass
        raise CottContractViolation(f"{path} does not match ABI union", phase="validation")
    if annotation is Any:
        return value
    if annotation is Never:
        raise CottContractViolation(f"{path} cannot contain Never", phase="validation")
    if annotation is bool and type(value) is bool:
        return value
    if annotation is int and type(value) is int:
        return value
    if annotation is float and type(value) is float:
        return value
    if annotation is str and type(value) is str and not any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        return value
    if annotation is bytes and type(value) is bytes:
        return value
    if isinstance(annotation, type) and type(value) is annotation:
        if annotation is JsonArray or annotation is JsonObject:
            _cott_validate_json(value)
        return value
    if origin is CottList and type(value) is CottList:
        item_type = args[0] if args else Any
        for item in value:
            _cott_validate_abi(item, item_type, path=path)
        return value
    if origin is CottSet and type(value) is CottSet:
        item_type = args[0] if args else Any
        for item in value:
            _cott_validate_abi(item, item_type, path=path)
        return value
    if origin is FrozenMap and type(value) is FrozenMap:
        key_type, item_type = args if len(args) == 2 else (Any, Any)
        for key, item in value.items():
            _cott_validate_abi(key, key_type, path=path)
            _cott_validate_abi(item, item_type, path=path)
        return value
    if origin is CottTuple2 and type(value) is CottTuple2:
        if args:
            _cott_validate_abi(value.first, args[0], path=path)
            _cott_validate_abi(value.second, args[1], path=path)
        return value
    raise CottContractViolation(f"{path} does not match ABI type", phase="validation")


class CottContractViolation(Exception):
    """Raised when a generated contract or provenance check is violated."""

    def __init__(self, message: str, *, function: str | None = None, clause: str | None = None, phase: str | None = None) -> None:
        self.message, self.function, self.clause, self.phase = message, function, clause, phase
        detail = message
        for label, value in (("function", function), ("clause", clause), ("phase", phase)):
            if value is not None:
                detail += f" [{label}={value}]"
        super().__init__(detail)


def _cott_display(value: object) -> str:
    if value is UNIT:
        return "UNIT"
    if isinstance(value, (Ok, Err, Some, Nothing, JsonNull, JsonBoolean, JsonInteger, JsonFloat, JsonString, JsonArray, JsonObject, Opaque)):
        return repr(value)
    return repr(value)


def _cott_check_project_identity(expected_project_name: str | None, *, phase: str = "facade-import") -> None:
    if expected_project_name is not None and expected_project_name != PROJECT_NAME:
        raise CottContractViolation(
            f"project identity mismatch: expected {expected_project_name!r}, runtime is {PROJECT_NAME!r}",
            phase=phase,
        )


_COTT_MODULE_CACHE: dict[str, tuple[_types.ModuleType, str]] = {}
_COTT_LOAD_LOCK = _threading.RLock()


class _CottImplementationImportBlocker:
    def find_spec(self, fullname: str, path: object = None, target: object = None) -> object:
        if fullname == "_cott_impl" or fullname.startswith("_cott_impl."):
            raise ModuleNotFoundError("direct _cott_impl imports are compiler-owned")
        return None


if not any(type(finder) is _CottImplementationImportBlocker for finder in _sys.meta_path):
    _sys.meta_path.insert(0, _CottImplementationImportBlocker())


def _cott_violation(message: str, *, phase: str = "provenance") -> CottContractViolation:
    return CottContractViolation(message, function="_cott_load", phase=phase)


def _cott_load(relative_path: str, expected_sha256: str, symbol: str, project_name: str | None = None, *, expected_project_name: str | None = None):
    """Verify and lazily load one generated implementation symbol."""
    if project_name is not None and expected_project_name is not None and project_name != expected_project_name:
        raise _cott_violation("conflicting project identities", phase="facade-import")
    _cott_check_project_identity(project_name if expected_project_name is None else expected_project_name, phase="facade-import")
    if type(relative_path) is not str or type(expected_sha256) is not str:
        raise _cott_violation("binding path and hash must be strings")
    if type(symbol) is not str or not symbol.isidentifier():
        raise _cott_violation("binding symbol must be an identifier")
    if not relative_path or "\\" in relative_path:
        raise _cott_violation("binding path must be a normalized relative POSIX path")
    parts = relative_path.split("/")
    if len(parts) < 2 or parts[0] != "_cott_impl" or any(part in ("", ".", "..") for part in parts):
        raise _cott_violation("binding path must be below _cott_impl")
    if any(not part.isidentifier() for part in parts[:-1]) or not parts[-1].endswith(".py") or parts[-1] == "__init__.py" or not parts[-1][:-3].isidentifier():
        raise _cott_violation("binding path contains an invalid module name")
    module_name = ".".join(parts)[:-3]
    digest_input = expected_sha256.removeprefix("sha256:")
    if len(digest_input) != 64 or any(char not in "0123456789abcdefABCDEF" for char in digest_input):
        raise _cott_violation("binding hash must be SHA-256 hex")
    root = _Path(__file__).resolve().parent.parent
    path = root.joinpath(*parts)
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
        if resolved != path:
            raise _cott_violation("binding path contains a symlink")
        flags = _os.O_RDONLY | getattr(_os, "O_NOFOLLOW", 0)
        fd = _os.open(path, flags)
        try:
            metadata = _os.fstat(fd)
            if not _stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise _cott_violation("binding is not a regular file")
            with _os.fdopen(fd, "rb") as stream:
                fd = -1
                source = stream.read()
        finally:
            if fd != -1:
                _os.close(fd)
    except CottContractViolation:
        raise
    except (OSError, ValueError) as error:
        raise _cott_violation(f"unable to read binding {relative_path}: {error}") from error

    digest = _hashlib.sha256(source).hexdigest()
    if digest != digest_input.lower():
        raise _cott_violation(f"binding hash mismatch for {relative_path}")

    with _COTT_LOAD_LOCK:
        cached = _COTT_MODULE_CACHE.get(module_name)
        if cached is not None:
            module, cached_digest = cached
            if cached_digest != digest or _sys.modules.get(module_name) is not module:
                raise _cott_violation(f"canonical module cache conflict for {module_name}")
            try:
                return getattr(module, symbol)
            except AttributeError as error:
                raise _cott_violation(f"binding symbol {symbol!r} is missing") from error
        if module_name in _sys.modules:
            raise _cott_violation(f"direct implementation import is not allowed: {module_name}")

        module = _types.ModuleType(module_name)
        module.__file__ = str(path)
        module.__package__ = module_name.rpartition(".")[0]
        module.__loader__ = None
        module.__cott_project_name__ = PROJECT_NAME
        _sys.modules[module_name] = module
        try:
            exec(compile(source, str(path), "exec"), module.__dict__)
            if module.__dict__.get("__cott_project_name__", PROJECT_NAME) != PROJECT_NAME:
                raise _cott_violation("implementation project identity mismatch", phase="implementation-load")
        except CottContractViolation:
            if _sys.modules.get(module_name) is module:
                del _sys.modules[module_name]
            raise
        except Exception as error:
            if _sys.modules.get(module_name) is module:
                del _sys.modules[module_name]
            raise _cott_violation(f"failed to load binding {relative_path}: {error}", phase="implementation-load") from error
        _COTT_MODULE_CACHE[module_name] = (module, digest)
        try:
            return getattr(module, symbol)
        except AttributeError as error:
            del _COTT_MODULE_CACHE[module_name]
            if _sys.modules.get(module_name) is module:
                del _sys.modules[module_name]
            raise _cott_violation(f"binding symbol {symbol!r} is missing") from error


__all__ = [
    "CottContractViolation", "CottFloat", "CottInt", "CottList", "CottSet", "CottTuple2", "Err", "F32", "F64", "FrozenMap",
    "I8", "I16", "I32", "I64", "JsonArray", "JsonBoolean", "JsonFloat", "JsonInteger", "JsonNull", "JsonObject", "JsonString", "JsonValue",
    "Never", "Nothing", "Ok", "Opaque", "Option", "PROJECT_NAME", "Result", "Some", "U8", "U16", "U32", "U64", "UNIT", "Unit",
]
"#;

const PY_TYPED: &[u8] = b"\n";

fn python_string_literal(value: &str) -> String {
    let mut escaped = String::with_capacity(value.len() + 2);
    escaped.push('\'');
    for character in value.chars() {
        match character {
            '\\' => escaped.push_str("\\\\"),
            '\'' => escaped.push_str("\\'"),
            '\n' => escaped.push_str("\\n"),
            '\r' => escaped.push_str("\\r"),
            '\t' => escaped.push_str("\\t"),
            character if character.is_control() => {
                use std::fmt::Write;
                write!(escaped, "\\u{:04x}", character as u32)
                    .expect("writing to String cannot fail");
            }
            character => escaped.push(character),
        }
    }
    escaped.push('\'');
    escaped
}

/// Render the compiler-owned, stdlib-only Python runtime files.
pub fn render_runtime(project_name: &str) -> BTreeMap<PathBuf, Vec<u8>> {
    let source = RUNTIME_INIT_TEMPLATE.replace(
        "__COTT_PROJECT_NAME_LITERAL__",
        &python_string_literal(project_name),
    );
    let mut files = BTreeMap::new();
    files.insert(
        PathBuf::from("cott_runtime/__init__.py"),
        source.into_bytes(),
    );
    files.insert(PathBuf::from("cott_runtime/py.typed"), PY_TYPED.to_vec());
    files
}
