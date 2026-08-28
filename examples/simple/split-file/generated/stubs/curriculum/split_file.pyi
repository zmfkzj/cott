from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.split_file_types import SplitFileError as SplitFileError, SplitFileError_InvalidChunkSize as SplitFileError_InvalidChunkSize, SplitFileError_OutputLimitExceeded as SplitFileError_OutputLimitExceeded, SplitRequest as SplitRequest
"""Validates the requested chunk size and output budget. Chunk size must be
from 1 through 10000 inclusive. A valid request may produce at most 10000
chunks. InvalidChunkSize is checked before OutputLimitExceeded."""
def validate_split_request(request: SplitRequest) -> Result[Unit, SplitFileError]: ...

"""Validates the request, then splits its lines into consecutive chunks in
input order. A valid empty line list produces an empty outer list. Every
chunk except possibly the last has exactly chunk_size lines, and no line is
omitted or duplicated."""
def split_lines(request: SplitRequest) -> Result[CottList[CottList[str]], SplitFileError]: ...

__all__ = ["SplitFileError", "SplitFileError_InvalidChunkSize", "SplitFileError_OutputLimitExceeded", "SplitRequest", "split_lines", "validate_split_request"]
