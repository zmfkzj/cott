package cott_impl.curriculum.decimal_binary

internal fun convert_binary_decimal(operation: curriculum.decimal_binary.Conversion): cott_runtime.CottResult<curriculum.decimal_binary.ConversionResult, curriculum.decimal_binary.ConversionError> =
    when (operation) {
        is curriculum.decimal_binary.Conversion.DecimalToBinary ->
            when (val r = curriculum.decimal_binary.decimal_to_binary(operation.value)) {
                is cott_runtime.Ok -> cott_runtime.Ok(curriculum.decimal_binary.ConversionResult.Binary(r.value))
                is cott_runtime.Err -> cott_runtime.Err(r.error)
            }
        is curriculum.decimal_binary.Conversion.BinaryToDecimal ->
            when (val r = curriculum.decimal_binary.binary_to_decimal(operation.digits)) {
                is cott_runtime.Ok -> cott_runtime.Ok(curriculum.decimal_binary.ConversionResult.Decimal(r.value))
                is cott_runtime.Err -> cott_runtime.Err(r.error)
            }
    }
