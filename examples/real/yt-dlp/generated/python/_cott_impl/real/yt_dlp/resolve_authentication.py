import cott_runtime
from cott_runtime import Result
from real.yt_dlp_types import Authentication, AuthenticationKind_Anonymous, AuthenticationKind_BrowserCookies, AuthenticationKind_Cookies, AuthenticationKind_Credentials, AuthenticationKind_Netrc, MediaError, MediaError_AuthenticationFailed, MediaError_CookieFailure


def resolve_authentication(request: Authentication) -> Result[Authentication, MediaError]:
    match request.kind:
        case AuthenticationKind_Anonymous():
            return cott_runtime.Ok(value=request)
        case AuthenticationKind_Credentials():
            if len(request.username) == 0 or len(request.password) == 0:
                return cott_runtime.Err(error=MediaError_AuthenticationFailed(message="credentials require a nonempty username and password"))
            return cott_runtime.Ok(value=request)
        case AuthenticationKind_Netrc():
            return cott_runtime.Err(error=MediaError_AuthenticationFailed(message="netrc authentication is not supported"))
        case AuthenticationKind_Cookies():
            return cott_runtime.Err(error=MediaError_CookieFailure(message="cookie file authentication is not supported"))
        case AuthenticationKind_BrowserCookies():
            return cott_runtime.Err(error=MediaError_CookieFailure(message="browser cookie authentication is not supported"))
