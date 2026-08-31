from pathlib import Path

from cott_runtime import Err, Ok, Result
from real.yt_dlp import render_output_path
from real.yt_dlp_types import MediaError, MediaError_PathFailure, MediaItem, OutputRequest


def _sanitize_component(value: str, restrict: bool, windows: bool) -> str:
    sanitized: list[str] = []
    character: str
    for character in value:
        if restrict and not (character.isascii() and (character.isalnum() or character == "." or character == "_" or character == "-")):
            sanitized.append("_")
        elif windows and (ord(character) < 32 or character == "<" or character == ">" or character == ":" or character == '"' or character == "\\" or character == "|" or character == "?" or character == "*"):
            sanitized.append("_")
        else:
            sanitized.append(character)

    result: str = "".join(sanitized)
    if windows:
        while result.endswith(" ") or result.endswith("."):
            result = result[:-1] + "_"
        stem: str = result.partition(".")[0].upper()
        if stem == "CON" or stem == "PRN" or stem == "AUX" or stem == "NUL" or stem in ("COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"):
            result = "_" + result
    return result


def _sanitize_rendered_path(value: str, restrict: bool, windows: bool) -> str:
    components: list[str] = []
    component: str
    for component in value.split("/"):
        if component == "" or component == "." or component == "..":
            components.append(component)
        else:
            components.append(_sanitize_component(component, restrict, windows))
    return "/".join(components)


def _trim_utf8(value: str, maximum_bytes: int) -> str:
    selected: list[str] = []
    used_bytes: int = 0
    character: str
    character_bytes: int
    for character in value:
        character_bytes = len(character.encode("utf-8"))
        if used_bytes + character_bytes > maximum_bytes:
            break
        selected.append(character)
        used_bytes += character_bytes
    return "".join(selected)


def _trim_filename(value: str, maximum_bytes: int) -> str:
    if len(value.encode("utf-8")) <= maximum_bytes:
        return value

    suffix: str = Path(value).suffix
    suffix_bytes: int = len(suffix.encode("utf-8"))
    if suffix != "" and suffix_bytes < maximum_bytes:
        stem: str = value[: len(value) - len(suffix)]
        trimmed_stem: str = _trim_utf8(stem, maximum_bytes - suffix_bytes)
        if trimmed_stem != "":
            return trimmed_stem + suffix
    return _trim_utf8(value, maximum_bytes)


def resolve_output_path(item: MediaItem, request: OutputRequest) -> Result[Path, MediaError]:
    rendered: str
    match render_output_path(item, request.template, request.missing_placeholder):
        case Err(error=error):
            return Err(error=error)
        case Ok(value=value):
            rendered = value

    sanitized: str = _sanitize_rendered_path(rendered, request.restrict_filenames, request.windows_filenames)
    unresolved: Path = Path(sanitized)
    if sanitized == "" or "\x00" in sanitized or unresolved.name == "" or unresolved.name == "." or unresolved.name == "..":
        return Err(error=MediaError_PathFailure(path=unresolved, message="rendered output path does not name a file"))
    if request.trim_filename_bytes < 0 or request.trim_filename_bytes > 65535:
        return Err(error=MediaError_PathFailure(path=unresolved, message="filename byte limit must be an unsigned 16-bit value"))

    relative: Path = unresolved
    if request.trim_filename_bytes > 0:
        filename: str = _trim_filename(unresolved.name, request.trim_filename_bytes)
        if filename == "":
            return Err(error=MediaError_PathFailure(path=unresolved, message="filename byte limit is too small"))
        relative = unresolved.with_name(filename)

    base: Path = request.output if request.output != Path() else request.home
    path: Path = relative if relative.is_absolute() else base / relative
    if path == request.temp:
        return Err(error=MediaError_PathFailure(path=path, message="output path must differ from temporary path"))
    return Ok(value=path)
