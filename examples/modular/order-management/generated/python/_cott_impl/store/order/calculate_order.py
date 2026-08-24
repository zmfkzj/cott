from cott_runtime import Err, Ok, Result
from store.catalog import find_item
from store.catalog_types import Catalog
from store.order_types import Order, OrderError, OrderError_EmptyOrder, OrderError_InvalidQuantity, OrderError_ItemUnavailable, OrderReceipt


def calculate_order(catalog: Catalog, order: Order) -> Result[OrderReceipt, OrderError]:
    if not order.lines:
        return Err(error=OrderError_EmptyOrder())

    total_items = 0
    total_cents = 0
    for line in order.lines:
        if line.quantity == 0:
            return Err(error=OrderError_InvalidQuantity(sku=line.sku))

        lookup = find_item(catalog, line.sku)
        match lookup:
            case Ok(value=item):
                total_items += line.quantity
                total_cents += item.price_cents * line.quantity
            case Err(error=cause):
                return Err(error=OrderError_ItemUnavailable(cause=cause))

    return Ok(value=OrderReceipt(order_id=order.order_id, total_items=total_items, total_cents=total_cents))
