from pathlib import Path

from cott_runtime import Err, Ok, Result
from real.posting.client_types import HttpMethod, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, PostingError, PostingError_InvalidRequest


def parse_method(value: str) -> Result[HttpMethod, PostingError]:
    if value == "GET":
        return Ok(value=HttpMethod_Get())
    if value == "POST":
        return Ok(value=HttpMethod_Post())
    if value == "PUT":
        return Ok(value=HttpMethod_Put())
    if value == "PATCH":
        return Ok(value=HttpMethod_Patch())
    if value == "DELETE":
        return Ok(value=HttpMethod_Delete())
    if value == "HEAD":
        return Ok(value=HttpMethod_Head())
    if value == "OPTIONS":
        return Ok(value=HttpMethod_Options())
    return Err(error=PostingError_InvalidRequest(path=Path("."), message="unsupported HTTP method: " + value))
