from cott_runtime import Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_InvalidTemplate, MediaItem


def render_output_path(item: MediaItem, template: str, missing_placeholder: str) -> Result[str, MediaError]:
    fragments: list[str] = []
    cursor = 0
    literal_start = 0
    template_length = len(template)

    while cursor < template_length:
        if template[cursor] != "%" or cursor + 1 >= template_length or template[cursor + 1] != "(":
            cursor += 1
            continue

        if literal_start < cursor:
            fragments.append(template[literal_start:cursor])

        closing = template.find(")", cursor + 2)
        if closing == -1 or closing == cursor + 2 or closing + 1 >= template_length or template[closing + 1] != "s":
            return Err(error=MediaError_InvalidTemplate())

        field_name = template[cursor + 2:closing]
        if field_name == "id":
            fragments.append(item.id)
        elif field_name == "title":
            fragments.append(item.title)
        elif field_name == "ext":
            fragments.append(item.ext)
        elif field_name == "playlist_index":
            fragments.append(str(item.playlist_index))
        else:
            fragments.append(missing_placeholder)

        cursor = closing + 2
        literal_start = cursor

    if literal_start < template_length:
        fragments.append(template[literal_start:])

    return Ok(value="".join(fragments))
