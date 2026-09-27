import base64
import http.client
import socket
import ssl
import urllib.parse
from typing import Final

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import Authentication, AuthenticationKind_Anonymous, AuthenticationKind_BrowserCookies, AuthenticationKind_Cookies, AuthenticationKind_Credentials, AuthenticationKind_Netrc, ExtractorDescriptor, GeoBypassMode_Country, GeoBypassMode_Default, GeoBypassMode_Disabled, GeoBypassMode_IpBlock, MediaError, MediaError_AuthenticationFailed, MediaError_GeoRestricted, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_UnsupportedUrl, MediaItem, NetworkPolicy, ProxyMode_Direct, ProxyMode_Http, ProxyMode_Socks

_MAX_REDIRECTS: Final[int] = 5


def _valid_url(url: str) -> bool:
    if not url.startswith(("http://", "https://")) or any(ch.isspace() or ord(ch) < 32 or 127 <= ord(ch) <= 159 for ch in url):
        return False
    try:
        parts = urllib.parse.urlsplit(url)
        return bool(parts.hostname) and (parts.port is None or 0 <= parts.port <= 65535)
    except ValueError:
        return False


def _origin(url: str) -> tuple[str, str | None, int]:
    parts = urllib.parse.urlsplit(url)
    return parts.scheme, parts.hostname, parts.port if parts.port is not None else (443 if parts.scheme == "https" else 80)


def _network_address(block: str) -> str:
    address, slash, prefix_text = block.partition("/")
    try:
        packed = socket.inet_pton(socket.AF_INET, address)
        family = socket.AF_INET
    except OSError:
        packed = socket.inet_pton(socket.AF_INET6, address)
        family = socket.AF_INET6
    width = len(packed) * 8
    if slash:
        if not prefix_text.isascii() or not prefix_text.isdecimal():
            raise ValueError("invalid IP block prefix")
        prefix = int(prefix_text)
    else:
        prefix = width
    if prefix > width:
        raise ValueError("invalid IP block prefix")
    mask = ((1 << prefix) - 1) << (width - prefix)
    network_address = (int.from_bytes(packed, "big") & mask).to_bytes(len(packed), "big")
    return socket.inet_ntop(family, network_address)


def _connection(url: str, proxy_url: str, timeout: float, context: ssl.SSLContext) -> tuple[http.client.HTTPConnection, str]:
    parts = urllib.parse.urlsplit(url)
    host = parts.hostname or ""
    port = parts.port if parts.port is not None else (443 if parts.scheme == "https" else 80)
    target = urllib.parse.urlunsplit(("", "", parts.path or "/", parts.query, ""))
    if proxy_url:
        proxy = urllib.parse.urlsplit(proxy_url)
        proxy_host = proxy.hostname or ""
        proxy_port = proxy.port if proxy.port is not None else 80
        if parts.scheme == "https":
            tunnel = http.client.HTTPSConnection(proxy_host, proxy_port, timeout=timeout, context=context)
            tunnel.set_tunnel(host, port)
            return tunnel, target
        absolute_target = urllib.parse.urlunsplit((parts.scheme, parts.netloc.rpartition("@")[2], parts.path or "/", parts.query, ""))
        return http.client.HTTPConnection(proxy_host, proxy_port, timeout=timeout), absolute_target
    if parts.scheme == "https":
        return http.client.HTTPSConnection(host, port, timeout=timeout, context=context), target
    return http.client.HTTPConnection(host, port, timeout=timeout), target


def _item(url: str, content_type: str) -> MediaItem:
    parts = urllib.parse.urlsplit(url)
    segment = parts.path.rsplit("/", 1)[-1]
    title = urllib.parse.unquote(segment) if segment else (parts.hostname or "")
    stem, dot, extension = title.rpartition(".")
    if dot and extension:
        identifier = stem
        ext = extension.lower()
    else:
        identifier = title
        mime_type = content_type.split(";", 1)[0].strip().lower()
        _, separator, subtype = mime_type.partition("/")
        ext = subtype if separator and subtype.isascii() and subtype.isalnum() else "unknown_video"
    return MediaItem(url=url, id=identifier, title=title, ext=ext, playlist_index=1)


