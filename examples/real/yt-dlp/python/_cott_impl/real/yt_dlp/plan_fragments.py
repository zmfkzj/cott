from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import FragmentPolicy, MediaError, MediaError_InvalidInput, TransferRequest


def plan_fragments(request: TransferRequest, policy: FragmentPolicy) -> Result[CottList[TransferRequest], MediaError]:
    if request.max_bytes == 0:
        return Err(error=MediaError_InvalidInput(message="max_bytes must be positive"))
    if policy.concurrent_fragments == 0:
        return Err(error=MediaError_InvalidInput(message="concurrent_fragments must be positive"))
    if policy.buffer_size == 0:
        return Err(error=MediaError_InvalidInput(message="buffer_size must be positive"))
    return Ok(value=CottList(values=[request]))
