package cott_impl.curriculum.workflow_scenario

internal fun begin_save(revision: kotlin.ULong, text: kotlin.String): curriculum.workflow_scenario.SaveSnapshot {
    require(revision > 0uL)
    return curriculum.workflow_scenario.SaveSnapshot(
        revision = revision,
        text = text,
        status = curriculum.workflow_scenario.SaveStatus.Queued
    )
}
