from cott_runtime import Err, Ok, Result
from curriculum.archive_request import canonicalize_archive_url
from curriculum.archive_request import compose_archive_plan
from curriculum.archive_request_types import ArchivePlan, ArchiveRequest, ArchiveRequestError, ArchiveRequestError_EmptySelection


def plan_archive(request: ArchiveRequest) -> Result[ArchivePlan, ArchiveRequestError]:
    if not request.include_html and not request.include_media:
        return Err(error=ArchiveRequestError_EmptySelection())

    canonical_url_result: Result[str, ArchiveRequestError] = canonicalize_archive_url(request.url)
    if isinstance(canonical_url_result, Err):
        return Err(error=canonical_url_result.error)

    return Ok(value=compose_archive_plan(canonical_url=canonical_url_result.value, include_html=request.include_html, include_media=request.include_media))
