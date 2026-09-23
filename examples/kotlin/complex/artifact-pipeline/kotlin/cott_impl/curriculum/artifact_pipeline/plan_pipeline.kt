package cott_impl.curriculum.artifact_pipeline

internal fun plan_pipeline(pipeline: curriculum.artifact_pipeline.Pipeline): cott_runtime.CottResult<curriculum.artifact_pipeline.ArtifactPlan, curriculum.artifact_pipeline.ArtifactPipelineError> {
    return when (val ordered = curriculum.artifact_pipeline.topologically_order_steps(pipeline.steps)) {
        is cott_runtime.Ok -> cott_runtime.Ok(curriculum.artifact_pipeline.ArtifactPlan(ordered.value))
        is cott_runtime.Err -> ordered
    }
}
