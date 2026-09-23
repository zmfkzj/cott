package cott_impl.curriculum.trait_protocol

internal fun task_factory(): cott_runtime.CottFactory<curriculum.trait_protocol.SimpleTask> =
    curriculum.trait_protocol.SimpleTask.cottFactory
