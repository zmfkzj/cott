from typing import Literal

from cott_runtime import Opaque
from curriculum.boundary_protocols_types import ConnectionId, HandleBundle


def wrap_handle(raw_id: ConnectionId) -> HandleBundle:
    handle: Opaque[Literal["client_session"]] = Opaque(tag="client_session", value=raw_id.value)
    return HandleBundle(handle=handle, raw_id=raw_id)
