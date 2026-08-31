from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import (
    FormatContainer,
    FormatContainer_Any,
    FormatContainer_Audio,
    FormatContainer_Best,
    FormatContainer_Video,
    FormatContainer_Worst,
    FormatDescriptor,
    FormatRequest,
    MediaError,
    MediaError_FormatUnavailable,
    MediaError_InvalidInput,
)


def filter_formats(formats: CottList[FormatDescriptor], request: FormatRequest) -> Result[CottList[FormatDescriptor], MediaError]:
    if (
        request.min_file_size < 0
        or request.max_file_size < 0
        or request.min_file_size > 18446744073709551615
        or request.max_file_size > 18446744073709551615
    ):
        return Err(error=MediaError_InvalidInput(message="file size limits must be unsigned 64-bit values"))
    if request.max_file_size > 0 and request.min_file_size > request.max_file_size:
        return Err(error=MediaError_InvalidInput(message="minimum file size cannot exceed maximum file size"))

    selected: list[FormatDescriptor] = []
    descriptor: FormatDescriptor
    requested_container: FormatContainer
    container_matches: bool
    for descriptor in formats:
        if request.selector != "" and descriptor.id != request.selector:
            continue
        if request.min_file_size > 0 and descriptor.file_size < request.min_file_size:
            continue
        if request.max_file_size > 0 and descriptor.file_size > request.max_file_size:
            continue

        container_matches = len(request.containers) == 0
        for requested_container in request.containers:
            match requested_container:
                case FormatContainer_Any():
                    container_matches = True
                case FormatContainer_Video() | FormatContainer_Audio() | FormatContainer_Best() | FormatContainer_Worst():
                    container_matches = requested_container == descriptor.container
            if container_matches:
                break
        if container_matches:
            selected.append(descriptor)

    if len(selected) == 0:
        return Err(error=MediaError_FormatUnavailable(selector=request.selector))
    return Ok(value=CottList(values=tuple(selected)))
