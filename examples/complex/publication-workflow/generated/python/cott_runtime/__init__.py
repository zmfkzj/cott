# Cott's compiler-owned Python runtime.
# This module intentionally depends only on Python's standard library.
from __future__ import annotations

import dataclasses as _dataclasses
import ast as _ast
import hashlib as _hashlib
import importlib.metadata as _metadata
import json as _json
import math as _math
import os as _os
import platform as _platform
import stat as _stat
import struct as _struct
import sys as _sys
import sysconfig as _sysconfig
import threading as _threading
import types as _types
from collections.abc import Generator as _Generator, Iterable, Iterator, Mapping, Sequence, Set
from dataclasses import dataclass
from pathlib import Path as _Path
from typing import Annotated, Any, Generic, Literal, Never, TypeAlias, TypeVar, Union, get_args as _get_args, get_origin as _get_origin, get_type_hints as _get_type_hints, final as _final, overload
_COTT_PATH_TYPE = type(_Path())




# The compiler embeds this value in every generated runtime.
PROJECT_NAME = 'publication-workflow'
_COTT_PROJECT_NAME = PROJECT_NAME
PROJECT_VERSION = '0.1.0'
_COTT_RUNTIME_ABI = "2"
_COTT_RUNTIME_VERSION = '0.3.0'


_T = TypeVar("_T")
_E = TypeVar("_E")
_K = TypeVar("_K")
_V = TypeVar("_V")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")
_N = TypeVar("_N", bound=int)

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


@_final
@dataclass(frozen=True, slots=True)
class CottExternal:
    path: str


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

def _cott_euclidean_mod(left: int, right: int) -> int:
    if right == 0:
        raise CottContractViolation("integer remainder divisor is zero", phase="contract-expression")
    return left % abs(right)


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

    @overload
    def __getitem__(self, index: int) -> _T: ...

    @overload
    def __getitem__(self, index: slice) -> tuple[_T, ...]: ...

    def __getitem__(self, index: int | slice) -> _T | tuple[_T, ...]:
        return self._values[index]

    def __iter__(self) -> Iterator[_T]:
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
class CottArray(Sequence[_T], Generic[_T, _N]):
    __slots__ = ("_values",)
    __hash__ = None

    def __init__(self, *, values: Iterable[_T]) -> None:
        object.__setattr__(
            self, "_values", values._values if type(values) is CottArray else tuple(values)
        )

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("CottArray is immutable")

    def __len__(self) -> int:
        return len(self._values)

    def __getitem__(self, index: int | slice) -> _T | tuple[_T, ...]:
        return self._values[index]

    def __iter__(self) -> Iterator[_T]:
        return iter(self._values)

    def __eq__(self, other: object) -> bool:
        return type(other) is CottArray and self._values == other._values

    def __repr__(self) -> str:
        return f"CottArray(values={self._values!r})"


@_final
class CottBuffer(Sequence[int], Generic[_N]):
    __slots__ = ("_data",)
    __hash__ = None

    def __init__(self, *, data: bytes) -> None:
        if type(data) is not bytes:
            raise CottContractViolation("CottBuffer.data must be exact bytes", phase="validation")
        object.__setattr__(self, "_data", data)

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("CottBuffer is immutable")

    @property
    def data(self) -> bytes:
        return self._data

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, index: int | slice) -> int | bytes:
        return self._data[index]

    def __iter__(self) -> Iterator[int]:
        return iter(self._data)

    def __eq__(self, other: object) -> bool:
        return type(other) is CottBuffer and self._data == other._data

    def __repr__(self) -> str:
        return f"CottBuffer(data={self._data.hex()!r})"

@_final
@dataclass(frozen=True, slots=True, kw_only=True, eq=False, repr=False)
class Opaque(Generic[_T]):
    __hash__ = None
    tag: str
    value: object

    def __post_init__(self) -> None:
        if type(self.tag) is not str or not self.tag:
            raise CottContractViolation("opaque tag must be a non-empty str", phase="validation")

    def unwrap(self) -> object:
        return self.value

    def __eq__(self, other: object) -> bool:
        return type(other) is Opaque and self.tag == other.tag and self.value is other.value

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


def _cott_fixed_length(annotation: object, path: str) -> int:
    values = _get_args(annotation)
    if len(values) != 1 or type(values[0]) is not int or values[0] < 0:
        raise CottContractViolation(f"{path} has an invalid fixed length", phase="validation")
    return values[0]


def _cott_substitute_type(annotation: object, substitutions: dict[object, object]) -> object:
    replacement = substitutions.get(annotation)
    if replacement is not None:
        return replacement
    args = _get_args(annotation)
    if not args:
        return annotation
    replaced = tuple(_cott_substitute_type(item, substitutions) for item in args)
    if replaced == args:
        return annotation
    copier = getattr(annotation, "copy_with", None)
    if copier is not None:
        return copier(replaced)
    return annotation


