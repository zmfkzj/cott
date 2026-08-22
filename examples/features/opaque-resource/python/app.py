from __future__ import annotations

import io

from cott_runtime import Ok
from curriculum.opaque_resource import echo_values, extract_handle_id, iter_lines, wrap_handle
from curriculum.opaque_resource_types import TextBuffer

result = wrap_handle(raw_id=42)
if isinstance(result, Ok):
    raw_id = extract_handle_id(bundle=result.value)
    print(f"Extracted handle id: {raw_id}")

buffer: TextBuffer = io.StringIO("alpha\nbeta\n")
print(f"Lines: {','.join(iter_lines(buffer=buffer))}")

values = echo_values(values=iter(("first", 7)))
generated = [next(values), values.send(object())]
try:
    next(values)
except StopIteration as complete:
    count = complete.value

print(f"Generated values: {','.join(map(str, generated))}")
print(f"Generator return count: {count}")
