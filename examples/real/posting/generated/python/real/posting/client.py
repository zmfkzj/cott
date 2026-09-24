from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.posting.client_types import Header, HttpMethod, HttpMethod_Custom, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, PostingError, PostingError_InvalidArguments, PostingError_InvalidRequest, PostingError_NetworkFailed, Request, Response

def parse_method(source: str) -> Result[HttpMethod, PostingError]:
    """Accept standard HTTP methods case-insensitively; preserve other non-empty methods."""
    source = _cott_validate_abi(source, str, path="$.source")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/parse_method.py", "981f7c79b35ac6afda06600b9f66046f40abd2fc737af1603770dab3e5ccd18d", "parse_method", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.parse_method")
        _result = _implementation(source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.parse_method"
        if _error.span is None:
            _error.span = {"end_byte":778,"end_column":1,"end_line":46,"start_byte":500,"start_column":1,"start_line":35}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.parse_method", phase="implementation-call", span={"end_byte":778,"end_column":1,"end_line":46,"start_byte":500,"start_column":1,"start_line":35}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.parse_method", phase="implementation-call", span={"end_byte":778,"end_column":1,"end_line":46,"start_byte":500,"start_column":1,"start_line":35}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[HttpMethod, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.parse_method", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidRequest,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.parse_method", phase="error", span={"end_byte":778,"end_column":1,"end_line":46,"start_byte":500,"start_column":1,"start_line":35}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.parse_method", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.posting.client.parse_method", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is PostingError_InvalidRequest:
        _cott_contract_condition(True, "real.posting.client.parse_method", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            method = _cott_match_value.value
            return (_cott_contract_condition(((len(source) > 0)), "real.posting.client.parse_method", "ensures:1"))
        _cott_contract_condition((False), "real.posting.client.parse_method", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.parse_method", clause="ensures:1", phase="ensures", span={"end_byte":721,"end_column":48,"end_line":40,"start_byte":678,"start_column":5,"start_line":40}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[HttpMethod, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def parse_arguments(arguments: CottList[str]) -> Result[Request, PostingError]:
    """Parse METHOD URL [BODY]; use a 30-second timeout and no headers."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/parse_arguments.py", "4407288432d83ab6810d54ab5a22d8bc6f4f7050e118b91bd57e6ac24a9f6845", "parse_arguments", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.parse_arguments")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.parse_arguments"
        if _error.span is None:
            _error.span = {"end_byte":1092,"end_column":1,"end_line":58,"start_byte":778,"start_column":1,"start_line":46}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.parse_arguments", phase="implementation-call", span={"end_byte":1092,"end_column":1,"end_line":58,"start_byte":778,"start_column":1,"start_line":46}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.parse_arguments", phase="implementation-call", span={"end_byte":1092,"end_column":1,"end_line":58,"start_byte":778,"start_column":1,"start_line":46}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Request, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidArguments, PostingError_InvalidRequest,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.parse_arguments", phase="error", span={"end_byte":1092,"end_column":1,"end_line":58,"start_byte":778,"start_column":1,"start_line":46}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.posting.client.parse_arguments", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is PostingError_InvalidArguments:
        _cott_contract_condition(True, "real.posting.client.parse_arguments", "error:2")
    if type(_result) is Err and type(_result.error) is PostingError_InvalidRequest:
        _cott_contract_condition(True, "real.posting.client.parse_arguments", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return (_cott_contract_condition(((len(arguments) >= 2)), "real.posting.client.parse_arguments", "ensures:1"))
        _cott_contract_condition((False), "real.posting.client.parse_arguments", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.parse_arguments", clause="ensures:1", phase="ensures", span={"end_byte":995,"end_column":53,"end_line":51,"start_byte":947,"start_column":5,"start_line":51}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Request, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def send_request(request: Request) -> Result[Response, PostingError]:
    """Send one HTTP request and retain status, final URL, headers, and the response
body decoded as UTF-8 with replacement characters for undecodable bytes. An HTTP
error status is still a received Response; InvalidRequest covers a non-HTTP(S)
URL, and NetworkFailed covers connection, timeout, and URL errors."""
    request = _cott_validate_abi(request, Request, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/send_request.py", "b4dfbec9d0a3f154c30b4de3aa92d0b8f99f6eb084cdaa34a76045beaed61e12", "send_request", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.send_request")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.send_request"
        if _error.span is None:
            _error.span = {"end_byte":1658,"end_column":1,"end_line":73,"start_byte":1092,"start_column":1,"start_line":58}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.send_request", phase="implementation-call", span={"end_byte":1658,"end_column":1,"end_line":73,"start_byte":1092,"start_column":1,"start_line":58}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.send_request", phase="implementation-call", span={"end_byte":1658,"end_column":1,"end_line":73,"start_byte":1092,"start_column":1,"start_line":58}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Response, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.send_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidRequest, PostingError_NetworkFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.send_request", phase="error", span={"end_byte":1658,"end_column":1,"end_line":73,"start_byte":1092,"start_column":1,"start_line":58}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.send_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.posting.client.send_request", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is PostingError_InvalidRequest:
        _cott_contract_condition(True, "real.posting.client.send_request", "error:2")
    if type(_result) is Err and type(_result.error) is PostingError_NetworkFailed:
        _cott_contract_condition(True, "real.posting.client.send_request", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            response = _cott_match_value.value
            return (_cott_contract_condition((((response).status > 0)), "real.posting.client.send_request", "ensures:1"))
        _cott_contract_condition((False), "real.posting.client.send_request", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.send_request", clause="ensures:1", phase="ensures", span={"end_byte":1557,"end_column":55,"end_line":66,"start_byte":1507,"start_column":5,"start_line":66}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Response, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def render_response(response: Response) -> str:
    """Render status and final URL, then headers and a UTF-8 replacement-decoded body."""
    response = _cott_validate_abi(response, Response, path="$.response")
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/render_response.py", "baadae63d7be76cf9de88896edb56e2c6291bff91c96d7e520aad63978f02ec7", "render_response", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.render_response")
        _result = _implementation(response)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.render_response"
        if _error.span is None:
            _error.span = {"end_byte":1826,"end_column":1,"end_line":80,"start_byte":1658,"start_column":1,"start_line":73}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.render_response", phase="implementation-call", span={"end_byte":1826,"end_column":1,"end_line":80,"start_byte":1658,"start_column":1,"start_line":73}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.render_response", phase="implementation-call", span={"end_byte":1826,"end_column":1,"end_line":80,"start_byte":1658,"start_column":1,"start_line":73}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def execute(arguments: CottList[str]) -> Result[str, PostingError]:
    """Call real.posting.client.parse_arguments, pass its request to
real.posting.client.send_request, and return the successful response rendered
by real.posting.client.render_response. Return an error from either earlier
operation unchanged; do not send a request after argument parsing fails."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/execute.py", "35612983578e67cdc37635fc49f6c650b7440e00279e3882b7ea25d0befd2af2", "execute", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.execute")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.execute"
        if _error.span is None:
            _error.span = {"end_byte":2406,"end_column":1,"end_line":95,"start_byte":1826,"start_column":1,"start_line":80}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.execute", phase="implementation-call", span={"end_byte":2406,"end_column":1,"end_line":95,"start_byte":1826,"start_column":1,"start_line":80}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.execute", phase="implementation-call", span={"end_byte":2406,"end_column":1,"end_line":95,"start_byte":1826,"start_column":1,"start_line":80}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidArguments, PostingError_InvalidRequest, PostingError_NetworkFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.execute", phase="error", span={"end_byte":2406,"end_column":1,"end_line":95,"start_byte":1826,"start_column":1,"start_line":80}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.posting.client.execute", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is PostingError_InvalidArguments:
        _cott_contract_condition(True, "real.posting.client.execute", "error:2")
    if type(_result) is Err and type(_result.error) is PostingError_InvalidRequest:
        _cott_contract_condition(True, "real.posting.client.execute", "error:3")
    if type(_result) is Err and type(_result.error) is PostingError_NetworkFailed:
        _cott_contract_condition(True, "real.posting.client.execute", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            rendered = _cott_match_value.value
            return (_cott_contract_condition(((len(rendered) > 0)), "real.posting.client.execute", "ensures:1"))
        _cott_contract_condition((False), "real.posting.client.execute", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.execute", clause="ensures:1", phase="ensures", span={"end_byte":2266,"end_column":52,"end_line":88,"start_byte":2219,"start_column":5,"start_line":88}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["Header", "HttpMethod", "HttpMethod_Custom", "HttpMethod_Delete", "HttpMethod_Get", "HttpMethod_Head", "HttpMethod_Options", "HttpMethod_Patch", "HttpMethod_Post", "HttpMethod_Put", "PostingError", "PostingError_InvalidArguments", "PostingError_InvalidRequest", "PostingError_NetworkFailed", "Request", "Response", "execute", "parse_arguments", "parse_method", "render_response", "send_request"]
