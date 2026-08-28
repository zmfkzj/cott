from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.stock_input_validation_types import Price as Price, Shares as Shares, StockInput as StockInput, StockInputError as StockInputError, StockInputError_EmptyName as StockInputError_EmptyName, StockInputError_NegativePrice as StockInputError_NegativePrice, StockInputError_NegativeShares as StockInputError_NegativeShares, StockInputError_NonFinitePrice as StockInputError_NonFinitePrice, StockName as StockName
"""Validates raw stock fields and constructs StockName, Shares, Price, and
StockInput values, returning the first applicable error. Validation is
ordered as EmptyName for a zero-length name, NegativeShares for shares
below zero, NonFinitePrice for NaN or either infinity, then NegativePrice
for a finite price below zero. Whitespace-only names, zero shares, zero
price, and negative zero are accepted. Successful values preserve the raw
name, shares, and price exactly. This pure function performs no I/O and
terminates for every Str, I64, and F64 input."""
def validate_stock_input(name: str, shares: I64, price: F64) -> Result[StockInput, StockInputError]: ...

__all__ = ["Price", "Shares", "StockInput", "StockInputError", "StockInputError_EmptyName", "StockInputError_NegativePrice", "StockInputError_NegativeShares", "StockInputError_NonFinitePrice", "StockName", "validate_stock_input"]
