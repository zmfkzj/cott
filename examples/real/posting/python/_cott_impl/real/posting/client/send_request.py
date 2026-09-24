import http.client
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable
from typing import Final

from cott_runtime import CottList, Err, Ok, Result
from real.posting.client_types import Header, HttpMethod, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, PostingError, PostingError_InvalidRequest, PostingError_NetworkFailed, Request, Response

_TOKEN_CHARS: Final[str] = "!#$%&'*+-.^_`|~0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


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


def _build_response(status: int, url: str, headers: Iterable[tuple[str, str]], body: bytes) -> Result[Response, PostingError]:
    if status <= 0:
        return Err(error=PostingError_NetworkFailed(message=f"invalid HTTP status: {status}"))
    return Ok(value=Response(status=status, url=url, headers=CottList(values=[Header(name=name, value=value) for name, value in headers]), body=body.decode("utf-8", errors="replace")))


def send_request(request: Request) -> Result[Response, PostingError]:
    try:
        scheme = urllib.parse.urlsplit(request.url).scheme.lower()
    except ValueError as exc:
        return Err(error=PostingError_InvalidRequest(message=str(exc)))
    if scheme not in ("http", "https"):
        return Err(error=PostingError_InvalidRequest(message=f"unsupported URL scheme: {request.url!r}"))
    method = _method_name(request.method)
    if not method or any(c not in _TOKEN_CHARS for c in method):
        return Err(error=PostingError_InvalidRequest(message=f"invalid HTTP method: {method!r}"))
    data = request.body.encode("utf-8") if request.body else None
    try:
        req = urllib.request.Request(request.url, data=data, method=method)
        for header in request.headers:
            req.add_header(header.name, header.value)
    except ValueError as exc:
        return Err(error=PostingError_InvalidRequest(message=str(exc)))
    timeout = request.timeout_ms / 1000 if request.timeout_ms > 0 else None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _build_response(resp.status, resp.url, resp.headers.items(), resp.read())
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read()
        except (OSError, http.client.HTTPException):
            body = b""
        finally:
            exc.close()
        return _build_response(exc.code, exc.url or request.url, exc.headers.items(), body)
    except (ValueError, http.client.InvalidURL) as exc:
        return Err(error=PostingError_InvalidRequest(message=str(exc)))
    except urllib.error.URLError as exc:
        return Err(error=PostingError_NetworkFailed(message=str(exc.reason)))
    except TimeoutError as exc:
        return Err(error=PostingError_NetworkFailed(message=f"timeout: {exc}"))
    except (OSError, http.client.HTTPException) as exc:
        return Err(error=PostingError_NetworkFailed(message=str(exc)))
