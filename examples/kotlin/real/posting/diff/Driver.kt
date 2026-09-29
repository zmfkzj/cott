// Kotlin half of the posting differential harness.
//
// Calls the public facade package `real.posting.client` (cott-module.jar) for every case in
// `--cases` and prints one normalized JSON line per case on stdout; the normal form is the one
// `driver.py` prints (see README.md).  `run.py` compiles this file against the module JAR and
// runs it; anything the facade prints is diverted to stderr so the result stream stays clean.
//
// The JVM has no JSON reader, so a small one lives here.  Inputs are decoded JSON values
// (Map / List / String / Long / Boolean / null); results are built from the same value kinds.
@file:Suppress("UNCHECKED_CAST")

package posting_diff

import cott_runtime.CottContractViolation
import cott_runtime.CottList
import cott_runtime.Err
import cott_runtime.Ok
import java.io.File
import java.io.FileDescriptor
import java.io.FileOutputStream
import java.io.PrintStream
import java.security.MessageDigest
import java.util.concurrent.Callable
import java.util.concurrent.ExecutionException
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException
import kotlin.system.exitProcess
import real.posting.client.Header
import real.posting.client.HttpMethod
import real.posting.client.PostingError
import real.posting.client.Request
import real.posting.client.Response
import real.posting.client.execute
import real.posting.client.parse_arguments
import real.posting.client.parse_method
import real.posting.client.render_response
import real.posting.client.send_request

private const val DEFAULT_DEADLINE_S = 60.0

/** Malformed case data: reported as a driver error, never as a facade result. */
private class CaseError(message: String) : RuntimeException(message)

// ---- JSON -----------------------------------------------------------------------------

private class JsonReader(private val text: String) {
    private var pos = 0

    fun readDocument(): Any? {
        val value = readValue()
        skipWhitespace()
        if (pos != text.length) fail("trailing characters")
        return value
    }

    private fun fail(message: String): Nothing = throw IllegalArgumentException("JSON error at offset $pos: $message")

    private fun skipWhitespace() {
        while (pos < text.length && text[pos] in " \t\r\n") pos++
    }

    private fun readValue(): Any? {
        skipWhitespace()
        if (pos >= text.length) fail("unexpected end of input")
        val c = text[pos]
        return when {
            c == '{' -> readObject()
            c == '[' -> readArray()
            c == '"' -> readString()
            c == 't' -> literal("true", true)
            c == 'f' -> literal("false", false)
            c == 'n' -> literal("null", null)
            c == '-' || c in '0'..'9' -> readNumber()
            else -> fail("unexpected '$c'")
        }
    }

    private fun literal(word: String, value: Any?): Any? {
        if (!text.startsWith(word, pos)) fail("expected $word")
        pos += word.length
        return value
    }

    private fun readNumber(): Any {
        val start = pos
        if (text[pos] == '-') pos++
        while (pos < text.length && (text[pos] in '0'..'9' || text[pos] in ".eE+-")) pos++
        val token = text.substring(start, pos)
        return token.toLongOrNull() ?: token.toDoubleOrNull() ?: fail("bad number '$token'")
    }

    private fun readString(): String {
        pos++ // opening quote
        val out = StringBuilder()
        while (true) {
            if (pos >= text.length) fail("unterminated string")
            val c = text[pos++]
            when (c) {
                '"' -> return out.toString()
                '\\' -> {
                    if (pos >= text.length) fail("unterminated escape")
                    when (val escaped = text[pos++]) {
                        '"' -> out.append('"')
                        '\\' -> out.append('\\')
                        '/' -> out.append('/')
                        'b' -> out.append('\b')
                        'f' -> out.append('\u000c')
                        'n' -> out.append('\n')
                        'r' -> out.append('\r')
                        't' -> out.append('\t')
                        'u' -> {
                            if (pos + 4 > text.length) fail("truncated \\u escape")
                            out.append(text.substring(pos, pos + 4).toInt(16).toChar())
                            pos += 4
                        }
                        else -> fail("bad escape \\$escaped")
                    }
                }
                else -> out.append(c)
            }
        }
    }

    private fun readArray(): List<Any?> {
        pos++ // [
        val items = ArrayList<Any?>()
        skipWhitespace()
        if (pos < text.length && text[pos] == ']') {
            pos++
            return items
        }
        while (true) {
            items.add(readValue())
            skipWhitespace()
            if (pos >= text.length) fail("unterminated array")
            when (text[pos++]) {
                ',' -> continue
                ']' -> return items
                else -> fail("expected ',' or ']'")
            }
        }
    }

