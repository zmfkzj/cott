from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.toolong.tui_types import Fragment as Fragment, ViewerFailure as ViewerFailure, ViewerFailure_Terminal as ViewerFailure_Terminal
from real.toolong.model_types import ScreenRow, StyledRun, ViewerSetup
"""Convert the runs of one bounded ScreenRow to prompt_toolkit formatted
text, in order. Each run becomes Fragment(run style, run text): a run's
cell code (see real.toolong.model.StyledRun) already is a prompt_toolkit
style string. This function does not insert a newline. The viewer slices
each row's runs into groups of at most 256 before calling this facade so
no call traverses a full dense terminal frame."""
def frame_fragments(row: ScreenRow) -> CottList[Fragment]: ...

"""Open url in the user's web browser like webbrowser.open (the webbrowser
module is not importable here): start "open" on macOS (sys.platform ==
"darwin") and "xdg-open" elsewhere with url as its only argument, with
subprocess.Popen, standard input, output and error on os.devnull and
start_new_session=True, without waiting. The result is true when the
process started and false when starting it raised OSError."""
def open_link(url: str) -> bool: ...

"""Toolong's interactive viewer (upstream's Textual UI app), driven by a
prompt_toolkit 3.0.52 full-screen Application built by composition only:
no subclasses; every callback is a lambda calling a top-level private
helper; the mutable driver state lives in a local dict.

Application: Application(layout=Layout(Window(FormattedTextControl(text,
focusable=True, get_cursor_position=cursor), always_hide_cursor=hidden)),
key_bindings=bindings, full_screen=True, mouse_support=True,
refresh_interval=0.05), with app.ttimeoutlen and app.timeoutlen set to
0.05. bindings has a single binding for Keys.Any whose handler passes every
key press of event.key_sequence, as TerminalInput.KeyPress(name, data)
(name is the Keys member's value, or the key itself when it is a
character), through real.toolong.keys.decode_key to
real.toolong.view.handle_key. text unwraps the frame's opaque tuple of
ScreenRow values, then for each row calls real.toolong.tui.frame_fragments
on groups of at most 256 of its StyledRun values, inserting
Fragment("", LF) between rows, and returns (style, text, mouse handler)
tuples; the mouse handler maps a prompt_toolkit MouseEvent with event type
MOUSE_UP to MouseKind.Click, SCROLL_UP to WheelUp and SCROLL_DOWN to
WheelDown at its position (the control fills the screen, so positions are
screen cells) and passes it to real.toolong.view.handle_mouse with the
current footer meta, returning None; other mouse events return
NotImplemented. cursor returns Point(x, y) of the frame's cursor or None;
hidden is a Condition that is true while the frame has no cursor. A
before_render handler (app.before_render += lambda) runs, on every
render: a size check (app.output.get_size(): columns and rows; a change
applies ViewerEvent.Resize), one bounded work step (below), Tick with the
milliseconds elapsed since start (time.monotonic), and the frame
composition. The viewer starts as real.toolong.view.initial_viewer(setup.tabs,
columns, rows) of the output size. app.run() runs the loop.
Creating or running the application failing because there is no usable
terminal returns ViewerFailure.Terminal with str() of the exception.

Per file keep a format order (real.toolong.text.default_line_formats())
and a timestamp order (real.toolong.timestamps.default_timestamp_order()).
Open every file of every tab with real.toolong.files.open_source before
the loop. For a single-file tab a failure applies ViewerEvent.OpenFailed
with "File NAME not found." for NotFound and "Failed to open NAME;
MESSAGE" for OpenFailed, where NAME is the Python repr of the file name.
For a merged tab every failure (either kind) applies Notify("", "Failed to
open NAME; MESSAGE", Error) and the file is treated as not opened; then
Loaded(tab) is applied.

Every update returned by real.toolong.view.handle_key, handle_mouse or
apply_event replaces the viewer, and its requests are carried out in
order: Bell calls app.output.bell(); Quit calls app.exit(); FindNext(tab,
start, direction) runs real.toolong.files.find_line with the tab's
sources, index, line_count and FindQuery(find value, regex,
case_sensitive) and applies Found; Navigate runs
real.toolong.files.locate_time from the request (threading the timestamp
orders) and applies Jumped; CancelScan stops the tab's scan (below);
OpenLink calls real.toolong.tui.open_link; Suggest(tab, value) applies
Suggestion(value, s) where s is target.start + the indexed word for
target.word.lower() when real.toolong.text.completion_target(value) is
Some(target) and that word is indexed, and "" otherwise.

Work step (at most about 50 ms of work per render, the active tab first):
Scanning. A single file of size 0 completes at once (Complete with count
0). Otherwise its index starts as real.toolong.index.start_file_index(size)
and is scanned backwards in chunks of 8 MiB from the end with
real.toolong.files.scan_breaks; before adding a chunk apply Progress(tab,
"Scanning… (NK lines)- ESCAPE to cancel", 1 - position / size) where N is
(breaks known so far) // 1000 with thousands separators; then
add_scanned_breaks(index, found, position), where position becomes the
lowest LF offset found so far (size while none was found), and apply
Breaks(tab, number of breaks). After the chunk at offset 0,
complete_file_scan(index, size, 0) and apply Complete(tab, number of
breaks). A merged tab scans each opened file in order with
real.toolong.files.scan_timestamps in batches of 10000 lines (threading
the file's timestamp order), applying Progress(tab, "Merging NAME -
ESCAPE to cancel" with the plain file name, (sizes of earlier files +
batch position) / total size) after each batch; when every file is done
it builds real.toolong.index.merge_timestamps(files, true) (not-opened
files as FileTimestamps(false, 0, Opaque("timestamp_entries", ())))
and applies Complete(tab, number of merged lines); then, when
setup.save_merge is Some(path), it saves with real.toolong.files.save_lines
and applies Notify("", "Saved merged log files to PATH", Information) or
Notify("", "Failed to save PATH; MESSAGE", Error), PATH being the Python
repr of str(path). CancelScan stops a
running scan: a single file completes with complete_file_scan(index, size,
position) and Complete; a merge uses merge_timestamps(what was scanned,
false) and Complete, without saving.
Tailing. After its scan completed, each opened single-file tab is polled
from position source.size onwards with real.toolong.files.poll_source, up
to 16 chunks per step while data arrives; each chunk with data updates the
index with add_tail_breaks(index, breaks, chunk position) and applies
Tailed(tab, breaks before, breaks after). Content that shrinks or is
replaced is not noticed (as upstream).
Piped input. While setup.pipe is Some and not exhausted, move the bytes
available on its descriptor (select.select with zero timeout, os.read of
up to 65536 bytes, at most 16 reads per step) to the end of the file at its
path; end of input closes the descriptor and stops.

Large indexes cross generated facades only through tagged opaque handles.
Each handle unwraps to an immutable tuple: "file_breaks" holds U64 offsets;
"timestamp_entries" holds TimestampEntry records; "merged_lines" holds
MergedLine records; "merged_breaks" holds per-file offset tuples. Use
.unwrap() for counts and offsets, and accumulate timestamp batches in
driver-owned lists until building FileTimestamps(entries:
Opaque("timestamp_entries", tuple)). Do not pass a full index or scan
batch through a recursively traversed List facade.

Frame composition: for the active tab, the visible lines scroll_y + r for r
below the text height of real.toolong.view.viewer_layout and below
line_count are located with real.toolong.index.line_location, read with
real.toolong.files.read_lines, parsed with real.toolong.text.parse_line
(threading the file's format order; parsed lines cached by tab, file and
span) and cut with abbreviate_text(text, 1000). Newly parsed lines feed the
find-suggestion index: for each real.toolong.text.search_words entry, when
the prefix is already a key (a use that marks it recent), store word under
prefix.lower() if the stored word is shorter than word; otherwise store
word under prefix.lower(); the index keeps the 10000 most recently used
keys. Apply Widths(tab, widest cell width of the new lines) when it grows.
The footer meta for line pointer (or scroll_y) is: the file name of that
line's file for a merged tab, the timestamp from
real.toolong.files.line_timestamp (threading the timestamp orders)
formatted with real.toolong.timestamps.format_local_timestamp when found,
and the decimal line + 1, joined with " • ". When the panel is shown and
the pointer is set, the panel content is the pointer line parsed as above:
real.toolong.text.pretty_json of its ParsedLine line split at LF when it is
JSON, otherwise real.toolong.text.wrap_text(abbreviate_text(text, 100000),
panel width - 6); apply PanelSize(tab, content rows, widest row) when it
changes. The frame is real.toolong.screen.compose_screen(viewer, content)
with the lines, panel and meta just computed, lines and panel passed as
the opaque "styled_lines" tuples described on FrameContent (never as
List values: a screenful of highlighted lines exceeds the ABI traversal
limit).

End: after app.run() returns, and also when anything raises, close every
opened source and return Ok (upstream swallows UI exceptions).

The file must pass BasedPyright strict checking: keep the driver state in
a dict[str, object] (or typed locals) and read every value back with
typing.cast to its concrete generated type; never annotate anything as Any
and never leave a value of unknown type.
Type callback variables before lambda assignment, e.g.
key_handler: Callable[[KeyPressEvent], None] = lambda event: _on_keys(state, event)
and render_handler: Callable[[Application[None]], None] = lambda app: _on_render(state),
then register the variables; casting the lambda itself leaves its parameters
unknown under BasedPyright strict. Do not import unused symbols (in
particular ByteSpan), and do not repeat isinstance checks after a variant
has already been narrowed by earlier branches."""
def run_viewer(setup: ViewerSetup) -> Result[Unit, ViewerFailure]: ...

__all__ = ["Fragment", "ViewerFailure", "ViewerFailure_Terminal", "frame_fragments", "open_link", "run_viewer"]
