from __future__ import annotations

from cott_runtime import Err, JsonObject, JsonString, JsonValue, Ok, Result
from curriculum.json_transform_types import (
    JsonTransformError,
    JsonTransformError_MissingField,
    JsonTransformError_NotAnObject,
)

def extract_string_field(payload: JsonValue, field: str) -> Result[str, JsonTransformError]:
    if not isinstance(payload, JsonObject):
        return Err(error=JsonTransformError_NotAnObject())
    raw_val = payload.value.get(field)
    if raw_val is None or not isinstance(raw_val, JsonString):
        return Err(error=JsonTransformError_MissingField(field_name=field))
    return Ok(value=raw_val.value)
