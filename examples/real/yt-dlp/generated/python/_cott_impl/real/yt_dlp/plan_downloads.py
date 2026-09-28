from cott_runtime import CottList
from real.yt_dlp_types import DownloadPlan, MediaItem


def plan_downloads(items: CottList[MediaItem], archive: CottList[str], break_on_existing: bool) -> DownloadPlan:
    if len(archive) == 0:
        return DownloadPlan(items=items, stopped_on_archive=False)

    known: set[str] = set(archive)
    selected: list[MediaItem] = []
    for item in items:
        if item.id in known:
            if break_on_existing:
                return DownloadPlan(items=CottList(values=selected), stopped_on_archive=True)
            continue
        selected.append(item)
    return DownloadPlan(items=CottList(values=selected), stopped_on_archive=False)
