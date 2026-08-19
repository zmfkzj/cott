# case-ranking

## Purpose
Rank matching cases using the set intersection of query terms and case terms.

## Key points
- Reject an empty query first, then validate blank query terms; for cases in input order, validate blank IDs, duplicate IDs, and blank terms.
- Exclude cases with zero distinct intersecting terms; sort the rest by descending overlap count, descending citation count, and ascending case ID.
