package cott_impl.curriculum.boundary_protocols

internal fun echo_values(values: cott_runtime.CottIterator<kotlin.Any?>): cott_runtime.CottGenerator<kotlin.Any?, kotlin.Any?, kotlin.ULong> {
    var count: kotlin.ULong = 0uL
    var finished: kotlin.Boolean = false
    return cott_runtime.CottRuntime.wrapGenerator(
        object : cott_runtime.CottGeneratorSource<kotlin.Any?, kotlin.Any?, kotlin.ULong> {
            override fun start(): cott_runtime.CottGeneratorStep<kotlin.Any?, kotlin.ULong> = next()

            override fun send(value: kotlin.Any?): cott_runtime.CottGeneratorStep<kotlin.Any?, kotlin.ULong> = next()

            override fun next(): cott_runtime.CottGeneratorStep<kotlin.Any?, kotlin.ULong> {
                if (finished) return cott_runtime.CottGeneratorStep.Return(count)
                if (!values.hasNext()) {
                    finished = true
                    return cott_runtime.CottGeneratorStep.Return(count)
                }
                check(count != kotlin.ULong.MAX_VALUE) { "Yield count exceeds u64" }
                val value = values.next()
                count += 1uL
                return cott_runtime.CottGeneratorStep.Yield(value)
            }

            override fun raise(error: kotlin.Throwable): cott_runtime.CottGeneratorStep<kotlin.Any?, kotlin.ULong> {
                finished = true
                throw error
            }

            override fun close(): kotlin.Unit {
                finished = true
                values.close()
            }
        },
        yielded = cott_runtime.CottTypes.ANY,
        sent = cott_runtime.CottTypes.ANY,
        returned = cott_runtime.CottTypes.U64
    )
}
