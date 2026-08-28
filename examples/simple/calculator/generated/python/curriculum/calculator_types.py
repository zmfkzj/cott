from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CalculatorOp_Add:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CalculatorOp_Subtract:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CalculatorOp_Multiply:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CalculatorOp_Divide:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CalculatorOp_Power:
    pass

CalculatorOp: TypeAlias = Union[CalculatorOp_Add, CalculatorOp_Subtract, CalculatorOp_Multiply, CalculatorOp_Divide, CalculatorOp_Power]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CalculatorError_DivideByZero:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CalculatorError_NonFinite:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CalculatorError_PowerDomain:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CalculatorError_Overflow:
    pass

CalculatorError: TypeAlias = Union[CalculatorError_DivideByZero, CalculatorError_NonFinite, CalculatorError_PowerDomain, CalculatorError_Overflow]

"""Validates one calculator request before evaluation.
Errors have this priority: NonFinite when either operand is NaN or
infinity, DivideByZero when division uses either sign of zero as the
divisor, then PowerDomain when zero has a negative exponent or a negative
base has a non-integral exponent."""
"""Validates and evaluates Add, Subtract, Multiply, Divide, or Power on two
binary64 operands. Validation errors are returned unchanged. A finite
result, including underflowed and signed zero values, is returned
unchanged; a non-finite result from finite operands returns Overflow.
Zero to the zero power is 1, and no operation returns a complex value."""
__all__ = ["CalculatorError", "CalculatorError_DivideByZero", "CalculatorError_NonFinite", "CalculatorError_Overflow", "CalculatorError_PowerDomain", "CalculatorOp", "CalculatorOp_Add", "CalculatorOp_Divide", "CalculatorOp_Multiply", "CalculatorOp_Power", "CalculatorOp_Subtract"]
