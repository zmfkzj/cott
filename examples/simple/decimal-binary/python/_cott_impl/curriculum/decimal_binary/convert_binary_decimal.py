from cott_runtime import Err, Ok, Result
from curriculum.decimal_binary import binary_to_decimal
from curriculum.decimal_binary_types import Conversion, Conversion_BinaryToDecimal, Conversion_DecimalToBinary, ConversionError, ConversionError_NegativeDecimal, ConversionResult, ConversionResult_Binary, ConversionResult_Decimal


def convert_binary_decimal(operation: Conversion) -> Result[ConversionResult, ConversionError]:
    match operation:
        case Conversion_DecimalToBinary(value=value):
            if value < 0:
                return Err(error=ConversionError_NegativeDecimal())
            return Ok(value=ConversionResult_Binary(digits=f"{value:b}"))
        case Conversion_BinaryToDecimal(digits=digits):
            match binary_to_decimal(digits):
                case Ok(value=value):
                    return Ok(value=ConversionResult_Decimal(value=value))
                case Err(error=error):
                    return Err(error=error)
