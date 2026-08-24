from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.portfolio_cost_types import Holding as Holding, PortfolioError as PortfolioError, PortfolioError_NegativePrice as PortfolioError_NegativePrice, PortfolioError_NegativeShares as PortfolioError_NegativeShares, PortfolioError_NonFinitePrice as PortfolioError_NonFinitePrice, PortfolioError_TotalOverflow as PortfolioError_TotalOverflow
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
def calculate_portfolio_cost(rows: CottList[Holding]) -> Result[F64, PortfolioError]: ...

__all__ = ["Holding", "PortfolioError", "PortfolioError_NegativePrice", "PortfolioError_NegativeShares", "PortfolioError_NonFinitePrice", "PortfolioError_TotalOverflow", "calculate_portfolio_cost"]
