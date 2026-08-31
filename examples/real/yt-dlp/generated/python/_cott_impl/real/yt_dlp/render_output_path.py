from cott_runtime import Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_InvalidTemplate, MediaItem


def _render_placeholder(item: MediaItem, name: str, missing_placeholder: str) -> str:
    value: str
    if name == "id":
        value = item.id
    elif name == "title":
        value = item.title
    elif name == "ext":
        value = item.ext
    elif name == "playlist_index":
        if item.playlist_index <= 0 or item.playlist_index > 18446744073709551615:
            return missing_placeholder
        return str(item.playlist_index)
    else:
        return missing_placeholder
    if value == "":
        return missing_placeholder
    return value


def render_output_path(item: MediaItem, template: str, missing_placeholder: str) -> Result[str, MediaError]:
    if template == "":
        return Err(error=MediaError_InvalidTemplate())

    rendered: list[str] = []
    index: int = 0
    while index < len(template):
        character: str = template[index]
        if character != "%":
            rendered.append(character)
            index += 1
            continue
        if index + 1 == len(template):
            return Err(error=MediaError_InvalidTemplate())
        marker: str = template[index + 1]
        if marker == "%":
            rendered.append("%")
            index += 2
            continue
        if marker != "(":
            return Err(error=MediaError_InvalidTemplate())

        closing: int = template.find(")", index + 2)
        if closing == -1 or closing + 1 == len(template) or template[closing + 1] != "s":
            return Err(error=MediaError_InvalidTemplate())
        name: str = template[index + 2 : closing]
        if name == "":
            return Err(error=MediaError_InvalidTemplate())
        rendered.append(_render_placeholder(item, name, missing_placeholder))
        index = closing + 2

    return Ok(value="".join(rendered))
