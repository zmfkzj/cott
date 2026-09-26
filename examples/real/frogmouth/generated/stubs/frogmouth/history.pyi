from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.history_types import History as History, HistoryEntry as HistoryEntry, MAXIMUM_HISTORY_LENGTH as MAXIMUM_HISTORY_LENGTH
from frogmouth.model_types import Location
"""A history holding the newest MAXIMUM_HISTORY_LENGTH of locations (the
oldest are dropped), in order, positioned at the newest location."""
def start_history(locations: CottList[Location]) -> History: ...

"""The location at history.current, or Nothing for an empty history."""
def current_location(history: History) -> Option[Location]: ...

"""Record a newly viewed location: append it as the newest entry, even when
it equals an existing entry, drop the oldest entry when the history would
exceed MAXIMUM_HISTORY_LENGTH, and move current to the newest entry.
Entries after current are kept."""
def remember_location(history: History, location: Location) -> History: ...

"""Move one entry toward the oldest location, or Nothing when already at the
oldest (or empty)."""
def step_back(history: History) -> Option[History]: ...

"""Move one entry toward the newest location, or Nothing when already at the
newest (or empty)."""
def step_forward(history: History) -> Option[History]: ...

"""Remove the entry at index history_id, or Nothing when there is no such
entry. An entry older than current moves current down by one, so the same
location stays current. Deleting the current entry keeps current at the
same index, clamped to the new newest entry (0 when the history becomes
empty)."""
def delete_history_entry(history: History, history_id: U64) -> Option[History]: ...

"""The rows of the history pane, newest entry first, each with the index of
its location. A Local prompt is
":page_facing_up: [bold]NAME[/]\\n[dim]PARENT[/]" where NAME is the last
"/"-separated segment of the target and PARENT the target without that
segment and its separating "/" ("/" for a segment directly under the
root, "." for a relative target of one segment). A Remote prompt is
":globe_with_meridians: [bold]NAME[/]\\n[dim]PARENT\\nHOST[/]" with NAME
and PARENT taken the same way from the URL path (an empty path gives an
empty NAME and the PARENT "."), and HOST the lower-cased host name
without userinfo or port. NAME, PARENT and HOST are escaped like
rich.markup.escape, so their text is shown literally."""
def history_entries(history: History) -> CottList[HistoryEntry]: ...

__all__ = ["History", "HistoryEntry", "MAXIMUM_HISTORY_LENGTH", "current_location", "delete_history_entry", "history_entries", "remember_location", "start_history", "step_back", "step_forward"]
