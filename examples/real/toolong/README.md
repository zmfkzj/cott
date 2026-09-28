# https://github.com/Textualize/toolong

Clean-room Cott reimplementation of Toolong 1.4.0, the terminal log viewer: `tl [OPTIONS] FILE...`
opens one tab per file (or one timestamp-merged tab with `-m`) in a full-screen viewer with
scrolling, tailing, find, go-to-line, time navigation, a line panel with pretty JSON, a help
screen, gzip/bzip2 files and piped standard input. Upstream's Textual UI is replaced by a
prompt_toolkit 3.0.52 driver; every callable, including that driver, is agent-generated from the
contracts. Python only adapts the process entry point (`python/toolong.py`).

## Run

```bash
project=examples/real/toolong
PYTHONPATH="$project/generated/python:$project/python" \
  "$project/.venv/bin/python" "$project/python/toolong.py" /var/log/syslog app.log.gz
```

Options follow click 8.1.7 exactly as upstream: `--version`, `-m/--merge`,
`-o/--output-merge PATH` (save the merged view, requires `-m`) and `--help`. When standard input is a
pipe, files and options are ignored (as upstream) and the piped bytes are copied to a temporary
file that is viewed, and tailed, while they arrive; keys are read from `/dev/tty`. Keys: arrows, `j`/`k`, Home/End, PageUp/PageDown scroll; Enter selects a line and
toggles the line panel; `ctrl+f` or `/` find (Down/Up jump between matches, case and regex
toggles); `ctrl+g` go to line; `m`/`M`, `h`/`H`, `d`/`D` jump a minute, hour or day forwards /
backwards by timestamp; `ctrl+t` tail; `ctrl+l` line numbers; Tab cycles focus (Left/Right
switch tabs from the tab strip); `f1`
help; Escape cancels a running scan, closes dialogs and the panel; `ctrl+c` quits.

## Contract

`src/real/toolong/` has eleven modules:

- `cli`: click-exact argument parsing and help, upstream's path sort and tab plan, and the
  process entry point.
- `files`: opening (compression detection, whole-file gzip/bzip2 decompression, descriptor
  reads), line-break and timestamp scans, tail polling, find, time navigation and merge saving.
- `index`: single-file backwards-scan indexes, tail breaks, timestamp merging and line lookup.
- `timestamps`: upstream's timestamp scanner table, shifting, comparison and footer formatting.
- `text`: ANSI decoding, the log/JSON highlighters, the format parser, find highlighting and
  matching, pretty JSON, wrapping and find suggestions.
- `keys`, `view`: key decoding, Textual input editing, the pure viewer state machine (actions,
  events, layout, footer keys) and mouse handling.
- `screen`, `help`: theme, text-to-cell rendering and every widget (tabs, log lines, find dialog,
  panel, footer, help, go-to, toasts) composed into a frame.
- `tui`: the prompt_toolkit driver and browser launching.

Two representation choices keep real logs inside the 1024-node ABI traversal limit, which the
runtime also enforces when a struct is constructed. Large or unbounded values (file break
indexes, timestamp batches, merged indexes, frame rows, the rendered help document and the
visible lines passed to the frame composer) cross facades as tagged `Opaque` tuples. Styles are
canonical style-code strings (`StyledSpan.style`, `StyledRun.style`; a cell code is exactly a
prompt_toolkit style string), so a styled line costs four nodes per span.

## Evidence

`cott verify` certifies the current snapshot with `observed=76 trust_declaration=3 unknown=1
unobserved=0` clause observations from 29 scenarios. The remaining trust declarations are the
effectful `run_command_line` and `run_viewer` clauses, which Cott does not execute;
`render_find_dialog`'s row-count clause is unknown because the candidate node limit for `TabView`
is exhausted. `cott requirements` reports the four requirements (`FIND_SEARCHES_RAW_LINES`,
`TIME_NAVIGATION_SKIPS_TO_TARGET`, `ESCAPE_CANCELS_A_RUNNING_SCAN`,
`FIND_NAVIGATION_STARTS_AFTER_THE_POINTER`) as `observed`: bounded scenario evidence, not proof.
Opaque values compare by identity, so scenarios check index contents through `line_location`,
`find_line`, `locate_time` and `save_lines` rather than directly.

The strict coverage policy selects 40 clauses across 25 callables: file opening,
decompression, line/span reads, tailing, saving, index transitions, timestamps,
search and highlighting, and viewer initialization. No unobserved, trust-declaration
or unknown allowance is enabled. The latest Sol regeneration and `verify` passed
all 40 selected clauses, including the previously missing
`real.toolong.files.save_lines:error:2` (`WriteFailed`) failure observation.
The raw-line search scenario also checks that backward searches starting at or
beyond the view's end return no result, including an empty view. The search doc
now agrees with the unchanged formal result bound. Merge-order scenarios and the
four requirements above remain separate evidence, not additional policy selectors.
Static proofs are separate from execution coverage and cannot make a clause observed.
Policy selection and bounded observation do not establish execution of every path.

The viewer itself is exercised outside Cott evidence by driving the real program in a tmux
pseudo-terminal: plain and highlighted logs, find, two tabs, a 300,000-line / 21 MB log (End,
Home, PageDown, go to line 150000, find), the JSON panel, a 43-field-per-line JSON log (rendering
and Home), a merged view and `-o` saving, `.gz` and `.bz2` files, live tailing of an appended
line, piped standard input, the help screen and `ctrl+c`.

## Limits

Densely highlighted lines remain slow: a later measurement parsed a 43-field JSON line in
about 0.46 seconds through the validated facades. The dense-JSON line panel was subsequently
observed at 160×40 after navigating Home and entering the panel; it showed the nested `"k30": 0`
value. That corrects the earlier inconclusive 25-second smoke, not the performance limitation.

Long highlighted lines are a confirmed compatibility gap. A 120×36 run with approximately
410 style spans per line exited after about 5.4 seconds with
`$.spans[170].end exceeds ABI traversal node limit 1024`. The viewer catches this failure and
returns exit status 0, so a zero exit status alone is not successful viewer evidence. The span
representation rewrite is preserved separately but could not be regenerated after the default
OMP provider returned `usage_limit_reached`; it is not installed or certified here.
