package cott_impl.curriculum.stock_record

internal fun value_record(record: curriculum.stock_record.StockRecord): cott_runtime.CottResult<kotlin.Double, curriculum.stock_record.StockRecordError> {
    val value = record.shares.toDouble() * record.price
    return if (value.isFinite()) {
        cott_runtime.Ok(value)
    } else {
        cott_runtime.Err(curriculum.stock_record.StockRecordError.ValuationOverflow)
    }
}
