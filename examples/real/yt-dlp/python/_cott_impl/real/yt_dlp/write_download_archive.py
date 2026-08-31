from pathlib import Path

from cott_runtime import CottList, Err, Ok, Result, UNIT, Unit, _cott_fixture_write
from real.yt_dlp_types import MediaError, MediaError_ArchiveFailure, MediaItem


def write_download_archive(path: Path, items: CottList[MediaItem]) -> Result[Unit, MediaError]:
    if len(items) > 100000:
        return Err(error=MediaError_ArchiveFailure(path=path, message="download archive cannot contain more than 100000 entries"))

    entries: list[str] = []
    item: MediaItem
    for item in items:
        if item.id == "" or item.id.strip() != item.id or "\n" in item.id or "\r" in item.id:
            return Err(error=MediaError_ArchiveFailure(path=path, message="download archive entries must be non-empty single lines without surrounding whitespace"))
        entries.append(item.id)

    content: str = "\n".join(entries)
    if content != "":
        content += "\n"
    _cott_fixture_write(path, content.encode("utf-8"))
    return Ok(value=UNIT)
