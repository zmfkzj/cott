from pathlib import Path

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some
from real.yt_dlp_types import ExternalToolRequest, MediaError, MediaError_ExternalToolMissing, MediaError_InvalidInput, MediaItem, PostProcessRequest, PostProcessorKind, PostProcessorKind_ConvertThumbnails, PostProcessorKind_EmbedMetadata, PostProcessorKind_EmbedSubtitle, PostProcessorKind_EmbedThumbnail, PostProcessorKind_ExtractAudio, PostProcessorKind_Fixup, PostProcessorKind_RecodeVideo, PostProcessorKind_RemuxVideo, PostProcessorKind_SplitChapters, PostProcessorKind_SponsorBlock


def _protocol_args(kind: PostProcessorKind, request: PostProcessRequest) -> Result[list[str], MediaError]:
    match kind:
        case PostProcessorKind_ExtractAudio():
            if request.audio_format == "":
                return Err(error=MediaError_InvalidInput(message="extract-audio requires a nonempty audio_format"))
            return Ok(value=["extract-audio", request.audio_format])
        case PostProcessorKind_RemuxVideo():
            if request.video_format == "":
                return Err(error=MediaError_InvalidInput(message="remux-video requires a nonempty video_format"))
            return Ok(value=["remux-video", request.video_format])
        case PostProcessorKind_RecodeVideo():
            if request.video_format == "":
                return Err(error=MediaError_InvalidInput(message="recode-video requires a nonempty video_format"))
            return Ok(value=["recode-video", request.video_format])
        case PostProcessorKind_EmbedSubtitle():
            return Ok(value=["embed-subtitle"])
        case PostProcessorKind_EmbedThumbnail():
            return Ok(value=["embed-thumbnail"])
        case PostProcessorKind_EmbedMetadata():
            return Ok(value=["embed-metadata"])
        case PostProcessorKind_SplitChapters():
            return Ok(value=["split-chapters"])
        case PostProcessorKind_ConvertThumbnails():
            if request.video_format == "":
                return Err(error=MediaError_InvalidInput(message="convert-thumbnails requires a nonempty video_format"))
            return Ok(value=["convert-thumbnails", request.video_format])
        case PostProcessorKind_SponsorBlock():
            if len(request.sponsorblock_categories) == 0 or any(category == "" for category in request.sponsorblock_categories):
                return Err(error=MediaError_InvalidInput(message="sponsorblock requires a nonempty list of nonempty categories"))
            return Ok(value=["sponsorblock", ",".join(request.sponsorblock_categories)])
        case PostProcessorKind_Fixup():
            return Ok(value=["fixup"])


def plan_post_processing(item: MediaItem, request: PostProcessRequest) -> Result[CottList[ExternalToolRequest], MediaError]:
    if len(request.kinds) == 0:
        empty: CottList[ExternalToolRequest] = CottList(values=[])
        return Ok(value=empty)
    match request.external_tool:
        case Nothing():
            return Err(error=MediaError_ExternalToolMissing(name="ffmpeg"))
        case Some(value=tool):
            if tool.executable == "":
                return Err(error=MediaError_ExternalToolMissing(name=tool.executable))
            if tool.input == Path("."):
                return Err(error=MediaError_InvalidInput(message="external tool input must not be the current directory"))
            if tool.output == Path("."):
                return Err(error=MediaError_InvalidInput(message="external tool output must not be the current directory"))
            if tool.timeout_ms == 0:
                return Err(error=MediaError_InvalidInput(message="external tool timeout_ms must be nonzero"))
            planned: list[ExternalToolRequest] = []
            for kind in request.kinds:
                match _protocol_args(kind, request):
                    case Err(error=error):
                        return Err(error=error)
                    case Ok(value=extra):
                        planned.append(ExternalToolRequest(
                            executable=tool.executable,
                            arguments=CottList(values=[*tool.arguments, *extra]),
                            input=tool.input,
                            output=tool.output,
                            timeout_ms=tool.timeout_ms,
                        ))
            return Ok(value=CottList(values=planned))
