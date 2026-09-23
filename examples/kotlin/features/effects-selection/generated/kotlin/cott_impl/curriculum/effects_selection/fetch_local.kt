package cott_impl.curriculum.effects_selection

internal fun fetch_local(url: kotlin.String): cott_runtime.CottResult<kotlin.String, curriculum.effects_selection.EffectError> {
    if (url.isEmpty()) {
        return cott_runtime.Err(curriculum.effects_selection.EffectError.OperationFailed("URL must not be empty"))
    }
    return try {
        val client = java.net.http.HttpClient.newBuilder()
            .followRedirects(java.net.http.HttpClient.Redirect.ALWAYS)
            .connectTimeout(java.time.Duration.ofSeconds(10))
            .build()
        val request = java.net.http.HttpRequest.newBuilder(java.net.URI(url))
            .timeout(java.time.Duration.ofSeconds(10))
            .GET()
            .build()
        val response = client.send(request, java.net.http.HttpResponse.BodyHandlers.ofByteArray())
        if (response.statusCode() !in 200..299) {
            cott_runtime.Err(curriculum.effects_selection.EffectError.OperationFailed("HTTP status ${response.statusCode()}"))
        } else {
            val text = java.nio.charset.StandardCharsets.UTF_8.newDecoder()
                .onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
                .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT)
                .decode(java.nio.ByteBuffer.wrap(response.body()))
                .toString()
            cott_runtime.Ok(text)
        }
    } catch (error: java.lang.InterruptedException) {
        java.lang.Thread.currentThread().interrupt()
        cott_runtime.Err(curriculum.effects_selection.EffectError.OperationFailed(error.message ?: "HTTP request interrupted"))
    } catch (error: kotlin.Exception) {
        cott_runtime.Err(curriculum.effects_selection.EffectError.OperationFailed(error.message ?: "HTTP request failed"))
    }
}
