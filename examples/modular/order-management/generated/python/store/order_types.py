from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from store.catalog_types import Catalog, CatalogError

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OrderLine:
    __hash__ = None
    sku: str
    quantity: U32

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "sku", _cott_validate_abi(self.sku, str, path="$.sku"))
        if not _cott_validated_construction():
            object.__setattr__(self, "quantity", _cott_validate_abi(self.quantity, U32, path="$.quantity"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Order:
    __hash__ = None
    order_id: str
    lines: CottList[OrderLine]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "order_id", _cott_validate_abi(self.order_id, str, path="$.order_id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "lines", _cott_validate_abi(self.lines, CottList[OrderLine], path="$.lines"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OrderReceipt:
    __hash__ = None
    order_id: str
    total_items: U32
    total_cents: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "order_id", _cott_validate_abi(self.order_id, str, path="$.order_id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "total_items", _cott_validate_abi(self.total_items, U32, path="$.total_items"))
        if not _cott_validated_construction():
            object.__setattr__(self, "total_cents", _cott_validate_abi(self.total_cents, U64, path="$.total_cents"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OrderError_EmptyOrder:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OrderError_InvalidQuantity:
    __hash__ = None
    sku: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OrderError_ItemUnavailable:
    __hash__ = None
    cause: CatalogError

OrderError: TypeAlias = Union[OrderError_EmptyOrder, OrderError_InvalidQuantity, OrderError_ItemUnavailable]

"""Ensure an order line has positive quantity."""
"""Validate all order lines, lookup item prices, and produce a receipt."""
__all__ = ["Order", "OrderError", "OrderError_EmptyOrder", "OrderError_InvalidQuantity", "OrderError_ItemUnavailable", "OrderLine", "OrderReceipt"]