def _cott_validate_abi(value: object, annotation: object, *, path: str = "$") -> object:
    """Validate an ABI value recursively and normalize concrete numeric aliases."""
    origin = _get_origin(annotation)
    args = _get_args(annotation)
    if origin is Annotated:
        external = next((item for item in args[1:] if isinstance(item, CottExternal)), None)
        if external is not None:
            target = args[0]
            if isinstance(target, type):
                try:
                    matches = isinstance(value, target)
                except TypeError:
                    return value
                if not matches:
                    raise CottContractViolation(f"{path} does not match external ABI type", phase="validation")
            return value
        normalized = _cott_normalize_scalar(value, annotation)
        return _cott_validate_abi(normalized, args[0], path=path)
    if origin in (Union, _types.UnionType):
        for candidate in args:
            try:
                return _cott_validate_abi(value, candidate, path=path)
            except CottContractViolation:
                pass
        raise CottContractViolation(f"{path} does not match ABI union", phase="validation")
    if origin is Literal:
        if any(type(value) is type(candidate) and value == candidate for candidate in args):
            return value
        raise CottContractViolation(f"{path} does not match ABI literal", phase="validation")
    if origin is type:
        if len(args) == 1 and value is args[0]:
            return value
        raise CottContractViolation(f"{path} does not match ABI Factory", phase="validation")
    if annotation is Any or annotation is object:
        return value
    if isinstance(annotation, TypeVar):
        return value
    if origin is _Generator or annotation is _Generator:
        if isinstance(value, _Generator):
            return value
        raise CottContractViolation(f"{path} does not match ABI generator", phase="validation")
    if origin is Iterator or annotation is Iterator:
        if isinstance(value, Iterator):
            return value
        raise CottContractViolation(f"{path} does not match ABI iterator", phase="validation")
    protocol = origin if isinstance(origin, type) and getattr(origin, "_is_protocol", False) else annotation
    if isinstance(protocol, type) and getattr(protocol, "_is_protocol", False):
        missing = [
            name
            for name, member in protocol.__dict__.items()
            if not name.startswith("_") and callable(member) and not hasattr(value, name)
        ]
        if not missing:
            return value
        raise CottContractViolation(f"{path} does not implement trait members: {', '.join(missing)}", phase="validation")
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
    if annotation is _Path and type(value) is _COTT_PATH_TYPE:
        return value
    if origin is Some and type(value) is Some:
        return Some(value=_cott_validate_abi(value.value, args[0] if args else Any, path=path))
    if origin is Ok and type(value) is Ok:
        return Ok(value=_cott_validate_abi(value.value, args[0] if args else Any, path=path))
    if origin is Err and type(value) is Err:
        return Err(error=_cott_validate_abi(value.error, args[0] if args else Any, path=path))
    if origin is Opaque and type(value) is Opaque:
        tags = _get_args(args[0]) if args and _get_origin(args[0]) is Literal else ()
        if len(tags) != 1 or type(tags[0]) is not str or value.tag != tags[0]:
            raise CottContractViolation(f"{path} has the wrong opaque tag", phase="validation")
        return value
    if origin is CottList and type(value) is CottList:
        item_type = args[0] if args else Any
        return CottList(values=(_cott_validate_abi(item, item_type, path=path) for item in value))
    if origin is CottSet and type(value) is CottSet:
        item_type = args[0] if args else Any
        return CottSet(values=(_cott_validate_abi(item, item_type, path=path) for item in value))
    if origin is FrozenMap and type(value) is FrozenMap:
        key_type, item_type = args if len(args) == 2 else (Any, Any)
        return FrozenMap(values={
            _cott_validate_abi(key, key_type, path=path): _cott_validate_abi(item, item_type, path=path)
            for key, item in value.items()
        })
    if origin is tuple:
        if type(value) is not tuple or len(value) != len(args):
            raise CottContractViolation(f"{path} does not match ABI tuple", phase="validation")
        return tuple(
            _cott_validate_abi(item, item_type, path=f"{path}[{index}]")
            for index, (item, item_type) in enumerate(zip(value, args))
        )
    if origin is CottArray:
        if type(value) is not CottArray or len(args) != 2:
            raise CottContractViolation(f"{path} does not match ABI array", phase="validation")
        length = _cott_fixed_length(args[1], path)
        if len(value) != length:
            raise CottContractViolation(f"{path} has the wrong array length", phase="validation")
        return CottArray(values=(
            _cott_validate_abi(item, args[0], path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ))
    if origin is CottBuffer:
        if type(value) is not CottBuffer or len(args) != 1:
            raise CottContractViolation(f"{path} does not match ABI buffer", phase="validation")
        length = _cott_fixed_length(args[0], path)
        if len(value.data) != length:
            raise CottContractViolation(f"{path} has the wrong buffer length", phase="validation")
        return value
    nominal = origin if isinstance(origin, type) and _dataclasses.is_dataclass(origin) else annotation
    if isinstance(nominal, type) and type(value) is nominal:
        if nominal is JsonArray or nominal is JsonObject:
            _cott_validate_json(value)
            return value
        if _dataclasses.is_dataclass(nominal):
            substitutions = dict(zip(getattr(nominal, "__parameters__", ()), args))
            hints = _get_type_hints(nominal, include_extras=True)
            return nominal(**{
                field.name: _cott_validate_abi(
                    getattr(value, field.name),
                    _cott_substitute_type(hints.get(field.name, Any), substitutions),
                    path=f"{path}.{field.name}",
                )
                for field in _dataclasses.fields(nominal)
            })
        return value
    raise CottContractViolation(f"{path} does not match ABI type", phase="validation")


def _cott_normalize_f32_abi(value: object, annotation: object, *, path: str = "$") -> object:
    """Normalize every concretely typed F32 while leaving other validation disabled."""
    origin = _get_origin(annotation)
    args = _get_args(annotation)
    if annotation is Any or annotation is object:
        return value
    if origin is Annotated:
        if any(isinstance(item, CottExternal) for item in args[1:]):
            return value
        metadata = next((item for item in args[1:] if isinstance(item, CottFloat)), None)
        return _cott_normalize_f32(value) if metadata is not None and metadata.bits == 32 else value
    if origin is _Generator or annotation is _Generator or origin is Iterator or annotation is Iterator:
        return value
    if origin in (Union, _types.UnionType):
        for candidate in args:
            candidate_origin = _get_origin(candidate)
            if (candidate_origin is not None and type(value) is candidate_origin) or (
                isinstance(candidate, type) and type(value) is candidate
            ):
                return _cott_normalize_f32_abi(value, candidate, path=path)
        return value
    if origin is Some and type(value) is Some:
        return Some(value=_cott_normalize_f32_abi(value.value, args[0] if args else Any, path=path))
    if origin is Ok and type(value) is Ok:
        return Ok(value=_cott_normalize_f32_abi(value.value, args[0] if args else Any, path=path))
    if origin is Err and type(value) is Err:
        return Err(error=_cott_normalize_f32_abi(value.error, args[0] if args else Any, path=path))
    if origin is CottList and type(value) is CottList:
        return CottList(values=(_cott_normalize_f32_abi(item, args[0], path=path) for item in value))
    if origin is CottSet and type(value) is CottSet:
        return CottSet(values=(_cott_normalize_f32_abi(item, args[0], path=path) for item in value))
    if origin is FrozenMap and type(value) is FrozenMap:
        return FrozenMap(values={
            _cott_normalize_f32_abi(key, args[0], path=path): _cott_normalize_f32_abi(item, args[1], path=path)
            for key, item in value.items()
        })
    if origin is tuple and type(value) is tuple and len(value) == len(args):
        return tuple(
            _cott_normalize_f32_abi(item, item_type, path=f"{path}[{index}]")
            for index, (item, item_type) in enumerate(zip(value, args))
        )
    if origin is CottArray and type(value) is CottArray and len(args) == 2:
        return CottArray(values=(
            _cott_normalize_f32_abi(item, args[0], path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ))
    nominal = origin if isinstance(origin, type) and _dataclasses.is_dataclass(origin) else annotation
    if isinstance(nominal, type) and type(value) is nominal and _dataclasses.is_dataclass(nominal):
        substitutions = dict(zip(getattr(nominal, "__parameters__", ()), args))
        hints = _get_type_hints(nominal, include_extras=True)
        return nominal(**{
            field.name: _cott_normalize_f32_abi(
                getattr(value, field.name),
                _cott_substitute_type(hints.get(field.name, Any), substitutions),
                path=f"{path}.{field.name}",
            )
            for field in _dataclasses.fields(nominal)
        })
    return value


class CottContractViolation(Exception):
    """Raised when a generated contract or provenance check is violated."""

    def __init__(
        self,
        message: str,
        *,
        symbol: str | None = None,
        phase: str | None = None,
        span: dict[str, int] | None = None,
        expected: str | None = None,
        actual: str | None = None,
        clause: str | None = None,
    ) -> None:
        self.message = message
        self.symbol = symbol
        self.phase = phase
        self.span = span
        self.expected = expected
        self.actual = actual
        self.clause = clause
        detail = message
        for label, value in (
            ("symbol", symbol),
            ("phase", phase),
            ("clause", clause),
            ("expected", expected),
            ("actual", actual),
        ):
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
_COTT_MODULE_CACHE: dict[str, tuple[_types.ModuleType, str, str]] = {}
_COTT_LOAD_CACHE: dict[tuple[str, str, str, str | None, str | None], tuple[_types.ModuleType, object, tuple[int, int, int, int, int], tuple[int, int, int, int, int]]] = {}
_COTT_LOAD_LOCK = _threading.RLock()


class _CottImplementationImportBlocker:
    def find_spec(self, fullname: str, path: object = None, target: object = None) -> object:
        if fullname == "_cott_impl" or fullname.startswith("_cott_impl."):
            raise ModuleNotFoundError("direct _cott_impl imports are compiler-owned")
        return None


if not any(type(finder) is _CottImplementationImportBlocker for finder in _sys.meta_path):
    _sys.meta_path.insert(0, _CottImplementationImportBlocker())


def _cott_violation(message: str, *, phase: str = "provenance") -> CottContractViolation:
    return CottContractViolation(message, symbol="_cott_load", phase=phase)


def _cott_regular_file_bytes(path: _Path, label: str) -> bytes:
    try:
        resolved = path.resolve(strict=True)
        if resolved != path:
            raise _cott_violation(f"{label} contains a symlink")
        metadata = path.stat()
        if not _stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise _cott_violation(f"{label} is not a regular file")
        return path.read_bytes()
    except CottContractViolation:
        raise
    except (OSError, ValueError) as error:
        raise _cott_violation(f"unable to read {label}: {error}") from error
def _cott_dependency_file_bytes(path: _Path, label: str) -> bytes:
    try:
        resolved = path.resolve(strict=True)
        if resolved != path:
            raise _cott_violation(f"{label} contains a symlink")
        metadata = path.stat()
        if not _stat.S_ISREG(metadata.st_mode):
            raise _cott_violation(f"{label} is not a regular file")
        return path.read_bytes()
    except CottContractViolation:
        raise
    except (OSError, ValueError) as error:
        raise _cott_violation(f"unable to read {label}: {error}") from error



def _cott_file_stamp(path: _Path, label: str) -> tuple[int, int, int, int, int]:
    try:
        metadata = path.lstat()
        if not _stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise _cott_violation(f"{label} is not a regular file")
        return (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns)
    except CottContractViolation:
        raise
    except (OSError, ValueError) as error:
        raise _cott_violation(f"unable to stat {label}: {error}") from error


def _cott_sha256(value: bytes) -> str:
    return "sha256:" + _hashlib.sha256(value).hexdigest()


def _cott_expected_digest(value: object, label: str) -> str:
    if type(value) is not str:
        raise _cott_violation(f"{label} must be a SHA-256 string")
    digest = value.removeprefix("sha256:")
    if len(digest) != 64 or any(char not in "0123456789abcdefABCDEF" for char in digest):
        raise _cott_violation(f"{label} must be a SHA-256 hex string")
    return "sha256:" + digest.lower()


def _cott_validate_python_tools(tools: object) -> None:
    if type(tools) is not dict or type(tools.get("python")) is not dict:
        raise _cott_violation("generation record omitted Python tool provenance")
    recorded = tools["python"]
    expected = {
        "implementation": _sys.implementation.name,
        "version": _platform.python_version(),
        "cache_tag": _sys.implementation.cache_tag,
        "os": _sys.platform,
        "machine": _platform.machine(),
        "platform": _sysconfig.get_platform(),
    }
    for key, actual in expected.items():
        if recorded.get(key) != actual:
            raise _cott_violation(f"Python runtime {key} mismatch")
    has_executable = "executable" in recorded
    has_hash = "content_hash" in recorded
    if has_executable != has_hash:
        raise _cott_violation("Python executable provenance is incomplete")
    if has_executable:
        try:
            runtime_executable = _Path(_sys.executable).resolve(strict=True)
            if _Path(recorded["executable"]).resolve(strict=True) != runtime_executable:
                raise _cott_violation("Python executable path mismatch")
        except CottContractViolation:
            raise
        except (OSError, TypeError, ValueError) as error:
            raise _cott_violation(f"invalid Python executable provenance: {error}") from error
        executable_hash = _cott_expected_digest(recorded.get("content_hash"), "Python executable hash")
        executable = _cott_regular_file_bytes(runtime_executable, "Python executable")
        if _cott_sha256(executable) != executable_hash:
            raise _cott_violation("Python executable hash mismatch")
    runtime = tools.get("runtime")
    if type(runtime) is not dict or runtime.get("abi") != _COTT_RUNTIME_ABI or runtime.get("version") != _COTT_RUNTIME_VERSION:
        raise _cott_violation("Cott runtime ABI or version mismatch")


def _cott_required_distributions(source: bytes, public_python_symbols: object) -> set[str]:
    try:
        tree = _ast.parse(source)
    except SyntaxError as error:
        raise _cott_violation(f"implementation source is not valid Python: {error}") from error
    if type(public_python_symbols) is not dict:
        raise _cott_violation("generation public Python symbols must be an object")
    project_modules = set()
    for module in public_python_symbols:
        if type(module) is not str or not module or any(not part.isidentifier() for part in module.split(".")):
            raise _cott_violation("generation contains an invalid public Python module")
        project_modules.update((module, f"{module}_types"))
    imports = set()
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, _ast.ImportFrom) and node.level == 0 and node.module:
            imports.add(node.module)
    stdlib = set(_sys.stdlib_module_names) | {"cott_runtime", "_cott_impl"}
    modules = {
        module.split(".", 1)[0]
        for module in imports
        if module not in project_modules and module.split(".", 1)[0] not in stdlib
    }
    owners = _metadata.packages_distributions()
    required = set()
    for module in sorted(modules):
        distributions = owners.get(module, [])
        if len(distributions) != 1:
            raise _cott_violation(f"external import {module!r} has ambiguous distribution ownership")
        required.add(distributions[0].lower().replace("_", "-"))
    return required


def _cott_validate_dependencies(dependencies: object, source: bytes, public_python_symbols: object) -> None:
    required = _cott_required_distributions(source, public_python_symbols)
    if type(dependencies) is not list:
        raise _cott_violation("generation dependencies must be an array")
    recorded_names = {
        dependency.get("name")
        for dependency in dependencies
        if type(dependency) is dict and type(dependency.get("name")) is str
    }
    if not required.issubset(recorded_names):
        raise _cott_violation("implementation external dependencies lack provenance")
    for dependency in dependencies:
        if type(dependency) is not dict:
            raise _cott_violation("generation dependency is not an object")
        name = dependency.get("name")
        version = dependency.get("version")
        installed = dependency.get("installed")
        if type(name) is not str or type(version) is not str or type(installed) is not dict:
            raise _cott_violation("dependency is missing installed provenance")
        try:
            distribution = _metadata.distribution(name)
            actual_name = distribution.metadata.get("Name")
            actual_version = distribution.version
            metadata = distribution.read_text("METADATA")
        except Exception as error:
            raise _cott_violation(f"unable to inspect dependency {name!r}: {error}") from error
        normalized = actual_name.lower().replace("_", "-") if type(actual_name) is str else ""
        if normalized != name or actual_version != version or installed.get("version") != version:
            raise _cott_violation(f"dependency {name!r} identity mismatch")
        expected_metadata = _cott_expected_digest(installed.get("metadata_hash"), f"dependency {name} METADATA hash")
        if metadata is None or _cott_sha256(metadata.encode()) != expected_metadata:
            raise _cott_violation(f"dependency {name!r} METADATA hash mismatch")
        origins = installed.get("origins")
        if type(origins) is not list or not origins:
            raise _cott_violation(f"dependency {name!r} omitted regular-file provenance")
        for origin in origins:
            if type(origin) is not dict or type(origin.get("path")) is not str:
                raise _cott_violation(f"dependency {name!r} has invalid file provenance")
            origin_path = origin["path"]
            if origin_path.startswith("/") or "\\" in origin_path:
                raise _cott_violation(f"dependency {name!r} has an invalid origin path")
            origin_parts = origin_path.split("/")
            if any(part in ("", ".", "..") for part in origin_parts):
                raise _cott_violation(f"dependency {name!r} has an invalid origin path")
            candidate = distribution.locate_file(origin_path)
            if candidate.is_symlink():
                raise _cott_violation(f"dependency {name!r} origin is a symlink")
            expected = _cott_expected_digest(origin.get("content_hash"), f"dependency {name} file hash")
            actual = _cott_sha256(_cott_dependency_file_bytes(candidate, f"dependency {name} file"))
            if actual != expected:
                raise _cott_violation(f"dependency {name!r} file hash mismatch")
def _cott_is_digest(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 71
        and value.startswith("sha256:")
        and all(character in "0123456789abcdef" for character in value[7:])
    )

def _cott_is_project_version(value: object) -> bool:
    if type(value) is not str:
        return False
    parts = value.split(".")
    return len(parts) == 3 and all(
        part and all(character in "0123456789" for character in part)
        and (part == "0" or not part.startswith("0"))
        for part in parts
    )


def _cott_is_verification(value: object) -> bool:
    if value is None:
        return True
    if type(value) is not dict:
        return False
    comparison = value.get("implementation_comparison")
    if comparison is None:
        return "implementation_comparison" not in value
    if type(comparison) is not dict or set(comparison) != {"baseline_generation_id", "status", "entries"}:
        return False
    baseline = comparison["baseline_generation_id"]
    status = comparison["status"]
    entries = comparison["entries"]
    if (
        (baseline is not None and not _cott_is_digest(baseline))
        or status not in ("no_baseline", "compared")
        or type(entries) is not list
        or status == "no_baseline" and (baseline is not None or entries)
        or status == "compared" and not _cott_is_digest(baseline)
    ):
        return False
    allowed_fields = {"content_hash", "concrete", "kind", "method", "owner", "python_symbol", "runtime_origin", "source_origin"}
    for entry in entries:
        if type(entry) is not dict or set(entry) != {"cott_symbol", "status", "changed_fields"}:
            return False
        changed_fields = entry["changed_fields"]
        if (
            type(entry["cott_symbol"]) is not str
            or entry["status"] not in ("added", "removed", "unchanged", "changed")
            or type(changed_fields) is not dict
            or set(changed_fields) - allowed_fields
            or entry["status"] == "unchanged" and changed_fields
            or entry["status"] != "unchanged" and not changed_fields
        ):
            return False
        for change in changed_fields.values():
            if (
                type(change) is not dict
                or set(change) != {"before", "after"}
                or change["before"] is not None and type(change["before"]) is not str
                or change["after"] is not None and type(change["after"]) is not str
            ):
                return False
    return True

def _cott_is_agent_run(value: object) -> bool:
    required = {
        "symbol", "adapter", "adapter_version", "argv_template", "executable", "executable_hash",
        "prompt_hash", "implementation_hash", "environment_names", "duration_ms", "status", "stdout", "stderr",
    }
    if type(value) is not dict or set(value) != required:
        return False
    if (
        any(type(value[field]) is not str for field in ("symbol", "adapter", "adapter_version", "executable", "executable_hash", "prompt_hash", "implementation_hash"))
        or type(value["argv_template"]) is not list
        or any(type(argument) is not str for argument in value["argv_template"])
        or type(value["environment_names"]) is not list
        or any(type(name) is not str for name in value["environment_names"])
        or type(value["duration_ms"]) is not int or not 0 <= value["duration_ms"] < 1 << 64
    ):
        return False
    status = value["status"]
    if type(status) is not dict or set(status) != {"exit_code", "signal", "timed_out", "cancelled"}:
        return False
    if any(
        code is not None and (type(code) is not int or not -(1 << 31) <= code < 1 << 31)
        for code in (status["exit_code"], status["signal"])
    ) or type(status["timed_out"]) is not bool or type(status["cancelled"]) is not bool:
        return False
    for stream in (value["stdout"], value["stderr"]):
        if type(stream) is not dict or set(stream) != {"bytes", "sha256", "truncated"}:
            return False
        if (
            type(stream["bytes"]) is not int or not 0 <= stream["bytes"] < 1 << 64
            or type(stream["sha256"]) is not str or type(stream["truncated"]) is not bool
        ):
            return False
    return True


def _cott_is_unresolved(value: object) -> bool:
    if type(value) is not dict or set(value) != {"cott_symbol", "kind", "span"}:
        return False
    if type(value["cott_symbol"]) is not str or not value["cott_symbol"] or value["kind"] not in ("function", "async_function", "impl_method"):
        return False
    span = value["span"]
    if type(span) is not dict or set(span) != {"start_byte", "end_byte", "start_line", "start_column", "end_line", "end_column"}:
        return False
    if any(type(span[key]) is not int for key in span):
        return False
    return (
        span["end_byte"] >= span["start_byte"]
        and span["end_line"] >= span["start_line"]
        and span["start_line"] > 0
        and span["start_column"] > 0
        and span["end_line"] > 0
        and span["end_column"] > 0
    )

def _cott_validate_generation_snapshot(snapshot: object, label: str) -> dict[object, object]:
    required = {
        "generation_id", "verified", "project_version", "compatibility", "inputs", "tools", "ir",
        "contract_surface", "public_python_symbols", "implementations", "dependencies", "managed_files",
        "unresolved", "verification", "agent_runs",
    }
    if type(snapshot) is not dict or set(snapshot) != required:
        raise _cott_violation(f"{label} generation snapshot is malformed")
    if not _cott_is_digest(snapshot["generation_id"]) or type(snapshot["verified"]) is not bool or not _cott_is_project_version(snapshot["project_version"]):
        raise _cott_violation(f"{label} generation snapshot identity is malformed")
    compatibility = snapshot["compatibility"]
    if (
        type(compatibility) is not dict
        or set(compatibility) != {"generation_schema", "canonical_ir_schema", "runtime_abi"}
        or any(type(compatibility[key]) is not int for key in compatibility)
        or compatibility != {"generation_schema": 2, "canonical_ir_schema": 5, "runtime_abi": 2}
    ):
        raise _cott_violation(f"{label} generation compatibility is incompatible")
    for field in ("inputs", "ir", "managed_files"):
        value = snapshot[field]
        if type(value) is not dict or any(not _cott_is_digest(digest) for digest in value.values()):
            raise _cott_violation(f"{label} generation {field} is malformed")
    if type(snapshot["tools"]) is not dict or type(snapshot["contract_surface"]) is not dict:
        raise _cott_violation(f"{label} generation metadata is malformed")
    public_python_symbols = snapshot["public_python_symbols"]
    if type(public_python_symbols) is not dict or any(
        type(module) is not str or type(symbols) is not list or any(type(symbol) is not str for symbol in symbols)
        for module, symbols in public_python_symbols.items()
    ):
        raise _cott_violation(f"{label} generation public Python symbols are malformed")
    implementations = snapshot["implementations"]
    if type(implementations) is not list:
        raise _cott_violation(f"{label} generation implementations must be an array")
    for implementation in implementations:
        complete = {"cott_symbol", "owner", "python_symbol", "source_origin", "runtime_origin", "content_hash", "kind", "concrete", "method"}
        if type(implementation) is not dict or set(implementation) != complete:
            raise _cott_violation("generation implementation is malformed")
        if (
            any(type(implementation[field]) is not str for field in ("cott_symbol", "python_symbol", "source_origin", "runtime_origin"))
            or implementation["owner"] not in ("manifest", "agent")
            or not _cott_is_digest(implementation["content_hash"])
        ):
            raise _cott_violation("generation implementation is malformed")
        kind = implementation["kind"]
        concrete = implementation["concrete"]
        method = implementation["method"]
        if kind in ("function", "async_function") and concrete is None and method is None:
            continue
        if kind == "impl_method" and type(concrete) is str and concrete and type(method) is str and method:
            continue
        raise _cott_violation("generation implementation kind is malformed")
    dependencies = snapshot["dependencies"]
    if type(dependencies) is not list:
        raise _cott_violation(f"{label} generation dependencies must be an array")
    for dependency in dependencies:
        required_dependency = {"name", "version", "lock_hash", "artifacts"}
        allowed_dependency = required_dependency | {"installed"}
        if type(dependency) is not dict or not required_dependency <= set(dependency) or set(dependency) - allowed_dependency:
            raise _cott_violation("generation dependency is malformed")
        if (
            type(dependency["name"]) is not str or not dependency["name"]
            or type(dependency["version"]) is not str or not dependency["version"]
            or not _cott_is_digest(dependency["lock_hash"])
            or type(dependency["artifacts"]) is not list
            or any(not _cott_is_digest(artifact) for artifact in dependency["artifacts"])
            or len(set(dependency["artifacts"])) != len(dependency["artifacts"])
            or ("installed" in dependency and type(dependency["installed"]) is not dict)
        ):
            raise _cott_violation("generation dependency is malformed")
    if (
        type(snapshot["unresolved"]) is not list
        or any(not _cott_is_unresolved(record) for record in snapshot["unresolved"])
        or not _cott_is_verification(snapshot["verification"])
        or type(snapshot["agent_runs"]) is not list
        or any(not _cott_is_agent_run(agent_run) for agent_run in snapshot["agent_runs"])
    ):
        raise _cott_violation(f"{label} generation metadata is malformed")
    return snapshot


def _cott_validate_generation_identity(snapshot: dict[object, object]) -> str:
    generation_id = snapshot["generation_id"]
    current = dict(snapshot)
    for key in ("generation_id", "verified", "verification", "agent_runs"):
        current.pop(key)
    expected_id = _cott_sha256(
        _json.dumps(
            {"domain": "cott.generation.v2", "schema_version": 2, "current": current},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        + b"\n"
    )
    if generation_id != expected_id:
        raise _cott_violation("generation identity mismatch")
    return generation_id


def _cott_validate_generation(root: _Path, relative_path: str, digest: str, symbol: str, project: str | None, cott_symbol: str | None, source: bytes) -> str:
    artifact_root = root.parent if root.name == "python" else root
    generation_path = artifact_root / "generation.json"
    try:
        current_record = _json.loads(_cott_regular_file_bytes(generation_path, "generation record"))
    except (TypeError, ValueError) as error:
        raise _cott_violation(f"generation record is malformed: {error}") from error
    if (
        type(current_record) is not dict
        or set(current_record) != {"schema_version", "current", "last_verified"}
        or type(current_record["schema_version"]) is not int
        or current_record["schema_version"] != 2
    ):
        raise _cott_violation("generation record is malformed")
    current = _cott_validate_generation_snapshot(current_record["current"], "current")
    last_verified = current_record["last_verified"]
    if last_verified is not None:
        last_verified = _cott_validate_generation_snapshot(last_verified, "last verified")
        if not last_verified["verified"]:
            raise _cott_violation("last verified generation snapshot is not verified")
        _cott_validate_generation_identity(last_verified)
    generation_id = _cott_validate_generation_identity(current)
    if current["project_version"] != PROJECT_VERSION:
        raise _cott_violation("generation project version mismatch")
    _cott_validate_python_tools(current["tools"])
    _cott_validate_dependencies(current["dependencies"], source, current["public_python_symbols"])
    implementations = current["implementations"]
    selected_origin = (("python/" if root.name == "python" else "") + relative_path)
    selected_python_symbol = f"{relative_path[:-3].replace('/', '.')}:{symbol}"
    matches = []
    for implementation in implementations:
        kind = implementation.get("kind")
        concrete = implementation.get("concrete")
        method = implementation.get("method")
        if kind is None:
            if symbol.startswith("_cott_impl_"):
                raise _cott_violation("generation implementation kind is malformed")
            kind = "function"
        if kind == "function":
            if concrete is not None or method is not None:
                raise _cott_violation("free-function provenance must not name an implementation method")
        elif kind == "impl_method":
            if not concrete.isidentifier() or not method.isidentifier():
                raise _cott_violation("implementation-method provenance is malformed")
        if (
            implementation["runtime_origin"] == selected_origin
            and implementation["python_symbol"] == selected_python_symbol
            and implementation["content_hash"] == digest
            and (cott_symbol is None or implementation["cott_symbol"] == cott_symbol)
        ):
            matches.append(implementation)
    if len(matches) != 1:
        raise _cott_violation("selected implementation does not match generation provenance")
    return generation_id


def _cott_load(relative_path: str, expected_sha256: str, symbol: str, project_name: str | None = None, *, expected_project_name: str | None = None, expected_cott_symbol: str | None = None):
    if project_name is not None and expected_project_name is not None and project_name != expected_project_name:
        raise _cott_violation("conflicting project identities", phase="facade-import")
    expected_project = project_name if expected_project_name is None else expected_project_name
    _cott_check_project_identity(expected_project, phase="facade-import")
    if type(relative_path) is not str or type(expected_sha256) is not str:
        raise _cott_violation("binding path and hash must be strings")
    if type(symbol) is not str or not symbol.isidentifier():
        raise _cott_violation("binding symbol must be an identifier")
    if expected_cott_symbol is not None and (type(expected_cott_symbol) is not str or not expected_cott_symbol):
        raise _cott_violation("Cott symbol must be a string")
    if not relative_path or "\\" in relative_path:
        raise _cott_violation("binding path must be a normalized relative POSIX path")
    parts = relative_path.split("/")
    if len(parts) < 2 or parts[0] != "_cott_impl" or any(part in ("", ".", "..") for part in parts):
        raise _cott_violation("binding path must be below _cott_impl")
    if any(not part.isidentifier() for part in parts[:-1]) or not parts[-1].endswith(".py") or parts[-1] == "__init__.py" or not parts[-1][:-3].isidentifier():
        raise _cott_violation("binding path contains an invalid module name")
    module_name = ".".join(parts)[:-3]
    digest_input = _cott_expected_digest(expected_sha256, "binding hash")
    root = _Path(__file__).resolve().parent.parent
    path = root.joinpath(*parts)
    generation_path = (root.parent if root.name == "python" else root) / "generation.json"
    cache_key = (relative_path, digest_input, symbol, expected_project, expected_cott_symbol)
    with _COTT_LOAD_LOCK:
        cached_load = _COTT_LOAD_CACHE.get(cache_key)
        if cached_load is not None:
            module, implementation, implementation_stamp, generation_stamp = cached_load
            if (
                _sys.modules.get(module_name) is module
                and _cott_file_stamp(path, f"binding {relative_path}") == implementation_stamp
                and _cott_file_stamp(generation_path, "generation record") == generation_stamp
            ):
                return implementation
            del _COTT_LOAD_CACHE[cache_key]

    source = _cott_regular_file_bytes(path, f"binding {relative_path}")
    digest = _cott_sha256(source)
    if digest != digest_input:
        raise _cott_violation(f"binding hash mismatch for {relative_path}")
    generation_id = _cott_validate_generation(root, relative_path, digest, symbol, expected_project, expected_cott_symbol, source)

    with _COTT_LOAD_LOCK:
        cached = _COTT_MODULE_CACHE.get(module_name)
        if cached is not None:
            module, cached_digest, cached_generation = cached
            if cached_digest != digest or cached_generation != generation_id or _sys.modules.get(module_name) is not module:
                raise _cott_violation(f"canonical module cache conflict for {module_name}")
            try:
                implementation = getattr(module, symbol)
            except AttributeError as error:
                raise _cott_violation(f"binding symbol {symbol!r} is missing") from error
            _COTT_LOAD_CACHE[cache_key] = (
                module,
                implementation,
                _cott_file_stamp(path, f"binding {relative_path}"),
                _cott_file_stamp(generation_path, "generation record"),
            )
            return implementation
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
        _COTT_MODULE_CACHE[module_name] = (module, digest, generation_id)
        try:
            implementation = getattr(module, symbol)
        except AttributeError as error:
            del _COTT_MODULE_CACHE[module_name]
            if _sys.modules.get(module_name) is module:
                del _sys.modules[module_name]
            raise _cott_violation(f"binding symbol {symbol!r} is missing") from error
        _COTT_LOAD_CACHE[cache_key] = (
            module,
            implementation,
            _cott_file_stamp(path, f"binding {relative_path}"),
            _cott_file_stamp(generation_path, "generation record"),
        )
        return implementation


__all__ = [
    "CottArray", "CottBuffer", "CottContractViolation", "CottExternal", "CottFloat", "CottInt", "CottList", "CottSet", "Err", "F32", "F64", "FrozenMap",
    "I8", "I16", "I32", "I64", "JsonArray", "JsonBoolean", "JsonFloat", "JsonInteger", "JsonNull", "JsonObject", "JsonString", "JsonValue",
    "Never", "Nothing", "Ok", "Opaque", "Option", "PROJECT_NAME", "PROJECT_VERSION", "Result", "Some", "U8", "U16", "U32", "U64", "UNIT", "Unit",
]
