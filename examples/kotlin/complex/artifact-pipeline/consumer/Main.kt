import cott_runtime.CottList
import cott_runtime.CottResult
import cott_runtime.CottSet
import cott_runtime.Err
import cott_runtime.Ok
import curriculum.artifact_pipeline.ArtifactPipelineError
import curriculum.artifact_pipeline.BuildStep
import curriculum.artifact_pipeline.Pipeline
import curriculum.artifact_pipeline.plan_pipeline
import curriculum.artifact_pipeline.topologically_order_steps

private const val MAX_PERMUTATION_NODES = 8

private data class RawStep(val name: String, val needs: List<String>)
private data class Case(val name: String, val steps: List<RawStep>, val expected: Expected)

private sealed interface Expected {
    data class Success(val names: List<String>) : Expected
    data class Failure(val error: String) : Expected
}

private fun <T> permutations(items: List<T>): List<List<T>> {
    if (items.isEmpty()) return listOf(emptyList())
    return items.flatMapIndexed { index, item ->
        permutations(items.filterIndexed { other, _ -> other != index }).map { listOf(item) + it }
    }
}

private fun <T> repeatedProduct(options: List<T>, count: Int): List<List<T>> {
    if (count == 0) return listOf(emptyList())
    return repeatedProduct(options, count - 1).flatMap { prefix ->
        options.map { option -> prefix + option }
    }
}

private fun powerSet(labels: List<String>): List<List<String>> =
    (0 until (1 shl labels.size)).map { mask ->
        labels.filterIndexed { index, _ -> mask and (1 shl index) != 0 }
    }

// The contract's any_blank_by table: the 25 Unicode White_Space code points, not Kotlin's isWhitespace.
private const val WHITE_SPACE =
    "\t\n\u000b\u000c\r \u0085\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000"

private fun isBlank(name: String): Boolean = name.all { it in WHITE_SPACE }

// Unicode code point order, not String.compareTo's UTF-16 code unit order.
private fun compareCodePoints(left: String, right: String): Int {
    val leftPoints = left.codePoints().toArray()
    val rightPoints = right.codePoints().toArray()
    for (index in 0 until minOf(leftPoints.size, rightPoints.size)) {
        val comparison = leftPoints[index].compareTo(rightPoints[index])
        if (comparison != 0) return comparison
    }
    return leftPoints.size.compareTo(rightPoints.size)
}

private fun lexicographicallyLess(left: List<String>, right: List<String>): Boolean {
    for (index in 0 until minOf(left.size, right.size)) {
        val comparison = compareCodePoints(left[index], right[index])
        if (comparison != 0) return comparison < 0
    }
    return left.size < right.size
}

private fun expectedOrder(steps: List<RawStep>): Expected {
    if (steps.any { isBlank(it.name) }) return Expected.Failure("BlankStepName")

    val names = steps.map { it.name }
    if (names.toSet().size != names.size) return Expected.Failure("DuplicateStep")

    val known = names.toSet()
    val needs = steps.associate { it.name to it.needs.toSet() }
    if (needs.values.any { dependencies -> dependencies.any { it !in known } }) {
        return Expected.Failure("UnknownDependency")
    }
    if (needs.any { (name, dependencies) -> name in dependencies }) {
        return Expected.Failure("SelfDependency")
    }
    require(names.size <= MAX_PERMUTATION_NODES) {
        "expectedOrder permutation cap is $MAX_PERMUTATION_NODES nodes"
    }

    var best: List<String>? = null
    for (candidate in permutations(names)) {
        val positions = candidate.withIndex().associate { it.value to it.index }
        val valid = needs.all { (name, dependencies) ->
            dependencies.all { dependency -> positions.getValue(dependency) < positions.getValue(name) }
        }
        if (valid && (best == null || lexicographicallyLess(candidate, best!!))) best = candidate
    }
    return best?.let { Expected.Success(it) } ?: Expected.Failure("Cycle")
}

private fun case(name: String, steps: List<RawStep>, expected: Expected? = null): Case =
    Case(name, steps, expected ?: expectedOrder(steps))

private fun enumeratedCases(): List<Case> {
    val cases = mutableListOf<Case>()
    val allLabels = listOf("a", "b", "c")
    for (count in 0..3) {
        val labels = allLabels.take(count)
        if (count == 0) {
            cases += case("enum0:", emptyList())
            continue
        }
        for (choice in repeatedProduct(powerSet(labels), count)) {
            val attached = labels.indices.associate { labels[it] to choice[it] }
            for (order in permutations(labels)) {
                val steps = order.map { RawStep(it, attached.getValue(it)) }
                val signature = order.joinToString(",") { name ->
                    "$name:${attached.getValue(name).joinToString("+")}"
                }
                cases += case("enum$count:$signature", steps)
            }
        }
    }
    return cases
}

