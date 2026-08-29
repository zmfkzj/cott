from typing import Final
from urllib.request import HTTPHandler, HTTPSHandler, OpenerDirector, Request

from cott_runtime import Err, Ok, Result
from frogmouth.document_types import (
    LoadError,
    LoadError_HttpFailure,
    LoadError_InvalidEncoding,
    LoadError_InvalidLocation,
    LoadError_NotFound,
    LoadError_PermissionDenied,
    LoadError_TooLarge,
)

_HTTP_TIMEOUT_SECONDS: Final[float] = 30.0
_MAX_MARKDOWN_BYTES: Final[int] = 5242880
_USER_AGENT: Final[str] = "Frogmouth"


def _validated_http_scheme(url: str) -> str:
    separator = url.find("://")
    if separator < 0:
        return ""
    scheme = url[:separator].lower()
    if scheme != "http" and scheme != "https":
        return ""

    authority_start = separator + 3
    authority_end = len(url)
    for delimiter in "/?#":
        position = url.find(delimiter, authority_start)
        if position >= 0 and position < authority_end:
            authority_end = position
    authority = url[authority_start:authority_end]
    if not authority:
        return ""

    for character in url:
        codepoint = ord(character)
        if codepoint <= 32 or codepoint >= 127:
            return ""

    host_port = authority.rsplit("@", 1)[-1]
    if not host_port:
        return ""

    port = ""
    if host_port.startswith("["):
        closing_bracket = host_port.find("]")
        if closing_bracket <= 1 or host_port.find("[", 1) >= 0 or host_port.find("]", closing_bracket + 1) >= 0:
            return ""
        host = host_port[1:closing_bracket]
        suffix = host_port[closing_bracket + 1:]
        if suffix:
            if not suffix.startswith(":"):
                return ""
            port = suffix[1:]
            if not port:
                return ""
        for character in host:
            if character not in "0123456789abcdefABCDEF:.%abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_":
                return ""
    else:
        if "[" in host_port or "]" in host_port or host_port.count(":") > 1:
            return ""
        if ":" in host_port:
            host, port = host_port.rsplit(":", 1)
            if not port:
                return ""
        else:
            host = host_port
        if not host:
            return ""
        for character in host:
            if not character.isalnum() and character != "." and character != "-":
                return ""

    if port:
        for character in port:
            if character < "0" or character > "9":
                return ""
        significant_port = port.lstrip("0")
        if len(significant_port) > 5 or (len(significant_port) == 5 and significant_port > "65535"):
            return ""
    return scheme


def load_http_markdown(url: str) -> Result[str, LoadError]:
    if not url:
        return Err(error=LoadError_InvalidLocation(message="HTTP URL must not be empty"))

    scheme = _validated_http_scheme(url)
    if not scheme:
        return Err(error=LoadError_InvalidLocation(message="location must be an absolute HTTP or HTTPS URL"))

    request = Request(url=url, headers={"Accept": "text/markdown, text/plain", "User-Agent": _USER_AGENT})
    opener = OpenerDirector()
    if scheme == "https":
        opener.add_handler(HTTPSHandler())
    else:
        opener.add_handler(HTTPHandler())

    response = opener.open(request, timeout=_HTTP_TIMEOUT_SECONDS)
    status = response.status
    if status == 404:
        response.close()
        return Err(error=LoadError_NotFound(source=url))
    if status == 401 or status == 403:
        response.close()
        return Err(error=LoadError_PermissionDenied(source=url))
    if status < 200 or status >= 300:
        response.close()
        return Err(error=LoadError_HttpFailure(url=url, status=status))

    body = response.read(_MAX_MARKDOWN_BYTES + 1)
    response.close()

    if len(body) > _MAX_MARKDOWN_BYTES:
        return Err(error=LoadError_TooLarge(source=url))

    markdown = body.decode("utf-8", errors="surrogateescape")
    for character in markdown:
        if 0xDC80 <= ord(character) <= 0xDCFF:
            return Err(error=LoadError_InvalidEncoding(source=url))
    return Ok(value=markdown)
