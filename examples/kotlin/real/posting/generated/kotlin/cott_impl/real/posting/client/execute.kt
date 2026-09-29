package cott_impl.real.posting.client

internal fun execute(arguments: cott_runtime.CottList<kotlin.String>): cott_runtime.CottResult<kotlin.String, real.posting.client.PostingError> {
    if (arguments.size < 2 || arguments.size > 3) {
        return cott_runtime.Err(real.posting.client.PostingError.InvalidArguments("expected METHOD URL [BODY]"))
    }
    val method = _parseMethod(arguments[0])
        ?: return cott_runtime.Err(real.posting.client.PostingError.InvalidRequest("invalid HTTP method: " + arguments[0]))
    val request = real.posting.client.Request(
        method,
        arguments[1],
        cott_runtime.CottList(emptyList<real.posting.client.Header>()),
        if (arguments.size == 3) arguments[2] else "",
        30000u
    )
    val sent = _send(request)
    val response = sent.first
    if (response == null) {
        return cott_runtime.Err(sent.second ?: real.posting.client.PostingError.NetworkFailed("request failed"))
    }
    return cott_runtime.Ok(_render(response))
}

private fun _isToken(s: kotlin.String): kotlin.Boolean {
    if (s.isEmpty()) return false
    for (c in s) {
        val ok = (c in 'A'..'Z') || (c in 'a'..'z') || (c in '0'..'9') || "!#$%&'*+-.^_`|~".indexOf(c) >= 0
        if (!ok) return false
    }
    return true
}

private fun _parseMethod(source: kotlin.String): real.posting.client.HttpMethod? {
    if (!_isToken(source)) return null
    return when (source.uppercase(java.util.Locale.ROOT)) {
        "GET" -> real.posting.client.HttpMethod.Get
        "HEAD" -> real.posting.client.HttpMethod.Head
        "POST" -> real.posting.client.HttpMethod.Post
        "PUT" -> real.posting.client.HttpMethod.Put
        "PATCH" -> real.posting.client.HttpMethod.Patch
        "DELETE" -> real.posting.client.HttpMethod.Delete
        "OPTIONS" -> real.posting.client.HttpMethod.Options
        else -> real.posting.client.HttpMethod.Custom(source)
    }
}

private fun _methodName(m: real.posting.client.HttpMethod): kotlin.String = when (m) {
    is real.posting.client.HttpMethod.Get -> "GET"
    is real.posting.client.HttpMethod.Head -> "HEAD"
    is real.posting.client.HttpMethod.Post -> "POST"
    is real.posting.client.HttpMethod.Put -> "PUT"
    is real.posting.client.HttpMethod.Patch -> "PATCH"
    is real.posting.client.HttpMethod.Delete -> "DELETE"
    is real.posting.client.HttpMethod.Options -> "OPTIONS"
    is real.posting.client.HttpMethod.Custom -> m.name
}

private fun _render(r: real.posting.client.Response): kotlin.String {
    val sb = StringBuilder()
    sb.append(r.status.toString()).append(' ').append(r.url).append('\n')
    for (h in r.headers) {
        sb.append(h.name).append(": ").append(h.value).append('\n')
    }
    sb.append('\n')
    sb.append(r.body)
    return sb.toString()
}

private fun _isHex(c: kotlin.Char): kotlin.Boolean = (c in '0'..'9') || (c in 'a'..'f') || (c in 'A'..'F')

private fun _urlCharsOk(s: kotlin.String): kotlin.Boolean {
    var i = 0
    while (i < s.length) {
        val c = s[i]
        if (c == '%') {
            if (i + 2 >= s.length || !_isHex(s[i + 1]) || !_isHex(s[i + 2])) return false
        } else {
            val ok = (c in 'A'..'Z') || (c in 'a'..'z') || (c in '0'..'9') || "-._~:/?#[]@!$&'()*+,;=".indexOf(c) >= 0
            if (!ok) return false
        }
        i++
    }
    return true
}

