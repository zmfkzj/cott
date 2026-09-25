// Cott's compiler-owned Kotlin/JVM runtime.
// Coroutine coordination uses the pinned kotlinx.coroutines runtime dependency.
@file:Suppress("UNCHECKED_CAST")
@file:OptIn(
    kotlinx.coroutines.DelicateCoroutinesApi::class,
    kotlinx.coroutines.ExperimentalCoroutinesApi::class,
)

package cott_runtime

import kotlinx.coroutines.CancellableContinuation
import kotlinx.coroutines.CopyableThreadContextElement
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.withContext
import java.math.BigInteger
import java.net.URI
import java.nio.file.Path
import java.util.ArrayDeque
import java.util.Collections
import java.util.IdentityHashMap
import java.util.LinkedHashMap
import java.util.LinkedHashSet
import java.util.concurrent.CountDownLatch
import java.util.concurrent.CancellationException
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.locks.ReentrantLock
import kotlin.coroutines.AbstractCoroutineContextElement
import kotlin.coroutines.CoroutineContext
import kotlin.coroutines.coroutineContext
import kotlin.coroutines.resume


public enum class RuntimeValidation {
    BOUNDARY,
    TEST_ONLY,
    OFF,
}

public enum class CottIntKind {
    I8,
    I16,
    I32,
    I64,
    U8,
    U16,
    U32,
    U64,
}

public interface CottConst {
    public val value: BigInteger
}

public interface CottOpaqueTag {
    public val tag: String
}


public interface CottFieldValue {
    public val cottTypeIdentity: String
    public val cottFieldNames: CottList<String>
    public fun cottField(name: String): Any?
}

public interface CottVariant : CottFieldValue {
    override val cottTypeIdentity: String get() = cottVariant
    public val cottVariant: String
    public val cottPayload: CottList<Any?>
}

public interface CottTupleValue {
    public val cottTupleElements: CottList<Any?>
    public fun cottRebuild(elements: CottList<Any?>): CottTupleValue
}

public interface CottTraitCarrier {
    public val cottTraits: CottSet<CottTrait<*>>
}

public data class CottSpan(
    public val startByte: Int,
    public val endByte: Int,
    public val startLine: Int,
    public val startColumn: Int,
    public val endLine: Int,
    public val endColumn: Int,
) {
    init {
        require(startByte >= 0 && endByte >= startByte) { "invalid byte span" }
        require(startLine >= 1 && endLine >= startLine) { "invalid line span" }
        require(startColumn >= 1 && endColumn >= 1) { "invalid column span" }
    }
}

public open class CottContractViolation(
    public val detail: String,
    public var symbol: String? = null,
    public val phase: String? = null,
    public var span: CottSpan? = null,
    public val expected: String? = null,
    public val actual: String? = null,
    public val clause: String? = null,
    cause: Throwable? = null,
) : RuntimeException(renderMessage(detail, symbol, phase, clause, expected, actual), cause) {
    private companion object {
        private fun renderMessage(
            detail: String,
            symbol: String?,
            phase: String?,
            clause: String?,
            expected: String?,
            actual: String?,
        ): String = buildString {
            append(detail)
            if (symbol != null) append(" [symbol=").append(symbol).append(']')
            if (phase != null) append(" [phase=").append(phase).append(']')
            if (clause != null) append(" [clause=").append(clause).append(']')
            if (expected != null) append(" [expected=").append(expected).append(']')
            if (actual != null) append(" [actual=").append(actual).append(']')
        }
    }
}

private class CottTraversalViolation(message: String) :
    CottContractViolation(message, phase = "validation")

public data class CottClauseObservation(
    public val symbol: String,
    public val clause: String,
    public val phase: String,
    public val passed: Boolean,
)

public class CottObservation public constructor() {
    private val values = ArrayList<CottClauseObservation>()

    internal fun record(observation: CottClauseObservation) {
        synchronized(values) { values.add(observation) }
    }

    public fun observations(): CottList<CottClauseObservation> =
        synchronized(values) { CottList(values) }
}

public data class CottFixtureKey(
    public val fixture: String,
    public val path: String,
)

public class CottFixtureContext public constructor(
    root: Path,
    urls: Map<CottFixtureKey, String>,
    clocks: Map<String, ULong>,
) {
    public constructor(
        root: Path,
        urls: Map<CottFixtureKey, String>,
    ) : this(root, urls, emptyMap())

    internal val root: Path = root.toAbsolutePath().normalize()
    internal val urls: FrozenMap<CottFixtureKey, String> = FrozenMap(urls)
    internal val clocks: FrozenMap<String, ULong> = FrozenMap(clocks)
}

private class FixtureElement(
    val fixtures: CottFixtureContext,
) : AbstractCoroutineContextElement(Key) {
    companion object Key : CoroutineContext.Key<FixtureElement>
}

private val threadFixtures = ThreadLocal<CottFixtureContext?>()

private class ObservationElement(
    val observation: CottObservation,
) : AbstractCoroutineContextElement(Key) {
    companion object Key : CoroutineContext.Key<ObservationElement>
}

private val threadObservation = ThreadLocal<CottObservation?>()

private suspend fun <T> runWithCoroutineContext(
    context: CoroutineContext,
    block: suspend () -> T,
): T = withContext(context) { block() }

public sealed interface CottResult<out T, out E>
public data class Ok<out T>(public val value: T) : CottResult<T, kotlin.Nothing> {
    override fun equals(other: Any?): Boolean =
        other is Ok<*> && CottRuntime.deepEqual(value, other.value)
    override fun hashCode(): Int = CottRuntime.deepHash(value)
}
public data class Err<out E>(public val error: E) : CottResult<kotlin.Nothing, E> {
    override fun equals(other: Any?): Boolean =
        other is Err<*> && CottRuntime.deepEqual(error, other.error)
    override fun hashCode(): Int = CottRuntime.deepHash(error)
}

public sealed interface CottOption<out T>
public data class Some<out T>(public val value: T) : CottOption<T> {
    override fun equals(other: Any?): Boolean =
        other is Some<*> && CottRuntime.deepEqual(value, other.value)
    override fun hashCode(): Int = CottRuntime.deepHash(value)
}
public object Nothing : CottOption<kotlin.Nothing> {
    override fun toString(): String = "Nothing"
}

public object CottUnit {
    override fun toString(): String = "UNIT"
}

public class CottKeywordArguments<out T>(values: Map<String, T>) : AbstractMap<String, T>() {
    private val backingValues: Map<String, T> =
        Collections.unmodifiableMap(LinkedHashMap<String, T>(values))
    init {
        backingValues.keys.forEach { CottRuntime.validateUnicode(it, "$.key") }
    }
    override val entries: Set<Map.Entry<String, T>> get() = backingValues.entries
    override fun get(key: String): T? = backingValues[key]
    override fun containsKey(key: String): Boolean = backingValues.containsKey(key)
    override fun equals(other: Any?): Boolean =
        other is CottKeywordArguments<*> && CottRuntime.deepEqual(this, other)
    override fun hashCode(): Int = CottRuntime.deepHash(this)
    override fun toString(): String = "CottKeywordArguments(values=$backingValues)"
}

public class CottBytes(bytes: ByteArray) : AbstractList<Byte>() {
    private val data: ByteArray = bytes.copyOf()
    override val size: Int get() = data.size
    override fun get(index: Int): Byte = data[index]
    public fun toByteArray(): ByteArray = data.copyOf()
    override fun equals(other: Any?): Boolean = other is CottBytes && data.contentEquals(other.data)
    override fun hashCode(): Int = data.contentHashCode()
    override fun toString(): String = data.joinToString(prefix = "CottBytes(", postfix = ")") {
        (it.toInt() and 0xff).toString(16).padStart(2, '0')
    }
}

public class CottBuffer<N : CottConst>(
    bytes: ByteArray,
    public val dimension: N,
) : AbstractList<Byte>() {
    private val data: ByteArray = bytes.copyOf()
    init {
        val expected = CottRuntime.constLength(dimension, "$.dimension")
        if (data.size != expected) CottRuntime.violation(
            "buffer length does not match its const marker",
            phase = "validation",
            expected = expected.toString(),
            actual = data.size.toString(),
        )
    }
    override val size: Int get() = data.size
    override fun get(index: Int): Byte = data[index]
    public fun toByteArray(): ByteArray = data.copyOf()
    internal fun contentEquals(other: CottBuffer<*>): Boolean =
        data.contentEquals(other.data)
    internal fun contentHashCode(): Int = data.contentHashCode()
    override fun equals(other: Any?): Boolean =
        other is CottBuffer<*> &&
            CottRuntime.sameConst(dimension, other.dimension) &&
            data.contentEquals(other.data)
    override fun hashCode(): Int =
        31 * CottRuntime.constHash(dimension) + data.contentHashCode()
    override fun toString(): String = "CottBuffer(size=$size, dimension=${dimension.value})"
}

public class CottList<out T>(values: Iterable<T>) : AbstractList<T>() {
    private val values: List<T> = Collections.unmodifiableList(ArrayList<T>().also { copy ->
        values.forEach { copy.add(it) }
    })
    override val size: Int get() = values.size
    override fun get(index: Int): T = values[index]
    override fun equals(other: Any?): Boolean =
        other is CottList<*> && CottRuntime.deepEqual(this, other)
    override fun hashCode(): Int = CottRuntime.deepHash(this)
    override fun toString(): String = "CottList(values=$values)"
}

public class CottSet<out T>(values: Iterable<T>) : AbstractSet<T>() {
    private val values: CottList<T> = CottList(ArrayList<T>().also { copy ->
        values.forEach { candidate ->
            if (copy.none { CottRuntime.canonicalEqual(it, candidate) }) copy.add(candidate)
        }
    })
    override val size: Int get() = values.size
    override fun iterator(): Iterator<T> = values.iterator()
    override fun contains(element: @UnsafeVariance T): Boolean =
        values.any { CottRuntime.canonicalEqual(it, element) }
    override fun equals(other: Any?): Boolean =
        other is CottSet<*> && CottRuntime.deepEqual(this, other)
    override fun hashCode(): Int = CottRuntime.deepHash(this)
    override fun toString(): String = "CottSet(values=$values)"
}

private class CottMapEntry<out K, out V>(
    override val key: K,
    override val value: V,
) : Map.Entry<K, V> {
    override fun equals(other: Any?): Boolean =
        other is Map.Entry<*, *> &&
            CottRuntime.canonicalEqual(key, other.key) &&
            CottRuntime.canonicalEqual(value, other.value)
    override fun hashCode(): Int =
        CottRuntime.deepHash(key) xor CottRuntime.deepHash(value)
}

public class FrozenMap<K, out V>(values: Map<out K, V>) : AbstractMap<K, V>() {
    private val ordered: CottList<Map.Entry<K, V>> = CottList(
        ArrayList<Map.Entry<K, V>>().also { copy ->
            values.forEach { (key, value) ->
                val prior = copy.indexOfFirst { CottRuntime.canonicalEqual(it.key, key) }
                if (prior >= 0) copy.removeAt(prior)
                copy.add(CottMapEntry(key, value))
            }
        },
    )
    override val entries: Set<Map.Entry<K, V>> =
        Collections.unmodifiableSet(LinkedHashSet(ordered))
    override fun get(key: K): V? =
        ordered.firstOrNull { CottRuntime.canonicalEqual(it.key, key) }?.value
    override fun containsKey(key: K): Boolean =
        ordered.any { CottRuntime.canonicalEqual(it.key, key) }
    override fun equals(other: Any?): Boolean =
        other is FrozenMap<*, *> && CottRuntime.deepEqual(this, other)
    override fun hashCode(): Int = CottRuntime.deepHash(this)
    override fun toString(): String = "FrozenMap(values=${ordered.associate { it.key to it.value }})"
}

public class CottTuple(values: Iterable<Any?>) : AbstractList<Any?>(), CottTupleValue {
    override val cottTupleElements: CottList<Any?> = CottList(values)
    override val size: Int get() = cottTupleElements.size
    override fun get(index: Int): Any? = cottTupleElements[index]
    override fun cottRebuild(elements: CottList<Any?>): CottTupleValue =
        CottTuple(elements)
    override fun equals(other: Any?): Boolean =
        other is CottTuple && CottRuntime.deepEqual(this, other)
    override fun hashCode(): Int = CottRuntime.deepHash(this)
    override fun toString(): String = "CottTuple(values=$cottTupleElements)"
}

public class CottArray<out T, N : CottConst>(
    values: Iterable<T>,
    public val dimension: N,
) : AbstractList<T>() {
    private val elements = CottList(values)
    init {
        val expected = CottRuntime.constLength(dimension, "$.dimension")
        if (elements.size != expected) CottRuntime.violation(
            "array length does not match its const marker",
            phase = "validation",
            expected = expected.toString(),
            actual = elements.size.toString(),
        )
    }
    override val size: Int get() = elements.size
    override fun get(index: Int): T = elements[index]
    override fun equals(other: Any?): Boolean =
        other is CottArray<*, *> && CottRuntime.deepEqual(this, other)
    override fun hashCode(): Int = CottRuntime.deepHash(this)
    override fun toString(): String = "CottArray(values=$elements, dimension=${dimension.value})"
}

public class Opaque<Tag : CottOpaqueTag> private constructor(
    public val tag: Tag,
    private val payload: Any,
) {
    init {
        if (tag.tag.isEmpty()) CottRuntime.violation("opaque tag must be non-empty", phase = "validation")
    }

    public fun unwrap(): Any = payload

    override fun equals(other: Any?): Boolean =
        other is Opaque<*> && tag === other.tag && payload === other.payload

    override fun hashCode(): Int =
        31 * System.identityHashCode(tag) + System.identityHashCode(payload)
    override fun toString(): String = "Opaque(tag=${tag.tag}, value=$payload)"

    public companion object {
        public fun <Tag : CottOpaqueTag> of(tag: Tag, value: Any): Opaque<Tag> =
            Opaque(tag, value)
    }
}

public class CottTrait<T : Any> private constructor(
    public val id: String,
    private val predicate: (Any) -> Boolean,
) {
    init {
        if (id.isEmpty()) CottRuntime.violation("trait identity must be non-empty", phase = "validation")
    }

    internal fun accepts(value: Any): Boolean =
        predicate(value) &&
            value is CottTraitCarrier &&
            value.cottTraits.any { it === this }

    override fun equals(other: Any?): Boolean = this === other
    override fun hashCode(): Int = System.identityHashCode(this)
    override fun toString(): String = "CottTrait($id)"

    public companion object {
        public fun <T : Any> exact(id: String, type: Class<T>): CottTrait<T> =
            CottTrait(id) { value -> value.javaClass === type }

        public fun <T : Any> checked(id: String, accepts: (Any) -> Boolean): CottTrait<T> =
            CottTrait(id, accepts)
    }
}

public class Dyn<T : Any> private constructor(
    public val value: T,
    public val trait: CottTrait<T>,
) {
    init {
        if (!trait.accepts(value)) {
            CottRuntime.violation(
                "dynamic value does not carry the requested exact trait",
                phase = "validation",
                expected = trait.id,
                actual = value.javaClass.name,
            )
        }
    }

    override fun equals(other: Any?): Boolean = this === other
    override fun hashCode(): Int = System.identityHashCode(this)
    override fun toString(): String = "Dyn(trait=${trait.id}, value=$value)"

    public companion object {
        public fun <T : Any> of(value: T, trait: CottTrait<T>): Dyn<T> = Dyn(value, trait)
    }
}

