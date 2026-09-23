from cott_runtime import CottList, Ok, Result
from real.yt_dlp_types import FragmentPolicy, MediaError, TransferRequest


def plan_fragments(request: TransferRequest, policy: FragmentPolicy) -> Result[CottList[TransferRequest], MediaError]:
    return Ok(value=CottList(values=[request]))
