from pathlib import Path

from cott_runtime import CottList, Err, Ok, Result, UNIT, Unit, _cott_fixture_read, _cott_fixture_write
from real.yt_dlp_types import (
    ExternalToolRequest,
    MediaError,
    MediaError_ExternalToolMissing,
    MediaError_PostProcessFailed,
)


def run_post_processing(requests: CottList[ExternalToolRequest]) -> Result[Unit, MediaError]:
    request: ExternalToolRequest
    for request in requests:
        if request.executable == "":
            return Err(error=MediaError_ExternalToolMissing(name=request.executable))
        if request.input == Path() or request.output == Path():
            return Err(
                error=MediaError_PostProcessFailed(
                    name=request.executable,
                    message="external post-processing input and output must name files",
                )
            )
        if request.timeout_ms <= 0 or request.timeout_ms > 4294967295:
            return Err(
                error=MediaError_PostProcessFailed(
                    name=request.executable,
                    message="external post-processing timeout must be an unsigned 32-bit value greater than zero",
                )
            )

        content: bytes = _cott_fixture_read(request.input)
        _cott_fixture_write(request.output, content)

    return Ok(value=UNIT)
