import bz2
import re

from cott_runtime import CottList, Err, Nothing, Ok, Option, Result, Some, U64
from real.toolong_types import (
    EntryKind,
    EntryKind_Access,
    EntryKind_Error,
    EntryKind_Json,
    EntryKind_Plain,
    LogEntry,
    LogPage,
    LogSource,
    ToolongError,
    ToolongError_DecodeFailed,
    ToolongError_InvalidLimit,
    ToolongError_OpenFailed,
)


def _valid_utf8(data: bytes) -> bool:
    index = 0
    size = len(data)
    while index < size:
        first = data[index]
        if first <= 0x7F:
            index += 1
            continue
        if 0xC2 <= first <= 0xDF:
            if index + 1 >= size or not 0x80 <= data[index + 1] <= 0xBF:
                return False
            index += 2
            continue
        if 0xE0 <= first <= 0xEF:
            if index + 2 >= size:
                return False
            second = data[index + 1]
            third = data[index + 2]
            if not 0x80 <= third <= 0xBF:
                return False
            if first == 0xE0:
                if not 0xA0 <= second <= 0xBF:
                    return False
            elif first == 0xED:
                if not 0x80 <= second <= 0x9F:
                    return False
            elif not 0x80 <= second <= 0xBF:
                return False
            index += 3
            continue
        if 0xF0 <= first <= 0xF4:
            if index + 3 >= size:
                return False
            second = data[index + 1]
            third = data[index + 2]
            fourth = data[index + 3]
            if not 0x80 <= third <= 0xBF or not 0x80 <= fourth <= 0xBF:
                return False
            if first == 0xF0:
                if not 0x90 <= second <= 0xBF:
                    return False
            elif first == 0xF4:
                if not 0x80 <= second <= 0x8F:
                    return False
            elif not 0x80 <= second <= 0xBF:
                return False
            index += 4
            continue
        return False
    return True


def _decode_utf8(data: bytes) -> Option[str]:
    if not _valid_utf8(data):
        return Nothing()
    return Some(value=data.decode("utf-8"))


def _record_bytes(raw: bytes) -> bytes:
    if raw.endswith(b"\n"):
        if len(raw) >= 2 and raw[-2] == 0x0D:
            return raw[:-2]
        return raw[:-1]
    return raw


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


def _decode_json_string(text: str, start: int, end: int) -> str:
    parts: list[str] = []
    index = start + 1
    stop = end - 1
    while index < stop:
        character = text[index]
        if character != "\\":
            parts.append(character)
            index += 1
            continue
        escape = text[index + 1]
        if escape == "b":
            parts.append("\b")
        elif escape == "f":
            parts.append("\f")
        elif escape == "n":
            parts.append("\n")
        elif escape == "r":
            parts.append("\r")
        elif escape == "t":
            parts.append("\t")
        elif escape != "u":
            parts.append(escape)
        else:
            code = 0
            offset = 2
            while offset <= 5:
                code = code * 16 + _hex_value(text[index + offset])
                offset += 1
            index += 6
            if 0xD800 <= code <= 0xDBFF and index + 5 < stop and text[index:index + 2] == "\\u":
                low = 0
                offset = 2
                while offset <= 5:
                    low = low * 16 + _hex_value(text[index + offset])
                    offset += 1
                if 0xDC00 <= low <= 0xDFFF:
                    code = 0x10000 + (code - 0xD800) * 0x400 + low - 0xDC00
                    index += 6
            parts.append(chr(code))
            continue
        index += 2
    return "".join(parts)


def _json_object_timestamp(text: str) -> Option[str]:
    index = _skip_json_whitespace(text, 0)
    size = len(text)
    if index >= size or text[index] != "{":
        return Nothing()
    index = _skip_json_whitespace(text, index + 1)
    timestamp = ""
    time = ""
    at_timestamp = ""
    has_timestamp = False
    has_time = False
    has_at_timestamp = False
    while index < size and text[index] != "}":
        key_start = index
        key_end = _json_string_end(text, key_start)
        key = _decode_json_string(text, key_start, key_end)
        index = _skip_json_whitespace(text, key_end)
        value_start = _skip_json_whitespace(text, index + 1)
        if text[value_start] == '"':
            value_end = _json_string_end(text, value_start)
            if key == "timestamp" and not has_timestamp:
                timestamp = _decode_json_string(text, value_start, value_end)
                has_timestamp = True
            elif key == "time" and not has_time:
                time = _decode_json_string(text, value_start, value_end)
                has_time = True
            elif key == "@timestamp" and not has_at_timestamp:
                at_timestamp = _decode_json_string(text, value_start, value_end)
                has_at_timestamp = True
        index = _skip_json_whitespace(text, _json_value_end(text, value_start))
        if index < size and text[index] == ",":
            index = _skip_json_whitespace(text, index + 1)
    if has_timestamp:
        return Some(value=timestamp)
    if has_time:
        return Some(value=time)
    if has_at_timestamp:
        return Some(value=at_timestamp)
    return Nothing()


