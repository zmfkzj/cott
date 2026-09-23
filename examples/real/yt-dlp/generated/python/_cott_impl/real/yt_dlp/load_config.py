import codecs
import shlex
from pathlib import Path
from typing import Final

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import CliInput, InputKind_Argument, MediaError, MediaError_InvalidConfig

_MAX_INPUTS: Final[int] = 100000


def _decode(data: bytes) -> str:
    for bom, encoding in (
        (codecs.BOM_UTF32_BE, "utf-32-be"),
        (codecs.BOM_UTF32_LE, "utf-32-le"),
        (codecs.BOM_UTF8, "utf-8"),
        (codecs.BOM_UTF16_BE, "utf-16-be"),
        (codecs.BOM_UTF16_LE, "utf-16-le"),
    ):
        if data.startswith(bom):
            return data[len(bom):].decode(encoding)
    return data.decode("utf-8")


def load_config(path: Path) -> Result[CottList[CliInput], MediaError]:
    try:
        with path.open("rb") as handle:
            data = handle.read()
    except OSError:
        return Err(error=MediaError_InvalidConfig(path=path, message="cannot read config file"))
    try:
        text = _decode(data)
    except UnicodeDecodeError:
        return Err(error=MediaError_InvalidConfig(path=path, message="config file is not valid text"))
    try:
        tokens = shlex.split(text, comments=True, posix=True)
    except ValueError:
        return Err(error=MediaError_InvalidConfig(path=path, message="malformed quoting in config file"))
    if len(tokens) > _MAX_INPUTS:
        return Err(error=MediaError_InvalidConfig(path=path, message="too many config arguments"))
    inputs: list[CliInput] = [CliInput(kind=InputKind_Argument(), value=token) for token in tokens]
    return Ok(value=CottList(values=inputs))
