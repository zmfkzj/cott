from __future__ import annotations

from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.move_2048_types import Board4 as Board4, Direction as Direction, Direction_Down as Direction_Down, Direction_Left as Direction_Left, Direction_Right as Direction_Right, Direction_Up as Direction_Up, LineMove as LineMove, Move2048Error as Move2048Error, Move2048Error_InvalidBoardSize as Move2048Error_InvalidBoardSize, Move2048Error_InvalidTile as Move2048Error_InvalidTile, Move2048Error_ScoreOverflow as Move2048Error_ScoreOverflow, MoveRequest as MoveRequest, MoveResult as MoveResult
"""Validate a row-major four-by-four board. InvalidBoardSize takes priority
over InvalidTile. A valid tile is zero or a power of two representable as
U16."""
def validate_2048_board(board: Board4) -> Result[Unit, Move2048Error]: ...

"""Compact one line toward its first cell and merge equal adjacent nonzero
tiles once. A tile created by a merge cannot merge again in the same line.
Preserve the input length by padding with zeros and report ScoreOverflow
if a merged tile cannot fit U16 or the accumulated score cannot fit U32."""
def merge_move_line(line: CottList[U16]) -> Result[LineMove, Move2048Error]: ...

"""Validate the board once, orient its four rows or columns toward the
requested direction, merge each through merge_move_line, and restore
row-major order. Return the immutable moved board, the checked sum of all
merge scores, and whether any cell changed."""
def apply_2048_move(request: MoveRequest) -> Result[MoveResult, Move2048Error]: ...

__all__ = ["Board4", "Direction", "Direction_Down", "Direction_Left", "Direction_Right", "Direction_Up", "LineMove", "Move2048Error", "Move2048Error_InvalidBoardSize", "Move2048Error_InvalidTile", "Move2048Error_ScoreOverflow", "MoveRequest", "MoveResult", "apply_2048_move", "merge_move_line", "validate_2048_board"]
