from cott_runtime import Ok, Result
from real.yt_dlp_types import MediaError, NetworkPolicy


def select_geo_route(policy: NetworkPolicy) -> Result[NetworkPolicy, MediaError]:
    return Ok(value=policy)
