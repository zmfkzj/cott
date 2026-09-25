from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from curriculum.assignment_rule_types import AccessCodeError, AccessCodeError_EmptyCode, AccessCodeError_LegacyFormat, AccessCodeError_TooShort, BaseAccessCodeRule, StrictAccessCodeRule

def validate_access_code(code: str) -> Result[str, AccessCodeError]:
    """Validate a code without modifying it: empty input fails first, then a code
shorter than four characters fails. A legacy prefix is not rejected."""
    code = _cott_validate_abi(code, str, path="$.code")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((len(code) == 0)), "curriculum.assignment_rule.validate_access_code", "error:2:condition")):
        _expected_error = AccessCodeError_EmptyCode
        _expected_error_span = {"end_byte":1064,"end_column":55,"end_line":37,"start_byte":1014,"start_column":5,"start_line":37}
        _expected_error_clause = "error:2"
    if _expected_error is None and (_cott_contract_condition(((len(code) < 4)), "curriculum.assignment_rule.validate_access_code", "error:3:condition")):
        _expected_error = AccessCodeError_TooShort
        _expected_error_span = {"end_byte":1117,"end_column":53,"end_line":38,"start_byte":1069,"start_column":5,"start_line":38}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/assignment_rule/validate_access_code.py", "ee44b2f60a5f9d0d0a559616193adfc9233eb9ba1ca08bee210fbdd6281af28b", "validate_access_code", expected_project_name="assignment-rule", expected_cott_symbol="curriculum.assignment_rule.validate_access_code")
        _result = _implementation(code)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.assignment_rule.validate_access_code"
        if _error.span is None:
            _error.span = {"end_byte":1119,"end_column":1,"end_line":40,"start_byte":663,"start_column":1,"start_line":26}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.assignment_rule.validate_access_code", phase="implementation-call", span={"end_byte":1119,"end_column":1,"end_line":40,"start_byte":663,"start_column":1,"start_line":26}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.assignment_rule.validate_access_code", phase="implementation-call", span={"end_byte":1119,"end_column":1,"end_line":40,"start_byte":663,"start_column":1,"start_line":26}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, AccessCodeError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.assignment_rule.validate_access_code", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.assignment_rule.validate_access_code", phase="error", span={"end_byte":1119,"end_column":1,"end_line":40,"start_byte":663,"start_column":1,"start_line":26}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.assignment_rule.validate_access_code", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.assignment_rule.validate_access_code", _expected_error_clause)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            value = _cott_match_value.value
            return (_cott_contract_condition(((len(value) >= 4)), "curriculum.assignment_rule.validate_access_code", "ensures:0"))
        _cott_contract_condition((False), "curriculum.assignment_rule.validate_access_code", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.assignment_rule.validate_access_code", clause="ensures:0", phase="ensures", span={"end_byte":614,"end_column":56,"end_line":22,"start_byte":563,"start_column":5,"start_line":22}, expected="true", actual="false")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            validated = _cott_match_value.value
            return (_cott_contract_condition(((validated == code)), "curriculum.assignment_rule.validate_access_code", "ensures:1"))
        _cott_contract_condition((False), "curriculum.assignment_rule.validate_access_code", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.assignment_rule.validate_access_code", clause="ensures:1", phase="ensures", span={"end_byte":988,"end_column":54,"end_line":34,"start_byte":939,"start_column":5,"start_line":34}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, AccessCodeError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["AccessCodeError", "AccessCodeError_EmptyCode", "AccessCodeError_LegacyFormat", "AccessCodeError_TooShort", "BaseAccessCodeRule", "StrictAccessCodeRule", "validate_access_code"]
