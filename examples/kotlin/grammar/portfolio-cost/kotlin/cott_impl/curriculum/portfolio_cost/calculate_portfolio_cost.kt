package cott_impl.curriculum.portfolio_cost

internal fun calculate_portfolio_cost(rows: cott_runtime.CottList<curriculum.portfolio_cost.Holding>): cott_runtime.CottResult<kotlin.Double, curriculum.portfolio_cost.PortfolioError> {
    var total = 0.0
    for (row in rows) {
        if (row.shares < 0L) {
            return cott_runtime.Err(curriculum.portfolio_cost.PortfolioError.NegativeShares)
        }
        if (!row.price.isFinite()) {
            return cott_runtime.Err(curriculum.portfolio_cost.PortfolioError.NonFinitePrice)
        }
        if (row.price < 0.0) {
            return cott_runtime.Err(curriculum.portfolio_cost.PortfolioError.NegativePrice)
        }
        val product = row.shares.toDouble() * row.price
        if (!product.isFinite()) {
            return cott_runtime.Err(curriculum.portfolio_cost.PortfolioError.TotalOverflow)
        }
        val nextTotal = total + product
        if (!nextTotal.isFinite()) {
            return cott_runtime.Err(curriculum.portfolio_cost.PortfolioError.TotalOverflow)
        }
        total = nextTotal
    }
    return cott_runtime.Ok(total)
}
