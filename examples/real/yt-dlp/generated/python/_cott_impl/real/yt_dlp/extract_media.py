import base64
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import PurePosixPath
from typing import Final

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import Authentication, AuthenticationKind_Anonymous, AuthenticationKind_BrowserCookies, AuthenticationKind_Cookies, AuthenticationKind_Credentials, AuthenticationKind_Netrc, ExtractorDescriptor, GeoBypassMode_Country, GeoBypassMode_Default, GeoBypassMode_Disabled, GeoBypassMode_IpBlock, MediaError, MediaError_AuthenticationFailed, MediaError_GeoRestricted, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_UnsupportedUrl, MediaItem, NetworkPolicy, ProxyMode_Direct, ProxyMode_Http, ProxyMode_Socks

_DEFAULT_TIMEOUT_S: Final[float] = 20.0


def _valid_http_url(url: str) -> bool:
    if url == "" or any(ch.isspace() or ord(ch) < 0x20 or ord(ch) == 0x7F for ch in url):
        return False
    try:
        parts = urllib.parse.urlsplit(url)
        host = parts.hostname
    except ValueError:
        return False
    return parts.scheme.lower() in ("http", "https") and host is not None and host != ""


def _extractor_accepts(url: str, extractor: ExtractorDescriptor) -> bool:
    if not extractor.enabled:
        return False
    if len(extractor.urls) == 0:
        return True
    for i in range(len(extractor.urls)):
        prefix: str = extractor.urls[i]
        if prefix != "" and url.startswith(prefix):
            return True
    return False


def _host_of(url: str) -> str:
    host = urllib.parse.urlsplit(url).hostname
    return host if host is not None else ""


def _basic_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def _auth_setup(extractor: ExtractorDescriptor, authentication: Authentication, headers: dict[str, str]) -> MediaError | None:
    match authentication.kind:
        case AuthenticationKind_Anonymous():
            if extractor.requires_login:
                return MediaError_AuthenticationFailed(message=f"extractor {extractor.name} requires login")
            return None
        case AuthenticationKind_Credentials():
            if authentication.username == "" or authentication.password == "":
                return MediaError_AuthenticationFailed(message="username and password are required")
            headers["Authorization"] = _basic_header(authentication.username, authentication.password)
            return None
        case AuthenticationKind_Netrc():
            return MediaError_AuthenticationFailed(message="netrc authentication requires file.read, which extract_media does not declare")
        case AuthenticationKind_Cookies():
            return MediaError_AuthenticationFailed(message="cookie-file authentication requires file.read, which extract_media does not declare")
        case AuthenticationKind_BrowserCookies():
            browser = authentication.browser.strip()
            if browser == "":
                return MediaError_AuthenticationFailed(message="browser name is required")
            return MediaError_AuthenticationFailed(message=f"browser cookie extraction unavailable for {browser}")


def _network_address(block: str) -> str | None:
    address, slash, prefix_text = block.partition("/")
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    try:
        packed = socket.inet_pton(family, address)
    except (OSError, ValueError):
        return None
    bits = len(packed) * 8
    prefix = bits
    if slash != "":
        if prefix_text == "" or not prefix_text.isascii() or not prefix_text.isdigit():
            return None
        prefix = int(prefix_text)
        if prefix > bits:
            return None
    mask = ((1 << bits) - 1) ^ ((1 << (bits - prefix)) - 1)
    network = int.from_bytes(packed, "big") & mask
    return socket.inet_ntop(family, network.to_bytes(len(packed), "big"))


def _geo_setup(network: NetworkPolicy, headers: dict[str, str]) -> MediaError | None:
    match network.geo_mode:
        case GeoBypassMode_Disabled():
            return None
        case GeoBypassMode_Default():
            return None
        case GeoBypassMode_Country():
            country = network.geo_country.strip()
            if len(country) != 2 or not country.isascii() or not country.isalpha():
                return MediaError_GeoRestricted(message="invalid geo bypass country code")
            return None
        case GeoBypassMode_IpBlock():
            address = _network_address(network.geo_ip_block.strip())
            if address is None:
                return MediaError_GeoRestricted(message="invalid geo bypass IP block")
            headers["X-Forwarded-For"] = address
            return None


def _network_setup(network: NetworkPolicy, headers: dict[str, str]) -> MediaError | None:
    if network.force_ipv4 and network.force_ipv6:
        return MediaError_NetworkFailure(message="cannot force both IPv4 and IPv6")
    match network.proxy_mode:
        case ProxyMode_Direct():
            return _geo_setup(network, headers)
        case ProxyMode_Http():
            if not _valid_http_url(network.proxy):
                return MediaError_NetworkFailure(message="invalid HTTP proxy")
            return _geo_setup(network, headers)
        case ProxyMode_Socks():
            return MediaError_NetworkFailure(message="SOCKS proxy is not supported")


def _item_from_url(final_url: str, content_type: str) -> MediaItem:
    path = PurePosixPath(urllib.parse.unquote(urllib.parse.urlsplit(final_url).path))
    name = path.name
    stem = path.stem if path.stem != "" else _host_of(final_url)
    ext = path.suffix[1:].lower() if path.suffix != "" else ""
    if ext == "":
        subtype = content_type.split(";", 1)[0].strip().lower().rpartition("/")[2]
        ext = subtype if subtype.isalnum() else "unknown_video"
    return MediaItem(url=final_url, id=stem, title=name if name != "" else stem, ext=ext, playlist_index=1)


def extract_media(url: str, extractor: ExtractorDescriptor, authentication: Authentication, network: NetworkPolicy) -> Result[CottList[MediaItem], MediaError]:
    target = url.strip()
    if not _valid_http_url(target) or not _extractor_accepts(target, extractor):
        return Err(error=MediaError_UnsupportedUrl())
    headers: dict[str, str] = {}
    auth_error = _auth_setup(extractor, authentication, headers)
    if auth_error is not None:
        return Err(error=auth_error)
    network_error = _network_setup(network, headers)
    if network_error is not None:
        return Err(error=network_error)
    timeout = network.socket_timeout_ms / 1000.0 if network.socket_timeout_ms > 0 else _DEFAULT_TIMEOUT_S
    request = urllib.request.Request(target, headers=headers, method="HEAD")
    if isinstance(network.proxy_mode, ProxyMode_Http):
        proxy_parts = urllib.parse.urlsplit(network.proxy)
        request.set_proxy(proxy_parts.netloc.rpartition("@")[2], proxy_parts.scheme.lower())
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            final_url: str = response.geturl()
            content_type: str = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        status: int = exc.code
        if status in (401, 403) and "Authorization" in headers:
            return Err(error=MediaError_AuthenticationFailed(message=f"HTTP {status}"))
        if status == 451:
            return Err(error=MediaError_GeoRestricted(message="HTTP 451"))
        return Err(error=MediaError_HttpStatus(status=status))
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLError):
            return Err(error=MediaError_NetworkFailure(message="TLS failure"))
        return Err(error=MediaError_NetworkFailure(message="connection failure"))
    except (TimeoutError, socket.timeout):
        return Err(error=MediaError_NetworkFailure(message="timeout"))
    except (OSError, ValueError):
        return Err(error=MediaError_NetworkFailure(message="transport failure"))
    if not _valid_http_url(final_url):
        return Err(error=MediaError_UnsupportedUrl())
    return Ok(value=CottList(values=[_item_from_url(final_url, content_type)]))
