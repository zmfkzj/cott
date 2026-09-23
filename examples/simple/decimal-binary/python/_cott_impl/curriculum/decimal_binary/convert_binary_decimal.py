from cott_runtime import Err, Ok, Result

from curriculum.decimal_binary import binary_to_decimal, decimal_to_binary
from curriculum.decimal_binary_types import Conversion, ConversionError, ConversionResult, ConversionResult_Binary, ConversionResult_Decimal, Conversion_BinaryToDecimal, Conversion_DecimalToBinary


def convert_binary_decimal(operation: Conversion) -> Result[ConversionResult, ConversionError]:
    if isinstance(operation, Conversion_DecimalToBinary):
        binary = decimal_to_binary(operation.value)
        if isinstance(binary, Err):
            return Err(error=binary.error)
        return Ok(value=ConversionResult_Binary(digits=binary.value))
    assert isinstance(operation, Conversion_BinaryToDecimal)
    decimal = binary_to_decimal(operation.digits)
    if isinstance(decimal, Err):
        return Err(error=decimal.error)
    return Ok(value=ConversionResult_Decimal(value=decimal.value))
