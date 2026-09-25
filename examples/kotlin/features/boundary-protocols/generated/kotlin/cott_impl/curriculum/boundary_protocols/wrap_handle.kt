package cott_impl.curriculum.boundary_protocols

internal fun wrap_handle(raw_id: curriculum.boundary_protocols.ConnectionId): curriculum.boundary_protocols.HandleBundle {
    val payload: kotlin.ULong = raw_id.value
    return curriculum.boundary_protocols.HandleBundle(
        handle = cott_runtime.Opaque.of(cott_runtime.CottOpaque_7237d55bbcbee604a7ba6463, payload),
        raw_id = raw_id
    )
}
