from cott_runtime import Err, Ok, Result
from curriculum.artifact_pipeline import topologically_order_steps
from curriculum.artifact_pipeline_types import ArtifactPipelineError, ArtifactPlan, Pipeline


def plan_pipeline(pipeline: Pipeline) -> Result[ArtifactPlan, ArtifactPipelineError]:
    ordered_steps = topologically_order_steps(pipeline.steps)
    if isinstance(ordered_steps, Err):
        return ordered_steps
    return Ok(value=ArtifactPlan(ordered_steps=ordered_steps.value))
