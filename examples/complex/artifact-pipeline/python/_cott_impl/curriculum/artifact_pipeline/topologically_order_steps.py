from heapq import heappop, heappush

from cott_runtime import CottList, Err, Ok, Result
from curriculum.artifact_pipeline_types import (
    ArtifactPipelineError,
    ArtifactPipelineError_BlankStepName,
    ArtifactPipelineError_Cycle,
    ArtifactPipelineError_DuplicateStep,
    ArtifactPipelineError_SelfDependency,
    ArtifactPipelineError_UnknownDependency,
    BuildStep,
)


def topologically_order_steps(steps: CottList[BuildStep]) -> Result[CottList[str], ArtifactPipelineError]:
    for step in steps:
        if not step.name.strip():
            return Err(error=ArtifactPipelineError_BlankStepName())

    by_name: dict[str, BuildStep] = {}
    for step in steps:
        if step.name in by_name:
            return Err(error=ArtifactPipelineError_DuplicateStep())
        by_name[step.name] = step

    for step in steps:
        for dependency in step.needs:
            if dependency not in by_name:
                return Err(error=ArtifactPipelineError_UnknownDependency())

    for step in steps:
        if step.name in step.needs:
            return Err(error=ArtifactPipelineError_SelfDependency())

    remaining: dict[str, int] = {}
    dependents: dict[str, list[str]] = {name: [] for name in by_name}
    for step in steps:
        for dependency in step.needs:
            dependents[dependency].append(step.name)
        remaining[step.name] = len(step.needs)

    ready: list[str] = []
    for name, count in remaining.items():
        if count == 0:
            heappush(ready, name)

    ordered: list[str] = []
    while ready:
        name = heappop(ready)
        ordered.append(name)
        for dependent in dependents[name]:
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                heappush(ready, dependent)

    if len(ordered) != len(steps):
        return Err(error=ArtifactPipelineError_Cycle())
    return Ok(value=CottList(values=ordered))
