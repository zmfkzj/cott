from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
MAX_F64: Final[F64] = 179769313486231570000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Holding:
    __hash__ = None
    shares: I64
    price: F64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "shares", _cott_validate_abi(self.shares, I64, path="$.shares"))
        if not _cott_validated_construction():
            object.__setattr__(self, "price", _cott_validate_abi(self.price, F64, path="$.price"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PortfolioError_NegativeShares:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PortfolioError_NonFinitePrice:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PortfolioError_NegativePrice:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PortfolioError_TotalOverflow:
    pass

PortfolioError: TypeAlias = Union[PortfolioError_NegativeShares, PortfolioError_NonFinitePrice, PortfolioError_NegativePrice, PortfolioError_TotalOverflow]

"""Computes the total market value of a portfolio: the sum of shares times
price over its holdings.

Holdings are examined one at a time in list order, and the first failing
holding decides the error. A holding fails with NegativeShares when its
share count is negative, otherwise with NonFinitePrice when its price is
NaN or infinite, otherwise with NegativePrice when its price is below zero.
Zero shares, signed-zero prices and an empty list are accepted.

The running total starts at 0.0. For each accepted holding, the share count
is converted to the nearest binary64 value and multiplied by the price, and
the product is added to the running total; every operation is binary64,
rounded to nearest, ties to even. If the product or the new running total
is not finite, TotalOverflow is returned at that holding, before later
holdings are examined."""
__all__ = ["Holding", "MAX_F64", "PortfolioError", "PortfolioError_NegativePrice", "PortfolioError_NegativeShares", "PortfolioError_NonFinitePrice", "PortfolioError_TotalOverflow"]
