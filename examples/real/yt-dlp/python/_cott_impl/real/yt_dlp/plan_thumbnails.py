from cott_runtime import CottList
from real.yt_dlp_types import MediaItem, ThumbnailRequest


def plan_thumbnails(item: MediaItem, request: ThumbnailRequest) -> CottList[str]:
    names: list[str] = []
    if request.write:
        if len(request.formats) == 0:
            names.append(item.id + ".thumbnail")
        else:
            for fmt in request.formats:
                if len(fmt) > 0:
                    names.append(item.id + "." + fmt)
    if len(request.convert_format) > 0:
        names.append(item.id + "." + request.convert_format)
    if request.embed:
        names.append("embed:" + item.id)
    return CottList(values=names)
