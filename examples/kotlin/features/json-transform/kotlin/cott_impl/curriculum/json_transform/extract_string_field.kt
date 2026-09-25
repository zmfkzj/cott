package cott_impl.curriculum.json_transform

internal fun extract_string_field(payload: cott_runtime.JsonValue, `field`: kotlin.String): cott_runtime.CottResult<curriculum.json_transform.StringField, curriculum.json_transform.JsonTransformError> {
    if (payload !is cott_runtime.JsonObject) {
        return cott_runtime.Err(curriculum.json_transform.JsonTransformError.NotAnObject)
    }
    val member = payload.value[`field`]
    return if (member is cott_runtime.JsonString) {
        cott_runtime.Ok(curriculum.json_transform.StringField(`field`, member.value))
    } else {
        cott_runtime.Err(curriculum.json_transform.JsonTransformError.MissingField(`field`))
    }
}
