from cott_runtime import CottList, Err, Ok, Result
from curriculum.artifact_pipeline_types import ArtifactPipelineError, ArtifactPipelineError_BlankStepName, ArtifactPipelineError_Cycle, ArtifactPipelineError_DuplicateStep, ArtifactPipelineError_SelfDependency, ArtifactPipelineError_UnknownDependency, BuildStep


def topologically_order_steps(steps: CottList[BuildStep]) -> Result[CottList[str], ArtifactPipelineError]:
    names: set[str] = set()
    for step in steps:
        if step.name == "":
            return Err(error=ArtifactPipelineError_BlankStepName())
        if step.name in names:
            return Err(error=ArtifactPipelineError_DuplicateStep())
        names.add(step.name)

    dependents: dict[str, list[str]] = {name: [] for name in names}
    remaining_dependencies: dict[str, int] = {}
    for step in steps:
        remaining_dependencies[step.name] = len(step.needs)
        for dependency in step.needs:
            if dependency not in names:
                return Err(error=ArtifactPipelineError_UnknownDependency())
            if dependency == step.name:
                return Err(error=ArtifactPipelineError_SelfDependency())
            dependents[dependency].append(step.name)

    ready: list[str] = sorted((name for name in names if remaining_dependencies[name] == 0), reverse=True)
    ordered_steps: list[str] = []
    while ready:
        step_name = ready.pop()
        ordered_steps.append(step_name)
        for dependent in dependents[step_name]:
            remaining_dependencies[dependent] -= 1
            if remaining_dependencies[dependent] == 0:
                ready.append(dependent)
        ready.sort(reverse=True)

    if len(ordered_steps) != len(steps):
        return Err(error=ArtifactPipelineError_Cycle())
    return Ok(value=CottList(values=ordered_steps))
