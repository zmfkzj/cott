from cott_runtime import Err, Ok, Result, UNIT, Unit
from curriculum.flashcard_schedule_types import FlashcardScheduleError, FlashcardScheduleError_EaseOutOfRange, FlashcardScheduleError_ZeroEase, Review


def validate_review_ease(review: Review) -> Result[Unit, FlashcardScheduleError]:
    if review.ease_permille == 0:
        return Err(error=FlashcardScheduleError_ZeroEase())
    if review.ease_permille < 1300 or review.ease_permille > 3000:
        return Err(error=FlashcardScheduleError_EaseOutOfRange())
    return Ok(value=UNIT)
