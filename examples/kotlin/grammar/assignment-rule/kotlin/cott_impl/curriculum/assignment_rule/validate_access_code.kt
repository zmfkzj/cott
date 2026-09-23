package cott_impl.curriculum.assignment_rule

internal fun validate_access_code(code: kotlin.String): cott_runtime.CottResult<kotlin.String, curriculum.assignment_rule.AccessCodeError> {
    val trimmed = code.trim()
    return if (trimmed.codePointCount(0, trimmed.length) >= 4) {
        cott_runtime.Ok(trimmed)
    } else {
        cott_runtime.Err(curriculum.assignment_rule.AccessCodeError.TooShort)
    }
}