// Returns [scheme, authority, path, query, fragment]; scheme/authority/query/fragment may be null.
private fun _splitRef(s: kotlin.String): Array<kotlin.String?> {
    var scheme: kotlin.String? = null
    var rest = s
    val p = s.indexOf(':')
    if (p > 0) {
        val cand = s.substring(0, p)
        val okScheme = cand[0].let { (it in 'A'..'Z') || (it in 'a'..'z') } &&
            cand.all { (it in 'A'..'Z') || (it in 'a'..'z') || (it in '0'..'9') || it == '+' || it == '-' || it == '.' }
        if (okScheme) {
            scheme = cand
            rest = s.substring(p + 1)
        }
    }
    var fragment: kotlin.String? = null
    val h = rest.indexOf('#')
    if (h >= 0) {
        fragment = rest.substring(h + 1)
        rest = rest.substring(0, h)
    }
    var query: kotlin.String? = null
    val q = rest.indexOf('?')
    if (q >= 0) {
        query = rest.substring(q + 1)
        rest = rest.substring(0, q)
    }
    var authority: kotlin.String? = null
    if (rest.startsWith("//")) {
        val after = rest.substring(2)
        val sl = after.indexOf('/')
        if (sl >= 0) {
            authority = after.substring(0, sl)
            rest = after.substring(sl)
        } else {
            authority = after
            rest = ""
        }
    }
    return arrayOf(scheme, authority, rest, query, fragment)
}

// Returns [host, port-digits-or-empty] or null when invalid.
private fun _hostInfo(authority: kotlin.String): Array<kotlin.String>? {
    val at = authority.lastIndexOf('@')
    val hp = authority.substring(at + 1)
    val host: kotlin.String
    val rest: kotlin.String
    if (hp.startsWith("[")) {
        val close = hp.indexOf(']')
        if (close < 0) return null
        host = hp.substring(0, close + 1)
        rest = hp.substring(close + 1)
        if (host.length <= 2) return null
    } else {
        val colon = hp.indexOf(':')
        host = if (colon < 0) hp else hp.substring(0, colon)
        rest = if (colon < 0) "" else hp.substring(colon)
    }
    if (host.isEmpty()) return null
    var port = ""
    if (rest.isNotEmpty()) {
        if (rest[0] != ':') return null
        port = rest.substring(1)
        if (port.length > 5 || !port.all { it in '0'..'9' }) return null
        if (port.isNotEmpty() && port.toInt() > 65535) return null
        if (port.isNotEmpty()) port = port.toInt().toString()
    }
    return arrayOf(host, port)
}

private fun _removeDotSegments(path: kotlin.String): kotlin.String {
    var input = path
    val out = StringBuilder()
    while (input.isNotEmpty()) {
        if (input.startsWith("../")) {
            input = input.substring(3)
        } else if (input.startsWith("./")) {
            input = input.substring(2)
        } else if (input.startsWith("/./")) {
            input = "/" + input.substring(3)
        } else if (input == "/.") {
            input = "/"
        } else if (input.startsWith("/../")) {
            input = "/" + input.substring(4)
            val idx = out.lastIndexOf("/")
            out.setLength(if (idx < 0) 0 else idx)
        } else if (input == "/..") {
            input = "/"
            val idx = out.lastIndexOf("/")
            out.setLength(if (idx < 0) 0 else idx)
        } else if (input == "." || input == "..") {
            input = ""
        } else {
            val start = if (input[0] == '/') 1 else 0
            var end = input.indexOf('/', start)
            if (end < 0) end = input.length
            out.append(input, 0, end)
            input = input.substring(end)
        }
    }
    return out.toString()
}

// Resolves ref against base (both already split); returns URL string.
private fun _resolve(base: Array<kotlin.String?>, ref: Array<kotlin.String?>): kotlin.String {
    val scheme: kotlin.String
    val authority: kotlin.String?
    val path: kotlin.String
    val query: kotlin.String?
    val refPath = ref[2] ?: ""
    if (ref[0] != null) {
        scheme = ref[0]!!
        authority = ref[1]
        path = _removeDotSegments(refPath)
        query = ref[3]
    } else {
        scheme = base[0]!!
        if (ref[1] != null) {
            authority = ref[1]
            path = _removeDotSegments(refPath)
            query = ref[3]
        } else {
            authority = base[1]
            val basePath = base[2] ?: ""
            if (refPath.isEmpty()) {
                path = basePath
                query = ref[3] ?: base[3]
            } else {
                if (refPath.startsWith("/")) {
                    path = _removeDotSegments(refPath)
                } else {
                    val merged = if (base[1] != null && basePath.isEmpty()) {
                        "/" + refPath
                    } else {
                        val ls = basePath.lastIndexOf('/')
                        (if (ls < 0) "" else basePath.substring(0, ls + 1)) + refPath
                    }
                    path = _removeDotSegments(merged)
                }
                query = ref[3]
            }
        }
    }
    val sb = StringBuilder()
    sb.append(scheme.lowercase(java.util.Locale.ROOT)).append(':')
    if (authority != null) sb.append("//").append(authority)
    sb.append(path)
    if (query != null) sb.append('?').append(query)
    if (ref[4] != null) sb.append('#').append(ref[4])
    return sb.toString()
}

