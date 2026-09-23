package cott_impl.curriculum.boundary_protocols

internal fun iter_lines(buffer: curriculum.boundary_protocols.TextBuffer): cott_runtime.CottIterator<kotlin.String> =
    cott_runtime.CottRuntime.wrapIterator(
        object : cott_runtime.CottIteratorSource<kotlin.String> {
            override fun next(): cott_runtime.CottStep<kotlin.String> {
                val line = buffer.readLine() ?: return cott_runtime.CottStep.Done
                return cott_runtime.CottStep.Yield(line)
            }
        },
        cott_runtime.CottTypes.STRING,
    )
