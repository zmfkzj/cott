from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

A = TypeVar("A")
B = TypeVar("B")
"""Create a pair tuple representing 2D integer coordinates."""
def make_coordinate_pair(x: I32, y: I32) -> tuple[I32, I32]: ...

"""Swap the elements of a generic pair tuple."""
def swap_pair(pair: tuple[A, B]) -> tuple[B, A]: ...

__all__ = ["make_coordinate_pair", "swap_pair"]
