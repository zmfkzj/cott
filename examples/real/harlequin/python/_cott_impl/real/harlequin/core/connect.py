from cott_runtime import Err, Ok, Result
from real.harlequin.core_types import (
    Connection,
    ConnectionError,
    ConnectionError_InvalidEndpoint,
    ConnectionRequest,
)


def connect(request: ConnectionRequest) -> Result[Connection, ConnectionError]:
    if request.endpoint.strip() == "":
        return Err(error=ConnectionError_InvalidEndpoint(endpoint=request.endpoint))

    return Ok(
        value=Connection(
            id=request.endpoint,
            adapter=request.adapter,
            endpoint=request.endpoint,
            read_only=request.read_only,
        )
    )
