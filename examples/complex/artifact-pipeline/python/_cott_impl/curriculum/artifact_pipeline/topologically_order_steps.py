from heapq import heappop, heappush
from typing import Final

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

_WHITE_SPACE: Final[str] = "\u0009\u000a\u000b\u000c\u000d\u0020\u0085\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000"


def _is_blank(name: str) -> bool:
    for ch in name:
        if ch not in _WHITE_SPACE:
            return False
    return True


def topologically_order_steps(steps: CottList[BuildStep]) -> Result[CottList[str], ArtifactPipelineError]:
    for step in steps:
        if _is_blank(step.name):
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
        for dependency in step.needs:
            if dependency == step.name:
                return Err(error=ArtifactPipelineError_SelfDependency())

    remaining: dict[str, int] = {}
    dependents: dict[str, list[str]] = {name: [] for name in names}
    for step in steps:
        count = 0
        for dependency in step.needs:
            dependents[dependency].append(step.name)
            count += 1
        remaining[step.name] = count

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

    if len(ordered) != len(names):
        return Err(error=ArtifactPipelineError_Cycle())
    return Ok(value=CottList(values=ordered))
