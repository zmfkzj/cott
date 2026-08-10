from cott_runtime import I64, Err, Ok, Result
from curriculum.decimal_binary_types import ConversionError, ConversionError_InvalidBinary, ConversionError_Overflow


def binary_to_decimal(digits: str) -> Result[I64, ConversionError]:
    if not digits:
        return Err(error=ConversionError_InvalidBinary())

    significant_digits: int = 0
    found_one: bool = False
    overflow: bool = False
    value: int = 0

    for digit in digits:
        if digit != "0" and digit != "1":
            return Err(error=ConversionError_InvalidBinary())
        if digit == "1":
            found_one = True
        if found_one:
            significant_digits += 1
            if significant_digits > 63:
                overflow = True
            elif digit == "1":
                value = (value << 1) + 1
            else:
                value <<= 1

    if overflow:
        return Err(error=ConversionError_Overflow())
    return Ok(value=value)
