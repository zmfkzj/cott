package examples.features.effects_selection

import curriculum.effects_selection.clock_ns
import curriculum.effects_selection.copy_result_is_ok
import curriculum.effects_selection.copy_text
import curriculum.effects_selection.fetch_local
import curriculum.effects_selection.text_result_is_ok
import curriculum.effects_selection.text_result_text

public fun main(): Unit {
    val facadeNames = listOf(
        ::copy_text.name,
        ::fetch_local.name,
        ::clock_ns.name,
        ::copy_result_is_ok.name,
        ::text_result_is_ok.name,
        ::text_result_text.name,
    )
    println("Compiler-owned fixture scenarios exercise: ${facadeNames.joinToString()}")
}
