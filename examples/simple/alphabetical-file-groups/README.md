# alphabetical-file-groups

## Purpose
Choose a folder from the first Unicode code point of each filename, then compose classifications in input order.

## Key points
- `classify_filename` formally preserves the filename and requires `EmptyFilename` exactly when it is empty; the folder rule in its doc uses the leading letter's full Unicode case fold or `misc` for a non-letter.
- `group_filenames` declares one move per input on success, first-error propagation, and order/multiplicity preservation. Its list-wide error condition and per-element ordering are observed with scenarios rather than expressible in a clause.
- Scenarios observe ASCII, `ß`→`ss`, `İ`→`i̇`, non-letter, empty filename, duplicate ordered moves, and an early error. Both linked requirements are observed in this verified snapshot, not proved; the full Unicode mapping and actual internal call order are not exhaustively checked.
