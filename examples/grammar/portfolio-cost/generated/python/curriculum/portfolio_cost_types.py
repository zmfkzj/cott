from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Holding:
    __hash__ = None
    shares: I64
    price: F64

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

"""Computes the total market value of a portfolio from a list of holdings.
Each holding supplies an I64 share count and an F64 price.

Holdings are processed in list order and evaluation stops at the first
error. For each holding, a negative share count returns NegativeShares;
otherwise a NaN or infinite price returns NonFinitePrice; otherwise a
price below zero returns NegativePrice. Zero shares, positive or negative
zero prices, and an empty list are accepted.

Starting from 0.0, each accepted share count is multiplied by its price
and the product is added to the running total using F64 arithmetic, in
list order. TotalOverflow is returned if either operation produces a
non-finite value. Otherwise Ok contains the finite, non-negative total;
ordinary F64 rounding and underflow are retained."""
__all__ = ["Holding", "PortfolioError", "PortfolioError_NegativePrice", "PortfolioError_NegativeShares", "PortfolioError_NonFinitePrice", "PortfolioError_TotalOverflow"]
