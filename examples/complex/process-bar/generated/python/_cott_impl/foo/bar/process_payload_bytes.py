from cott_runtime import Ok, Result
from foo.bar_types import BarError, BarOptions


def process_payload_bytes(data: bytes, options: BarOptions) -> Result[bytes, BarError]:
    return Ok(value=data)
