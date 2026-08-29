from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LogSource:
    __hash__ = None
    path: Path

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, Path, path="$.path"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LogEntry:
    __hash__ = None
    source: Path
    record: U64
    byte_offset: U64
    timestamp: Option[str]
    kind: EntryKind
    text: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "source", _cott_validate_abi(self.source, Path, path="$.source"))
        if not _cott_validated_construction():
            object.__setattr__(self, "record", _cott_validate_abi(self.record, U64, path="$.record"))
        if not _cott_validated_construction():
            object.__setattr__(self, "byte_offset", _cott_validate_abi(self.byte_offset, U64, path="$.byte_offset"))
        if not _cott_validated_construction():
            object.__setattr__(self, "timestamp", _cott_validate_abi(self.timestamp, Option[str], path="$.timestamp"))
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, EntryKind, path="$.kind"))
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LogPage:
    __hash__ = None
    source: LogSource
    entries: CottList[LogEntry]
    next_byte: U64
    complete: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "source", _cott_validate_abi(self.source, LogSource, path="$.source"))
        if not _cott_validated_construction():
            object.__setattr__(self, "entries", _cott_validate_abi(self.entries, CottList[LogEntry], path="$.entries"))
        if not _cott_validated_construction():
            object.__setattr__(self, "next_byte", _cott_validate_abi(self.next_byte, U64, path="$.next_byte"))
        if not _cott_validated_construction():
            object.__setattr__(self, "complete", _cott_validate_abi(self.complete, bool, path="$.complete"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EntryKind_Access:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EntryKind_Error:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EntryKind_Json:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EntryKind_Plain:
    pass

EntryKind: TypeAlias = Union[EntryKind_Access, EntryKind_Error, EntryKind_Json, EntryKind_Plain]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ToolongError_InvalidLimit:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ToolongError_InvalidIndent:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ToolongError_InvalidOffset:
    __hash__ = None
    path: Path
    offset: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ToolongError_OpenFailed:
    __hash__ = None
    path: Path
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ToolongError_DecodeFailed:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ToolongError_CompressedAppendUnsupported:
    __hash__ = None
    path: Path

ToolongError: TypeAlias = Union[ToolongError_InvalidLimit, ToolongError_InvalidIndent, ToolongError_InvalidOffset, ToolongError_OpenFailed, ToolongError_DecodeFailed, ToolongError_CompressedAppendUnsupported]

__all__ = ["EntryKind", "EntryKind_Access", "EntryKind_Error", "EntryKind_Json", "EntryKind_Plain", "LogEntry", "LogPage", "LogSource", "ToolongError", "ToolongError_CompressedAppendUnsupported", "ToolongError_DecodeFailed", "ToolongError_InvalidIndent", "ToolongError_InvalidLimit", "ToolongError_InvalidOffset", "ToolongError_OpenFailed"]
