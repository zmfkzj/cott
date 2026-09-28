from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import FormatContainer, FormatContainer_Any, FormatContainer_Audio, FormatContainer_Best, FormatContainer_Video, FormatContainer_Worst, FormatDescriptor, FormatRequest, MediaError, MediaError_FormatUnavailable, MediaError_InvalidInput


def _container_matches(wanted: FormatContainer, fmt: FormatDescriptor) -> bool:
    match wanted:
        case FormatContainer_Any():
            return True
        case FormatContainer_Video():
            return fmt.has_video
        case FormatContainer_Audio():
            return fmt.has_audio
        case FormatContainer_Best():
            return isinstance(fmt.container, FormatContainer_Best)
        case FormatContainer_Worst():
            return isinstance(fmt.container, FormatContainer_Worst)


def filter_formats(formats: CottList[FormatDescriptor], request: FormatRequest) -> Result[CottList[FormatDescriptor], MediaError]:
    if request.max_file_size != 0 and request.max_file_size < request.min_file_size:
        return Err(error=MediaError_InvalidInput(message="min_file_size exceeds max_file_size"))
    selected: list[FormatDescriptor] = []
    for fmt in formats:
        if fmt.file_size < request.min_file_size or (request.max_file_size != 0 and fmt.file_size > request.max_file_size):
            continue
        if len(request.containers) != 0 and not any(_container_matches(wanted, fmt) for wanted in request.containers):
            continue
        selected.append(fmt)
    if not selected:
        return Err(error=MediaError_FormatUnavailable(selector=request.selector))
    return Ok(value=CottList(values=selected))
