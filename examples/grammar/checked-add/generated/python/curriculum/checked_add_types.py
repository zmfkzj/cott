from __future__ import annotations

import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
"""Compute the exact mathematical sum of two signed 32-bit integers as a signed 64-bit integer.
Each input is in the inclusive range -2,147,483,648 through 2,147,483,647, so the result is in the inclusive range -4,294,967,296 through 4,294,967,294 and cannot overflow I64.
The function performs no additional validation, raises no declared errors, and deterministically returns left plus right."""
__all__ = []
