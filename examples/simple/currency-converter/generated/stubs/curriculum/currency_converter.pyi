from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.currency_converter_types import ConversionRequest as ConversionRequest, CurrencyError as CurrencyError, CurrencyError_DuplicateRate as CurrencyError_DuplicateRate, CurrencyError_InvalidCurrencyCode as CurrencyError_InvalidCurrencyCode, CurrencyError_MissingRate as CurrencyError_MissingRate, CurrencyError_NegativeQuantity as CurrencyError_NegativeQuantity, CurrencyError_NonFiniteQuantity as CurrencyError_NonFiniteQuantity, CurrencyError_NonFiniteRate as CurrencyError_NonFiniteRate, CurrencyError_NonFiniteResult as CurrencyError_NonFiniteResult, CurrencyError_NonPositiveRate as CurrencyError_NonPositiveRate, Rate as Rate
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
def validate_conversion_request(request: ConversionRequest) -> Result[Unit, CurrencyError]: ...

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
def convert_currency(request: ConversionRequest) -> Result[F64, CurrencyError]: ...

__all__ = ["ConversionRequest", "CurrencyError", "CurrencyError_DuplicateRate", "CurrencyError_InvalidCurrencyCode", "CurrencyError_MissingRate", "CurrencyError_NegativeQuantity", "CurrencyError_NonFiniteQuantity", "CurrencyError_NonFiniteRate", "CurrencyError_NonFiniteResult", "CurrencyError_NonPositiveRate", "Rate", "convert_currency", "validate_conversion_request"]
