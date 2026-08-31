from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerOptions:
    __hash__ = None
    sources: CottList[Path]
    contains: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "sources", _cott_validate_abi(self.sources, CottList[Path], path="$.sources"))
        if not _cott_validated_construction():
            object.__setattr__(self, "contains", _cott_validate_abi(self.contains, Option[str], path="$.contains"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LogEntry:
    __hash__ = None
    source: Path
    line: U64
    text: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "source", _cott_validate_abi(self.source, Path, path="$.source"))
        if not _cott_validated_construction():
            object.__setattr__(self, "line", _cott_validate_abi(self.line, U64, path="$.line"))
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ToolongError_InvalidArguments:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ToolongError_ReadFailed:
    __hash__ = None
    path: Path
    message: str

ToolongError: TypeAlias = Union[ToolongError_InvalidArguments, ToolongError_ReadFailed]

"""Parse [--contains TEXT] followed by one or more log paths."""
"""Read UTF-8 log lines in source order and number each source from one."""
"""Keep all entries without a filter; otherwise keep case-insensitive substring matches."""
"""Render path:line and text for each entry, separated by newlines."""
"""Parse arguments, load logs, apply the optional filter, and render matching entries."""
__all__ = ["LogEntry", "ToolongError", "ToolongError_InvalidArguments", "ToolongError_ReadFailed", "ViewerOptions"]
