from cott_runtime import Err, Ok, Result
from foo.bar_types import BarError, BarError_InvalidPayload, InputPayload


def validate_payload(data: InputPayload) -> Result[InputPayload, BarError]:
    if len(data.data) == 0:
        return Err(error=BarError_InvalidPayload(reason="payload data must not be empty"))
    return Ok(value=data)
