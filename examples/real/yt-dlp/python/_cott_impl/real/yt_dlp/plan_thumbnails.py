from cott_runtime import CottList
from real.yt_dlp_types import MediaItem, ThumbnailRequest


def plan_thumbnails(item: MediaItem, request: ThumbnailRequest) -> CottList[str]:
    planned: list[str] = []
    thumbnail_format: str
    if request.write:
        if len(request.formats) == 0:
            planned.append(f"{item.id}.thumbnail")
        else:
            for thumbnail_format in request.formats:
                if thumbnail_format != "":
                    planned.append(f"{item.id}.{thumbnail_format}")
    if request.convert_format != "":
        planned.append(f"{item.id}.{request.convert_format}")
    if request.embed:
        planned.append(f"embed:{item.id}")
    return CottList(values=tuple(planned))
