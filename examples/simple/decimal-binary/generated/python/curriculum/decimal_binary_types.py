from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Conversion_DecimalToBinary:
    __hash__ = None
    value: I64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Conversion_BinaryToDecimal:
    __hash__ = None
    digits: str

Conversion: TypeAlias = Union[Conversion_DecimalToBinary, Conversion_BinaryToDecimal]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConversionResult_Binary:
    __hash__ = None
    digits: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConversionResult_Decimal:
    __hash__ = None
    value: I64

ConversionResult: TypeAlias = Union[ConversionResult_Binary, ConversionResult_Decimal]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConversionError_NegativeDecimal:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConversionError_InvalidBinary:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConversionError_Overflow:
    pass

ConversionError: TypeAlias = Union[ConversionError_NegativeDecimal, ConversionError_InvalidBinary, ConversionError_Overflow]

"""Converts one decimal I64 to canonical binary text.

Every nonnegative value succeeds with the shortest sequence of ASCII `0`
and `1` digits, without leading zeros; zero is exactly `"0"`. A negative
value returns `NegativeDecimal`."""
"""Converts binary text to a nonnegative decimal I64.

The input must be nonempty and contain only ASCII `0` and `1`; leading
zeros are allowed and ignored. Any other input returns `InvalidBinary`.
After the entire string is validated, more than 63 significant digits
returns `Overflow`, so invalid characters take priority over overflow."""
"""Routes a tagged conversion through the matching decimal or binary
conversion operation and wraps its successful scalar result.

Errors from the selected operation are returned unchanged."""
__all__ = ["Conversion", "ConversionError", "ConversionError_InvalidBinary", "ConversionError_NegativeDecimal", "ConversionError_Overflow", "ConversionResult", "ConversionResult_Binary", "ConversionResult_Decimal", "Conversion_BinaryToDecimal", "Conversion_DecimalToBinary"]
