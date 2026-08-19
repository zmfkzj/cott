from __future__ import annotations

from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.trait_protocol_types import Completable as Completable, Prioritizable as Prioritizable, Summarizable as Summarizable

_cott_format_summary_T = TypeVar("_cott_format_summary_T", bound=Summarizable)
class _cott__cott_inspect_task_T_Bounds(Summarizable, Prioritizable, Protocol):
    pass

_cott_inspect_task_T = TypeVar("_cott_inspect_task_T", bound=_cott__cott_inspect_task_T_Bounds)
"""Format the summary string from any item implementing {Summarizable}."""
def format_summary(item: _cott_format_summary_T) -> str: ...

"""Inspect an item requiring both {Summarizable} and {Prioritizable} trait bounds."""
def inspect_task(item: _cott_inspect_task_T) -> str: ...


@final
class SimpleTask:
    title: str
    urgency: I32
    completed: bool
    def __init__(self, title: str, urgency: I32) -> None: ...
    def summary(self: SimpleTask) -> str: ...
    def priority_level(self: SimpleTask) -> I32: ...
    def complete(self: SimpleTask) -> bool: ...
__all__ = ["Completable", "Prioritizable", "SimpleTask", "Summarizable", "format_summary", "inspect_task"]
