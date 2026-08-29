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
        match validate_line(line):
            case Err(error=error):
                return Err(error=error)
            case Ok(value=valid_line):
                match find_item(catalog, valid_line.sku):
                    case Err(error=cause):
                        return Err(error=OrderError_ItemUnavailable(cause=cause))
                    case Ok(value=item):
                        total_items += valid_line.quantity
                        total_cents += item.price_cents * valid_line.quantity

    return Ok(
        value=OrderReceipt(
            order_id=order.order_id,
            total_items=total_items,
            total_cents=total_cents,
        )
    )
