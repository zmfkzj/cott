# experiment-ranking

## Purpose
Validate experiment-run metrics and rank them deterministically by direction.

## Key points
- Reject an empty list first; validate each run in the order of a blank identifier, non-finite score, and exactly equal duplicate identifier.
- Choose descending or ascending score order, then break ties by ascending run identifier. The first identifier is the best run.
