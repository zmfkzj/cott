import os

from cott_runtime import CottList, Err, Ok, Result
from real.posting.client import extract_url_variables
from real.posting.client_types import PostingError, PostingError_InvalidHeader, PostingError_UnresolvedVariable, RequestDocument


def _is_variable_name(value: str) -> bool:
    if value == "":
        return False
    first: str = value[0]
    if not ("A" <= first <= "Z" or "a" <= first <= "z" or first == "_"):
        return False
    for character in value[1:]:
        if not ("A" <= character <= "Z" or "a" <= character <= "z" or "0" <= character <= "9" or character == "_"):
            return False
    return True


def _parse_variable_lines(source: str) -> tuple[bool, dict[str, str], str]:
    values: dict[str, str] = {}
    lines: list[str] = source.split("\n")
    for raw_line in lines:
        line: str = raw_line[:-1] if raw_line.endswith("\r") else raw_line
        if line.strip(" \t") == "":
            continue
        separator: int = line.find("=")
        if separator <= 0:
            return (False, values, "variable line must contain a non-empty name followed by '='")
        name: str = line[:separator]
        if not _is_variable_name(name):
            return (False, values, "invalid variable name: " + name)
        values[name] = line[separator + 1 :]
    return (True, values, "")


def _substitute_url(url: str, values: dict[str, str]) -> str:
    pieces: list[str] = []
    index: int = 0
    length: int = len(url)
    while index < length:
        if url[index] != ":":
            pieces.append(url[index])
            index += 1
            continue
        if index + 1 < length and url[index + 1] == ":":
            pieces.append(":")
            index += 2
            continue
        start: int = index + 1
        if start >= length or not ("A" <= url[start] <= "Z" or "a" <= url[start] <= "z" or url[start] == "_"):
            pieces.append(":")
            index += 1
            continue
        end: int = start + 1
        while end < length and ("A" <= url[end] <= "Z" or "a" <= url[end] <= "z" or "0" <= url[end] <= "9" or url[end] == "_"):
            end += 1
        pieces.append(values[url[start:end]])
        index = end
    return "".join(pieces)


def resolve_request(request: RequestDocument, variables: str) -> Result[RequestDocument, PostingError]:
    valid: bool
    values: dict[str, str]
    message: str
    valid, values, message = _parse_variable_lines(variables)
    if not valid:
        return Err(error=PostingError_InvalidHeader(message=message))

    names: CottList[str] = extract_url_variables(request.url)
    for name in names:
        environment_value: str | None = os.environ.get(name)
        if environment_value is not None:
            values[name] = environment_value
        elif name not in values:
            return Err(error=PostingError_UnresolvedVariable(name=name))

    resolved_url: str = _substitute_url(request.url, values)
    resolved: RequestDocument = RequestDocument(
        name=request.name,
        method=request.method,
        url=resolved_url,
        headers=request.headers,
        body=request.body,
        json_body=request.json_body,
    )
    return Ok(value=resolved)
