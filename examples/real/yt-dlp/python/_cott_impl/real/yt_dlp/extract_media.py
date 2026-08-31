from base64 import b64encode
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import (
    Authentication,
    AuthenticationKind_Anonymous,
    AuthenticationKind_BrowserCookies,
    AuthenticationKind_Cookies,
    AuthenticationKind_Credentials,
    AuthenticationKind_Netrc,
    ExtractorDescriptor,
    MediaError,
    MediaError_AuthenticationFailed,
    MediaError_GeoRestricted,
    MediaError_HttpStatus,
    MediaError_NetworkFailure,
    MediaError_UnsupportedUrl,
    MediaItem,
    NetworkPolicy,
)


def extract_media(url: str, extractor: ExtractorDescriptor, authentication: Authentication, network: NetworkPolicy) -> Result[CottList[MediaItem], MediaError]:
    if url == "" or not (url.startswith("http://") or url.startswith("https://")):
        return Err(error=MediaError_UnsupportedUrl())
    if not extractor.enabled:
        return Err(error=MediaError_UnsupportedUrl())

    supported: bool = False
    prefix: str
    for prefix in extractor.urls:
        if url.startswith(prefix):
            supported = True
            break
    if not supported:
        return Err(error=MediaError_UnsupportedUrl())
    if network.socket_timeout_ms == 0:
        return Err(error=MediaError_NetworkFailure(message="socket timeout must be greater than zero"))

    headers: dict[str, str] = {}
    match authentication.kind:
        case AuthenticationKind_Anonymous():
            if (
                authentication.username != ""
                or authentication.password != ""
                or authentication.netrc_location != Path()
                or authentication.cookie_file != Path()
                or authentication.browser != ""
                or authentication.profile != ""
            ):
                return Err(error=MediaError_AuthenticationFailed(message="anonymous authentication cannot include authentication details"))
            if extractor.requires_login:
                return Err(error=MediaError_AuthenticationFailed(message=f"extractor requires authentication: {extractor.name}"))
        case AuthenticationKind_Credentials():
            if authentication.username == "" or authentication.password == "":
                return Err(error=MediaError_AuthenticationFailed(message="credential authentication requires a username and password"))
            if (
                authentication.netrc_location != Path()
                or authentication.cookie_file != Path()
                or authentication.browser != ""
                or authentication.profile != ""
            ):
                return Err(error=MediaError_AuthenticationFailed(message="credential authentication cannot include netrc or cookie settings"))
            credentials: bytes = f"{authentication.username}:{authentication.password}".encode("utf-8")
            headers["Authorization"] = f"Basic {b64encode(credentials).decode('ascii')}"
        case AuthenticationKind_Netrc():
            if authentication.netrc_location == Path():
                return Err(error=MediaError_AuthenticationFailed(message="netrc authentication requires a netrc location"))
            if (
                authentication.username != ""
                or authentication.password != ""
                or authentication.cookie_file != Path()
                or authentication.browser != ""
                or authentication.profile != ""
            ):
                return Err(error=MediaError_AuthenticationFailed(message="netrc authentication cannot include credentials or cookie settings"))
        case AuthenticationKind_Cookies():
            if authentication.cookie_file == Path():
                return Err(error=MediaError_AuthenticationFailed(message="cookie authentication requires a cookie file"))
            if (
                authentication.username != ""
                or authentication.password != ""
                or authentication.netrc_location != Path()
                or authentication.browser != ""
                or authentication.profile != ""
            ):
                return Err(error=MediaError_AuthenticationFailed(message="cookie authentication cannot include credentials, netrc, or browser settings"))
        case AuthenticationKind_BrowserCookies():
            if authentication.browser == "":
                return Err(error=MediaError_AuthenticationFailed(message="browser cookie authentication requires a browser"))
            if (
                authentication.username != ""
                or authentication.password != ""
                or authentication.netrc_location != Path()
                or authentication.cookie_file != Path()
            ):
                return Err(error=MediaError_AuthenticationFailed(message="browser cookie authentication cannot include credentials, netrc, or a cookie file"))

    request: Request = Request(url=url, headers=headers, method="HEAD")
    with urlopen(request, timeout=network.socket_timeout_ms / 1000.0) as response:
        status: int = response.status
        final_url: str = response.geturl()

    if status == 401 or status == 403 or status == 407:
        return Err(error=MediaError_AuthenticationFailed(message=f"authentication was rejected with HTTP status {status}"))
    if status == 451:
        return Err(error=MediaError_GeoRestricted(message="media is unavailable from the selected geographic route"))
    if status <= 0:
        return Err(error=MediaError_NetworkFailure(message="network response did not include a valid HTTP status"))
    if status < 200 or status >= 400:
        return Err(error=MediaError_HttpStatus(status=status))
    if final_url == "" or not (final_url.startswith("http://") or final_url.startswith("https://")):
        return Err(error=MediaError_UnsupportedUrl())

    path: str = urlsplit(final_url).path.rstrip("/")
    filename: str = unquote(path.rsplit("/", 1)[-1])
    if filename == "":
        identifier: str = extractor.name
        extension: str = ""
    else:
        stem: str
        separator: str
        stem, separator, extension = filename.rpartition(".")
        if separator == "" or stem == "":
            identifier = filename
            extension = ""
        else:
            identifier = stem
    item: MediaItem = MediaItem(url=final_url, id=identifier, title=identifier, ext=extension, playlist_index=1)
    return Ok(value=CottList(values=(item,)))
