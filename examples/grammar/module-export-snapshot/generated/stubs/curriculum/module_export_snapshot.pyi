from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.module_export_snapshot_types import ModuleSnapshot as ModuleSnapshot
"""Construct a module snapshot without transforming or cross-assigning either
input. `exported_x` is assigned to `exported_x`, and `module_x` is assigned
independently to `module_x`. The construction is deterministic and accepts
every I64 value, including both bounds and equal input values."""
def build_snapshot(exported_x: I64, module_x: I64) -> ModuleSnapshot: ...

__all__ = ["ModuleSnapshot", "build_snapshot"]
