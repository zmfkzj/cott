# https://github.com/Textualize/toolong

Clean-room Cott reimplementation of Toolong's log reading and filtering as a one-shot command:
`[--contains TEXT] PATH...` prints the matching lines of one or more log files. Toolong's Textual
viewer, tailing, merging by timestamp, JSON log formatting and compressed files are not
reimplemented. Python only adapts console I/O (`python/toolong.py`).

## Run

```bash
project=examples/real/toolong
PYTHONPATH="$project/generated/python:$project/python" \
  "$project/.venv/bin/python" "$project/python/toolong.py" --contains error /path/to/app.log
```

Each kept line prints as `path:line text`, numbered from one per file. `--contains` is recognized
only as the first argument and matches after mapping ASCII `A`-`Z` to `a`-`z` (no Unicode case
folding). Errors print to stderr with exit status 2.

## Contract

`src/real/toolong.cott` specifies:

- `parse_arguments`: the exact option grammar; an empty argument list is a formal
  `InvalidArguments` condition and the source count is tied to the argument count.
- `parse_log`: a pure stage that splits file text at LF only, drops one trailing CR per line and
  numbers entries from one (`LogEntry.line > 0` is a type invariant).
- `load_entries`: reads each source as strict UTF-8 and concatenates `parse_log` per source;
  the first unreadable source is `ReadFailed` with that path.
- `filter_entries`: the exact ASCII case mapping, order and multiplicity; no filter or an empty
  filter returns the entries unchanged (formal clauses).
- `render_entries`: the exact line format.
- `execute`: the composition root `parse_arguments` → `load_entries` → `filter_entries` →
  `render_entries`, with parse and load errors returned unchanged. Requirements state this
  composition and the per-source loading order.

## Evidence

`cott verify` certifies the current snapshot with `observed=17 trust_declaration=0 unknown=0
unobserved=0` clause observations. The five scenarios cover the argument grammar, LF-only
splitting (CR alone and VT do not split), ASCII-only filtering (an accented filter keeps
nothing), exact rendering, loading two fixture files, the first undecodable or missing file, and
the composed `execute` output and errors, including an empty argument list. The file scenarios
use the compiler-owned filesystem fixture, so they observe the implementation's fixture-adapter
branch and the composition. The production branch that reads host files is not observed by Cott
evidence.

`cott requirements` reports all three requirements (`EXECUTE_RENDERS_FILTERED_LOADED_ENTRIES`,
`EXECUTE_RETURNS_STAGE_ERRORS_UNCHANGED`, `LOAD_PARSES_EACH_SOURCE_IN_ORDER`) as `observed` for
the current snapshot: bounded scenario evidence, not proof.
