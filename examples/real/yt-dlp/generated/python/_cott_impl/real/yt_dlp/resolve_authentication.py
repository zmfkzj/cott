from pathlib import Path

from cott_runtime import Err, Ok, Result, _cott_fixture_read
from real.yt_dlp_types import (
    Authentication,
    AuthenticationKind_Anonymous,
    AuthenticationKind_BrowserCookies,
    AuthenticationKind_Cookies,
    AuthenticationKind_Credentials,
    AuthenticationKind_Netrc,
    MediaError,
    MediaError_AuthenticationFailed,
    MediaError_CookieFailure,
)


def resolve_authentication(request: Authentication) -> Result[Authentication, MediaError]:
    match request.kind:
        case AuthenticationKind_Anonymous():
            if (
                request.username != ""
                or request.password != ""
                or request.netrc_location != Path()
                or request.cookie_file != Path()
                or request.browser != ""
                or request.profile != ""
            ):
                return Err(error=MediaError_AuthenticationFailed(message="anonymous authentication cannot include authentication details"))
        case AuthenticationKind_Credentials():
            if request.username == "" or request.password == "":
                return Err(error=MediaError_AuthenticationFailed(message="credential authentication requires a username and password"))
            if request.netrc_location != Path() or request.cookie_file != Path() or request.browser != "" or request.profile != "":
                return Err(error=MediaError_AuthenticationFailed(message="credential authentication cannot include netrc or cookie settings"))
        case AuthenticationKind_Netrc():
            if request.netrc_location == Path():
                return Err(error=MediaError_AuthenticationFailed(message="netrc authentication requires a netrc location"))
            if request.username != "" or request.password != "" or request.cookie_file != Path() or request.browser != "" or request.profile != "":
                return Err(error=MediaError_AuthenticationFailed(message="netrc authentication cannot include credentials or cookie settings"))
            if _cott_fixture_read(request.netrc_location).strip() == b"":
                return Err(error=MediaError_AuthenticationFailed(message="netrc file must not be empty"))
        case AuthenticationKind_Cookies():
            if request.cookie_file == Path():
                return Err(error=MediaError_CookieFailure(message="cookie authentication requires a cookie file"))
            if request.username != "" or request.password != "" or request.netrc_location != Path() or request.browser != "" or request.profile != "":
                return Err(error=MediaError_CookieFailure(message="cookie authentication cannot include credentials, netrc, or browser settings"))
            if _cott_fixture_read(request.cookie_file).strip() == b"":
                return Err(error=MediaError_CookieFailure(message="cookie file must not be empty"))
        case AuthenticationKind_BrowserCookies():
            if request.browser == "":
                return Err(error=MediaError_CookieFailure(message="browser cookie authentication requires a browser"))
            if request.username != "" or request.password != "" or request.netrc_location != Path() or request.cookie_file != Path():
                return Err(error=MediaError_CookieFailure(message="browser cookie authentication cannot include credentials, netrc, or a cookie file"))

    return Ok(value=request)