public class CottFactory<T : Any> private constructor(
    public val type: Class<T>,
) {
    override fun equals(other: Any?): Boolean =
        other is CottFactory<*> && type === other.type
    override fun hashCode(): Int = System.identityHashCode(type)
    override fun toString(): String = "CottFactory(${type.name})"

    public companion object {
        public fun <T : Any> of(type: Class<T>): CottFactory<T> = CottFactory(type)
    }
}

public sealed interface JsonValue
public object JsonNull : JsonValue {
    override fun toString(): String = "JsonNull"
}
public data class JsonBoolean(public val value: Boolean) : JsonValue
public data class JsonInteger(public val value: BigInteger) : JsonValue {
    init { CottRuntime.checkInt(value, signed = true, bits = 64, path = "$.value") }
}
public data class JsonFloat(public val value: Double) : JsonValue {
    init { CottRuntime.validateF64(value, "$.value") }
    override fun equals(other: Any?): Boolean = other is JsonFloat && value == other.value
    override fun hashCode(): Int = if (value == 0.0) 0.0.hashCode() else value.hashCode()
}
public data class JsonString(public val value: String) : JsonValue {
    init { CottRuntime.validateUnicode(value, "$.value") }
}
public data class JsonArray(public val value: CottList<JsonValue>) : JsonValue {
    public constructor(values: Iterable<JsonValue>) : this(CottList(values))
    init { CottRuntime.abi(this, CottTypes.JSON, RuntimeValidation.BOUNDARY) }
}
public data class JsonObject(public val value: FrozenMap<String, JsonValue>) : JsonValue {
    public constructor(values: Map<String, JsonValue>) : this(FrozenMap(values))
    init { CottRuntime.abi(this, CottTypes.JSON, RuntimeValidation.BOUNDARY) }
}

private class VisitKey(val value: Any?, val type: CottType<*>) {
    override fun equals(other: Any?): Boolean =
        other is VisitKey && value === other.value && type === other.type
    override fun hashCode(): Int = 31 * System.identityHashCode(value) + System.identityHashCode(type)
}

internal class Traversal(private val normalizeOnly: Boolean) {
    private val active = HashSet<VisitKey>()
    private val completed = HashMap<VisitKey, Any?>()
    private var nodes = 0

    fun <T> transform(value: Any?, type: CottType<T>, path: String, depth: Int): T {
        if (depth > 64) throw CottTraversalViolation("$path exceeds ABI traversal depth 64")
        nodes += 1
        if (nodes > 1024) throw CottTraversalViolation("$path exceeds ABI traversal node limit 1024")
        val key = VisitKey(value, type)
        if (completed.containsKey(key)) return completed[key] as T
        if (!active.add(key)) throw CottTraversalViolation("$path contains an active value cycle")
        return try {
            val result = if (normalizeOnly) {
                type.normalizeDirect(value, path, this, depth)
            } else {
                type.validateDirect(value, path, this, depth)
            }
            active.remove(key)
            completed[key] = result
            result as T
        } catch (error: Throwable) {
            active.remove(key)
            throw error
        }
    }
}

internal class Adaptation {
    private val active = HashSet<VisitKey>()
    private val completed = HashMap<VisitKey, Any?>()
    private var nodes = 0

    fun <T> transform(
        value: Any?,
        type: CottType<T>,
        mode: RuntimeValidation,
        path: String,
        depth: Int,
    ): T {
        if (depth > 64) throw CottTraversalViolation("$path exceeds ABI traversal depth 64")
        nodes += 1
        if (nodes > 1024) throw CottTraversalViolation("$path exceeds ABI traversal node limit 1024")
        val key = VisitKey(value, type.adaptationType())
        if (completed.containsKey(key)) return completed[key] as T
        if (!active.add(key)) throw CottTraversalViolation("$path contains an active value cycle")
        return try {
            val result = type.adaptDirect(value, mode, path, this, depth)
            active.remove(key)
            completed[key] = result
            result as T
        } catch (error: Throwable) {
            active.remove(key)
            throw error
        }
    }

    suspend fun <T> transformSuspend(
        value: Any?,
        type: CottType<T>,
        mode: RuntimeValidation,
        path: String,
        depth: Int,
    ): T {
        if (depth > 64) throw CottTraversalViolation("$path exceeds ABI traversal depth 64")
        nodes += 1
        if (nodes > 1024) throw CottTraversalViolation("$path exceeds ABI traversal node limit 1024")
        val key = VisitKey(value, type.adaptationType())
        if (completed.containsKey(key)) return completed[key] as T
        if (!active.add(key)) throw CottTraversalViolation("$path contains an active value cycle")
        return try {
            val result = type.adaptSuspendDirect(value, mode, path, this, depth)
            active.remove(key)
            completed[key] = result
            result as T
        } catch (error: Throwable) {
            active.remove(key)
            throw error
        }
    }
}


private class DeepSnapshotter {
    private val active = IdentityHashMap<Any, Boolean>()
    private var nodes = 0

    fun snapshot(value: Any?, path: String = "$", depth: Int = 0): Any? {
        if (depth > 64) throw CottTraversalViolation("$path exceeds snapshot depth 64")
        nodes += 1
        if (nodes > 1024) throw CottTraversalViolation("$path exceeds snapshot node limit 1024")
        if (value == null || value is String || value is Number || value is Boolean ||
            value is Char || value is CottConst || value is CottOpaqueTag ||
            value === CottUnit || value === Nothing || value === JsonNull ||
            value is Opaque<*> || value is Dyn<*> || value is Path
        ) {
            return value
        }
        if (active.put(value, true) != null) {
            throw CottTraversalViolation("$path contains an active value cycle")
        }
        return try {
            when (value) {
                is CottBytes -> CottBytes(value.toByteArray())
                is CottBuffer<*> ->
                    CottBuffer<CottConst>(value.toByteArray(), value.dimension)
                is ByteArray -> value.copyOf()
                is ShortArray -> value.copyOf()
                is IntArray -> value.copyOf()
                is LongArray -> value.copyOf()
                is FloatArray -> value.copyOf()
                is DoubleArray -> value.copyOf()
                is BooleanArray -> value.copyOf()
                is CharArray -> value.copyOf()
                is CottList<*> -> CottList(value.mapIndexed { index, item ->
                    snapshot(item, "$path[$index]", depth + 1)
                })
                is CottSet<*> -> CottSet(value.mapIndexed { index, item ->
                    snapshot(item, "$path[$index]", depth + 1)
                })
                is FrozenMap<*, *> -> {
                    val result = LinkedHashMap<Any?, Any?>()
                    value.entries.forEach { entry ->
                        result[snapshot(entry.key, "$path.key", depth + 1)] =
                            snapshot(entry.value, "$path[${entry.key}]", depth + 1)
                    }
                    FrozenMap(result)
                }
                is CottKeywordArguments<*> -> CottKeywordArguments(value.mapValues { entry ->
                    snapshot(entry.value, "$path[${entry.key}]", depth + 1)
                })
                is CottTuple -> CottTuple(value.mapIndexed { index, item ->
                    snapshot(item, "$path[$index]", depth + 1)
                })
                is CottArray<*, *> -> CottArray<Any?, CottConst>(
                    value.mapIndexed { index, item -> snapshot(item, "$path[$index]", depth + 1) },
                    value.dimension,
                )
                is Some<*> -> Some(snapshot(value.value, "$path.value", depth + 1))
                is Ok<*> -> Ok(snapshot(value.value, "$path.value", depth + 1))
                is Err<*> -> Err(snapshot(value.error, "$path.error", depth + 1))
                is JsonBoolean, is JsonInteger, is JsonFloat, is JsonString -> value
                is JsonArray -> JsonArray(value.value.mapIndexed { index, item ->
                    snapshot(item, "$path.value[$index]", depth + 1) as JsonValue
                })
                is JsonObject -> JsonObject(value.value.mapValues { entry ->
                    snapshot(entry.value, "$path.value[${entry.key}]", depth + 1) as JsonValue
                })
                is List<*> -> value.mapIndexed { index, item ->
                    snapshot(item, "$path[$index]", depth + 1)
                }
                is Set<*> -> LinkedHashSet<Any?>().also { result ->
                    value.forEachIndexed { index, item ->
                        result.add(snapshot(item, "$path[$index]", depth + 1))
                    }
                }
                is Map<*, *> -> LinkedHashMap<Any?, Any?>().also { result ->
                    value.entries.forEach { entry ->
                        result[snapshot(entry.key, "$path.key", depth + 1)] =
                            snapshot(entry.value, "$path[${entry.key}]", depth + 1)
                    }
                }
                else -> value
            }
        } finally {
            active.remove(value)
        }
    }
}

private class DeepPair(val left: Any, val right: Any) {
    override fun equals(other: Any?): Boolean =
        other is DeepPair && left === other.left && right === other.right
    override fun hashCode(): Int =
        31 * System.identityHashCode(left) + System.identityHashCode(right)
}

private class DeepComparator {
    private val active = HashSet<DeepPair>()
    private var nodes = 0

    fun equal(left: Any?, right: Any?, path: String = "$", depth: Int = 0): Boolean {
        if (left === right) return true
        if (left == null || right == null || left.javaClass !== right.javaClass) return false
        if (depth > 64) throw CottTraversalViolation("$path exceeds equality depth 64")
        nodes += 1
        if (nodes > 1024) throw CottTraversalViolation("$path exceeds equality node limit 1024")
        val pair = DeepPair(left, right)
        if (!active.add(pair)) throw CottTraversalViolation("$path contains an active value cycle")
        return try {
            when {
                left is Float && right is Float -> left == right
                left is Double && right is Double -> left == right
                left is ByteArray && right is ByteArray -> left.contentEquals(right)
                left is ShortArray && right is ShortArray -> left.contentEquals(right)
                left is IntArray && right is IntArray -> left.contentEquals(right)
                left is LongArray && right is LongArray -> left.contentEquals(right)
                left is FloatArray && right is FloatArray ->
                    left.size == right.size &&
                        left.indices.all { index -> left[index] == right[index] }
                left is DoubleArray && right is DoubleArray ->
                    left.size == right.size &&
                        left.indices.all { index -> left[index] == right[index] }
                left is BooleanArray && right is BooleanArray -> left.contentEquals(right)
                left is CharArray && right is CharArray -> left.contentEquals(right)
                left is CottBuffer<*> && right is CottBuffer<*> ->
                    CottRuntime.sameConst(left.dimension, right.dimension) &&
                        left.contentEquals(right)
                left is CottArray<*, *> && right is CottArray<*, *> ->
                    CottRuntime.sameConst(left.dimension, right.dimension) &&
                        sequenceEqual(left, right, path, depth)
                left is CottTupleValue && right is CottTupleValue ->
                    sequenceEqual(left.cottTupleElements, right.cottTupleElements, path, depth)
                left is CottFieldValue && right is CottFieldValue -> {
                    left.cottTypeIdentity == right.cottTypeIdentity &&
                        left.cottFieldNames == right.cottFieldNames &&
                        left.cottFieldNames.all { name ->
                            equal(left.cottField(name), right.cottField(name), "$path.$name", depth + 1)
                        }
                }
                left is Some<*> && right is Some<*> ->
                    equal(left.value, right.value, "$path.value", depth + 1)
                left is Ok<*> && right is Ok<*> ->
                    equal(left.value, right.value, "$path.value", depth + 1)
                left is Err<*> && right is Err<*> ->
                    equal(left.error, right.error, "$path.error", depth + 1)
                left is JsonFloat && right is JsonFloat -> left.value == right.value
                left is JsonArray && right is JsonArray ->
                    sequenceEqual(left.value, right.value, "$path.value", depth)
                left is JsonObject && right is JsonObject ->
                    mapEqual(left.value, right.value, "$path.value", depth)
                left is List<*> && right is List<*> ->
                    sequenceEqual(left, right, path, depth)
                left is Set<*> && right is Set<*> -> {
                    if (left.size != right.size) false
                    else left.all { candidate ->
                        right.any { other -> equal(candidate, other, "$path.element", depth + 1) }
                    }
                }
                left is Map<*, *> && right is Map<*, *> -> mapEqual(left, right, path, depth)
                else -> left == right
            }
        } finally {
            active.remove(pair)
        }
    }

    private fun mapEqual(
        left: Map<*, *>,
        right: Map<*, *>,
        path: String,
        depth: Int,
    ): Boolean = left.size == right.size && left.entries.all { entry ->
        right.entries.any { other ->
            equal(entry.key, other.key, "$path.key", depth + 1) &&
                equal(entry.value, other.value, "$path[${entry.key}]", depth + 1)
        }
    }

    private fun sequenceEqual(
        left: List<*>,
        right: List<*>,
        path: String,
        depth: Int,
    ): Boolean = left.size == right.size && left.indices.all { index ->
        equal(left[index], right[index], "$path[$index]", depth + 1)
    }
}

private class DeepHasher {
    private val active = IdentityHashMap<Any, Boolean>()
    private var nodes = 0

    fun hash(value: Any?, path: String = "$", depth: Int = 0): Int {
        if (value == null) return 0
        if (depth > 64) throw CottTraversalViolation("$path exceeds hash depth 64")
        nodes += 1
        if (nodes > 1024) throw CottTraversalViolation("$path exceeds hash node limit 1024")
        if (value is Float) return if (value == 0.0f) 0.0f.hashCode() else value.hashCode()
        if (value is Double) return if (value == 0.0) 0.0.hashCode() else value.hashCode()
        if (value is CottConst) return CottRuntime.constHash(value)
        if (value is String || value is Number || value is Boolean || value is Char ||
            value is BigInteger || value is CottOpaqueTag ||
            value === CottUnit || value === Nothing || value === JsonNull ||
            value is Opaque<*> || value is Dyn<*> || value is Path
        ) {
            return value.hashCode()
        }
        if (active.put(value, true) != null) {
            throw CottTraversalViolation("$path contains an active value cycle")
        }
        return try {
            when (value) {
                is ByteArray -> value.contentHashCode()
                is ShortArray -> value.contentHashCode()
                is IntArray -> value.contentHashCode()
                is LongArray -> value.contentHashCode()
                is FloatArray -> orderedHash(value.map { if (it == 0.0f) 0.0f else it }, path, depth)
                is DoubleArray -> orderedHash(value.map { if (it == 0.0) 0.0 else it }, path, depth)
                is BooleanArray -> value.contentHashCode()
                is CharArray -> value.contentHashCode()
                is CottBuffer<*> ->
                    31 * CottRuntime.constHash(value.dimension) + value.contentHashCode()
                is CottArray<*, *> ->
                    31 * CottRuntime.constHash(value.dimension) + orderedHash(value, path, depth)
                is CottTupleValue -> orderedHash(value.cottTupleElements, path, depth)
                is CottFieldValue -> {
                    var result = value.cottTypeIdentity.hashCode()
                    value.cottFieldNames.forEach { name ->
                        result = 31 * result + name.hashCode()
                        result = 31 * result + hash(value.cottField(name), "$path.$name", depth + 1)
                    }
                    result
                }
                is Some<*> -> hash(value.value, "$path.value", depth + 1)
                is Ok<*> -> hash(value.value, "$path.value", depth + 1)
                is Err<*> -> hash(value.error, "$path.error", depth + 1)
                is JsonFloat -> if (value.value == 0.0) 0.0.hashCode() else value.value.hashCode()
                is JsonArray -> orderedHash(value.value, "$path.value", depth)
                is JsonObject -> mapHash(value.value, "$path.value", depth)
                is List<*> -> orderedHash(value, path, depth)
                is Set<*> -> value.sumOf { hash(it, "$path.element", depth + 1) }
                is Map<*, *> -> mapHash(value, path, depth)
                else -> value.hashCode()
            }
        } finally {
            active.remove(value)
        }
    }

