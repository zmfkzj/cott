from __future__ import annotations

from cott_runtime import CottTuple2, I32

def make_coordinate_pair(x: I32, y: I32) -> CottTuple2[I32, I32]:
    return CottTuple2(first=x, second=y)
