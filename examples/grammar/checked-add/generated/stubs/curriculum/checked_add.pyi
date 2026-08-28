from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit
"""Compute the exact mathematical sum of two signed 32-bit integers as a signed 64-bit integer.
Each input is in the inclusive range -2,147,483,648 through 2,147,483,647, so the result is in the inclusive range -4,294,967,296 through 4,294,967,294 and cannot overflow I64.
The function performs no additional validation, raises no declared errors, and deterministically returns left plus right."""
def checked_add(left: I32, right: I32) -> I64: ...

__all__ = ["checked_add"]
