package examples.features.effects_selection

import curriculum.effects_selection.clock_ns
import curriculum.effects_selection.copy_text
import curriculum.effects_selection.fetch_local
import curriculum.effects_selection.read_text

public fun main(): Unit {
    val facadeNames = listOf(
        ::read_text.name,
        ::copy_text.name,
        ::fetch_local.name,
        ::clock_ns.name,
    )
    println("Compiler-owned fixture scenarios exercise: ${facadeNames.joinToString()}")
}
