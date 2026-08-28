from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.rock_paper_scissors_types import RoundResult as RoundResult, RoundResult_ComputerWins as RoundResult_ComputerWins, RoundResult_Tie as RoundResult_Tie, RoundResult_UserWins as RoundResult_UserWins, RpsMove as RpsMove, RpsMove_Paper as RpsMove_Paper, RpsMove_Rock as RpsMove_Rock, RpsMove_Scissors as RpsMove_Scissors
"""Return whether the user's move defeats the computer's move.

Rock defeats Scissors, Paper defeats Rock, and Scissors defeats Paper.
Ties and losing pairs return false."""
def user_beats_computer(user: RpsMove, computer: RpsMove) -> bool: ...

"""Classify a supplied pair of moves as a tie, user win, or computer win.

Equal moves produce Tie. Other pairs are classified through
user_beats_computer; the function performs no random selection."""
def decide_round(user: RpsMove, computer: RpsMove) -> RoundResult: ...

__all__ = ["RoundResult", "RoundResult_ComputerWins", "RoundResult_Tie", "RoundResult_UserWins", "RpsMove", "RpsMove_Paper", "RpsMove_Rock", "RpsMove_Scissors", "decide_round", "user_beats_computer"]
