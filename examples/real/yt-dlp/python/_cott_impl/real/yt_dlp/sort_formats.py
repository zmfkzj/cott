from cott_runtime import CottList
from real.yt_dlp_types import FormatDescriptor


def _sort_key(fmt: FormatDescriptor, keys: list[str]) -> tuple[int, ...]:
    values: list[int] = []
    for key in keys:
        if key == "res":
            values.append(-fmt.video_height)
        elif key == "abr":
            values.append(-fmt.audio_bitrate)
        else:
            values.append(-fmt.file_size)
    return tuple(values)


def sort_formats(formats: CottList[FormatDescriptor], fields: CottList[str]) -> CottList[FormatDescriptor]:
    keys: list[str] = []
    for name in fields:
        if name in ("res", "abr", "size") and name not in keys:
            keys.append(name)
    ordered: list[FormatDescriptor] = [fmt for fmt in formats]
    if keys:
        ordered.sort(key=lambda fmt: _sort_key(fmt, keys))
    return CottList(values=ordered)
