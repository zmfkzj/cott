from curriculum.workflow_scenario_types import SearchResult, SearchSnapshot, SearchStatus_Ready


def apply_search(snapshot: SearchSnapshot, candidate: SearchResult) -> SearchSnapshot:
    if candidate.request_id != snapshot.request_id:
        return snapshot
    return SearchSnapshot(request_id=snapshot.request_id, applied_request_id=candidate.request_id, query=snapshot.query, result=candidate.result, status=SearchStatus_Ready())
