from cott_runtime import CottList
from real.yt_dlp_types import FormatDescriptor


def sort_formats(formats: CottList[FormatDescriptor], fields: CottList[str]) -> CottList[FormatDescriptor]:
    ordered: list[FormatDescriptor] = [fmt for fmt in formats]
    return CottList(values=ordered)
