# textfile-analysis

## Purpose
Compute line, character, word, and special-character statistics for Unicode text in one struct.

## Key points
- `TextAnalysis` returns total lines, characters excluding whitespace, words, unique words, and special characters as separate U64 fields.
- Word extraction uses only maximal contiguous Unicode alphanumeric spans after case folding, unlike the `unique-words` example, which applies NFKC normalization.
- The Python implementation counts only U+000A as a line delimiter and counts only code points that are neither alphanumeric nor whitespace as special characters.
