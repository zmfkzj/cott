from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.move_2048_types import Board4, Direction, Direction_Down, Direction_Left, Direction_Right, Direction_Up, LineMove, Move2048Error, Move2048Error_InvalidBoardSize, Move2048Error_InvalidTile, Move2048Error_ScoreOverflow, MoveRequest, MoveResult

def validate_2048_board(board: Board4) -> Result[Unit, Move2048Error]:
    """Validate a row-major four-by-four board. InvalidBoardSize takes priority
over InvalidTile. A valid tile is zero or a power of two representable as
U16."""
    board = _cott_validate_abi(board, Board4, path="$.board")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len((board).cells) != 16)):
        _expected_error = Move2048Error_InvalidBoardSize
        _expected_error_span = {"end_byte":715,"end_column":68,"end_line":37,"start_byte":652,"start_column":5,"start_line":37}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/move_2048/validate_2048_board.py", "7d34d09fb3e3c9e72920645be3a9d68a58f6de3bf3978d728878d137eb5b6f8d", "validate_2048_board", expected_project_name="move-2048", expected_cott_symbol="curriculum.move_2048.validate_2048_board")
        _result = _implementation(board)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.move_2048.validate_2048_board"
        if _error.span is None:
            _error.span = {"end_byte":769,"end_column":1,"end_line":42,"start_byte":393,"start_column":1,"start_line":30}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.move_2048.validate_2048_board", phase="implementation-call", span={"end_byte":769,"end_column":1,"end_line":42,"start_byte":393,"start_column":1,"start_line":30}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.move_2048.validate_2048_board", phase="implementation-call", span={"end_byte":769,"end_column":1,"end_line":42,"start_byte":393,"start_column":1,"start_line":30}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, Move2048Error], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.move_2048.validate_2048_board", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (Move2048Error_InvalidTile,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.move_2048.validate_2048_board", phase="error", span={"end_byte":769,"end_column":1,"end_line":42,"start_byte":393,"start_column":1,"start_line":30}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.move_2048.validate_2048_board", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    return _result

def merge_move_line(line: CottList[U16]) -> Result[LineMove, Move2048Error]:
    """Compact one line toward its first cell and merge equal adjacent nonzero
tiles once. A tile created by a merge cannot merge again in the same line.
Preserve the input length by padding with zeros and report ScoreOverflow
if a merged tile cannot fit U16 or the accumulated score cannot fit U32."""
    line = _cott_validate_abi(line, CottList[U16], path="$.line")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/move_2048/merge_move_line.py", "1c35faf382905800ba82f6ea9fcdcec987cc870c485999058a6b3b794bfd885c", "merge_move_line", expected_project_name="move-2048", expected_cott_symbol="curriculum.move_2048.merge_move_line")
        _result = _implementation(line)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.move_2048.merge_move_line"
        if _error.span is None:
            _error.span = {"end_byte":1287,"end_column":1,"end_line":56,"start_byte":769,"start_column":1,"start_line":42}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.move_2048.merge_move_line", phase="implementation-call", span={"end_byte":1287,"end_column":1,"end_line":56,"start_byte":769,"start_column":1,"start_line":42}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.move_2048.merge_move_line", phase="implementation-call", span={"end_byte":1287,"end_column":1,"end_line":56,"start_byte":769,"start_column":1,"start_line":42}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[LineMove, Move2048Error], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.move_2048.merge_move_line", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (Move2048Error_ScoreOverflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.move_2048.merge_move_line", phase="error", span={"end_byte":1287,"end_column":1,"end_line":56,"start_byte":769,"start_column":1,"start_line":42}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.move_2048.merge_move_line", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            moved = _cott_match_value.value
            return ((len((moved).cells) == len(line)))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.move_2048.merge_move_line", clause="ensures:1", phase="ensures", span={"end_byte":1230,"end_column":60,"end_line":50,"start_byte":1175,"start_column":5,"start_line":50}, expected="true", actual="false")
    return _result

def apply_2048_move(request: MoveRequest) -> Result[MoveResult, Move2048Error]:
    """Validate the board once, orient its four rows or columns toward the
requested direction, merge each through merge_move_line, and restore
row-major order. Return the immutable moved board, the checked sum of all
merge scores, and whether any cell changed."""
    request = _cott_validate_abi(request, MoveRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len(((request).board).cells) != 16)):
        _expected_error = Move2048Error_InvalidBoardSize
        _expected_error_span = {"end_byte":1794,"end_column":76,"end_line":66,"start_byte":1723,"start_column":5,"start_line":66}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/move_2048/apply_2048_move.py", "a6fe8b62e63e02905fac5aa279e5112c8f0d7659b99da536b0257abd88864d7c", "apply_2048_move", expected_project_name="move-2048", expected_cott_symbol="curriculum.move_2048.apply_2048_move")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.move_2048.apply_2048_move"
        if _error.span is None:
            _error.span = {"end_byte":1885,"end_column":1,"end_line":71,"start_byte":1287,"start_column":1,"start_line":56}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.move_2048.apply_2048_move", phase="implementation-call", span={"end_byte":1885,"end_column":1,"end_line":71,"start_byte":1287,"start_column":1,"start_line":56}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.move_2048.apply_2048_move", phase="implementation-call", span={"end_byte":1885,"end_column":1,"end_line":71,"start_byte":1287,"start_column":1,"start_line":56}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[MoveResult, Move2048Error], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.move_2048.apply_2048_move", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (Move2048Error_InvalidTile, Move2048Error_ScoreOverflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.move_2048.apply_2048_move", phase="error", span={"end_byte":1885,"end_column":1,"end_line":71,"start_byte":1287,"start_column":1,"start_line":56}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.move_2048.apply_2048_move", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            moved = _cott_match_value.value
            return ((len(((moved).board).cells) == 16))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.move_2048.apply_2048_move", clause="ensures:1", phase="ensures", span={"end_byte":1717,"end_column":60,"end_line":64,"start_byte":1662,"start_column":5,"start_line":64}, expected="true", actual="false")
    return _result

__all__ = ["Board4", "Direction", "Direction_Down", "Direction_Left", "Direction_Right", "Direction_Up", "LineMove", "Move2048Error", "Move2048Error_InvalidBoardSize", "Move2048Error_InvalidTile", "Move2048Error_ScoreOverflow", "MoveRequest", "MoveResult", "apply_2048_move", "merge_move_line", "validate_2048_board"]
