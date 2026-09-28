import os
import stat
from pathlib import Path
from typing import Final

import cott_runtime
from cott_runtime import CottList, Result
from real.yt_dlp_types import MediaError, MediaError_PluginRejected, PluginDescriptor

_MAX_PATHS: Final[int] = 100000
_MAX_BYTES: Final[int] = 1048576
_MAX_DECLARATIONS: Final[int] = 100000
_CHUNK: Final[int] = 65536


def _reject(path: Path, message: str) -> Result[CottList[PluginDescriptor], MediaError]:
    return cott_runtime.Err(error=MediaError_PluginRejected(path=path, message=message))


def _read_manifest(path: Path) -> Result[str, str]:
    if os.name != "posix":
        return cott_runtime.Err(error="platform cannot safely open plugin manifests")
    try:
        flags: int = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
    except AttributeError:
        return cott_runtime.Err(error="platform cannot safely open plugin manifests")
    try:
        fd: int = os.open(path, flags)
    except (OSError, ValueError, UnicodeError):
        return cott_runtime.Err(error="plugin manifest cannot be opened")
    outcome: Result[str, str]
    try:
        info: os.stat_result = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            outcome = cott_runtime.Err(error="plugin manifest is not a regular file")
        elif info.st_size > _MAX_BYTES:
            outcome = cott_runtime.Err(error="plugin manifest exceeds size limit")
        else:
            data: bytearray = bytearray()
            while len(data) <= _MAX_BYTES:
                block: bytes = os.read(fd, min(_CHUNK, _MAX_BYTES + 1 - len(data)))
                if not block:
                    break
                data.extend(block)
            if len(data) > _MAX_BYTES:
                outcome = cott_runtime.Err(error="plugin manifest exceeds size limit")
            else:
                try:
                    outcome = cott_runtime.Ok(value=data.decode("utf-8-sig"))
                except UnicodeDecodeError:
                    outcome = cott_runtime.Err(error="plugin manifest is not valid UTF-8")
    except OSError:
        outcome = cott_runtime.Err(error="plugin manifest cannot be inspected or read")
    try:
        os.close(fd)
    except OSError:
        return cott_runtime.Err(error="plugin manifest cannot be closed")
    return outcome


def _parse_manifest(path: Path, text: str) -> Result[PluginDescriptor, str]:
    extractors: list[str] = []
    processors: list[str] = []
    for raw_line in text.splitlines():
        line: str = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        kind, separator, remainder = line.partition(":")
        name: str = remainder.strip()
        if not separator or not name:
            return cott_runtime.Err(error="plugin manifest declaration is malformed")
        if kind not in ("extractor", "postprocessor", "post_processor"):
            return cott_runtime.Err(error="plugin manifest declaration type is unknown")
        if len(extractors) + len(processors) >= _MAX_DECLARATIONS:
            return cott_runtime.Err(error="plugin manifest exceeds declaration limit")
        if kind == "extractor":
            extractors.append(name)
        else:
            processors.append(name)
    if not extractors and not processors:
        return cott_runtime.Err(error="plugin manifest declares no plugins")
    return cott_runtime.Ok(value=PluginDescriptor(name=path.stem, path=path, extractor_names=CottList(values=extractors), post_processor_names=CottList(values=processors)))


def load_plugins(paths: CottList[Path]) -> Result[CottList[PluginDescriptor], MediaError]:
    if len(paths) > _MAX_PATHS:
        return _reject(paths[_MAX_PATHS], "too many plugin manifests")
    descriptors: list[PluginDescriptor] = []
    for path in paths:
        if not path.stem:
            return _reject(path, "plugin manifest name is empty")
        match _read_manifest(path):
            case cott_runtime.Err(error=read_error):
                return _reject(path, read_error)
            case cott_runtime.Ok(value=text):
                match _parse_manifest(path, text):
                    case cott_runtime.Err(error=parse_error):
                        return _reject(path, parse_error)
                    case cott_runtime.Ok(value=descriptor):
                        descriptors.append(descriptor)
    return cott_runtime.Ok(value=CottList(values=descriptors))
