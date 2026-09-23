from cott_runtime import CottList, Ok, Result
from real.yt_dlp_types import CliInput, MediaError


def resolve_inputs(inputs: CottList[CliInput], config: CottList[CliInput]) -> Result[CottList[str], MediaError]:
    urls: list[str] = []
    for item in inputs:
        urls.append(item.value)
    for entry in config:
        urls.append(entry.value)
    return Ok(value=CottList(values=urls))
