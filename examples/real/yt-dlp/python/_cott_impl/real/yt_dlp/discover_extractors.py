from cott_runtime import CottList
from real.yt_dlp_types import ExtractorDescriptor


def discover_extractors() -> CottList[ExtractorDescriptor]:
    empty: CottList[ExtractorDescriptor] = CottList(values=[])
    return empty
