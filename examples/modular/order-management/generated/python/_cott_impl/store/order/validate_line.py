from cott_runtime import Err, Ok, Result
from store.order_types import OrderError, OrderError_InvalidQuantity, OrderLine


def validate_line(line: OrderLine) -> Result[OrderLine, OrderError]:
    """Ensure an order line has positive quantity."""
    if line.quantity == 0:
        return Err(error=OrderError_InvalidQuantity(sku=line.sku))
    return Ok(value=line)
