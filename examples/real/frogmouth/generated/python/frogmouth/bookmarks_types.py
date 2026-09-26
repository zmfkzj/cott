from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from frogmouth.model_types import Location

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Bookmark:
    __hash__ = None
    title: str
    location: Location

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "title", _cott_validate_abi(self.title, str, path="$.title"))
        if not _cott_validated_construction():
            object.__setattr__(self, "location", _cott_validate_abi(self.location, Location, path="$.location"))
        if not (_cott_contract_condition(((len((self).title) > 0)), "frogmouth.bookmarks.Bookmark", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="frogmouth.bookmarks.Bookmark", clause="invariant:0", phase="invariant", span={"end_byte":162,"end_column":33,"end_line":9,"start_byte":134,"start_column":5,"start_line":9}, expected="true", actual="false")

"""Append Bookmark(title, location) and return all bookmarks stably sorted
by title, comparing titles by Unicode code point like Python sorted();
bookmarks with equal titles keep their relative order, the new one last."""
"""Give the bookmark at index the new title, keeping its location and the
order of all bookmarks (the list is not re-sorted)."""
"""Remove the bookmark at index, keeping the order of the others."""
"""The initial title offered when bookmarking location: the last
"/"-separated segment, ignoring trailing "/" characters, of the Local
target or of the Remote URL's path (the text after the authority up to
the first "?" or "#"). It is empty for a URL without a path."""
"""The value an input dialog accepts: value without leading and trailing
whitespace as Python str.strip() removes it, or Nothing when that is
empty, in which case the dialog stays open."""
"""The Rich console markup prompt of each bookmark, in list order:
":page_facing_up: [bold]TITLE[/]\\n[dim]TARGET[/]" for a Local location
and ":globe_with_meridians: [bold]TITLE[/]\\n[dim]TARGET[/]" for a Remote
one. TITLE and TARGET are escaped like rich.markup.escape, so their text
is shown literally."""
__all__ = ["Bookmark"]
