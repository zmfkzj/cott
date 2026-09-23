package cott_impl.curriculum.effects_selection

internal fun copy_result_is_ok(result: cott_runtime.CottResult<kotlin.ULong, curriculum.effects_selection.EffectError>): kotlin.Boolean =
    result is cott_runtime.Ok<*>
