from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottExternal, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StockName:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))
        if not ((len(self.value) > 0)):
            raise CottContractViolation("StockName refinement failed", symbol="curriculum.stock_input_validation.StockName", phase="refinement", span={"end_byte":87,"end_column":23,"end_line":4,"start_byte":75,"start_column":11,"start_line":4}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Shares:
    value: I64

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, I64, path="$.value"))
        if not ((self.value >= 0)):
            raise CottContractViolation("Shares refinement failed", symbol="curriculum.stock_input_validation.Shares", phase="refinement", span={"end_byte":128,"end_column":20,"end_line":7,"start_byte":119,"start_column":11,"start_line":7}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Price:
    value: F64

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, F64, path="$.value"))
        if not ((self.value >= 0)):
            raise CottContractViolation("Price refinement failed", symbol="curriculum.stock_input_validation.Price", phase="refinement", span={"end_byte":170,"end_column":22,"end_line":10,"start_byte":159,"start_column":11,"start_line":10}, expected="true", actual="false")

    __hash__ = None
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StockInput:
    __hash__ = None
    name: StockName
    shares: Shares
    price: Price

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StockInputError_EmptyName:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StockInputError_NegativeShares:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StockInputError_NonFinitePrice:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StockInputError_NegativePrice:
    pass

StockInputError: TypeAlias = Union[StockInputError_EmptyName, StockInputError_NegativeShares, StockInputError_NonFinitePrice, StockInputError_NegativePrice]

"""Validates raw stock fields and constructs StockName, Shares, Price, and
StockInput values, returning the first applicable error. Validation is
ordered as EmptyName for a zero-length name, NegativeShares for shares
below zero, NonFinitePrice for NaN or either infinity, then NegativePrice
for a finite price below zero. Whitespace-only names, zero shares, zero
price, and negative zero are accepted. Successful values preserve the raw
name, shares, and price exactly. This pure function performs no I/O and
terminates for every Str, I64, and F64 input."""
__all__ = ["Price", "Shares", "StockInput", "StockInputError", "StockInputError_EmptyName", "StockInputError_NegativePrice", "StockInputError_NegativeShares", "StockInputError_NonFinitePrice", "StockName"]
