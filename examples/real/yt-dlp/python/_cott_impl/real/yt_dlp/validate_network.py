import socket
from typing import Final
from urllib.parse import urlsplit

from cott_runtime import Err, Ok, Result
from real.yt_dlp_types import GeoBypassMode_Country, GeoBypassMode_Default, GeoBypassMode_Disabled, GeoBypassMode_IpBlock, MediaError, MediaError_InvalidInput, NetworkPolicy, ProxyMode_Direct, ProxyMode_Http, ProxyMode_Socks

_HTTP_SCHEMES: Final[str] = "http https"
_SOCKS_SCHEMES: Final[str] = "socks4 socks4a socks5 socks5h"


def _invalid(message: str) -> Result[NetworkPolicy, MediaError]:
    return Err(error=MediaError_InvalidInput(message=message))


def _parses_as(family: int, text: str) -> bool:
    try:
        socket.inet_pton(family, text)
    except (OSError, ValueError):
        return False
    return True


def _ip_version(text: str) -> int:
    if text == "" or not text.isascii():
        return 0
    if _parses_as(socket.AF_INET, text):
        return 4
    if _parses_as(socket.AF_INET6, text):
        return 6
    return 0


def _valid_ip_block(block: str) -> bool:
    address, sep, prefix = block.partition("/")
    version: int = _ip_version(address)
    if version == 0:
        return False
    if not sep:
        return True
    if prefix != "" and prefix.isascii() and prefix.isdigit():
        return int(prefix) <= (32 if version == 4 else 128)
    return False


def _valid_proxy(proxy: str, schemes: str) -> bool:
    if proxy == "" or any(ch.isspace() or ord(ch) < 0x20 or ord(ch) == 0x7F for ch in proxy):
        return False
    try:
        parts = urlsplit(proxy)
        port = parts.port
    except ValueError:
        return False
    if parts.netloc.endswith(":"):
        return False
    return parts.scheme in schemes.split(" ") and (parts.hostname or "") != "" and (port is None or port > 0)


def validate_network(policy: NetworkPolicy) -> Result[NetworkPolicy, MediaError]:
    if policy.socket_timeout_ms == 0:
        return _invalid("socket timeout must be positive")
    if policy.force_ipv4 and policy.force_ipv6:
        return _invalid("force_ipv4 and force_ipv6 are mutually exclusive")
    match policy.proxy_mode:
        case ProxyMode_Direct():
            if policy.proxy != "":
                return _invalid("direct mode does not accept a proxy")
        case ProxyMode_Http():
            if not _valid_proxy(policy.proxy, _HTTP_SCHEMES):
                return _invalid("invalid HTTP proxy URL")
        case ProxyMode_Socks():
            if not _valid_proxy(policy.proxy, _SOCKS_SCHEMES):
                return _invalid("invalid SOCKS proxy URL")
    if policy.source_address != "":
        version: int = _ip_version(policy.source_address)
        if version == 0:
            return _invalid("invalid source address")
        if policy.force_ipv4 and version != 4:
            return _invalid("source address conflicts with force_ipv4")
        if policy.force_ipv6 and version != 6:
            return _invalid("source address conflicts with force_ipv6")
    match policy.geo_mode:
        case GeoBypassMode_Disabled() | GeoBypassMode_Default():
            if policy.geo_country != "" or policy.geo_ip_block != "":
                return _invalid("geo country and IP block require their geo bypass mode")
        case GeoBypassMode_Country():
            if policy.geo_ip_block != "" or len(policy.geo_country) != 2 or not policy.geo_country.isascii() or not policy.geo_country.isalpha():
                return _invalid("geo country must be two ASCII letters")
        case GeoBypassMode_IpBlock():
            if policy.geo_country != "" or not _valid_ip_block(policy.geo_ip_block):
                return _invalid("invalid geo IP block")
    return Ok(value=policy)
