package cott_impl.curriculum.boundary_protocols

internal fun extract_handle_id(bundle: curriculum.boundary_protocols.HandleBundle): curriculum.boundary_protocols.ConnectionId {
    val payload: kotlin.Any = bundle.handle.unwrap()
    val rawId = payload as kotlin.ULong
    return curriculum.boundary_protocols.ConnectionId(rawId)
}
