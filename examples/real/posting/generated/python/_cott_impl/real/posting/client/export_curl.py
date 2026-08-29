import shlex

from cott_runtime import Err, Ok, Result
from real.posting.client import normalize_json_content, resolve_request
from real.posting.client_types import Header, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, PostingError, PostingError_InvalidHeader, RequestDocument


def _render_curl(request: RequestDocument) -> Result[str, PostingError]:
    method: str = "GET"
    match request.method:
        case HttpMethod_Get():
            method = "GET"
        case HttpMethod_Post():
            method = "POST"
        case HttpMethod_Put():
            method = "PUT"
        case HttpMethod_Patch():
            method = "PATCH"
        case HttpMethod_Delete():
            method = "DELETE"
        case HttpMethod_Head():
            method = "HEAD"
        case HttpMethod_Options():
            method = "OPTIONS"

    headers: list[Header] = list(request.headers)
    parts: list[str] = ["curl", "-X", method, shlex.quote(request.url)]
    for header in headers:
        if header.name == "":
            return Err(error=PostingError_InvalidHeader(message="header name must not be empty"))
        if not all(character in "!#$%&'*+-.^_`|~0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" for character in header.name):
            return Err(error=PostingError_InvalidHeader(message="invalid header name: " + header.name))
        if any((ord(character) < 32 and character != "\t") or ord(character) == 127 for character in header.value):
            return Err(error=PostingError_InvalidHeader(message="header value contains invalid control characters"))
        parts.extend(("-H", shlex.quote(header.name + ": " + header.value)))

    if request.body != "":
        parts.extend(("--data-raw", shlex.quote(request.body)))
    return Ok(value=" ".join(parts))


def export_curl(request: RequestDocument, variables: str) -> Result[str, PostingError]:
    match resolve_request(request, variables):
        case Err(error=error):
            return Err(error=error)
        case Ok(value=resolved):
            match normalize_json_content(resolved):
                case Err(error=error):
                    return Err(error=error)
                case Ok(value=normalized):
                    return _render_curl(normalized)
