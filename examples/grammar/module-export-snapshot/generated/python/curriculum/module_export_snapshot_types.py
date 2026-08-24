from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottExternal, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ModuleSnapshot:
    __hash__ = None
    exported_x: I64
    module_x: I64

"""Construct a module snapshot without transforming or cross-assigning either
input. `exported_x` is assigned to `exported_x`, and `module_x` is assigned
independently to `module_x`. The construction is deterministic and accepts
every I64 value, including both bounds and equal input values."""
__all__ = ["ModuleSnapshot"]
