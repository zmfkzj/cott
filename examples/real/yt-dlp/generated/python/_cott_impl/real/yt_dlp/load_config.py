import os
import stat
from pathlib import Path
from typing import Final

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp import parse_arguments
from real.yt_dlp_types import CliInput, MediaError, MediaError_InvalidConfig

_MAX_BYTES: Final[int] = 1048576
_MAX_ARGUMENTS: Final[int] = 100000
_WHITESPACE: Final[str] = " \t\r\n"
_DQ_ESCAPABLE: Final[str] = "$`\"\\\n"
_BOM: Final[bytes] = b"\xef\xbb\xbf"


def _split(text: str) -> list[str] | None:
    tokens: list[str] = []
    current: list[str] = []
    in_token = False
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in _WHITESPACE:
            if in_token:
                tokens.append("".join(current))
                if len(tokens) > _MAX_ARGUMENTS:
                    return None
                current = []
                in_token = False
            i += 1
        elif ch == "#" and not in_token:
            while i < n and text[i] != "\n":
                i += 1
        elif ch == "\\":
            if i + 1 >= n:
                return None
            nxt = text[i + 1]
            if nxt != "\n":
                current.append(nxt)
                in_token = True
            i += 2
        elif ch == "'":
            end = text.find("'", i + 1)
            if end < 0:
                return None
            current.append(text[i + 1:end])
            in_token = True
            i = end + 1
        elif ch == '"':
            in_token = True
            i += 1
            closed = False
            while i < n:
                c = text[i]
                if c == '"':
                    closed = True
                    i += 1
                    break
                if c == "\\" and i + 1 < n and text[i + 1] in _DQ_ESCAPABLE:
                    if text[i + 1] != "\n":
                        current.append(text[i + 1])
                    i += 2
                else:
                    current.append(c)
                    i += 1
            if not closed:
                return None
        else:
            current.append(ch)
            in_token = True
            i += 1
    if in_token:
        tokens.append("".join(current))
    if len(tokens) > _MAX_ARGUMENTS:
        return None
    return tokens


def load_config(path: Path) -> Result[CottList[CliInput], MediaError]:
    try:
        with path.open("rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                return Err(error=MediaError_InvalidConfig(path=path, message="config path is not a regular file"))
            data = handle.read(_MAX_BYTES + 1)
    except OSError:
        return Err(error=MediaError_InvalidConfig(path=path, message="cannot read config file"))
    if len(data) > _MAX_BYTES:
        return Err(error=MediaError_InvalidConfig(path=path, message="config file is too large"))
    if data.startswith(_BOM):
        data = data[len(_BOM):]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return Err(error=MediaError_InvalidConfig(path=path, message="config file is not valid UTF-8"))
    tokens = _split(text)
    if tokens is None:
        return Err(error=MediaError_InvalidConfig(path=path, message="malformed quoting or too many arguments in config file"))
    parsed = parse_arguments(CottList(values=tokens))
    match parsed:
        case Ok(value=inputs):
            return Ok(value=inputs)
        case Err():
            return Err(error=MediaError_InvalidConfig(path=path, message="invalid arguments in config file"))