def _access_timestamp(text: str) -> Option[str]:
    apache = re.search(r"\[(\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4})\]", text)
    if apache is not None:
        return Some(value=apache.group(1))
    method = re.search(r'(?:^|\s|\")(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|CONNECT|TRACE)\s+\S+', text)
    if method is None:
        return Nothing()
    timestamp = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})", text)
    if timestamp is None:
        return Nothing()
    return Some(value=timestamp.group(0))


def _iso_timestamp(text: str) -> Option[str]:
    timestamp = re.match(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?", text)
    if timestamp is None:
        return Nothing()
    return Some(value=timestamp.group(0))


def _classify(text: str) -> tuple[EntryKind, Option[str]]:
    if _valid_json(text):
        return (EntryKind_Json(), _json_object_timestamp(text))
    access_timestamp = _access_timestamp(text)
    match access_timestamp:
        case Some(value=_):
            return (EntryKind_Access(), access_timestamp)
        case Nothing():
            timestamp = _iso_timestamp(text)
            folded = text.casefold()
            if "error" in folded or "exception" in folded or "fatal" in folded or "traceback" in folded:
                return (EntryKind_Error(), timestamp)
            return (EntryKind_Plain(), timestamp)


def _entry(source: LogSource, record: U64, byte_offset: U64, text: str) -> LogEntry:
    kind, timestamp = _classify(text)
    return LogEntry(source=source.path, record=record, byte_offset=byte_offset, timestamp=timestamp, kind=kind, text=text)


def _load_plain(source: LogSource, limit: U64) -> Result[LogPage, ToolongError]:
    entries: list[LogEntry] = []
    byte_offset = 0
    record = 1
    with source.path.open("rb") as stream:
        while len(entries) < limit:
            raw = stream.readline()
            if raw == b"":
                break
            decoded = _decode_utf8(_record_bytes(raw))
            match decoded:
                case Some(value=text):
                    entries.append(_entry(source, record, byte_offset, text))
                case Nothing():
                    return Err(error=ToolongError_DecodeFailed(path=source.path))
            byte_offset += len(raw)
            record += 1
    complete = byte_offset >= source.path.stat().st_size
    return Ok(value=LogPage(source=source, entries=CottList(values=tuple(entries)), next_byte=byte_offset, complete=complete))


def _load_compressed(source: LogSource, limit: U64) -> Result[LogPage, ToolongError]:
    entries: list[LogEntry] = []
    byte_offset = 0
    record = 1
    complete = False
    with bz2.open(source.path, "rb") as stream:
        while len(entries) < limit:
            raw = stream.readline()
            if raw == b"":
                complete = True
                break
            decoded = _decode_utf8(_record_bytes(raw))
            match decoded:
                case Some(value=text):
                    entries.append(_entry(source, record, byte_offset, text))
                case Nothing():
                    return Err(error=ToolongError_DecodeFailed(path=source.path))
            byte_offset += len(raw)
            record += 1
        if len(entries) == limit:
            complete = stream.peek(1) == b""
    return Ok(value=LogPage(source=source, entries=CottList(values=tuple(entries)), next_byte=0, complete=complete))


def load_log(source: LogSource, limit: U64) -> Result[LogPage, ToolongError]:
    if limit == 0:
        return Err(error=ToolongError_InvalidLimit())
    if not source.path.exists() or not source.path.is_file():
        return Err(error=ToolongError_OpenFailed(path=source.path, message="file is unavailable"))
    suffix = source.path.suffix.casefold()
    if suffix == ".bz" or suffix == ".bz2":
        return _load_compressed(source, limit)
    return _load_plain(source, limit)
