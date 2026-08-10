from __future__ import annotations

import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StockRecord:
    __hash__ = None
    name: str
    shares: I64
    price: F64

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
