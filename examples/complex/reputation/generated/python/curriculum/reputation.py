from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.reputation_types import Reputation, ReputationError, ReputationError_NegativeStarting, ReputationError_ReputationOverflow, ReputationError_WouldBecomeNegative, ReputationEvent, ReputationEvent_AcceptedAnswer, ReputationEvent_Downvote, ReputationEvent_Upvote, ReputationRequest

def reputation_delta(event: ReputationEvent) -> I32:
    """Return the fixed score change for one reputation event.

Upvotes add 10, downvotes subtract 2, and accepted answers add 15."""
    event = _cott_validate_abi(event, ReputationEvent, path="$.event")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/reputation/reputation_delta.py", "536d3d7296b7ad37389644cc62314e0115f04b9262e45c1606826ef2cfe0a792", "reputation_delta", expected_project_name="reputation", expected_cott_symbol="curriculum.reputation.reputation_delta")
        _result = _implementation(event)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.reputation.reputation_delta"
        if _error.span is None:
            _error.span = {"end_byte":526,"end_column":1,"end_line":29,"start_byte":301,"start_column":1,"start_line":20}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.reputation.reputation_delta", phase="implementation-call", span={"end_byte":526,"end_column":1,"end_line":29,"start_byte":301,"start_column":1,"start_line":20}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.reputation.reputation_delta", phase="implementation-call", span={"end_byte":526,"end_column":1,"end_line":29,"start_byte":301,"start_column":1,"start_line":20}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, I32, path="$.return")
    return _result

def calculate_reputation(request: ReputationRequest) -> Result[Reputation, ReputationError]:
    """Fold reputation events in request order from a non-negative starting score.

Reject a negative starting score before processing events. During the fold,
reject the first event that would overflow I32 or make the score negative."""
    request = _cott_validate_abi(request, ReputationRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (((request).starting < 0)):
        _expected_error = ReputationError_NegativeStarting
        _expected_error_span = {"end_byte":1079,"end_column":69,"end_line":40,"start_byte":1015,"start_column":5,"start_line":40}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/reputation/calculate_reputation.py", "6eda4aa34fa7b209e99d4798ed58468ece10376351a64ac6ca104538375c31cb", "calculate_reputation", expected_project_name="reputation", expected_cott_symbol="curriculum.reputation.calculate_reputation")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.reputation.calculate_reputation"
        if _error.span is None:
            _error.span = {"end_byte":1187,"end_column":1,"end_line":45,"start_byte":526,"start_column":1,"start_line":29}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.reputation.calculate_reputation", phase="implementation-call", span={"end_byte":1187,"end_column":1,"end_line":45,"start_byte":526,"start_column":1,"start_line":29}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.reputation.calculate_reputation", phase="implementation-call", span={"end_byte":1187,"end_column":1,"end_line":45,"start_byte":526,"start_column":1,"start_line":29}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Reputation, ReputationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.reputation.calculate_reputation", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ReputationError_ReputationOverflow, ReputationError_WouldBecomeNegative,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.reputation.calculate_reputation", phase="error", span={"end_byte":1187,"end_column":1,"end_line":45,"start_byte":526,"start_column":1,"start_line":29}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.reputation.calculate_reputation", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        reputation = _result.value
        if not (((reputation).value >= 0)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.reputation.calculate_reputation", clause="ensures:1", phase="ensures", span={"end_byte":941,"end_column":59,"end_line":37,"start_byte":887,"start_column":5,"start_line":37}, expected="true", actual="false")
    if type(_result) is Ok and True:
        reputation = _result.value
        if not (((reputation).value <= 2147483647)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.reputation.calculate_reputation", clause="ensures:2", phase="ensures", span={"end_byte":1009,"end_column":68,"end_line":38,"start_byte":946,"start_column":5,"start_line":38}, expected="true", actual="false")
    return _result

__all__ = ["Reputation", "ReputationError", "ReputationError_NegativeStarting", "ReputationError_ReputationOverflow", "ReputationError_WouldBecomeNegative", "ReputationEvent", "ReputationEvent_AcceptedAnswer", "ReputationEvent_Downvote", "ReputationEvent_Upvote", "ReputationRequest", "calculate_reputation", "reputation_delta"]
