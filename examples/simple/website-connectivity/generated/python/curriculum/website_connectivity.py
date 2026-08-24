from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.website_connectivity_types import ConnectivityStatus, ConnectivityStatus_NotWorking, ConnectivityStatus_Working, WebsiteClassification, WebsiteObservation, WebsiteObservationError, WebsiteObservationError_EmptyUrl, WebsiteObservationError_InvalidStatusCode

def classify_observation(observation: WebsiteObservation) -> Result[WebsiteClassification, WebsiteObservationError]:
    """Validates and classifies one caller-supplied HTTP status observation.

An empty URL returns EmptyUrl before the status code is checked;
whitespace-only and otherwise nonempty URLs are accepted as opaque text
and preserved exactly. A status code outside the inclusive HTTP range 100
through 599 returns InvalidStatusCode.

Status 200 maps to Working; every other accepted status maps to NotWorking."""
    observation = _cott_validate_abi(observation, WebsiteObservation, path="$.observation")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len((observation).url) == 0)):
        _expected_error = WebsiteObservationError_EmptyUrl
        _expected_error_span = {"end_byte":1022,"end_column":73,"end_line":35,"start_byte":954,"start_column":5,"start_line":35}
        _expected_error_clause = "error:2"
    if _expected_error is None and ((((observation).status_code < 100) or ((observation).status_code > 599))):
        _expected_error = WebsiteObservationError_InvalidStatusCode
        _expected_error_span = {"end_byte":1144,"end_column":122,"end_line":36,"start_byte":1027,"start_column":5,"start_line":36}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/website_connectivity/classify_observation.py", "ce31ab98827979393256c8f59855d0f521c4d95c2c5541faf6acd5a442c913b6", "classify_observation", expected_project_name="website-connectivity", expected_cott_symbol="curriculum.website_connectivity.classify_observation")
        _result = _implementation(observation)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.website_connectivity.classify_observation"
        if _error.span is None:
            _error.span = {"end_byte":1162,"end_column":1,"end_line":40,"start_byte":296,"start_column":1,"start_line":19}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.website_connectivity.classify_observation", phase="implementation-call", span={"end_byte":1162,"end_column":1,"end_line":40,"start_byte":296,"start_column":1,"start_line":19}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.website_connectivity.classify_observation", phase="implementation-call", span={"end_byte":1162,"end_column":1,"end_line":40,"start_byte":296,"start_column":1,"start_line":19}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[WebsiteClassification, WebsiteObservationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.website_connectivity.classify_observation", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.website_connectivity.classify_observation", phase="error", span={"end_byte":1162,"end_column":1,"end_line":40,"start_byte":296,"start_column":1,"start_line":19}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.website_connectivity.classify_observation", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        classification = _result.value
        if not (((classification).url == (observation).url)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.website_connectivity.classify_observation", clause="ensures:1", phase="ensures", span={"end_byte":948,"end_column":79,"end_line":33,"start_byte":874,"start_column":5,"start_line":33}, expected="true", actual="false")
    return _result

def classify_websites(observations: CottList[WebsiteObservation]) -> Result[CottList[WebsiteClassification], WebsiteObservationError]:
    """Classifies website observations by applying classify_observation to each
item in input order.

The first invalid observation is returned unchanged. Within each item, an
empty URL takes priority over an invalid status code. Success contains one
classification per observation in the same order; empty input succeeds."""
    observations = _cott_validate_abi(observations, CottList[WebsiteObservation], path="$.observations")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/website_connectivity/classify_websites.py", "8cfd099a84281944330c2062f25cd85f5b37a72c5ba1424e0d9851ab496de9e6", "classify_websites", expected_project_name="website-connectivity", expected_cott_symbol="curriculum.website_connectivity.classify_websites")
        _result = _implementation(observations)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.website_connectivity.classify_websites"
        if _error.span is None:
            _error.span = {"end_byte":1850,"end_column":1,"end_line":58,"start_byte":1162,"start_column":1,"start_line":40}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.website_connectivity.classify_websites", phase="implementation-call", span={"end_byte":1850,"end_column":1,"end_line":58,"start_byte":1162,"start_column":1,"start_line":40}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.website_connectivity.classify_websites", phase="implementation-call", span={"end_byte":1850,"end_column":1,"end_line":58,"start_byte":1162,"start_column":1,"start_line":40}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[WebsiteClassification], WebsiteObservationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.website_connectivity.classify_websites", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (WebsiteObservationError_EmptyUrl, WebsiteObservationError_InvalidStatusCode,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.website_connectivity.classify_websites", phase="error", span={"end_byte":1850,"end_column":1,"end_line":58,"start_byte":1162,"start_column":1,"start_line":40}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.website_connectivity.classify_websites", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        classifications = _result.value
        if not ((len(classifications) == len(observations))):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.website_connectivity.classify_websites", clause="ensures:1", phase="ensures", span={"end_byte":1737,"end_column":82,"end_line":52,"start_byte":1660,"start_column":5,"start_line":52}, expected="true", actual="false")
    return _result

__all__ = ["ConnectivityStatus", "ConnectivityStatus_NotWorking", "ConnectivityStatus_Working", "WebsiteClassification", "WebsiteObservation", "WebsiteObservationError", "WebsiteObservationError_EmptyUrl", "WebsiteObservationError_InvalidStatusCode", "classify_observation", "classify_websites"]
