from foo.bar_types import OutputPayload, PayloadFormat, PayloadSize


def build_output(data: bytes, source_size: PayloadSize, format: PayloadFormat) -> OutputPayload:
    return OutputPayload(data=data, source_size=source_size, format=format)
