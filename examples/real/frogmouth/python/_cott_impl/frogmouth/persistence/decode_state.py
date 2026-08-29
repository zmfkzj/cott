from pathlib import Path

from cott_runtime import CottList, Err, Ok, Result
from frogmouth.model_types import BrowserState
from frogmouth.persistence_types import StateError, StateError_InvalidData


def _skip_json_whitespace(source: str, index: int) -> int:
    length = len(source)
    while index < length and source[index] in " \t\r\n":
        index += 1
    return index


def _hex_digit_value(character: str) -> int:
    if "0" <= character <= "9":
        return ord(character) - ord("0")
    if "a" <= character <= "f":
        return ord(character) - ord("a") + 10
    if "A" <= character <= "F":
        return ord(character) - ord("A") + 10
    return -1


def _parse_hex_quad(source: str, index: int) -> tuple[bool, int, int]:
    if index + 4 > len(source):
        return False, 0, index
    value = 0
    end = index + 4
    while index < end:
        digit = _hex_digit_value(source[index])
        if digit < 0:
            return False, 0, index
        value = value * 16 + digit
        index += 1
    return True, value, index


def _parse_json_string(source: str, index: int) -> tuple[bool, str, int]:
    if index >= len(source) or source[index] != '"':
        return False, "", index

    index += 1
    characters: list[str] = []
    while index < len(source):
        character = source[index]
        if character == '"':
            return True, "".join(characters), index + 1
        if character == "\\":
            index += 1
            if index >= len(source):
                return False, "", index
            escape = source[index]
            if escape == '"' or escape == "\\" or escape == "/":
                characters.append(escape)
                index += 1
                continue
            if escape == "b":
                characters.append("\b")
                index += 1
                continue
            if escape == "f":
                characters.append("\f")
                index += 1
                continue
            if escape == "n":
                characters.append("\n")
                index += 1
                continue
            if escape == "r":
                characters.append("\r")
                index += 1
                continue
            if escape == "t":
                characters.append("\t")
                index += 1
                continue
            if escape != "u":
                return False, "", index

            valid, codepoint, index = _parse_hex_quad(source, index + 1)
            if not valid:
                return False, "", index
            if 0xD800 <= codepoint <= 0xDBFF:
                if index + 2 > len(source) or source[index : index + 2] != "\\u":
                    return False, "", index
                valid, low_surrogate, index = _parse_hex_quad(source, index + 2)
                if not valid or low_surrogate < 0xDC00 or low_surrogate > 0xDFFF:
                    return False, "", index
                codepoint = 0x10000 + (codepoint - 0xD800) * 0x400 + low_surrogate - 0xDC00
            elif 0xDC00 <= codepoint <= 0xDFFF:
                return False, "", index
            characters.append(chr(codepoint))
            continue

        codepoint = ord(character)
        if codepoint < 0x20 or 0xD800 <= codepoint <= 0xDFFF:
            return False, "", index
        characters.append(character)
        index += 1
    return False, "", index


def _parse_string_array(source: str, index: int) -> tuple[bool, list[str], int]:
    index = _skip_json_whitespace(source, index)
    if index >= len(source) or source[index] != "[":
        return False, [], index

    values: list[str] = []
    index = _skip_json_whitespace(source, index + 1)
    if index < len(source) and source[index] == "]":
        return True, values, index + 1

    while index < len(source):
        valid, value, index = _parse_json_string(source, index)
        if not valid:
            return False, [], index
        values.append(value)
        index = _skip_json_whitespace(source, index)
        if index >= len(source):
            return False, [], index
        if source[index] == "]":
            return True, values, index + 1
        if source[index] != ",":
            return False, [], index
        index = _skip_json_whitespace(source, index + 1)
    return False, [], index


def decode_state(source: str, path: Path) -> Result[BrowserState, StateError]:
    index = _skip_json_whitespace(source, 0)
    if index >= len(source) or source[index] != "{":
        return Err(error=StateError_InvalidData(path=path))

    history_values: list[str] = []
    bookmark_values: list[str] = []
    history_seen = False
    bookmarks_seen = False
    index = _skip_json_whitespace(source, index + 1)

    while index < len(source) and source[index] != "}":
        valid, key, index = _parse_json_string(source, index)
        if not valid:
            return Err(error=StateError_InvalidData(path=path))
        index = _skip_json_whitespace(source, index)
        if index >= len(source) or source[index] != ":":
            return Err(error=StateError_InvalidData(path=path))
        index = _skip_json_whitespace(source, index + 1)

        if key == "history" and not history_seen:
            valid, history_values, index = _parse_string_array(source, index)
            history_seen = valid
        elif key == "bookmarks" and not bookmarks_seen:
            valid, bookmark_values, index = _parse_string_array(source, index)
            bookmarks_seen = valid
        else:
            return Err(error=StateError_InvalidData(path=path))
        if not valid:
            return Err(error=StateError_InvalidData(path=path))

        index = _skip_json_whitespace(source, index)
        if index >= len(source):
            return Err(error=StateError_InvalidData(path=path))
        if source[index] == "}":
            break
        if source[index] != ",":
            return Err(error=StateError_InvalidData(path=path))
        index = _skip_json_whitespace(source, index + 1)
        if index >= len(source) or source[index] == "}":
            return Err(error=StateError_InvalidData(path=path))

    if index >= len(source) or source[index] != "}" or not history_seen or not bookmarks_seen:
        return Err(error=StateError_InvalidData(path=path))
    if _skip_json_whitespace(source, index + 1) != len(source):
        return Err(error=StateError_InvalidData(path=path))

    history: CottList[str] = CottList(values=history_values)
    bookmarks: CottList[str] = CottList(values=bookmark_values)
    return Ok(value=BrowserState(history=history, bookmarks=bookmarks))
