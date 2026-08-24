from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottExternal, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ReorderRequest:
    __hash__ = None
    sku: str
    on_hand: U64
    reserved: U64
    reorder_point: U64
    target_level: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ReorderPlan:
    __hash__ = None
    sku: str
    order_qty: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InventoryReorderError_BlankSku:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InventoryReorderError_ReservedExceedsOnHand:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InventoryReorderError_TargetBelowReorderPoint:
    pass

InventoryReorderError: TypeAlias = Union[InventoryReorderError_BlankSku, InventoryReorderError_ReservedExceedsOnHand, InventoryReorderError_TargetBelowReorderPoint]

"""Compute stock available for reorder planning after reservations. Return
ReservedExceedsOnHand when reservations cannot be subtracted safely."""
"""Validate one inventory request and build its deterministic reorder plan.
A blank SKU is rejected before available stock is computed. An invalid
target is rejected afterward. Stock at or below the reorder point is
replenished to the target level; stock above it produces a zero-quantity
plan."""
__all__ = ["InventoryReorderError", "InventoryReorderError_BlankSku", "InventoryReorderError_ReservedExceedsOnHand", "InventoryReorderError_TargetBelowReorderPoint", "ReorderPlan", "ReorderRequest"]
