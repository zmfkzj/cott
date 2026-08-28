from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Empty:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_X:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_O:
    pass

Cell: TypeAlias = Union[Cell_Empty, Cell_X, Cell_O]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Player_X:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Player_O:
    pass

Player: TypeAlias = Union[Player_X, Player_O]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Outcome_InProgress:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Outcome_XWins:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Outcome_OWins:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Outcome_Draw:
    pass

Outcome: TypeAlias = Union[Outcome_InProgress, Outcome_XWins, Outcome_OWins, Outcome_Draw]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MoveResult:
    __hash__ = None
    board: CottList[Cell]
    next_player: Player
    outcome: Outcome

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MoveError_InvalidBoard:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MoveError_InvalidPosition:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MoveError_InvalidTurn:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MoveError_Terminal:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MoveError_Occupied:
    pass

MoveError: TypeAlias = Union[MoveError_InvalidBoard, MoveError_InvalidPosition, MoveError_InvalidTurn, MoveError_Terminal, MoveError_Occupied]

"""Validate the shape, mark counts, and winning lines of a three-by-three
board. InvalidBoard is returned when the board does not have nine cells,
the mark counts are impossible, both players have won, or a winner's mark
count is inconsistent with that player having moved last."""
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
__all__ = ["Cell", "Cell_Empty", "Cell_O", "Cell_X", "MoveError", "MoveError_InvalidBoard", "MoveError_InvalidPosition", "MoveError_InvalidTurn", "MoveError_Occupied", "MoveError_Terminal", "MoveResult", "Outcome", "Outcome_Draw", "Outcome_InProgress", "Outcome_OWins", "Outcome_XWins", "Player", "Player_O", "Player_X"]
