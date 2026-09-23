package cott_impl.curriculum.boundary_protocols

internal fun wrap_handle(raw_id: kotlin.ULong): cott_runtime.CottResult<curriculum.boundary_protocols.HandleBundle, curriculum.boundary_protocols.HandleError> {
    if (raw_id == 0uL) {
        return cott_runtime.Err(curriculum.boundary_protocols.HandleError.InvalidHandle)
    }
    return cott_runtime.Ok(
        curriculum.boundary_protocols.HandleBundle(
            handle = cott_runtime.Opaque.of(cott_runtime.CottOpaque_7237d55bbcbee604a7ba6463, raw_id),
            raw_id = raw_id
        )
    )
}
