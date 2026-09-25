from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.posting.client_types import Header as Header, HttpMethod as HttpMethod, HttpMethod_Custom as HttpMethod_Custom, HttpMethod_Delete as HttpMethod_Delete, HttpMethod_Get as HttpMethod_Get, HttpMethod_Head as HttpMethod_Head, HttpMethod_Options as HttpMethod_Options, HttpMethod_Patch as HttpMethod_Patch, HttpMethod_Post as HttpMethod_Post, HttpMethod_Put as HttpMethod_Put, PostingError as PostingError, PostingError_InvalidArguments as PostingError_InvalidArguments, PostingError_InvalidRequest as PostingError_InvalidRequest, PostingError_NetworkFailed as PostingError_NetworkFailed, Request as Request, Response as Response
"""Parse an HTTP method name. A source equal to GET, HEAD, POST, PUT, PATCH,
DELETE or OPTIONS under ASCII case-insensitive comparison is that standard
variant. Any other HTTP token is HttpMethod.Custom with the source unchanged
(no case mapping). An HTTP token is one or more of the ASCII characters A-Z,
a-z, 0-9 and ! # $ % & ' * + - . ^ _ ` | ~. Every other source, including the
empty string, is InvalidRequest."""
def parse_method(source: str) -> Result[HttpMethod, PostingError]: ...

"""Parse the command line METHOD URL [BODY]. The method is
real.posting.client.parse_method of METHOD, and its error is returned
unchanged. URL and BODY are copied verbatim; the URL is not validated here
(real.posting.client.send_request validates it). A missing BODY is the empty
string. The request has no headers and a 30000 millisecond timeout."""
def parse_arguments(arguments: CottList[str]) -> Result[Request, PostingError]: ...

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
def send_request(request: Request) -> Result[Response, PostingError]: ...

"""Render a response as LF-separated lines: first the decimal status, one space
and the URL; then one "NAME: VALUE" line per header in order; then one empty
line; then the body unchanged. There is no trailing LF after the body."""
def render_response(response: Response) -> str: ...

"""The posting composition root. Call real.posting.client.parse_arguments with
arguments, pass its Request to real.posting.client.send_request, and return
real.posting.client.render_response of the received Response. An error from
parse_arguments is returned unchanged and no request is sent; an error from
send_request is returned unchanged and nothing is rendered."""
def execute(arguments: CottList[str]) -> Result[str, PostingError]: ...

__all__ = ["Header", "HttpMethod", "HttpMethod_Custom", "HttpMethod_Delete", "HttpMethod_Get", "HttpMethod_Head", "HttpMethod_Options", "HttpMethod_Patch", "HttpMethod_Post", "HttpMethod_Put", "PostingError", "PostingError_InvalidArguments", "PostingError_InvalidRequest", "PostingError_NetworkFailed", "Request", "Response", "execute", "parse_arguments", "parse_method", "render_response", "send_request"]
