from __future__ import annotations

from cott_runtime import Ok
from curriculum.json_transform import extract_string_field, wrap_scalar_json

payload = wrap_scalar_json("greeting", "Hello Cott")
extracted = extract_string_field(payload, "greeting")
if isinstance(extracted, Ok):
    print(f"Extracted JSON field: {extracted.value}")
