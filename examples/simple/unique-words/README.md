# unique-words

## Purpose
Extract normalized words from Unicode text and find words that occur exactly once.

## Key points
- A word is a maximal contiguous sequence of Unicode alphanumeric characters or underscores, and a list can preserve input order.
- The Python implementation applies NFKC normalization, full case folding, and NFKC normalization again to unify equivalent spellings.
- Unique words select only entries with an occurrence count of exactly 1 and sort them in ascending Unicode code-point order, distinguishing this from simple deduplication.
