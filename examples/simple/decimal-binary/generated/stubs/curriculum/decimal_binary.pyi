from __future__ import annotations

from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.decimal_binary_types import Conversion as Conversion, ConversionError as ConversionError, ConversionError_InvalidBinary as ConversionError_InvalidBinary, ConversionError_NegativeDecimal as ConversionError_NegativeDecimal, ConversionError_Overflow as ConversionError_Overflow, ConversionResult as ConversionResult, ConversionResult_Binary as ConversionResult_Binary, ConversionResult_Decimal as ConversionResult_Decimal, Conversion_BinaryToDecimal as Conversion_BinaryToDecimal, Conversion_DecimalToBinary as Conversion_DecimalToBinary
"""Converts one decimal I64 to canonical binary text.

Every nonnegative value succeeds with the shortest sequence of ASCII `0`
and `1` digits, without leading zeros; zero is exactly `"0"`. A negative
value returns `NegativeDecimal`."""
def decimal_to_binary(value: I64) -> Result[str, ConversionError]: ...

"""Converts binary text to a nonnegative decimal I64.

The input must be nonempty and contain only ASCII `0` and `1`; leading
zeros are allowed and ignored. Any other input returns `InvalidBinary`.
After the entire string is validated, more than 63 significant digits
returns `Overflow`, so invalid characters take priority over overflow."""
def binary_to_decimal(digits: str) -> Result[I64, ConversionError]: ...

"""Routes a tagged conversion through the matching decimal or binary
conversion operation and wraps its successful scalar result.

Errors from the selected operation are returned unchanged."""
def convert_binary_decimal(operation: Conversion) -> Result[ConversionResult, ConversionError]: ...

__all__ = ["Conversion", "ConversionError", "ConversionError_InvalidBinary", "ConversionError_NegativeDecimal", "ConversionError_Overflow", "ConversionResult", "ConversionResult_Binary", "ConversionResult_Decimal", "Conversion_BinaryToDecimal", "Conversion_DecimalToBinary", "binary_to_decimal", "convert_binary_decimal", "decimal_to_binary"]
