from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from frogmouth.model_types import Location

"""The maximum number of locations kept in the browsing history."""
MAXIMUM_HISTORY_LENGTH: Final[U64] = 256

"""The browsing history, oldest location first. current is the index of the
history position the viewer is at; it is 0 in an empty history."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class History:
    __hash__ = None
    locations: CottList[Location]
    current: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "locations", _cott_validate_abi(self.locations, CottList[Location], path="$.locations"))
        if not _cott_validated_construction():
            object.__setattr__(self, "current", _cott_validate_abi(self.current, U64, path="$.current"))
        if not (_cott_contract_condition(((len((self).locations) <= MAXIMUM_HISTORY_LENGTH)), "frogmouth.history.History", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="frogmouth.history.History", clause="invariant:0", phase="invariant", span={"end_byte":458,"end_column":59,"end_line":18,"start_byte":404,"start_column":5,"start_line":18}, expected="true", actual="false")
        if not (_cott_contract_condition(((((len((self).locations) == 0) and ((self).current == 0)) or ((self).current < len((self).locations)))), "frogmouth.history.History", "invariant:1")):
            raise CottContractViolation("invariant failed", symbol="frogmouth.history.History", clause="invariant:1", phase="invariant", span={"end_byte":559,"end_column":101,"end_line":19,"start_byte":463,"start_column":5,"start_line":19}, expected="true", actual="false")

"""One row of the history pane. history_id is the index of location in
History.locations; prompt is Rich console markup."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HistoryEntry:
    __hash__ = None
    history_id: U64
    location: Location
    prompt: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "history_id", _cott_validate_abi(self.history_id, U64, path="$.history_id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "location", _cott_validate_abi(self.location, Location, path="$.location"))
        if not _cott_validated_construction():
            object.__setattr__(self, "prompt", _cott_validate_abi(self.prompt, str, path="$.prompt"))

"""A history holding the newest MAXIMUM_HISTORY_LENGTH of locations (the
oldest are dropped), in order, positioned at the newest location."""
"""The location at history.current, or Nothing for an empty history."""
"""Record a newly viewed location: append it as the newest entry, even when
it equals an existing entry, drop the oldest entry when the history would
exceed MAXIMUM_HISTORY_LENGTH, and move current to the newest entry.
Entries after current are kept."""
"""Move one entry toward the oldest location, or Nothing when already at the
oldest (or empty)."""
"""Move one entry toward the newest location, or Nothing when already at the
newest (or empty)."""
"""Remove the entry at index history_id, or Nothing when there is no such
entry. An entry older than current moves current down by one, so the same
location stays current. Deleting the current entry keeps current at the
same index, clamped to the new newest entry (0 when the history becomes
empty)."""
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
__all__ = ["History", "HistoryEntry", "MAXIMUM_HISTORY_LENGTH"]
