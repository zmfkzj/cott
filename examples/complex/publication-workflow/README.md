# publication-workflow

## Purpose
Determine valid workflow transitions from publication status and requested action.

## Key points
- The transition table permits only draft submission → under review, under-review approval → published, and published withdrawal → withdrawn; the target function returns `Nothing` for impossible combinations.
- If the current status is under review, the request is approval, and editor approval is absent, return `ApprovalRequired`; otherwise, invalid transitions are `InvalidTransition`. A successful transition always differs from the current status.
