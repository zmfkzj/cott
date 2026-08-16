from cott_runtime import Err, Ok, Result, U32, U64
from store.catalog import find_item
from store.catalog_types import Catalog
from store.order import validate_line
from store.order_types import (
    Order,
    OrderError,
    OrderError_EmptyOrder,
    OrderError_ItemUnavailable,
    OrderReceipt,
)


def calculate_order(catalog: Catalog, order: Order) -> Result[OrderReceipt, OrderError]:
    if len(order.lines) == 0:
        return Err(error=OrderError_EmptyOrder())
    total_items = 0
    total_cents = 0
    for raw_line in order.lines:
        line_res = validate_line(raw_line)
        if isinstance(line_res, Err):
            return Err(error=line_res.error)
        item_res = find_item(catalog, line_res.value.sku)
        if isinstance(item_res, Err):
            return Err(error=OrderError_ItemUnavailable(cause=item_res.error))
        total_items += int(line_res.value.quantity)
        total_cents += int(item_res.value.price_cents) * int(line_res.value.quantity)
    return Ok(
        value=OrderReceipt(
            order_id=order.order_id,
            total_items=U32(total_items),
            total_cents=U64(total_cents),
        )
    )
