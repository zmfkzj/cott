from cott_runtime import Err, JsonObject, JsonString, JsonValue, Ok, Result
from curriculum.json_transform_types import JsonTransformError, JsonTransformError_MissingField, JsonTransformError_NotAnObject, StringField


def extract_string_field(payload: JsonValue, field: str) -> Result[StringField, JsonTransformError]:
    if not isinstance(payload, JsonObject):
        return Err(error=JsonTransformError_NotAnObject())
    entry = payload.value.get(field)
    if not isinstance(entry, JsonString):
        return Err(error=JsonTransformError_MissingField(field_name=field))
    return Ok(value=StringField(name=field, text=entry.value))
