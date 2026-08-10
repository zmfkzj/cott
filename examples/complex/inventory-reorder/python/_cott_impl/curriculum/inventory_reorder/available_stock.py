from cott_runtime import Err, Ok, Result, U64
from curriculum.inventory_reorder_types import InventoryReorderError, InventoryReorderError_ReservedExceedsOnHand


def available_stock(on_hand: U64, reserved: U64) -> Result[U64, InventoryReorderError]:
    if reserved > on_hand:
        return Err(error=InventoryReorderError_ReservedExceedsOnHand())
    return Ok(value=on_hand - reserved)
