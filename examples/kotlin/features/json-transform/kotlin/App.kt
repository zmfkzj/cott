package examples.features.json_transform

import cott_runtime.Err
import cott_runtime.Ok
import cott_runtime.Some
import curriculum.json_transform.JsonChain
import curriculum.json_transform.extract_string_field
import curriculum.json_transform.wrap_scalar_json
import kotlinx.coroutines.runBlocking

public fun main(): Unit = runBlocking {
    val payload = wrap_scalar_json("greeting", "Hello Cott")
    when (val extracted = extract_string_field(payload, "greeting")) {
        is Ok -> println("Extracted JSON field: ${extracted.value.text}")
        is Err -> error("unexpected JSON extraction error: ${extracted.error}")
    }

    val chain = JsonChain.Link("first", Some(JsonChain.End))
    println("Recursive JSON chain: ${chain.value}")
}
