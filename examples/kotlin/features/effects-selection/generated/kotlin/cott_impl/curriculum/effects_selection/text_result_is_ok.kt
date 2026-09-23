package cott_impl.curriculum.effects_selection

internal fun text_result_is_ok(result: cott_runtime.CottResult<kotlin.String, curriculum.effects_selection.EffectError>): kotlin.Boolean =
    result is cott_runtime.Ok<*>
