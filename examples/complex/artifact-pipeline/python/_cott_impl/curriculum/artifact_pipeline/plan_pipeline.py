from cott_runtime import CottList, Err, Ok, Result
from curriculum.artifact_pipeline import topologically_order_steps
from curriculum.artifact_pipeline_types import ArtifactPipelineError, ArtifactPlan, Pipeline


def plan_pipeline(pipeline: Pipeline) -> Result[ArtifactPlan, ArtifactPipelineError]:
    ordering: Result[CottList[str], ArtifactPipelineError] = topologically_order_steps(pipeline.steps)
    if isinstance(ordering, Err):
        return Err(error=ordering.error)
    return Ok(value=ArtifactPlan(ordered_steps=ordering.value))
