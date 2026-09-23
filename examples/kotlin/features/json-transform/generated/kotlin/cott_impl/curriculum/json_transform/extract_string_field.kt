package cott_impl.curriculum.json_transform

internal fun extract_string_field(payload: cott_runtime.JsonValue, `field`: kotlin.String): cott_runtime.CottResult<kotlin.String, curriculum.json_transform.JsonTransformError> {
    if (payload !is cott_runtime.JsonObject) {
        return cott_runtime.Err(curriculum.json_transform.JsonTransformError.NotAnObject)
    }
    val value = payload.value[`field`]
    return if (value is cott_runtime.JsonString) {
        cott_runtime.Ok(value.value)
    } else {
        cott_runtime.Err(curriculum.json_transform.JsonTransformError.MissingField(`field`))
    }
}
