from cott_runtime import Err, Ok, Result
from foo.bar import build_output
from foo.bar_types import BarError, BarError_InvalidPayload, BarOptions, InputPayload, OutputPayload


def process_bar(data: InputPayload, options: BarOptions) -> Result[OutputPayload, BarError]:
    if len(data.data) == 0:
        return Err(error=BarError_InvalidPayload(reason="payload data must not be empty"))
    return Ok(value=build_output(data=data.data, source_size=data.declared_size, format=data.format))
