package cott_impl.curriculum.workflow_scenario

internal fun begin_search(request_id: kotlin.ULong, query: kotlin.String): curriculum.workflow_scenario.SearchSnapshot {
    require(request_id > 0uL)
    return curriculum.workflow_scenario.SearchSnapshot(
        request_id = request_id,
        applied_request_id = 0uL,
        query = query,
        result = "",
        status = curriculum.workflow_scenario.SearchStatus.Loading
    )
}
