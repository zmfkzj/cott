package cott_impl.curriculum.stock_record

internal fun value_stock_record(record: curriculum.stock_record.StockRecord): cott_runtime.CottResult<kotlin.Double, curriculum.stock_record.StockRecordError> {
    if (record.name.isEmpty()) {
        return cott_runtime.Err(curriculum.stock_record.StockRecordError.EmptyName)
    }
    if (record.shares < 0L) {
        return cott_runtime.Err(curriculum.stock_record.StockRecordError.NegativeShares)
    }
    if (!(-curriculum.stock_record.MAX_F64 <= record.price && record.price <= curriculum.stock_record.MAX_F64)) {
        return cott_runtime.Err(curriculum.stock_record.StockRecordError.NonFinitePrice)
    }
    if (record.price < 0.0) {
        return cott_runtime.Err(curriculum.stock_record.StockRecordError.NegativePrice)
    }
    return curriculum.stock_record.value_record(record)
}
