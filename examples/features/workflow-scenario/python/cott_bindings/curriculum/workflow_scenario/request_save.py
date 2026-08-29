from __future__ import annotations

from cott_runtime import U64
from curriculum.workflow_scenario_types import SaveSnapshot, SaveStatus_Queued


def request_save(snapshot: SaveSnapshot, revision: U64, text: str) -> SaveSnapshot:
    if revision <= snapshot.revision:
        return snapshot
    return SaveSnapshot(revision=revision, text=text, status=SaveStatus_Queued())