private fun _invalid(msg: kotlin.String): kotlin.Pair<real.posting.client.Response?, real.posting.client.PostingError?> =
    kotlin.Pair(null, real.posting.client.PostingError.InvalidRequest(msg))

private fun _defaultPort(scheme: kotlin.String): kotlin.Int = if (scheme == "https") 443 else 80

private fun _origin(parts: Array<kotlin.String?>, info: Array<kotlin.String>): kotlin.String {
    val scheme = parts[0]!!.lowercase(java.util.Locale.ROOT)
    val port = if (info[1].isEmpty()) _defaultPort(scheme) else info[1].toInt()
    return scheme + "|" + info[0].lowercase(java.util.Locale.ROOT) + "|" + port
}

private fun _send(request: real.posting.client.Request): kotlin.Pair<real.posting.client.Response?, real.posting.client.PostingError?> {
    if (request.timeout_ms == 0u) return _invalid("timeout_ms is 0")
    if (!(request.url.startsWith("http://") || request.url.startsWith("https://"))) return _invalid("unsupported URL scheme")
    if (!_urlCharsOk(request.url)) return _invalid("URL contains invalid characters")
    val firstParts = _splitRef(request.url)
    val firstAuth = firstParts[1] ?: return _invalid("URL has no host")
    if (_hostInfo(firstAuth) == null) return _invalid("invalid URL host or port")
    for (h in request.headers) {
        if (!_isToken(h.name)) return _invalid("invalid header name")
        if (h.value.indexOf('\r') >= 0 || h.value.indexOf('\n') >= 0) return _invalid("invalid header value")
    }
    val method = request.method
    if (method is real.posting.client.HttpMethod.Custom && !_isToken(method.name)) return _invalid("invalid method")

    val follows = method is real.posting.client.HttpMethod.Get || method is real.posting.client.HttpMethod.Head
    val timeout = request.timeout_ms.toLong().coerceAtMost(Int.MAX_VALUE.toLong()).toInt()
    var currentUrl = request.url
    var headers: List<real.posting.client.Header> = request.headers.toList()
    var redirects = 0
    try {
        while (true) {
            val response = _fetch(method, currentUrl, headers, request.body, timeout)
            val s = response.status.toInt()
            if (!follows || redirects >= 10 || !(s == 301 || s == 302 || s == 303 || s == 307 || s == 308)) {
                return kotlin.Pair(response, null)
            }
            val loc = response.headers.firstOrNull { it.name.equals("Location", ignoreCase = true) }
                ?: return kotlin.Pair(response, null)
            val ref = loc.value
            if (!_urlCharsOk(ref)) return kotlin.Pair(response, null)
            val baseParts = _splitRef(currentUrl)
            val target = _resolve(baseParts, _splitRef(ref))
            val tParts = _splitRef(target)
            val tScheme = tParts[0]?.lowercase(java.util.Locale.ROOT)
            if (tScheme != "http" && tScheme != "https") return kotlin.Pair(response, null)
            val tAuth = tParts[1] ?: return kotlin.Pair(response, null)
            val tInfo = _hostInfo(tAuth) ?: return kotlin.Pair(response, null)
            val bInfo = _hostInfo(baseParts[1]!!) ?: return kotlin.Pair(response, null)
            if (baseParts[0]!!.lowercase(java.util.Locale.ROOT) == "https" && tScheme == "http") {
                return kotlin.Pair(response, null)
            }
            if (_origin(baseParts, bInfo) != _origin(tParts, tInfo)) {
                headers = headers.filter {
                    !(it.name.equals("Authorization", ignoreCase = true) ||
                        it.name.equals("Cookie", ignoreCase = true) ||
                        it.name.equals("Proxy-Authorization", ignoreCase = true) ||
                        it.name.equals("Host", ignoreCase = true))
                }
            }
            currentUrl = target
            redirects++
        }
    } catch (e: java.io.IOException) {
        return kotlin.Pair(null, real.posting.client.PostingError.NetworkFailed(e.message ?: "network failure"))
    } catch (e: RuntimeException) {
        return kotlin.Pair(null, real.posting.client.PostingError.NetworkFailed(e.message ?: "network failure"))
    }
}