    private fun orderedHash(values: Iterable<*>, path: String, depth: Int): Int {
        var result = 1
        var index = 0
        for (value in values) {
            result = 31 * result + hash(value, "$path[$index]", depth + 1)
            index += 1
        }
        return result
    }

    private fun mapHash(values: Map<*, *>, path: String, depth: Int): Int =
        values.entries.sumOf { entry ->
            hash(entry.key, "$path.key", depth + 1) xor
                hash(entry.value, "$path[${entry.key}]", depth + 1)
        }
}
public abstract class CottType<T> internal constructor(public val displayName: String) {
    internal abstract fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any?
    internal open fun normalizeDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? = value
    internal open fun adaptationType(): CottType<*> = this
    internal open fun adaptDirect(
        value: Any?,
        mode: RuntimeValidation,
        path: String,
        state: Adaptation,
        depth: Int,
    ): Any? = value
    internal open suspend fun adaptSuspendDirect(
        value: Any?,
        mode: RuntimeValidation,
        path: String,
        state: Adaptation,
        depth: Int,
    ): Any? = adaptDirect(value, mode, path, state, depth)
    internal fun adapt(value: Any?, mode: RuntimeValidation, path: String): T =
        Adaptation().transform(value, this, mode, path, 0)
    internal suspend fun adaptSuspend(value: Any?, mode: RuntimeValidation, path: String): T =
        Adaptation().transformSuspend(value, this, mode, path, 0)
    override fun toString(): String = displayName
}

public class CottNominalField<T : Any> public constructor(
    public val name: String,
    public val type: CottType<*>,
    public val read: (T) -> Any?,
)

public object CottTypes {
    private fun mismatch(path: String, expected: String, value: Any?): kotlin.Nothing = CottRuntime.violation(
        "$path does not match ABI type",
        phase = "validation",
        expected = expected,
        actual = value?.javaClass?.name ?: "null",
    )

    private fun <T> scalar(
        name: String,
        validate: (Any?, String) -> T,
        normalize: ((Any?, String) -> Any?)? = null,
    ): CottType<T> = object : CottType<T>(name) {
        override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
            validate(value, path)
        override fun normalizeDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
            normalize?.invoke(value, path) ?: value
    }

    @JvmField public val ANY: CottType<Any?> = object : CottType<Any?>("Any") {
        override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? = value
    }
    @JvmField public val NEVER: CottType<kotlin.Nothing> = object : CottType<kotlin.Nothing>("Never") {
        override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
            mismatch(path, "Never", value)
    }
    @JvmField public val BOOL: CottType<Boolean> = scalar("Bool", { value, path ->
        value as? Boolean ?: mismatch(path, "Bool", value)
    })
    @JvmField public val I8: CottType<Byte> = scalar("I8", { value, path ->
        value as? Byte ?: mismatch(path, "I8", value)
    })
    @JvmField public val I16: CottType<Short> = scalar("I16", { value, path ->
        value as? Short ?: mismatch(path, "I16", value)
    })
    @JvmField public val I32: CottType<Int> = scalar("I32", { value, path ->
        value as? Int ?: mismatch(path, "I32", value)
    })
    @JvmField public val I64: CottType<Long> = scalar("I64", { value, path ->
        value as? Long ?: mismatch(path, "I64", value)
    })
    @JvmField public val U8: CottType<UByte> = scalar("U8", { value, path ->
        value as? UByte ?: mismatch(path, "U8", value)
    })
    @JvmField public val U16: CottType<UShort> = scalar("U16", { value, path ->
        value as? UShort ?: mismatch(path, "U16", value)
    })
    @JvmField public val U32: CottType<UInt> = scalar("U32", { value, path ->
        value as? UInt ?: mismatch(path, "U32", value)
    })
    @JvmField public val U64: CottType<ULong> = scalar("U64", { value, path ->
        value as? ULong ?: mismatch(path, "U64", value)
    })
    @JvmField public val F32: CottType<Float> = scalar("F32", { value, path ->
        value as? Float ?: mismatch(path, "F32", value)
        CottRuntime.validateF32(value, path)
    }, { value, path -> if (value is Float) CottRuntime.validateF32(value, path) else value })
    @JvmField public val F64: CottType<Double> = scalar("F64", { value, path ->
        value as? Double ?: mismatch(path, "F64", value)
        CottRuntime.validateF64(value, path)
    })
    @JvmField public val STRING: CottType<String> = scalar("String", { value, path ->
        value as? String ?: mismatch(path, "String", value)
        CottRuntime.validateUnicode(value, path)
    })
    @JvmField public val BYTES: CottType<CottBytes> = scalar("Bytes", { value, path ->
        value as? CottBytes ?: mismatch(path, "CottBytes", value)
    })
    @JvmField public val PATH: CottType<Path> = scalar("Path", { value, path ->
        value as? Path ?: mismatch(path, "java.nio.file.Path", value)
    })
    @JvmField public val UNIT: CottType<CottUnit> = scalar("Unit", { value, path ->
        if (value !== CottUnit) mismatch(path, "CottUnit", value)
        CottUnit
    })
    @JvmField public val JSON: CottType<JsonValue> = deferred("JsonValue") { jsonType() }

    public fun integer(kind: CottIntKind): CottType<*> = when (kind) {
        CottIntKind.I8 -> I8
        CottIntKind.I16 -> I16
        CottIntKind.I32 -> I32
        CottIntKind.I64 -> I64
        CottIntKind.U8 -> U8
        CottIntKind.U16 -> U16
        CottIntKind.U32 -> U32
        CottIntKind.U64 -> U64
    }


    public fun <T> deferred(name: String, provider: () -> CottType<T>): CottType<T> =
        object : CottType<T>(name) {
            private val resolved: CottType<T> by lazy(provider)
            override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
                state.transform(value, resolved, path, depth + 1)
            override fun normalizeDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
                state.transform(value, resolved, path, depth + 1)
            override fun adaptationType(): CottType<*> = resolved.adaptationType()
            override fun adaptDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? = resolved.adaptDirect(value, mode, path, state, depth)
            override suspend fun adaptSuspendDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? = resolved.adaptSuspendDirect(value, mode, path, state, depth)
        }

    public fun <T> option(item: CottType<T>): CottType<CottOption<T>> =
        object : CottType<CottOption<T>>("Option<$item>") {
            override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? = when (value) {
                is Some<*> -> {
                    val normalized = state.transform(value.value, item, "$path.value", depth + 1)
                    if (normalized === value.value) value else Some(normalized)
                }
                Nothing -> Nothing
                else -> mismatch(path, displayName, value)
            }
            override fun normalizeDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
                if (value is Some<*>) {
                    val normalized = state.transform(value.value, item, "$path.value", depth + 1)
                    if (normalized === value.value) value else Some(normalized)
                } else value
            override fun adaptDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? {
                if (value !is Some<*>) return value
                val adapted = state.transform(value.value, item, mode, "$path.value", depth + 1)
                return if (adapted === value.value) value else Some(adapted)
            }
            override suspend fun adaptSuspendDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? {
                if (value !is Some<*>) return value
                val adapted = state.transformSuspend(value.value, item, mode, "$path.value", depth + 1)
                return if (adapted === value.value) value else Some(adapted)
            }
        }

    public fun <T, E> result(ok: CottType<T>, err: CottType<E>): CottType<CottResult<T, E>> =
        object : CottType<CottResult<T, E>>("Result<$ok, $err>") {
            override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? = when (value) {
                is Ok<*> -> {
                    val normalized = state.transform(value.value, ok, "$path.value", depth + 1)
                    if (normalized === value.value) value else Ok(normalized)
                }
                is Err<*> -> {
                    val normalized = state.transform(value.error, err, "$path.error", depth + 1)
                    if (normalized === value.error) value else Err(normalized)
                }
                else -> mismatch(path, displayName, value)
            }
            override fun normalizeDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? = when (value) {
                is Ok<*> -> {
                    val normalized = state.transform(value.value, ok, "$path.value", depth + 1)
                    if (normalized === value.value) value else Ok(normalized)
                }
                is Err<*> -> {
                    val normalized = state.transform(value.error, err, "$path.error", depth + 1)
                    if (normalized === value.error) value else Err(normalized)
                }
                else -> value
            }
            override fun adaptDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? = when (value) {
                is Ok<*> -> {
                    val adapted = state.transform(value.value, ok, mode, "$path.value", depth + 1)
                    if (adapted === value.value) value else Ok(adapted)
                }
                is Err<*> -> {
                    val adapted = state.transform(value.error, err, mode, "$path.error", depth + 1)
                    if (adapted === value.error) value else Err(adapted)
                }
                else -> value
            }
            override suspend fun adaptSuspendDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? = when (value) {
                is Ok<*> -> {
                    val adapted = state.transformSuspend(value.value, ok, mode, "$path.value", depth + 1)
                    if (adapted === value.value) value else Ok(adapted)
                }
                is Err<*> -> {
                    val adapted = state.transformSuspend(value.error, err, mode, "$path.error", depth + 1)
                    if (adapted === value.error) value else Err(adapted)
                }
                else -> value
            }
        }

    public fun <T> list(item: CottType<T>): CottType<CottList<T>> =
        sequenceType("CottList<$item>", item, { it as? CottList<*> }, { CottList(it) })

    public fun <T> set(item: CottType<T>): CottType<CottSet<T>> =
        sequenceType("CottSet<$item>", item, { it as? CottSet<*> }, { CottSet(it) })

    private fun <T, C> sequenceType(
        name: String,
        item: CottType<T>,
        cast: (Any?) -> Iterable<*>?,
        build: (Iterable<T>) -> C,
    ): CottType<C> = object : CottType<C>(name) {
        private fun transform(value: Any?, path: String, state: Traversal, depth: Int, strict: Boolean): Any? {
            val sequence = cast(value) ?: return if (strict) mismatch(path, displayName, value) else value
            val transformed = ArrayList<T>()
            var changed = false
            sequence.forEachIndexed { index, raw ->
                val next = state.transform(raw, item, "$path[$index]", depth + 1)
                transformed.add(next)
                changed = changed || next !== raw
            }
            return if (!changed) value else build(transformed)
        }
        override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
            transform(value, path, state, depth, true)
        override fun normalizeDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
            transform(value, path, state, depth, false)
        override fun adaptDirect(
            value: Any?,
            mode: RuntimeValidation,
            path: String,
            state: Adaptation,
            depth: Int,
        ): Any? {
            val sequence = cast(value) ?: return value
            val result = ArrayList<T>()
            var changed = false
            sequence.forEachIndexed { index, raw ->
                val adapted = state.transform(raw, item, mode, "$path[$index]", depth + 1)
                result.add(adapted)
                changed = changed || adapted !== raw
            }
            return if (changed) build(result) else value
        }
        override suspend fun adaptSuspendDirect(
            value: Any?,
            mode: RuntimeValidation,
            path: String,
            state: Adaptation,
            depth: Int,
        ): Any? {
            val sequence = cast(value) ?: return value
            val result = ArrayList<T>()
            var changed = false
            sequence.forEachIndexed { index, raw ->
                val adapted = state.transformSuspend(raw, item, mode, "$path[$index]", depth + 1)
                result.add(adapted)
                changed = changed || adapted !== raw
            }
            return if (changed) build(result) else value
        }
    }

    public fun <K, V> map(
        keyType: CottType<K>,
        valueType: CottType<V>,
    ): CottType<FrozenMap<K, V>> =
        object : CottType<FrozenMap<K, V>>("FrozenMap<$keyType, $valueType>") {
            private fun transform(raw: Any?, path: String, state: Traversal, depth: Int, strict: Boolean): Any? {
                val map = raw as? FrozenMap<*, *> ?: return if (strict) mismatch(path, displayName, raw) else raw
                val transformed = LinkedHashMap<Any?, Any?>()
                var changed = false
                map.entries.forEach { entry ->
                    val rawKey = entry.key
                    val rawValue = entry.value
                    val nextKey = state.transform(rawKey, keyType, "$path.key", depth + 1)
                    val nextValue = state.transform(rawValue, valueType, "$path[$rawKey]", depth + 1)
                    transformed[nextKey] = nextValue
                    changed = changed || nextKey !== rawKey || nextValue !== rawValue
                }
                return if (!changed) raw else FrozenMap(transformed)
            }
            override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
                transform(value, path, state, depth, true)
            override fun normalizeDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
                transform(value, path, state, depth, false)
            override fun adaptDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? {
                val map = value as? FrozenMap<*, *> ?: return value
                val result = LinkedHashMap<Any?, Any?>()
                var changed = false
                map.entries.forEach { entry ->
                    val rawKey = entry.key
                    val rawValue = entry.value
                    val nextKey = state.transform(rawKey, keyType, mode, "$path.key", depth + 1)
                    val nextValue = state.transform(
                        rawValue, valueType, mode, "$path[$rawKey]", depth + 1,
                    )
                    result[nextKey] = nextValue
                    changed = changed || nextKey !== rawKey || nextValue !== rawValue
                }
                return if (changed) FrozenMap(result) else value
            }
            override suspend fun adaptSuspendDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? {
                val map = value as? FrozenMap<*, *> ?: return value
                val result = LinkedHashMap<Any?, Any?>()
                var changed = false
                for (entry in map.entries) {
                    val rawKey = entry.key
                    val rawValue = entry.value
                    val nextKey = state.transformSuspend(rawKey, keyType, mode, "$path.key", depth + 1)
                    val nextValue = state.transformSuspend(
                        rawValue, valueType, mode, "$path[$rawKey]", depth + 1,
                    )
                    result[nextKey] = nextValue
                    changed = changed || nextKey !== rawKey || nextValue !== rawValue
                }
                return if (changed) FrozenMap(result) else value
            }
        }

    public fun <T> keywordArguments(item: CottType<T>): CottType<CottKeywordArguments<T>> =
        object : CottType<CottKeywordArguments<T>>("KeywordArguments<$item>") {
            private fun transform(
                raw: Any?,
                path: String,
                state: Traversal,
                depth: Int,
                strict: Boolean,
            ): Any? {
                val arguments = raw as? CottKeywordArguments<*>
                    ?: return if (strict) mismatch(path, displayName, raw) else raw
                val transformed = LinkedHashMap<String, Any?>()
                var changed = false
                arguments.forEach { (key, value) ->
                    CottRuntime.validateUnicode(key, "$path.key")
                    val next = state.transform(value, item, "$path[$key]", depth + 1)
                    transformed[key] = next
                    changed = changed || next !== value
                }
                return if (changed) CottKeywordArguments(transformed) else raw
            }
            override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
                transform(value, path, state, depth, true)
            override fun normalizeDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
                transform(value, path, state, depth, false)
            override fun adaptDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? {
                val arguments = value as? CottKeywordArguments<*> ?: return value
                val result = LinkedHashMap<String, Any?>()
                var changed = false
                arguments.forEach { (key, raw) ->
                    val adapted = state.transform(raw, item, mode, "$path[$key]", depth + 1)
                    result[key] = adapted
                    changed = changed || adapted !== raw
                }
                return if (changed) CottKeywordArguments(result) else value
            }
            override suspend fun adaptSuspendDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? {
                val arguments = value as? CottKeywordArguments<*> ?: return value
                val result = LinkedHashMap<String, Any?>()
                var changed = false
                for ((key, raw) in arguments) {
                    val adapted = state.transformSuspend(raw, item, mode, "$path[$key]", depth + 1)
                    result[key] = adapted
                    changed = changed || adapted !== raw
                }
                return if (changed) CottKeywordArguments(result) else value
            }
        }

