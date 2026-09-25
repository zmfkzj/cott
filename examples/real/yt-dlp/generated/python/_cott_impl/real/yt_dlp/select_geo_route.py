from typing import Final

from cott_runtime import Err, Ok, Result
from real.yt_dlp_types import GeoBypassMode_Country, GeoBypassMode_Default, GeoBypassMode_Disabled, GeoBypassMode_IpBlock, MediaError, MediaError_GeoRestricted, NetworkPolicy

_DIGITS: Final[str] = "0123456789"
_HEX: Final[str] = "0123456789abcdefABCDEF"


def _parse_decimal(text: str, maximum: int) -> bool:
    if text == "" or len(text) > 3 or any(c not in _DIGITS for c in text):
        return False
    if len(text) > 1 and text[0] == "0":
        return False
    return int(text) <= maximum


def _valid_ipv4(text: str) -> bool:
    octets: list[str] = text.split(".")
    if len(octets) != 4:
        return False
    return all(_parse_decimal(octet, 255) for octet in octets)


def _valid_hextets(groups: list[str]) -> bool:
    return all(0 < len(g) <= 4 and all(c in _HEX for c in g) for g in groups)


def _valid_ipv6(text: str) -> bool:
    if text == "":
        return False
    tail_count: int = 0
    body: str = text
    last_colon: int = text.rfind(":")
    if last_colon != -1 and "." in text[last_colon + 1:]:
        if not _valid_ipv4(text[last_colon + 1:]):
            return False
        tail_count = 2
        body = text[: last_colon + 1]
        if not body.endswith("::"):
            body = body[:-1]
    if body.count("::") > 1:
        return False
    if "::" in body:
        left, right = body.split("::", 1)
        left_groups: list[str] = left.split(":") if left else []
        right_groups: list[str] = right.split(":") if right else []
        if not _valid_hextets(left_groups) or not _valid_hextets(right_groups):
            return False
        return len(left_groups) + len(right_groups) + tail_count <= 7
    groups: list[str] = body.split(":") if body else []
    return _valid_hextets(groups) and len(groups) + tail_count == 8


def _valid_prefix(text: str, maximum: int) -> bool:
    if text == "" or any(c not in _DIGITS for c in text):
        return False
    significant: str = text.lstrip("0")
    if len(significant) > 3:
        return False
    return significant == "" or int(significant) <= maximum


def _valid_ip_block(block: str) -> bool:
    if block == "" or block != block.strip():
        return False
    address, sep, prefix = block.partition("/")
    if ":" in address:
        if not _valid_ipv6(address):
            return False
        return not sep or _valid_prefix(prefix, 128)
    if not _valid_ipv4(address):
        return False
    return not sep or _valid_prefix(prefix, 32)


def select_geo_route(policy: NetworkPolicy) -> Result[NetworkPolicy, MediaError]:
    match policy.geo_mode:
        case GeoBypassMode_Disabled() | GeoBypassMode_Default():
            return Ok(value=policy)
        case GeoBypassMode_Country():
            return Err(error=MediaError_GeoRestricted(message="country geo-bypass is not supported"))
        case GeoBypassMode_IpBlock():
            if not _valid_ip_block(policy.geo_ip_block):
                return Err(error=MediaError_GeoRestricted(message="invalid geo-bypass IP block"))
            return Ok(value=policy)
