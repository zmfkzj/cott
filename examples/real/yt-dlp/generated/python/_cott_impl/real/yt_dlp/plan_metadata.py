from cott_runtime import CottList
from real.yt_dlp_types import MediaItem, MetadataRequest


def plan_metadata(item: MediaItem, request: MetadataRequest) -> CottList[str]:
    planned: list[str] = []
    if request.write_info_json:
        planned.append(f"{item.id}.info.json")
    if request.write_description:
        planned.append(f"{item.id}.description")
    if request.write_comments:
        planned.append(f"{item.id}.comments.json")
    if request.write_playlist_metadata:
        planned.append(f"{item.id}.playlist.json")
    if request.embed:
        planned.append(f"embed:{item.id}")
    return CottList(values=tuple(planned))