    public fun tuple(items: List<CottType<*>>): CottType<CottTupleValue> =
        object : CottType<CottTupleValue>("Tuple<${items.joinToString()}>") {
            private fun transform(value: Any?, path: String, state: Traversal, depth: Int, strict: Boolean): Any? {
                val tuple = value as? CottTupleValue
                    ?: return if (strict) mismatch(path, displayName, value) else value
                val elements = tuple.cottTupleElements
                if (strict && elements.size != items.size) mismatch(path, displayName, value)
                if (elements.size != items.size) return value
                elements.indices.forEach { index ->
                    state.transform(elements[index], items[index], "$path[$index]", depth + 1)
                }
                return value
            }
            override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
                transform(value, path, state, depth, true)
            override fun normalizeDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
                transform(value, path, state, depth, false)
            override fun adaptDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? {
                val tuple = value as? CottTupleValue ?: return value
                val result = ArrayList<Any?>(tuple.cottTupleElements.size)
                var changed = false
                tuple.cottTupleElements.forEachIndexed { index, raw ->
                    val adapted = state.transform(raw, items[index], mode, "$path[$index]", depth + 1)
                    result.add(adapted)
                    changed = changed || adapted !== raw
                }
                return if (changed) tuple.cottRebuild(CottList(result)) else value
            }
            override suspend fun adaptSuspendDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? {
                val tuple = value as? CottTupleValue ?: return value
                val result = ArrayList<Any?>(tuple.cottTupleElements.size)
                var changed = false
                tuple.cottTupleElements.forEachIndexed { index, raw ->
                    val adapted = state.transformSuspend(
                        raw, items[index], mode, "$path[$index]", depth + 1,
                    )
                    result.add(adapted)
                    changed = changed || adapted !== raw
                }
                return if (changed) tuple.cottRebuild(CottList(result)) else value
            }
        }

    public fun <T, N : CottConst> array(
        item: CottType<T>,
        length: Int,
        marker: N? = null,
    ): CottType<CottArray<T, N>> = arrayDescriptor(item, length, marker)

    public fun <T, N : CottConst> arrayParameterized(
        item: CottType<T>,
        witness: N,
        kind: CottIntKind,
    ): CottType<CottArray<T, N>> {
        CottRuntime.validateConst(witness, kind)
        return arrayDescriptor(item, CottRuntime.constLength(witness), witness)
    }

    private fun <T, N : CottConst> arrayDescriptor(
        item: CottType<T>,
        expectedLength: Int?,
        expectedMarker: N?,
    ): CottType<CottArray<T, N>> {
        if (expectedLength != null && expectedLength < 0) {
            CottRuntime.violation("array length must be non-negative", phase = "validation")
        }
        return object : CottType<CottArray<T, N>>("Array<$item, ${expectedLength ?: "parameter"}>") {
            private fun transform(
                value: Any?,
                path: String,
                state: Traversal,
                depth: Int,
                strict: Boolean,
            ): Any? {
                val array = value as? CottArray<*, *>
                    ?: return if (strict) mismatch(path, displayName, value) else value
                val actualLength = CottRuntime.constLength(array.dimension, "$path.dimension")
                if (array.size != actualLength || (expectedLength != null && actualLength != expectedLength)) {
                    CottRuntime.violation(
                        "$path has the wrong array length",
                        phase = "validation",
                        expected = (expectedLength ?: actualLength).toString(),
                        actual = array.size.toString(),
                    )
                }
                if (expectedMarker != null && !CottRuntime.sameConst(array.dimension, expectedMarker)) {
                    mismatch("$path.dimension", expectedMarker.javaClass.name, array.dimension)
                }
                val result = ArrayList<Any?>()
                var changed = false
                array.forEachIndexed { index, raw ->
                    val next = state.transform(raw, item, "$path[$index]", depth + 1)
                    result.add(next)
                    changed = changed || next !== raw
                }
                return if (!changed) value else CottArray<Any?, CottConst>(result, array.dimension)
            }
            override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
                transform(value, path, state, depth, true)
            override fun normalizeDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
                transform(value, path, state, depth, false)
            override fun adaptDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? {
                val array = value as? CottArray<*, *> ?: return value
                val result = ArrayList<Any?>()
                var changed = false
                array.forEachIndexed { index, raw ->
                    val adapted = state.transform(raw, item, mode, "$path[$index]", depth + 1)
                    result.add(adapted)
                    changed = changed || adapted !== raw
                }
                return if (changed) CottArray<Any?, CottConst>(result, array.dimension) else value
            }
            override suspend fun adaptSuspendDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? {
                val array = value as? CottArray<*, *> ?: return value
                val result = ArrayList<Any?>()
                var changed = false
                array.forEachIndexed { index, raw ->
                    val adapted = state.transformSuspend(raw, item, mode, "$path[$index]", depth + 1)
                    result.add(adapted)
                    changed = changed || adapted !== raw
                }
                return if (changed) CottArray<Any?, CottConst>(result, array.dimension) else value
            }
        }
    }

    public fun <N : CottConst> buffer(
        length: Int,
        marker: N? = null,
    ): CottType<CottBuffer<N>> = bufferDescriptor(length, marker)

    public fun <N : CottConst> bufferParameterized(
        witness: N,
        kind: CottIntKind,
    ): CottType<CottBuffer<N>> {
        CottRuntime.validateConst(witness, kind)
        return bufferDescriptor(CottRuntime.constLength(witness), witness)
    }

    private fun <N : CottConst> bufferDescriptor(
        expectedLength: Int?,
        expectedMarker: N?,
    ): CottType<CottBuffer<N>> = scalar(
        "Buffer<${expectedLength ?: "parameter"}>",
        { value, path ->
            val buffer = value as? CottBuffer<*> ?: mismatch(path, "CottBuffer", value)
            val actualLength = CottRuntime.constLength(buffer.dimension, "$path.dimension")
            if (buffer.size != actualLength || (expectedLength != null && actualLength != expectedLength)) {
                CottRuntime.violation(
                    "$path has the wrong buffer length",
                    phase = "validation",
                    expected = (expectedLength ?: actualLength).toString(),
                    actual = buffer.size.toString(),
                )
            }
            if (expectedMarker != null && !CottRuntime.sameConst(buffer.dimension, expectedMarker)) {
                mismatch("$path.dimension", expectedMarker.javaClass.name, buffer.dimension)
            }
            buffer as CottBuffer<N>
        },
    )

    public fun <Tag : CottOpaqueTag> opaque(tag: Tag): CottType<Opaque<Tag>> =
        scalar("Opaque<${tag.tag}>", { value, path ->
            val opaque = value as? Opaque<*> ?: mismatch(path, "Opaque<${tag.tag}>", value)
            if (opaque.tag !== tag) CottRuntime.violation(
                "$path has the wrong opaque tag", phase = "validation",
                expected = tag.tag, actual = opaque.tag.tag,
            )
            opaque as Opaque<Tag>
        })

    public fun <T : Any> dyn(trait: CottTrait<T>): CottType<Dyn<T>> = scalar("Dyn<${trait.id}>", { value, path ->
        val dyn = value as? Dyn<*> ?: mismatch(path, "Dyn<${trait.id}>", value)
        if (dyn.trait !== trait || !trait.accepts(dyn.value)) CottRuntime.violation(
            "$path has the wrong dynamic trait", phase = "validation",
            expected = trait.id, actual = dyn.trait.id,
        )
        dyn as Dyn<T>
    })

    public fun <T : Any> factory(type: Class<T>): CottType<CottFactory<T>> =
        scalar("Factory<${type.name}>", { value, path ->
            val factory = value as? CottFactory<*> ?: mismatch(path, "Factory<${type.name}>", value)
            if (factory.type !== type) mismatch(path, "exact factory ${type.name}", value)
            factory as CottFactory<T>
        })

    public fun <T> external(name: String, accepts: (Any?) -> Boolean): CottType<T> =
        scalar(name, { value, path ->
            if (!accepts(value)) mismatch(path, name, value)
            value as T
        })

    public fun literal(expected: Any?): CottType<Any?> =
        scalar("Literal<$expected>", { value, path ->
            if (!CottRuntime.canonicalEqual(value, expected)) mismatch(path, "literal $expected", value)
            value
        })

    public fun oneOf(types: List<CottType<*>>): CottType<Any?> =
        object : CottType<Any?>("Union<${types.joinToString()}>") {
            init {
                if (types.isEmpty()) CottRuntime.violation(
                    "ABI union must have a member",
                    phase = "validation",
                )
            }
            override fun validateDirect(
                value: Any?,
                path: String,
                state: Traversal,
                depth: Int,
            ): Any? {
                for (type in types) {
                    try {
                        return state.transform(value, type, path, depth + 1)
                    } catch (error: CottTraversalViolation) {
                        throw error
                    } catch (_: CottContractViolation) {
                        // A union mismatch is local to this candidate.
                    }
                }
                return mismatch(path, displayName, value)
            }
        }

    public fun <T : Any> nominal(
        name: String,
        exactClass: Class<T>,
        fields: List<CottNominalField<T>>,
        rebuild: (List<Any?>) -> T,
    ): CottType<T> = object : CottType<T>(name) {
        private fun transform(value: Any?, path: String, state: Traversal, depth: Int, strict: Boolean): Any? {
            if (value == null || value.javaClass !== exactClass) {
                return if (strict) mismatch(path, name, value) else value
            }
            val typed = value as T
            var changed = false
            val normalized = fields.map { field ->
                val raw = field.read(typed)
                val next = state.transform(raw, field.type, "$path.${field.name}", depth + 1)
                changed = changed || !CottRuntime.canonicalEqual(raw, next)
                next
            }
            return if (changed) rebuild(normalized) else typed
        }
        override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
            transform(value, path, state, depth, true)
        override fun normalizeDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? =
            transform(value, path, state, depth, false)
        override fun adaptDirect(
            value: Any?,
            mode: RuntimeValidation,
            path: String,
            state: Adaptation,
            depth: Int,
        ): Any? {
            if (value == null || value.javaClass !== exactClass) return value
            val typed = value as T
            val result = ArrayList<Any?>(fields.size)
            var changed = false
            fields.forEach { field ->
                val raw = field.read(typed)
                val adapted = state.transform(raw, field.type, mode, "$path.${field.name}", depth + 1)
                result.add(adapted)
                changed = changed || adapted !== raw
            }
            return if (changed) rebuild(result) else typed
        }
        override suspend fun adaptSuspendDirect(
            value: Any?,
            mode: RuntimeValidation,
            path: String,
            state: Adaptation,
            depth: Int,
        ): Any? {
            if (value == null || value.javaClass !== exactClass) return value
            val typed = value as T
            val result = ArrayList<Any?>(fields.size)
            var changed = false
            for (field in fields) {
                val raw = field.read(typed)
                val adapted = state.transformSuspend(
                    raw, field.type, mode, "$path.${field.name}", depth + 1,
                )
                result.add(adapted)
                changed = changed || adapted !== raw
            }
            return if (changed) rebuild(result) else typed
        }
    }

    public fun <T> iterator(item: CottType<T>): CottType<CottIterator<T>> =
        object : CottType<CottIterator<T>>("Iterator<$item>") {
            override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? = when (value) {
                is CottIterator<*> -> value
                is CottIteratorSource<*> -> value
                else -> mismatch(path, displayName, value)
            }
            override fun adaptDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? = when (value) {
                is CottIterator<*> -> if (value.matches(item, mode)) value else mismatch(
                    path, "compatible Iterator<$item> wrapper", value,
                )
                is CottIteratorSource<*> -> CottIterator(value as CottIteratorSource<T>, item, mode, path)
                else -> value
            }
        }

    public fun <Y, S, R> generator(
        yielded: CottType<Y>, sent: CottType<S>, returned: CottType<R>,
    ): CottType<CottGenerator<Y, S, R>> = object : CottType<CottGenerator<Y, S, R>>(
        "Generator<$yielded, $sent, $returned>"
    ) {
        override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? = when (value) {
            is CottGenerator<*, *, *> -> value
            is CottGeneratorSource<*, *, *> -> value
            else -> mismatch(path, displayName, value)
        }
        override fun adaptDirect(
            value: Any?,
            mode: RuntimeValidation,
            path: String,
            state: Adaptation,
            depth: Int,
        ): Any? = when (value) {
            is CottGenerator<*, *, *> -> if (
                value.matches(yielded, sent, returned, mode)
            ) value else mismatch(path, "compatible $displayName wrapper", value)
            is CottGeneratorSource<*, *, *> -> CottGenerator(
                value as CottGeneratorSource<Y, S, R>, yielded, sent, returned, mode, path,
            )
            else -> value
        }
    }

    public fun <T> asyncIterator(item: CottType<T>): CottType<CottAsyncIterator<T>> =
        object : CottType<CottAsyncIterator<T>>("AsyncIterator<$item>") {
            override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? = when (value) {
                is CottAsyncIterator<*> -> value
                is CottAsyncIteratorSource<*> -> value
                else -> mismatch(path, displayName, value)
            }
            override fun adaptDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? = when (value) {
                is CottAsyncIterator<*> -> if (value.matches(item, mode)) value else mismatch(
                    path, "compatible AsyncIterator<$item> wrapper", value,
                )
                is CottAsyncIteratorSource<*> ->
                    CottAsyncIterator(value as CottAsyncIteratorSource<T>, item, mode, path)
                else -> value
            }
        }

    public fun <Y, S, R> asyncGenerator(
        yielded: CottType<Y>,
        sent: CottType<S>,
        returned: CottType<R>,
    ): CottType<CottAsyncGenerator<Y, S, R>> =
        object : CottType<CottAsyncGenerator<Y, S, R>>(
            "AsyncGenerator<$yielded, $sent, $returned>"
        ) {
            override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? = when (value) {
                is CottAsyncGenerator<*, *, *> -> value
                is CottAsyncGeneratorSource<*, *, *> -> value
                else -> mismatch(path, displayName, value)
            }
            override fun adaptDirect(
                value: Any?,
                mode: RuntimeValidation,
                path: String,
                state: Adaptation,
                depth: Int,
            ): Any? = when (value) {
                is CottAsyncGenerator<*, *, *> -> if (
                    value.matches(yielded, sent, returned, mode)
                ) value else mismatch(path, "compatible $displayName wrapper", value)
                is CottAsyncGeneratorSource<*, *, *> -> CottAsyncGenerator(
                    value as CottAsyncGeneratorSource<Y, S, R>,
                    yielded,
                    sent,
                    returned,
                    mode,
                    path,
                )
                else -> value
            }
        }

