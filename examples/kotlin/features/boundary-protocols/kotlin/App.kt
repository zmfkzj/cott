package examples.features.boundary_protocols

import cott_runtime.CottAsyncGeneratorSource
import cott_runtime.CottAsyncIteratorSource
import cott_runtime.CottGeneratorStep
import cott_runtime.CottIteratorSource
import cott_runtime.CottRuntime
import cott_runtime.CottStep
import cott_runtime.CottTypes
import cott_runtime.CottUnit
import cott_runtime.Err
import cott_runtime.Ok
import curriculum.boundary_protocols.adapt_unknown
import curriculum.boundary_protocols.async_lines
import curriculum.boundary_protocols.echo_async
import curriculum.boundary_protocols.echo_values
import curriculum.boundary_protocols.extract_handle_id
import curriculum.boundary_protocols.iter_lines
import curriculum.boundary_protocols.TextBuffer
import curriculum.boundary_protocols.wrap_handle
import kotlinx.coroutines.runBlocking

private class IteratorValues(private val values: List<Any?>) : CottIteratorSource<Any?> {
    private var position: Int = 0

    override fun next(): CottStep<Any?> =
        if (position < values.size) CottStep.Yield(values[position++]) else CottStep.Done
}

private class AsyncIteratorValues<T>(private val values: List<T>) : CottAsyncIteratorSource<T> {
    private var position: Int = 0

    override suspend fun next(): CottStep<T> =
        if (position < values.size) CottStep.Yield(values[position++]) else CottStep.Done
}

private class AsyncGeneratorValues(private val values: List<Any?>) :
    CottAsyncGeneratorSource<Any?, Any?, CottUnit> {
    private var position: Int = 0

    private fun pull(): CottGeneratorStep<Any?, CottUnit> =
        if (position < values.size) CottGeneratorStep.Yield(values[position++])
        else CottGeneratorStep.Return(CottUnit)

    override suspend fun start(): CottGeneratorStep<Any?, CottUnit> = pull()
    override suspend fun send(value: Any?): CottGeneratorStep<Any?, CottUnit> = pull()
    override suspend fun next(): CottGeneratorStep<Any?, CottUnit> = pull()
    override suspend fun raise(error: Throwable): CottGeneratorStep<Any?, CottUnit> = throw error
    override suspend fun close(): Unit {
        position = values.size
    }
}

private fun yielded(step: CottGeneratorStep<Any?, *>): Any? = when (step) {
    is CottGeneratorStep.Yield -> step.value
    is CottGeneratorStep.Return -> error("protocol completed before yielding")
}

public fun main(): Unit = runBlocking {
    when (val result = wrap_handle(42uL)) {
        is Ok -> {
            check(result.value.raw_id == 42uL)
            println("Wrapped raw id: ${result.value.raw_id}")
            println("Extracted handle id: ${extract_handle_id(result.value)}")
        }
        is Err -> error("unexpected handle error: ${result.error}")
    }

    val unknown = adapt_unknown(mapOf("label" to "explicit"))
    val label = (unknown as? Map<*, *>)?.get("label") as? String
        ?: error("expected a string label")
    println("Narrowed unknown: $label")

    val buffer: TextBuffer = "alpha\nbeta\n".reader().buffered()
    buffer.use {
        println("Lines: ${iter_lines(it).asSequence().joinToString(",")}")
    }

    val iterator = CottRuntime.wrapIterator(
        IteratorValues(listOf("first", 7)),
        CottTypes.ANY,
    )
    val generated = echo_values(iterator)
    val first = yielded(generated.nextStep())
    val second = yielded(generated.send(Any()))
    val count = when (val completion = generated.nextStep()) {
        is CottGeneratorStep.Return -> completion.value
        is CottGeneratorStep.Yield -> error("generator yielded too many values")
    }
    println("Generator return count: $count")
    println("Generated values: $first,$second")

    val lineInput = CottRuntime.wrapAsyncIterator(
        AsyncIteratorValues(listOf("gamma", "delta")),
        CottTypes.STRING,
    )
    val lines = async_lines(lineInput)
    val line1 = (lines.next() as CottStep.Yield).value
    val line2 = (lines.next() as CottStep.Yield).value
    check(lines.next() === CottStep.Done)
    println("Async lines: $line1,$line2")

    val asyncInput = CottRuntime.wrapAsyncGenerator(
        AsyncGeneratorValues(listOf("first", 7)),
        CottTypes.ANY,
        CottTypes.ANY,
        CottTypes.UNIT,
    )
    val asyncValues = echo_async(asyncInput)
    val asyncFirst = yielded(asyncValues.start())
    val asyncSecond = yielded(asyncValues.send(Any()))
    check(asyncValues.next() is CottGeneratorStep.Return)
    println("Async generated values: $asyncFirst,$asyncSecond")
    asyncValues.close()
    asyncValues.close()
    println("Async generator closed twice")
}
