from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_any_blank_by, _cott_ends_with, _cott_starts_with

from real.posting.client_types import Header, HttpMethod, HttpMethod_Custom, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, PostingError, PostingError_InvalidArguments, PostingError_InvalidRequest, PostingError_NetworkFailed, Request, Response

def parse_method(source: str) -> Result[HttpMethod, PostingError]:
    """Parse an HTTP method name. A source equal to GET, HEAD, POST, PUT, PATCH,
DELETE or OPTIONS under ASCII case-insensitive comparison is that standard
variant. Any other HTTP token is HttpMethod.Custom with the source unchanged
(no case mapping). An HTTP token is one or more of the ASCII characters A-Z,
a-z, 0-9 and ! # $ % & ' * + - . ^ _ ` | ~. Every other source, including the
empty string, is InvalidRequest."""
    source = _cott_validate_abi(source, str, path="$.source")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((source == "")), "real.posting.client.parse_method", "error:2:condition")):
        _expected_error = PostingError_InvalidRequest
        _expected_error_span = {"end_byte":1146,"end_column":56,"end_line":47,"start_byte":1095,"start_column":5,"start_line":47}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/parse_method.py", "e719103fda297b6627701874bc2f0026766b9a6c80f28e7195f83f2c9fd5eea5", "parse_method", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.parse_method")
        _result = _implementation(source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.parse_method"
        if _error.span is None:
            _error.span = {"end_byte":1202,"end_column":1,"end_line":52,"start_byte":500,"start_column":1,"start_line":35}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.parse_method", phase="implementation-call", span={"end_byte":1202,"end_column":1,"end_line":52,"start_byte":500,"start_column":1,"start_line":35}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.parse_method", phase="implementation-call", span={"end_byte":1202,"end_column":1,"end_line":52,"start_byte":500,"start_column":1,"start_line":35}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[HttpMethod, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.parse_method", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidRequest,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.parse_method", phase="error", span={"end_byte":1202,"end_column":1,"end_line":52,"start_byte":500,"start_column":1,"start_line":35}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.parse_method", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.posting.client.parse_method", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is PostingError_InvalidRequest:
        _cott_contract_condition(True, "real.posting.client.parse_method", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and type(_cott_match_value.value) is HttpMethod_Custom and True:
            name = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[0].name)
            return (_cott_contract_condition(((name == source)), "real.posting.client.parse_method", "ensures:1"))
        _cott_contract_condition((False), "real.posting.client.parse_method", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.parse_method", clause="ensures:1", phase="ensures", span={"end_byte":1089,"end_column":65,"end_line":45,"start_byte":1029,"start_column":5,"start_line":45}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[HttpMethod, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def parse_arguments(arguments: CottList[str]) -> Result[Request, PostingError]:
    """Parse the command line METHOD URL [BODY]. The method is
real.posting.client.parse_method of METHOD, and its error is returned
unchanged. URL and BODY are copied verbatim; the URL is not validated here
(real.posting.client.send_request validates it). A missing BODY is the empty
string. The request has no headers and a 30000 millisecond timeout."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((len(arguments) < 2) or (len(arguments) > 3))), "real.posting.client.parse_arguments", "error:4:condition")):
        _expected_error = PostingError_InvalidArguments
        _expected_error_span = {"end_byte":1946,"end_column":84,"end_line":65,"start_byte":1867,"start_column":5,"start_line":65}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/parse_arguments.py", "23b99105154bf882669e864d66186fec8d77189bbb344d2b179076fedd563e70", "parse_arguments", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.parse_arguments")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.parse_arguments"
        if _error.span is None:
            _error.span = {"end_byte":2002,"end_column":1,"end_line":70,"start_byte":1202,"start_column":1,"start_line":52}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.parse_arguments", phase="implementation-call", span={"end_byte":2002,"end_column":1,"end_line":70,"start_byte":1202,"start_column":1,"start_line":52}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.parse_arguments", phase="implementation-call", span={"end_byte":2002,"end_column":1,"end_line":70,"start_byte":1202,"start_column":1,"start_line":52}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Request, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidRequest,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.parse_arguments", phase="error", span={"end_byte":2002,"end_column":1,"end_line":70,"start_byte":1202,"start_column":1,"start_line":52}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.posting.client.parse_arguments", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is PostingError_InvalidRequest:
        _cott_contract_condition(True, "real.posting.client.parse_arguments", "error:5")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return (_cott_contract_condition(((len((request).headers) == 0)), "real.posting.client.parse_arguments", "ensures:1"))
        _cott_contract_condition((False), "real.posting.client.parse_arguments", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.parse_arguments", clause="ensures:1", phase="ensures", span={"end_byte":1722,"end_column":59,"end_line":61,"start_byte":1668,"start_column":5,"start_line":61}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return (_cott_contract_condition((((request).timeout_ms == 30000)), "real.posting.client.parse_arguments", "ensures:2"))
        _cott_contract_condition((False), "real.posting.client.parse_arguments", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.parse_arguments", clause="ensures:2", phase="ensures", span={"end_byte":1784,"end_column":62,"end_line":62,"start_byte":1727,"start_column":5,"start_line":62}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return (_cott_contract_condition((((not (len(arguments) == 2)) or ((request).body == ""))), "real.posting.client.parse_arguments", "ensures:3"))
        _cott_contract_condition((False), "real.posting.client.parse_arguments", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.parse_arguments", clause="ensures:3", phase="ensures", span={"end_byte":1861,"end_column":77,"end_line":63,"start_byte":1789,"start_column":5,"start_line":63}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Request, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def send_request(request: Request) -> Result[Response, PostingError]:
    """Send one HTTP/1.1 request over the host network stack. The method name is
the upper-case standard name or the Custom name unchanged; request.headers
are sent in order; a non-empty body is sent as its UTF-8 bytes and an empty
body sends no payload. timeout_ms bounds the connection attempt and each
blocking read, in milliseconds.

HttpMethod.Get and HttpMethod.Head requests follow 301, 302, 303, 307 and 308
responses that carry a Location header, resolving a relative Location against
the current URL, at most 10 times; a further redirect response is returned as
received. Requests with any other method, including a Custom one, never follow
redirects.

The Response holds the final status, the final URL (request.url when no
redirect was followed), the received headers in received order with
duplicates kept, and the body decoded as UTF-8 with each undecodable byte
sequence replaced by U+FFFD; a Content-Type charset is ignored. A received
status of 400 or above is still a successful Response, never an error.

InvalidRequest: timeout_ms is 0; the URL does not start with the lower-case
"http://" or "https://" or has no host; a header name is blank or not an
HTTP token (as defined by real.posting.client.parse_method); a header value
contains CR or LF; or the method is a Custom name that is not an HTTP token.
No connection is attempted for an InvalidRequest. NetworkFailed: name
resolution, connection, timeout, a connection closed before a complete
response, or a final status outside 100-599."""
    request = _cott_validate_abi(request, Request, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((request).timeout_ms == 0)), "real.posting.client.send_request", "error:4:condition")):
        _expected_error = PostingError_InvalidRequest
        _expected_error_span = {"end_byte":4067,"end_column":67,"end_line":103,"start_byte":4005,"start_column":5,"start_line":103}
        _expected_error_clause = "error:4"
    if _expected_error is None and (_cott_contract_condition(((not (_cott_starts_with((request).url, "http://") or _cott_starts_with((request).url, "https://")))), "real.posting.client.send_request", "error:5:condition")):
        _expected_error = PostingError_InvalidRequest
        _expected_error_span = {"end_byte":4192,"end_column":125,"end_line":104,"start_byte":4072,"start_column":5,"start_line":104}
        _expected_error_clause = "error:5"
    if _expected_error is None and (_cott_contract_condition((_cott_any_blank_by((request).headers, "name")), "real.posting.client.send_request", "error:6:condition")):
        _expected_error = PostingError_InvalidRequest
        _expected_error_span = {"end_byte":4278,"end_column":86,"end_line":105,"start_byte":4197,"start_column":5,"start_line":105}
        _expected_error_clause = "error:6"
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/send_request.py", "4ffc4a3589c19e3aaa88f8b3df8b0973f8d339d71f179d0685ead19d938ec997", "send_request", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.send_request")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.send_request"
        if _error.span is None:
            _error.span = {"end_byte":4378,"end_column":1,"end_line":111,"start_byte":2002,"start_column":1,"start_line":70}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.send_request", phase="implementation-call", span={"end_byte":4378,"end_column":1,"end_line":111,"start_byte":2002,"start_column":1,"start_line":70}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.send_request", phase="implementation-call", span={"end_byte":4378,"end_column":1,"end_line":111,"start_byte":2002,"start_column":1,"start_line":70}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Response, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.send_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidRequest, PostingError_NetworkFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.send_request", phase="error", span={"end_byte":4378,"end_column":1,"end_line":111,"start_byte":2002,"start_column":1,"start_line":70}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.send_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.posting.client.send_request", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is PostingError_InvalidRequest:
        _cott_contract_condition(True, "real.posting.client.send_request", "error:7")
    if type(_result) is Err and type(_result.error) is PostingError_NetworkFailed:
        _cott_contract_condition(True, "real.posting.client.send_request", "error:8")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            response = _cott_match_value.value
            return (_cott_contract_condition(((100 <= (response).status <= 599)), "real.posting.client.send_request", "ensures:1"))
        _cott_contract_condition((False), "real.posting.client.send_request", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.send_request", clause="ensures:1", phase="ensures", span={"end_byte":3761,"end_column":65,"end_line":99,"start_byte":3701,"start_column":5,"start_line":99}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            response = _cott_match_value.value
            return (_cott_contract_condition((((not (not (((request).method == HttpMethod_Get()) or ((request).method == HttpMethod_Head())))) or ((response).url == (request).url))), "real.posting.client.send_request", "ensures:2"))
        _cott_contract_condition((False), "real.posting.client.send_request", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.send_request", clause="ensures:2", phase="ensures", span={"end_byte":3905,"end_column":144,"end_line":100,"start_byte":3766,"start_column":5,"start_line":100}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            response = _cott_match_value.value
            return (_cott_contract_condition((((not ((request).method == HttpMethod_Head())) or ((response).body == ""))), "real.posting.client.send_request", "ensures:3"))
        _cott_contract_condition((False), "real.posting.client.send_request", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.send_request", clause="ensures:3", phase="ensures", span={"end_byte":3999,"end_column":94,"end_line":101,"start_byte":3910,"start_column":5,"start_line":101}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Response, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def render_response(response: Response) -> str:
    """Render a response as LF-separated lines: first the decimal status, one space
and the URL; then one "NAME: VALUE" line per header in order; then one empty
line; then the body unchanged. There is no trailing LF after the body."""
    response = _cott_validate_abi(response, Response, path="$.response")
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/render_response.py", "69f073cd6a32d1ea94f05fc151960c308e3b807e79142d8d0f1939e16f20a0a7", "render_response", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.render_response")
        _result = _implementation(response)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.render_response"
        if _error.span is None:
            _error.span = {"end_byte":4831,"end_column":1,"end_line":124,"start_byte":4378,"start_column":1,"start_line":111}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.render_response", phase="implementation-call", span={"end_byte":4831,"end_column":1,"end_line":124,"start_byte":4378,"start_column":1,"start_line":111}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.render_response", phase="implementation-call", span={"end_byte":4831,"end_column":1,"end_line":124,"start_byte":4378,"start_column":1,"start_line":111}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not (_cott_contract_condition((((response).url in _result)), "real.posting.client.render_response", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.render_response", clause="ensures:1", phase="ensures", span={"end_byte":4727,"end_column":45,"end_line":118,"start_byte":4687,"start_column":5,"start_line":118}, expected="true", actual="false")
    if not (_cott_contract_condition((_cott_ends_with(_result, (response).body)), "real.posting.client.render_response", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.render_response", clause="ensures:2", phase="ensures", span={"end_byte":4774,"end_column":47,"end_line":119,"start_byte":4732,"start_column":5,"start_line":119}, expected="true", actual="false")
    if not (_cott_contract_condition((("\n\n" in _result)), "real.posting.client.render_response", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.render_response", clause="ensures:3", phase="ensures", span={"end_byte":4813,"end_column":39,"end_line":120,"start_byte":4779,"start_column":5,"start_line":120}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def execute(arguments: CottList[str]) -> Result[str, PostingError]:
    """The posting composition root. Call real.posting.client.parse_arguments with
arguments, pass its Request to real.posting.client.send_request, and return
real.posting.client.render_response of the received Response. An error from
parse_arguments is returned unchanged and no request is sent; an error from
send_request is returned unchanged and nothing is rendered."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((len(arguments) < 2) or (len(arguments) > 3))), "real.posting.client.execute", "error:2:condition")):
        _expected_error = PostingError_InvalidArguments
        _expected_error_span = {"end_byte":5589,"end_column":84,"end_line":137,"start_byte":5510,"start_column":5,"start_line":137}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/execute.py", "35612983578e67cdc37635fc49f6c650b7440e00279e3882b7ea25d0befd2af2", "execute", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.execute")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.execute"
        if _error.span is None:
            _error.span = {"end_byte":5689,"end_column":1,"end_line":143,"start_byte":4831,"start_column":1,"start_line":124}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.execute", phase="implementation-call", span={"end_byte":5689,"end_column":1,"end_line":143,"start_byte":4831,"start_column":1,"start_line":124}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.execute", phase="implementation-call", span={"end_byte":5689,"end_column":1,"end_line":143,"start_byte":4831,"start_column":1,"start_line":124}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidRequest, PostingError_NetworkFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.execute", phase="error", span={"end_byte":5689,"end_column":1,"end_line":143,"start_byte":4831,"start_column":1,"start_line":124}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.posting.client.execute", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is PostingError_InvalidRequest:
        _cott_contract_condition(True, "real.posting.client.execute", "error:3")
    if type(_result) is Err and type(_result.error) is PostingError_NetworkFailed:
        _cott_contract_condition(True, "real.posting.client.execute", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            rendered = _cott_match_value.value
            return (_cott_contract_condition((("\n\n" in rendered)), "real.posting.client.execute", "ensures:1"))
        _cott_contract_condition((False), "real.posting.client.execute", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.execute", clause="ensures:1", phase="ensures", span={"end_byte":5504,"end_column":62,"end_line":135,"start_byte":5447,"start_column":5,"start_line":135}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["Header", "HttpMethod", "HttpMethod_Custom", "HttpMethod_Delete", "HttpMethod_Get", "HttpMethod_Head", "HttpMethod_Options", "HttpMethod_Patch", "HttpMethod_Post", "HttpMethod_Put", "PostingError", "PostingError_InvalidArguments", "PostingError_InvalidRequest", "PostingError_NetworkFailed", "Request", "Response", "execute", "parse_arguments", "parse_method", "render_response", "send_request"]
