from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from real.posting.client_types import Header, HttpMethod, HttpMethod_Custom, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, PostingError, PostingError_InvalidArguments, PostingError_InvalidRequest, PostingError_NetworkFailed, Request, Response

def parse_method(source: str) -> Result[HttpMethod, PostingError]:
    """Accept standard HTTP methods case-insensitively; preserve other non-empty methods."""
    source = _cott_validate_abi(source, str, path="$.source")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/parse_method.py", "c7a3e668f644c430f7f7958520b5f8b25949f432f342ab64482593883a14eabb", "parse_method", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.parse_method")
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
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            method = _cott_match_value.value
            return ((len(source) > 0))
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
        _implementation = _cott_load("_cott_impl/real/posting/client/parse_arguments.py", "c5338299c0231280ac676c78962ebdf8ebfd4fadf81a95005c71e661403e673d", "parse_arguments", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.parse_arguments")
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
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return ((len(arguments) >= 2))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.parse_arguments", clause="ensures:1", phase="ensures", span={"end_byte":995,"end_column":53,"end_line":51,"start_byte":947,"start_column":5,"start_line":51}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Request, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def send_request(request: Request) -> Result[Response, PostingError]:
    """Send one HTTP request and retain status, final URL, headers, and response bytes."""
    request = _cott_validate_abi(request, Request, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/send_request.py", "e48b354421e312b8b3c8c927f8ee79829f61e10aaf95e6bc87eebdb440eab288", "send_request", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.send_request")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.send_request"
        if _error.span is None:
            _error.span = {"end_byte":1422,"end_column":1,"end_line":70,"start_byte":1092,"start_column":1,"start_line":58}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.send_request", phase="implementation-call", span={"end_byte":1422,"end_column":1,"end_line":70,"start_byte":1092,"start_column":1,"start_line":58}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.send_request", phase="implementation-call", span={"end_byte":1422,"end_column":1,"end_line":70,"start_byte":1092,"start_column":1,"start_line":58}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Response, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.send_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidRequest, PostingError_NetworkFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.send_request", phase="error", span={"end_byte":1422,"end_column":1,"end_line":70,"start_byte":1092,"start_column":1,"start_line":58}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.send_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            response = _cott_match_value.value
            return (((response).status > 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.send_request", clause="ensures:1", phase="ensures", span={"end_byte":1321,"end_column":55,"end_line":63,"start_byte":1271,"start_column":5,"start_line":63}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Response, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def render_response(response: Response) -> str:
    """Render status and final URL, then headers and a UTF-8 replacement-decoded body."""
    response = _cott_validate_abi(response, Response, path="$.response")
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/render_response.py", "8ba935adde0bc4951ecb92b86ebd8d298313c2bc8fadb760e6e758f970659fa5", "render_response", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.render_response")
        _result = _implementation(response)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.render_response"
        if _error.span is None:
            _error.span = {"end_byte":1590,"end_column":1,"end_line":77,"start_byte":1422,"start_column":1,"start_line":70}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.render_response", phase="implementation-call", span={"end_byte":1590,"end_column":1,"end_line":77,"start_byte":1422,"start_column":1,"start_line":70}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.render_response", phase="implementation-call", span={"end_byte":1590,"end_column":1,"end_line":77,"start_byte":1422,"start_column":1,"start_line":70}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def execute(arguments: CottList[str]) -> Result[str, PostingError]:
    """Parse arguments, send the request, and render its response."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/execute.py", "9b14a36537ae9ccc5a41a857d5c1aee7cbf210b2d9f176ea113f8b3b658ac4b3", "execute", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.execute")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.execute"
        if _error.span is None:
            _error.span = {"end_byte":1929,"end_column":1,"end_line":89,"start_byte":1590,"start_column":1,"start_line":77}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.execute", phase="implementation-call", span={"end_byte":1929,"end_column":1,"end_line":89,"start_byte":1590,"start_column":1,"start_line":77}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.execute", phase="implementation-call", span={"end_byte":1929,"end_column":1,"end_line":89,"start_byte":1590,"start_column":1,"start_line":77}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidArguments, PostingError_InvalidRequest, PostingError_NetworkFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.execute", phase="error", span={"end_byte":1929,"end_column":1,"end_line":89,"start_byte":1590,"start_column":1,"start_line":77}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            rendered = _cott_match_value.value
            return ((len(rendered) > 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.execute", clause="ensures:1", phase="ensures", span={"end_byte":1789,"end_column":52,"end_line":82,"start_byte":1742,"start_column":5,"start_line":82}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["Header", "HttpMethod", "HttpMethod_Custom", "HttpMethod_Delete", "HttpMethod_Get", "HttpMethod_Head", "HttpMethod_Options", "HttpMethod_Patch", "HttpMethod_Post", "HttpMethod_Put", "PostingError", "PostingError_InvalidArguments", "PostingError_InvalidRequest", "PostingError_NetworkFailed", "Request", "Response", "execute", "parse_arguments", "parse_method", "render_response", "send_request"]
