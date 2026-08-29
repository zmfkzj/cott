from __future__ import annotations

from cott_runtime import U64
from curriculum.workflow_scenario_types import SearchSnapshot, SearchStatus_Loading


def begin_search(request_id: U64, query: str) -> SearchSnapshot:
    return SearchSnapshot(
        request_id=request_id,
        applied_request_id=0,
        query=query,
        result="",
        status=SearchStatus_Loading(),
    )
