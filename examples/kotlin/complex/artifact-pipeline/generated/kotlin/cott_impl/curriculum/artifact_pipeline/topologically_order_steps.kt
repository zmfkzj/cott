package cott_impl.curriculum.artifact_pipeline

internal fun topologically_order_steps(steps: cott_runtime.CottList<curriculum.artifact_pipeline.BuildStep>): cott_runtime.CottResult<cott_runtime.CottList<kotlin.String>, curriculum.artifact_pipeline.ArtifactPipelineError> {
    for (step in steps) {
        if (step.name.isBlank()) {
            return cott_runtime.Err(curriculum.artifact_pipeline.ArtifactPipelineError.BlankStepName)
        }
    }

    val indices = HashMap<String, Int>(steps.size)
    for ((index, step) in steps.withIndex()) {
        if (indices.put(step.name, index) != null) {
            return cott_runtime.Err(curriculum.artifact_pipeline.ArtifactPipelineError.DuplicateStep)
        }
    }

    var hasSelfDependency = false
    for (step in steps) {
        for (dependency in step.needs) {
            if (!indices.containsKey(dependency)) {
                return cott_runtime.Err(curriculum.artifact_pipeline.ArtifactPipelineError.UnknownDependency)
            }
            if (dependency == step.name) {
                hasSelfDependency = true
            }
        }
    }
    if (hasSelfDependency) {
        return cott_runtime.Err(curriculum.artifact_pipeline.ArtifactPipelineError.SelfDependency)
    }

    val remainingDependencies = IntArray(steps.size)
    val dependents = Array(steps.size) { ArrayList<Int>() }
    val ready = java.util.PriorityQueue<Int>(Comparator { left, right ->
        steps[left].name.compareTo(steps[right].name)
    })
    for ((index, step) in steps.withIndex()) {
        remainingDependencies[index] = step.needs.size
        if (step.needs.isEmpty()) {
            ready.add(index)
        }
        for (dependency in step.needs) {
            dependents[indices.getValue(dependency)].add(index)
        }
    }

    val ordered = ArrayList<String>(steps.size)
    while (ready.isNotEmpty()) {
        val index = ready.remove()
        ordered.add(steps[index].name)
        for (dependent in dependents[index]) {
            remainingDependencies[dependent]--
            if (remainingDependencies[dependent] == 0) {
                ready.add(dependent)
            }
        }
    }
    if (ordered.size != steps.size) {
        return cott_runtime.Err(curriculum.artifact_pipeline.ArtifactPipelineError.Cycle)
    }
    return cott_runtime.Ok(cott_runtime.CottList(ordered))
}
