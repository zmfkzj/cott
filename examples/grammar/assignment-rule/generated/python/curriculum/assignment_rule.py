from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.assignment_rule_types import Assignment, BaseAssignmentRule, ParseAssignmentError, ParseAssignmentError_EmptyName, ParseAssignmentError_MissingEquals, StrictAssignmentRule

def parse_assignment(line: str) -> Result[Assignment, ParseAssignmentError]:
    """Parses one {Assignment} without I/O or mutation following {StrictAssignmentRule}."""
    line = _cott_validate_abi(line, str, path="$.line")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/assignment_rule/parse_assignment.py", "1e050560998a191e8d92e59d51e15bb902c3a6b2bec4bf49924703904289ddcc", "parse_assignment", expected_project_name="assignment-rule", expected_cott_symbol="curriculum.assignment_rule.parse_assignment")
        _result = _implementation(line)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.assignment_rule.parse_assignment"
        if _error.span is None:
            _error.span = {"end_byte":1157,"end_column":1,"end_line":47,"start_byte":944,"start_column":1,"start_line":41}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.assignment_rule.parse_assignment", phase="implementation-call", span={"end_byte":1157,"end_column":1,"end_line":47,"start_byte":944,"start_column":1,"start_line":41}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.assignment_rule.parse_assignment", phase="implementation-call", span={"end_byte":1157,"end_column":1,"end_line":47,"start_byte":944,"start_column":1,"start_line":41}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Assignment, ParseAssignmentError], path="$.return")
    return _result

__all__ = ["Assignment", "BaseAssignmentRule", "ParseAssignmentError", "ParseAssignmentError_EmptyName", "ParseAssignmentError_MissingEquals", "StrictAssignmentRule", "parse_assignment"]
