from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Get:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Head:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Post:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Put:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Patch:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Delete:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Options:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Custom:
    __hash__ = None
    name: str

HttpMethod: TypeAlias = Union[HttpMethod_Get, HttpMethod_Head, HttpMethod_Post, HttpMethod_Put, HttpMethod_Patch, HttpMethod_Delete, HttpMethod_Options, HttpMethod_Custom]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Header:
    __hash__ = None
    name: str
    value: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Request:
    __hash__ = None
    method: HttpMethod
    url: str
    headers: CottList[Header]
    body: str
    timeout_ms: U32

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "method", _cott_validate_abi(self.method, HttpMethod, path="$.method"))
        if not _cott_validated_construction():
            object.__setattr__(self, "url", _cott_validate_abi(self.url, str, path="$.url"))
        if not _cott_validated_construction():
            object.__setattr__(self, "headers", _cott_validate_abi(self.headers, CottList[Header], path="$.headers"))
        if not _cott_validated_construction():
            object.__setattr__(self, "body", _cott_validate_abi(self.body, str, path="$.body"))
        if not _cott_validated_construction():
            object.__setattr__(self, "timeout_ms", _cott_validate_abi(self.timeout_ms, U32, path="$.timeout_ms"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Response:
    __hash__ = None
    status: U16
    url: str
    headers: CottList[Header]
    body: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "status", _cott_validate_abi(self.status, U16, path="$.status"))
        if not _cott_validated_construction():
            object.__setattr__(self, "url", _cott_validate_abi(self.url, str, path="$.url"))
        if not _cott_validated_construction():
            object.__setattr__(self, "headers", _cott_validate_abi(self.headers, CottList[Header], path="$.headers"))
        if not _cott_validated_construction():
            object.__setattr__(self, "body", _cott_validate_abi(self.body, str, path="$.body"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_InvalidArguments:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_InvalidRequest:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_NetworkFailed:
    __hash__ = None
    message: str

PostingError: TypeAlias = Union[PostingError_InvalidArguments, PostingError_InvalidRequest, PostingError_NetworkFailed]

"""Parse an HTTP method name. A source equal to GET, HEAD, POST, PUT, PATCH,
DELETE or OPTIONS under ASCII case-insensitive comparison is that standard
variant. Any other HTTP token is HttpMethod.Custom with the source unchanged
(no case mapping). An HTTP token is one or more of the ASCII characters A-Z,
a-z, 0-9 and ! # $ % & ' * + - . ^ _ ` | ~. Every other source, including the
empty string, is InvalidRequest."""
"""Parse the command line METHOD URL [BODY]. The method is
real.posting.client.parse_method of METHOD, and its error is returned
unchanged. URL and BODY are copied verbatim; the URL is not validated here
(real.posting.client.send_request validates it). A missing BODY is the empty
string. The request has no headers and a 30000 millisecond timeout."""
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
"""Render a response as LF-separated lines: first the decimal status, one space
and the URL; then one "NAME: VALUE" line per header in order; then one empty
line; then the body unchanged. There is no trailing LF after the body."""
"""The posting composition root. Call real.posting.client.parse_arguments with
arguments, pass its Request to real.posting.client.send_request, and return
real.posting.client.render_response of the received Response. An error from
parse_arguments is returned unchanged and no request is sent; an error from
send_request is returned unchanged and nothing is rendered."""
__all__ = ["Header", "HttpMethod", "HttpMethod_Custom", "HttpMethod_Delete", "HttpMethod_Get", "HttpMethod_Head", "HttpMethod_Options", "HttpMethod_Patch", "HttpMethod_Post", "HttpMethod_Put", "PostingError", "PostingError_InvalidArguments", "PostingError_InvalidRequest", "PostingError_NetworkFailed", "Request", "Response"]
