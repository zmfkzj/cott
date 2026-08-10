from __future__ import annotations

import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PasswordError_InvalidLength:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PasswordError_InsufficientDraws:
    pass

PasswordError: TypeAlias = Union[PasswordError_InvalidLength, PasswordError_InsufficientDraws]

"""For a length n from 1 through 128 inclusive, returns
2n + floor(n / 2) - 1, the exact number of draws generate_password
consumes. Every other length returns InvalidLength."""
"""Validates length before inspecting draws, so a length outside 1 through 128
returns InvalidLength even when draws are insufficient. For a valid length
n, exactly 2n + floor(n / 2) - 1 draws are required; a shorter list returns
InsufficientDraws without indexing it, and later draws are ignored.

The password contains floor(n / 2) letters, ceil(3n / 10) digits, and
n minus those two counts special characters. Draws are consumed as two per
letter, then one per digit, then one per special character, followed by
n - 1 shuffle draws. For each letter, the first draw's least nonnegative
remainder modulo 26 selects from "abcdefghijklmnopqrstuvwxyz"; the second
draw's remainder modulo 2 chooses lowercase for 0 or uppercase for 1.
Digit draws select from "0123456789" modulo 10, and special-character draws
select from "@#$%&*" modulo 6.

Letters, digits, and special characters are first concatenated in that
order. Fisher-Yates then visits indices i from n - 1 down through 1 and
swaps each with the index selected by the next draw's least nonnegative
remainder modulo i + 1. Success returns the resulting n-character string."""
__all__ = ["PasswordError", "PasswordError_InsufficientDraws", "PasswordError_InvalidLength"]
