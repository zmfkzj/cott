package examples.features.contracts_evidence

import cott_runtime.Err
import cott_runtime.Nothing
import cott_runtime.Ok
import cott_runtime.Some
import curriculum.contracts_evidence.LabelRequest
import curriculum.contracts_evidence.assess_label

public fun main(): Unit {
    val requests = listOf(
        LabelRequest(Nothing, 3uL),
        LabelRequest(Some("ok"), 3uL),
        LabelRequest(Some("evidence"), 3uL),
    )
    for (request in requests) {
        when (val result = assess_label(request)) {
            is Err -> println(result.error)
            is Ok -> println(result.value.text)
        }
    }
}
