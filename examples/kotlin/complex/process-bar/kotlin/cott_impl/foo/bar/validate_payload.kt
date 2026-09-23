package cott_impl.foo.bar

internal fun validate_payload(`data`: foo.bar.InputPayload): cott_runtime.CottResult<foo.bar.InputPayload, foo.bar.BarError> =
    if (`data`.data.isEmpty()) {
        cott_runtime.Err(foo.bar.BarError.InvalidPayload(reason = "Payload bytes must not be empty"))
    } else {
        cott_runtime.Ok(`data`)
    }
