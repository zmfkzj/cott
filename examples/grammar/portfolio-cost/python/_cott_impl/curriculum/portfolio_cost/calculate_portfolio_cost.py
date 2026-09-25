from math import isfinite

from cott_runtime import CottList, Err, F64, Ok, Result
from curriculum.portfolio_cost_types import (
    Holding,
    PortfolioError,
    PortfolioError_NegativePrice,
    PortfolioError_NegativeShares,
    PortfolioError_NonFinitePrice,
    PortfolioError_TotalOverflow,
)

def calculate_portfolio_cost(rows: CottList[Holding]) -> Result[F64, PortfolioError]:
    total = 0.0
    for holding in rows:
        if holding.shares < 0:
            return Err(error=PortfolioError_NegativeShares())
        price = holding.price
        if not isfinite(price):
            return Err(error=PortfolioError_NonFinitePrice())
        if price < 0.0:
            return Err(error=PortfolioError_NegativePrice())
        product = float(holding.shares) * price
        if not isfinite(product):
            return Err(error=PortfolioError_TotalOverflow())
        total = total + product
        if not isfinite(total):
            return Err(error=PortfolioError_TotalOverflow())
    return Ok(value=total)
