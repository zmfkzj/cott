from __future__ import annotations

from typing import Literal

from cott_runtime import Err, Ok, Opaque, Result, U64
from curriculum.boundary_protocols_types import HandleBundle, HandleError, HandleError_InvalidHandle


def wrap_handle(raw_id: U64) -> Result[HandleBundle, HandleError]:
    if raw_id == 0:
        return Err(error=HandleError_InvalidHandle())
    return Ok(value=HandleBundle(handle=Opaque[Literal["client_session"]](tag="client_session", value=raw_id), raw_id=raw_id))
