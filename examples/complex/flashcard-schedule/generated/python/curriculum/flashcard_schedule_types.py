from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottExternal, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Rating_Again:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Rating_Hard:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Rating_Good:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Rating_Easy:
    pass

Rating: TypeAlias = Union[Rating_Again, Rating_Hard, Rating_Good, Rating_Easy]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Review:
    __hash__ = None
    due_day: U32
    interval_days: U32
    ease_permille: U16
    rating: Rating

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ScheduledCard:
    __hash__ = None
    due_day: U32
    interval_days: U32
    ease_permille: U16

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FlashcardScheduleError_ZeroEase:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FlashcardScheduleError_EaseOutOfRange:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FlashcardScheduleError_DateOverflow:
    pass

FlashcardScheduleError: TypeAlias = Union[FlashcardScheduleError_ZeroEase, FlashcardScheduleError_EaseOutOfRange, FlashcardScheduleError_DateOverflow]

"""Validates the ease value used by flashcard scheduling. ZeroEase takes
priority over EaseOutOfRange."""
"""Validates review ease, then deterministically schedules the next due day.
Again resets the interval to one day and subtracts 200 ease points; Hard
grows the interval by 1.2 and subtracts 150; Good multiplies by the current
ease; and Easy additionally multiplies by 1.3 and adds 150 ease points.
DateOverflow is returned when adding the computed interval would exceed
the maximum U32 due day."""
__all__ = ["FlashcardScheduleError", "FlashcardScheduleError_DateOverflow", "FlashcardScheduleError_EaseOutOfRange", "FlashcardScheduleError_ZeroEase", "Rating", "Rating_Again", "Rating_Easy", "Rating_Good", "Rating_Hard", "Review", "ScheduledCard"]
