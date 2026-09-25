from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.artifact_pipeline_types import ArtifactPipelineError as ArtifactPipelineError, ArtifactPipelineError_BlankStepName as ArtifactPipelineError_BlankStepName, ArtifactPipelineError_Cycle as ArtifactPipelineError_Cycle, ArtifactPipelineError_DuplicateStep as ArtifactPipelineError_DuplicateStep, ArtifactPipelineError_SelfDependency as ArtifactPipelineError_SelfDependency, ArtifactPipelineError_UnknownDependency as ArtifactPipelineError_UnknownDependency, ArtifactPlan as ArtifactPlan, BuildStep as BuildStep, Pipeline as Pipeline
"""Order build steps so that every step follows the steps named in its needs.
Names and needs are compared exactly, without trimming or normalization. A
blank name is empty or consists only of the 25 Unicode White_Space
characters used by any_blank_by; U+FEFF, U+180E, U+200B and U+001C are not
whitespace for this contract."""
def topologically_order_steps(steps: CottList[BuildStep]) -> Result[CottList[str], ArtifactPipelineError]: ...

"""Plan the pipeline by ordering pipeline.steps through the public
topologically_order_steps facade."""
def plan_pipeline(pipeline: Pipeline) -> Result[ArtifactPlan, ArtifactPipelineError]: ...

__all__ = ["ArtifactPipelineError", "ArtifactPipelineError_BlankStepName", "ArtifactPipelineError_Cycle", "ArtifactPipelineError_DuplicateStep", "ArtifactPipelineError_SelfDependency", "ArtifactPipelineError_UnknownDependency", "ArtifactPlan", "BuildStep", "Pipeline", "plan_pipeline", "topologically_order_steps"]
