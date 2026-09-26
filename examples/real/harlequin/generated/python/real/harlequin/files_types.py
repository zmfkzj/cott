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
class FileError_NotFound:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileError_IsADirectory:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileError_PermissionDenied:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileError_InvalidEncoding:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileError_Failed:
    __hash__ = None
    path: Path
    message: str

FileError: TypeAlias = Union[FileError_NotFound, FileError_IsADirectory, FileError_PermissionDenied, FileError_InvalidEncoding, FileError_Failed]

"""Read the file at path as UTF-8 text (universal newlines are NOT translated:
bytes are decoded as they are). A missing file is NotFound(path); a
directory is IsADirectory(path); an access refusal is PermissionDenied(path);
bytes that are not UTF-8 are InvalidEncoding(path); any other OS error is
Failed(path, message) with the OS error text."""
"""Write text to path as UTF-8, creating missing parent directories, through a
temporary file in the same directory that is flushed, fsynced and then
atomically renamed over path (os.replace), so a failed save leaves any
previous file unchanged; the temporary file is removed on failure. Returns
the number of bytes written. An existing directory at path is
IsADirectory(path); an access refusal is PermissionDenied(path); any other
failure is Failed(path, message)."""
"""Turn what a user typed into a path: surrounding whitespace removed; a
leading "~" or "~/" is replaced by home; a relative path is joined to cwd;
the result is normalized lexically (os.path.normpath) without resolving
symlinks. An empty text is cwd."""
"""Tab completion for a path input: the directory part of text (up to and
including its last "/", or "" for none) is expanded like expand_path and
listed; entries whose name starts with the remaining text (hidden entries
only when that text starts with ".") are returned as the original directory
part followed by the entry name, with "/" appended for directories, sorted
by name. A directory that cannot be listed yields []."""
__all__ = ["FileError", "FileError_Failed", "FileError_InvalidEncoding", "FileError_IsADirectory", "FileError_NotFound", "FileError_PermissionDenied"]
