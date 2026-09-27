import os
import stat
from pathlib import Path
from typing import Final

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_PluginRejected, PluginDescriptor

_MAX_PATHS: Final[int] = 100000
_MAX_BYTES: Final[int] = 1048576
_MAX_DECLARATIONS: Final[int] = 100000
_CHUNK: Final[int] = 65536


def _reject(path: Path, message: str) -> Result[CottList[PluginDescriptor], MediaError]:
    return Err(error=MediaError_PluginRejected(path=path, message=message))


def _read_bounded(path: Path) -> Result[bytes, str]:
    if os.name != "posix" or os.O_NOFOLLOW == 0:
        return Err(error="platform cannot open plugin manifests without following symlinks")
    try:
        fd: int = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    except (OSError, ValueError):
        return Err(error="plugin manifest cannot be opened")

    outcome: Result[bytes, str]
    try:
        info: os.stat_result = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            outcome = Err(error="plugin manifest is not a regular file")
        elif info.st_size > _MAX_BYTES:
            outcome = Err(error="plugin manifest exceeds size limit")
        else:
            buffer: bytearray = bytearray()
            while True:
                chunk: bytes = os.read(fd, min(_CHUNK, _MAX_BYTES + 1 - len(buffer)))
                if not chunk:
                    break
                buffer.extend(chunk)
                if len(buffer) > _MAX_BYTES:
                    break
            if len(buffer) > _MAX_BYTES:
                outcome = Err(error="plugin manifest exceeds size limit")
            else:
                outcome = Ok(value=bytes(buffer))
    except OSError:
        outcome = Err(error="plugin manifest cannot be read")
    try:
        os.close(fd)
    except OSError:
        return Err(error="plugin manifest cannot be closed")
    return outcome


def _parse(path: Path, data: bytes) -> Result[PluginDescriptor, str]:
    try:
        text: str = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return Err(error="plugin manifest is not valid UTF-8")
    extractors: list[str] = []
    processors: list[str] = []
    for raw_line in text.splitlines():
        line: str = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        kind, sep, remainder = line.partition(":")
        name: str = remainder.strip()
        if not sep or not name:
            return Err(error="plugin manifest declaration is malformed")
        if kind not in ("extractor", "postprocessor", "post_processor"):
            return Err(error="plugin manifest declaration type is unknown")
        if len(extractors) + len(processors) >= _MAX_DECLARATIONS:
            return Err(error="plugin manifest exceeds declaration limit")
        if kind == "extractor":
            extractors.append(name)
        else:
            processors.append(name)
    if not extractors and not processors:
        return Err(error="plugin manifest declares no plugins")
    return Ok(value=PluginDescriptor(name=path.stem, path=path, extractor_names=CottList(values=extractors), post_processor_names=CottList(values=processors)))


def load_plugins(paths: CottList[Path]) -> Result[CottList[PluginDescriptor], MediaError]:
    if len(paths) > _MAX_PATHS:
        return _reject(paths[_MAX_PATHS], "too many plugin manifests")
    descriptors: list[PluginDescriptor] = []
    for path in paths:
        if not path.stem:
            return _reject(path, "plugin manifest name is empty")
        match _read_bounded(path):
            case Err(error=read_error):
                return _reject(path, read_error)
            case Ok(value=data):
                match _parse(path, data):
                    case Err(error=parse_error):
                        return _reject(path, parse_error)
                    case Ok(value=descriptor):
                        descriptors.append(descriptor)
    return Ok(value=CottList(values=descriptors))
