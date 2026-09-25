import base64
import http.client
import socket
import ssl
import urllib.parse
from pathlib import PurePosixPath
from typing import Final

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import Authentication, AuthenticationKind_Anonymous, AuthenticationKind_BrowserCookies, AuthenticationKind_Cookies, AuthenticationKind_Credentials, AuthenticationKind_Netrc, ExtractorDescriptor, GeoBypassMode_Country, GeoBypassMode_Default, GeoBypassMode_Disabled, GeoBypassMode_IpBlock, MediaError, MediaError_AuthenticationFailed, MediaError_GeoRestricted, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_UnsupportedUrl, MediaItem, NetworkPolicy, ProxyMode_Direct, ProxyMode_Http, ProxyMode_Socks

_DEFAULT_TIMEOUT_S: Final[float] = 20.0
_MAX_REDIRECTS: Final[int] = 5


def _valid_http_url(url: str) -> bool:
    if url == "" or any(ch.isspace() or ord(ch) < 0x20 or ord(ch) == 0x7F for ch in url):
        return False
    try:
        parts = urllib.parse.urlsplit(url)
        host = parts.hostname
        _ = parts.port
    except ValueError:
        return False
    return parts.scheme in ("http", "https") and host is not None and host != ""


def _extractor_accepts(url: str, extractor: ExtractorDescriptor) -> bool:
    if not extractor.enabled:
        return False
    for i in range(len(extractor.urls)):
        prefix: str = extractor.urls[i]
        if prefix != "" and url.startswith(prefix):
            return True
    return False


def _host_of(url: str) -> str:
    host = urllib.parse.urlsplit(url).hostname
    return host if host is not None else ""


