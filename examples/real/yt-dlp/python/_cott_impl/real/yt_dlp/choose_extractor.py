from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import ExtractorDescriptor, MediaError, MediaError_ExtractorMissing, MediaError_UnsupportedUrl


def choose_extractor(url: str, extractors: CottList[ExtractorDescriptor]) -> Result[ExtractorDescriptor, MediaError]:
    missing_name: str | None = None
    for extractor in extractors:
        matched: bool = False
        for pattern in extractor.urls:
            if pattern != "" and url.startswith(pattern):
                matched = True
                break
        if not matched:
            continue
        if extractor.enabled:
            return Ok(value=extractor)
        if missing_name is None:
            missing_name = extractor.name
    if missing_name is not None:
        return Err(error=MediaError_ExtractorMissing(name=missing_name))
    return Err(error=MediaError_UnsupportedUrl())
