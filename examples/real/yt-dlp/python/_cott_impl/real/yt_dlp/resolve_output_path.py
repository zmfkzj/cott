from pathlib import Path
from typing import Final

from cott_runtime import Err, Ok, Result
from real.yt_dlp import render_output_path
from real.yt_dlp_types import MediaError, MediaError_PathFailure, MediaItem, OutputRequest

_RESTRICT_ALLOWED: Final[str] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
_WINDOWS_FORBIDDEN: Final[str] = "<>:\"\\|?*"
_WINDOWS_RESERVED: Final[str] = "CON PRN AUX NUL COM1 COM2 COM3 COM4 COM5 COM6 COM7 COM8 COM9 LPT1 LPT2 LPT3 LPT4 LPT5 LPT6 LPT7 LPT8 LPT9"


def _sanitize_component(component: str, restrict: bool, windows: bool) -> str:
    if component in ("", ".", ".."):
        return component
    result: str = component
    if restrict:
        result = "".join(ch if ch in _RESTRICT_ALLOWED else "_" for ch in result)
    if windows:
        result = "".join("_" if (ord(ch) < 0x20 or ord(ch) == 0x7F or ch in _WINDOWS_FORBIDDEN) else ch for ch in result)
        stripped: str = result.rstrip(" .")
        result = stripped + "_" * (len(result) - len(stripped))
        stem: str = result.split(".", 1)[0]
        if stem.upper() in _WINDOWS_RESERVED.split(" "):
            result = "_" + result
    return result


def _truncate_utf8(text: str, limit: int) -> str:
    return text.encode("utf-8")[:limit].decode("utf-8", errors="ignore")


def _trim_filename(name: str, limit: int) -> str:
    encoded: bytes = name.encode("utf-8")
    if limit == 0 or len(encoded) <= limit:
        return name
    dot: int = name.rfind(".")
    if dot > 0:
        ext_len: int = len(name[dot:].encode("utf-8"))
        if ext_len < limit:
            stem: str = _truncate_utf8(name[:dot], limit - ext_len)
            if stem != "":
                return stem + name[dot:]
    return _truncate_utf8(name, limit)


def _failure(path: Path, message: str) -> Result[Path, MediaError]:
    return Err(error=MediaError_PathFailure(path=path, message=message))


def _resolve_rendered(rendered: str, request: OutputRequest) -> Result[Path, MediaError]:
    if rendered == "" or "\x00" in rendered:
        return _failure(Path(rendered.replace("\x00", "")), "rendered output path is empty or contains NUL")
    components: list[str] = [_sanitize_component(part, request.restrict_filenames, request.windows_filenames) for part in rendered.split("/")]
    last: str = components[-1]
    if last in ("", ".", ".."):
        return _failure(Path(rendered), "rendered output path has no filename")
    try:
        trimmed: str = _trim_filename(last, request.trim_filename_bytes)
    except UnicodeError:
        return _failure(Path(rendered), "output filename is not valid UTF-8")
    if trimmed == "":
        return _failure(Path(rendered), "trimmed output filename is empty")
    components[-1] = trimmed
    relative: Path = Path("/".join(components))
    final: Path
    if relative.is_absolute():
        final = relative
    elif request.output != Path("."):
        final = request.output / relative
    else:
        final = request.home / relative
    if final == request.temp:
        return _failure(final, "output path equals the temporary path")
    return Ok(value=final)


def resolve_output_path(item: MediaItem, request: OutputRequest) -> Result[Path, MediaError]:
    rendered_result: Result[str, MediaError] = render_output_path(item, request.template, request.missing_placeholder)
    match rendered_result:
        case Err(error=render_error):
            return Err(error=render_error)
        case Ok(value=rendered):
            return _resolve_rendered(rendered, request)
