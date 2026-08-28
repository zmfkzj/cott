from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.tic_tac_toe_types import Cell as Cell, Cell_Empty as Cell_Empty, Cell_O as Cell_O, Cell_X as Cell_X, MoveError as MoveError, MoveError_InvalidBoard as MoveError_InvalidBoard, MoveError_InvalidPosition as MoveError_InvalidPosition, MoveError_InvalidTurn as MoveError_InvalidTurn, MoveError_Occupied as MoveError_Occupied, MoveError_Terminal as MoveError_Terminal, MoveResult as MoveResult, Outcome as Outcome, Outcome_Draw as Outcome_Draw, Outcome_InProgress as Outcome_InProgress, Outcome_OWins as Outcome_OWins, Outcome_XWins as Outcome_XWins, Player as Player, Player_O as Player_O, Player_X as Player_X
"""Validate the shape, mark counts, and winning lines of a three-by-three
board. InvalidBoard is returned when the board does not have nine cells,
the mark counts are impossible, both players have won, or a winner's mark
count is inconsistent with that player having moved last."""
def validate_board_state(board: CottList[Cell]) -> Result[Unit, MoveError]: ...

"""Apply one move to a row-major three-by-three board. InvalidBoard for a
non-nine-cell board precedes InvalidPosition for a position outside 0
through 8. validate_board_state then rejects inconsistent counts or wins;
InvalidTurn, Terminal, and Occupied follow in that order.

X moves first. Before X moves the X and O counts are equal; before O moves
there is exactly one more X. Winning lines are (0,1,2), (3,4,5), (6,7,8),
(0,3,6), (1,4,7), (2,5,8), (0,4,8), and (2,4,6). A new win yields XWins
or OWins, a full board without a winner yields Draw, and every other move
yields InProgress. The returned board is a new immutable list, and
next_player is the other player even after a win or draw."""
def apply_tic_tac_toe_move(board: CottList[Cell], player: Player, position: I64) -> Result[MoveResult, MoveError]: ...

__all__ = ["Cell", "Cell_Empty", "Cell_O", "Cell_X", "MoveError", "MoveError_InvalidBoard", "MoveError_InvalidPosition", "MoveError_InvalidTurn", "MoveError_Occupied", "MoveError_Terminal", "MoveResult", "Outcome", "Outcome_Draw", "Outcome_InProgress", "Outcome_OWins", "Outcome_XWins", "Player", "Player_O", "Player_X", "apply_tic_tac_toe_move", "validate_board_state"]
