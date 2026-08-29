from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
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

"""Read UTF-8 text from a compiler-owned filesystem fixture."""
"""Read source through its public facade and atomically replace destination."""
"""Fetch UTF-8 text from a compiler-owned local HTTP fixture."""
"""Return whether a text effect result is successful."""
"""Return successful text, or an empty string for an error result."""
"""Return whether a copy effect result is successful."""
"""Store value under key in a SQLite database, then read that value back."""
"""Return a compiler-owned deterministic fixture clock in nanoseconds."""
"""Choose one index below limit from a deterministic seeded random stream."""
"""End the current process with code."""
__all__ = ["EffectError", "EffectError_InputMissing", "EffectError_OperationFailed"]
