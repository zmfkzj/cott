package cott_impl.curriculum.boundary_protocols

internal fun extract_handle_id(bundle: curriculum.boundary_protocols.HandleBundle): kotlin.ULong {
    val rawId = bundle.handle.unwrap() as kotlin.ULong
    check(rawId > 0uL)
    return rawId
}
