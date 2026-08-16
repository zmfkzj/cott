from __future__ import annotations

from typing import Literal
from cott_runtime import Err, Ok, Opaque, Result, U64
from curriculum.opaque_resource_types import HandleError, HandleError_InvalidHandle

def wrap_handle(raw_id: U64) -> Result[Opaque[Literal["client_session"]], HandleError]:
    if raw_id == 0:
        return Err(error=HandleError_InvalidHandle())
    return Ok(value=Opaque(tag="client_session", value=raw_id))
