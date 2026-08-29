from __future__ import annotations

from curriculum.workflow_scenario_types import SaveReceipt, SaveSnapshot, SaveStatus_Flushed


def flush_save(snapshot: SaveSnapshot) -> SaveReceipt:
    return SaveReceipt(
        revision=snapshot.revision,
        text=snapshot.text,
        status=SaveStatus_Flushed(),
    )
