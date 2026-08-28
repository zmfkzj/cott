from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.stock_record_types import StockRecord as StockRecord, StockRecordError as StockRecordError, StockRecordError_EmptyName as StockRecordError_EmptyName, StockRecordError_NegativePrice as StockRecordError_NegativePrice, StockRecordError_NegativeShares as StockRecordError_NegativeShares, StockRecordError_NonFinitePrice as StockRecordError_NonFinitePrice, StockRecordError_ValuationOverflow as StockRecordError_ValuationOverflow
"""Computes the value of a validated stock record.

The caller supplies non-negative shares and a non-negative price.
ValuationOverflow is returned when the binary64 product is not finite."""
def value_record(record: StockRecord) -> Result[F64, StockRecordError]: ...

"""Validates and values one raw stock record.

Validation reports EmptyName, NegativeShares, NonFinitePrice, then
NegativePrice in source order. A valid record is valued by value_record."""
def value_stock_record(record: StockRecord) -> Result[F64, StockRecordError]: ...

__all__ = ["StockRecord", "StockRecordError", "StockRecordError_EmptyName", "StockRecordError_NegativePrice", "StockRecordError_NegativeShares", "StockRecordError_NonFinitePrice", "StockRecordError_ValuationOverflow", "value_record", "value_stock_record"]
