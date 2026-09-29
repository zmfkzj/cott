package cott_impl.real.posting.client

private fun _mkUrl(scheme: String, authority: String, host: String, port: Int?, path: String, query: String?, fragment: String?): List<String?> =
    listOf(scheme, authority, host, port?.toString(), path, query, fragment)

private fun _uScheme(u: List<String?>): String = u[0]!!
private fun _uAuth(u: List<String?>): String = u[1]!!
private fun _uHost(u: List<String?>): String = u[2]!!
private fun _uPort(u: List<String?>): Int? = u[3]?.toInt()
private fun _uPath(u: List<String?>): String = u[4]!!
private fun _uQuery(u: List<String?>): String? = u[5]

private fun _isToken(s: String): Boolean {
    if (s.isEmpty()) return false
    for (c in s) {
        val ok = (c in 'A'..'Z') || (c in 'a'..'z') || (c in '0'..'9') || "!#$%&'*+-.^_`|~".indexOf(c) >= 0
        if (!ok) return false
    }
    return true
}

private fun _isHex(c: Char): Boolean = (c in '0'..'9') || (c in 'a'..'f') || (c in 'A'..'F')

private fun _urlCharsOk(s: String): Boolean {
    var i = 0
    while (i < s.length) {
        val c = s[i]
        if (c == '%') {
            if (i + 2 >= s.length) return false
            if (!_isHex(s[i + 1]) || !_isHex(s[i + 2])) return false
            i += 3
            continue
        }
        val ok = (c in 'A'..'Z') || (c in 'a'..'z') || (c in '0'..'9') || "-._~:/?#[]@!$&'()*+,;=".indexOf(c) >= 0
        if (!ok) return false
        i++
    }
    return true
}

private fun _methodName(m: real.posting.client.HttpMethod): String = when (m) {
    is real.posting.client.HttpMethod.Get -> "GET"
    is real.posting.client.HttpMethod.Head -> "HEAD"
    is real.posting.client.HttpMethod.Post -> "POST"
    is real.posting.client.HttpMethod.Put -> "PUT"
    is real.posting.client.HttpMethod.Patch -> "PATCH"
    is real.posting.client.HttpMethod.Delete -> "DELETE"
    is real.posting.client.HttpMethod.Options -> "OPTIONS"
    is real.posting.client.HttpMethod.Custom -> m.name
}

private fun _parseUrl(url: String): List<String?>? {
    val scheme: String
    if (url.startsWith("http://")) scheme = "http" else if (url.startsWith("https://")) scheme = "https" else return null
    if (!_urlCharsOk(url)) return null
    val rest = url.substring(scheme.length + 3)
    var authEnd = rest.length
    for (i in rest.indices) {
        val c = rest[i]
        if (c == '/' || c == '?' || c == '#') { authEnd = i; break }
    }
    val authority = rest.substring(0, authEnd)
    val tail = rest.substring(authEnd)
    val at = authority.lastIndexOf('@')
    val hostPort = if (at >= 0) authority.substring(at + 1) else authority
    val host: String
    var portStr = ""
    if (hostPort.startsWith("[")) {
        val close = hostPort.indexOf(']')
        if (close < 0) return null
        host = hostPort.substring(0, close + 1)
        if (host.length <= 2) return null
        val after = hostPort.substring(close + 1)
        if (after.isNotEmpty()) {
            if (after[0] != ':') return null
            portStr = after.substring(1)
        }
    } else {
        val colon = hostPort.indexOf(':')
        if (colon >= 0) {
            host = hostPort.substring(0, colon)
            portStr = hostPort.substring(colon + 1)
        } else {
            host = hostPort
        }
    }
    if (host.isEmpty()) return null
    var port: Int? = null
    if (portStr.isNotEmpty()) {
        if (portStr.length > 5 || !portStr.all { it in '0'..'9' }) return null
        val p = portStr.toInt()
        if (p > 65535) return null
        port = p
    }
    var fragment: String? = null
    var beforeFrag = tail
    val hash = tail.indexOf('#')
    if (hash >= 0) {
        fragment = tail.substring(hash + 1)
        beforeFrag = tail.substring(0, hash)
    }
    var query: String? = null
    var path = beforeFrag
    val q = beforeFrag.indexOf('?')
    if (q >= 0) {
        query = beforeFrag.substring(q + 1)
        path = beforeFrag.substring(0, q)
    }
    return _mkUrl(scheme, authority, host, port, path, query, fragment)
}

private fun _defaultPort(scheme: String): Int = if (scheme == "https") 443 else 80

private fun _effPort(u: List<String?>): Int = _uPort(u) ?: _defaultPort(_uScheme(u))

