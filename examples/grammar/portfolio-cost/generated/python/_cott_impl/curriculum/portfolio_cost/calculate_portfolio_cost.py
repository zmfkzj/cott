from cott_runtime import CottList, Err, F64, I64, Ok, Result
from curriculum.portfolio_cost_types import Holding, PortfolioError, PortfolioError_NegativePrice, PortfolioError_NegativeShares, PortfolioError_NonFinitePrice, PortfolioError_TotalOverflow


def calculate_portfolio_cost(rows: CottList[Holding]) -> Result[F64, PortfolioError]:
    total: F64 = 0.0
    for holding in rows:
        shares: I64 = holding.shares
        price: F64 = holding.price
        if shares < 0:
            return Err(error=PortfolioError_NegativeShares())
        if price != price or price - price != 0.0:
            return Err(error=PortfolioError_NonFinitePrice())
        if price < 0.0:
            return Err(error=PortfolioError_NegativePrice())
        product: F64 = shares * price
        if product != product or product - product != 0.0:
            return Err(error=PortfolioError_TotalOverflow())
        total = total + product
        if total != total or total - total != 0.0:
            return Err(error=PortfolioError_TotalOverflow())
    return Ok(value=total)
