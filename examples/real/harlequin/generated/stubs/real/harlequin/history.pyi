from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.history_types import HarlequinPaths as HarlequinPaths, HistoryError as HistoryError, HistoryError_Unavailable as HistoryError_Unavailable, HistoryFilter as HistoryFilter, HistoryFocus as HistoryFocus, HistoryFocus_List as HistoryFocus_List, HistoryFocus_Outcome as HistoryFocus_Outcome, HistoryFocus_Program as HistoryFocus_Program, HistoryFocus_Search as HistoryFocus_Search, HistoryOutcome as HistoryOutcome, HistoryOutcome_Close as HistoryOutcome_Close, HistoryOutcome_Reload as HistoryOutcome_Reload, HistoryOutcome_Select as HistoryOutcome_Select, HistoryOutcome_Stay as HistoryOutcome_Stay, HistoryScreen as HistoryScreen, HistoryStep as HistoryStep, QueryRecord as QueryRecord, QueryStatus as QueryStatus, QueryStatus_Canceled as QueryStatus_Canceled, QueryStatus_Error as QueryStatus_Error, QueryStatus_Ok as QueryStatus_Ok
from real.harlequin.style_types import StyledLine
"""Compute Harlequin's per-user directories exactly as platformdirs does for
appname "harlequin" with appauthor False.
platform "darwin": config_dir home/Library/Application Support/harlequin,
cache_dir home/Library/Caches/harlequin, state_dir and data_dir
home/Library/Application Support/harlequin, log_dir home/Library/Logs/harlequin.
Any other platform (Linux and other Unix): config_dir $XDG_CONFIG_HOME/harlequin
(default home/.config/harlequin), cache_dir $XDG_CACHE_HOME/harlequin (default
home/.cache/harlequin), state_dir $XDG_STATE_HOME/harlequin (default
home/.local/state/harlequin), data_dir $XDG_DATA_HOME/harlequin (default
home/.local/share/harlequin), log_dir state_dir/log. An XDG variable that is
unset or blank uses the default; values are used verbatim otherwise.
query_log is state_dir/history.db, buffer_cache is cache_dir/buffers-1.json and
crash_dir is log_dir."""
def harlequin_paths(platform: str, home: Path, environment: FrozenMap[str, str]) -> HarlequinPaths: ...

"""Append record to the SQLite query log at log_path and return its row id.
The store is created on first use: create missing parent directories with
mode 0700, open with sqlite3 (busy timeout 5000 ms, journal_mode WAL when the
file system allows it, synchronous NORMAL), set file mode 0600 on a new file,
and create the table when absent:
queries(id INTEGER PRIMARY KEY, run_at TEXT NOT NULL, program TEXT NOT NULL,
connection TEXT, profile TEXT, adapter TEXT, sql TEXT NOT NULL, status TEXT
NOT NULL, rows INTEGER, truncated INTEGER, elapsed_ms REAL, error_text TEXT) with
index queries_by_connection on (connection, id DESC), and PRAGMA user_version
1. status is stored as "ok", "error" or "canceled"; truncated as 0/1 or NULL.
The first write in a process also trims the table to its newest 100000 rows.
Any failure to open, create or write is Unavailable(log_path, message) with
the error text; logging never raises."""
def record_query(log_path: Path, record: QueryRecord) -> Result[I64, HistoryError]: ...

"""Fill in the outcome of a logged statement once it is known: set status,
rows, truncated, elapsed_ms (rounded to 3 decimals) and error_text (from failure) of the row
with this id in the log at log_path. A missing row is not an error. Any
failure is Unavailable(log_path, message)."""
def update_query(log_path: Path, row: I64, status: QueryStatus, rows: Option[I64], truncated: Option[bool], elapsed_ms: Option[F64], failure: Option[str]) -> Result[Unit, HistoryError]: ...

"""Read the log at log_path newest first (descending id), keeping rows that
match filter, at most limit rows (all rows for Nothing). The search is a
SQL LIKE '%term%' with "\\\\", "%" and "_" escaped by a backslash (ESCAPE
'\\\\'). A log file that does not exist, or has no queries table, yields an
empty list; reading never creates or migrates the store (open it read-only
with a 250 ms busy timeout). Other failures are Unavailable(log_path,
message). Rows with a status other than ok/error/canceled are skipped."""
def recent_queries(log_path: Path, filter: HistoryFilter, limit: Option[U64]) -> Result[CottList[QueryRecord], HistoryError]: ...