    private fun readObject(): Map<String, Any?> {
        pos++ // {
        val members = LinkedHashMap<String, Any?>()
        skipWhitespace()
        if (pos < text.length && text[pos] == '}') {
            pos++
            return members
        }
        while (true) {
            skipWhitespace()
            if (pos >= text.length || text[pos] != '"') fail("expected object key")
            val key = readString()
            skipWhitespace()
            if (pos >= text.length || text[pos++] != ':') fail("expected ':'")
            members[key] = readValue()
            skipWhitespace()
            if (pos >= text.length) fail("unterminated object")
            when (text[pos++]) {
                ',' -> continue
                '}' -> return members
                else -> fail("expected ',' or '}'")
            }
        }
    }
}

private fun parseJson(text: String): Any? = JsonReader(text).readDocument()

/** Writes ASCII-only JSON so the result stream is independent of any platform encoding. */
private fun writeJson(value: Any?, out: StringBuilder) {
    when (value) {
        null -> out.append("null")
        is Boolean -> out.append(value)
        is Int -> out.append(value)
        is Long -> out.append(value)
        is String -> writeJsonString(value, out)
        is Map<*, *> -> {
            out.append('{')
            var first = true
            for ((key, member) in value) {
                if (!first) out.append(',')
                first = false
                writeJsonString(key as String, out)
                out.append(':')
                writeJson(member, out)
            }
            out.append('}')
        }
        is List<*> -> {
            out.append('[')
            value.forEachIndexed { index, item ->
                if (index > 0) out.append(',')
                writeJson(item, out)
            }
            out.append(']')
        }
        else -> throw IllegalStateException("cannot encode ${value::class.java.name}")
    }
}

private fun writeJsonString(value: String, out: StringBuilder) {
    out.append('"')
    for (c in value) {
        when {
            c == '"' -> out.append("\\\"")
            c == '\\' -> out.append("\\\\")
            c == '\n' -> out.append("\\n")
            c == '\r' -> out.append("\\r")
            c == '\t' -> out.append("\\t")
            c.code < 0x20 || c.code > 0x7e -> out.append("\\u").append(String.format("%04x", c.code))
            else -> out.append(c)
        }
    }
    out.append('"')
}

// ---- case access ----------------------------------------------------------------------

private fun resolve(value: Any?, variables: Map<String, String>): Any? = when (value) {
    is String -> variables.entries.fold(value) { text, (name, replacement) -> text.replace("{$name}", replacement) }
    is List<*> -> value.map { resolve(it, variables) }
    is Map<*, *> -> value.entries.associateTo(LinkedHashMap<String, Any?>()) { (k, v) -> (k as String) to resolve(v, variables) }
    else -> value
}

private fun Map<String, Any?>.field(name: String): Any? =
    if (containsKey(name)) this[name] else throw CaseError("missing \"$name\"")

private fun Map<String, Any?>.requireKeys(vararg names: String) {
    val missing = names.filterNot { containsKey(it) }
    if (missing.isNotEmpty()) throw CaseError("missing $missing")
}

private fun Map<String, Any?>.text(name: String): String =
    field(name) as? String ?: throw CaseError("\"$name\" must be a string")

private fun Map<String, Any?>.integer(name: String): Long =
    field(name) as? Long ?: throw CaseError("\"$name\" must be an integer")

private fun Map<String, Any?>.obj(name: String): Map<String, Any?> =
    field(name) as? Map<String, Any?> ?: throw CaseError("\"$name\" must be an object")

private fun Map<String, Any?>.list(name: String): List<Any?> =
    field(name) as? List<Any?> ?: throw CaseError("\"$name\" must be an array")

private fun Map<String, Any?>.strings(name: String): List<String> =
    list(name).map { it as? String ?: throw CaseError("\"$name\" must hold strings") }

// ---- building typed inputs ------------------------------------------------------------

private fun buildMethod(spec: Any?): HttpMethod {
    val variant: String
    var name: String? = null
    if (spec is String) {
        variant = spec
    } else {
        val fields = spec as? Map<String, Any?> ?: throw CaseError("method must be a string or object")
        variant = fields.text("variant")
        name = fields["name"] as? String
    }
    return when (variant) {
        "Get" -> HttpMethod.Get
        "Head" -> HttpMethod.Head
        "Post" -> HttpMethod.Post
        "Put" -> HttpMethod.Put
        "Patch" -> HttpMethod.Patch
        "Delete" -> HttpMethod.Delete
        "Options" -> HttpMethod.Options
        "Custom" -> HttpMethod.Custom(name ?: throw CaseError("Custom method needs a name"))
        else -> throw CaseError("unknown method variant \"$variant\"")
    }
}

