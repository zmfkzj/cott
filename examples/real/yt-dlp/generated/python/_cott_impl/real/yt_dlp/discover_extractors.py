from cott_runtime import CottList
from real.yt_dlp_types import ExtractorDescriptor


def discover_extractors() -> CottList[ExtractorDescriptor]:
    urls: CottList[str] = CottList(values=["http://", "https://"])
    generic: ExtractorDescriptor = ExtractorDescriptor(name="generic", urls=urls, enabled=True, requires_login=False)
    return CottList(values=[generic])
