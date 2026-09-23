from typing import Final

from cott_runtime import Err, Ok, Result
from real.yt_dlp_types import MediaError, MediaError_UpdateUnavailable, UpdatePolicy, UpdatePolicy_Apply, UpdatePolicy_Check, UpdatePolicy_Master, UpdatePolicy_Never, UpdatePolicy_Nightly

_STABLE: Final[str] = "yt-dlp/yt-dlp"
_NIGHTLY: Final[str] = "yt-dlp/yt-dlp-nightly-builds"
_MASTER: Final[str] = "yt-dlp/yt-dlp-master-builds"


def resolve_update_repository(policy: UpdatePolicy, channel: str) -> Result[str, MediaError]:
    match policy:
        case UpdatePolicy_Never():
            return Ok(value="")
        case UpdatePolicy_Nightly():
            return Ok(value=_NIGHTLY)
        case UpdatePolicy_Master():
            return Ok(value=_MASTER)
        case UpdatePolicy_Check() | UpdatePolicy_Apply():
            name: str = channel.strip()
            if name == "" or name == "stable":
                return Ok(value=_STABLE)
            if name == "nightly":
                return Ok(value=_NIGHTLY)
            if name == "master":
                return Ok(value=_MASTER)
            return Err(error=MediaError_UpdateUnavailable(message="unknown update channel"))
