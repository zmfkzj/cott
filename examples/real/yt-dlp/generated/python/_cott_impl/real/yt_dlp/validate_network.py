import socket
from urllib.parse import urlsplit

from cott_runtime import Err, Ok, Result
from real.yt_dlp_types import GeoBypassMode_Country, GeoBypassMode_Default, GeoBypassMode_Disabled, GeoBypassMode_IpBlock, MediaError, MediaError_InvalidInput, NetworkPolicy, ProxyMode_Direct, ProxyMode_Http, ProxyMode_Socks


def _invalid(message: str) -> Result[NetworkPolicy, MediaError]:
    return Err(error=MediaError_InvalidInput(message=message))


def _ip_version(text: str) -> int:
    if not text or not text.isascii():
        return 0
    for family, version in ((socket.AF_INET, 4), (socket.AF_INET6, 6)):
        try:
            socket.inet_pton(family, text)
        except (OSError, ValueError):
            continue
        return version
    return 0


def _valid_ip_block(block: str) -> bool:
    address, slash, prefix = block.partition("/")
    version: int = _ip_version(address)
    if version == 0:
        return False
    if not slash:
        return True
    if not prefix or not prefix.isascii() or not prefix.isdecimal():
        return False
    significant: str = prefix.lstrip("0")
    if len(significant) > 3:
        return False
    return int(significant or "0") <= (32 if version == 4 else 128)


def _valid_proxy(proxy: str, http: bool) -> bool:
    if not proxy or any(ch.isspace() or ord(ch) < 32 or 127 <= ord(ch) <= 159 for ch in proxy):
        return False
    try:
        parts = urlsplit(proxy)
        port: int | None = parts.port
        host: str | None = parts.hostname
    except ValueError:
        return False
    if http:
        if parts.scheme not in ("http", "https"):
            return False
    elif parts.scheme not in ("socks4", "socks4a", "socks5", "socks5h"):
        return False
    return bool(host) and not parts.netloc.endswith(":") and (port is None or port > 0)


def validate_network(policy: NetworkPolicy) -> Result[NetworkPolicy, MediaError]:
    if policy.socket_timeout_ms == 0:
        return _invalid("socket timeout must be positive")
    if policy.force_ipv4 and policy.force_ipv6:
        return _invalid("force_ipv4 and force_ipv6 are mutually exclusive")
    match policy.proxy_mode:
        case ProxyMode_Direct():
            if policy.proxy:
                return _invalid("direct mode does not accept a proxy")
        case ProxyMode_Http():
            if not _valid_proxy(policy.proxy, True):
                return _invalid("invalid HTTP proxy URL")
        case ProxyMode_Socks():
            if not _valid_proxy(policy.proxy, False):
                return _invalid("invalid SOCKS proxy URL")
    if policy.source_address:
        version: int = _ip_version(policy.source_address)
        if version == 0:
            return _invalid("invalid source address")
        if policy.force_ipv4 and version != 4:
            return _invalid("source address conflicts with force_ipv4")
        if policy.force_ipv6 and version != 6:
            return _invalid("source address conflicts with force_ipv6")
    match policy.geo_mode:
        case GeoBypassMode_Disabled() | GeoBypassMode_Default():
            if policy.geo_country or policy.geo_ip_block:
                return _invalid("geo country and IP block require their geo bypass mode")
        case GeoBypassMode_Country():
            if policy.geo_ip_block or len(policy.geo_country) != 2 or not policy.geo_country.isascii() or not policy.geo_country.isalpha():
                return _invalid("geo country must be two ASCII letters")
        case GeoBypassMode_IpBlock():
            if policy.geo_country or not _valid_ip_block(policy.geo_ip_block):
                return _invalid("invalid geo IP block")
    return Ok(value=policy)
