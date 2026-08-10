from __future__ import annotations

import dataclasses as _dataclasses
from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.tic_tac_toe_types import Cell, Cell_Empty, Cell_O, Cell_X, MoveError, MoveError_InvalidBoard, MoveError_InvalidPosition, MoveError_InvalidTurn, MoveError_Occupied, MoveError_Terminal, MoveResult, Outcome, Outcome_Draw, Outcome_InProgress, Outcome_OWins, Outcome_XWins, Player, Player_O, Player_X

def validate_board_state(board: CottList[Cell]) -> Result[Unit, MoveError]:
    """Validate the shape, mark counts, and winning lines of a three-by-three
board. InvalidBoard is returned when the board does not have nine cells,
the mark counts are impossible, both players have won, or a winner's mark
count is inconsistent with that player having moved last."""
    board = _cott_validate_abi(board, CottList[Cell], path="$.board")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len(board) != 9)):
        _expected_error = MoveError_InvalidBoard
        _expected_error_span = {"end_byte":769,"end_column":53,"end_line":38,"start_byte":721,"start_column":5,"start_line":38}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/tic_tac_toe/validate_board_state.py", "a94c69cdbf7762ca8a665fa3bfb9455783753837839abf990880013c1310f0e7", "validate_board_state", expected_project_name="tic-tac-toe", expected_cott_symbol="curriculum.tic_tac_toe.validate_board_state")
        _result = _implementation(board)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.tic_tac_toe.validate_board_state"
        if _error.span is None:
            _error.span = {"end_byte":804,"end_column":1,"end_line":41,"start_byte":333,"start_column":1,"start_line":30}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.tic_tac_toe.validate_board_state", phase="implementation-call", span={"end_byte":804,"end_column":1,"end_line":41,"start_byte":333,"start_column":1,"start_line":30}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.tic_tac_toe.validate_board_state", phase="implementation-call", span={"end_byte":804,"end_column":1,"end_line":41,"start_byte":333,"start_column":1,"start_line":30}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, MoveError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.tic_tac_toe.validate_board_state", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MoveError_InvalidBoard,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.tic_tac_toe.validate_board_state", phase="error", span={"end_byte":804,"end_column":1,"end_line":41,"start_byte":333,"start_column":1,"start_line":30}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.tic_tac_toe.validate_board_state", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    return _result

def apply_tic_tac_toe_move(board: CottList[Cell], player: Player, position: I64) -> Result[MoveResult, MoveError]:
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
    board = _cott_validate_abi(board, CottList[Cell], path="$.board")
    player = _cott_validate_abi(player, Player, path="$.player")
    position = _cott_validate_abi(position, I64, path="$.position")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len(board) != 9)):
        _expected_error = MoveError_InvalidBoard
        _expected_error_span = {"end_byte":1794,"end_column":53,"end_line":62,"start_byte":1746,"start_column":5,"start_line":62}
        _expected_error_clause = "error:2"
    if _expected_error is None and (((position < 0) or (position > 8))):
        _expected_error = MoveError_InvalidPosition
        _expected_error_span = {"end_byte":1864,"end_column":70,"end_line":63,"start_byte":1799,"start_column":5,"start_line":63}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/tic_tac_toe/apply_tic_tac_toe_move.py", "9cfdb8e7e010594918de9f8f99f03ae6a64a7da7e9ed5c088289c07e97c5a90e", "apply_tic_tac_toe_move", expected_project_name="tic-tac-toe", expected_cott_symbol="curriculum.tic_tac_toe.apply_tic_tac_toe_move")
        _result = _implementation(board, player, position)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.tic_tac_toe.apply_tic_tac_toe_move"
        if _error.span is None:
            _error.span = {"end_byte":1988,"end_column":1,"end_line":68,"start_byte":804,"start_column":1,"start_line":41}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.tic_tac_toe.apply_tic_tac_toe_move", phase="implementation-call", span={"end_byte":1988,"end_column":1,"end_line":68,"start_byte":804,"start_column":1,"start_line":41}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.tic_tac_toe.apply_tic_tac_toe_move", phase="implementation-call", span={"end_byte":1988,"end_column":1,"end_line":68,"start_byte":804,"start_column":1,"start_line":41}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[MoveResult, MoveError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.tic_tac_toe.apply_tic_tac_toe_move", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MoveError_InvalidBoard, MoveError_InvalidTurn, MoveError_Terminal, MoveError_Occupied,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.tic_tac_toe.apply_tic_tac_toe_move", phase="error", span={"end_byte":1988,"end_column":1,"end_line":68,"start_byte":804,"start_column":1,"start_line":41}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.tic_tac_toe.apply_tic_tac_toe_move", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        moved = _result.value
        if not ((len((moved).board) == 9)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.tic_tac_toe.apply_tic_tac_toe_move", clause="ensures:1", phase="ensures", span={"end_byte":1740,"end_column":53,"end_line":60,"start_byte":1692,"start_column":5,"start_line":60}, expected="true", actual="false")
    return _result

__all__ = ["Cell", "Cell_Empty", "Cell_O", "Cell_X", "MoveError", "MoveError_InvalidBoard", "MoveError_InvalidPosition", "MoveError_InvalidTurn", "MoveError_Occupied", "MoveError_Terminal", "MoveResult", "Outcome", "Outcome_Draw", "Outcome_InProgress", "Outcome_OWins", "Outcome_XWins", "Player", "Player_O", "Player_X", "apply_tic_tac_toe_move", "validate_board_state"]
