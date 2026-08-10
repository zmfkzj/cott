from __future__ import annotations

import dataclasses as _dataclasses
from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.rock_paper_scissors_types import RoundResult, RoundResult_ComputerWins, RoundResult_Tie, RoundResult_UserWins, RpsMove, RpsMove_Paper, RpsMove_Rock, RpsMove_Scissors

def user_beats_computer(user: RpsMove, computer: RpsMove) -> bool:
    """Return whether the user's move defeats the computer's move.

Rock defeats Scissors, Paper defeats Rock, and Scissors defeats Paper.
Ties and losing pairs return false."""
    user = _cott_validate_abi(user, RpsMove, path="$.user")
    computer = _cott_validate_abi(computer, RpsMove, path="$.computer")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/rock_paper_scissors/user_beats_computer.py", "71804aee9bc4a4559bef07231784a12394c4acfc59686d02c9bbce984960b6b8", "user_beats_computer", expected_project_name="rock-paper-scissors", expected_cott_symbol="curriculum.rock_paper_scissors.user_beats_computer")
        _result = _implementation(user, computer)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.rock_paper_scissors.user_beats_computer"
        if _error.span is None:
            _error.span = {"end_byte":414,"end_column":1,"end_line":21,"start_byte":143,"start_column":1,"start_line":13}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.rock_paper_scissors.user_beats_computer", phase="implementation-call", span={"end_byte":414,"end_column":1,"end_line":21,"start_byte":143,"start_column":1,"start_line":13}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.rock_paper_scissors.user_beats_computer", phase="implementation-call", span={"end_byte":414,"end_column":1,"end_line":21,"start_byte":143,"start_column":1,"start_line":13}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, bool, path="$.return")
    return _result

def decide_round(user: RpsMove, computer: RpsMove) -> RoundResult:
    """Classify a supplied pair of moves as a tie, user win, or computer win.

Equal moves produce Tie. Other pairs are classified through
user_beats_computer; the function performs no random selection."""
    user = _cott_validate_abi(user, RpsMove, path="$.user")
    computer = _cott_validate_abi(computer, RpsMove, path="$.computer")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/rock_paper_scissors/decide_round.py", "285bbfc724088af8dda9b70a70fc26229fcca1418b339bc80138eac47fc8aef0", "decide_round", expected_project_name="rock-paper-scissors", expected_cott_symbol="curriculum.rock_paper_scissors.decide_round")
        _result = _implementation(user, computer)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.rock_paper_scissors.decide_round"
        if _error.span is None:
            _error.span = {"end_byte":712,"end_column":1,"end_line":28,"start_byte":414,"start_column":1,"start_line":21}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.rock_paper_scissors.decide_round", phase="implementation-call", span={"end_byte":712,"end_column":1,"end_line":28,"start_byte":414,"start_column":1,"start_line":21}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.rock_paper_scissors.decide_round", phase="implementation-call", span={"end_byte":712,"end_column":1,"end_line":28,"start_byte":414,"start_column":1,"start_line":21}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, RoundResult, path="$.return")
    return _result

__all__ = ["RoundResult", "RoundResult_ComputerWins", "RoundResult_Tie", "RoundResult_UserWins", "RpsMove", "RpsMove_Paper", "RpsMove_Rock", "RpsMove_Scissors", "decide_round", "user_beats_computer"]
