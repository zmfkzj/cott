package cott_impl.real.posting.client

internal fun render_response(response: real.posting.client.Response): kotlin.String {
    val sb = StringBuilder()
    sb.append(response.status.toString()).append(' ').append(response.url)
    for (header in response.headers) {
        sb.append('\n').append(header.name).append(": ").append(header.value)
    }
    sb.append('\n').append('\n').append(response.body)
    return sb.toString()
}
