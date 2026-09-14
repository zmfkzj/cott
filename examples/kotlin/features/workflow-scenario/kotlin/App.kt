package examples.features.workflow_scenario

import curriculum.workflow_scenario.apply_search
import curriculum.workflow_scenario.begin_save
import curriculum.workflow_scenario.begin_search
import curriculum.workflow_scenario.flush_save
import curriculum.workflow_scenario.request_save
import curriculum.workflow_scenario.resolve_search
import kotlinx.coroutines.runBlocking

public fun main(): Unit = runBlocking {
    val oldResult = resolve_search(1uL, "old")
    val newest = begin_search(2uL, "new")
    val newResult = resolve_search(2uL, "new")
    val applied = apply_search(newest, newResult)
    val protected = apply_search(applied, oldResult)

    val queued = begin_save(1uL, "draft")
    val coalesced = request_save(queued, 2uL, "published")
    val flushed = flush_save(coalesced)

    check(protected.applied_request_id == 2uL)
    check(protected.result == "new result")
    check(flushed.revision == 2uL)
    check(flushed.text == "published")
    println(protected.result)
    println(flushed.text)
}
