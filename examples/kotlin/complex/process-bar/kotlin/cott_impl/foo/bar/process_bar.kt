package cott_impl.foo.bar

internal fun process_bar(`data`: foo.bar.InputPayload, options: foo.bar.BarOptions): cott_runtime.CottResult<foo.bar.OutputPayload, foo.bar.BarError> {
    val validated = when (val result = foo.bar.validate_payload(data)) {
        is cott_runtime.Ok -> result.value
        is cott_runtime.Err -> return result
    }
    val processed = when (val result = foo.bar.process_payload_bytes(validated.data, options)) {
        is cott_runtime.Ok -> result.value
        is cott_runtime.Err -> return result
    }
    return cott_runtime.Ok(foo.bar.build_output(processed, data.declared_size, data.format))
}
