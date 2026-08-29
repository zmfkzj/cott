from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@runtime_checkable
class Summarizable(Protocol):
    _cott_trait = True
    async def summary(self) -> _cott_curriculum_trait_protocol_Summarizable_Summary_91a0038fc149a52d660ec2d4c914e0f201ef340095a79ffc2c9cd89ad6d2311f:
        ...


@runtime_checkable
class Prioritizable(Protocol):
    _cott_trait = True
    async def priority_level(self) -> I32:
        ...


T = TypeVar("T", covariant=True)
@runtime_checkable
class TaskView(Summarizable, Prioritizable, Protocol[T]):
    _cott_trait = True
    async def summary(self) -> _cott_curriculum_trait_protocol_Summarizable_Summary_91a0038fc149a52d660ec2d4c914e0f201ef340095a79ffc2c9cd89ad6d2311f:
        ...

    async def priority_level(self) -> I32:
        ...

    async def display(self) -> T:
        ...

    async def category(self) -> str:
        ...


@runtime_checkable
class Completable(Protocol):
    _cott_trait = True
    async def complete(self) -> bool:
        ...


_cott_curriculum_trait_protocol_Summarizable_curriculum_trait_protocol_Summarizable_Summary = TypeVar("_cott_curriculum_trait_protocol_Summarizable_curriculum_trait_protocol_Summarizable_Summary")
_cott_curriculum_trait_protocol_TaskView_curriculum_trait_protocol_Summarizable_Summary = TypeVar("_cott_curriculum_trait_protocol_TaskView_curriculum_trait_protocol_Summarizable_Summary")
_cott_curriculum_trait_protocol_Summarizable_Summary_91a0038fc149a52d660ec2d4c914e0f201ef340095a79ffc2c9cd89ad6d2311f = TypeVar("_cott_curriculum_trait_protocol_Summarizable_Summary_91a0038fc149a52d660ec2d4c914e0f201ef340095a79ffc2c9cd89ad6d2311f")

@final
class TaskLifecycle_Pending:
    __slots__ = ()
    _instance: TaskLifecycle_Pending | None = None

    def __new__(cls) -> TaskLifecycle_Pending:
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "TaskLifecycle.Pending"
@final
class TaskLifecycle_Completed:
    __slots__ = ()
    _instance: TaskLifecycle_Completed | None = None

    def __new__(cls) -> TaskLifecycle_Completed:
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "TaskLifecycle.Completed"
TaskLifecycle: TypeAlias = Union[TaskLifecycle_Pending, TaskLifecycle_Completed]

__all__ = ["Completable", "Prioritizable", "Summarizable", "TaskLifecycle", "TaskLifecycle_Completed", "TaskLifecycle_Pending", "TaskView"]
