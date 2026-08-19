# split-file

## Purpose
Split a text file's list of lines into contiguous chunks of bounded size.

## Key points
- `SplitRequest` carries the line list and chunk size together, and success represents each output file's lines as a nested list.
- Chunk size is 1–10,000; if more than 10,000 chunks would be generated, it returns `OutputLimitExceeded` to preserve the output budget.
- The Python implementation preserves input order without omitting or duplicating lines, and successfully maps an empty list to an empty chunk list.
