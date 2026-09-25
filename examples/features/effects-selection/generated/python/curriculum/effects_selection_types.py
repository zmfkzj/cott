from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EffectError_InputMissing:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EffectError_OperationFailed:
    __hash__ = None
    message: str

EffectError: TypeAlias = Union[EffectError_InputMissing, EffectError_OperationFailed]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileText:
    __hash__ = None
    path: Path
    text: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, Path, path="$.path"))
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CopyReceipt:
    __hash__ = None
    destination: Path
    bytes_written: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "destination", _cott_validate_abi(self.destination, Path, path="$.destination"))
        if not _cott_validated_construction():
            object.__setattr__(self, "bytes_written", _cott_validate_abi(self.bytes_written, U64, path="$.bytes_written"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PageText:
    __hash__ = None
    url: str
    text: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "url", _cott_validate_abi(self.url, str, path="$.url"))
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))

"""Read the file at source and decode its bytes as strict UTF-8. The result
pairs the decoded text with source. An absent source returns InputMissing
carrying source; any other read failure and bytes that are not valid UTF-8
return OperationFailed."""
"""Copy the text of source to destination as UTF-8 bytes. bytes_written is
the encoded byte count, not the character count. A read_text error is
returned unchanged and destination is left untouched."""
"""GET url over HTTP, following redirects, and decode the final response body
as strict UTF-8. The result pairs the text with the requested url. An empty
url returns OperationFailed without sending a request; a connection or read
failure, a timeout, a final status outside 200-299 and a body that is not
valid UTF-8 return OperationFailed."""
"""Store value under key in the SQLite database file at database, replacing
any previous value for key, then read the value stored under key back from
that database. Any SQLite failure returns OperationFailed."""
"""Read the compiler-owned clock fixture and return its time in nanoseconds.
The fixture is configured in milliseconds, so start_ms 17 reads as
17000000. Reading does not advance the clock."""
"""Choose an index below limit from seed."""
"""Terminate the current process."""
__all__ = ["CopyReceipt", "EffectError", "EffectError_InputMissing", "EffectError_OperationFailed", "FileText", "PageText"]
