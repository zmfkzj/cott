from __future__ import annotations

import dataclasses as _dataclasses
from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.assignment_rule_types import Assignment, BaseAssignmentRule, ParseAssignmentError, ParseAssignmentError_EmptyName, ParseAssignmentError_MissingEquals, StrictAssignmentRule

def parse_assignment(line: str) -> Result[Assignment, ParseAssignmentError]:
    """Parses one assignment without I/O or mutation following strict rules."""
    line = _cott_validate_abi(line, str, path="$.line")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/assignment_rule/parse_assignment.py", "1e050560998a191e8d92e59d51e15bb902c3a6b2bec4bf49924703904289ddcc", "parse_assignment", expected_project_name="assignment-rule", expected_cott_symbol="curriculum.assignment_rule.parse_assignment")
        _result = _implementation(line)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.assignment_rule.parse_assignment"
        if _error.span is None:
            _error.span = {"end_byte":989,"end_column":1,"end_line":39,"start_byte":788,"start_column":1,"start_line":33}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.assignment_rule.parse_assignment", phase="implementation-call", span={"end_byte":989,"end_column":1,"end_line":39,"start_byte":788,"start_column":1,"start_line":33}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.assignment_rule.parse_assignment", phase="implementation-call", span={"end_byte":989,"end_column":1,"end_line":39,"start_byte":788,"start_column":1,"start_line":33}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Assignment, ParseAssignmentError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.assignment_rule.parse_assignment", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ParseAssignmentError_EmptyName,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.assignment_rule.parse_assignment", phase="error", span={"end_byte":989,"end_column":1,"end_line":39,"start_byte":788,"start_column":1,"start_line":33}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.assignment_rule.parse_assignment", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        assignment = _result.value
        if not ((len((assignment).name) > 1)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.assignment_rule.parse_assignment", clause="ensures:0", phase="ensures", span={"end_byte":628,"end_column":70,"end_line":25,"start_byte":563,"start_column":5,"start_line":25}, expected="true", actual="false")
    if type(_result) is Ok and True:
        assignment = _result.value
        if not ((len((assignment).value) > 0)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.assignment_rule.parse_assignment", clause="ensures:1", phase="ensures", span={"end_byte":744,"end_column":62,"end_line":29,"start_byte":687,"start_column":5,"start_line":29}, expected="true", actual="false")
    return _result

__all__ = ["Assignment", "BaseAssignmentRule", "ParseAssignmentError", "ParseAssignmentError_EmptyName", "ParseAssignmentError_MissingEquals", "StrictAssignmentRule", "parse_assignment"]
