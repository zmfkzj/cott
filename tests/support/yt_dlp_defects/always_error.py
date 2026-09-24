from cott_runtime import Err, Result
from real.yt_dlp_types import ExecutionReport, ExecutionRequest, MediaError, MediaError_NetworkFailure


def execute(request: ExecutionRequest) -> Result[ExecutionReport, MediaError]:
    """Defect: returns a declared transport failure for every request, including valid input."""
    return Err(error=MediaError_NetworkFailure(message=f"media service unavailable for {len(request.inputs)} inputs"))
