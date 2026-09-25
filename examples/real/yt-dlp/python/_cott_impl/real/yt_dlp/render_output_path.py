from cott_runtime import Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_InvalidTemplate, MediaItem


def _field_value(item: MediaItem, name: str, conversion: str, missing_placeholder: str) -> str | None:
    if name == "playlist_index":
        return f"{item.playlist_index:d}"
    if conversion != "s":
        return None
    if name == "id":
        return item.id
    if name == "title":
        return item.title
    if name == "ext":
        return item.ext
    return missing_placeholder


def render_output_path(item: MediaItem, template: str, missing_placeholder: str) -> Result[str, MediaError]:
    size: int = len(template)
    if size == 0:
        return Err(error=MediaError_InvalidTemplate())
    pieces: list[str] = []
    index: int = 0
    while index < size:
        ch: str = template[index]
        if ch != "%":
            pieces.append(ch)
            index += 1
            continue
        if index + 1 < size and template[index + 1] == "%":
            pieces.append("%")
            index += 2
            continue
        if index + 1 >= size or template[index + 1] != "(":
            return Err(error=MediaError_InvalidTemplate())
        close: int = template.find(")", index + 2)
        if close == -1 or close + 1 >= size:
            return Err(error=MediaError_InvalidTemplate())
        name: str = template[index + 2 : close]
        conversion: str = template[close + 1]
        if len(name) == 0 or "%" in name or "(" in name or conversion not in ("s", "d"):
            return Err(error=MediaError_InvalidTemplate())
        value: str | None = _field_value(item, name, conversion, missing_placeholder)
        if value is None:
            return Err(error=MediaError_InvalidTemplate())
        pieces.append(value)
        index = close + 2
    return Ok(value="".join(pieces))
