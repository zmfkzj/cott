import asyncio
from typing import Final

from cott_runtime import U64
from curriculum.workflow_scenario_types import SearchResult

_RESULT_SUFFIX: Final[str] = " result"


async def resolve_search(request_id: U64, query: str) -> SearchResult:
    await asyncio.sleep(0)
    return SearchResult(request_id=request_id, query=query, result=query + _RESULT_SUFFIX)