def extract_media(url: str, extractor: ExtractorDescriptor, authentication: Authentication, network: NetworkPolicy) -> Result[CottList[MediaItem], MediaError]:
    if not _valid_url(url) or not extractor.enabled or not any(prefix and url.startswith(prefix) for prefix in extractor.urls):
        return Err(error=MediaError_UnsupportedUrl())

    match authentication.kind:
        case AuthenticationKind_Anonymous():
            if extractor.requires_login:
                return Err(error=MediaError_AuthenticationFailed(message="extractor requires login"))
            authorization = None
        case AuthenticationKind_Credentials():
            if not authentication.username or not authentication.password:
                return Err(error=MediaError_AuthenticationFailed(message="username and password are required"))
            token = base64.b64encode(f"{authentication.username}:{authentication.password}".encode("utf-8")).decode("ascii")
            authorization = f"Basic {token}"
        case AuthenticationKind_Netrc() | AuthenticationKind_Cookies() | AuthenticationKind_BrowserCookies():
            return Err(error=MediaError_AuthenticationFailed(message="authentication mode is not supported"))

    match network.proxy_mode:
        case ProxyMode_Socks():
            return Err(error=MediaError_NetworkFailure(message="SOCKS proxy is not supported"))
        case ProxyMode_Http():
            if not network.proxy.startswith("http://") or not _valid_url(network.proxy):
                return Err(error=MediaError_NetworkFailure(message="invalid HTTP proxy"))
            proxy_url = network.proxy
        case ProxyMode_Direct():
            proxy_url = ""

    match network.geo_mode:
        case GeoBypassMode_Country():
            return Err(error=MediaError_GeoRestricted(message="country geo bypass is not supported"))
        case GeoBypassMode_IpBlock():
            try:
                forwarding = _network_address(network.geo_ip_block)
            except (OSError, ValueError):
                return Err(error=MediaError_GeoRestricted(message="invalid geo bypass IP block"))
        case GeoBypassMode_Default() | GeoBypassMode_Disabled():
            forwarding = None

    headers: dict[str, str] = {}
    if authorization is not None:
        headers["Authorization"] = authorization
    if forwarding is not None:
        headers["X-Forwarded-For"] = forwarding

    timeout = network.socket_timeout_ms / 1000.0
    try:
        context = ssl.create_default_context()
    except (OSError, ValueError):
        return Err(error=MediaError_NetworkFailure(message="request failed"))
    current = url
    redirects = 0
    while True:
        request_headers = headers if authorization is None or _origin(current) == _origin(url) else {key: value for key, value in headers.items() if key != "Authorization"}
        try:
            conn, target = _connection(current, proxy_url, timeout, context)
            try:
                conn.request("HEAD", target, headers=request_headers)
                response = conn.getresponse()
                status = response.status
                location = response.getheader("Location")
                content_type = response.getheader("Content-Type") or ""
            finally:
                conn.close()
        except (OSError, TimeoutError, http.client.HTTPException, ValueError):
            return Err(error=MediaError_NetworkFailure(message="request failed"))

        if status in (301, 302, 303, 307, 308) and location:
            if redirects >= _MAX_REDIRECTS:
                return Err(error=MediaError_NetworkFailure(message="redirect limit exceeded"))
            try:
                next_url = urllib.parse.urldefrag(urllib.parse.urljoin(current, location))[0]
            except ValueError:
                return Err(error=MediaError_NetworkFailure(message="invalid redirect"))
            if not _valid_url(next_url):
                return Err(error=MediaError_NetworkFailure(message="invalid redirect"))
            current = next_url
            redirects += 1
            continue
        if 200 <= status < 300:
            return Ok(value=CottList(values=[_item(current, content_type)]))
        if status in (401, 403) and "Authorization" in request_headers:
            return Err(error=MediaError_AuthenticationFailed(message="credentials rejected"))
        if status == 451:
            return Err(error=MediaError_GeoRestricted(message="HTTP 451"))
        return Err(error=MediaError_HttpStatus(status=status))