private fun buildHeaders(pairs: List<Any?>): CottList<Header> = CottList(
    pairs.map { pair ->
        val entry = pair as? List<Any?> ?: throw CaseError("header must be a [name, value] pair")
        if (entry.size != 2) throw CaseError("header must be a [name, value] pair")
        Header(entry[0] as? String ?: throw CaseError("header name"), entry[1] as? String ?: throw CaseError("header value"))
    },
)

// ---- normalizing outputs --------------------------------------------------------------

private fun normMethod(method: HttpMethod): Map<String, Any?> = when (method) {
    is HttpMethod.Get -> mapOf("variant" to "Get")
    is HttpMethod.Head -> mapOf("variant" to "Head")
    is HttpMethod.Post -> mapOf("variant" to "Post")
    is HttpMethod.Put -> mapOf("variant" to "Put")
    is HttpMethod.Patch -> mapOf("variant" to "Patch")
    is HttpMethod.Delete -> mapOf("variant" to "Delete")
    is HttpMethod.Options -> mapOf("variant" to "Options")
    is HttpMethod.Custom -> mapOf("variant" to "Custom", "name" to method.name)
}

private fun normHeaders(headers: List<Header>): List<Map<String, Any?>> =
    headers.map { mapOf("name" to it.name, "value" to it.value) }

private fun normBody(body: String, digest: Boolean): Map<String, Any?> {
    if (!digest) return mapOf("body" to body)
    val data = body.toByteArray(Charsets.UTF_8)
    val hash = MessageDigest.getInstance("SHA-256").digest(data).joinToString("") { String.format("%02x", it) }
    return mapOf("body_digest" to mapOf("utf8_len" to data.size.toLong(), "sha256" to hash))
}

private fun normValue(value: Any?, digest: Boolean): Any? = when (value) {
    is String -> value
    is Request -> mapOf(
        "method" to normMethod(value.method),
        "url" to value.url,
        "headers" to normHeaders(value.headers),
        "body" to value.body,
        "timeout_ms" to value.timeout_ms.toLong(),
    )
    is Response -> mapOf(
        "status" to value.status.toInt().toLong(),
        "url" to value.url,
        "headers" to normHeaders(value.headers),
    ) + normBody(value.body, digest)
    is HttpMethod -> normMethod(value)
    else -> mapOf("unexpected_type" to (value?.let { it::class.java.simpleName } ?: "null"))
}

private fun normError(error: Any?): Map<String, Any?> = when (error) {
    is PostingError.InvalidArguments -> mapOf("variant" to "InvalidArguments", "message_present" to error.message.isNotEmpty())
    is PostingError.InvalidRequest -> mapOf("variant" to "InvalidRequest", "message_present" to error.message.isNotEmpty())
    is PostingError.NetworkFailed -> mapOf("variant" to "NetworkFailed", "message_present" to error.message.isNotEmpty())
    else -> mapOf("unexpected_type" to (error?.let { it::class.java.simpleName } ?: "null"))
}

private fun normResult(result: Any?, digest: Boolean = false): Map<String, Any?> = when (result) {
    is Ok<*> -> mapOf("tag" to "Ok", "value" to normValue(result.value, digest))
    is Err<*> -> mapOf("tag" to "Err", "error" to normError(result.error))
    is String -> mapOf("tag" to "Str", "value" to result)
    else -> mapOf("tag" to "Unexpected", "type" to (result?.let { it::class.java.simpleName } ?: "null"))
}

/**
 * A boundary violation is an input the ABI rejects before any implementation code runs (an unpaired surrogate in a Str,
 * say); anything else that is thrown, including a violation of the implementation's return value ("$.return" paths) or
 * of an ensures/error clause, is a fault of the implementation and stays a Raise.
 */
private fun normThrowable(error: Throwable): Map<String, Any?> {
    if (error is CottContractViolation && error.phase == "validation" && !error.detail.startsWith("\$.return")) {
        return mapOf("tag" to "Violation", "phase" to error.phase)
    }
    val out = LinkedHashMap<String, Any?>()
    out["tag"] = "Raise"
    out["type"] = error::class.java.simpleName
    if (error is CottContractViolation) {
        out["phase"] = error.phase
        out["clause"] = error.clause
    }
    return out
}

// ---- running cases --------------------------------------------------------------------

