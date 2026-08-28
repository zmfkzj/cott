from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.calculator_types import CalculatorError as CalculatorError, CalculatorError_DivideByZero as CalculatorError_DivideByZero, CalculatorError_NonFinite as CalculatorError_NonFinite, CalculatorError_Overflow as CalculatorError_Overflow, CalculatorError_PowerDomain as CalculatorError_PowerDomain, CalculatorOp as CalculatorOp, CalculatorOp_Add as CalculatorOp_Add, CalculatorOp_Divide as CalculatorOp_Divide, CalculatorOp_Multiply as CalculatorOp_Multiply, CalculatorOp_Power as CalculatorOp_Power, CalculatorOp_Subtract as CalculatorOp_Subtract
"""Validates one calculator request before evaluation.
Errors have this priority: NonFinite when either operand is NaN or
infinity, DivideByZero when division uses either sign of zero as the
divisor, then PowerDomain when zero has a negative exponent or a negative
base has a non-integral exponent."""
def validate_calculation(left: F64, operator: CalculatorOp, right: F64) -> Result[Unit, CalculatorError]: ...

"""Validates and evaluates Add, Subtract, Multiply, Divide, or Power on two
binary64 operands. Validation errors are returned unchanged. A finite
result, including underflowed and signed zero values, is returned
unchanged; a non-finite result from finite operands returns Overflow.
Zero to the zero power is 1, and no operation returns a complex value."""
def calculate(left: F64, operator: CalculatorOp, right: F64) -> Result[F64, CalculatorError]: ...

__all__ = ["CalculatorError", "CalculatorError_DivideByZero", "CalculatorError_NonFinite", "CalculatorError_Overflow", "CalculatorError_PowerDomain", "CalculatorOp", "CalculatorOp_Add", "CalculatorOp_Divide", "CalculatorOp_Multiply", "CalculatorOp_Power", "CalculatorOp_Subtract", "calculate", "validate_calculation"]
