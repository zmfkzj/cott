from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottExternal, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi

@runtime_checkable
class Summarizable(Protocol):
    def summary(self) -> str:
        ...


@runtime_checkable
class Prioritizable(Protocol):
    def priority_level(self) -> I32:
        ...


@runtime_checkable
class Completable(Protocol):
    def complete(self) -> bool:
        ...


"""Format the summary string from any item implementing {Summarizable}."""
"""Inspect an item requiring both {Summarizable} and {Prioritizable} trait bounds."""
class _cott__cott_inspect_task_T_Bounds(Summarizable, Prioritizable, Protocol):
    pass

__all__ = ["Completable", "Prioritizable", "Summarizable"]
