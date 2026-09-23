package cott_impl.curriculum.workflow_scenario

internal fun flush_save(snapshot: curriculum.workflow_scenario.SaveSnapshot): curriculum.workflow_scenario.SaveReceipt =
    curriculum.workflow_scenario.SaveReceipt(
        revision = snapshot.revision,
        text = snapshot.text,
        status = curriculum.workflow_scenario.SaveStatus.Flushed,
    )