private fun _readLine(input: java.io.InputStream): kotlin.String {
    val buf = java.io.ByteArrayOutputStream()
    while (true) {
        val b = input.read()
        if (b < 0) throw java.io.IOException("connection closed before complete response")
        if (b == '\n'.code) break
        buf.write(b)
        if (buf.size() > 1048576) throw java.io.IOException("line too long")
    }
    val bytes = buf.toByteArray()
    var n = bytes.size
    if (n > 0 && bytes[n - 1] == '\r'.code.toByte()) n--
    return String(bytes, 0, n, Charsets.ISO_8859_1)
}

private fun _readExactly(input: java.io.InputStream, out: java.io.ByteArrayOutputStream, count: kotlin.Long, limit: kotlin.Long): kotlin.Unit {
    if (out.size().toLong() + count > limit) throw java.io.IOException("response body too large")
    var remaining = count
    val chunk = ByteArray(8192)
    while (remaining > 0) {
        val n = input.read(chunk, 0, minOf(remaining, chunk.size.toLong()).toInt())
        if (n < 0) throw java.io.IOException("connection closed before complete response")
        out.write(chunk, 0, n)
        remaining -= n
    }
}

private fun _decodeUtf8(bytes: ByteArray): kotlin.String {
    val sb = StringBuilder(bytes.size)
    var i = 0
    val size = bytes.size
    while (i < size) {
        val b = bytes[i].toInt() and 0xFF
        if (b < 0x80) {
            sb.append(b.toChar())
            i++
            continue
        }
        var n = 0
        var lo = 0x80
        var hi = 0xBF
        var cp = 0
        if (b in 0xC2..0xDF) {
            n = 2; cp = b and 0x1F
        } else if (b in 0xE0..0xEF) {
            n = 3; cp = b and 0x0F
            if (b == 0xE0) lo = 0xA0
            if (b == 0xED) hi = 0x9F
        } else if (b in 0xF0..0xF4) {
            n = 4; cp = b and 0x07
            if (b == 0xF0) lo = 0x90
            if (b == 0xF4) hi = 0x8F
        }
        if (n == 0) {
            sb.append('\uFFFD')
            i++
            continue
        }
        var j = i + 1
        var complete = true
        var k = 1
        while (k < n) {
            val cLo = if (k == 1) lo else 0x80
            val cHi = if (k == 1) hi else 0xBF
            val c = if (j < size) bytes[j].toInt() and 0xFF else -1
            if (c < cLo || c > cHi) {
                complete = false
                break
            }
            cp = (cp shl 6) or (c and 0x3F)
            j++
            k++
        }
        if (complete) sb.appendCodePoint(cp) else sb.append('\uFFFD')
        i = j
    }
    return sb.toString()
}