    private fun jsonType(): CottType<JsonValue> = object : CottType<JsonValue>("JsonValue") {
        override fun validateDirect(value: Any?, path: String, state: Traversal, depth: Int): Any? = when (value) {
            JsonNull -> value
            is JsonBoolean -> value
            is JsonInteger -> { CottRuntime.checkInt(value.value, true, 64, "$path.value"); value }
            is JsonFloat -> { CottRuntime.validateF64(value.value, "$path.value"); value }
            is JsonString -> { CottRuntime.validateUnicode(value.value, "$path.value"); value }
            is JsonArray -> {
                value.value.forEachIndexed { index, item ->
                    state.transform(item, JSON, "$path.value[$index]", depth + 1)
                }
                value
            }
            is JsonObject -> {
                value.value.forEach { (key, item) ->
                    CottRuntime.validateUnicode(key, "$path.key")
                    state.transform(item, JSON, "$path.value[$key]", depth + 1)
                }
                value
            }
            else -> mismatch(path, "JsonValue", value)
        }
    }
}

public object CottRuntime {
    public val PROJECT_NAME: String = "order-management"
    public val PROJECT_VERSION: String = "0.1.0"
    public val COMPILER_VERSION: String = "1.0.0"
    public val RUNTIME_ABI: Int = 1
    public val RUNTIME_VERSION: String = "1.0.0"

    public fun exitWithCode(code: UByte): kotlin.Nothing =
        kotlin.system.exitProcess(code.toInt())

    public fun requireIdentity(
        expectedProjectName: String,
        expectedProjectVersion: String,
        expectedAbi: Int,
    ) {
        if (
            expectedProjectName != PROJECT_NAME ||
            expectedProjectVersion != PROJECT_VERSION ||
            expectedAbi != RUNTIME_ABI
        ) {
            violation(
                "runtime identity mismatch",
                phase = "identity",
                expected = "$expectedProjectName@$expectedProjectVersion/abi$expectedAbi",
                actual = "$PROJECT_NAME@$PROJECT_VERSION/abi$RUNTIME_ABI",
            )
        }
    }

    public fun <N : CottConst> constValue(
        witness: N,
        kind: CottIntKind,
        path: String = "$",
    ): BigInteger {
        val bits = when (kind) {
            CottIntKind.U8 -> 8
            CottIntKind.U16 -> 16
            CottIntKind.U32 -> 32
            CottIntKind.U64 -> 64
            else -> violation(
                "const generic witness must use an unsigned integer kind",
                phase = "validation",
                expected = "U8, U16, U32, or U64",
                actual = kind.name,
            )
        }
        return checkInt(witness.value, signed = false, bits = bits, path = path)
    }

    public fun <N : CottConst> validateConst(
        witness: N,
        kind: CottIntKind,
        path: String = "$",
    ): N {
        constValue(witness, kind, path)
        return witness
    }

    public fun sameConst(left: CottConst, right: CottConst): Boolean =
        left.javaClass === right.javaClass && left.value == right.value

    public fun constHash(marker: CottConst): Int =
        31 * marker.javaClass.hashCode() + marker.value.hashCode()

    public fun constLength(marker: CottConst, path: String = "$"): Int {
        val value = marker.value
        val maximum = BigInteger.valueOf(Int.MAX_VALUE.toLong())
        if (value < BigInteger.ZERO || value > maximum) violation(
            "$path is not a JVM container length",
            phase = "validation",
            expected = "0..$maximum",
            actual = value.toString(),
        )
        return value.toInt()
    }
    private fun currentObservation(): CottObservation? = threadObservation.get()

    private suspend fun currentSuspendObservation(): CottObservation? =
        coroutineContext[ObservationElement]?.observation ?: threadObservation.get()

    public fun <T> withTestObservation(observation: CottObservation, block: () -> T): T {
        val previous = threadObservation.get()
        threadObservation.set(observation)
        return try { block() } finally { threadObservation.set(previous) }
    }

    public suspend fun <T> withTestObservationSuspend(
        observation: CottObservation,
        block: suspend () -> T,
    ): T = runWithCoroutineContext(coroutineContext + ObservationElement(observation), block)

    internal suspend fun runObservedCheck(block: () -> Boolean) {
        val observation = currentSuspendObservation()
        if (observation == null) block() else withTestObservation(observation, block)
    }

    public fun <T> withFixtureContext(fixtures: CottFixtureContext, block: () -> T): T {
        val previous = threadFixtures.get()
        threadFixtures.set(fixtures)
        return try { block() } finally { threadFixtures.set(previous) }
    }

    public suspend fun <T> withFixtureContextSuspend(
        fixtures: CottFixtureContext,
        block: suspend () -> T,
    ): T = runWithCoroutineContext(coroutineContext + FixtureElement(fixtures), block)

    private fun fixtures(): CottFixtureContext = threadFixtures.get()
        ?: violation("fixture access requires an active test context", phase = "fixture")

    private suspend fun fixturesSuspend(): CottFixtureContext =
        coroutineContext[FixtureElement]?.fixtures ?: fixtures()

    public fun fixtureClockNs(name: String): ULong =
        resolveFixtureClockNs(fixtures(), name)

    public suspend fun fixtureClockNsSuspend(name: String): ULong =
        resolveFixtureClockNs(fixturesSuspend(), name)

    private fun resolveFixtureClockNs(
        context: CottFixtureContext,
        name: String,
    ): ULong {
        validateUnicode(name, "$.name")
        if (name.isEmpty()) violation(
            "fixture clock name must be non-empty",
            phase = "fixture",
        )
        val milliseconds = context.clocks[name] ?: violation(
            "fixture clock is not configured",
            phase = "fixture",
            expected = name,
        )
        if (milliseconds > ULong.MAX_VALUE / 1_000_000uL) violation(
            "fixture clock milliseconds overflow nanoseconds",
            phase = "fixture",
            expected = "0..${ULong.MAX_VALUE / 1_000_000uL}",
            actual = milliseconds.toString(),
        )
        return milliseconds * 1_000_000uL
    }

    public fun fixturePath(fixture: String, path: String): Path =
        resolveFixturePath(fixtures(), fixture, path)

    public suspend fun fixturePathSuspend(fixture: String, path: String): Path =
        resolveFixturePath(fixturesSuspend(), fixture, path)

    private fun resolveFixturePath(
        context: CottFixtureContext,
        fixture: String,
        path: String,
    ): Path {
        validateUnicode(fixture, "$.fixture")
        validateUnicode(path, "$.path")
        if (fixture.isEmpty() || path.isEmpty()) violation(
            "fixture path components must be non-empty",
            phase = "fixture",
        )
        val relative = context.root.fileSystem.getPath(fixture).resolve(path)
        if (relative.isAbsolute) violation("fixture path must be relative", phase = "fixture")
        val resolved = context.root.resolve(relative).normalize()
        if (!resolved.startsWith(context.root)) violation(
            "fixture path escapes its root",
            phase = "fixture",
            actual = resolved.toString(),
        )
        return resolved
    }

    public fun fixtureUrl(fixture: String, path: String): String =
        resolveFixtureUrl(fixtures(), fixture, path)

    public suspend fun fixtureUrlSuspend(fixture: String, path: String): String =
        resolveFixtureUrl(fixturesSuspend(), fixture, path)

    private fun resolveFixtureUrl(
        context: CottFixtureContext,
        fixture: String,
        path: String,
    ): String {
        validateUnicode(fixture, "$.fixture")
        validateUnicode(path, "$.path")
        val value = context.urls[CottFixtureKey(fixture, path)] ?: violation(
            "fixture URL route is not configured",
            phase = "fixture",
            expected = "$fixture:$path",
        )
        val uri = try {
            URI(value)
        } catch (error: IllegalArgumentException) {
            violation("fixture URL is invalid", phase = "fixture", actual = value, cause = error)
        }
        val loopback = uri.host == "localhost" || uri.host == "127.0.0.1" || uri.host == "::1"
        if ((uri.scheme != "http" && uri.scheme != "https") || !loopback || uri.userInfo != null) {
            violation(
                "fixture URL must be loopback HTTP without user information",
                phase = "fixture",
                actual = value,
            )
        }
        return value
    }

    private fun validates(mode: RuntimeValidation): Boolean = when (mode) {
        RuntimeValidation.BOUNDARY -> true
        RuntimeValidation.TEST_ONLY -> currentObservation() != null
        RuntimeValidation.OFF -> false
    }

    public fun shouldValidate(mode: RuntimeValidation): Boolean = validates(mode)

    public fun contractsEnabled(mode: RuntimeValidation): Boolean = shouldValidate(mode)

    private suspend fun validatesSuspend(mode: RuntimeValidation): Boolean = when (mode) {
        RuntimeValidation.BOUNDARY -> true
        RuntimeValidation.TEST_ONLY -> currentSuspendObservation() != null
        RuntimeValidation.OFF -> false
    }

    public suspend fun shouldValidateSuspend(mode: RuntimeValidation): Boolean =
        validatesSuspend(mode)

    public suspend fun contractsEnabledSuspend(mode: RuntimeValidation): Boolean =
        shouldValidateSuspend(mode)

    public fun <T> abi(
        value: Any?,
        type: CottType<T>,
        mode: RuntimeValidation = RuntimeValidation.BOUNDARY,
        path: String = "$",
    ): T = Traversal(normalizeOnly = !validates(mode)).transform(value, type, path, 0)

    public suspend fun <T> abiSuspend(
        value: Any?,
        type: CottType<T>,
        mode: RuntimeValidation = RuntimeValidation.BOUNDARY,
        path: String = "$",
    ): T = Traversal(normalizeOnly = !validatesSuspend(mode)).transform(value, type, path, 0)

    public fun <T> returnValue(
        value: Any?,
        type: CottType<T>,
        mode: RuntimeValidation = RuntimeValidation.BOUNDARY,
        path: String = "$.return",
    ): T {
        val validated = abi(value, type, mode, path)
        return type.adapt(validated, mode, path)
    }

    public suspend fun <T> returnValueSuspend(
        value: Any?,
        type: CottType<T>,
        mode: RuntimeValidation = RuntimeValidation.BOUNDARY,
        path: String = "$.return",
    ): T {
        val validated = abiSuspend(value, type, mode, path)
        return type.adaptSuspend(validated, mode, path)
    }

    public fun int(decimal: String): BigInteger = try {
        BigInteger(decimal)
    } catch (error: NumberFormatException) {
        violation("invalid canonical integer", phase = "validation", actual = decimal, cause = error)
    }

    public fun checkInt(value: BigInteger, signed: Boolean, bits: Int, path: String = "$"): BigInteger {
        if (bits != 8 && bits != 16 && bits != 32 && bits != 64) {
            violation("invalid integer width", phase = "validation")
        }
        val low = if (signed) BigInteger.ONE.shiftLeft(bits - 1).negate() else BigInteger.ZERO
        val high = if (signed) {
            BigInteger.ONE.shiftLeft(bits - 1).subtract(BigInteger.ONE)
        } else {
            BigInteger.ONE.shiftLeft(bits).subtract(BigInteger.ONE)
        }
        if (value < low || value > high) violation(
            "$path is outside ${if (signed) "signed" else "unsigned"} $bits-bit range",
            phase = "validation",
            expected = "$low..$high",
            actual = value.toString(),
        )
        return value
    }

    public fun mathInt(value: Any?): BigInteger = when (value) {
        is BigInteger -> value
        is Byte -> BigInteger.valueOf(value.toLong())
        is Short -> BigInteger.valueOf(value.toLong())
        is Int -> BigInteger.valueOf(value.toLong())
        is Long -> BigInteger.valueOf(value)
        is UByte -> BigInteger.valueOf(value.toLong())
        is UShort -> BigInteger.valueOf(value.toLong())
        is UInt -> BigInteger(value.toString())
        is ULong -> BigInteger(value.toString())
        else -> violation(
            "expected an exact integer",
            phase = "contract-expression",
            actual = value?.javaClass?.name ?: "null",
        )
    }

    public fun intValue(value: BigInteger, kind: CottIntKind, path: String = "$"): Any =
        when (kind) {
            CottIntKind.I8 -> checkInt(value, true, 8, path).toByte()
            CottIntKind.I16 -> checkInt(value, true, 16, path).toShort()
            CottIntKind.I32 -> checkInt(value, true, 32, path).toInt()
            CottIntKind.I64 -> checkInt(value, true, 64, path).toLong()
            CottIntKind.U8 -> checkInt(value, false, 8, path).toInt().toUByte()
            CottIntKind.U16 -> checkInt(value, false, 16, path).toInt().toUShort()
            CottIntKind.U32 -> checkInt(value, false, 32, path).toString().toUInt()
            CottIntKind.U64 -> checkInt(value, false, 64, path).toString().toULong()
        }

    public fun intAdd(left: Any?, right: Any?): BigInteger = mathInt(left).add(mathInt(right))
    public fun intSubtract(left: Any?, right: Any?): BigInteger = mathInt(left).subtract(mathInt(right))
    public fun intMultiply(left: Any?, right: Any?): BigInteger = mathInt(left).multiply(mathInt(right))
    public fun intNegate(value: Any?): BigInteger = mathInt(value).negate()
    public fun intAdd(left: Any?, right: Any?, result: CottIntKind): Any =
        intValue(intAdd(left, right), result)
    public fun intSubtract(left: Any?, right: Any?, result: CottIntKind): Any =
        intValue(intSubtract(left, right), result)
    public fun intMultiply(left: Any?, right: Any?, result: CottIntKind): Any =
        intValue(intMultiply(left, right), result)
    public fun intNegate(value: Any?, result: CottIntKind): Any =
        intValue(intNegate(value), result)

    public fun intDivide(left: Any?, right: Any?): BigInteger {
        val divisor = mathInt(right)
        if (divisor == BigInteger.ZERO) violation(
            "integer division divisor is zero",
            phase = "contract-expression",
        )
        return mathInt(left).divide(divisor)
    }

    public fun euclideanRemainder(left: Any?, right: Any?): BigInteger {
        val divisor = mathInt(right)
        if (divisor == BigInteger.ZERO) violation(
            "integer remainder divisor is zero",
            phase = "contract-expression",
        )
        return mathInt(left).mod(divisor.abs())
    }

    public fun euclideanDivide(left: Any?, right: Any?): BigInteger {
        val dividend = mathInt(left)
        val divisor = mathInt(right)
        if (divisor == BigInteger.ZERO) violation(
            "integer division divisor is zero",
            phase = "contract-expression",
        )
        return dividend.subtract(euclideanRemainder(dividend, divisor)).divide(divisor)
    }

    public fun intDivide(left: Any?, right: Any?, result: CottIntKind): Any =
        intValue(intDivide(left, right), result)

    public fun euclideanRemainder(left: Any?, right: Any?, result: CottIntKind): Any =
        intValue(euclideanRemainder(left, right), result)

    public fun euclideanDivide(left: Any?, right: Any?, result: CottIntKind): Any =
        intValue(euclideanDivide(left, right), result)

    public fun normalizeF32(value: Double, path: String = "$" ): Float {
        if (!value.isFinite()) violation("$path must be a finite F32", phase = "validation")
        val normalized = value.toFloat()
        if (!normalized.isFinite()) violation("$path is outside binary32 range", phase = "validation")
        return normalized
    }

    public fun validateF32(value: Float, path: String = "$" ): Float {
        if (!value.isFinite()) violation("$path must be a finite F32", phase = "validation")
        return value
    }

    public fun validateF64(value: Double, path: String = "$" ): Double {
        if (!value.isFinite()) violation("$path must be a finite F64", phase = "validation")
        return value
    }

