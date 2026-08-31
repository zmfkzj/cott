from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp import transfer_media
from real.yt_dlp_types import (
    FragmentPolicy,
    MediaError,
    MediaError_HttpStatus,
    MediaError_InvalidInput,
    MediaError_NetworkFailure,
    MediaError_OutputFailure,
    MediaError_RetryExhausted,
    TransferReceipt,
    TransferRequest,
)


def transfer_fragments(fragments: CottList[TransferRequest], policy: FragmentPolicy) -> Result[CottList[TransferReceipt], MediaError]:
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

    receipts: list[TransferReceipt] = []
    fragment: TransferRequest
    for fragment in fragments:
        transfer_attempts: int = 0
        file_access_attempts: int = 0
        transferred: bool = False
        while not transferred:
            match transfer_media(fragment):
                case Ok(value=receipt):
                    receipts.append(receipt)
                    transferred = True
                case Err(error=error):
                    match error:
                        case MediaError_NetworkFailure():
                            transfer_attempts += 1
                            if transfer_attempts > policy.fragment_retries:
                                return Err(error=MediaError_RetryExhausted(attempts=transfer_attempts))
                        case MediaError_HttpStatus(status=status):
                            if status != 408 and status != 429 and (status < 500 or status >= 600):
                                return Err(error=error)
                            transfer_attempts += 1
                            if transfer_attempts > policy.fragment_retries:
                                return Err(error=MediaError_RetryExhausted(attempts=transfer_attempts))
                        case MediaError_OutputFailure():
                            file_access_attempts += 1
                            if file_access_attempts > policy.file_access_retries:
                                return Err(error=error)
                        case _:
                            return Err(error=error)

    return Ok(value=CottList(values=tuple(receipts)))
