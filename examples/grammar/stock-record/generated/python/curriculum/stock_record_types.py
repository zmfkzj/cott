from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StockRecord:
    __hash__ = None
    name: str
    shares: I64
    price: F64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "shares", _cott_validate_abi(self.shares, I64, path="$.shares"))
        if not _cott_validated_construction():
            object.__setattr__(self, "price", _cott_validate_abi(self.price, F64, path="$.price"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StockRecordError_EmptyName:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StockRecordError_NegativeShares:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StockRecordError_NonFinitePrice:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StockRecordError_NegativePrice:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StockRecordError_ValuationOverflow:
    pass

StockRecordError: TypeAlias = Union[StockRecordError_EmptyName, StockRecordError_NegativeShares, StockRecordError_NonFinitePrice, StockRecordError_NegativePrice, StockRecordError_ValuationOverflow]

"""Computes the value of a validated stock record.

The caller supplies non-negative shares and a non-negative price.
ValuationOverflow is returned when the binary64 product is not finite."""
"""Validates and values one raw stock record.

Validation reports EmptyName, NegativeShares, NonFinitePrice, then
NegativePrice in source order. A valid record is valued by value_record."""
__all__ = ["StockRecord", "StockRecordError", "StockRecordError_EmptyName", "StockRecordError_NegativePrice", "StockRecordError_NegativeShares", "StockRecordError_NonFinitePrice", "StockRecordError_ValuationOverflow"]