    public fun f32Add(left: Float, right: Float): Float = normalizeF32(left.toDouble() + right.toDouble())
    public fun f32Subtract(left: Float, right: Float): Float = normalizeF32(left.toDouble() - right.toDouble())
    public fun f32Multiply(left: Float, right: Float): Float = normalizeF32(left.toDouble() * right.toDouble())
    public fun f32Divide(left: Float, right: Float): Float = normalizeF32(left.toDouble() / right.toDouble())
    public fun f32Negate(value: Float): Float = validateF32(-value)
    public fun f64Add(left: Double, right: Double): Double = validateF64(left + right)
    public fun f64Subtract(left: Double, right: Double): Double = validateF64(left - right)
    public fun f64Multiply(left: Double, right: Double): Double = validateF64(left * right)
    public fun f64Divide(left: Double, right: Double): Double = validateF64(left / right)
    public fun f64Negate(value: Double): Double = validateF64(-value)

    public fun validateUnicode(value: String, path: String = "$" ): String {
        var index = 0
        while (index < value.length) {
            val character = value[index]
            when {
                Character.isHighSurrogate(character) -> {
                    if (index + 1 >= value.length || !Character.isLowSurrogate(value[index + 1])) {
                        violation("$path contains an unpaired UTF-16 surrogate", phase = "validation")
                    }
                    index += 2
                }
                Character.isLowSurrogate(character) ->
                    violation("$path contains an unpaired UTF-16 surrogate", phase = "validation")
                else -> index += 1
            }
        }
        return value
    }

    private fun isIntegerValue(value: Any?): Boolean =
        value is BigInteger ||
            value is Byte ||
            value is Short ||
            value is Int ||
            value is Long ||
            value is UByte ||
            value is UShort ||
            value is UInt ||
            value is ULong

    public fun canonicalEqual(left: Any?, right: Any?): Boolean {
        if (left === right) return true
        if (left == null || right == null) return false
        if (isIntegerValue(left) && isIntegerValue(right)) return mathInt(left) == mathInt(right)
        if (left is CottConst && right is CottConst) return sameConst(left, right)
        if (left.javaClass !== right.javaClass) return false
        if (
            left is String ||
            left is Float ||
            left is Double ||
            left is Boolean ||
            left is Char ||
            left is Number ||
            left is Path ||
            left is Class<*>
        ) {
            return when (left) {
                is Float -> left == right as Float
                is Double -> left == right as Double
                else -> left == right
            }
        }
        return DeepComparator().equal(left, right)
    }

    public fun canonicalOrder(left: Any?, right: Any?): Int {
        if (isIntegerValue(left) && isIntegerValue(right)) {
            return mathInt(left).compareTo(mathInt(right))
        }
        if (left == null || right == null || left.javaClass !== right.javaClass) {
            violation(
                "canonical ordering requires compatible exact types",
                phase = "contract-expression",
                expected = left?.javaClass?.name ?: "null",
                actual = right?.javaClass?.name ?: "null",
            )
        }
        return when {
            left is String && right is String -> compareUnicode(left, right)
            left is Float && right is Float -> {
                validateF32(left)
                validateF32(right)
                when {
                    left < right -> -1
                    left > right -> 1
                    else -> 0
                }
            }
            left is Double && right is Double -> {
                validateF64(left)
                validateF64(right)
                when {
                    left < right -> -1
                    left > right -> 1
                    else -> 0
                }
            }
            else -> try {
                (left as Comparable<Any?>).compareTo(right)
            } catch (error: ClassCastException) {
                violation("value has no canonical ordering", phase = "contract-expression", cause = error)
            }
        }
    }

    private fun compareUnicode(left: String, right: String): Int {
        validateUnicode(left)
        validateUnicode(right)
        var leftIndex = 0
        var rightIndex = 0
        while (leftIndex < left.length && rightIndex < right.length) {
            val leftPoint = left.codePointAt(leftIndex)
            val rightPoint = right.codePointAt(rightIndex)
            if (leftPoint != rightPoint) return leftPoint.compareTo(rightPoint)
            leftIndex += Character.charCount(leftPoint)
            rightIndex += Character.charCount(rightPoint)
        }
        return (left.length - leftIndex).compareTo(right.length - rightIndex)
    }

    public fun canonicalCompare(left: Any?, right: Any?): Int =
        canonicalOrder(left, right)

    public fun startsWith(value: Any?, prefix: Any?): Boolean =
        value is String && prefix is String && value.startsWith(prefix)

    public fun endsWith(value: Any?, suffix: Any?): Boolean =
        value is String && suffix is String && value.endsWith(suffix)

    public fun contains(value: Any?, member: Any?): Boolean = when (value) {
        is String -> member is String && value.contains(member)
        is CottList<*> -> value.any { canonicalEqual(it, member) }
        is CottSet<*> -> value.any { canonicalEqual(it, member) }
        is CottTupleValue -> value.cottTupleElements.any { canonicalEqual(it, member) }
        is CottArray<*, *> -> value.any { canonicalEqual(it, member) }
        is FrozenMap<*, *> -> value.keys.any { canonicalEqual(it, member) }
        is CottKeywordArguments<*> -> value.keys.any { canonicalEqual(it, member) }
        else -> false
    }

    public fun length(value: Any?): BigInteger = BigInteger.valueOf(when (value) {
        is String -> value.codePointCount(0, value.length).toLong()
        is CottBytes -> value.size.toLong()
        is CottBuffer<*> -> value.size.toLong()
        is CottList<*> -> value.size.toLong()
        is CottSet<*> -> value.size.toLong()
        is CottTupleValue -> value.cottTupleElements.size.toLong()
        is CottArray<*, *> -> value.size.toLong()
        is FrozenMap<*, *> -> value.size.toLong()
        is CottKeywordArguments<*> -> value.size.toLong()
        else -> violation("len operand has no canonical length", phase = "contract-expression")
    })

    public fun <T> uniqueBy(values: Iterable<T>, select: (T) -> Any?): Boolean {
        val seen = ArrayList<Any?>()
        for (value in values) {
            val selected = select(value)
            if (seen.any { canonicalEqual(selected, it) }) return false
            seen.add(selected)
        }
        return true
    }

    public fun <T, V : Comparable<V>> descendingBy(values: Iterable<T>, select: (T) -> V): Boolean {
        val iterator = values.iterator()
        if (!iterator.hasNext()) return true
        var previous = select(iterator.next())
        while (iterator.hasNext()) {
            val current = select(iterator.next())
            if (current > previous) return false
            previous = current
        }
        return true
    }

    public fun uniqueBy(values: Iterable<*>, field: String): Boolean =
        uniqueBy(values) { value -> field(value, field) }

    public fun uniqueBy(values: Iterable<*>, expectedOwner: String, field: String): Boolean =
        uniqueBy(values) { value -> field(value, expectedOwner, field) }

    public fun descendingBy(values: Iterable<*>, field: String): Boolean {
        val iterator = values.iterator()
        if (!iterator.hasNext()) return true
        var previous = field(iterator.next(), field)
        while (iterator.hasNext()) {
            val current = field(iterator.next(), field)
            if (canonicalOrder(current, previous) > 0) return false
            previous = current
        }
        return true
    }

    public fun descendingBy(values: Iterable<*>, expectedOwner: String, field: String): Boolean {
        val iterator = values.iterator()
        if (!iterator.hasNext()) return true
        var previous = field(iterator.next(), expectedOwner, field)
        while (iterator.hasNext()) {
            val current = field(iterator.next(), expectedOwner, field)
            if (canonicalOrder(current, previous) > 0) return false
            previous = current
        }
        return true
    }

    // Unicode White_Space, pinned identically in every Cott target. Every
    // member is a BMP scalar, so a UTF-16 surrogate is never whitespace.
    private val cottWhiteSpace: Set<Int> = setOf(
        0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x20, 0x85, 0xA0, 0x1680,
        0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008, 0x2009, 0x200A,
        0x2028, 0x2029, 0x202F, 0x205F, 0x3000,
    )

    private fun stringField(value: Any?, expectedOwner: String, name: String): String =
        field(value, expectedOwner, name) as? String ?: violation(
            "selected field is not a Str",
            phase = "contract-expression",
            expected = "Str",
            actual = field(value, expectedOwner, name)?.javaClass?.name ?: "null",
        )

    private fun stringDependencies(value: Any?, expectedOwner: String, name: String): List<String> {
        val dependencies = field(value, expectedOwner, name) as? Iterable<*> ?: violation(
            "selected dependency field is not a Str collection",
            phase = "contract-expression",
            expected = "Set[Str] or List[Str]",
            actual = field(value, expectedOwner, name)?.javaClass?.name ?: "null",
        )
        return dependencies.map { dependency ->
            dependency as? String ?: violation(
                "dependency is not a Str",
                phase = "contract-expression",
                expected = "Str",
                actual = dependency?.javaClass?.name ?: "null",
            )
        }
    }

    private fun orderedStrings(order: Iterable<*>): List<String> = order.map { item ->
        item as? String ?: violation(
            "order item is not a Str",
            phase = "contract-expression",
            expected = "Str",
            actual = item?.javaClass?.name ?: "null",
        )
    }

    public fun anyBlankBy(values: Iterable<*>, expectedOwner: String, field: String): Boolean =
        values.any { value -> stringField(value, expectedOwner, field).all { it.code in cottWhiteSpace } }

    public fun unknownDependencyBy(
        values: Iterable<*>,
        expectedOwner: String,
        key: String,
        dependencies: String,
    ): Boolean {
        val elements = values.toList()
        val keys = elements.mapTo(HashSet()) { stringField(it, expectedOwner, key) }
        return elements.any { value ->
            stringDependencies(value, expectedOwner, dependencies).any { it !in keys }
        }
    }

    public fun selfDependencyBy(
        values: Iterable<*>,
        expectedOwner: String,
        key: String,
        dependencies: String,
    ): Boolean = values.any { value ->
        stringField(value, expectedOwner, key) in stringDependencies(value, expectedOwner, dependencies)
    }

    public fun cyclicBy(
        values: Iterable<*>,
        expectedOwner: String,
        key: String,
        dependencies: String,
    ): Boolean {
        val elements = values.toList()
        val dependents = LinkedHashMap<String, MutableSet<String>>()
        for (value in elements) dependents.getOrPut(stringField(value, expectedOwner, key)) { LinkedHashSet() }
        for (value in elements) {
            val dependent = stringField(value, expectedOwner, key)
            for (dependency in stringDependencies(value, expectedOwner, dependencies)) {
                dependents[dependency]?.add(dependent)
            }
        }
        val incoming = LinkedHashMap<String, Int>()
        for (node in dependents.keys) incoming[node] = 0
        for (targets in dependents.values) {
            for (target in targets) incoming[target] = incoming.getValue(target) + 1
        }
        val ready = ArrayDeque(incoming.filterValues { it == 0 }.keys)
        var ordered = 0
        while (ready.isNotEmpty()) {
            val node = ready.removeLast()
            ordered += 1
            for (target in dependents.getValue(node)) {
                val remaining = incoming.getValue(target) - 1
                incoming[target] = remaining
                if (remaining == 0) ready.addLast(target)
            }
        }
        return ordered != dependents.size
    }

    public fun permutationBy(
        order: Iterable<*>,
        values: Iterable<*>,
        expectedOwner: String,
        key: String,
    ): Boolean {
        val remaining = HashMap<String, Int>()
        for (value in values) {
            val selected = stringField(value, expectedOwner, key)
            remaining[selected] = (remaining[selected] ?: 0) + 1
        }
        for (item in orderedStrings(order)) {
            val count = remaining[item] ?: 0
            if (count == 0) return false
            remaining[item] = count - 1
        }
        return remaining.values.all { it == 0 }
    }

    public fun dependencyOrderedBy(
        order: Iterable<*>,
        values: Iterable<*>,
        expectedOwner: String,
        key: String,
        dependencies: String,
    ): Boolean {
        val first = HashMap<String, Int>()
        val last = HashMap<String, Int>()
        orderedStrings(order).forEachIndexed { position, item ->
            first.putIfAbsent(item, position)
            last[item] = position
        }
        for (value in values) {
            val dependentPosition = first[stringField(value, expectedOwner, key)] ?: continue
            for (dependency in stringDependencies(value, expectedOwner, dependencies)) {
                val dependencyPosition = last[dependency] ?: continue
                if (dependencyPosition >= dependentPosition) return false
            }
        }
        return true
    }

    public fun field(value: Any?, name: String): Any? {
        if (name.isEmpty()) violation("field name must be non-empty", phase = "contract-expression")
        val nominal = value as? CottFieldValue ?: violation(
            "value does not expose canonical field",
            phase = "contract-expression",
            expected = name,
            actual = value?.javaClass?.name ?: "null",
        )
        return nominal.cottField(name)
    }

    public fun field(value: Any?, expectedOwner: String, name: String): Any? {
        val nominal = value as? CottFieldValue ?: violation(
            "value does not expose canonical field",
            phase = "contract-expression",
            expected = expectedOwner,
            actual = value?.javaClass?.name ?: "null",
        )
        if (nominal.cottTypeIdentity != expectedOwner) violation(
            "field owner identity mismatch",
            phase = "contract-expression",
            expected = expectedOwner,
            actual = nominal.cottTypeIdentity,
        )
        return field(nominal, name)
    }

    public fun resultOk(value: Any?): CottOption<Any?> =
        if (value is Ok<*>) Some(value.value) else Nothing

    public fun resultErr(value: Any?): CottOption<Any?> =
        if (value is Err<*>) Some(value.error) else Nothing

    public fun deepSnapshot(value: Any?): Any? = DeepSnapshotter().snapshot(value)

    public fun deepEqual(left: Any?, right: Any?): Boolean =
        DeepComparator().equal(left, right)

    public fun deepHash(value: Any?): Int = DeepHasher().hash(value)

    public fun optionSome(value: Any?): CottOption<Any?> =
        if (value is Some<*>) Some(value.value) else Nothing

    public fun variant(value: Any?, expectedVariant: String): CottOption<CottList<Any?>> =
        if (value is CottVariant && value.cottVariant == expectedVariant) {
            Some(value.cottPayload)
        } else {
            Nothing
        }

    public fun matchesResultOk(value: Any?): Boolean = value is Ok<*>
    public fun matchesResultErr(value: Any?): Boolean = value is Err<*>
    public fun matchesSome(value: Any?): Boolean = value is Some<*>
    public fun matchesNothing(value: Any?): Boolean = value === Nothing
    public fun matchesVariant(value: Any?, expectedVariant: String): Boolean =
        value is CottVariant && value.cottVariant == expectedVariant

    private fun observe(
        observation: CottObservation?,
        condition: Boolean,
        symbol: String,
        phase: String,
        clause: String?,
    ) {
        if (observation != null && clause != null) {
            observation.record(CottClauseObservation(symbol, clause, phase, condition))
        }
    }

    public fun requireContract(
        condition: Boolean,
        symbol: String,
        clause: String? = null,
        span: CottSpan? = null,
        expected: String? = null,
        actual: String? = null,
    ) = checkContract(condition, symbol, "requires", clause, span, expected, actual)

    public fun ensureContract(
        condition: Boolean,
        symbol: String,
        clause: String? = null,
        span: CottSpan? = null,
        expected: String? = null,
        actual: String? = null,
    ) = checkContract(condition, symbol, "ensures", clause, span, expected, actual)

