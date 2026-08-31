from cott_runtime import CottList, Err, Ok, Result, _cott_fixture_read
from real.yt_dlp_types import ArchiveRequest, MediaError, MediaError_ArchiveFailure


def read_download_archive(request: ArchiveRequest) -> Result[CottList[str], MediaError]:
    content: str = _cott_fixture_read(request.path).decode("utf-8-sig")
    entries: list[str] = []
    line: str
    for line in content.splitlines():
        entry: str = line.strip()
        if entry == "":
            continue
        if len(entries) == 100000:
            return Err(
                error=MediaError_ArchiveFailure(
                    path=request.path,
                    message="download archive contains more than 100000 entries",
                )
            )
        entries.append(entry)
    return Ok(value=CottList(values=tuple(entries)))