def _auth_setup(extractor: ExtractorDescriptor, authentication: Authentication, headers: dict[str, str]) -> MediaError | None:
    match authentication.kind:
        case AuthenticationKind_Anonymous():
            if extractor.requires_login:
                return MediaError_AuthenticationFailed(message="extractor requires login")
            return None
        case AuthenticationKind_Credentials():
            if authentication.username == "" or authentication.password == "":
                return MediaError_AuthenticationFailed(message="username and password are required")
            token = base64.b64encode(f"{authentication.username}:{authentication.password}".encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {token}"
            return None
        case AuthenticationKind_Netrc():
            return MediaError_AuthenticationFailed(message="netrc authentication is not supported")
        case AuthenticationKind_Cookies():
            return MediaError_AuthenticationFailed(message="cookie authentication is not supported")
        case AuthenticationKind_BrowserCookies():
            return MediaError_AuthenticationFailed(message="browser cookie authentication is not supported")


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
    network_int = int.from_bytes(packed, "big") & mask
    return socket.inet_ntop(family, network_int.to_bytes(len(packed), "big"))


def _geo_setup(network: NetworkPolicy, headers: dict[str, str]) -> MediaError | None:
    match network.geo_mode:
        case GeoBypassMode_Disabled():
            return None
        case GeoBypassMode_Default():
            return None
        case GeoBypassMode_Country():
            return MediaError_GeoRestricted(message="country geo bypass is not supported")
        case GeoBypassMode_IpBlock():
            address = _network_address(network.geo_ip_block.strip())
            if address is None:
                return MediaError_GeoRestricted(message="invalid geo bypass IP block")
            headers["X-Forwarded-For"] = address
            return None


def _network_setup(network: NetworkPolicy, headers: dict[str, str]) -> MediaError | None:
    match network.proxy_mode:
        case ProxyMode_Direct():
            return _geo_setup(network, headers)
        case ProxyMode_Http():
            if not _valid_http_url(network.proxy) or not network.proxy.startswith("http://"):
                return MediaError_NetworkFailure(message="invalid HTTP proxy")
            return _geo_setup(network, headers)
        case ProxyMode_Socks():
            return MediaError_NetworkFailure(message="SOCKS proxy is not supported")


def _item_from_url(final_url: str, content_type: str) -> MediaItem:
    path = PurePosixPath(urllib.parse.unquote(urllib.parse.urlsplit(final_url).path))
    name = path.name
    if name == "":
        host = _host_of(final_url)
        title = host
        stem = host
        ext = ""
    else:
        title = name
        stem = path.stem
        ext = path.suffix[1:].lower()
    if ext == "":
        subtype = content_type.split(";", 1)[0].strip().lower().rpartition("/")[2]
        ext = subtype if subtype != "" and subtype.isascii() and subtype.isalnum() else "unknown_video"
    return MediaItem(url=final_url, id=stem, title=title, ext=ext, playlist_index=1)


def _open(target: str, network: NetworkPolicy, timeout: float, context: ssl.SSLContext) -> tuple[http.client.HTTPConnection, str]:
    parts = urllib.parse.urlsplit(target)
    host = parts.hostname if parts.hostname is not None else ""
    port = parts.port if parts.port is not None else (443 if parts.scheme == "https" else 80)
    path = urllib.parse.urlunsplit(("", "", parts.path if parts.path != "" else "/", parts.query, ""))
    if isinstance(network.proxy_mode, ProxyMode_Http):
        proxy = urllib.parse.urlsplit(network.proxy)
        proxy_host = proxy.hostname if proxy.hostname is not None else ""
        proxy_port = proxy.port if proxy.port is not None else 80
        if parts.scheme == "https":
            tunnel = http.client.HTTPSConnection(proxy_host, proxy_port, timeout=timeout, context=context)
            tunnel.set_tunnel(host, port)
            return tunnel, path
        conn = http.client.HTTPConnection(proxy_host, proxy_port, timeout=timeout)
        return conn, urllib.parse.urlunsplit((parts.scheme, parts.netloc.rpartition("@")[2], parts.path if parts.path != "" else "/", parts.query, ""))
    if parts.scheme == "https":
        return http.client.HTTPSConnection(host, port, timeout=timeout, context=context), path
    return http.client.HTTPConnection(host, port, timeout=timeout), path


def extract_media(url: str, extractor: ExtractorDescriptor, authentication: Authentication, network: NetworkPolicy) -> Result[CottList[MediaItem], MediaError]:
    if not _valid_http_url(url) or not _extractor_accepts(url, extractor):
        return Err(error=MediaError_UnsupportedUrl())
    headers: dict[str, str] = {}
    auth_error = _auth_setup(extractor, authentication, headers)
    if auth_error is not None:
        return Err(error=auth_error)
    network_error = _network_setup(network, headers)
    if network_error is not None:
        return Err(error=network_error)
    timeout = network.socket_timeout_ms / 1000.0 if network.socket_timeout_ms > 0 else _DEFAULT_TIMEOUT_S
    context = ssl.create_default_context()
    origin_host = _host_of(url)
    current = url
    redirects = 0
    while True:
        request_headers = dict(headers)
        if _host_of(current) != origin_host:
            request_headers.pop("Authorization", None)
        try:
            conn, target = _open(current, network, timeout, context)
            try:
                conn.request("HEAD", target, headers=request_headers)
                response = conn.getresponse()
                status: int = response.status
                location = response.getheader("Location")
                content_type = response.getheader("Content-Type", "") or ""
            finally:
                conn.close()
        except ssl.SSLError:
            return Err(error=MediaError_NetworkFailure(message="TLS failure"))
        except (TimeoutError, socket.timeout):
            return Err(error=MediaError_NetworkFailure(message="timeout"))
        except socket.gaierror:
            return Err(error=MediaError_NetworkFailure(message="DNS failure"))
        except OSError:
            return Err(error=MediaError_NetworkFailure(message="connection failure"))
        except (http.client.HTTPException, ValueError):
            return Err(error=MediaError_NetworkFailure(message="transport failure"))
        if status in (301, 302, 303, 307, 308) and location is not None and location.strip() != "":
            if redirects >= _MAX_REDIRECTS:
                return Err(error=MediaError_NetworkFailure(message="redirect limit exceeded"))
            redirects += 1
            next_url = urllib.parse.urljoin(current, location.strip())
            next_url = urllib.parse.urldefrag(next_url)[0]
            if not _valid_http_url(next_url):
                return Err(error=MediaError_NetworkFailure(message="invalid redirect"))
            current = next_url
            continue
        if 200 <= status < 300:
            return Ok(value=CottList(values=[_item_from_url(current, content_type)]))
        if status in (401, 403) and "Authorization" in request_headers:
            return Err(error=MediaError_AuthenticationFailed(message=f"HTTP {status}"))
        if status == 451:
            return Err(error=MediaError_GeoRestricted(message="HTTP 451"))
        return Err(error=MediaError_HttpStatus(status=status))
