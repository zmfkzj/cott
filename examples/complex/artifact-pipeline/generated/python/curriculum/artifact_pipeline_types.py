from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BuildStep:
    __hash__ = None
    name: str
    needs: CottSet[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "needs", _cott_validate_abi(self.needs, CottSet[str], path="$.needs"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Pipeline:
    __hash__ = None
    steps: CottList[BuildStep]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "steps", _cott_validate_abi(self.steps, CottList[BuildStep], path="$.steps"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactPlan:
    __hash__ = None
    ordered_steps: CottList[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "ordered_steps", _cott_validate_abi(self.ordered_steps, CottList[str], path="$.ordered_steps"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactPipelineError_BlankStepName:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactPipelineError_DuplicateStep:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactPipelineError_UnknownDependency:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactPipelineError_SelfDependency:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactPipelineError_Cycle:
    pass

ArtifactPipelineError: TypeAlias = Union[ArtifactPipelineError_BlankStepName, ArtifactPipelineError_DuplicateStep, ArtifactPipelineError_UnknownDependency, ArtifactPipelineError_SelfDependency, ArtifactPipelineError_Cycle]

"""Validate build-step names and dependencies, then return their deterministic
topological order. Blank and duplicate names are rejected before dependency
errors. Ready steps are ordered lexicographically."""
"""Order and validate the pipeline's build steps with topologically_order_steps
and construct an artifact plan, propagating any ordering error unchanged."""
__all__ = ["ArtifactPipelineError", "ArtifactPipelineError_BlankStepName", "ArtifactPipelineError_Cycle", "ArtifactPipelineError_DuplicateStep", "ArtifactPipelineError_SelfDependency", "ArtifactPipelineError_UnknownDependency", "ArtifactPlan", "BuildStep", "Pipeline"]
