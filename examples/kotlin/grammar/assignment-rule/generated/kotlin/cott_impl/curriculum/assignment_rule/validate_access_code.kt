package cott_impl.curriculum.assignment_rule

internal fun validate_access_code(code: kotlin.String): cott_runtime.CottResult<kotlin.String, curriculum.assignment_rule.AccessCodeError> {
    val length = code.codePointCount(0, code.length)
    return when {
        length == 0 -> cott_runtime.Err(curriculum.assignment_rule.AccessCodeError.EmptyCode)
        length < 4 -> cott_runtime.Err(curriculum.assignment_rule.AccessCodeError.TooShort)
        else -> cott_runtime.Ok(code)
    }
}
