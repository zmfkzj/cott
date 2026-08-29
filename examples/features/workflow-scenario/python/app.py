from __future__ import annotations

import asyncio

from curriculum.workflow_scenario import (
    apply_search,
    begin_save,
    begin_search,
    flush_save,
    request_save,
    resolve_search,
)


async def main() -> None:
    old_result = await resolve_search(1, "old")
    newest = begin_search(2, "new")
    new_result = await resolve_search(2, "new")
    applied = apply_search(newest, new_result)
    protected = apply_search(applied, old_result)

    queued = begin_save(1, "draft")
    coalesced = request_save(queued, 2, "published")
    flushed = flush_save(coalesced)

    assert protected.applied_request_id == 2
    assert protected.result == "new result"
    assert flushed.revision == 2
    assert flushed.text == "published"
    print(protected.result)
    print(flushed.text)


asyncio.run(main())
