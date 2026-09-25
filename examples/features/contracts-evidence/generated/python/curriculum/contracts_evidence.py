from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from curriculum.contracts_evidence_types import AcceptedLabel, LabelAssessment, LabelEvidenceError, LabelEvidenceError_Missing, LabelEvidenceError_TooShort, LabelRequest

def assess_label(request: LabelRequest) -> Result[LabelAssessment, LabelEvidenceError]:
    """Assess the offered label against the request's minimum length. Lengths count
Unicode scalar values, as Cott `.len` does. A missing label fails with
`Missing`. An offered label shorter than `minimum_length` fails with
`TooShort` whose `actual` is the offered label unchanged. Any other label is
accepted unchanged: the assessment's `text` and `label` are the offered label
and `length` is its length."""
    request = _cott_validate_abi(request, LabelRequest, path="$.request")
    if not (_cott_contract_condition((((request).minimum_length > 0)), "curriculum.contracts_evidence.assess_label", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="curriculum.contracts_evidence.assess_label", clause="requires:1", phase="requires", span={"end_byte":961,"end_column":40,"end_line":32,"start_byte":926,"start_column":5,"start_line":32}, expected="true", actual="false")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    def _cott_match_error_5() -> bool:
        _cott_match_value = (request).label
        if type(_cott_match_value) is Nothing:
            return (_cott_contract_condition((True), "curriculum.contracts_evidence.assess_label", "error:5:condition"))
        _cott_contract_condition((False), "curriculum.contracts_evidence.assess_label", "error:5:applicable")
        return False
    if _expected_error is None and (_cott_match_error_5()):
        _expected_error = LabelEvidenceError_Missing
        _expected_error_span = {"end_byte":1234,"end_column":79,"end_line":38,"start_byte":1160,"start_column":5,"start_line":38}
        _expected_error_clause = "error:5"
    def _cott_match_error_6() -> bool:
        _cott_match_value = (request).label
        if type(_cott_match_value) is Some and True:
            text = _cott_match_value.value
            return (_cott_contract_condition(((len(text) < (request).minimum_length)), "curriculum.contracts_evidence.assess_label", "error:6:condition"))
        _cott_contract_condition((False), "curriculum.contracts_evidence.assess_label", "error:6:applicable")
        return False
    if _expected_error is None and (_cott_match_error_6()):
        _expected_error = LabelEvidenceError_TooShort
        _expected_error_span = {"end_byte":1358,"end_column":124,"end_line":39,"start_byte":1239,"start_column":5,"start_line":39}
        _expected_error_clause = "error:6"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/contracts_evidence/assess_label.py", "d6bb6a1c4af2738f192bc18f77a388d0b11d8f754647977f59c1a9b02b3dc372", "assess_label", expected_project_name="contracts-evidence", expected_cott_symbol="curriculum.contracts_evidence.assess_label")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.contracts_evidence.assess_label"
        if _error.span is None:
            _error.span = {"end_byte":1376,"end_column":1,"end_line":43,"start_byte":390,"start_column":1,"start_line":22}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.contracts_evidence.assess_label", phase="implementation-call", span={"end_byte":1376,"end_column":1,"end_line":43,"start_byte":390,"start_column":1,"start_line":22}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.contracts_evidence.assess_label", phase="implementation-call", span={"end_byte":1376,"end_column":1,"end_line":43,"start_byte":390,"start_column":1,"start_line":22}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[LabelAssessment, LabelEvidenceError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.contracts_evidence.assess_label", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.contracts_evidence.assess_label", phase="error", span={"end_byte":1376,"end_column":1,"end_line":43,"start_byte":390,"start_column":1,"start_line":22}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.contracts_evidence.assess_label", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.contracts_evidence.assess_label", _expected_error_clause)
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            value = _cott_match_value.value
            return (_cott_contract_condition(((len((value).text) >= (request).minimum_length)), "curriculum.contracts_evidence.assess_label", "ensures:2"))
        _cott_contract_condition((False), "curriculum.contracts_evidence.assess_label", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.contracts_evidence.assess_label", clause="ensures:2", phase="ensures", span={"end_byte":1035,"end_column":73,"end_line":34,"start_byte":967,"start_column":5,"start_line":34}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is LabelEvidenceError_TooShort and True:
            actual = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((len(actual) < (request).minimum_length)), "curriculum.contracts_evidence.assess_label", "ensures:3"))
        _cott_contract_condition((False), "curriculum.contracts_evidence.assess_label", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.contracts_evidence.assess_label", clause="ensures:3", phase="ensures", span={"end_byte":1134,"end_column":99,"end_line":35,"start_byte":1040,"start_column":5,"start_line":35}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[LabelAssessment, LabelEvidenceError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["AcceptedLabel", "LabelAssessment", "LabelEvidenceError", "LabelEvidenceError_Missing", "LabelEvidenceError_TooShort", "LabelRequest", "assess_label"]
