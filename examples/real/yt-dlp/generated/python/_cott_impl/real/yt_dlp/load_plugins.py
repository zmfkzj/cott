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
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    except FileNotFoundError:
        return Err(error="plugin manifest not found")
    except (OSError, ValueError, TypeError):
        return Err(error="plugin manifest cannot be opened or is a symlink")
    outcome: Result[bytes, str] = Err(error="plugin manifest read failed")
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            outcome = Err(error="plugin manifest is not a regular file")
        elif info.st_size > _MAX_BYTES:
            outcome = Err(error="plugin manifest exceeds size limit")
        else:
            buffer = bytearray()
            oversized = False
            while True:
                chunk = os.read(fd, _CHUNK)
                if not chunk:
                    break
                buffer.extend(chunk)
                if len(buffer) > _MAX_BYTES:
                    oversized = True
                    break
            if oversized:
                outcome = Err(error="plugin manifest exceeds size limit")
            else:
                outcome = Ok(value=bytes(buffer))
    except OSError:
        outcome = Err(error="plugin manifest read failed")
    try:
        os.close(fd)
    except OSError:
        return Err(error="plugin manifest close failed")
    return outcome


def _parse(path: Path, data: bytes) -> Result[PluginDescriptor, str]:
    name = Path(path).stem
    if name == "":
        return Err(error="plugin manifest name is empty")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return Err(error="plugin manifest is not valid UTF-8")
    extractors: list[str] = []
    processors: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "" or line.startswith("#"):
            continue
        kind, sep, rest = line.partition(":")
        entry = rest.strip()
        if sep == "" or entry == "":
            return Err(error="plugin manifest declaration is malformed")
        if kind == "extractor":
            extractors.append(entry)
        elif kind == "postprocessor" or kind == "post_processor":
            processors.append(entry)
        else:
            return Err(error="plugin manifest declaration type is unknown")
        if len(extractors) + len(processors) > _MAX_DECLARATIONS:
            return Err(error="plugin manifest exceeds declaration limit")
    if len(extractors) + len(processors) == 0:
        return Err(error="plugin manifest declares no plugins")
    return Ok(value=PluginDescriptor(name=name, path=path, extractor_names=CottList(values=extractors), post_processor_names=CottList(values=processors)))


def load_plugins(paths: CottList[Path]) -> Result[CottList[PluginDescriptor], MediaError]:
    if len(paths) > _MAX_PATHS:
        return _reject(paths[_MAX_PATHS], "too many plugin manifests")
    descriptors: list[PluginDescriptor] = []
    for path in paths:
        match _read_bounded(Path(path)):
            case Err(error=read_message):
                return _reject(path, read_message)
            case Ok(value=data):
                match _parse(path, data):
                    case Err(error=parse_message):
                        return _reject(path, parse_message)
                    case Ok(value=descriptor):
                        descriptors.append(descriptor)
    return Ok(value=CottList(values=descriptors))
