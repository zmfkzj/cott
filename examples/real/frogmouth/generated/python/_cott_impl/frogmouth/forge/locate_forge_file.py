import http.client
import urllib.error
import urllib.parse
import urllib.request
from typing import Final

from cott_runtime import CottList, Err, Ok, Result
from frogmouth.forge_types import ForgeError, ForgeError_Unresolved
from frogmouth.model_types import Forge, Location, LocationKind_Remote

_USER_AGENT: Final[str] = "frogmouth v0.9.1"
_TIMEOUT_SECONDS: Final[float] = 5.0
_MAX_REDIRECTS: Final[int] = 10


def _build_opener() -> urllib.request.OpenerDirector:
    # No HTTPRedirectHandler: stdlib redirects rebuild the request as GET, so redirects are followed here to keep the method.
    opener = urllib.request.OpenerDirector()
    opener.add_handler(urllib.request.HTTPHandler())
    opener.add_handler(urllib.request.HTTPSHandler())
    opener.add_handler(urllib.request.HTTPDefaultErrorHandler())
    opener.add_handler(urllib.request.HTTPErrorProcessor())
    return opener


def _probe_status(opener: urllib.request.OpenerDirector, url: str, method: str) -> int:
    current = url
    redirects = 0
    while True:
        request = urllib.request.Request(current, headers={"User-Agent": _USER_AGENT}, method=method)
        try:
            # The timeout becomes the socket timeout, bounding the connect and every read.
            with opener.open(request, timeout=_TIMEOUT_SECONDS) as response:
                return int(response.status)
        except urllib.error.HTTPError as error:
            status = int(error.code)
            location = error.headers.get("Location")
            error.close()
        if status not in (301, 302, 303, 307, 308) or location is None or redirects >= _MAX_REDIRECTS:
            return status
        target = urllib.parse.urljoin(current, location)
        if urllib.parse.urlsplit(target).scheme not in ("http", "https"):
            return status
        current = target
        redirects += 1


def locate_forge_file(forge: Forge, candidates: CottList[str]) -> Result[Location, ForgeError]:
    opener = _build_opener()
    for candidate in candidates:
        try:
            status = _probe_status(opener, candidate, "HEAD")
            if status == 405 or status == 501:
                status = _probe_status(opener, candidate, "GET")
        except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError):
            break
        if 200 <= status <= 299:
            return Ok(value=Location(kind=LocationKind_Remote(), target=candidate))
    return Err(error=ForgeError_Unresolved(forge=forge))
