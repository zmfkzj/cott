from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.bookmarks_types import Bookmark as Bookmark
from frogmouth.model_types import Location
"""Append Bookmark(title, location) and return all bookmarks stably sorted
by title, comparing titles by Unicode code point like Python sorted();
bookmarks with equal titles keep their relative order, the new one last."""
def add_bookmark(bookmarks: CottList[Bookmark], title: str, location: Location) -> CottList[Bookmark]: ...

"""Give the bookmark at index the new title, keeping its location and the
order of all bookmarks (the list is not re-sorted)."""
def rename_bookmark(bookmarks: CottList[Bookmark], index: U64, title: str) -> CottList[Bookmark]: ...

"""Remove the bookmark at index, keeping the order of the others."""
def delete_bookmark(bookmarks: CottList[Bookmark], index: U64) -> CottList[Bookmark]: ...

"""The initial title offered when bookmarking location: the last
"/"-separated segment, ignoring trailing "/" characters, of the Local
target or of the Remote URL's path (the text after the authority up to
the first "?" or "#"). It is empty for a URL without a path."""
def suggest_bookmark_title(location: Location) -> str: ...

"""The value an input dialog accepts: value without leading and trailing
whitespace as Python str.strip() removes it, or Nothing when that is
empty, in which case the dialog stays open."""
def accept_dialog_text(value: str) -> Option[str]: ...

"""The Rich console markup prompt of each bookmark, in list order:
":page_facing_up: [bold]TITLE[/]\\n[dim]TARGET[/]" for a Local location
and ":globe_with_meridians: [bold]TITLE[/]\\n[dim]TARGET[/]" for a Remote
one. TITLE and TARGET are escaped like rich.markup.escape, so their text
is shown literally."""
def bookmark_entries(bookmarks: CottList[Bookmark]) -> CottList[str]: ...

__all__ = ["Bookmark", "accept_dialog_text", "add_bookmark", "bookmark_entries", "delete_bookmark", "rename_bookmark", "suggest_bookmark_title"]
