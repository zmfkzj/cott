from cott_runtime import CottList, Err, Ok, Result
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


def parse_arguments(arguments: CottList[str]) -> Result[Request, PostingError]:
    argument_count = len(arguments)
    if argument_count < 2 or argument_count > 3:
        return Err(error=PostingError_InvalidArguments(message="expected METHOD URL [BODY]"))

    method_source = arguments[0]
    if len(method_source) == 0:
        return Err(error=PostingError_InvalidRequest(message="HTTP method must not be empty"))

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

    body = arguments[2] if argument_count == 3 else ""
    return Ok(
        value=Request(
            method=method,
            url=arguments[1],
            headers=CottList(values=()),
            body=body,
            timeout_ms=30000,
        )
    )
