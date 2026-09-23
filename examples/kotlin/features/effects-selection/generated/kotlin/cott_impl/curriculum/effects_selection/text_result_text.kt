package cott_impl.curriculum.effects_selection

internal fun text_result_text(result: cott_runtime.CottResult<kotlin.String, curriculum.effects_selection.EffectError>): kotlin.String =
    when (result) {
        is cott_runtime.Ok -> result.value
        is cott_runtime.Err -> ""
    }
