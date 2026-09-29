from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.posting.client_types import Header as Header, HttpMethod as HttpMethod, HttpMethod_Custom as HttpMethod_Custom, HttpMethod_Delete as HttpMethod_Delete, HttpMethod_Get as HttpMethod_Get, HttpMethod_Head as HttpMethod_Head, HttpMethod_Options as HttpMethod_Options, HttpMethod_Patch as HttpMethod_Patch, HttpMethod_Post as HttpMethod_Post, HttpMethod_Put as HttpMethod_Put, MAX_RESPONSE_BODY_BYTES as MAX_RESPONSE_BODY_BYTES, PostingError as PostingError, PostingError_InvalidArguments as PostingError_InvalidArguments, PostingError_InvalidRequest as PostingError_InvalidRequest, PostingError_NetworkFailed as PostingError_NetworkFailed, Request as Request, Response as Response
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

The URL consists only of RFC 3986 characters: ASCII letters, digits and
- . _ ~ : / ? # [ ] @ ! $ & ' ( ) * + , ; =, plus "%" always followed by two
hexadecimal digits. Any other character (space, control character, non-ASCII
character, < > " { } | backslash ^ or the grave accent) and any "%" not
followed by two hexadecimal digits make the request InvalidRequest.

The request target is the URL path ("/" when the path is empty), followed by
"?" and the query when the URL contains a "?" before any "#" (even when the
query is empty). The fragment is never sent. Percent-encoded octets are sent
exactly as written, neither decoded nor re-encoded. Unless request.headers has
a header named Host (ASCII case-insensitive), a Host header is sent whose
value is the URL host exactly as written (ASCII case kept, an IPv6 literal
with its brackets, no userinfo), followed by ":" and the port only when the
URL gives a port other than the scheme default (80 for http, 443 for https).
URL userinfo is neither sent nor used for authentication, and Response.url
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
or has no host, is not followed and that 3xx response is returned.

A redirect is followed only when it does not leave https for http; a 3xx
response whose Location is an http:// URL while the current URL is https:// is
not followed and is returned as the result. When a followed redirect changes
the origin compared with the previous URL (scheme and host compared ASCII
case-insensitively, port compared after applying the scheme default), the request
headers named Authorization, Cookie, Proxy-Authorization and Host (ASCII
case-insensitive name comparison) are not sent to the new origin; all other
request headers are still sent. A redirect within the same origin keeps every
header. The Host header of every request, including one sent after a followed
redirect, follows the Host rule above for the URL being requested, so a Host
header removed by the credential rule is replaced by the URL's own host.

The Response holds the final status, the final URL (request.url when no
redirect was followed), the received headers in received order with
duplicates kept, and the body decoded as UTF-8 with each maximal subpart of
an ill-formed sequence (Unicode section 3.9, Table 3-8) replaced by one
U+FFFD, so the bytes ED A0 80 become three U+FFFD; a leading byte order mark
is kept as U+FEFF and NUL is kept; a Content-Type charset is ignored. A received
status of 400 or above is still a successful Response, never an error.

The received body is limited to MAX_RESPONSE_BODY_BYTES (67108864) bytes,
counted before decoding; a body of more bytes is NetworkFailed and no partial
Response is returned.

InvalidRequest: timeout_ms is 0; the URL does not start with the lower-case
"http://" or "https://", has no host or has a character outside the URL
characters above; a header name is blank or not an
HTTP token (as defined by real.posting.client.parse_method); a header value
contains CR or LF; or the method is a Custom name that is not an HTTP token.
No connection is attempted for an InvalidRequest. NetworkFailed: name
resolution, connection, timeout, a connection closed before the empty line
that ends the header block, before all Content-Length bytes, or before the
terminating chunk of a chunked body, a response that does not start with an
HTTP/1.x status line, a header line without a colon, a response body larger
than MAX_RESPONSE_BODY_BYTES, or a final status outside 100-599. No partial
Response is returned. When the response has neither a Content-Length nor
chunked transfer coding, the body extends to the connection close."""
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

__all__ = ["Header", "HttpMethod", "HttpMethod_Custom", "HttpMethod_Delete", "HttpMethod_Get", "HttpMethod_Head", "HttpMethod_Options", "HttpMethod_Patch", "HttpMethod_Post", "HttpMethod_Put", "MAX_RESPONSE_BODY_BYTES", "PostingError", "PostingError_InvalidArguments", "PostingError_InvalidRequest", "PostingError_NetworkFailed", "Request", "Response", "execute", "parse_arguments", "parse_method", "render_response", "send_request"]
