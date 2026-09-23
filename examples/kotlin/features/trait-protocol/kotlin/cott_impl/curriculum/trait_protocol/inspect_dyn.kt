package cott_impl.curriculum.trait_protocol

internal suspend fun inspect_dyn(item: cott_runtime.Dyn<curriculum.trait_protocol.TaskView<kotlin.String, *>>): kotlin.String =
    item.toString()
