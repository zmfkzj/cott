from cott_runtime import Err, Ok, Result
from curriculum.flashcard_schedule_types import FlashcardScheduleError, FlashcardScheduleError_DateOverflow, FlashcardScheduleError_EaseOutOfRange, FlashcardScheduleError_ZeroEase, Rating_Again, Rating_Good, Rating_Hard, Review, ScheduledCard


def schedule_review(review: Review) -> Result[ScheduledCard, FlashcardScheduleError]:
    if review.ease_permille == 0:
        return Err(error=FlashcardScheduleError_ZeroEase())
    if review.ease_permille < 1300 or review.ease_permille > 3000:
        return Err(error=FlashcardScheduleError_EaseOutOfRange())

    interval_days: int
    ease_permille: int
    if isinstance(review.rating, Rating_Again):
        interval_days = 1
        ease_permille = max(1100, review.ease_permille - 200)
    elif isinstance(review.rating, Rating_Hard):
        interval_days = max(1, review.interval_days * 12 // 10)
        ease_permille = max(1100, review.ease_permille - 150)
    elif isinstance(review.rating, Rating_Good):
        interval_days = max(1, review.interval_days * review.ease_permille // 1000)
        ease_permille = review.ease_permille
    else:
        interval_days = max(1, review.interval_days * review.ease_permille * 13 // 10000)
        ease_permille = min(3150, review.ease_permille + 150)

    if interval_days > 4_294_967_295 - review.due_day:
        return Err(error=FlashcardScheduleError_DateOverflow())

    return Ok(value=ScheduledCard(due_day=review.due_day + interval_days, interval_days=interval_days, ease_permille=ease_permille))
