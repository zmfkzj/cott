from cott_runtime import CottList
from real.yt_dlp_types import MediaItem, MetadataRequest


def plan_metadata(item: MediaItem, request: MetadataRequest) -> CottList[str]:
    outputs: list[str] = []
    if request.write_info_json:
        outputs.append(item.id + ".info.json")
    if request.write_description:
        outputs.append(item.id + ".description")
    if request.write_comments:
        outputs.append(item.id + ".comments.json")
    if request.write_playlist_metadata:
        outputs.append(item.id + ".playlist.json")
    if request.embed:
        outputs.append("embed:" + item.id)
    return CottList(values=outputs)
