package cott_impl.curriculum.stock_record

internal fun value_stock_record(record: curriculum.stock_record.StockRecord): cott_runtime.CottResult<kotlin.Double, curriculum.stock_record.StockRecordError> {
    if (record.name.isEmpty()) {
        return cott_runtime.Err(curriculum.stock_record.StockRecordError.EmptyName)
    }
    if (record.shares < 0L) {
        return cott_runtime.Err(curriculum.stock_record.StockRecordError.NegativeShares)
    }
    if (!record.price.isFinite()) {
        return cott_runtime.Err(curriculum.stock_record.StockRecordError.NonFinitePrice)
    }
    if (record.price < 0.0) {
        return cott_runtime.Err(curriculum.stock_record.StockRecordError.NegativePrice)
    }
    val value = record.shares.toDouble() * record.price
    if (!value.isFinite()) {
        return cott_runtime.Err(curriculum.stock_record.StockRecordError.ValuationOverflow)
    }
    return cott_runtime.Ok(value)
}
