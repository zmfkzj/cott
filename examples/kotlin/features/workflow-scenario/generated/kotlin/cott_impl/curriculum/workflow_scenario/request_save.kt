package cott_impl.curriculum.workflow_scenario

internal fun request_save(snapshot: curriculum.workflow_scenario.SaveSnapshot, revision: kotlin.ULong, text: kotlin.String): curriculum.workflow_scenario.SaveSnapshot {
    require(revision > 0uL)
    if (revision <= snapshot.revision) return snapshot
    return curriculum.workflow_scenario.SaveSnapshot(
        revision,
        text,
        curriculum.workflow_scenario.SaveStatus.Queued
    )
}