private fun _sameOrigin(a: List<String?>, b: List<String?>): Boolean =
    _uScheme(a).lowercase() == _uScheme(b).lowercase() &&
        _uHost(a).lowercase() == _uHost(b).lowercase() &&
        _effPort(a) == _effPort(b)

private fun _removeDotSegments(path: String): String {
    var input = path
    val out = StringBuilder()
    while (input.isNotEmpty()) {
        if (input.startsWith("../")) {
            input = input.substring(3)
        } else if (input.startsWith("./")) {
            input = input.substring(2)
        } else if (input.startsWith("/./")) {
            input = input.substring(2)
        } else if (input == "/.") {
            input = "/"
        } else if (input.startsWith("/../") || input == "/..") {
            input = if (input == "/..") "/" else input.substring(3)
            val idx = out.lastIndexOf("/")
            if (idx >= 0) out.setLength(idx) else out.setLength(0)
        } else if (input == "." || input == "..") {
            input = ""
        } else {
            val start = if (input.startsWith("/")) 1 else 0
            val next = input.indexOf('/', start)
            val end = if (next < 0) input.length else next
            out.append(input, 0, end)
            input = input.substring(end)
        }
    }
    return out.toString()
}

private fun _resolve(base: List<String?>, ref: String): String? {
    if (!_urlCharsOk(ref)) return null
    var rest = ref
    var fragment: String? = null
    val hash = rest.indexOf('#')
    if (hash >= 0) {
        fragment = rest.substring(hash + 1)
        rest = rest.substring(0, hash)
    }
    var query: String? = null
    val qm = rest.indexOf('?')
    if (qm >= 0) {
        query = rest.substring(qm + 1)
        rest = rest.substring(0, qm)
    }
    var scheme: String? = null
    val m = Regex("^([A-Za-z][A-Za-z0-9+.\\-]*):").find(rest)
    if (m != null) {
        scheme = m.groupValues[1].lowercase()
        rest = rest.substring(m.value.length)
    }
    var authority: String? = null
    if (rest.startsWith("//")) {
        var end = rest.length
        val s = rest.indexOf('/', 2)
        if (s >= 0) end = s
        authority = rest.substring(2, end)
        rest = rest.substring(end)
    }
    val tScheme: String
    val tAuth: String?
    val tPath: String
    val tQuery: String?
    val basePath = _uPath(base)
    if (scheme != null) {
        tScheme = scheme
        tAuth = authority
        tPath = _removeDotSegments(rest)
        tQuery = query
    } else {
        tScheme = _uScheme(base)
        if (authority != null) {
            tAuth = authority
            tPath = _removeDotSegments(rest)
            tQuery = query
        } else {
            tAuth = _uAuth(base)
            if (rest.isEmpty()) {
                tPath = basePath
                tQuery = query ?: _uQuery(base)
            } else {
                if (rest.startsWith("/")) {
                    tPath = _removeDotSegments(rest)
                } else {
                    val merged = if (basePath.isEmpty()) "/" + rest else basePath.substring(0, basePath.lastIndexOf('/') + 1) + rest
                    tPath = _removeDotSegments(merged)
                }
                tQuery = query
            }
        }
    }
    if (tScheme != "http" && tScheme != "https") return null
    if (tAuth == null) return null
    val sb = StringBuilder()
    sb.append(tScheme).append("://").append(tAuth).append(tPath)
    if (tQuery != null) sb.append('?').append(tQuery)
    if (fragment != null) sb.append('#').append(fragment)
    return sb.toString()
}

private fun _readLine(input: java.io.InputStream): String {
    val buf = java.io.ByteArrayOutputStream()
    while (true) {
        val b = input.read()
        if (b < 0) throw java.io.IOException("connection closed")
        if (b == '\n'.code) break
        buf.write(b)
        if (buf.size() > 1048576) throw java.io.IOException("line too long")
    }
    val bytes = buf.toByteArray()
    var n = bytes.size
    if (n > 0 && bytes[n - 1] == '\r'.code.toByte()) n--
    return String(bytes, 0, n, Charsets.ISO_8859_1)
}

private fun _readExactly(input: java.io.InputStream, out: java.io.ByteArrayOutputStream, count: Long, limit: Long): Unit {
    if (out.size().toLong() + count > limit) throw java.io.IOException("body too large")
    var left = count
    val chunk = ByteArray(8192)
    while (left > 0) {
        val n = input.read(chunk, 0, minOf(left, chunk.size.toLong()).toInt())
        if (n < 0) throw java.io.IOException("truncated body")
        out.write(chunk, 0, n)
        left -= n
    }
}

private fun _findHeader(headers: List<real.posting.client.Header>, name: String): String? {
    for (h in headers) if (h.name.equals(name, ignoreCase = true)) return h.value
    return null
}

