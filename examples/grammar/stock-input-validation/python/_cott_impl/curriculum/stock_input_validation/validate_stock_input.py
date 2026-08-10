from cott_runtime import Err, F64, I64, Ok, Result
from curriculum.stock_input_validation_types import (
    Price,
    Shares,
    StockInput,
    StockInputError,
    StockInputError_EmptyName,
    StockInputError_NegativePrice,
    StockInputError_NegativeShares,
    StockInputError_NonFinitePrice,
    StockName,
)


def validate_stock_input(name: str, shares: I64, price: F64) -> Result[StockInput, StockInputError]:
    if len(name) == 0:
        return Err(error=StockInputError_EmptyName())
    if shares < 0:
        return Err(error=StockInputError_NegativeShares())
    if price != price or price == float("inf") or price == float("-inf"):
        return Err(error=StockInputError_NonFinitePrice())
    if price < 0:
        return Err(error=StockInputError_NegativePrice())
    return Ok(value=StockInput(name=StockName(value=name), shares=Shares(value=shares), price=Price(value=price)))
