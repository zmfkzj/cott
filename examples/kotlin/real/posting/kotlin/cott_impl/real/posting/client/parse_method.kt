package cott_impl.real.posting.client

internal fun parse_method(source: kotlin.String): cott_runtime.CottResult<real.posting.client.HttpMethod, real.posting.client.PostingError> {
    if (!_isHttpToken(source)) {
        return cott_runtime.Err(real.posting.client.PostingError.InvalidRequest("invalid HTTP method: expected a non-empty HTTP token"))
    }
    return cott_runtime.Ok(_httpMethodFromToken(source))
}

private fun _isHttpToken(text: kotlin.String): kotlin.Boolean {
    if (text.isEmpty()) {
        return false
    }
    for (index in 0 until text.length) {
        if (!_isHttpTokenChar(text[index])) {
            return false
        }
    }
    return true
}

private fun _isHttpTokenChar(c: kotlin.Char): kotlin.Boolean {
    return when (c) {
        in 'A'..'Z', in 'a'..'z', in '0'..'9' -> true
        '!', '#', '$', '%', '&', '\'', '*', '+', '-', '.', '^', '_', '`', '|', '~' -> true
        else -> false
    }
}

private fun _httpMethodFromToken(token: kotlin.String): real.posting.client.HttpMethod {
    return when {
        _equalsAsciiIgnoreCase(token, "GET") -> real.posting.client.HttpMethod.Get
        _equalsAsciiIgnoreCase(token, "HEAD") -> real.posting.client.HttpMethod.Head
        _equalsAsciiIgnoreCase(token, "POST") -> real.posting.client.HttpMethod.Post
        _equalsAsciiIgnoreCase(token, "PUT") -> real.posting.client.HttpMethod.Put
        _equalsAsciiIgnoreCase(token, "PATCH") -> real.posting.client.HttpMethod.Patch
        _equalsAsciiIgnoreCase(token, "DELETE") -> real.posting.client.HttpMethod.Delete
        _equalsAsciiIgnoreCase(token, "OPTIONS") -> real.posting.client.HttpMethod.Options
        else -> real.posting.client.HttpMethod.Custom(token)
    }
}

private fun _equalsAsciiIgnoreCase(text: kotlin.String, upperAsciiName: kotlin.String): kotlin.Boolean {
    if (text.length != upperAsciiName.length) {
        return false
    }
    for (index in 0 until text.length) {
        val c = text[index]
        val upper = if (c in 'a'..'z') c - ('a' - 'A') else c
        if (upper != upperAsciiName[index]) {
            return false
        }
    }
    return true
}
