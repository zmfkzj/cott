from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Board4:
    __hash__ = None
    cells: CottList[U16]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Direction_Left:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Direction_Right:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Direction_Up:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Direction_Down:
    pass

Direction: TypeAlias = Union[Direction_Left, Direction_Right, Direction_Up, Direction_Down]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MoveRequest:
    __hash__ = None
    board: Board4
    direction: Direction

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MoveResult:
    __hash__ = None
    board: Board4
    score_gain: U32
    changed: bool

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LineMove:
    __hash__ = None
    cells: CottList[U16]
    score_gain: U32

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Move2048Error_InvalidBoardSize:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Move2048Error_InvalidTile:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Move2048Error_ScoreOverflow:
    pass

Move2048Error: TypeAlias = Union[Move2048Error_InvalidBoardSize, Move2048Error_InvalidTile, Move2048Error_ScoreOverflow]

"""Validate a row-major four-by-four board. InvalidBoardSize takes priority
over InvalidTile. A valid tile is zero or a power of two representable as
U16."""
"""Compact one line toward its first cell and merge equal adjacent nonzero
tiles once. A tile created by a merge cannot merge again in the same line.
Preserve the input length by padding with zeros and report ScoreOverflow
if a merged tile cannot fit U16 or the accumulated score cannot fit U32."""
"""Validate the board once, orient its four rows or columns toward the
requested direction, merge each through merge_move_line, and restore
row-major order. Return the immutable moved board, the checked sum of all
merge scores, and whether any cell changed."""
__all__ = ["Board4", "Direction", "Direction_Down", "Direction_Left", "Direction_Right", "Direction_Up", "LineMove", "Move2048Error", "Move2048Error_InvalidBoardSize", "Move2048Error_InvalidTile", "Move2048Error_ScoreOverflow", "MoveRequest", "MoveResult"]
