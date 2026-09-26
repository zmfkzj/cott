import codecs
import http.client
import urllib.error
import urllib.request
from typing import Final

from cott_runtime import Err, Ok, Result
from frogmouth.document_types import LoadError, LoadError_RemoteFailed, RemoteDocument, RemoteDocument_Markdown, RemoteDocument_NotMarkdown
from frogmouth.model_types import Document, Location, LocationKind_Remote

_USER_AGENT: Final[str] = "frogmouth v0.9.1"
_TIMEOUT: Final[float] = 5.0
_LOOP_PREFIX: Final[str] = "The HTTP server returned a redirect error that would lead to an infinite loop."


def _status_kind(status: int) -> str:
    if 100 <= status < 200:
        return "Informational response"
    if 300 <= status < 400:
        return "Redirect response"
    if 400 <= status < 500:
        return "Client error"
    if 500 <= status < 600:
        return "Server error"
    return "Invalid status code"


def _status_message(status: int, reason: str, final_url: str) -> str:
    return (
        f"{_status_kind(status)} '{status} {reason}' for url '{final_url}'\n"
        f"For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/{status}"
    )


def _codec_name(charset: str | None) -> str:
    if charset:
        try:
            return codecs.lookup(charset).name
        except LookupError:
            return "utf-8"
    return "utf-8"


def fetch_remote_document(url: str) -> Result[RemoteDocument, LoadError]:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
            status = response.status
            reason = str(response.reason)
            final_url = response.geturl() or url
            content_type = response.headers.get("Content-Type", "") or ""
            charset = response.headers.get_content_charset()
            body = response.read()
    except urllib.error.HTTPError as error:
        error_reason = str(error.reason)
        if error_reason.startswith(_LOOP_PREFIX):
            return Err(error=LoadError_RemoteFailed(url=url, message=error_reason))
        return Err(error=LoadError_RemoteFailed(url=url, message=_status_message(error.code, error_reason, error.url or url)))
    except urllib.error.URLError as error:
        return Err(error=LoadError_RemoteFailed(url=url, message=str(error.reason)))
    except (http.client.HTTPException, OSError, ValueError) as error:
        return Err(error=LoadError_RemoteFailed(url=url, message=str(error) or repr(error)))
    if not 200 <= status < 300:
        return Err(error=LoadError_RemoteFailed(url=url, message=_status_message(status, reason, final_url)))
    if not (
        content_type.startswith("text/plain")
        or content_type.startswith("text/markdown")
        or content_type.startswith("text/x-markdown")
    ):
        return Ok(value=RemoteDocument_NotMarkdown(content_type=content_type))
    markdown = body.decode(_codec_name(charset), errors="replace")
    location = Location(kind=LocationKind_Remote(), target=url)
    return Ok(value=RemoteDocument_Markdown(document=Document(location=location, markdown=markdown)))
