import json
import re
from typing import Final

from cott_runtime import CottList
from real.toolong.model_types import LineFormat, LineFormat_CombinedLog, LineFormat_CommonLog, LineFormat_Json, LineFormat_Plain, ParsedLine, StyledSpan, StyledText
from real.toolong.text import decode_ansi, highlight_json, highlight_repr
from real.toolong.text_types import COMBINED_LOG_PATTERN, COMMON_LOG_PATTERN

_MAX_LINE: Final[int] = 10000
_METHOD_PATTERN: Final[str] = "GET|POST|PUT|HEAD|POST|DELETE|OPTIONS|PATCH"
_STATUS_4XX_STYLE: Final[str] = "fg:ansired bold"
_STATUS_OTHER_STYLE: Final[str] = "fg:ansimagenta"
_METHOD_STYLE: Final[str] = "fg:ansiyellow bold"


def _highlight_plain(line: str) -> StyledText:
    text = decode_ansi(line)
    if len(text.spans) == 0:
        return highlight_repr(text)
    return text


def _try_json(line: str) -> tuple[str, StyledText] | None:
    stripped = line.strip()
    if not stripped:
        return None
    try:
        json.loads(stripped)
    except ValueError:
        return None
    text = decode_ansi(stripped)
    if len(text.spans) == 0:
        text = highlight_json(text)
    return stripped, text


def _try_log(line: str, pattern: str) -> StyledText | None:
    match = re.fullmatch(pattern, line)
    if match is None:
        return None
    text = _highlight_plain(line)
    spans: list[StyledSpan] = [span for span in text.spans]
    plain = text.text
    status = match.group("status")
    if status:
        style = _STATUS_4XX_STYLE if status.startswith("4") else _STATUS_OTHER_STYLE
        for found in re.finditer(re.escape(" " + status + " "), plain):
            spans.append(StyledSpan(start=found.start(), end=found.end(), style=style))
    for found in re.finditer(_METHOD_PATTERN, plain):
        spans.append(StyledSpan(start=found.start(), end=found.end(), style=_METHOD_STYLE))
    return StyledText(text=plain, spans=CottList(values=spans))


def _try_format(line: str, fmt: LineFormat) -> tuple[str, StyledText] | None:
    if isinstance(fmt, LineFormat_Json):
        return _try_json(line)
    if isinstance(fmt, LineFormat_CommonLog):
        text = _try_log(line, COMMON_LOG_PATTERN)
    elif isinstance(fmt, LineFormat_CombinedLog):
        text = _try_log(line, COMBINED_LOG_PATTERN)
    else:
        return line, _highlight_plain(line)
    if text is None:
        return None
    return line, text


def parse_line(line: str, order: CottList[LineFormat]) -> ParsedLine:
    if len(line) > _MAX_LINE:
        line = line[:_MAX_LINE]
    index = 0
    for fmt in order:
        parsed = _try_format(line, fmt)
        if parsed is not None:
            if index == 0:
                new_order = order
            else:
                formats = [candidate for candidate in order]
                formats.insert(0, formats.pop(index))
                new_order = CottList(values=formats)
            return ParsedLine(format=fmt, line=parsed[0], text=parsed[1], order=new_order)
        index += 1
    return ParsedLine(format=LineFormat_Plain(), line="", text=StyledText(text="", spans=CottList(values=[])), order=order)
