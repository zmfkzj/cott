from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import (
    ExtractorDescriptor,
    MediaError,
    MediaError_ExtractorMissing,
    MediaError_UnsupportedUrl,
)


def choose_extractor(url: str, extractors: CottList[ExtractorDescriptor]) -> Result[ExtractorDescriptor, MediaError]:
    disabled_match: ExtractorDescriptor | None = None
    extractor: ExtractorDescriptor
    for extractor in extractors:
        prefix: str
        for prefix in extractor.urls:
            if url.startswith(prefix):
                if extractor.enabled:
                    return Ok(value=extractor)
                if disabled_match is None:
                    disabled_match = extractor
                break

    if disabled_match is not None:
        return Err(error=MediaError_ExtractorMissing(name=disabled_match.name))
    return Err(error=MediaError_UnsupportedUrl())
