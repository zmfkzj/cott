package cott_impl.real.posting.client

private fun _isHttpTokenCharacter(character: kotlin.Char): kotlin.Boolean {
    return when (character) {
        in 'A'..'Z', in 'a'..'z', in '0'..'9' -> true
        '!', '#', '$', '%', '&', '\'', '*', '+', '-', '.', '^', '_', '`', '|', '~' -> true
        else -> false
    }
}

private fun _isHttpToken(source: kotlin.String): kotlin.Boolean {
    if (source.isEmpty()) {
        return false
    }
    for (character in source) {
        if (!_isHttpTokenCharacter(character)) {
            return false
        }
    }
    return true
}

private fun _equalsAsciiIgnoreCase(source: kotlin.String, upperName: kotlin.String): kotlin.Boolean {
    if (source.length != upperName.length) {
        return false
    }
    for (index in 0 until source.length) {
        var character: kotlin.Char = source[index]
        if (character in 'a'..'z') {
            character = character - 32
        }
        if (character != upperName[index]) {
            return false
        }
    }
    return true
}

private fun _parseMethod(source: kotlin.String): real.posting.client.HttpMethod? {
    if (!_isHttpToken(source)) {
        return null
    }
    return when {
        _equalsAsciiIgnoreCase(source, "GET") -> real.posting.client.HttpMethod.Get
        _equalsAsciiIgnoreCase(source, "HEAD") -> real.posting.client.HttpMethod.Head
        _equalsAsciiIgnoreCase(source, "POST") -> real.posting.client.HttpMethod.Post
        _equalsAsciiIgnoreCase(source, "PUT") -> real.posting.client.HttpMethod.Put
        _equalsAsciiIgnoreCase(source, "PATCH") -> real.posting.client.HttpMethod.Patch
        _equalsAsciiIgnoreCase(source, "DELETE") -> real.posting.client.HttpMethod.Delete
        _equalsAsciiIgnoreCase(source, "OPTIONS") -> real.posting.client.HttpMethod.Options
        else -> real.posting.client.HttpMethod.Custom(source)
    }
}

private fun _invalidArguments(message: kotlin.String): cott_runtime.CottResult<real.posting.client.Request, real.posting.client.PostingError> {
    return cott_runtime.Err(real.posting.client.PostingError.InvalidArguments(message))
}

private fun _invalidRequest(message: kotlin.String): cott_runtime.CottResult<real.posting.client.Request, real.posting.client.PostingError> {
    return cott_runtime.Err(real.posting.client.PostingError.InvalidRequest(message))
}

internal fun  parse_arguments(arguments: cott_runtime.CottList<kotlin.String>): cott_runtime.CottResult<real.posting.client.Request, real.posting.client.PostingError> {
    val argumentCount: kotlin.Int = arguments.size
    if (argumentCount < 2 || argumentCount > 3) {
        return _invalidArguments("expected METHOD URL [BODY] but received " + argumentCount.toString() + " arguments")
    }
    val methodSource: kotlin.String = arguments[0]
    val method: real.posting.client.HttpMethod? = _parseMethod(methodSource)
    if (method == null) {
        return _invalidRequest("invalid HTTP method: " + methodSource)
    }
    val url: kotlin.String = arguments[1]
    val body: kotlin.String = if (argumentCount == 3) arguments[2] else ""
    return cott_runtime.Ok(
        real.posting.client.Request(
            method,
            url,
            cott_runtime.CottList(kotlin.collections.emptyList<real.posting.client.Header>()),
            body,
            30000u
        )
    )
}
