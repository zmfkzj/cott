from cott_runtime import Err, Ok, Result
from foo.bar import build_output, process_payload_bytes, validate_payload
from foo.bar_types import BarError, BarOptions, InputPayload, OutputPayload


def process_bar(data: InputPayload, options: BarOptions) -> Result[OutputPayload, BarError]:
    match validate_payload(data):
        case Err(error=error):
            return Err(error=error)
        case Ok(value=validated):
            match process_payload_bytes(validated.data, options):
                case Err(error=error):
                    return Err(error=error)
                case Ok(value=processed):
                    return Ok(
                        value=build_output(
                            processed,
                            validated.declared_size,
                            validated.format,
                        )
                    )
