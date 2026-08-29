from cott_runtime import CottList
from real.yt_dlp_types import DownloadPlan, MediaItem


def plan_downloads(items: CottList[MediaItem], archive: CottList[str], break_on_existing: bool) -> DownloadPlan:
    """Preserve item order while applying archive and break-on-existing policy."""
    planned: list[MediaItem] = []
    stopped_on_archive = False

    for item in items:
        if item.url in archive:
            if break_on_existing:
                stopped_on_archive = True
                break
            continue
        planned.append(item)

    return DownloadPlan(items=CottList(values=tuple(planned)), stopped_on_archive=stopped_on_archive)
