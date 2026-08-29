from pathlib import Path
import urllib.error
import urllib.request

from cott_runtime import CottList, Err, Ok, Result, U32
from real.posting.client import normalize_json_content
from real.posting.client_types import Header, HttpMethod, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, HttpResponse, PostingError, PostingError_InvalidHeader, PostingError_InvalidRequest, PostingError_NetworkFailed, PostingError_TimedOut, RequestDocument


def _method_text(method: HttpMethod) -> str:
    match method:
        case HttpMethod_Get():
            return "GET"
        case HttpMethod_Post():
            return "POST"
        case HttpMethod_Put():
            return "PUT"
        case HttpMethod_Patch():
            return "PATCH"
        case HttpMethod_Delete():
            return "DELETE"
        case HttpMethod_Head():
            return "HEAD"
        case HttpMethod_Options():
            return "OPTIONS"
    return ""


def _valid_http_url(url: str) -> bool:
    lowered: str = url.lower()
    prefix_length: int
    if lowered.startswith("http://"):
        prefix_length = 7
    elif lowered.startswith("https://"):
        prefix_length = 8
    else:
        return False
    authority_end: int = len(url)
    separator: str
    for separator in "/?#":
        position: int = url.find(separator, prefix_length)
        if position >= 0 and position < authority_end:
            authority_end = position
    if authority_end == prefix_length:
        return False
    character: str
    for character in url:
        codepoint: int = ord(character)
        if codepoint <= 32 or codepoint == 127 or 55296 <= codepoint <= 57343:
            return False
    return True


def _invalid_header(headers: CottList[Header]) -> str:
    header: Header
    character: str
    for header in headers:
        if header.name == "":
            return "header name must not be empty"
        for character in header.name:
            if character not in "!#$%&'*+-.^_`|~0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
                return "invalid header name: " + header.name
        for character in header.value:
            if (ord(character) < 32 and character != "\t") or ord(character) == 127:
                return "header value contains invalid control characters"
    return ""


def _is_timeout_message(message: str) -> bool:
    lowered: str = message.lower()
    return "timed out" in lowered or "timeout" in lowered


def _http_error_response(failure: urllib.error.HTTPError, timeout_ms: U32) -> Result[HttpResponse, PostingError]:
    headers: list[Header] = []
    header_name: str
    header_value: str
    for header_name, header_value in failure.headers.items():
        headers.append(Header(name=header_name, value=header_value))
    try:
        with failure:
            body: bytes = failure.read()
    except TimeoutError:
        return Err(error=PostingError_TimedOut(timeout_ms=timeout_ms))
    except OSError as read_failure:
        return Err(error=PostingError_NetworkFailed(message=str(read_failure)))
    response_headers: CottList[Header] = CottList(values=tuple(headers))
    return Ok(value=HttpResponse(status=failure.code, headers=response_headers, body=body))


def send_request(request: RequestDocument, timeout_ms: U32) -> Result[HttpResponse, PostingError]:
    match normalize_json_content(request):
        case Err(error=error):
            return Err(error=error)
        case Ok(value=normalized):
            method: str = _method_text(normalized.method)
            if method == "":
                return Err(error=PostingError_InvalidRequest(path=Path("."), message="unsupported HTTP method"))
            if not _valid_http_url(normalized.url):
                return Err(error=PostingError_InvalidRequest(path=Path("."), message="URL must use HTTP or HTTPS and include a host"))
            header_message: str = _invalid_header(normalized.headers)
            if header_message != "":
                return Err(error=PostingError_InvalidHeader(message=header_message))
            if timeout_ms == 0:
                return Err(error=PostingError_TimedOut(timeout_ms=timeout_ms))

            try:
                data: bytes | None = normalized.body.encode("utf-8") if normalized.body != "" else None
                http_request: urllib.request.Request = urllib.request.Request(normalized.url, data=data, method=method)
                header: Header
                for header in normalized.headers:
                    http_request.add_header(header.name, header.value)
                with urllib.request.urlopen(http_request, timeout=timeout_ms / 1000.0) as response:
                    headers: list[Header] = []
                    header_name: str
                    header_value: str
                    for header_name, header_value in response.headers.items():
                        headers.append(Header(name=header_name, value=header_value))
                    body: bytes = response.read()
                    response_headers: CottList[Header] = CottList(values=tuple(headers))
                    return Ok(value=HttpResponse(status=response.status, headers=response_headers, body=body))
            except urllib.error.HTTPError as failure:
                return _http_error_response(failure, timeout_ms)
            except TimeoutError:
                return Err(error=PostingError_TimedOut(timeout_ms=timeout_ms))
            except urllib.error.URLError as failure:
                message: str = str(failure.reason)
                if _is_timeout_message(message):
                    return Err(error=PostingError_TimedOut(timeout_ms=timeout_ms))
                return Err(error=PostingError_NetworkFailed(message=message))
            except ValueError as failure:
                return Err(error=PostingError_InvalidRequest(path=Path("."), message=str(failure)))
            except OSError as failure:
                return Err(error=PostingError_NetworkFailed(message=str(failure)))
