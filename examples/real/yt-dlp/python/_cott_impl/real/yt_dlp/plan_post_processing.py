from pathlib import Path

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some
from real.yt_dlp_types import (
    ExternalToolRequest,
    MediaError,
    MediaError_ExternalToolMissing,
    MediaError_InvalidInput,
    MediaItem,
    PostProcessRequest,
    PostProcessorKind_ConvertThumbnails,
    PostProcessorKind_EmbedMetadata,
    PostProcessorKind_EmbedSubtitle,
    PostProcessorKind_EmbedThumbnail,
    PostProcessorKind_ExtractAudio,
    PostProcessorKind_Fixup,
    PostProcessorKind_RecodeVideo,
    PostProcessorKind_RemuxVideo,
    PostProcessorKind_SponsorBlock,
    PostProcessorKind_SplitChapters,
)


def plan_post_processing(item: MediaItem, request: PostProcessRequest) -> Result[CottList[ExternalToolRequest], MediaError]:
    if len(request.kinds) == 0:
        empty: CottList[ExternalToolRequest] = CottList(values=())
        return Ok(value=empty)

    tool: ExternalToolRequest
    match request.external_tool:
        case Nothing():
            return Err(error=MediaError_ExternalToolMissing(name="ffmpeg"))
        case Some(value=selected_tool):
            tool = selected_tool

    if tool.executable == "":
        return Err(error=MediaError_ExternalToolMissing(name=tool.executable))
    if tool.input == Path() or tool.output == Path():
        return Err(error=MediaError_InvalidInput(message="external post-processing input and output must name files"))
    if tool.timeout_ms <= 0 or tool.timeout_ms > 4294967295:
        return Err(error=MediaError_InvalidInput(message="external post-processing timeout must be an unsigned 32-bit value greater than zero"))

    planned: list[ExternalToolRequest] = []
    kind_arguments: list[str]
    kind: PostProcessorKind_ExtractAudio | PostProcessorKind_RemuxVideo | PostProcessorKind_RecodeVideo | PostProcessorKind_EmbedSubtitle | PostProcessorKind_EmbedThumbnail | PostProcessorKind_EmbedMetadata | PostProcessorKind_SplitChapters | PostProcessorKind_ConvertThumbnails | PostProcessorKind_SponsorBlock | PostProcessorKind_Fixup
    for kind in request.kinds:
        match kind:
            case PostProcessorKind_ExtractAudio():
                if request.audio_format == "":
                    return Err(error=MediaError_InvalidInput(message="extracting audio requires an audio format"))
                kind_arguments = ["extract-audio", request.audio_format]
            case PostProcessorKind_RemuxVideo():
                if request.video_format == "":
                    return Err(error=MediaError_InvalidInput(message="remuxing video requires a video format"))
                kind_arguments = ["remux-video", request.video_format]
            case PostProcessorKind_RecodeVideo():
                if request.video_format == "":
                    return Err(error=MediaError_InvalidInput(message="recoding video requires a video format"))
                kind_arguments = ["recode-video", request.video_format]
            case PostProcessorKind_EmbedSubtitle():
                kind_arguments = ["embed-subtitle"]
            case PostProcessorKind_EmbedThumbnail():
                kind_arguments = ["embed-thumbnail"]
            case PostProcessorKind_EmbedMetadata():
                kind_arguments = ["embed-metadata"]
            case PostProcessorKind_SplitChapters():
                kind_arguments = ["split-chapters"]
            case PostProcessorKind_ConvertThumbnails():
                if request.video_format == "":
                    return Err(error=MediaError_InvalidInput(message="converting thumbnails requires a video format"))
                kind_arguments = ["convert-thumbnails", request.video_format]
            case PostProcessorKind_SponsorBlock():
                if len(request.sponsorblock_categories) == 0:
                    return Err(error=MediaError_InvalidInput(message="SponsorBlock requires at least one category"))
                category: str
                for category in request.sponsorblock_categories:
                    if category == "":
                        return Err(error=MediaError_InvalidInput(message="SponsorBlock categories must not be empty"))
                kind_arguments = ["sponsorblock", ",".join(request.sponsorblock_categories)]
            case PostProcessorKind_Fixup():
                kind_arguments = ["fixup"]

        arguments: list[str] = list(tool.arguments)
        arguments.extend(kind_arguments)
        planned.append(
            ExternalToolRequest(
                executable=tool.executable,
                arguments=CottList(values=tuple(arguments)),
                input=tool.input,
                output=tool.output,
                timeout_ms=tool.timeout_ms,
            )
        )

    return Ok(value=CottList(values=tuple(planned)))