private fun _fetch(
    method: real.posting.client.HttpMethod,
    url: kotlin.String,
    headers: List<real.posting.client.Header>,
    body: kotlin.String,
    timeout: kotlin.Int
): real.posting.client.Response {
    val parts = _splitRef(url)
    val https = parts[0]!!.lowercase(java.util.Locale.ROOT) == "https"
    val info = _hostInfo(parts[1]!!) ?: throw java.io.IOException("invalid URL")
    val rawHost = info[0]
    val bare = if (rawHost.startsWith("[")) rawHost.substring(1, rawHost.length - 1) else rawHost
    val defaultPort = if (https) 443 else 80
    val port = if (info[1].isEmpty()) defaultPort else info[1].toInt()
    val limit = real.posting.client.MAX_RESPONSE_BODY_BYTES.toLong()
    val plain = java.net.Socket()
    try {
        plain.connect(java.net.InetSocketAddress(bare, port), timeout)
        plain.soTimeout = timeout
        val socket: java.net.Socket = if (https) {
            val factory = javax.net.ssl.SSLSocketFactory.getDefault() as javax.net.ssl.SSLSocketFactory
            val ssl = factory.createSocket(plain, bare, port, true)
            ssl.soTimeout = timeout
            (ssl as javax.net.ssl.SSLSocket).startHandshake()
            ssl
        } else plain

        var target = parts[2] ?: ""
        if (target.isEmpty()) target = "/"
        if (parts[3] != null) target = target + "?" + parts[3]
        val sb = StringBuilder()
        sb.append(_methodName(method)).append(' ').append(target).append(" HTTP/1.1\r\n")
        if (headers.none { it.name.equals("Host", ignoreCase = true) }) {
            sb.append("Host: ").append(rawHost)
            if (info[1].isNotEmpty() && port != defaultPort) sb.append(':').append(port)
            sb.append("\r\n")
        }
        for (h in headers) sb.append(h.name).append(": ").append(h.value).append("\r\n")
        val payload = body.toByteArray(Charsets.UTF_8)
        if (payload.isNotEmpty()) {
            sb.append("Content-Length: ").append(payload.size).append("\r\n")
        }
        sb.append("Connection: close\r\n\r\n")
        val out = socket.getOutputStream()
        out.write(sb.toString().toByteArray(Charsets.UTF_8))
        if (payload.isNotEmpty()) out.write(payload)
        out.flush()

        val input = java.io.BufferedInputStream(socket.getInputStream())
        val statusLine = _readLine(input)
        if (!statusLine.startsWith("HTTP/1.")) throw java.io.IOException("malformed status line")
        val sp = statusLine.indexOf(' ')
        if (sp < 0 || statusLine.length < sp + 4) throw java.io.IOException("malformed status line")
        val code = statusLine.substring(sp + 1, sp + 4)
        if (!code.all { it in '0'..'9' } || (statusLine.length > sp + 4 && statusLine[sp + 4] != ' ')) {
            throw java.io.IOException("malformed status line")
        }
        val status = code.toInt()
        val received = ArrayList<real.posting.client.Header>()
        while (true) {
            val line = _readLine(input)
            if (line.isEmpty()) break
            val idx = line.indexOf(':')
            if (idx < 0) throw java.io.IOException("malformed header line")
            received.add(real.posting.client.Header(line.substring(0, idx), line.substring(idx + 1).trim(' ', '\t')))
        }
        if (status < 100 || status > 599) throw java.io.IOException("status out of range")

        val bodyBytes = java.io.ByteArrayOutputStream()
        val noBody = method is real.posting.client.HttpMethod.Head || status < 200 || status == 204 || status == 304
        if (!noBody) {
            val te = received.firstOrNull { it.name.equals("Transfer-Encoding", ignoreCase = true) }
            val cl = received.firstOrNull { it.name.equals("Content-Length", ignoreCase = true) }
            if (te != null && te.value.lowercase(java.util.Locale.ROOT).contains("chunked")) {
                while (true) {
                    val sizeLine = _readLine(input)
                    val semi = sizeLine.indexOf(';')
                    val hex = (if (semi >= 0) sizeLine.substring(0, semi) else sizeLine).trim()
                    if (hex.isEmpty() || !hex.all { _isHex(it) } || hex.length > 15) throw java.io.IOException("bad chunk size")
                    val size = hex.toLong(16)
                    if (size == 0L) {
                        while (_readLine(input).isNotEmpty()) { }
                        break
                    }
                    _readExactly(input, bodyBytes, size, limit)
                    _readLine(input)
                }
            } else if (cl != null) {
                val v = cl.value.trim()
                if (v.isEmpty() || !v.all { it in '0'..'9' } || v.length > 18) throw java.io.IOException("bad Content-Length")
                _readExactly(input, bodyBytes, v.toLong(), limit)
            } else {
                val chunk = ByteArray(8192)
                while (true) {
                    val n = input.read(chunk)
                    if (n < 0) break
                    if (bodyBytes.size().toLong() + n > limit) throw java.io.IOException("response body too large")
                    bodyBytes.write(chunk, 0, n)
                }
            }
        }
        return real.posting.client.Response(
            status.toUShort(),
            url,
            cott_runtime.CottList(received),
            _decodeUtf8(bodyBytes.toByteArray())
        )
    } finally {
        try {
            plain.close()
        } catch (e: java.io.IOException) {
        }
    }
}
