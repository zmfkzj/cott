from cott_runtime import CottList
from curriculum.archive_request_types import ArchivePlan, CaptureKind, CaptureKind_Html, CaptureKind_Media


def compose_archive_plan(canonical_url: str, include_html: bool, include_media: bool) -> ArchivePlan:
    captures: CottList[CaptureKind]
    if include_html:
        if include_media:
            captures = CottList(values=[CaptureKind_Html(), CaptureKind_Media()])
        else:
            captures = CottList(values=[CaptureKind_Html()])
    elif include_media:
        captures = CottList(values=[CaptureKind_Media()])
    else:
        captures = CottList(values=[])
    return ArchivePlan(canonical_url=canonical_url, captures=captures)
