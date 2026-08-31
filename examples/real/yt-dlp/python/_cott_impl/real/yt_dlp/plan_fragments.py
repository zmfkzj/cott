from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import (
    FragmentPolicy,
    MediaError,
    MediaError_InvalidInput,
    MediaError_SizeLimit,
    TransferRequest,
)


def plan_fragments(request: TransferRequest, policy: FragmentPolicy) -> Result[CottList[TransferRequest], MediaError]:
    if request.url == "":
        return Err(error=MediaError_InvalidInput(message="transfer URL must not be empty"))
    if request.max_bytes <= 0 or request.max_bytes > 18446744073709551615:
        return Err(error=MediaError_InvalidInput(message="maximum bytes must be an unsigned 64-bit value greater than zero"))
    if policy.concurrent_fragments <= 0 or policy.concurrent_fragments > 65535:
        return Err(error=MediaError_InvalidInput(message="concurrent fragments must be an unsigned 16-bit value greater than zero"))
    if policy.buffer_size <= 0 or policy.buffer_size > 4294967295:
        return Err(error=MediaError_InvalidInput(message="buffer size must be an unsigned 32-bit value greater than zero"))
    if policy.chunk_size <= 0 or policy.chunk_size > 4294967295:
        return Err(error=MediaError_InvalidInput(message="chunk size must be an unsigned 32-bit value greater than zero"))
    if policy.rate_limit_bytes_per_second < 0 or policy.rate_limit_bytes_per_second > 18446744073709551615:
        return Err(error=MediaError_InvalidInput(message="rate limit must be an unsigned 64-bit value"))
    if policy.retries < 0 or policy.retries > 4294967295:
        return Err(error=MediaError_InvalidInput(message="retries must be an unsigned 32-bit value"))
    if policy.fragment_retries < 0 or policy.fragment_retries > 4294967295:
        return Err(error=MediaError_InvalidInput(message="fragment retries must be an unsigned 32-bit value"))
    if policy.file_access_retries < 0 or policy.file_access_retries > 4294967295:
        return Err(error=MediaError_InvalidInput(message="file access retries must be an unsigned 32-bit value"))

    fragment_count: int = ((request.max_bytes - 1) // policy.chunk_size) + 1
    if fragment_count > 100000:
        return Err(error=MediaError_SizeLimit())

    fragments: list[TransferRequest] = []
    remaining: int = request.max_bytes
    while remaining > 0:
        fragment_size: int = min(remaining, policy.chunk_size)
        fragments.append(
            TransferRequest(
                url=request.url,
                destination=request.destination,
                simulate=request.simulate,
                max_bytes=fragment_size,
            )
        )
        remaining -= fragment_size

    return Ok(value=CottList(values=tuple(fragments)))
