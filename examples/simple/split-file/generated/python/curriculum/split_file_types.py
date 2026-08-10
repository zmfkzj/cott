from __future__ import annotations

import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SplitRequest:
    __hash__ = None
    lines: CottList[str]
    chunk_size: I64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SplitFileError_InvalidChunkSize:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SplitFileError_OutputLimitExceeded:
    pass

SplitFileError: TypeAlias = Union[SplitFileError_InvalidChunkSize, SplitFileError_OutputLimitExceeded]

"""Validates the requested chunk size and output budget. Chunk size must be
from 1 through 10000 inclusive. A valid request may produce at most 10000
chunks. InvalidChunkSize is checked before OutputLimitExceeded."""
"""Validates the request, then splits its lines into consecutive chunks in
input order. A valid empty line list produces an empty outer list. Every
chunk except possibly the last has exactly chunk_size lines, and no line is
omitted or duplicated."""
__all__ = ["SplitFileError", "SplitFileError_InvalidChunkSize", "SplitFileError_OutputLimitExceeded", "SplitRequest"]
