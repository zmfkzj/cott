from __future__ import annotations

from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.inventory_reorder_types import InventoryReorderError as InventoryReorderError, InventoryReorderError_BlankSku as InventoryReorderError_BlankSku, InventoryReorderError_ReservedExceedsOnHand as InventoryReorderError_ReservedExceedsOnHand, InventoryReorderError_TargetBelowReorderPoint as InventoryReorderError_TargetBelowReorderPoint, ReorderPlan as ReorderPlan, ReorderRequest as ReorderRequest
"""Compute stock available for reorder planning after reservations. Return
ReservedExceedsOnHand when reservations cannot be subtracted safely."""
def available_stock(on_hand: U64, reserved: U64) -> Result[U64, InventoryReorderError]: ...

"""Validate one inventory request and build its deterministic reorder plan.
A blank SKU is rejected before available stock is computed. An invalid
target is rejected afterward. Stock at or below the reorder point is
replenished to the target level; stock above it produces a zero-quantity
plan."""
def plan_reorder(request: ReorderRequest) -> Result[ReorderPlan, InventoryReorderError]: ...

__all__ = ["InventoryReorderError", "InventoryReorderError_BlankSku", "InventoryReorderError_ReservedExceedsOnHand", "InventoryReorderError_TargetBelowReorderPoint", "ReorderPlan", "ReorderRequest", "available_stock", "plan_reorder"]
