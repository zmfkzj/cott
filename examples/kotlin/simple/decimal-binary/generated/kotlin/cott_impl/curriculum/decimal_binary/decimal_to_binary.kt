package cott_impl.curriculum.decimal_binary

internal fun decimal_to_binary(`value`: kotlin.Long): cott_runtime.CottResult<kotlin.String, curriculum.decimal_binary.ConversionError> {
    if (`value` < 0L) {
        return cott_runtime.Err(curriculum.decimal_binary.ConversionError.NegativeDecimal)
    }
    return cott_runtime.Ok(java.lang.Long.toBinaryString(`value`))
}
