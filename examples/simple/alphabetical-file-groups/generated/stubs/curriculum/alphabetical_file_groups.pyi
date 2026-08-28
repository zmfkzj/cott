from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.alphabetical_file_groups_types import FileGroupError as FileGroupError, FileGroupError_EmptyFilename as FileGroupError_EmptyFilename, FileMove as FileMove
"""Classify one filename by its first Unicode code point.

Return EmptyFilename for an empty filename. Otherwise copy the filename
unchanged and select the full Unicode case-fold of a leading letter as its
folder. Select "misc" when the leading code point is not a letter."""
def classify_filename(filename: str) -> Result[FileMove, FileGroupError]: ...

"""Classify each filename in input order with classify_filename.

Stop at the first EmptyFilename error and propagate it unchanged. Otherwise
return one FileMove per input in the same order. An empty input list
succeeds with an empty move list."""
def group_filenames(filenames: CottList[str]) -> Result[CottList[FileMove], FileGroupError]: ...

__all__ = ["FileGroupError", "FileGroupError_EmptyFilename", "FileMove", "classify_filename", "group_filenames"]
