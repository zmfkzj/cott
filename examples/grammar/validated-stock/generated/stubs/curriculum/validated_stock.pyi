from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.validated_stock_types import Price as Price, Shares as Shares, Stock as Stock, StockName as StockName, ValuationError as ValuationError, ValuationError_Overflow as ValuationError_Overflow
"""Computes the market value of one validated stock position. StockName
accepts every non-empty string; Shares accepts integers from zero through
9,223,372,036,854,775,807; Price accepts finite binary64 values from 0.0
through 1.7976931348623157e308 inclusive. Each nominal constructor
validates before value_stock is called; constructor failures are contract
violations, not ValuationError values. For a valid Stock, value_stock
multiplies shares by price exactly once and returns the finite binary64
product in Ok, including zero when either factor is zero. Overflow is
returned when multiplication produces infinity and is the only function
error."""
def value_stock(stock: Stock) -> Result[F64, ValuationError]: ...

__all__ = ["Price", "Shares", "Stock", "StockName", "ValuationError", "ValuationError_Overflow", "value_stock"]
