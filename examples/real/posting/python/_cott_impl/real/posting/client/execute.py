from cott_runtime import CottList, Err, Ok, Result
from real.posting.client import send_request
from real.posting.client_types import (
    HttpMethod,
    HttpMethod_Custom,
    HttpMethod_Delete,
    HttpMethod_Get,
    HttpMethod_Head,
    HttpMethod_Options,
    HttpMethod_Patch,
    HttpMethod_Post,
    HttpMethod_Put,
    PostingError,
    PostingError_InvalidArguments,
    PostingError_InvalidRequest,
    Request,
)


def execute(arguments: CottList[str]) -> Result[str, PostingError]:
    if len(arguments) < 2 or len(arguments) > 3:
        return Err(error=PostingError_InvalidArguments(message="expected METHOD URL [BODY]"))

    method_source = ""
    url = ""
    body = ""
    argument_index = 0
    for argument in arguments:
        if argument_index == 0:
            method_source = argument
        elif argument_index == 1:
            url = argument
        else:
            body = argument
        argument_index += 1
    if len(method_source) == 0:
        return Err(error=PostingError_InvalidRequest(message="HTTP method cannot be empty"))

    normalized_method = method_source.upper()
    method: HttpMethod
    if normalized_method == "GET":
        method = HttpMethod_Get()
    elif normalized_method == "HEAD":
        method = HttpMethod_Head()
    elif normalized_method == "POST":
        method = HttpMethod_Post()
    elif normalized_method == "PUT":
        method = HttpMethod_Put()
    elif normalized_method == "PATCH":
        method = HttpMethod_Patch()
    elif normalized_method == "DELETE":
        method = HttpMethod_Delete()
    elif normalized_method == "OPTIONS":
        method = HttpMethod_Options()
    else:
        method = HttpMethod_Custom(name=method_source)

    request = Request(
        method=method,
        url=url,
        headers=CottList(values=()),
        body=body,
        timeout_ms=30_000,
    )
    match send_request(request):
        case Err(error=error):
            return Err(error=error)
        case Ok(value=response):
            header_lines = "".join(
                f"{header.name}: {header.value}\n" for header in response.headers
            )
            rendered = (
                f"{response.status} {response.url}\n"
                f"{header_lines}\n"
                f"{response.body}"
            )
            return Ok(value=rendered)