private fun explicitCases(): List<Case> = listOf(
    case("empty", emptyList()),
    case("unicode-white-space", listOf(RawStep("\u0085\u2007\u202f", emptyList()))),
    case("bom-is-not-white-space", listOf(RawStep("\ufeff", emptyList()))),
    case("separator-is-not-white-space", listOf(RawStep("\u001c", emptyList()))),
    case(
        "code-point-order",
        listOf(
            RawStep("\uff5e", emptyList()),
            RawStep("\ud83d\ude00", emptyList()),
        ),
        Expected.Success(listOf("\uff5e", "\ud83d\ude00")),
    ),
    case(
        "shuffled-chain",
        listOf(
            RawStep("c", listOf("b")),
            RawStep("a", emptyList()),
            RawStep("b", listOf("a")),
        ),
    ),
    case(
        "diamond",
        listOf(
            RawStep("d", listOf("b", "c")),
            RawStep("b", listOf("a")),
            RawStep("c", listOf("a")),
            RawStep("a", emptyList()),
        ),
    ),
    case(
        "disconnected",
        listOf(
            RawStep("z", emptyList()),
            RawStep("a", emptyList()),
            RawStep("m", emptyList()),
        ),
    ),
    case(
        "lex-ready-new-node-priority",
        listOf(
            RawStep("m", emptyList()),
            RawStep("z", emptyList()),
            RawStep("a", listOf("m")),
        ),
    ),
    case(
        "names-preserved-once",
        listOf(
            RawStep("pack", emptyList()),
            RawStep("test", listOf("pack")),
            RawStep("lint", listOf("pack")),
        ),
    ),
    case("blank-empty", listOf(RawStep("", emptyList()))),
    case("blank-spaces", listOf(RawStep("  ", emptyList()))),
    case("blank-tabs", listOf(RawStep("\t\n", emptyList()))),
    case(
        "name-with-padding-kept",
        listOf(
            RawStep(" a", emptyList()),
            RawStep("b", listOf(" a")),
        ),
    ),
    case(
        "duplicate",
        listOf(
            RawStep("a", emptyList()),
            RawStep("a", listOf("b")),
        ),
    ),
    case("unknown", listOf(RawStep("a", listOf("ghost")))),
    case("unknown-empty-dep", listOf(RawStep("a", listOf("")))),
    case("self", listOf(RawStep("a", listOf("a")))),
    case(
        "cycle-2",
        listOf(
            RawStep("a", listOf("b")),
            RawStep("b", listOf("a")),
        ),
    ),
    case(
        "cycle-3",
        listOf(
            RawStep("a", listOf("c")),
            RawStep("b", listOf("a")),
            RawStep("c", listOf("b")),
        ),
    ),
    case(
        "precedence-blank",
        listOf(
            RawStep("  ", listOf("ghost", "  ")),
            RawStep("  ", emptyList()),
            RawStep("x", listOf("y")),
            RawStep("y", listOf("x")),
        ),
    ),
    case(
        "precedence-duplicate",
        listOf(
            RawStep("a", listOf("ghost")),
            RawStep("a", listOf("a")),
            RawStep("b", listOf("c")),
            RawStep("c", listOf("b")),
        ),
    ),
    case(
        "precedence-unknown",
        listOf(
            RawStep("a", listOf("a", "ghost")),
            RawStep("b", listOf("c")),
            RawStep("c", listOf("b")),
        ),
    ),
    case(
        "precedence-self",
        listOf(
            RawStep("a", listOf("a")),
            RawStep("b", listOf("c")),
            RawStep("c", listOf("b")),
        ),
    ),
    case(
        "large-dag",
        listOf(
            RawStep("deploy", listOf("image")),
            RawStep("lint", listOf("compile")),
            RawStep("image", listOf("bundle")),
            RawStep("compile", emptyList()),
            RawStep("bundle", listOf("lint", "test")),
            RawStep("test", listOf("compile")),
        ),
    ),
    case(
        "large-chain",
        listOf(
            RawStep("s5", listOf("s4")),
            RawStep("s1", emptyList()),
            RawStep("s8", listOf("s7")),
            RawStep("s3", listOf("s2")),
            RawStep("s7", listOf("s6")),
            RawStep("s2", listOf("s1")),
            RawStep("s6", listOf("s5")),
            RawStep("s4", listOf("s3")),
        ),
        Expected.Success(listOf("s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8")),
    ),
    case(
        "large-new-ready",
        listOf(
            RawStep("b", emptyList()),
            RawStep("d", emptyList()),
            RawStep("c", listOf("b")),
            RawStep("a", listOf("c")),
        ),
    ),
)

private fun errorName(error: ArtifactPipelineError): String = when (error) {
    ArtifactPipelineError.BlankStepName -> "BlankStepName"
    ArtifactPipelineError.DuplicateStep -> "DuplicateStep"
    ArtifactPipelineError.UnknownDependency -> "UnknownDependency"
    ArtifactPipelineError.SelfDependency -> "SelfDependency"
    ArtifactPipelineError.Cycle -> "Cycle"
}

private fun rawSteps(steps: List<RawStep>): CottList<BuildStep> = CottList(
    steps.map { step -> BuildStep(name = step.name, needs = CottSet(step.needs)) },
)

private fun normalizeOrder(result: CottResult<CottList<String>, ArtifactPipelineError>): Expected =
    when (result) {
        is Ok -> Expected.Success(result.value.toList())
        is Err -> Expected.Failure(errorName(result.error))
    }

private fun normalizePlan(result: CottResult<curriculum.artifact_pipeline.ArtifactPlan, ArtifactPipelineError>): Expected =
    when (result) {
        is Ok -> Expected.Success(result.value.ordered_steps.toList())
        is Err -> Expected.Failure(errorName(result.error))
    }

private fun check(evaluate: (List<RawStep>) -> Expected): Int {
    val cases = enumeratedCases() + explicitCases()
    for (case in cases) {
        val actual = evaluate(case.steps)
        check(actual == case.expected) {
            "${case.name}: expected ${case.expected}, got $actual"
        }
    }
    return cases.size
}

fun main() {
    val orderedCount = check { steps ->
        normalizeOrder(topologically_order_steps(rawSteps(steps)))
    }
    val plannedCount = check { steps ->
        normalizePlan(plan_pipeline(Pipeline(steps = rawSteps(steps))))
    }
    println("{\"topologically_order_steps\":$orderedCount,\"plan_pipeline\":$plannedCount}")
}
