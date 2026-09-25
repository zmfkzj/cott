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
class AccessCodeError_LegacyFormat:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AccessCodeError_EmptyCode:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AccessCodeError_TooShort:
    pass

AccessCodeError: TypeAlias = Union[AccessCodeError_LegacyFormat, AccessCodeError_EmptyCode, AccessCodeError_TooShort]

"""Base rule requires a nonempty success value and allows a legacy-format failure.
The strict rule strengthens that success obligation and removes the error."""
class BaseAccessCodeRule:
    pass

"""Current rule strengthens the minimum success length from one to four, then
deletes the legacy-format error allowance."""
class StrictAccessCodeRule(BaseAccessCodeRule):
    pass

"""Validate a code without modifying it: empty input fails first, then a code
shorter than four characters fails. A legacy prefix is not rejected."""
__all__ = ["AccessCodeError", "AccessCodeError_EmptyCode", "AccessCodeError_LegacyFormat", "AccessCodeError_TooShort", "BaseAccessCodeRule", "StrictAccessCodeRule"]
