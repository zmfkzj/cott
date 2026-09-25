from cott_runtime import CottList, Err, Ok, Result
from real.posting.client import parse_method
from real.posting.client_types import PostingError, PostingError_InvalidArguments, Request


def parse_arguments(arguments: CottList[str]) -> Result[Request, PostingError]:
    values: list[str] = [argument for argument in arguments]
    if len(values) < 2 or len(values) > 3:
        return Err(error=PostingError_InvalidArguments(message="usage: METHOD URL [BODY]"))
    method = parse_method(values[0])
    if isinstance(method, Err):
        return Err(error=method.error)
    body = values[2] if len(values) == 3 else ""
    return Ok(value=Request(method=method.value, url=values[1], headers=CottList(values=[]), body=body, timeout_ms=30000))
