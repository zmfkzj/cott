from __future__ import annotations

from cott_runtime import U64
from curriculum.workflow_scenario_types import SearchResult


async def resolve_search(request_id: U64, query: str) -> SearchResult:
    return SearchResult(request_id=request_id, query=query, result=f"{query} result")
