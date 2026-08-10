from __future__ import annotations

import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
"""Normalize text with Unicode NFKC, full case folding, and NFKC again, then
return its words in source order. A word is a maximal sequence of Unicode
alphanumeric characters or underscores."""
"""Return normalized words that occur exactly once, sorted in ascending
Unicode code-point order."""
__all__ = []
