from __future__ import annotations

from typing import Literal
from cott_runtime import Opaque, U64

def extract_handle_id(handle: Opaque[Literal["client_session"]]) -> U64:
    return handle.value
