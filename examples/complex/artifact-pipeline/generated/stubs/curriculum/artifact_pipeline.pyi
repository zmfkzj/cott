from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.artifact_pipeline_types import ArtifactPipelineError as ArtifactPipelineError, ArtifactPipelineError_BlankStepName as ArtifactPipelineError_BlankStepName, ArtifactPipelineError_Cycle as ArtifactPipelineError_Cycle, ArtifactPipelineError_DuplicateStep as ArtifactPipelineError_DuplicateStep, ArtifactPipelineError_SelfDependency as ArtifactPipelineError_SelfDependency, ArtifactPipelineError_UnknownDependency as ArtifactPipelineError_UnknownDependency, ArtifactPlan as ArtifactPlan, BuildStep as BuildStep, Pipeline as Pipeline
"""Validate build-step names and dependencies, then return their deterministic
topological order. Blank and duplicate names are rejected before dependency
errors. Ready steps are ordered lexicographically."""
def topologically_order_steps(steps: CottList[BuildStep]) -> Result[CottList[str], ArtifactPipelineError]: ...

"""Order and validate the pipeline's build steps with topologically_order_steps
and construct an artifact plan, propagating any ordering error unchanged."""
def plan_pipeline(pipeline: Pipeline) -> Result[ArtifactPlan, ArtifactPipelineError]: ...

__all__ = ["ArtifactPipelineError", "ArtifactPipelineError_BlankStepName", "ArtifactPipelineError_Cycle", "ArtifactPipelineError_DuplicateStep", "ArtifactPipelineError_SelfDependency", "ArtifactPipelineError_UnknownDependency", "ArtifactPlan", "BuildStep", "Pipeline", "plan_pipeline", "topologically_order_steps"]
