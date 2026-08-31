from cott_runtime import CottList
from real.yt_dlp_types import FormatDescriptor


def sort_formats(formats: CottList[FormatDescriptor], fields: CottList[str]) -> CottList[FormatDescriptor]:
    ordered: list[FormatDescriptor] = list(formats)
    field_index: int = len(fields)
    while field_index > 0:
        field_index -= 1
        field: str = fields[field_index]
        reverse: bool = field.startswith("+")
        name: str = field[1:] if reverse else field

        if name == "id":
            ordered.sort(key=lambda descriptor: descriptor.id, reverse=reverse)
        elif name == "ext" or name == "extension":
            ordered.sort(key=lambda descriptor: descriptor.extension, reverse=reverse)
        elif name == "height" or name == "res" or name == "video_height":
            ordered.sort(key=lambda descriptor: descriptor.video_height, reverse=reverse)
        elif name == "abr" or name == "br" or name == "audio_bitrate":
            ordered.sort(key=lambda descriptor: descriptor.audio_bitrate, reverse=reverse)
        elif name == "filesize" or name == "size" or name == "file_size":
            ordered.sort(key=lambda descriptor: descriptor.file_size, reverse=reverse)
        elif name == "hasvid" or name == "has_video":
            ordered.sort(key=lambda descriptor: descriptor.has_video, reverse=reverse)
        elif name == "hasaud" or name == "has_audio":
            ordered.sort(key=lambda descriptor: descriptor.has_audio, reverse=reverse)

    return CottList(values=tuple(ordered))
