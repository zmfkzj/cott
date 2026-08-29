from cott_runtime import Err, I64, Ok, Result
from curriculum.decimal_binary_types import ConversionError, ConversionError_InvalidBinary, ConversionError_Overflow


def binary_to_decimal(digits: str) -> Result[I64, ConversionError]:
    if digits == "":
        return Err(error=ConversionError_InvalidBinary())

    value = 0
    significant_digits = 0
    for digit in digits:
        if digit != "0" and digit != "1":
            return Err(error=ConversionError_InvalidBinary())
        if significant_digits != 0 or digit == "1":
            significant_digits += 1
            if significant_digits <= 63:
                value *= 2
                if digit == "1":
                    value += 1

    if significant_digits > 63:
        return Err(error=ConversionError_Overflow())
    return Ok(value=value)
