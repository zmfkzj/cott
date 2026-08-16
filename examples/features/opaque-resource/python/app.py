from __future__ import annotations

from cott_runtime import Ok
from curriculum.opaque_resource import extract_handle_id, wrap_handle

result = wrap_handle(42)
if isinstance(result, Ok):
    handle = result.value
    raw_id = extract_handle_id(handle)
    print(f"Extracted handle id: {raw_id}")
