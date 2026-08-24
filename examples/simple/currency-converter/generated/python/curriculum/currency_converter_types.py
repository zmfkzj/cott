from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottExternal, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Rate:
    __hash__ = None
    code: str
    per_eur: F64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConversionRequest:
    __hash__ = None
    quantity: F64
    from_currency: str
    to_currency: str
    eur_rates: CottList[Rate]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CurrencyError_NonFiniteQuantity:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CurrencyError_NegativeQuantity:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CurrencyError_InvalidCurrencyCode:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CurrencyError_NonFiniteRate:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CurrencyError_NonPositiveRate:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CurrencyError_DuplicateRate:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CurrencyError_MissingRate:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CurrencyError_NonFiniteResult:
    pass

CurrencyError: TypeAlias = Union[CurrencyError_NonFiniteQuantity, CurrencyError_NegativeQuantity, CurrencyError_InvalidCurrencyCode, CurrencyError_NonFiniteRate, CurrencyError_NonPositiveRate, CurrencyError_DuplicateRate, CurrencyError_MissingRate, CurrencyError_NonFiniteResult]

"""Validates a currency conversion request and its complete EUR rate list,
returning Ok(Unit) when every rule is satisfied.

The source code, destination code, and every rate code must contain exactly
three ASCII uppercase letters A through Z. Codes are case-sensitive and
are not trimmed. The quantity must be finite and non-negative; negative
zero is accepted. Every per-EUR rate must be finite and strictly positive.

A non-finite quantity is reported before a negative quantity. The source
code is checked before the destination code. Rates are then checked in list
order; within each rate, its code is checked before a non-finite value, a
non-positive value, and a duplicate code, in that order. The entire list is
checked before missing rates, so DuplicateRate takes priority over
MissingRate. A missing source rate is checked before a missing destination
rate. Empty, singleton, and longer lists follow these same rules."""
"""Validates the request, propagating its validation error unchanged, then
converts the quantity using rates expressed as units of currency per EUR.

When the source and destination codes differ, the quantity is divided by
the source rate and that result is multiplied by the destination rate,
using F64 arithmetic in that order. A non-finite intermediate or product
returns NonFiniteResult. When the codes are equal, the fully validated list
must still contain that code exactly once, but rate arithmetic is skipped
and the quantity is used unchanged.

The successful quantity is rounded to the nearest multiple of 0.01. An
exact halfway case is rounded to the multiple whose hundredths integer is
even. Ok contains the resulting finite, non-negative F64 value."""
__all__ = ["ConversionRequest", "CurrencyError", "CurrencyError_DuplicateRate", "CurrencyError_InvalidCurrencyCode", "CurrencyError_MissingRate", "CurrencyError_NegativeQuantity", "CurrencyError_NonFiniteQuantity", "CurrencyError_NonFiniteRate", "CurrencyError_NonFiniteResult", "CurrencyError_NonPositiveRate", "Rate"]
