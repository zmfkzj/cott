from cott_runtime import Ok, Result
from real.yt_dlp_types import MediaError, WorkaroundPolicy


def validate_workarounds(policy: WorkaroundPolicy) -> Result[WorkaroundPolicy, MediaError]:
    return Ok(value=policy)
