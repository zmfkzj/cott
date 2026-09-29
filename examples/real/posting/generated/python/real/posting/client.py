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

from real.posting.client_types import Header, HttpMethod, HttpMethod_Custom, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, MAX_RESPONSE_BODY_BYTES, PostingError, PostingError_InvalidArguments, PostingError_InvalidRequest, PostingError_NetworkFailed, Request, Response

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
        _expected_error_span = {"end_byte":1193,"end_column":56,"end_line":49,"start_byte":1142,"start_column":5,"start_line":49}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/parse_method.py", "e719103fda297b6627701874bc2f0026766b9a6c80f28e7195f83f2c9fd5eea5", "parse_method", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.parse_method")
        _result = _implementation(source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.parse_method"
        if _error.span is None:
            _error.span = {"end_byte":1249,"end_column":1,"end_line":54,"start_byte":547,"start_column":1,"start_line":37}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.parse_method", phase="implementation-call", span={"end_byte":1249,"end_column":1,"end_line":54,"start_byte":547,"start_column":1,"start_line":37}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.parse_method", phase="implementation-call", span={"end_byte":1249,"end_column":1,"end_line":54,"start_byte":547,"start_column":1,"start_line":37}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[HttpMethod, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.parse_method", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidRequest,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.parse_method", phase="error", span={"end_byte":1249,"end_column":1,"end_line":54,"start_byte":547,"start_column":1,"start_line":37}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
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
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.parse_method", clause="ensures:1", phase="ensures", span={"end_byte":1136,"end_column":65,"end_line":47,"start_byte":1076,"start_column":5,"start_line":47}, expected="true", actual="false")
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
        _expected_error_span = {"end_byte":1993,"end_column":84,"end_line":67,"start_byte":1914,"start_column":5,"start_line":67}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/parse_arguments.py", "a06e14ade8096ca2ba75d9f8d1607f8f3aa8a7067dec954e1b4388db26a34075", "parse_arguments", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.parse_arguments")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.parse_arguments"
        if _error.span is None:
            _error.span = {"end_byte":2049,"end_column":1,"end_line":72,"start_byte":1249,"start_column":1,"start_line":54}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.parse_arguments", phase="implementation-call", span={"end_byte":2049,"end_column":1,"end_line":72,"start_byte":1249,"start_column":1,"start_line":54}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.parse_arguments", phase="implementation-call", span={"end_byte":2049,"end_column":1,"end_line":72,"start_byte":1249,"start_column":1,"start_line":54}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Request, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidRequest,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.parse_arguments", phase="error", span={"end_byte":2049,"end_column":1,"end_line":72,"start_byte":1249,"start_column":1,"start_line":54}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
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
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.parse_arguments", clause="ensures:1", phase="ensures", span={"end_byte":1769,"end_column":59,"end_line":63,"start_byte":1715,"start_column":5,"start_line":63}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return (_cott_contract_condition((((request).timeout_ms == 30000)), "real.posting.client.parse_arguments", "ensures:2"))
        _cott_contract_condition((False), "real.posting.client.parse_arguments", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.parse_arguments", clause="ensures:2", phase="ensures", span={"end_byte":1831,"end_column":62,"end_line":64,"start_byte":1774,"start_column":5,"start_line":64}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return (_cott_contract_condition((((not (len(arguments) == 2)) or ((request).body == ""))), "real.posting.client.parse_arguments", "ensures:3"))
        _cott_contract_condition((False), "real.posting.client.parse_arguments", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.parse_arguments", clause="ensures:3", phase="ensures", span={"end_byte":1908,"end_column":77,"end_line":65,"start_byte":1836,"start_column":5,"start_line":65}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Request, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def send_request(request: Request) -> Result[Response, PostingError]:
    """Send one HTTP/1.1 request over the host network stack. The method name is
the upper-case standard name or the Custom name unchanged; request.headers
are sent in order; a non-empty body is sent as its UTF-8 bytes and an empty
body sends no payload. timeout_ms bounds the connection attempt and each
blocking read, in milliseconds.

The URL consists only of RFC 3986 characters: ASCII letters, digits and
- . _ ~ : / ? # [ ] @ ! $ & ' ( ) * + , ; =, plus "%" always followed by two
hexadecimal digits. Any other character (space, control character, non-ASCII
character, < > " { } | backslash ^ or the grave accent) and any "%" not
followed by two hexadecimal digits make the request InvalidRequest.

The request target is the URL path ("/" when the path is empty), followed by
"?" and the query when the URL contains a "?" before any "#" (even when the
query is empty). The literal "." and ".." segments of the path are removed
as in RFC 3986 section 5.2.4 (so /a/./b/../echo is sent as /a/echo);
percent-encoded dots are not decoded and stay. The fragment is never sent.
Percent-encoded octets are sent exactly as written, neither decoded nor
re-encoded. Unless request.headers has
a header named Host (ASCII case-insensitive), a Host header is sent whose
value is the URL host exactly as written (ASCII case kept, an IPv6 literal
with its brackets, no userinfo), followed by ":" and the port only when the
port differs from the scheme default (80 for http, 443 for https). The port
is a run of decimal digits whose decimal value is used (leading zeros are
allowed and never shown, so ":080" on an http URL sends no port); an empty
port means the scheme default. A port with a non-digit or a value above
65535 makes the request InvalidRequest, and port 0 is attempted and fails as
NetworkFailed. URL userinfo is neither sent nor used for authentication, and Response.url
keeps the URL as given.

HttpMethod.Get and HttpMethod.Head requests follow 301, 302, 303, 307 and 308
responses that carry a Location header, at most 10 times; a further redirect
response is returned as received. Requests with any other method, including a
Custom one, never follow redirects. The Location is resolved against the
current URL by RFC 3986 section 5.2 (strict; dot segments removed by section
5.2.4; empty path segments kept; a query-only reference keeps the base path;
the fragment of the reference is kept in the resolved URL and the fragment of
the base is not inherited). For example, the base http://h/dir/redir with
Location "?q=1" resolves to http://h/dir/redir?q=1, the base http://h/redir
with "../../echo" resolves to http://h/echo, and the base http://h/a/b/c with
"..//g" resolves to http://h/a//g. A Location that does not consist only of
the URL characters above, or that resolves to a URL that is not http or https
or has no host, is not followed and that 3xx response is returned. When the
response has several Location fields, the Location is their values in
received order joined with ", "; such a value contains a space, so it is
never valid and the 3xx response is returned. The scheme of a Location is
case-insensitive: the resolved URL, which is used for the next request, for
Response.url and for the origin comparison, has its scheme in lower case
and otherwise keeps the rules above. A Location whose port contains a
non-digit or is above 65535 is not followed and that 3xx response is
returned.

A redirect is followed only when it does not leave https for http; a 3xx
response whose Location is an http:// URL while the current URL is https:// is
not followed and is returned as the result. When a followed redirect changes
the origin compared with the previous URL (scheme and host compared ASCII
case-insensitively, port compared as its decimal value after applying the scheme default), the request
headers named Authorization, Cookie, Proxy-Authorization and Host (ASCII
case-insensitive name comparison) are not sent to the new origin; all other
request headers are still sent. A redirect within the same origin keeps every
header. The Host header of every request, including one sent after a followed
redirect, follows the Host rule above for the URL being requested, so a Host
header removed by the credential rule is replaced by the URL's own host.

The Response holds the final status, the final URL (request.url when no
redirect was followed), the received headers in received order with
duplicates kept, names as received and values with leading and trailing
space and horizontal tab removed, and the body decoded as UTF-8 with each maximal subpart of
an ill-formed sequence (Unicode section 3.9, Table 3-8) replaced by one
U+FFFD, so the bytes ED A0 80 become three U+FFFD; a leading byte order mark
is kept as U+FEFF and NUL is kept; a Content-Type charset is ignored. A received header field name is one or
more HTTP token characters (as defined by real.posting.client.parse_method)
immediately followed by ":"; any other field line (a name with a non-ASCII
byte, "@" or another non-token character, an empty name, whitespace before
the colon, or no colon) is NetworkFailed. The header values of the final
response are decoded as a whole: when every value is ASCII they are used as
is; otherwise, when every value is valid UTF-8 they are decoded as UTF-8;
otherwise every value is decoded as ISO-8859-1. A received
status of 400 or above is still a successful Response, never an error.

The received body is limited to MAX_RESPONSE_BODY_BYTES (67108864) bytes,
counted before decoding; a body of more bytes is NetworkFailed and no partial
Response is returned.

A response to a request whose wire method is exactly HEAD (HttpMethod.Head
or a Custom name HEAD) has no body whatever its Content-Length or
Transfer-Encoding say, and a response with status 204 or 304 has no body
either. An interim response with status 100 or 102 to 199 is read together
with its headers and discarded, and the next response is read; a 101 response
is NetworkFailed because no protocol upgrade is ever requested. The status
line is HTTP/1.x, a space and three digits, optionally followed by a space and
a reason phrase that may be empty; a missing reason phrase is accepted.
A chunk-size line starts with one or more hexadecimal digits, after which
only nothing, spaces or horizontal tabs, or optional spaces or horizontal
tabs followed by ";" and an ignored chunk extension may follow; any other
line (leading whitespace, a "0x" prefix, other characters, no digits) is
NetworkFailed. Trailer fields are read and discarded and are not part of
Response.headers. A connection closed after the last chunk (size 0) but before
the final empty line is NetworkFailed.

InvalidRequest: timeout_ms is 0; the URL does not start with the lower-case
"http://" or "https://", has no host, has a character outside the URL
characters above or has an unusable port; a header name is blank or not an
HTTP token (as defined by real.posting.client.parse_method); a header value
contains CR or LF or a character above U+007F; or the method is a Custom name that is not an HTTP token.
No connection is attempted for an InvalidRequest. NetworkFailed: name
resolution, connection, timeout, a connection closed before the empty line
that ends the header block, before all Content-Length bytes, or before the
terminating chunk of a chunked body, a response that does not start with an
HTTP/1.x status line, a header line whose name is not an HTTP token followed by a colon, a response body larger
than MAX_RESPONSE_BODY_BYTES, or a final status outside 100-599. No partial
Response is returned. When the response has neither a Content-Length nor
chunked transfer coding, the body extends to the connection close."""
    request = _cott_validate_abi(request, Request, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((request).timeout_ms == 0)), "real.posting.client.send_request", "error:4:condition")):
        _expected_error = PostingError_InvalidRequest
        _expected_error_span = {"end_byte":10654,"end_column":67,"end_line":193,"start_byte":10592,"start_column":5,"start_line":193}
        _expected_error_clause = "error:4"
    if _expected_error is None and (_cott_contract_condition(((not (_cott_starts_with((request).url, "http://") or _cott_starts_with((request).url, "https://")))), "real.posting.client.send_request", "error:5:condition")):
        _expected_error = PostingError_InvalidRequest
        _expected_error_span = {"end_byte":10779,"end_column":125,"end_line":194,"start_byte":10659,"start_column":5,"start_line":194}
        _expected_error_clause = "error:5"
    if _expected_error is None and (_cott_contract_condition((_cott_any_blank_by((request).headers, "name")), "real.posting.client.send_request", "error:6:condition")):
        _expected_error = PostingError_InvalidRequest
        _expected_error_span = {"end_byte":10865,"end_column":86,"end_line":195,"start_byte":10784,"start_column":5,"start_line":195}
        _expected_error_clause = "error:6"
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/send_request.py", "ddbe010d626dd32b439ea8a7b3505df376040ea5cf7032e6f0bc2c89c5e2b560", "send_request", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.send_request")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.send_request"
        if _error.span is None:
            _error.span = {"end_byte":10965,"end_column":1,"end_line":201,"start_byte":2049,"start_column":1,"start_line":72}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.send_request", phase="implementation-call", span={"end_byte":10965,"end_column":1,"end_line":201,"start_byte":2049,"start_column":1,"start_line":72}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.send_request", phase="implementation-call", span={"end_byte":10965,"end_column":1,"end_line":201,"start_byte":2049,"start_column":1,"start_line":72}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Response, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.send_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidRequest, PostingError_NetworkFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.send_request", phase="error", span={"end_byte":10965,"end_column":1,"end_line":201,"start_byte":2049,"start_column":1,"start_line":72}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
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
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.send_request", clause="ensures:1", phase="ensures", span={"end_byte":10348,"end_column":65,"end_line":189,"start_byte":10288,"start_column":5,"start_line":189}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            response = _cott_match_value.value
            return (_cott_contract_condition((((not (not (((request).method == HttpMethod_Get()) or ((request).method == HttpMethod_Head())))) or ((response).url == (request).url))), "real.posting.client.send_request", "ensures:2"))
        _cott_contract_condition((False), "real.posting.client.send_request", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.send_request", clause="ensures:2", phase="ensures", span={"end_byte":10492,"end_column":144,"end_line":190,"start_byte":10353,"start_column":5,"start_line":190}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            response = _cott_match_value.value
            return (_cott_contract_condition((((not ((request).method == HttpMethod_Head())) or ((response).body == ""))), "real.posting.client.send_request", "ensures:3"))
        _cott_contract_condition((False), "real.posting.client.send_request", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.send_request", clause="ensures:3", phase="ensures", span={"end_byte":10586,"end_column":94,"end_line":191,"start_byte":10497,"start_column":5,"start_line":191}, expected="true", actual="false")
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
            _error.span = {"end_byte":11418,"end_column":1,"end_line":214,"start_byte":10965,"start_column":1,"start_line":201}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.render_response", phase="implementation-call", span={"end_byte":11418,"end_column":1,"end_line":214,"start_byte":10965,"start_column":1,"start_line":201}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.render_response", phase="implementation-call", span={"end_byte":11418,"end_column":1,"end_line":214,"start_byte":10965,"start_column":1,"start_line":201}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not (_cott_contract_condition((((response).url in _result)), "real.posting.client.render_response", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.render_response", clause="ensures:1", phase="ensures", span={"end_byte":11314,"end_column":45,"end_line":208,"start_byte":11274,"start_column":5,"start_line":208}, expected="true", actual="false")
    if not (_cott_contract_condition((_cott_ends_with(_result, (response).body)), "real.posting.client.render_response", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.render_response", clause="ensures:2", phase="ensures", span={"end_byte":11361,"end_column":47,"end_line":209,"start_byte":11319,"start_column":5,"start_line":209}, expected="true", actual="false")
    if not (_cott_contract_condition((("\n\n" in _result)), "real.posting.client.render_response", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.render_response", clause="ensures:3", phase="ensures", span={"end_byte":11400,"end_column":39,"end_line":210,"start_byte":11366,"start_column":5,"start_line":210}, expected="true", actual="false")
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
        _expected_error_span = {"end_byte":12176,"end_column":84,"end_line":227,"start_byte":12097,"start_column":5,"start_line":227}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/execute.py", "35612983578e67cdc37635fc49f6c650b7440e00279e3882b7ea25d0befd2af2", "execute", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.execute")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.execute"
        if _error.span is None:
            _error.span = {"end_byte":12276,"end_column":1,"end_line":233,"start_byte":11418,"start_column":1,"start_line":214}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.execute", phase="implementation-call", span={"end_byte":12276,"end_column":1,"end_line":233,"start_byte":11418,"start_column":1,"start_line":214}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.execute", phase="implementation-call", span={"end_byte":12276,"end_column":1,"end_line":233,"start_byte":11418,"start_column":1,"start_line":214}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidRequest, PostingError_NetworkFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.execute", phase="error", span={"end_byte":12276,"end_column":1,"end_line":233,"start_byte":11418,"start_column":1,"start_line":214}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
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
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.execute", clause="ensures:1", phase="ensures", span={"end_byte":12091,"end_column":62,"end_line":225,"start_byte":12034,"start_column":5,"start_line":225}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["Header", "HttpMethod", "HttpMethod_Custom", "HttpMethod_Delete", "HttpMethod_Get", "HttpMethod_Head", "HttpMethod_Options", "HttpMethod_Patch", "HttpMethod_Post", "HttpMethod_Put", "MAX_RESPONSE_BODY_BYTES", "PostingError", "PostingError_InvalidArguments", "PostingError_InvalidRequest", "PostingError_NetworkFailed", "Request", "Response", "execute", "parse_arguments", "parse_method", "render_response", "send_request"]
