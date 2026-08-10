from cott_runtime import Err, Ok, Result, U64
from curriculum.inventory_reorder import available_stock
from curriculum.inventory_reorder_types import (
    InventoryReorderError,
    InventoryReorderError_BlankSku,
    InventoryReorderError_TargetBelowReorderPoint,
    ReorderPlan,
    ReorderRequest,
)


def plan_reorder(request: ReorderRequest) -> Result[ReorderPlan, InventoryReorderError]:
    if len(request.sku) == 0:
        return Err(error=InventoryReorderError_BlankSku())

    stock_result = available_stock(request.on_hand, request.reserved)
    if isinstance(stock_result, Err):
        return Err(error=stock_result.error)

    available: U64 = stock_result.value
    if request.target_level < request.reorder_point:
        return Err(error=InventoryReorderError_TargetBelowReorderPoint())

    order_qty: U64 = request.target_level - available if available <= request.reorder_point else 0
    return Ok(value=ReorderPlan(sku=request.sku, order_qty=order_qty))
