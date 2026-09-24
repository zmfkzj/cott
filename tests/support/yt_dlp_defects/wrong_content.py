import json
from pathlib import Path

from cott_runtime import CottList, Ok, Result
from real.yt_dlp_types import DownloadPlan, ExecutionReport, ExecutionRequest, MediaError, MediaItem, SimulationMode_Download


def execute(request: ExecutionRequest) -> Result[ExecutionReport, MediaError]:
    """Defect: guesses items from input text and writes a placeholder, not the transferred media."""
    items: list[MediaItem] = []
    for entry in request.inputs:
        name: str = entry.value.rsplit("/", 1)[-1]
        stem, _, ext = name.partition(".")
        items.append(MediaItem(url=entry.value, id=name, title=stem, ext=ext, playlist_index=1))
    download: bool = request.simulation == SimulationMode_Download()
    if download:
        for item in items:
            (Path(request.output.output) / item.id).write_bytes(item.url.encode("utf-8"))
    rendered: str = "\n".join(
        json.dumps({"url": item.url, "id": item.id, "title": item.title, "ext": item.ext, "playlist_index": item.playlist_index}, ensure_ascii=False, separators=(",", ":"))
        for item in items
    )
    selected: CottList[MediaItem] = CottList(values=items)
    return Ok(value=ExecutionReport(selected=selected, downloads=DownloadPlan(items=selected, stopped_on_archive=False), rendered=rendered, simulated=not download))
