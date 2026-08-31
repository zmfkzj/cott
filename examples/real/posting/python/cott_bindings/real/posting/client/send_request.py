from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from cott_runtime import CottList, Err, Ok, Result
from real.posting.client_types import (
    Header,
    HttpMethod,
    HttpMethod_Delete,
    HttpMethod_Get,
    HttpMethod_Head,
    HttpMethod_Options,
    HttpMethod_Patch,
    HttpMethod_Post,
    HttpMethod_Put,
    PostingError,
    PostingError_InvalidRequest,
    PostingError_NetworkFailed,
    Request,
    Response,
)


def _method_name(method: HttpMethod) -> str:
    if isinstance(method, HttpMethod_Get):
        return "GET"
    if isinstance(method, HttpMethod_Head):
        return "HEAD"
    if isinstance(method, HttpMethod_Post):
        return "POST"
    if isinstance(method, HttpMethod_Put):
        return "PUT"
    if isinstance(method, HttpMethod_Patch):
        return "PATCH"
    if isinstance(method, HttpMethod_Delete):
        return "DELETE"
    if isinstance(method, HttpMethod_Options):
        return "OPTIONS"
    return method.name


def _response(status: int, url: str, headers: list[tuple[str, str]], body: bytes) -> Response:
    return Response(
        status=status,
        url=url,
        headers=CottList(values=(Header(name=name, value=value) for name, value in headers)),
        body=body.decode("utf-8", errors="replace"),
    )


def send_request(request: Request) -> Result[Response, PostingError]:
    if not request.url.startswith(("http://", "https://")):
        return Err(error=PostingError_InvalidRequest(message="URL must use HTTP or HTTPS"))
    body = request.body.encode() or None
    outgoing = UrlRequest(
        request.url,
        data=body,
        headers={header.name: header.value for header in request.headers},
        method=_method_name(request.method),
    )
    try:
        with urlopen(outgoing, timeout=request.timeout_ms / 1000) as incoming:
            return Ok(
                value=_response(
                    incoming.status,
                    incoming.url,
                    list(incoming.headers.items()),
                    incoming.read(),
                )
            )
    except HTTPError as error:
        return Ok(
            value=_response(error.code, error.url, list(error.headers.items()), error.read())
        )
    except (URLError, TimeoutError, ValueError) as error:
        return Err(error=PostingError_NetworkFailed(message=str(error)))
