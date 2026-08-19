# flashcard-schedule

## Purpose
Determine the next review date, interval, and difficulty from a review rating and difficulty.

## Key points
- Reject difficulty 0 first; otherwise, validate the 1300–3000‰ range. Again resets to 1 day, while Hard, Good, and Easy apply their respective integer-ratio interval calculations.
- Again and Hard lower difficulty to no less than 1100‰; Easy adds 150‰ but caps it at 3150‰. A next-date `U32` overflow is `DateOverflow`.
