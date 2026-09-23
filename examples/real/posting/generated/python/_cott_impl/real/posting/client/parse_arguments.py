from cott_runtime import CottList, Err, Ok, Result
from real.posting.client_types import HttpMethod, HttpMethod_Custom, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, PostingError, PostingError_InvalidArguments, PostingError_InvalidRequest, Request


def _parse_method(name: str) -> HttpMethod:
    upper = name.upper()
    if upper == "GET":
        return HttpMethod_Get()
    if upper == "HEAD":
        return HttpMethod_Head()
    if upper == "POST":
        return HttpMethod_Post()
    if upper == "PUT":
        return HttpMethod_Put()
    if upper == "PATCH":
        return HttpMethod_Patch()
    if upper == "DELETE":
        return HttpMethod_Delete()
    if upper == "OPTIONS":
        return HttpMethod_Options()
    return HttpMethod_Custom(name=name)


def parse_arguments(arguments: CottList[str]) -> Result[Request, PostingError]:
    values: list[str] = [argument for argument in arguments]
    if len(values) < 2 or len(values) > 3:
        return Err(error=PostingError_InvalidArguments(message="usage: METHOD URL [BODY]"))
    method_name = values[0]
    url = values[1]
    if method_name == "":
        return Err(error=PostingError_InvalidRequest(message="method must not be empty"))
    if url == "":
        return Err(error=PostingError_InvalidRequest(message="url must not be empty"))
    body = values[2] if len(values) == 3 else ""
    return Ok(value=Request(method=_parse_method(method_name), url=url, headers=CottList(values=[]), body=body, timeout_ms=30000))
