from cott_runtime import Err, Ok, Result
from real.posting.client_types import HttpMethod, HttpMethod_Custom, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, PostingError, PostingError_InvalidRequest


def parse_method(source: str) -> Result[HttpMethod, PostingError]:
    if len(source) == 0:
        return Err(error=PostingError_InvalidRequest(message="HTTP method must not be empty"))
    match source.upper():
        case "GET":
            return Ok(value=HttpMethod_Get())
        case "HEAD":
            return Ok(value=HttpMethod_Head())
        case "POST":
            return Ok(value=HttpMethod_Post())
        case "PUT":
            return Ok(value=HttpMethod_Put())
        case "PATCH":
            return Ok(value=HttpMethod_Patch())
        case "DELETE":
            return Ok(value=HttpMethod_Delete())
        case "OPTIONS":
            return Ok(value=HttpMethod_Options())
        case _:
            return Ok(value=HttpMethod_Custom(name=source))