private fun _fetch(
    method: String,
    u: List<String?>,
    headers: List<real.posting.client.Header>,
    body: String,
    timeoutMs: Int,
): Triple<Int, List<real.posting.client.Header>, ByteArray> {
    val limit = real.posting.client.MAX_RESPONSE_BODY_BYTES.toLong()
    val host = _uHost(u)
    val connectHost = if (host.startsWith("[")) host.substring(1, host.length - 1) else host
    val port = _effPort(u)
    val https = _uScheme(u) == "https"
    val plain = java.net.Socket()
    var socket: java.net.Socket = plain
    try {
        plain.connect(java.net.InetSocketAddress(connectHost, port), timeoutMs)
        plain.soTimeout = timeoutMs
        if (https) {
            val factory = javax.net.ssl.SSLSocketFactory.getDefault() as javax.net.ssl.SSLSocketFactory
            val ssl = factory.createSocket(plain, connectHost, port, true) as javax.net.ssl.SSLSocket
            socket = ssl
            val params = ssl.sslParameters
            params.endpointIdentificationAlgorithm = "HTTPS"
            ssl.sslParameters = params
            ssl.soTimeout = timeoutMs
            ssl.startHandshake()
        }
        val uPath = _uPath(u)
        val uQuery = _uQuery(u)
        val path = (if (uPath.isEmpty()) "/" else uPath) + (if (uQuery != null) "?" + uQuery else "")
        val bodyBytes = body.toByteArray(Charsets.UTF_8)
        val head = StringBuilder()
        head.append(method).append(' ').append(path).append(" HTTP/1.1\r\n")
        if (_findHeader(headers, "Host") == null) {
            head.append("Host: ").append(host)
            val up = _uPort(u)
            if (up != null && up != _defaultPort(_uScheme(u))) head.append(':').append(up)
            head.append("\r\n")
        }
        for (h in headers) head.append(h.name).append(": ").append(h.value).append("\r\n")
        if (bodyBytes.isNotEmpty() && _findHeader(headers, "Content-Length") == null) {
            head.append("Content-Length: ").append(bodyBytes.size).append("\r\n")
        }
        if (_findHeader(headers, "Connection") == null) head.append("Connection: close\r\n")
        head.append("\r\n")
        val out = socket.getOutputStream()
        out.write(head.toString().toByteArray(Charsets.UTF_8))
        if (bodyBytes.isNotEmpty()) out.write(bodyBytes)
        out.flush()

        val input = java.io.BufferedInputStream(socket.getInputStream())
        while (true) {
            val line = _readLine(input)
            val sm = Regex("^HTTP/1\\.[0-9] ([0-9]{3})(?: .*)?$").find(line) ?: throw java.io.IOException("bad status line")
            val status = sm.groupValues[1].toInt()
            val hdrs = ArrayList<real.posting.client.Header>()
            while (true) {
                val l = _readLine(input)
                if (l.isEmpty()) break
                val idx = l.indexOf(':')
                if (idx < 0) throw java.io.IOException("bad header")
                hdrs.add(real.posting.client.Header(l.substring(0, idx), l.substring(idx + 1).trim()))
            }
            if (status in 100..199 && status != 101) continue
            if (status < 100 || status > 599) throw java.io.IOException("status out of range")
            val bodyOut = java.io.ByteArrayOutputStream()
            val noBody = method == "HEAD" || status in 100..199 || status == 204 || status == 304
            if (!noBody) {
                val te = _findHeader(hdrs, "Transfer-Encoding")
                val cl = _findHeader(hdrs, "Content-Length")
                if (te != null && te.lowercase().contains("chunked")) {
                    while (true) {
                        val sizeLine = _readLine(input)
                        val semi = sizeLine.indexOf(';')
                        val hex = (if (semi >= 0) sizeLine.substring(0, semi) else sizeLine).trim()
                        val size = hex.toLongOrNull(16) ?: throw java.io.IOException("bad chunk size")
                        if (size < 0) throw java.io.IOException("bad chunk size")
                        if (size == 0L) {
                            while (_readLine(input).isNotEmpty()) { }
                            break
                        }
                        _readExactly(input, bodyOut, size, limit)
                        if (_readLine(input).isNotEmpty()) throw java.io.IOException("bad chunk")
                    }
                } else if (cl != null) {
                    val n = cl.trim().toLongOrNull() ?: throw java.io.IOException("bad content-length")
                    if (n < 0) throw java.io.IOException("bad content-length")
                    _readExactly(input, bodyOut, n, limit)
                } else {
                    val chunk = ByteArray(8192)
                    while (true) {
                        val n = input.read(chunk)
                        if (n < 0) break
                        if (bodyOut.size().toLong() + n > limit) throw java.io.IOException("body too large")
                        bodyOut.write(chunk, 0, n)
                    }
                }
            }
            return Triple(status, hdrs, bodyOut.toByteArray())
        }
    } finally {
        try { socket.close() } catch (e: java.io.IOException) { }
        try { plain.close() } catch (e: java.io.IOException) { }
    }
}

