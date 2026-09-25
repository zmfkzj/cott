from cott_runtime import CottList
from real.yt_dlp_types import DownloadPlan, MediaItem


def plan_downloads(items: CottList[MediaItem], archive: CottList[str], break_on_existing: bool) -> DownloadPlan:
    known: set[str] = set()
    for entry in archive:
        known.add(entry)
    selected: list[MediaItem] = []
    for item in items:
        if item.id in known:
            if break_on_existing:
                return DownloadPlan(items=CottList(values=selected), stopped_on_archive=True)
            continue
        selected.append(item)
    return DownloadPlan(items=CottList(values=selected), stopped_on_archive=False)
