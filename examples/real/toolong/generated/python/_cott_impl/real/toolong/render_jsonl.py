import json

from cott_runtime import CottList, Err, Ok, Result, U8
from real.toolong_types import LogEntry, ToolongError, ToolongError_InvalidIndent


def _skip_json_whitespace(text: str, index: int) -> int:
    size = len(text)
    while index < size and text[index] in " \t\r\n":
        index += 1
    return index


def _hex_value(character: str) -> int:
    if "0" <= character <= "9":
        return ord(character) - ord("0")
    if "a" <= character <= "f":
        return ord(character) - ord("a") + 10
    if "A" <= character <= "F":
        return ord(character) - ord("A") + 10
    return -1


def _json_string_end(text: str, index: int) -> int:
    size = len(text)
    if index >= size or text[index] != '"':
        return -1
    index += 1
    while index < size:
        character = text[index]
        if character == '"':
            return index + 1
        if ord(character) < 0x20:
            return -1
        if character != "\\":
            index += 1
            continue
        index += 1
        if index >= size:
            return -1
        escape = text[index]
        if escape in '"\\/bfnrt':
            index += 1
            continue
        if escape != "u" or index + 4 >= size:
            return -1
        offset = 1
        while offset <= 4:
            if _hex_value(text[index + offset]) < 0:
                return -1
            offset += 1
        index += 5
    return -1


def _json_number_end(text: str, index: int) -> int:
    size = len(text)
    if index < size and text[index] == "-":
        index += 1
    if index >= size:
        return -1
    if text[index] == "0":
        index += 1
        if index < size and "0" <= text[index] <= "9":
            return -1
    elif "1" <= text[index] <= "9":
        index += 1
        while index < size and "0" <= text[index] <= "9":
            index += 1
    else:
        return -1
    if index < size and text[index] == ".":
        index += 1
        if index >= size or not "0" <= text[index] <= "9":
            return -1
        while index < size and "0" <= text[index] <= "9":
            index += 1
    if index < size and text[index] in "eE":
        index += 1
        if index < size and text[index] in "+-":
            index += 1
        if index >= size or not "0" <= text[index] <= "9":
            return -1
        while index < size and "0" <= text[index] <= "9":
            index += 1
    return index


def _json_value_end(text: str, index: int) -> int:
    index = _skip_json_whitespace(text, index)
    size = len(text)
    if index >= size:
        return -1
    character = text[index]
    if character == '"':
        return _json_string_end(text, index)
    if character == "{":
        index = _skip_json_whitespace(text, index + 1)
        if index < size and text[index] == "}":
            return index + 1
        while index < size:
            index = _json_string_end(text, index)
            if index < 0:
                return -1
            index = _skip_json_whitespace(text, index)
            if index >= size or text[index] != ":":
                return -1
            index = _json_value_end(text, index + 1)
            if index < 0:
                return -1
            index = _skip_json_whitespace(text, index)
            if index < size and text[index] == "}":
                return index + 1
            if index >= size or text[index] != ",":
                return -1
            index = _skip_json_whitespace(text, index + 1)
        return -1
    if character == "[":
        index = _skip_json_whitespace(text, index + 1)
        if index < size and text[index] == "]":
            return index + 1
        while index < size:
            index = _json_value_end(text, index)
            if index < 0:
                return -1
            index = _skip_json_whitespace(text, index)
            if index < size and text[index] == "]":
                return index + 1
            if index >= size or text[index] != ",":
                return -1
            index = _skip_json_whitespace(text, index + 1)
        return -1
    if text.startswith("true", index):
        return index + 4
    if text.startswith("false", index):
        return index + 5
    if text.startswith("null", index):
        return index + 4
    return _json_number_end(text, index)


def _valid_json(text: str) -> bool:
    end = _json_value_end(text, 0)
    return end >= 0 and _skip_json_whitespace(text, end) == len(text)


def render_jsonl(entries: CottList[LogEntry], indent: U8) -> Result[CottList[str], ToolongError]:
    if indent == 0:
        return Err(error=ToolongError_InvalidIndent())
    lines: list[str] = []
    for entry in entries:
        if _valid_json(entry.text):
            lines.append(json.dumps(json.loads(entry.text), ensure_ascii=False, sort_keys=True, indent=indent))
        else:
            lines.append(entry.text)
    return Ok(value=CottList(values=tuple(lines)))
