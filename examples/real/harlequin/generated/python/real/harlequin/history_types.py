from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.harlequin.style_types import StyledLine

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QueryStatus_Ok:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QueryStatus_Error:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QueryStatus_Canceled:
    pass

QueryStatus: TypeAlias = Union[QueryStatus_Ok, QueryStatus_Error, QueryStatus_Canceled]

"""One statement in the shared query log that Harlequin and hsql both write.
run_at is the UTC start time in ISO-8601 with microseconds and "+00:00"
(datetime.now(timezone.utc).isoformat()); program is "harlequin" or "hsql";
connection is the connection id the session is keyed by; profile and adapter
name how it connected; sql is the redacted statement text; rows is the number
of rows fetched (Nothing for DDL/DML or when never counted); truncated is
whether a hard limit stopped the fetch; elapsed_ms is the fetch time in
milliseconds rounded to 3 decimals; error_text is the redacted error text."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QueryRecord:
    __hash__ = None
    run_at: str
    program: str
    connection: str
    profile: Option[str]
    adapter: str
    sql: str
    status: QueryStatus
    rows: Option[I64]
    truncated: Option[bool]
    elapsed_ms: Option[F64]
    error_text: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "run_at", _cott_validate_abi(self.run_at, str, path="$.run_at"))
        if not _cott_validated_construction():
            object.__setattr__(self, "program", _cott_validate_abi(self.program, str, path="$.program"))
        if not _cott_validated_construction():
            object.__setattr__(self, "connection", _cott_validate_abi(self.connection, str, path="$.connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "profile", _cott_validate_abi(self.profile, Option[str], path="$.profile"))
        if not _cott_validated_construction():
            object.__setattr__(self, "adapter", _cott_validate_abi(self.adapter, str, path="$.adapter"))
        if not _cott_validated_construction():
            object.__setattr__(self, "sql", _cott_validate_abi(self.sql, str, path="$.sql"))
        if not _cott_validated_construction():
            object.__setattr__(self, "status", _cott_validate_abi(self.status, QueryStatus, path="$.status"))
        if not _cott_validated_construction():
            object.__setattr__(self, "rows", _cott_validate_abi(self.rows, Option[I64], path="$.rows"))
        if not _cott_validated_construction():
            object.__setattr__(self, "truncated", _cott_validate_abi(self.truncated, Option[bool], path="$.truncated"))
        if not _cott_validated_construction():
            object.__setattr__(self, "elapsed_ms", _cott_validate_abi(self.elapsed_ms, Option[F64], path="$.elapsed_ms"))
        if not _cott_validated_construction():
            object.__setattr__(self, "error_text", _cott_validate_abi(self.error_text, Option[str], path="$.error_text"))

"""A filter over the query log. Every present criterion must hold: connection
equality, sql containing search as a literal substring (case-insensitive, as
SQLite LIKE), program equality and status equality. An empty search matches
everything."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HistoryFilter:
    __hash__ = None
    connection: Option[str]
    search: str
    program: Option[str]
    status: Option[QueryStatus]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "connection", _cott_validate_abi(self.connection, Option[str], path="$.connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "search", _cott_validate_abi(self.search, str, path="$.search"))
        if not _cott_validated_construction():
            object.__setattr__(self, "program", _cott_validate_abi(self.program, Option[str], path="$.program"))
        if not _cott_validated_construction():
            object.__setattr__(self, "status", _cott_validate_abi(self.status, Option[QueryStatus], path="$.status"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HistoryError_Unavailable:
    __hash__ = None
    path: Path
    message: str

HistoryError: TypeAlias = Union[HistoryError_Unavailable]

"""The directories Harlequin keeps per-user state in, as platformdirs computes
them for appname "harlequin" (appauthor False)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HarlequinPaths:
    __hash__ = None
    config_dir: Path
    cache_dir: Path
    state_dir: Path
    log_dir: Path
    data_dir: Path
    query_log: Path
    buffer_cache: Path
    crash_dir: Path

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "config_dir", _cott_validate_abi(self.config_dir, Path, path="$.config_dir"))
        if not _cott_validated_construction():
            object.__setattr__(self, "cache_dir", _cott_validate_abi(self.cache_dir, Path, path="$.cache_dir"))
        if not _cott_validated_construction():
            object.__setattr__(self, "state_dir", _cott_validate_abi(self.state_dir, Path, path="$.state_dir"))
        if not _cott_validated_construction():
            object.__setattr__(self, "log_dir", _cott_validate_abi(self.log_dir, Path, path="$.log_dir"))
        if not _cott_validated_construction():
            object.__setattr__(self, "data_dir", _cott_validate_abi(self.data_dir, Path, path="$.data_dir"))
        if not _cott_validated_construction():
            object.__setattr__(self, "query_log", _cott_validate_abi(self.query_log, Path, path="$.query_log"))
        if not _cott_validated_construction():
            object.__setattr__(self, "buffer_cache", _cott_validate_abi(self.buffer_cache, Path, path="$.buffer_cache"))
        if not _cott_validated_construction():
            object.__setattr__(self, "crash_dir", _cott_validate_abi(self.crash_dir, Path, path="$.crash_dir"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HistoryFocus_List:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HistoryFocus_Search:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HistoryFocus_Program:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HistoryFocus_Outcome:
    pass

HistoryFocus: TypeAlias = Union[HistoryFocus_List, HistoryFocus_Search, HistoryFocus_Program, HistoryFocus_Outcome]

"""The Query History screen (F8). selected is an index into the records currently
shown; first_row is the scroll position; search_cursor is the caret position
in the search text. The records themselves are passed alongside this state."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HistoryScreen:
    __hash__ = None
    filter: HistoryFilter
    filters_visible: bool
    focus: HistoryFocus
    search_cursor: U64
    selected: U64
    first_row: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "filter", _cott_validate_abi(self.filter, HistoryFilter, path="$.filter"))
        if not _cott_validated_construction():
            object.__setattr__(self, "filters_visible", _cott_validate_abi(self.filters_visible, bool, path="$.filters_visible"))
        if not _cott_validated_construction():
            object.__setattr__(self, "focus", _cott_validate_abi(self.focus, HistoryFocus, path="$.focus"))
        if not _cott_validated_construction():
            object.__setattr__(self, "search_cursor", _cott_validate_abi(self.search_cursor, U64, path="$.search_cursor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "selected", _cott_validate_abi(self.selected, U64, path="$.selected"))
        if not _cott_validated_construction():
            object.__setattr__(self, "first_row", _cott_validate_abi(self.first_row, U64, path="$.first_row"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HistoryOutcome_Stay:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HistoryOutcome_Close:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HistoryOutcome_Reload:
    __hash__ = None
    filter: HistoryFilter

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HistoryOutcome_Select:
    __hash__ = None
    sql: str

HistoryOutcome: TypeAlias = Union[HistoryOutcome_Stay, HistoryOutcome_Close, HistoryOutcome_Reload, HistoryOutcome_Select]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HistoryStep:
    __hash__ = None
    screen: HistoryScreen
    outcome: HistoryOutcome

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "screen", _cott_validate_abi(self.screen, HistoryScreen, path="$.screen"))
        if not _cott_validated_construction():
            object.__setattr__(self, "outcome", _cott_validate_abi(self.outcome, HistoryOutcome, path="$.outcome"))

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
"""Fill in the outcome of a logged statement once it is known: set status,
rows, truncated, elapsed_ms (rounded to 3 decimals) and error_text (from failure) of the row
with this id in the log at log_path. A missing row is not an error. Any
failure is Unavailable(log_path, message)."""
"""Read the log at log_path newest first (descending id), keeping rows that
match filter, at most limit rows (all rows for Nothing). The search is a
SQL LIKE '%term%' with "\\\\", "%" and "_" escaped by a backslash (ESCAPE
'\\\\'). A log file that does not exist, or has no queries table, yields an
empty list; reading never creates or migrates the store (open it read-only
with a 250 ms busy timeout). Other failures are Unavailable(log_path,
message). Rows with a status other than ok/error/canceled are skipped."""
"""The status line Harlequin's history list shows for one record:
the run_at time shifted by timezone_offset_minutes and formatted
"%a, %b %d %H:%M:%S", two spaces, then the outcome. For status other than
Ok the outcome is the upper-case status ("ERROR", "CANCELED"). For Ok it is
"{n} record" / "{n} records" (n formatted with plain decimal digits) when
rows is Some and nonzero, otherwise "SUCCESS", followed by
" in {seconds:.2f}s" when elapsed_ms is Some (seconds = elapsed_ms / 1000).
A run_at that does not parse as ISO-8601 is shown verbatim."""
"""The query lines a history row shows: sql stripped and split into lines;
with more than 8 lines, the first 7 followed by "… (N more lines)" where N
is the number of lines not shown."""
"""The initial History screen for the active connection: filter with
connection Some(connection), empty search, no program or status; filters
hidden; focus List; everything else 0."""
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
__all__ = ["HarlequinPaths", "HistoryError", "HistoryError_Unavailable", "HistoryFilter", "HistoryFocus", "HistoryFocus_List", "HistoryFocus_Outcome", "HistoryFocus_Program", "HistoryFocus_Search", "HistoryOutcome", "HistoryOutcome_Close", "HistoryOutcome_Reload", "HistoryOutcome_Select", "HistoryOutcome_Stay", "HistoryScreen", "HistoryStep", "QueryRecord", "QueryStatus", "QueryStatus_Canceled", "QueryStatus_Error", "QueryStatus_Ok"]
