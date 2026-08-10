from urllib.parse import SplitResult, urlsplit

from cott_runtime import Err, Ok, Result
from curriculum.archive_request_types import ArchiveRequestError, ArchiveRequestError_InvalidUrl


def canonicalize_archive_url(url: str) -> Result[str, ArchiveRequestError]:
    def invalid_url() -> Result[str, ArchiveRequestError]:
        return Err(error=ArchiveRequestError_InvalidUrl())

    def has_valid_percent_escapes(value: str) -> bool:
        index: int = 0
        hexadecimal_digits: str = "0123456789abcdefABCDEF"
        while index < len(value):
            if value[index] == "%":
                if index + 2 >= len(value) or value[index + 1] not in hexadecimal_digits or value[index + 2] not in hexadecimal_digits:
                    return False
                index += 3
            else:
                index += 1
        return True

    if not url or any(ord(character) <= 0x20 or ord(character) == 0x7F or character == "\\" for character in url):
        return invalid_url()
    if not has_valid_percent_escapes(url):
        return invalid_url()

    scheme_end: int = url.find(":")
    if scheme_end <= 0 or not url[scheme_end + 1 :].startswith("//"):
        return invalid_url()

    try:
        parsed: SplitResult = urlsplit(url)
        hostname: str | None = parsed.hostname
        port: int | None = parsed.port
    except ValueError:
        return invalid_url()

    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc or not hostname or port is not None and not 0 <= port <= 65535:
        return invalid_url()

    authority_start: int = scheme_end + 3
    authority_end: int = len(url)
    for delimiter in "/?#":
        delimiter_index: int = url.find(delimiter, authority_start)
        if delimiter_index != -1 and delimiter_index < authority_end:
            authority_end = delimiter_index
    authority: str = url[authority_start:authority_end]
    user_info_end: int = authority.rfind("@")
    if authority.count("@") > 1:
        return invalid_url()
    host_port_start: int = user_info_end + 1
    host_port: str = authority[host_port_start:]
    if not host_port:
        return invalid_url()

    if host_port.startswith("["):
        host_end: int = host_port.find("]") + 1
        if host_end == 0 or (host_port[host_end:] and not host_port[host_end:].startswith(":")):
            return invalid_url()
    else:
        if host_port.count(":") > 1:
            return invalid_url()
        colon_index: int = host_port.rfind(":")
        host_end = len(host_port) if colon_index == -1 else colon_index

    if host_end == 0:
        return invalid_url()
    canonical_authority: str = authority[:host_port_start] + host_port[:host_end].lower() + host_port[host_end:]
    return Ok(value=url[:scheme_end].lower() + "://" + canonical_authority + url[authority_end:])
