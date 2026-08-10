from cott_runtime import I64, Err, Ok, Result
from curriculum.decimal_binary_types import ConversionError, ConversionError_NegativeDecimal


def decimal_to_binary(value: I64) -> Result[str, ConversionError]:
    if value < 0:
        return Err(error=ConversionError_NegativeDecimal())
    return Ok(value=format(value, "b"))
