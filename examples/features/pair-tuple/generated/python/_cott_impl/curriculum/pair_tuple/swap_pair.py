from __future__ import annotations

from typing import TypeVar


A = TypeVar("A")
B = TypeVar("B")

def swap_pair(pair: tuple[A, B]) -> tuple[B, A]:
    return (pair[1], pair[0])
