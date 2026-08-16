from __future__ import annotations

from typing import TypeVar
from cott_runtime import CottTuple2

A = TypeVar("A")
B = TypeVar("B")

def swap_pair(pair: CottTuple2[A, B]) -> CottTuple2[B, A]:
    return CottTuple2(first=pair.second, second=pair.first)
