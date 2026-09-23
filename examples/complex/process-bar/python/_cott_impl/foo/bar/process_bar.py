from cott_runtime import Err, Ok, Result
from foo.bar import build_output, process_payload_bytes, validate_payload
from foo.bar_types import BarError, BarOptions, InputPayload, OutputPayload


def process_bar(data: InputPayload, options: BarOptions) -> Result[OutputPayload, BarError]:
    validated = validate_payload(data)
    if isinstance(validated, Err):
        return validated
    processed = process_payload_bytes(validated.value.data, options)
    if isinstance(processed, Err):
        return processed
    return Ok(value=build_output(processed.value, data.declared_size, data.format))
