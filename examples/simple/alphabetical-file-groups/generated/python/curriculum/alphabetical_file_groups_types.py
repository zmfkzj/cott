from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileMove:
    __hash__ = None
    filename: str
    folder: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "filename", _cott_validate_abi(self.filename, str, path="$.filename"))
        if not _cott_validated_construction():
            object.__setattr__(self, "folder", _cott_validate_abi(self.folder, str, path="$.folder"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileGroupError_EmptyFilename:
    pass

FileGroupError: TypeAlias = Union[FileGroupError_EmptyFilename]

"""Classify one filename by its first Unicode code point.

Return EmptyFilename for an empty filename. Otherwise copy the filename
unchanged and select the full Unicode case-fold of a leading letter as its
folder. Select "misc" when the leading code point is not a letter."""
"""Classify each filename in input order with classify_filename.

Stop at the first EmptyFilename error and propagate it unchanged. Otherwise
return one FileMove per input in the same order. An empty input list
succeeds with an empty move list."""
__all__ = ["FileGroupError", "FileGroupError_EmptyFilename", "FileMove"]
