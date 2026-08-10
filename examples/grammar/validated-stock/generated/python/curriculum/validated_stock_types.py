from __future__ import annotations

import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StockName:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))
        if not ((len(self.value) > 0)):
            raise CottContractViolation("StockName refinement failed", symbol="curriculum.validated_stock.StockName", phase="refinement", span={"end_byte":80,"end_column":23,"end_line":4,"start_byte":68,"start_column":11,"start_line":4}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Shares:
    value: I64

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, I64, path="$.value"))
        if not ((self.value >= 0)):
            raise CottContractViolation("Shares refinement failed", symbol="curriculum.validated_stock.Shares", phase="refinement", span={"end_byte":121,"end_column":20,"end_line":7,"start_byte":112,"start_column":11,"start_line":7}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Price:
    value: F64

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, F64, path="$.value"))
        if not (((self.value >= 0) and (self.value <= 179769313486231570000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000))):
            raise CottContractViolation("Price refinement failed", symbol="curriculum.validated_stock.Price", phase="refinement", span={"end_byte":198,"end_column":57,"end_line":10,"start_byte":152,"start_column":11,"start_line":10}, expected="true", actual="false")

    __hash__ = None
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Stock:
    __hash__ = None
    name: StockName
    shares: Shares
    price: Price

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ValuationError_Overflow:
    pass

ValuationError: TypeAlias = Union[ValuationError_Overflow]

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
__all__ = ["Price", "Shares", "Stock", "StockName", "ValuationError", "ValuationError_Overflow"]
