from cott_runtime import Err, F64, Ok, Result
from curriculum.validated_stock_types import Stock, ValuationError, ValuationError_Overflow


def value_stock(stock: Stock) -> Result[F64, ValuationError]:
    value: F64 = stock.shares.value * stock.price.value
    if value == float("inf"):
        return Err(error=ValuationError_Overflow())
    return Ok(value=value)
