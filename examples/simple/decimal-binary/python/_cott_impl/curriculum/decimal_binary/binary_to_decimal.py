from cott_runtime import I64, Err, Ok, Result

from curriculum.decimal_binary_types import ConversionError, ConversionError_InvalidBinary, ConversionError_Overflow


def binary_to_decimal(digits: str) -> Result[I64, ConversionError]:
    if not digits:
        return Err(error=ConversionError_InvalidBinary())
    for ch in digits:
        if ch != "0" and ch != "1":
            return Err(error=ConversionError_InvalidBinary())
    significant = digits.lstrip("0")
    if len(significant) > 63:
        return Err(error=ConversionError_Overflow())
    value = 0
    for ch in significant:
        value = value * 2 + (1 if ch == "1" else 0)
    return Ok(value=value)