private fun _decodeUtf8(bytes: ByteArray): String {
    val sb = StringBuilder(bytes.size)
    var i = 0
    val n = bytes.size
    while (i < n) {
        val b = bytes[i].toInt() and 0xFF
        if (b < 0x80) {
            sb.append(b.toChar())
            i++
            continue
        }
        var need = 0
        var lo = 0x80
        var hi = 0xBF
        var mask = 0
        if (b in 0xC2..0xDF) { need = 1; mask = 0x1F }
        else if (b == 0xE0) { need = 2; mask = 0x0F; lo = 0xA0 }
        else if (b == 0xED) { need = 2; mask = 0x0F; hi = 0x9F }
        else if (b in 0xE1..0xEF) { need = 2; mask = 0x0F }
        else if (b == 0xF0) { need = 3; mask = 0x07; lo = 0x90 }
        else if (b in 0xF1..0xF3) { need = 3; mask = 0x07 }
        else if (b == 0xF4) { need = 3; mask = 0x07; hi = 0x8F }
        if (need == 0) {
            sb.append('\uFFFD')
            i++
            continue
        }
        var cp = b and mask
        var j = i + 1
        var ok = true
        for (k in 0 until need) {
            if (j >= n) { ok = false; break }
            val c = bytes[j].toInt() and 0xFF
            val l = if (k == 0) lo else 0x80
            val h = if (k == 0) hi else 0xBF
            if (c < l || c > h) { ok = false; break }
            cp = (cp shl 6) or (c and 0x3F)
            j++
        }
        if (ok) sb.appendCodePoint(cp) else sb.append('\uFFFD')
        i = j
    }
    return sb.toString()
}

internal fun send_request(request: real.posting.client.Request): cott_runtime.CottResult<real.posting.client.Response, real.posting.client.PostingError> {
    if (request.timeout_ms == 0u) {
        return cott_runtime.Err(real.posting.client.PostingError.InvalidRequest("timeout_ms must be positive"))
    }
    val first = _parseUrl(request.url)
        ?: return cott_runtime.Err(real.posting.client.PostingError.InvalidRequest("invalid URL"))
    for (h in request.headers) {
        if (h.name.isBlank() || !_isToken(h.name)) {
            return cott_runtime.Err(real.posting.client.PostingError.InvalidRequest("invalid header name"))
        }
        if (h.value.indexOf('\r') >= 0 || h.value.indexOf('\n') >= 0) {
            return cott_runtime.Err(real.posting.client.PostingError.InvalidRequest("invalid header value"))
        }
    }
    val m = request.method
    if (m is real.posting.client.HttpMethod.Custom && !_isToken(m.name)) {
        return cott_runtime.Err(real.posting.client.PostingError.InvalidRequest("invalid method"))
    }
    val timeoutMs = if (request.timeout_ms > Int.MAX_VALUE.toUInt()) Int.MAX_VALUE else request.timeout_ms.toInt()
    val name = _methodName(m)
    val follows = m is real.posting.client.HttpMethod.Get || m is real.posting.client.HttpMethod.Head
    var cur = first
    var url = request.url
    var headers: List<real.posting.client.Header> = request.headers.toList()
    var redirects = 0
    try {
        while (true) {
            val (status, rh, bytes) = _fetch(name, cur, headers, request.body, timeoutMs)
            if (follows && redirects < 10 && (status == 301 || status == 302 || status == 303 || status == 307 || status == 308)) {
                val location = _findHeader(rh, "Location")
                if (location != null) {
                    val resolved = _resolve(cur, location)
                    val next = if (resolved != null) _parseUrl(resolved) else null
                    if (resolved != null && next != null && !(_uScheme(cur) == "https" && _uScheme(next) == "http")) {
                        if (!_sameOrigin(cur, next)) {
                            headers = headers.filter { h ->
                                !(h.name.equals("Authorization", true) || h.name.equals("Cookie", true) ||
                                    h.name.equals("Proxy-Authorization", true) || h.name.equals("Host", true))
                            }
                        }
                        cur = next
                        url = resolved
                        redirects++
                        continue
                    }
                }
            }
            return cott_runtime.Ok(
                real.posting.client.Response(
                    status.toUShort(),
                    url,
                    cott_runtime.CottList(rh),
                    _decodeUtf8(bytes),
                )
            )
        }
    } catch (e: java.io.IOException) {
        return cott_runtime.Err(real.posting.client.PostingError.NetworkFailed(e.message ?: "network failure"))
    } catch (e: RuntimeException) {
        return cott_runtime.Err(real.posting.client.PostingError.NetworkFailed(e.message ?: "network failure"))
    }
}
