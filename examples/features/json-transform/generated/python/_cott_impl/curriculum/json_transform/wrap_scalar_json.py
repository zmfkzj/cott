from __future__ import annotations

from cott_runtime import FrozenMap, JsonObject, JsonString, JsonValue

def wrap_scalar_json(key: str, value: str) -> JsonValue:
    return JsonObject(value=FrozenMap(values={key: JsonString(value=value)}))
