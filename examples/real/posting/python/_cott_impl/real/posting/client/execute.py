from cott_runtime import CottList, Err, Ok, Result
from real.posting.client import parse_arguments, render_response, send_request
from real.posting.client_types import PostingError


def execute(arguments: CottList[str]) -> Result[str, PostingError]:
    parsed = parse_arguments(arguments)
    if isinstance(parsed, Err):
        return parsed
    sent = send_request(parsed.value)
    if isinstance(sent, Err):
        return sent
    return Ok(value=render_response(sent.value))
