import json

from cott_runtime import CottList, Err, Ok, Result
from real.posting.client_types import Header, PostingError, PostingError_InvalidJson, RequestDocument


def _scan_json_string(source: str, index: int) -> tuple[bool, int]:
    length: int = len(source)
    if index >= length or source[index] != '"':
        return (False, index)
    index += 1
    while index < length:
        character: str = source[index]
        codepoint: int = ord(character)
        if character == '"':
            return (True, index + 1)
        if codepoint < 32 or 55296 <= codepoint <= 57343:
            return (False, index)
        if character != "\\":
            index += 1
            continue
        if index + 1 >= length:
            return (False, index)
        escape: str = source[index + 1]
        if escape in '"\\/bfnrt':
            index += 2
            continue
        if escape != "u" or index + 6 > length:
            return (False, index)
        hexadecimal: str = source[index + 2 : index + 6]
        if len(hexadecimal) != 4 or not all(digit in "0123456789abcdefABCDEF" for digit in hexadecimal):
            return (False, index)
        if hexadecimal[0] in "dD" and hexadecimal[1] in "89aAbB":
            if index + 12 > length or source[index + 6 : index + 8] != "\\u":
                return (False, index)
            low_hexadecimal: str = source[index + 8 : index + 12]
            if len(low_hexadecimal) != 4 or not all(digit in "0123456789abcdefABCDEF" for digit in low_hexadecimal):
                return (False, index)
            if low_hexadecimal[0] not in "dD" or low_hexadecimal[1] not in "cCdDeEfF":
                return (False, index)
            index += 12
            continue
        if hexadecimal[0] in "dD" and hexadecimal[1] in "cCdDeEfF":
            return (False, index)
        index += 6
    return (False, index)


def _scan_json_number(source: str, index: int) -> tuple[bool, int]:
    start: int = index
    length: int = len(source)
    if index < length and source[index] == "-":
        index += 1
    if index >= length:
        return (False, index)
    if source[index] == "0":
        index += 1
        if index < length and "0" <= source[index] <= "9":
            return (False, index)
    elif "1" <= source[index] <= "9":
        index += 1
        while index < length and "0" <= source[index] <= "9":
            index += 1
    else:
        return (False, index)
    if index < length and source[index] == ".":
        index += 1
        if index >= length or not "0" <= source[index] <= "9":
            return (False, index)
        while index < length and "0" <= source[index] <= "9":
            index += 1
    if index < length and source[index] in "eE":
        index += 1
        if index < length and source[index] in "+-":
            index += 1
        if index >= length or not "0" <= source[index] <= "9":
            return (False, index)
        while index < length and "0" <= source[index] <= "9":
            index += 1
    if index - start > 1000:
        return (False, index)
    return (True, index)


def _scan_json_value(source: str, index: int, depth: int) -> tuple[bool, int]:
    length: int = len(source)
    while index < length and source[index] in " \t\r\n":
        index += 1
    if index >= length or depth > 200:
        return (False, index)
    character: str = source[index]
    if character == '"':
        return _scan_json_string(source, index)
    if character == "-" or "0" <= character <= "9":
        return _scan_json_number(source, index)
    if source.startswith("true", index):
        return (True, index + 4)
    if source.startswith("false", index):
        return (True, index + 5)
    if source.startswith("null", index):
        return (True, index + 4)
    if character == "[":
        index += 1
        while index < length and source[index] in " \t\r\n":
            index += 1
        if index < length and source[index] == "]":
            return (True, index + 1)
        while True:
            valid: bool
            valid, index = _scan_json_value(source, index, depth + 1)
            if not valid:
                return (False, index)
            while index < length and source[index] in " \t\r\n":
                index += 1
            if index < length and source[index] == "]":
                return (True, index + 1)
            if index >= length or source[index] != ",":
                return (False, index)
            index += 1
    if character == "{":
        index += 1
        while index < length and source[index] in " \t\r\n":
            index += 1
        if index < length and source[index] == "}":
            return (True, index + 1)
        while True:
            valid_key: bool
            valid_key, index = _scan_json_string(source, index)
            if not valid_key:
                return (False, index)
            while index < length and source[index] in " \t\r\n":
                index += 1
            if index >= length or source[index] != ":":
                return (False, index)
            valid_value: bool
            valid_value, index = _scan_json_value(source, index + 1, depth + 1)
            if not valid_value:
                return (False, index)
            while index < length and source[index] in " \t\r\n":
                index += 1
            if index < length and source[index] == "}":
                return (True, index + 1)
            if index >= length or source[index] != ",":
                return (False, index)
            index += 1
            while index < length and source[index] in " \t\r\n":
                index += 1
    return (False, index)


def _is_valid_json(source: str) -> bool:
    valid: bool
    index: int
    valid, index = _scan_json_value(source, 0, 0)
    if not valid:
        return False
    length: int = len(source)
    while index < length and source[index] in " \t\r\n":
        index += 1
    return index == length


def normalize_json_content(request: RequestDocument) -> Result[RequestDocument, PostingError]:
    if not request.json_body:
        return Ok(value=request)
    if not _is_valid_json(request.body):
        return Err(error=PostingError_InvalidJson(message="invalid JSON body"))

    parsed: object = json.loads(request.body)
    normalized_body: str = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
    if not _is_valid_json(normalized_body):
        return Err(error=PostingError_InvalidJson(message="JSON body contains a non-finite number"))

    headers: list[Header] = list(request.headers)
    has_content_type: bool = False
    index: int = 0
    while index < len(headers):
        header: Header = headers[index]
        if header.name.lower() == "content-type":
            has_content_type = True
            break
        index += 1
    if not has_content_type:
        headers.append(Header(name="Content-Type", value="application/json"))

    normalized_headers: CottList[Header] = CottList(values=tuple(headers))
    normalized: RequestDocument = RequestDocument(
        name=request.name,
        method=request.method,
        url=request.url,
        headers=normalized_headers,
        body=normalized_body,
        json_body=request.json_body,
    )
    return Ok(value=normalized)
