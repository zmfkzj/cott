from cott_runtime import Err, Ok, Result
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
    PostingError_InvalidRequest,
)


def parse_method(source: str) -> Result[HttpMethod, PostingError]:
    if source == "":
        return Err(error=PostingError_InvalidRequest(message="HTTP method must not be empty"))
    normalized = source.upper()
    if normalized == "GET":
        return Ok(value=HttpMethod_Get())
    if normalized == "HEAD":
        return Ok(value=HttpMethod_Head())
    if normalized == "POST":
        return Ok(value=HttpMethod_Post())
    if normalized == "PUT":
        return Ok(value=HttpMethod_Put())
    if normalized == "PATCH":
        return Ok(value=HttpMethod_Patch())
    if normalized == "DELETE":
        return Ok(value=HttpMethod_Delete())
    if normalized == "OPTIONS":
        return Ok(value=HttpMethod_Options())
    return Ok(value=HttpMethod_Custom(name=source))
