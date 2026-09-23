package cott_impl.curriculum.json_transform

internal suspend fun wrap_scalar_json(key: kotlin.String, `value`: kotlin.String): cott_runtime.JsonValue {
    require(key.isNotEmpty())
    return cott_runtime.JsonObject(kotlin.collections.mapOf(key to cott_runtime.JsonString(`value`)))
}
