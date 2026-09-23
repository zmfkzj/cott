package cott_impl.curriculum.decimal_binary

internal fun binary_to_decimal(digits: kotlin.String): cott_runtime.CottResult<kotlin.Long, curriculum.decimal_binary.ConversionError> {
    if (digits.isEmpty()) {
        return cott_runtime.Err(curriculum.decimal_binary.ConversionError.InvalidBinary)
    }

    var firstOne: kotlin.Int = -1
    for (index in digits.indices) {
        when (digits[index]) {
            '0' -> Unit
            '1' -> if (firstOne < 0) firstOne = index
            else -> return cott_runtime.Err(curriculum.decimal_binary.ConversionError.InvalidBinary)
        }
    }

    if (firstOne < 0) return cott_runtime.Ok(0L)
    if (digits.length - firstOne > 63) {
        return cott_runtime.Err(curriculum.decimal_binary.ConversionError.Overflow)
    }

    var value: kotlin.Long = 0L
    for (index in firstOne until digits.length) {
        value = value * 2L + if (digits[index] == '1') 1L else 0L
    }
    return cott_runtime.Ok(value)
}
