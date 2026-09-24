from typing import Literal

from cott_runtime import U64, Err, Ok, Opaque, Result
from curriculum.boundary_protocols_types import HandleBundle, HandleError, HandleError_InvalidHandle


def wrap_handle(raw_id: U64) -> Result[HandleBundle, HandleError]:
    if raw_id == 0:
        return Err(error=HandleError_InvalidHandle())
    handle: Opaque[Literal["client_session"]] = Opaque(tag="client_session", value=raw_id)
    return Ok(value=HandleBundle(handle=handle, raw_id=raw_id))
