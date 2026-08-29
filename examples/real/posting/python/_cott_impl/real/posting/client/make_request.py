from pathlib import Path

from cott_runtime import CottList, Err, Ok, Result
from real.posting.client_types import Header, HttpMethod, PostingError, PostingError_InvalidHeader, PostingError_InvalidRequest, RequestDocument


def make_request(name: str, method: HttpMethod, url: str, header_lines: str, body: str, json_body: bool) -> Result[RequestDocument, PostingError]:
    if name == "":
        return Err(error=PostingError_InvalidRequest(path=Path("."), message="name must not be empty"))
    if url == "":
        return Err(error=PostingError_InvalidRequest(path=Path("."), message="url must not be empty"))

    headers: list[Header] = []
    lines: list[str] = header_lines.split("\n")
    for raw_line in lines:
        line: str = raw_line[:-1] if raw_line.endswith("\r") else raw_line
        if line.strip(" \t") == "":
            continue
        separator: int = line.find(":")
        if separator <= 0:
            return Err(error=PostingError_InvalidHeader(message="header line must contain a non-empty name followed by ':'"))
        header_name: str = line[:separator].strip(" \t")
        header_value: str = line[separator + 1 :].strip(" \t")
        if header_name == "":
            return Err(error=PostingError_InvalidHeader(message="header name must not be empty"))
        if not all(character in "!#$%&'*+-.^_`|~0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" for character in header_name):
            return Err(error=PostingError_InvalidHeader(message="invalid header name: " + header_name))
        if any((ord(character) < 32 and character != "\t") or ord(character) == 127 for character in header_value):
            return Err(error=PostingError_InvalidHeader(message="header value contains invalid control characters"))
        headers.append(Header(name=header_name, value=header_value))

    request_headers: CottList[Header] = CottList(values=tuple(headers))
    return Ok(value=RequestDocument(name=name, method=method, url=url, headers=request_headers, body=body, json_body=json_body))
