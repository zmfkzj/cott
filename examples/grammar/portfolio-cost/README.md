# portfolio-cost

## Purpose
Expresses portfolio valuation through contracts and an error domain while calculating a list of structures in order.

## Key points
- `Holding` has `I64` shares and an `F64` price, and `calculate_portfolio_cost` declares with `ensures` that a successful total is at least 0.
- `PortfolioError` distinguishes negative shares, non-finite prices, negative prices, and total overflow.
- The Python implementation stops at the first error in list order and checks for non-finite values after each multiplication and accumulated addition, returning `TotalOverflow`.