    public fun invariant(
        condition: Boolean,
        symbol: String,
        clause: String? = null,
        span: CottSpan? = null,
        expected: String? = null,
        actual: String? = null,
    ) = checkContract(condition, symbol, "invariant", clause, span, expected, actual)

    public fun checkContract(
        condition: Boolean,
        symbol: String,
        phase: String,
        clause: String? = null,
        span: CottSpan? = null,
        expected: String? = null,
        actual: String? = null,
    ) {
        observe(currentObservation(), condition, symbol, phase, clause)
        if (!condition) violation("$phase clause failed", symbol, phase, span, expected, actual, clause)
    }

    public suspend fun checkContractSuspend(
        condition: Boolean,
        symbol: String,
        phase: String,
        clause: String? = null,
        span: CottSpan? = null,
        expected: String? = null,
        actual: String? = null,
    ) {
        observe(currentSuspendObservation(), condition, symbol, phase, clause)
        if (!condition) violation("$phase clause failed", symbol, phase, span, expected, actual, clause)
    }

    public suspend fun requireContractSuspend(
        condition: Boolean,
        symbol: String,
        clause: String? = null,
        span: CottSpan? = null,
        expected: String? = null,
        actual: String? = null,
    ) = checkContractSuspend(condition, symbol, "requires", clause, span, expected, actual)

    public suspend fun ensureContractSuspend(
        condition: Boolean,
        symbol: String,
        clause: String? = null,
        span: CottSpan? = null,
        expected: String? = null,
        actual: String? = null,
    ) = checkContractSuspend(condition, symbol, "ensures", clause, span, expected, actual)

    public suspend fun invariantSuspend(
        condition: Boolean,
        symbol: String,
        clause: String? = null,
        span: CottSpan? = null,
        expected: String? = null,
        actual: String? = null,
    ) = checkContractSuspend(condition, symbol, "invariant", clause, span, expected, actual)

    public fun snapshotBytes(bytes: ByteArray): CottBytes = CottBytes(bytes)
    public fun <N : CottConst> snapshotBuffer(
        bytes: ByteArray,
        dimension: N,
    ): CottBuffer<N> = CottBuffer(bytes, dimension)
    public fun <T> snapshotList(values: Iterable<T>): CottList<T> = CottList(values)
    public fun <T> snapshotSet(values: Iterable<T>): CottSet<T> = CottSet(values)
    public fun <K, V> snapshotMap(values: Map<out K, V>): FrozenMap<K, V> = FrozenMap(values)
    public fun snapshotTuple(values: Iterable<Any?>): CottTuple = CottTuple(values)
    public fun <T, N : CottConst> snapshotArray(
        values: Iterable<T>,
        dimension: N,
    ): CottArray<T, N> = CottArray(values, dimension)

    public fun <T> wrapIterator(
        source: CottIteratorSource<T>, item: CottType<T>,
        mode: RuntimeValidation = RuntimeValidation.BOUNDARY, path: String = "$.return",
    ): CottIterator<T> = CottIterator(source, item, mode, path)

    public fun <Y, S, R> wrapGenerator(
        source: CottGeneratorSource<Y, S, R>, yielded: CottType<Y>, sent: CottType<S>, returned: CottType<R>,
        mode: RuntimeValidation = RuntimeValidation.BOUNDARY, path: String = "$.return",
    ): CottGenerator<Y, S, R> = CottGenerator(source, yielded, sent, returned, mode, path)

    public fun <T> wrapAsyncIterator(
        source: CottAsyncIteratorSource<T>, item: CottType<T>,
        mode: RuntimeValidation = RuntimeValidation.BOUNDARY, path: String = "$.return",
    ): CottAsyncIterator<T> = CottAsyncIterator(source, item, mode, path)

    public fun <Y, S, R> wrapAsyncGenerator(
        source: CottAsyncGeneratorSource<Y, S, R>, yielded: CottType<Y>, sent: CottType<S>, returned: CottType<R>,
        mode: RuntimeValidation = RuntimeValidation.BOUNDARY, path: String = "$.return",
    ): CottAsyncGenerator<Y, S, R> = CottAsyncGenerator(source, yielded, sent, returned, mode, path)

    public fun rethrowImplementation(
        error: Throwable,
        symbol: String,
        span: CottSpan? = null,
        asynchronous: Boolean = false,
    ): kotlin.Nothing {
        if (error is CottContractViolation) {
            if (error.symbol == null) error.symbol = symbol
            if (error.span == null) error.span = span
            throw error
        }
        if (asynchronous && error is CancellationException) throw error
        if (error is Error) throw error
        violation(
            "implementation raised an undeclared exception",
            symbol = symbol,
            phase = "implementation-call",
            span = span,
            expected = "declared Result error or ordinary return",
            actual = error.javaClass.name,
            cause = error,
        )
    }

    public fun violation(
        detail: String,
        symbol: String? = null,
        phase: String? = null,
        span: CottSpan? = null,
        expected: String? = null,
        actual: String? = null,
        clause: String? = null,
        cause: Throwable? = null,
    ): kotlin.Nothing = throw CottContractViolation(detail, symbol, phase, span, expected, actual, clause, cause)
}

public sealed interface CottStep<out T> {
    public data class Yield<out T>(public val value: T) : CottStep<T>
    public object Done : CottStep<kotlin.Nothing>
}

public sealed interface CottGeneratorStep<out Y, out R> {
    public data class Yield<out Y>(public val value: Y) : CottGeneratorStep<Y, kotlin.Nothing>
    public data class Return<out R>(public val value: R) : CottGeneratorStep<kotlin.Nothing, R>
}

public interface CottIteratorSource<out T> {
    public fun next(): CottStep<T>
    public fun close() {}
}

public interface CottGeneratorSource<out Y, in S, out R> {
    public fun start(): CottGeneratorStep<Y, R>
    public fun send(value: S): CottGeneratorStep<Y, R>
    public fun next(): CottGeneratorStep<Y, R>
    public fun raise(error: Throwable): CottGeneratorStep<Y, R>
    public fun close() {}
}

public interface CottAsyncIteratorSource<out T> {
    public suspend fun next(): CottStep<T>
    public suspend fun close() {}
}

public interface CottAsyncGeneratorSource<out Y, in S, out R> {
    public suspend fun start(): CottGeneratorStep<Y, R>
    public suspend fun send(value: S): CottGeneratorStep<Y, R>
    public suspend fun next(): CottGeneratorStep<Y, R>
    public suspend fun raise(error: Throwable): CottGeneratorStep<Y, R>
    public suspend fun close() {}
}

private enum class ProtocolState { NEW, ACTIVE, DONE, CLOSED }

private class OperationGuard(private val asynchronous: Boolean) {
    private val active = AtomicBoolean(false)
    fun <T> run(block: () -> T): T {
        begin()
        return try { block() } finally { active.set(false) }
    }
    suspend fun <T> runSuspend(block: suspend () -> T): T {
        begin()
        return try { block() } finally { active.set(false) }
    }
    private fun begin() {
        if (!active.compareAndSet(false, true)) CottRuntime.violation(
            "concurrent ${if (asynchronous) "async " else ""}protocol operation",
            phase = if (asynchronous) "async-lifecycle" else "iterator-lifecycle",
        )
    }
}

public class CottIterator<T> internal constructor(
    private val source: CottIteratorSource<T>,
    private val item: CottType<T>,
    private val mode: RuntimeValidation,
    private val path: String,
) : Iterator<T>, AutoCloseable {
    private val guard = OperationGuard(false)
    private var state = ProtocolState.NEW
    private var pending: CottOption<T> = Nothing

    internal fun matches(expectedItem: CottType<*>, expectedMode: RuntimeValidation): Boolean =
        item === expectedItem && mode == expectedMode

    private fun pull(): Boolean {
        if (state == ProtocolState.DONE || state == ProtocolState.CLOSED) return false
        return when (val step = source.next()) {
            CottStep.Done -> { state = ProtocolState.DONE; false }
            is CottStep.Yield -> {
                state = ProtocolState.ACTIVE
                pending = Some(CottRuntime.returnValue(step.value, item, mode, "$path.yield"))
                true
            }
        }
    }

    override fun hasNext(): Boolean = guard.run {
        pending is Some<*> || pull()
    }

    override fun next(): T = guard.run {
        if (pending !is Some<*> && !pull()) throw NoSuchElementException("Cott iterator is complete")
        val result = (pending as Some<T>).value
        pending = Nothing
        result
    }

    override fun close() = guard.run {
        if (state == ProtocolState.CLOSED || state == ProtocolState.DONE) return@run
        source.close()
        state = ProtocolState.CLOSED
        pending = Nothing
    }
}

public class CottGenerator<Y, S, R> internal constructor(
    private val source: CottGeneratorSource<Y, S, R>,
    private val yielded: CottType<Y>,
    private val sent: CottType<S>,
    private val returned: CottType<R>,
    private val mode: RuntimeValidation,
    private val path: String,
) : Iterator<Y>, AutoCloseable {
    private val guard = OperationGuard(false)
    private var state = ProtocolState.NEW
    private var completion: CottOption<R> = Nothing
    private var pending: CottOption<Y> = Nothing

    internal fun matches(
        expectedYielded: CottType<*>,
        expectedSent: CottType<*>,
        expectedReturned: CottType<*>,
        expectedMode: RuntimeValidation,
    ): Boolean =
        yielded === expectedYielded &&
            sent === expectedSent &&
            returned === expectedReturned &&
            mode == expectedMode

    private fun validate(step: CottGeneratorStep<Y, R>): CottGeneratorStep<Y, R> = when (step) {
        is CottGeneratorStep.Yield -> {
            state = ProtocolState.ACTIVE
            CottGeneratorStep.Yield(CottRuntime.returnValue(step.value, yielded, mode, "$path.yield"))
        }
        is CottGeneratorStep.Return -> {
            val value = CottRuntime.returnValue(step.value, returned, mode, "$path.return")
            completion = Some(value)
            state = ProtocolState.DONE
            CottGeneratorStep.Return(value)
        }
    }

    private fun advance(): CottGeneratorStep<Y, R> {
        if (state == ProtocolState.DONE || state == ProtocolState.CLOSED) {
            return (completion as? Some<R>)?.let { CottGeneratorStep.Return(it.value) }
                ?: throw NoSuchElementException("Cott generator is closed")
        }
        return validate(
            if (state == ProtocolState.NEW) source.start() else source.next()
        )
    }

    public fun nextStep(): CottGeneratorStep<Y, R> = guard.run { advance() }

    public fun send(value: S): CottGeneratorStep<Y, R> = guard.run {
        if (state == ProtocolState.NEW) CottRuntime.violation(
            "generator must be started before send", phase = "generator-lifecycle",
        )
        if (state == ProtocolState.DONE || state == ProtocolState.CLOSED) {
            CottRuntime.violation("generator is complete", phase = "generator-lifecycle")
        }
        validate(source.send(CottRuntime.abi(value, sent, mode, "$path.send")))
    }

    public fun throwInto(error: Throwable): CottGeneratorStep<Y, R> = guard.run {
        if (state == ProtocolState.DONE || state == ProtocolState.CLOSED) {
            CottRuntime.violation("generator is complete", phase = "generator-lifecycle")
        }
        validate(source.raise(error))
    }

    public fun returnValue(): CottOption<R> = completion

    override fun hasNext(): Boolean = guard.run {
        if (pending is Some<*>) return@run true
        when (val step = advance()) {
            is CottGeneratorStep.Yield -> { pending = Some(step.value); true }
            is CottGeneratorStep.Return -> false
        }
    }

    override fun next(): Y = guard.run {
        if (pending is Some<*>) {
            val result = (pending as Some<Y>).value
            pending = Nothing
            return@run result
        }
        when (val step = advance()) {
            is CottGeneratorStep.Yield -> step.value
            is CottGeneratorStep.Return -> throw NoSuchElementException("Cott generator returned")
        }
    }

    override fun close() = guard.run {
        if (state == ProtocolState.CLOSED || state == ProtocolState.DONE) return@run
        source.close()
        state = ProtocolState.CLOSED
        pending = Nothing
    }
}

public class CottAsyncIterator<T> internal constructor(
    private val source: CottAsyncIteratorSource<T>,
    private val item: CottType<T>,
    private val mode: RuntimeValidation,
    private val path: String,
) {
    private val guard = OperationGuard(true)
    private var state = ProtocolState.NEW

    internal fun matches(expectedItem: CottType<*>, expectedMode: RuntimeValidation): Boolean =
        item === expectedItem && mode == expectedMode

    public suspend fun next(): CottStep<T> = guard.runSuspend {
        if (state == ProtocolState.DONE || state == ProtocolState.CLOSED) return@runSuspend CottStep.Done
        when (val step = source.next()) {
            CottStep.Done -> { state = ProtocolState.DONE; CottStep.Done }
            is CottStep.Yield -> {
                state = ProtocolState.ACTIVE
                CottStep.Yield(CottRuntime.returnValueSuspend(step.value, item, mode, "$path.yield"))
            }
        }
    }

    public suspend fun close() = guard.runSuspend {
        if (state == ProtocolState.CLOSED || state == ProtocolState.DONE) return@runSuspend
        source.close()
        state = ProtocolState.CLOSED
    }
}

public class CottAsyncGenerator<Y, S, R> internal constructor(
    private val source: CottAsyncGeneratorSource<Y, S, R>,
    private val yielded: CottType<Y>,
    private val sent: CottType<S>,
    private val returned: CottType<R>,
    private val mode: RuntimeValidation,
    private val path: String,
) {
    private val guard = OperationGuard(true)
    private var state = ProtocolState.NEW
    private var completion: CottOption<R> = Nothing

    internal fun matches(
        expectedYielded: CottType<*>,
        expectedSent: CottType<*>,
        expectedReturned: CottType<*>,
        expectedMode: RuntimeValidation,
    ): Boolean =
        yielded === expectedYielded &&
            sent === expectedSent &&
            returned === expectedReturned &&
            mode == expectedMode

    private suspend fun validate(step: CottGeneratorStep<Y, R>): CottGeneratorStep<Y, R> = when (step) {
        is CottGeneratorStep.Yield -> {
            state = ProtocolState.ACTIVE
            CottGeneratorStep.Yield(CottRuntime.returnValueSuspend(step.value, yielded, mode, "$path.yield"))
        }
        is CottGeneratorStep.Return -> {
            val value = CottRuntime.returnValueSuspend(step.value, returned, mode, "$path.return")
            completion = Some(value)
            state = ProtocolState.DONE
            CottGeneratorStep.Return(value)
        }
    }

    public suspend fun start(): CottGeneratorStep<Y, R> = guard.runSuspend {
        if (state != ProtocolState.NEW) CottRuntime.violation(
            "async generator has already started", phase = "async-lifecycle",
        )
        validate(source.start())
    }

    public suspend fun next(): CottGeneratorStep<Y, R> = guard.runSuspend {
        if (state == ProtocolState.NEW) validate(source.start())
        else if (state == ProtocolState.ACTIVE) validate(source.next())
        else (completion as? Some<R>)?.let { CottGeneratorStep.Return(it.value) }
            ?: CottRuntime.violation("async generator is closed", phase = "async-lifecycle")
    }

    public suspend fun send(value: S): CottGeneratorStep<Y, R> = guard.runSuspend {
        if (state == ProtocolState.NEW) CottRuntime.violation(
            "async generator must be started before send", phase = "async-lifecycle",
        )
        if (state == ProtocolState.DONE || state == ProtocolState.CLOSED) {
            CottRuntime.violation("async generator is complete", phase = "async-lifecycle")
        }
        validate(source.send(CottRuntime.abiSuspend(value, sent, mode, "$path.send")))
    }

    public suspend fun throwInto(error: Throwable): CottGeneratorStep<Y, R> = guard.runSuspend {
        if (state == ProtocolState.DONE || state == ProtocolState.CLOSED) {
            CottRuntime.violation("async generator is complete", phase = "async-lifecycle")
        }
        validate(source.raise(error))
    }

    public fun returnValue(): CottOption<R> = completion

    public suspend fun close() = guard.runSuspend {
        if (state == ProtocolState.CLOSED || state == ProtocolState.DONE) return@runSuspend
        source.close()
        state = ProtocolState.CLOSED
    }
}

