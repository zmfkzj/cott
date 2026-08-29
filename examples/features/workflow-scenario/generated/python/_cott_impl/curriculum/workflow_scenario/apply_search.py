from __future__ import annotations

from curriculum.workflow_scenario_types import (
    SearchResult,
    SearchSnapshot,
    SearchStatus_Ready,
)


def apply_search(snapshot: SearchSnapshot, candidate: SearchResult) -> SearchSnapshot:
    if candidate.request_id != snapshot.request_id or candidate.query != snapshot.query:
        return snapshot
    return SearchSnapshot(
        request_id=snapshot.request_id,
        applied_request_id=candidate.request_id,
        query=candidate.query,
        result=candidate.result,
        status=SearchStatus_Ready(),
    )
