from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.files_types import FileError as FileError, FileError_Failed as FileError_Failed, FileError_InvalidEncoding as FileError_InvalidEncoding, FileError_IsADirectory as FileError_IsADirectory, FileError_NotFound as FileError_NotFound, FileError_PermissionDenied as FileError_PermissionDenied
"""Read the file at path as UTF-8 text (universal newlines are NOT translated:
bytes are decoded as they are). A missing file is NotFound(path); a
directory is IsADirectory(path); an access refusal is PermissionDenied(path);
bytes that are not UTF-8 are InvalidEncoding(path); any other OS error is
Failed(path, message) with the OS error text."""
def load_text_file(path: Path) -> Result[str, FileError]: ...

"""Write text to path as UTF-8, creating missing parent directories, through a
temporary file in the same directory that is flushed, fsynced and then
atomically renamed over path (os.replace), so a failed save leaves any
previous file unchanged; the temporary file is removed on failure. Returns
the number of bytes written. An existing directory at path is
IsADirectory(path); an access refusal is PermissionDenied(path); any other
failure is Failed(path, message)."""
def save_text_file(path: Path, text: str) -> Result[U64, FileError]: ...

"""Turn what a user typed into a path: surrounding whitespace removed; a
leading "~" or "~/" is replaced by home; a relative path is joined to cwd;
the result is normalized lexically (os.path.normpath) without resolving
symlinks. An empty text is cwd."""
def expand_path(text: str, home: Path, cwd: Path) -> Path: ...

"""Tab completion for a path input: the directory part of text (up to and
including its last "/", or "" for none) is expanded like expand_path and
listed; entries whose name starts with the remaining text (hidden entries
only when that text starts with ".") are returned as the original directory
part followed by the entry name, with "/" appended for directories, sorted
by name. A directory that cannot be listed yields []."""
def complete_path(text: str, home: Path, cwd: Path) -> CottList[str]: ...

__all__ = ["FileError", "FileError_Failed", "FileError_InvalidEncoding", "FileError_IsADirectory", "FileError_NotFound", "FileError_PermissionDenied", "complete_path", "expand_path", "load_text_file", "save_text_file"]
