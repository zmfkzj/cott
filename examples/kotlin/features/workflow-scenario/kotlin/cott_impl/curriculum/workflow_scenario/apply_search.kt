package cott_impl.curriculum.workflow_scenario

internal fun apply_search(snapshot: curriculum.workflow_scenario.SearchSnapshot, candidate: curriculum.workflow_scenario.SearchResult): curriculum.workflow_scenario.SearchSnapshot {
    if (candidate.request_id != snapshot.request_id) return snapshot

    return curriculum.workflow_scenario.SearchSnapshot(
        request_id = snapshot.request_id,
        applied_request_id = candidate.request_id,
        query = snapshot.query,
        result = candidate.result,
        status = curriculum.workflow_scenario.SearchStatus.Ready
    )
}
