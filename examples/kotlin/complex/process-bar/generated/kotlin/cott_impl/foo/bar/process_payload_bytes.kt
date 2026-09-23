package cott_impl.foo.bar

internal fun process_payload_bytes(`data`: cott_runtime.CottBytes, options: foo.bar.BarOptions): cott_runtime.CottResult<cott_runtime.CottBytes, foo.bar.BarError> =
    cott_runtime.Ok(`data`)