"""The status line Harlequin's history list shows for one record:
the run_at time shifted by timezone_offset_minutes and formatted
"%a, %b %d %H:%M:%S", two spaces, then the outcome. For status other than
Ok the outcome is the upper-case status ("ERROR", "CANCELED"). For Ok it is
"{n} record" / "{n} records" (n formatted with plain decimal digits) when
rows is Some and nonzero, otherwise "SUCCESS", followed by
" in {seconds:.2f}s" when elapsed_ms is Some (seconds = elapsed_ms / 1000).
A run_at that does not parse as ISO-8601 is shown verbatim."""
def history_label(record: QueryRecord, timezone_offset_minutes: I64) -> str: ...

"""The query lines a history row shows: sql stripped and split into lines;
with more than 8 lines, the first 7 followed by "… (N more lines)" where N
is the number of lines not shown."""
def history_preview(sql: str) -> CottList[str]: ...

"""The initial History screen for the active connection: filter with
connection Some(connection), empty search, no program or status; filters
hidden; focus List; everything else 0."""
def open_history_screen(connection: str) -> HistoryScreen: ...

"""Apply one key to the History screen, as Harlequin's history screen reacts.
key is a normalized Textual key name; text is the printable character the key
produced ("" when none). records are the records currently shown.
- "escape": when filters are visible and focus is Search with a nonempty
  search, clear the search (Reload); when filters are visible otherwise,
  hide them and clear search, program and status (Reload); when filters are
  hidden, Close.
- "ctrl+f": toggle filters_visible; showing focuses Search, hiding clears
  search, program and status and focuses List (Reload when anything was
  cleared, else Stay).
- "enter": on List with records, Select(records[selected].sql); on Search,
  focus List; on Program or Outcome, cycle that choice (Program: Nothing ->
  "harlequin" -> "hsql" -> Nothing; Outcome: Nothing -> Ok -> Error ->
  Canceled -> Nothing) and Reload.
- "tab"/"shift+tab" while filters are visible: move focus forward/backward
  through Search, Program, Outcome, List (wrapping).
- On List: "up"/"down" move selected by one, "pageup"/"pagedown" by 10,
  "home"/"end" to the first/last record, clamped; any printable text
  (single character, not a space-only key name) shows filters, focuses
  Search, appends text to the search and Reloads.
- On Search: printable text inserts at search_cursor; "backspace" deletes
  before it, "delete" after it; "left"/"right"/"home"/"end" move the caret;
  every change of the search Reloads.
- Every other key: Stay.
A Reload resets selected and first_row to 0. selected is always clamped to
the records."""
def history_key(screen: HistoryScreen, records: CottList[QueryRecord], key: str, text: str) -> HistoryStep: ...

"""Draw the History screen body into width x height cells.
Line 1: the title "Query History" styled "class:hq.dialog.title" followed by
" — " and the list subtitle "No matching queries", "1 query" or
"{n} queries" styled "class:hq.muted".
When filters are visible, line 2 is: "Search: " then the search text or the
placeholder "Filter by query text" (styled "class:hq.muted" when the search
is empty), then "  Program: " and the program or "Any program", then
"  Outcome: " and the status ("ok", "error", "canceled") or "Any outcome";
the focused filter's value span carries " class:hq.cursor".
Then a list area and a preview area: the list takes the upper part and shows,
for each record from first_row (moved minimally so selected is visible), its
history_label line (styled "class:hq.error" when status is not Ok, else
"class:hq.text") followed by its history_preview lines indented two spaces
(styled "class:hq.muted"), with " class:hq.selection" added to every line of
the selected record; the preview shows up to 8 lines starting with
"Highlighted Query Preview" (styled "class:hq.title") and the selected
record's sql lines. The footer line is "Enter: Select  Ctrl+F: Filter
Esc: Cancel" styled "class:hq.footer". Lines are cut at width cells and at
most height lines are returned. Render only lines of actual content:
do not pad either the record list or the preview with blank rows to fill
height. The terminal widget paints unused space. In particular, an empty
history returns at most title, optional filters, preview heading and footer
regardless of how large height is; computation and allocation must not be
proportional to empty terminal space."""
def render_history(screen: HistoryScreen, records: CottList[QueryRecord], width: U64, height: U64, timezone_offset_minutes: I64) -> CottList[StyledLine]: ...

__all__ = ["HarlequinPaths", "HistoryError", "HistoryError_Unavailable", "HistoryFilter", "HistoryFocus", "HistoryFocus_List", "HistoryFocus_Outcome", "HistoryFocus_Program", "HistoryFocus_Search", "HistoryOutcome", "HistoryOutcome_Close", "HistoryOutcome_Reload", "HistoryOutcome_Select", "HistoryOutcome_Stay", "HistoryScreen", "HistoryStep", "QueryRecord", "QueryStatus", "QueryStatus_Canceled", "QueryStatus_Error", "QueryStatus_Ok", "harlequin_paths", "history_key", "history_label", "history_preview", "open_history_screen", "recent_queries", "record_query", "render_history", "update_query"]