/** Validates the case data eagerly and returns the call into the facade. */
private fun prepare(case: Map<String, Any?>): () -> Map<String, Any?> {
    val digest = case["body_digest"] == true
    when (val fn = case.text("fn")) {
        "parse_method" -> {
            val source = case.text("source")
            return { normResult(parse_method(source)) }
        }
        "parse_arguments" -> {
            val arguments = case.strings("arguments")
            return { normResult(parse_arguments(CottList(arguments))) }
        }
        "execute" -> {
            val arguments = case.strings("arguments")
            return { normResult(execute(CottList(arguments))) }
        }
        "send_request" -> {
            val spec = case.obj("request")
            spec.requireKeys("method", "url", "headers", "body", "timeout_ms")
            return {
                val request = Request(
                    buildMethod(spec["method"]),
                    spec.text("url"),
                    buildHeaders(spec.list("headers")),
                    spec.text("body"),
                    spec.integer("timeout_ms").toUInt(),
                )
                normResult(send_request(request), digest)
            }
        }
        "render_response" -> {
            val spec = case.obj("response")
            spec.requireKeys("status", "url", "headers", "body")
            return {
                val response = Response(
                    spec.integer("status").toUShort(),
                    spec.text("url"),
                    buildHeaders(spec.list("headers")),
                    spec.text("body"),
                )
                normResult(render_response(response))
            }
        }
        else -> throw CaseError("unknown fn \"$fn\"")
    }
}

private class Outcome(val result: Map<String, Any?>? = null, val driverError: String? = null)

private val pool = Executors.newCachedThreadPool { runnable -> Thread(runnable, "case").apply { isDaemon = true } }

/** Runs one case on a daemon thread so a hung implementation cannot stall the run. */
private fun runCase(case: Map<String, Any?>, deadlineS: Double): Outcome {
    val thunk = try {
        prepare(case)
    } catch (error: CaseError) {
        return Outcome(driverError = "malformed case: ${error.message}")
    }
    val future = pool.submit(
        Callable {
            try {
                thunk()
            } catch (error: Throwable) {
                error.printStackTrace()
                normThrowable(error)
            }
        },
    )
    return try {
        Outcome(result = future.get((deadlineS * 1000).toLong(), TimeUnit.MILLISECONDS))
    } catch (error: TimeoutException) {
        future.cancel(true)
        Outcome(driverError = "no result within ${deadlineS}s (case abandoned)")
    } catch (error: ExecutionException) {
        Outcome(driverError = "driver failure: ${error.cause}")
    }
}

/** Pays one-time class-loading and connection costs before any case is timed. */
private fun warmUp(variables: Map<String, String>) {
    try {
        parse_method("GET")
        send_request(
            Request(HttpMethod.Get, variables.getValue("A") + "/text", CottList(emptyList()), "", 10000u),
        )
    } catch (error: Throwable) {
        // The warm-up outcome is irrelevant.
    }
}

fun main(args: Array<String>) {
    var casesPath: String? = null
    var varsPath: String? = null
    var index = 0
    while (index < args.size) {
        when (args[index]) {
            "--cases" -> casesPath = args.getOrNull(++index)
            "--vars" -> varsPath = args.getOrNull(++index)
            else -> {
                System.err.println("usage: Driver --cases FILE --vars FILE")
                exitProcess(2)
            }
        }
        index++
    }
    if (casesPath == null || varsPath == null) {
        System.err.println("usage: Driver --cases FILE --vars FILE")
        exitProcess(2)
    }
    val results = PrintStream(FileOutputStream(FileDescriptor.out), false, "US-ASCII")
    System.setOut(System.err)
    val cases = parseJson(File(casesPath).readText(Charsets.UTF_8)) as List<Any?>
    val rawVariables = parseJson(File(varsPath).readText(Charsets.UTF_8)) as Map<String, Any?>
    val variables = rawVariables.mapValues { it.value as String }
    warmUp(variables)
    for (raw in cases) {
        val case = resolve(raw, variables) as Map<String, Any?>
        val started = System.nanoTime()
        val deadline = (case["deadline_s"] as? Number)?.toDouble() ?: DEFAULT_DEADLINE_S
        val outcome = runCase(case, deadline)
        val record = LinkedHashMap<String, Any?>()
        record["case"] = case["id"]
        record["ms"] = (System.nanoTime() - started) / 1_000_000
        if (outcome.result != null) record["result"] = outcome.result else record["driver_error"] = outcome.driverError
        val line = StringBuilder()
        writeJson(record, line)
        results.print(line.append('\n'))
        results.flush()
    }
    results.flush()
    exitProcess(0)
}
