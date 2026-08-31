from cott_runtime import Err, Ok, Result
from real.yt_dlp_types import (
    GeoBypassMode_Country,
    GeoBypassMode_Default,
    GeoBypassMode_Disabled,
    GeoBypassMode_IpBlock,
    MediaError,
    MediaError_InvalidInput,
    NetworkPolicy,
    ProxyMode_Direct,
    ProxyMode_Http,
    ProxyMode_Socks,
)


def validate_network(policy: NetworkPolicy) -> Result[NetworkPolicy, MediaError]:
    if policy.socket_timeout_ms == 0:
        return Err(error=MediaError_InvalidInput(message="socket timeout must be greater than zero"))
    if policy.force_ipv4 and policy.force_ipv6:
        return Err(error=MediaError_InvalidInput(message="IPv4 and IPv6 cannot both be forced"))
    if policy.source_address != "" and (policy.force_ipv4 or policy.force_ipv6):
        return Err(error=MediaError_InvalidInput(message="source address cannot be combined with a forced IP version"))

    match policy.proxy_mode:
        case ProxyMode_Direct():
            if policy.proxy != "":
                return Err(error=MediaError_InvalidInput(message="direct proxy mode requires an empty proxy"))
        case ProxyMode_Http():
            if not (policy.proxy.startswith("http://") or policy.proxy.startswith("https://")):
                return Err(error=MediaError_InvalidInput(message="HTTP proxy mode requires an HTTP or HTTPS proxy URL"))
        case ProxyMode_Socks():
            if not (
                policy.proxy.startswith("socks4://")
                or policy.proxy.startswith("socks4a://")
                or policy.proxy.startswith("socks5://")
                or policy.proxy.startswith("socks5h://")
            ):
                return Err(error=MediaError_InvalidInput(message="SOCKS proxy mode requires a SOCKS proxy URL"))

    match policy.geo_mode:
        case GeoBypassMode_Disabled() | GeoBypassMode_Default():
            if policy.geo_country != "" or policy.geo_ip_block != "":
                return Err(error=MediaError_InvalidInput(message="default or disabled geo bypass cannot specify a route"))
        case GeoBypassMode_Country():
            if policy.geo_country == "" or policy.geo_ip_block != "":
                return Err(error=MediaError_InvalidInput(message="country geo bypass requires only a country"))
        case GeoBypassMode_IpBlock():
            if policy.geo_ip_block == "" or policy.geo_country != "":
                return Err(error=MediaError_InvalidInput(message="IP block geo bypass requires only an IP block"))

    return Ok(value=policy)
