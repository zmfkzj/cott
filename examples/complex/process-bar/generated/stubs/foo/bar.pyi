from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from foo.bar_types import BarError as BarError, BarError_InvalidPayload as BarError_InvalidPayload, BarOptions as BarOptions, InputPayload as InputPayload, MAX_PAYLOAD_SIZE as MAX_PAYLOAD_SIZE, OutputPayload as OutputPayload, PayloadFormat as PayloadFormat, PayloadFormat_Raw as PayloadFormat_Raw, PayloadFormat_Structured as PayloadFormat_Structured, PayloadFormat_Text as PayloadFormat_Text, PayloadSize as PayloadSize, Probability as Probability
"""Reject a payload without bytes. declared_size is caller-supplied metadata
carried to the output; it is not compared with the byte count."""
def validate_payload(data: InputPayload) -> Result[InputPayload, BarError]: ...

"""The byte-processing stage of this fixture is the identity: it always
succeeds with the input bytes, whatever the options."""
def process_payload_bytes(data: bytes, options: BarOptions) -> Result[bytes, BarError]: ...

"""Construct output from processed bytes and the original payload metadata."""
def build_output(data: bytes, source_size: PayloadSize, format: PayloadFormat) -> OutputPayload: ...

"""Domain-named operation of the fixture: validate the payload, process its
bytes, then build the output from the processed bytes and the validated
metadata."""
def process_bar(data: InputPayload, options: BarOptions) -> Result[OutputPayload, BarError]: ...

__all__ = ["BarError", "BarError_InvalidPayload", "BarOptions", "InputPayload", "MAX_PAYLOAD_SIZE", "OutputPayload", "PayloadFormat", "PayloadFormat_Raw", "PayloadFormat_Structured", "PayloadFormat_Text", "PayloadSize", "Probability", "build_output", "process_bar", "process_payload_bytes", "validate_payload"]
