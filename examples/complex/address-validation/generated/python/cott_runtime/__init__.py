# Cott's compiler-owned Python runtime.

# This module intentionally depends only on Python's standard library.
from __future__ import annotations


import hashlib as _hashlib
import json as _json
import os as _os
from dataclasses import dataclass
from pathlib import Path as _Path
import stat as _stat
import sys as _sys
import threading as _threading
import types as _types
from typing import Generic, TypeAlias, TypeVar, Union


# The compiler embeds this value in every generated runtime.
PROJECT_NAME = 'address-validation'
_COTT_PROJECT_NAME = PROJECT_NAME
_COTT_RUNTIME_ABI = "1"


_T = TypeVar("_T")
_E = TypeVar("_E")


@dataclass(frozen=True, slots=True, kw_only=True)
class Ok(Generic[_T]):
    value: _T


@dataclass(frozen=True, slots=True, kw_only=True)
class Err(Generic[_E]):
    error: _E


@dataclass(frozen=True, slots=True, kw_only=True)
class Some(Generic[_T]):
    value: _T


@dataclass(frozen=True, slots=True, kw_only=True, repr=False)
class Nothing:
    def __repr__(self) -> str:
        return "Nothing()"


Result: TypeAlias = Union[Ok[_T], Err[_E]]
Option: TypeAlias = Union[Some[_T], Nothing]


@dataclass(frozen=True, slots=True, kw_only=True, repr=False)
class Unit:
    _instance = None

    def __new__(cls):
        instance = cls._instance
        if instance is None:
            instance = object.__new__(cls)
            cls._instance = instance
        return instance

    def __repr__(self) -> str:
        return "UNIT"


UNIT = Unit()


class CottContractViolation(Exception):
    """Raised when a generated contract or provenance check is violated."""

    def __init__(self, message: str, *, function: str | None = None, clause: str | None = None):
        self.message = message
        self.function = function
        self.clause = clause
        detail = message
        if function is not None:
            detail = f"{detail} [function={function}]"
        if clause is not None:
            detail = f"{detail} [clause={clause}]"
        super().__init__(detail)


def _cott_display(value: object) -> str:
    """Return a deterministic, human-readable representation of a Cott value."""
    if value is UNIT:
        return "UNIT"
    if isinstance(value, Ok):
        return f"Ok(value={_cott_display(value.value)})"
    if isinstance(value, Err):
        return f"Err(error={_cott_display(value.error)})"
    if isinstance(value, Some):
        return f"Some(value={_cott_display(value.value)})"
    if isinstance(value, Nothing):
        return "Nothing()"
    if isinstance(value, Unit):
        return "UNIT"
    if value is None or isinstance(value, (bool, int, float)):
        return repr(value)
    if isinstance(value, str):
        return _json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, bytes):
        return "0x" + value.hex()
    if isinstance(value, tuple):
        items = ", ".join(_cott_display(item) for item in value)
        if len(value) == 1:
            items += ","
        return f"({items})"
    if isinstance(value, list):
        return "[" + ", ".join(_cott_display(item) for item in value) + "]"
    if isinstance(value, (set, frozenset)):
        return "{" + ", ".join(sorted(_cott_display(item) for item in value)) + "}"
    if isinstance(value, dict):
        items = sorted((_cott_display(key), _cott_display(item)) for key, item in value.items())
        return "{" + ", ".join(f"{key}: {item}" for key, item in items) + "}"
    return repr(value)


_COTT_MODULE_CACHE: dict[str, tuple[_types.ModuleType, str]] = {}
_COTT_LOAD_LOCK = _threading.RLock()


def _cott_violation(message: str) -> CottContractViolation:
    return CottContractViolation(message, function="_cott_load")


def _cott_load(relative_path: str, expected_sha256: str, symbol: str):
    """Verify and lazily load one generated implementation symbol."""
    if not isinstance(relative_path, str) or not isinstance(expected_sha256, str):
        raise _cott_violation("binding path and hash must be strings")
    if not isinstance(symbol, str) or not symbol.isidentifier():
        raise _cott_violation("binding symbol must be an identifier")
    if not relative_path or "\\" in relative_path:
        raise _cott_violation("binding path must be a normalized relative POSIX path")
    parts = relative_path.split("/")
    if len(parts) < 2 or parts[0] != "_cott_impl" or any(part in ("", ".", "..") for part in parts):
        raise _cott_violation("binding path must be below _cott_impl")
    if parts[-1] == "__init__.py" or not parts[-1].endswith(".py"):
        raise _cott_violation("binding path must name a Python implementation file")

    module_name = ".".join(parts)[:-3]
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
    expected = expected_sha256.removeprefix("sha256:")
    if digest != expected:
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
        except BaseException as error:
            if _sys.modules.get(module_name) is module:
                del _sys.modules[module_name]
            if isinstance(error, CottContractViolation):
                raise
            raise _cott_violation(f"failed to load binding {relative_path}: {error}") from error
        _COTT_MODULE_CACHE[module_name] = (module, digest)
        try:
            return getattr(module, symbol)
        except AttributeError as error:
            del _COTT_MODULE_CACHE[module_name]
            if _sys.modules.get(module_name) is module:
                del _sys.modules[module_name]
            raise _cott_violation(f"binding symbol {symbol!r} is missing") from error


__all__ = [
    "CottContractViolation",
    "Err",
    "Nothing",
    "Ok",
    "Option",
    "PROJECT_NAME",
    "Result",
    "Some",
    "UNIT",
    "Unit",
]
