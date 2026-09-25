from curriculum.boundary_protocols_types import ConnectionId, HandleBundle


def extract_handle_id(bundle: HandleBundle) -> ConnectionId:
    payload: object = bundle.handle.unwrap()
    if not isinstance(payload, int) or isinstance(payload, bool):
        raise TypeError("client_session handle payload must be a U64 connection id")
    return ConnectionId(value=payload)
