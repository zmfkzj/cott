package cott_impl.foo.bar

internal fun build_output(`data`: cott_runtime.CottBytes, source_size: foo.bar.PayloadSize, format: foo.bar.PayloadFormat): foo.bar.OutputPayload =
    foo.bar.OutputPayload(data = `data`, source_size = source_size, format = format)
