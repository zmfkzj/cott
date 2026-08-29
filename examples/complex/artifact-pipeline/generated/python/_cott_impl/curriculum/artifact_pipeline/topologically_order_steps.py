from heapq import heapify, heappop, heappush

from cott_runtime import CottList, Err, Ok, Result
from curriculum.artifact_pipeline_types import ArtifactPipelineError, ArtifactPipelineError_BlankStepName, ArtifactPipelineError_Cycle, ArtifactPipelineError_DuplicateStep, ArtifactPipelineError_SelfDependency, ArtifactPipelineError_UnknownDependency, BuildStep


def topologically_order_steps(steps: CottList[BuildStep]) -> Result[CottList[str], ArtifactPipelineError]:
    for step in steps:
        if step.name.strip() == "":
            return Err(error=ArtifactPipelineError_BlankStepName())

    names: set[str] = set()
    for step in steps:
        if step.name in names:
            return Err(error=ArtifactPipelineError_DuplicateStep())
        names.add(step.name)

    for step in steps:
        for dependency in step.needs:
            if dependency not in names:
                return Err(error=ArtifactPipelineError_UnknownDependency())

    for step in steps:
        if step.name in step.needs:
            return Err(error=ArtifactPipelineError_SelfDependency())

    indegree: dict[str, int] = {}
    dependents: dict[str, list[str]] = {}
    for step in steps:
        indegree[step.name] = len(step.needs)
        dependents[step.name] = []
    for step in steps:
        for dependency in step.needs:
            dependents[dependency].append(step.name)

    ready: list[str] = [name for name in names if indegree[name] == 0]
    heapify(ready)
    ordered_steps: list[str] = []
    while ready:
        name = heappop(ready)
        ordered_steps.append(name)
        for dependent in dependents[name]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heappush(ready, dependent)

    if len(ordered_steps) != len(steps):
        return Err(error=ArtifactPipelineError_Cycle())
    return Ok(value=CottList(values=ordered_steps))
