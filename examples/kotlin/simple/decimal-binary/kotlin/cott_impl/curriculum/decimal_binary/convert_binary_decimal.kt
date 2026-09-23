package cott_impl.curriculum.decimal_binary

internal fun convert_binary_decimal(operation: curriculum.decimal_binary.Conversion): cott_runtime.CottResult<curriculum.decimal_binary.ConversionResult, curriculum.decimal_binary.ConversionError> =
    when (operation) {
        is curriculum.decimal_binary.Conversion.DecimalToBinary -> {
            if (operation.value < 0L) {
                cott_runtime.Err(curriculum.decimal_binary.ConversionError.NegativeDecimal)
            } else {
                cott_runtime.Ok(
                    curriculum.decimal_binary.ConversionResult.Binary(
                        java.lang.Long.toBinaryString(operation.value)
                    )
                )
            }
        }
        is curriculum.decimal_binary.Conversion.BinaryToDecimal -> {
            _convert_binary_digits(operation.digits)
        }
    }

private fun _convert_binary_digits(digits: String): cott_runtime.CottResult<curriculum.decimal_binary.ConversionResult, curriculum.decimal_binary.ConversionError> {
    if (digits.isEmpty()) {
        return cott_runtime.Err(curriculum.decimal_binary.ConversionError.InvalidBinary)
    }
    for (digit in digits) {
        if (digit != '0' && digit != '1') {
            return cott_runtime.Err(curriculum.decimal_binary.ConversionError.InvalidBinary)
        }
    }
    var value = 0L
    for (digit in digits) {
        val bit = if (digit == '1') 1L else 0L
        if (value > (Long.MAX_VALUE - bit) / 2L) {
            return cott_runtime.Err(curriculum.decimal_binary.ConversionError.Overflow)
        }
        value = value * 2L + bit
    }
    return cott_runtime.Ok(curriculum.decimal_binary.ConversionResult.Decimal(value))
}
