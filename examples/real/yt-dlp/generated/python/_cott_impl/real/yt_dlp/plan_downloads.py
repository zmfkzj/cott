from cott_runtime import CottList
from real.yt_dlp_types import DownloadPlan, MediaItem


def plan_downloads(items: CottList[MediaItem], archive: CottList[str], break_on_existing: bool) -> DownloadPlan:
    archived_ids: set[str] = set(archive)
    planned: list[MediaItem] = []
    stopped_on_archive: bool = False
    item: MediaItem
    for item in items:
        if item.id in archived_ids:
            if break_on_existing:
                stopped_on_archive = True
                break
            continue
        planned.append(item)
    return DownloadPlan(items=CottList(values=tuple(planned)), stopped_on_archive=stopped_on_archive)
