import http.client
import urllib.parse
from typing import Final

from cott_runtime import CottList, Err, Ok, Result
from real.posting.client_types import Header, HttpMethod, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, PostingError, PostingError_InvalidRequest, PostingError_NetworkFailed, Request, Response

_TOKEN_CHARS: Final[str] = "!#$%&'*+-.^_`|~0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_MAX_REDIRECTS: Final[int] = 10


def _is_token(value: str) -> bool:
    return value != "" and all(c in _TOKEN_CHARS for c in value)


def _method_name(method: HttpMethod) -> str:
    if isinstance(method, HttpMethod_Get):
        return "GET"
    if isinstance(method, HttpMethod_Head):
        return "HEAD"
    if isinstance(method, HttpMethod_Post):
        return "POST"
    if isinstance(method, HttpMethod_Put):
        return "PUT"
    if isinstance(method, HttpMethod_Patch):
        return "PATCH"
    if isinstance(method, HttpMethod_Delete):
        return "DELETE"
    if isinstance(method, HttpMethod_Options):
        return "OPTIONS"
    return method.name


def _valid_url(url: str) -> bool:
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    try:
        parts = urllib.parse.urlsplit(url)
        host = parts.hostname
        parts.port
    except ValueError:
        return False
    return bool(host)


def _exchange(request: Request, method: str, url: str, data: bytes | None) -> tuple[int, list[tuple[str, str]], bytes]:
    parts = urllib.parse.urlsplit(url)
    host = parts.hostname or ""
    timeout = request.timeout_ms / 1000
    conn: http.client.HTTPConnection
    if parts.scheme == "https":
        conn = http.client.HTTPSConnection(host, parts.port, timeout=timeout)
    else:
        conn = http.client.HTTPConnection(host, parts.port, timeout=timeout)
    try:
        target = parts.path or "/"
        if parts.query:
            target = f"{target}?{parts.query}"
        names = {header.name.lower() for header in request.headers}
        conn.putrequest(method, target, skip_host="host" in names, skip_accept_encoding=True)
        for header in request.headers:
            conn.putheader(header.name, header.value)
        if data is not None and "content-length" not in names and "transfer-encoding" not in names:
            conn.putheader("Content-Length", str(len(data)))
        conn.endheaders(data)
        resp = conn.getresponse()
        body = resp.read()
        return resp.status, resp.getheaders(), body
    finally:
        conn.close()


def send_request(request: Request) -> Result[Response, PostingError]:
    if request.timeout_ms == 0:
        return Err(error=PostingError_InvalidRequest(message="timeout_ms must be positive"))
    if not _valid_url(request.url):
        return Err(error=PostingError_InvalidRequest(message=f"invalid URL: {request.url!r}"))
    for header in request.headers:
        if not _is_token(header.name):
            return Err(error=PostingError_InvalidRequest(message=f"invalid header name: {header.name!r}"))
        if "\r" in header.value or "\n" in header.value:
            return Err(error=PostingError_InvalidRequest(message=f"invalid header value for {header.name!r}"))
    method = _method_name(request.method)
    if not _is_token(method):
        return Err(error=PostingError_InvalidRequest(message=f"invalid HTTP method: {method!r}"))
    data = request.body.encode("utf-8") if request.body else None
    follow = isinstance(request.method, (HttpMethod_Get, HttpMethod_Head))
    url = request.url
    redirects = 0
    while True:
        try:
            status, headers, body = _exchange(request, method, url, data)
        except (OSError, http.client.HTTPException, ValueError) as exc:
            return Err(error=PostingError_NetworkFailed(message=f"network failure: {exc!r}"))
        if not 100 <= status <= 599:
            return Err(error=PostingError_NetworkFailed(message=f"invalid HTTP status: {status}"))
        location = next((value for name, value in headers if name.lower() == "location"), None)
        if follow and status in (301, 302, 303, 307, 308) and location is not None and redirects < _MAX_REDIRECTS:
            next_url = urllib.parse.urljoin(url, location)
            if _valid_url(next_url):
                url = next_url
                redirects += 1
                continue
        return Ok(value=Response(status=status, url=url, headers=CottList(values=[Header(name=name, value=value) for name, value in headers]), body=body.decode("utf-8", errors="replace")))
