from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.calculator_types import CalculatorError as CalculatorError, CalculatorError_DivideByZero as CalculatorError_DivideByZero, CalculatorOp as CalculatorOp, CalculatorOp_Add as CalculatorOp_Add, CalculatorOp_Divide as CalculatorOp_Divide, CalculatorOp_Multiply as CalculatorOp_Multiply, CalculatorOp_Subtract as CalculatorOp_Subtract
"""Apply one arithmetic operation and reject division by zero."""
def calculate(left: F64, operator: CalculatorOp, right: F64) -> Result[F64, CalculatorError]: ...

__all__ = ["CalculatorError", "CalculatorError_DivideByZero", "CalculatorOp", "CalculatorOp_Add", "CalculatorOp_Divide", "CalculatorOp_Multiply", "CalculatorOp_Subtract", "calculate"]
