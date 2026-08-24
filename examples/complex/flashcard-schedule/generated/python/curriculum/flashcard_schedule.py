from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.flashcard_schedule_types import FlashcardScheduleError, FlashcardScheduleError_DateOverflow, FlashcardScheduleError_EaseOutOfRange, FlashcardScheduleError_ZeroEase, Rating, Rating_Again, Rating_Easy, Rating_Good, Rating_Hard, Review, ScheduledCard

def validate_review_ease(review: Review) -> Result[Unit, FlashcardScheduleError]:
    """Validates the ease value used by flashcard scheduling. ZeroEase takes
priority over EaseOutOfRange."""
    review = _cott_validate_abi(review, Review, path="$.review")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (((review).ease_permille == 0)):
        _expected_error = FlashcardScheduleError_ZeroEase
        _expected_error_span = {"end_byte":634,"end_column":73,"end_line":31,"start_byte":566,"start_column":5,"start_line":31}
        _expected_error_clause = "error:1"
    if _expected_error is None and ((((review).ease_permille != 0) and (((review).ease_permille < 1300) or ((review).ease_permille > 3000)))):
        _expected_error = FlashcardScheduleError_EaseOutOfRange
        _expected_error_span = {"end_byte":780,"end_column":146,"end_line":32,"start_byte":639,"start_column":5,"start_line":32}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/flashcard_schedule/validate_review_ease.py", "abeb236d26d9432ed434a4e02790e489567a993d5153ba8e557d5ad32b2df84f", "validate_review_ease", expected_project_name="flashcard-schedule", expected_cott_symbol="curriculum.flashcard_schedule.validate_review_ease")
        _result = _implementation(review)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.flashcard_schedule.validate_review_ease"
        if _error.span is None:
            _error.span = {"end_byte":798,"end_column":1,"end_line":36,"start_byte":352,"start_column":1,"start_line":25}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.flashcard_schedule.validate_review_ease", phase="implementation-call", span={"end_byte":798,"end_column":1,"end_line":36,"start_byte":352,"start_column":1,"start_line":25}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.flashcard_schedule.validate_review_ease", phase="implementation-call", span={"end_byte":798,"end_column":1,"end_line":36,"start_byte":352,"start_column":1,"start_line":25}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, FlashcardScheduleError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.flashcard_schedule.validate_review_ease", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.flashcard_schedule.validate_review_ease", phase="error", span={"end_byte":798,"end_column":1,"end_line":36,"start_byte":352,"start_column":1,"start_line":25}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.flashcard_schedule.validate_review_ease", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    return _result

def schedule_review(review: Review) -> Result[ScheduledCard, FlashcardScheduleError]:
    """Validates review ease, then deterministically schedules the next due day.
Again resets the interval to one day and subtracts 200 ease points; Hard
grows the interval by 1.2 and subtracts 150; Good multiplies by the current
ease; and Easy additionally multiplies by 1.3 and adds 150 ease points.
DateOverflow is returned when adding the computed interval would exceed
the maximum U32 due day."""
    review = _cott_validate_abi(review, Review, path="$.review")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (((review).ease_permille == 0)):
        _expected_error = FlashcardScheduleError_ZeroEase
        _expected_error_span = {"end_byte":1598,"end_column":73,"end_line":50,"start_byte":1530,"start_column":5,"start_line":50}
        _expected_error_clause = "error:4"
    if _expected_error is None and ((((review).ease_permille != 0) and (((review).ease_permille < 1300) or ((review).ease_permille > 3000)))):
        _expected_error = FlashcardScheduleError_EaseOutOfRange
        _expected_error_span = {"end_byte":1744,"end_column":146,"end_line":51,"start_byte":1603,"start_column":5,"start_line":51}
        _expected_error_clause = "error:5"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/flashcard_schedule/schedule_review.py", "06298552b32cb14e48672bd2c5ef88e7b3e0a58adaa08af9395055e419213695", "schedule_review", expected_project_name="flashcard-schedule", expected_cott_symbol="curriculum.flashcard_schedule.schedule_review")
        _result = _implementation(review)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.flashcard_schedule.schedule_review"
        if _error.span is None:
            _error.span = {"end_byte":1807,"end_column":1,"end_line":55,"start_byte":798,"start_column":1,"start_line":36}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.flashcard_schedule.schedule_review", phase="implementation-call", span={"end_byte":1807,"end_column":1,"end_line":55,"start_byte":798,"start_column":1,"start_line":36}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.flashcard_schedule.schedule_review", phase="implementation-call", span={"end_byte":1807,"end_column":1,"end_line":55,"start_byte":798,"start_column":1,"start_line":36}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ScheduledCard, FlashcardScheduleError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.flashcard_schedule.schedule_review", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (FlashcardScheduleError_DateOverflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.flashcard_schedule.schedule_review", phase="error", span={"end_byte":1807,"end_column":1,"end_line":55,"start_byte":798,"start_column":1,"start_line":36}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.flashcard_schedule.schedule_review", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        card = _result.value
        if not (((card).interval_days >= 1)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.flashcard_schedule.schedule_review", clause="ensures:1", phase="ensures", span={"end_byte":1374,"end_column":55,"end_line":46,"start_byte":1324,"start_column":5,"start_line":46}, expected="true", actual="false")
    if type(_result) is Ok and True:
        card = _result.value
        if not (((card).due_day > (review).due_day)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.flashcard_schedule.schedule_review", clause="ensures:2", phase="ensures", span={"end_byte":1435,"end_column":61,"end_line":47,"start_byte":1379,"start_column":5,"start_line":47}, expected="true", actual="false")
    if type(_result) is Ok and True:
        card = _result.value
        if not ((((card).ease_permille >= 1100) and ((card).ease_permille <= 3150))):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.flashcard_schedule.schedule_review", clause="ensures:3", phase="ensures", span={"end_byte":1524,"end_column":89,"end_line":48,"start_byte":1440,"start_column":5,"start_line":48}, expected="true", actual="false")
    return _result

__all__ = ["FlashcardScheduleError", "FlashcardScheduleError_DateOverflow", "FlashcardScheduleError_EaseOutOfRange", "FlashcardScheduleError_ZeroEase", "Rating", "Rating_Again", "Rating_Easy", "Rating_Good", "Rating_Hard", "Review", "ScheduledCard", "schedule_review", "validate_review_ease"]
