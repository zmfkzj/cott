from cott_runtime import Err, Ok, Result
from curriculum.decimal_binary import binary_to_decimal
from curriculum.decimal_binary_types import Conversion, Conversion_DecimalToBinary, ConversionError, ConversionError_NegativeDecimal, ConversionResult, ConversionResult_Binary, ConversionResult_Decimal


def convert_binary_decimal(operation: Conversion) -> Result[ConversionResult, ConversionError]:
    if isinstance(operation, Conversion_DecimalToBinary):
        if operation.value < 0:
            return Err(error=ConversionError_NegativeDecimal())
        return Ok(value=ConversionResult_Binary(digits=format(operation.value, "b")))

    conversion = binary_to_decimal(operation.digits)
    if isinstance(conversion, Err):
        return Err(error=conversion.error)
    return Ok(value=ConversionResult_Decimal(value=conversion.value))
