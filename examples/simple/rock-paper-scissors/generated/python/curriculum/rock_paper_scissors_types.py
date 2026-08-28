from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RpsMove_Rock:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RpsMove_Paper:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RpsMove_Scissors:
    pass

RpsMove: TypeAlias = Union[RpsMove_Rock, RpsMove_Paper, RpsMove_Scissors]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RoundResult_UserWins:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RoundResult_ComputerWins:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RoundResult_Tie:
    pass

RoundResult: TypeAlias = Union[RoundResult_UserWins, RoundResult_ComputerWins, RoundResult_Tie]

"""Return whether the user's move defeats the computer's move.

Rock defeats Scissors, Paper defeats Rock, and Scissors defeats Paper.
Ties and losing pairs return false."""
"""Classify a supplied pair of moves as a tie, user win, or computer win.

Equal moves produce Tie. Other pairs are classified through
user_beats_computer; the function performs no random selection."""
__all__ = ["RoundResult", "RoundResult_ComputerWins", "RoundResult_Tie", "RoundResult_UserWins", "RpsMove", "RpsMove_Paper", "RpsMove_Rock", "RpsMove_Scissors"]
