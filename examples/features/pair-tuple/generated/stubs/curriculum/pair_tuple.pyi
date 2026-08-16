from __future__ import annotations

from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

A = TypeVar("A")
B = TypeVar("B")
"""Create a pair tuple representing 2D integer coordinates."""
def make_coordinate_pair(x: I32, y: I32) -> CottTuple2[I32, I32]: ...

"""Swap the elements of a generic pair tuple."""
def swap_pair(pair: CottTuple2[A, B]) -> CottTuple2[B, A]: ...

__all__ = ["make_coordinate_pair", "swap_pair"]
