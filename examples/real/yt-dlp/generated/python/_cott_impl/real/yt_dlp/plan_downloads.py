from cott_runtime import CottList
from real.yt_dlp_types import DownloadPlan, MediaItem


def _archived_ids(archive: CottList[str]) -> set[str]:
    ids: set[str] = set()
    for entry in archive:
        stripped = entry.strip()
        if stripped == "":
            continue
        ids.add(stripped)
        tokens = stripped.split()
        if len(tokens) == 2:
            ids.add(tokens[1])
    return ids


def plan_downloads(items: CottList[MediaItem], archive: CottList[str], break_on_existing: bool) -> DownloadPlan:
    known = _archived_ids(archive)
    selected: list[MediaItem] = []
    for item in items:
        if item.id in known:
            if break_on_existing:
                return DownloadPlan(items=CottList(values=selected), stopped_on_archive=True)
            continue
        selected.append(item)
    return DownloadPlan(items=CottList(values=selected), stopped_on_archive=False)
