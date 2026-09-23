package cott_impl.curriculum.effects_selection

internal fun exit_with_code(code: kotlin.UByte): kotlin.Nothing =
    cott_runtime.CottRuntime.exitWithCode(code)
