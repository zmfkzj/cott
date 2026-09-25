from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.portfolio_cost_types import Holding as Holding, MAX_F64 as MAX_F64, PortfolioError as PortfolioError, PortfolioError_NegativePrice as PortfolioError_NegativePrice, PortfolioError_NegativeShares as PortfolioError_NegativeShares, PortfolioError_NonFinitePrice as PortfolioError_NonFinitePrice, PortfolioError_TotalOverflow as PortfolioError_TotalOverflow
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
def calculate_portfolio_cost(rows: CottList[Holding]) -> Result[F64, PortfolioError]: ...

__all__ = ["Holding", "MAX_F64", "PortfolioError", "PortfolioError_NegativePrice", "PortfolioError_NegativeShares", "PortfolioError_NonFinitePrice", "PortfolioError_TotalOverflow", "calculate_portfolio_cost"]
