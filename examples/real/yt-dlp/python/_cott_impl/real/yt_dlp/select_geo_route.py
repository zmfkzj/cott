import socket

import cott_runtime
from cott_runtime import Result
from real.yt_dlp_types import GeoBypassMode_Country, GeoBypassMode_Default, GeoBypassMode_Disabled, GeoBypassMode_IpBlock, MediaError, MediaError_GeoRestricted, NetworkPolicy


def _valid_ip_block(block: str) -> bool:
    address, separator, prefix = block.partition("/")
    if not address or "%" in address:
        return False
    width: int
    try:
        socket.inet_pton(socket.AF_INET, address)
        width = 32
    except OSError:
        try:
            socket.inet_pton(socket.AF_INET6, address)
            width = 128
        except OSError:
            return False
    if not separator:
        return True
    if not prefix or any(digit not in "0123456789" for digit in prefix):
        return False
    significant = prefix.lstrip("0")
    return len(significant) <= 3 and int(significant or "0") <= width


def select_geo_route(policy: NetworkPolicy) -> Result[NetworkPolicy, MediaError]:
    match policy.geo_mode:
        case GeoBypassMode_Disabled() | GeoBypassMode_Default():
            return cott_runtime.Ok(value=policy)
        case GeoBypassMode_Country():
            return cott_runtime.Err(error=MediaError_GeoRestricted(message="country geo-bypass is not supported"))
        case GeoBypassMode_IpBlock():
            if not _valid_ip_block(policy.geo_ip_block):
                return cott_runtime.Err(error=MediaError_GeoRestricted(message="invalid geo-bypass IP block"))
            return cott_runtime.Ok(value=policy)
