from cott_runtime import Err, Ok, Result
from store.catalog import find_item
from store.catalog_types import Catalog
from store.order import validate_line
from store.order_types import Order, OrderError, OrderError_EmptyOrder, OrderError_ItemUnavailable, OrderReceipt


def calculate_order(catalog: Catalog, order: Order) -> Result[OrderReceipt, OrderError]:
    if len(order.lines) == 0:
        return Err(error=OrderError_EmptyOrder())

    total_items = 0
    total_cents = 0
    for line in order.lines:
        validated = validate_line(line)
        if isinstance(validated, Err):
            return Err(error=validated.error)

        found = find_item(catalog, validated.value.sku)
        if isinstance(found, Err):
            return Err(error=OrderError_ItemUnavailable(cause=found.error))

        total_items += validated.value.quantity
        total_cents += found.value.price_cents * validated.value.quantity

    return Ok(value=OrderReceipt(order_id=order.order_id, total_items=total_items, total_cents=total_cents))