public class CottSyncLock public constructor() {
    private val lock = ReentrantLock(true)
    public fun <T> withLock(block: () -> T): T {
        lock.lock()
        return try { block() } finally { lock.unlock() }
    }
}

private class CoroutineLockOwnership(
    val lock: Any,
    val token: Any,
    val parent: CoroutineLockOwnership?,
)

private class CoroutineLockElement private constructor(
    private val ownership: CoroutineLockOwnership?,
    private val pendingInstallation: Boolean,
) : AbstractCoroutineContextElement(Key), CopyableThreadContextElement<Unit> {
    companion object Key : CoroutineContext.Key<CoroutineLockElement> {
        private val Empty = CoroutineLockElement(null, pendingInstallation = false)

        fun installing(
            lock: Any,
            token: Any,
            parent: CoroutineLockElement?,
        ): CoroutineLockElement = CoroutineLockElement(
            CoroutineLockOwnership(lock, token, parent?.ownership),
            pendingInstallation = true,
        )
    }

    fun tokenFor(target: Any): Any? {
        var current = ownership
        while (current != null) {
            if (current.lock === target) return current.token
            current = current.parent
        }
        return null
    }

    private fun activated(): CoroutineLockElement =
        if (pendingInstallation) CoroutineLockElement(ownership, pendingInstallation = false) else this

    // withContext copies a newly added element once; only later copies denote a launched child.
    override fun copyForChild(): CoroutineLockElement =
        if (pendingInstallation) activated() else Empty

    override fun mergeForChild(overwritingElement: CoroutineContext.Element): CoroutineContext =
        (overwritingElement as CoroutineLockElement).activated()

    override fun updateThreadContext(context: CoroutineContext) = Unit

    override fun restoreThreadContext(context: CoroutineContext, oldState: Unit) = Unit
}

public class CottSuspendLock public constructor() {
    private val lock = Mutex()

    public suspend fun <T> withLock(block: suspend () -> T): T {
        val parent = coroutineContext[CoroutineLockElement]
        if (parent?.tokenFor(this) != null) return block()

        val token = Any()
        lock.lock(token)
        return try {
            withContext(CoroutineLockElement.installing(this, token, parent)) { block() }
        } finally {
            lock.unlock(token)
        }
    }
}

private class CottHybridLock {
    private enum class WaiterState {
        NEW,
        QUEUED,
        GRANTED,
        ACQUIRED,
        CANCELLED,
    }

    private sealed class Waiter(val token: Any) {
        var state: WaiterState = WaiterState.NEW
    }

    private class SyncWaiter(token: Any) : Waiter(token) {
        val ready = CountDownLatch(1)
    }

    private class AsyncWaiter(
        token: Any,
        val continuation: CancellableContinuation<Unit>,
    ) : Waiter(token)

    private val monitor = Any()
    private val waiters = ArrayDeque<Waiter>()
    private var owner: Any? = null
    private var depth = 0

    private fun tryAcquireLocked(token: Any): Boolean {
        if (owner === token) {
            depth += 1
            return true
        }
        if (owner == null && waiters.isEmpty()) {
            owner = token
            depth = 1
            return true
        }
        return false
    }

    private fun grantNextLocked(): Waiter? {
        while (!waiters.isEmpty()) {
            val waiter = waiters.removeFirst()
            check(waiter.state == WaiterState.QUEUED) {
                "Cott resource lock queue contains a waiter that is not queued"
            }
            if (waiter is AsyncWaiter && !waiter.continuation.isActive) {
                waiter.state = WaiterState.CANCELLED
                continue
            }
            owner = waiter.token
            depth = 1
            waiter.state = WaiterState.GRANTED
            return waiter
        }
        return null
    }

    private fun releaseLocked(token: Any): Waiter? {
        if (owner !== token) {
            throw IllegalStateException("Cott resource lock released by a non-owner")
        }
        check(depth > 0) { "Cott resource lock has invalid ownership depth" }
        depth -= 1
        if (depth != 0) return null
        owner = null
        return grantNextLocked()
    }

    private fun wake(waiter: Waiter?) {
        when (waiter) {
            null -> Unit
            is SyncWaiter -> waiter.ready.countDown()
            is AsyncWaiter -> waiter.continuation.resume(Unit)
        }
    }

    private fun cancel(waiter: Waiter) {
        val next = synchronized(monitor) {
            when (waiter.state) {
                WaiterState.NEW -> {
                    waiter.state = WaiterState.CANCELLED
                    null
                }
                WaiterState.QUEUED -> {
                    check(waiters.remove(waiter)) {
                        "Cott resource lock lost a queued waiter"
                    }
                    waiter.state = WaiterState.CANCELLED
                    null
                }
                WaiterState.GRANTED -> {
                    val next = releaseLocked(waiter.token)
                    waiter.state = WaiterState.CANCELLED
                    next
                }
                WaiterState.ACQUIRED,
                WaiterState.CANCELLED -> null
            }
        }
        wake(next)
    }

    private fun acquireSync(token: Any) {
        if (synchronized(monitor) { tryAcquireLocked(token) }) return

        val waiter = SyncWaiter(token)
        val queued = synchronized(monitor) {
            if (tryAcquireLocked(token)) {
                waiter.state = WaiterState.ACQUIRED
                false
            } else {
                waiter.state = WaiterState.QUEUED
                waiters.addLast(waiter)
                true
            }
        }
        if (!queued) return

        try {
            waiter.ready.await()
        } catch (error: InterruptedException) {
            cancel(waiter)
            throw error
        }
        synchronized(monitor) {
            check(waiter.state == WaiterState.GRANTED && owner === token) {
                "Cott resource lock resumed a synchronous waiter without ownership"
            }
            waiter.state = WaiterState.ACQUIRED
        }
    }

    private suspend fun acquireSuspend(token: Any) {
        if (synchronized(monitor) { tryAcquireLocked(token) }) return

        lateinit var waiter: AsyncWaiter
        suspendCancellableCoroutine<Unit> { continuation ->
            waiter = AsyncWaiter(token, continuation)
            continuation.invokeOnCancellation { cancel(waiter) }
            val acquired = synchronized(monitor) {
                if (waiter.state == WaiterState.CANCELLED) {
                    false
                } else if (tryAcquireLocked(token)) {
                    waiter.state = WaiterState.GRANTED
                    true
                } else {
                    waiter.state = WaiterState.QUEUED
                    waiters.addLast(waiter)
                    false
                }
            }
            if (acquired) continuation.resume(Unit)
        }
        synchronized(monitor) {
            check(waiter.state == WaiterState.GRANTED && owner === token) {
                "Cott resource lock resumed an asynchronous waiter without ownership"
            }
            waiter.state = WaiterState.ACQUIRED
        }
    }

    private fun release(token: Any) {
        val next = synchronized(monitor) { releaseLocked(token) }
        wake(next)
    }

    fun <T> withSync(block: () -> T): T {
        val token = Thread.currentThread()
        acquireSync(token)
        return try {
            block()
        } finally {
            release(token)
        }
    }

    suspend fun <T> withSuspend(block: suspend () -> T): T {
        val parent = coroutineContext[CoroutineLockElement]
        if (parent?.tokenFor(this) != null) return block()

        val token = Any()
        acquireSuspend(token)
        return try {
            withContext(CoroutineLockElement.installing(this, token, parent)) { block() }
        } finally {
            release(token)
        }
    }
}

public class CottResourceGuard public constructor() {
    private val lock = CottHybridLock()
    public fun <T> withLock(block: () -> T): T = lock.withSync(block)
    public suspend fun <T> withLockSuspend(block: suspend () -> T): T =
        lock.withSuspend(block)
}

public class CottStateField public constructor(
    public val name: String,
    public val type: CottType<*>,
    public val read: () -> Any?,
    public val write: (Any?) -> Unit,
)

public data class CottTransition(
    public val field: String,
    public val from: Any,
    public val to: Any,
)

public data class CottInvariant(
    public val clause: String,
    public val check: () -> Boolean,
    public val span: CottSpan? = null,
) {
    public companion object {
        public fun checked(clause: String, check: () -> Unit, span: CottSpan? = null): CottInvariant =
            CottInvariant(clause, CheckedInvariant(check), span)
    }
}

private class CheckedInvariant(private val check: () -> Unit) : () -> Boolean {
    override fun invoke(): Boolean {
        check()
        return true
    }
}

public class CottStateSnapshot internal constructor(
    internal val values: Map<String, Any?>,
)

public class CottResourceContract public constructor(
    private val symbol: String,
    fields: List<CottStateField>,
    modifies: Set<String>,
    transitions: List<CottTransition>,
    invariants: List<CottInvariant>,
    private val guard: CottResourceGuard = CottResourceGuard(),
) {
    private val fields = CottList(fields)
    private val modifies = CottSet(modifies)
    private val transitions = CottList(transitions)
    private val invariants = CottList(invariants)
    private val fieldByName: Map<String, CottStateField> = fields.associateBy { it.name }
    private val transitionFields: CottSet<String> = CottSet(transitions.map { it.field })

    init {
        val names = fields.map { it.name }
        if (names.toSet().size != names.size || names.any { it.isEmpty() }) {
            CottRuntime.violation("resource state fields must be unique and non-empty", symbol, "state")
        }
        val known = names.toSet()
        if (modifies.any { it !in known } || transitions.any { it.field !in known }) {
            CottRuntime.violation("resource rules reference an unknown state field", symbol, "state")
        }
    }

    public fun snapshot(): CottStateSnapshot = CottStateSnapshot(
        LinkedHashMap<String, Any?>().also { copy ->
            fields.forEach { copy[it.name] = CottRuntime.deepSnapshot(it.read()) }
        },
    )

    private fun validateState() {
        fields.forEach { field ->
            val raw = field.read()
            val validated = CottRuntime.abi(raw, field.type, RuntimeValidation.BOUNDARY, "$.${field.name}")
            if (!CottRuntime.deepEqual(raw, validated)) field.write(validated)
        }
    }

    private fun validateTransitions(old: CottStateSnapshot, exceptional: Boolean) {
        transitions.forEach { transition ->
            val before = old.values[transition.field]
            val after = fieldByName.getValue(transition.field).read()
            if (before !== transition.from) CottRuntime.violation(
                if (exceptional) "exceptional resource transition source failed" else "resource transition source failed",
                symbol, if (exceptional) "exceptional-transitions" else "transitions",
                expected = "${transition.field} identity ${transition.from}", actual = before.toString(),
            )
            val targetMatches = after === transition.to
            if ((!exceptional && !targetMatches) || (exceptional && after !== before && !targetMatches)) {
                CottRuntime.violation(
                    if (exceptional) "exceptional resource transition target failed" else "resource transition target failed",
                    symbol, if (exceptional) "exceptional-transitions" else "transitions",
                    expected = if (exceptional) "old or ${transition.to}" else transition.to.toString(),
                    actual = after.toString(),
                )
            }
        }
    }

    private fun validateFrame(old: CottStateSnapshot, exceptional: Boolean) {
        val transitionFields = this.transitionFields
        fields.forEach { field ->
            if (field.name !in modifies && field.name !in transitionFields) {
                CottRuntime.checkContract(
                    CottRuntime.deepEqual(field.read(), old.values[field.name]),
                    symbol,
                    if (exceptional) "exceptional-modifies" else "modifies",
                    clause = "modifies:${field.name}",
                    expected = "${field.name} unchanged",
                    actual = "${field.name} changed",
                )
            }
        }
    }

    private suspend fun validateFrameSuspend(old: CottStateSnapshot, exceptional: Boolean) {
        val transitionFields = this.transitionFields
        for (field in fields) {
            if (field.name !in modifies && field.name !in transitionFields) {
                CottRuntime.checkContractSuspend(
                    CottRuntime.deepEqual(field.read(), old.values[field.name]),
                    symbol,
                    if (exceptional) "exceptional-modifies" else "modifies",
                    clause = "modifies:${field.name}",
                    expected = "${field.name} unchanged",
                    actual = "${field.name} changed",
                )
            }
        }
    }

    private fun validateInvariants() {
        invariants.forEach { invariant ->
            if (invariant.check is CheckedInvariant) {
                invariant.check()
                return@forEach
            }
            CottRuntime.invariant(
                invariant.check(), symbol, invariant.clause, invariant.span,
                expected = invariant.clause, actual = "false",
            )
        }
    }

    private suspend fun validateInvariantsSuspend() {
        for (invariant in invariants) {
            if (invariant.check is CheckedInvariant) {
                CottRuntime.runObservedCheck(invariant.check)
                continue
            }
            CottRuntime.invariantSuspend(
                invariant.check(), symbol, invariant.clause, invariant.span,
                expected = invariant.clause, actual = "false",
            )
        }
    }

    public fun validateInitial() {
        validateState()
        validateInvariants()
    }

    public fun validateNormal(old: CottStateSnapshot) {
        validateState()
        validateTransitions(old, exceptional = false)
        validateFrame(old, exceptional = false)
        validateInvariants()
    }

    public fun validateExceptional(old: CottStateSnapshot) {
        validateState()
        validateTransitions(old, exceptional = true)
        validateFrame(old, exceptional = true)
        validateInvariants()
    }

    public suspend fun validateNormalSuspend(old: CottStateSnapshot) {
        validateState()
        validateTransitions(old, exceptional = false)
        validateFrameSuspend(old, exceptional = false)
        validateInvariantsSuspend()
    }

    public suspend fun validateExceptionalSuspend(old: CottStateSnapshot) {
        validateState()
        validateTransitions(old, exceptional = true)
        validateFrameSuspend(old, exceptional = true)
        validateInvariantsSuspend()
    }

    public fun <R, T> enforceMutation(
        before: () -> Unit,
        implementation: () -> R,
        after: (R) -> T,
    ): T = guard.withLock {
        val old = snapshot()
        before()
        val raw = try {
            implementation()
        } catch (error: Throwable) {
            validateExceptional(old)
            throw error
        }
        validateNormal(old)
        after(raw)
    }

    public suspend fun <R, T> enforceMutationSuspend(
        before: suspend () -> Unit,
        implementation: suspend () -> R,
        after: suspend (R) -> T,
    ): T = guard.withLockSuspend {
        val old = snapshot()
        before()
        val raw = try {
            implementation()
        } catch (error: Throwable) {
            validateExceptionalSuspend(old)
            throw error
        }
        validateNormalSuspend(old)
        after(raw)
    }

    public fun <T> withMutation(block: () -> T): T =
        enforceMutation(before = {}, implementation = block, after = { it })

    public suspend fun <T> withMutationSuspend(block: suspend () -> T): T =
        enforceMutationSuspend(before = {}, implementation = block, after = { it })
}
