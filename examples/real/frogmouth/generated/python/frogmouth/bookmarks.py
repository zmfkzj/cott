from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from frogmouth.bookmarks_types import Bookmark
from frogmouth.model_types import Location

def add_bookmark(bookmarks: CottList[Bookmark], title: str, location: Location) -> CottList[Bookmark]:
    """Append Bookmark(title, location) and return all bookmarks stably sorted
by title, comparing titles by Unicode code point like Python sorted();
bookmarks with equal titles keep their relative order, the new one last."""
    bookmarks = _cott_validate_abi(bookmarks, CottList[Bookmark], path="$.bookmarks")
    title = _cott_validate_abi(title, str, path="$.title")
    location = _cott_validate_abi(location, Location, path="$.location")
    if not (_cott_contract_condition(((len(title) > 0)), "frogmouth.bookmarks.add_bookmark", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.bookmarks.add_bookmark", clause="requires:1", phase="requires", span={"end_byte":533,"end_column":27,"end_line":18,"start_byte":511,"start_column":5,"start_line":18}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/bookmarks/add_bookmark.py", "2aa80bc391280fe0c79702fba00b426b268a9880d33ce77aaad732c9c8be60d8", "add_bookmark", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.bookmarks.add_bookmark")
        _result = _implementation(bookmarks, title, location)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.bookmarks.add_bookmark"
        if _error.span is None:
            _error.span = {"end_byte":596,"end_column":1,"end_line":24,"start_byte":164,"start_column":1,"start_line":11}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.bookmarks.add_bookmark", phase="implementation-call", span={"end_byte":596,"end_column":1,"end_line":24,"start_byte":164,"start_column":1,"start_line":11}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.bookmarks.add_bookmark", phase="implementation-call", span={"end_byte":596,"end_column":1,"end_line":24,"start_byte":164,"start_column":1,"start_line":11}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[Bookmark], path="$.return")
    if not (_cott_contract_condition(((len(_result) == (len(bookmarks) + 1))), "frogmouth.bookmarks.add_bookmark", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.bookmarks.add_bookmark", clause="ensures:2", phase="ensures", span={"end_byte":578,"end_column":44,"end_line":20,"start_byte":539,"start_column":5,"start_line":20}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[Bookmark], path="$.return", validator=_cott_validate_abi)
    return _result

def rename_bookmark(bookmarks: CottList[Bookmark], index: U64, title: str) -> CottList[Bookmark]:
    """Give the bookmark at index the new title, keeping its location and the
order of all bookmarks (the list is not re-sorted)."""
    bookmarks = _cott_validate_abi(bookmarks, CottList[Bookmark], path="$.bookmarks")
    index = _cott_validate_abi(index, U64, path="$.index")
    title = _cott_validate_abi(title, str, path="$.title")
    if not (_cott_contract_condition(((index < len(bookmarks))), "frogmouth.bookmarks.rename_bookmark", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.bookmarks.rename_bookmark", clause="requires:1", phase="requires", span={"end_byte":871,"end_column":35,"end_line":30,"start_byte":841,"start_column":5,"start_line":30}, expected="true", actual="false")
    if not (_cott_contract_condition(((len(title) > 0)), "frogmouth.bookmarks.rename_bookmark", "requires:2")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.bookmarks.rename_bookmark", clause="requires:2", phase="requires", span={"end_byte":898,"end_column":27,"end_line":31,"start_byte":876,"start_column":5,"start_line":31}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/bookmarks/rename_bookmark.py", "66393a3f718892ffd6989e871d3fe7fe46ba1577bd1569a5a4f6d9c96b30bc60", "rename_bookmark", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.bookmarks.rename_bookmark")
        _result = _implementation(bookmarks, index, title)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.bookmarks.rename_bookmark"
        if _error.span is None:
            _error.span = {"end_byte":957,"end_column":1,"end_line":37,"start_byte":596,"start_column":1,"start_line":24}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.bookmarks.rename_bookmark", phase="implementation-call", span={"end_byte":957,"end_column":1,"end_line":37,"start_byte":596,"start_column":1,"start_line":24}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.bookmarks.rename_bookmark", phase="implementation-call", span={"end_byte":957,"end_column":1,"end_line":37,"start_byte":596,"start_column":1,"start_line":24}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[Bookmark], path="$.return")
    if not (_cott_contract_condition(((len(_result) == len(bookmarks))), "frogmouth.bookmarks.rename_bookmark", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.bookmarks.rename_bookmark", clause="ensures:3", phase="ensures", span={"end_byte":939,"end_column":40,"end_line":33,"start_byte":904,"start_column":5,"start_line":33}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[Bookmark], path="$.return", validator=_cott_validate_abi)
    return _result

def delete_bookmark(bookmarks: CottList[Bookmark], index: U64) -> CottList[Bookmark]:
    """Remove the bookmark at index, keeping the order of the others."""
    bookmarks = _cott_validate_abi(bookmarks, CottList[Bookmark], path="$.bookmarks")
    index = _cott_validate_abi(index, U64, path="$.index")
    if not (_cott_contract_condition(((index < len(bookmarks))), "frogmouth.bookmarks.delete_bookmark", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.bookmarks.delete_bookmark", clause="requires:1", phase="requires", span={"end_byte":1156,"end_column":35,"end_line":42,"start_byte":1126,"start_column":5,"start_line":42}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/bookmarks/delete_bookmark.py", "f12cfa4358c535fcc041eb280627177bc3ddd50c561a26ea0c245fccf5e6aefb", "delete_bookmark", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.bookmarks.delete_bookmark")
        _result = _implementation(bookmarks, index)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.bookmarks.delete_bookmark"
        if _error.span is None:
            _error.span = {"end_byte":1219,"end_column":1,"end_line":48,"start_byte":957,"start_column":1,"start_line":37}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.bookmarks.delete_bookmark", phase="implementation-call", span={"end_byte":1219,"end_column":1,"end_line":48,"start_byte":957,"start_column":1,"start_line":37}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.bookmarks.delete_bookmark", phase="implementation-call", span={"end_byte":1219,"end_column":1,"end_line":48,"start_byte":957,"start_column":1,"start_line":37}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[Bookmark], path="$.return")
    if not (_cott_contract_condition((((len(_result) + 1) == len(bookmarks))), "frogmouth.bookmarks.delete_bookmark", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.bookmarks.delete_bookmark", clause="ensures:2", phase="ensures", span={"end_byte":1201,"end_column":44,"end_line":44,"start_byte":1162,"start_column":5,"start_line":44}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[Bookmark], path="$.return", validator=_cott_validate_abi)
    return _result

def suggest_bookmark_title(location: Location) -> str:
    """The initial title offered when bookmarking location: the last
"/"-separated segment, ignoring trailing "/" characters, of the Local
target or of the Remote URL's path (the text after the authority up to
the first "?" or "#"). It is empty for a URL without a path."""
    location = _cott_validate_abi(location, Location, path="$.location")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/bookmarks/suggest_bookmark_title.py", "21f70121797941ce6fdbdbffbda70080554ef743aeaa7e5d9c7a0ed2497fe4c4", "suggest_bookmark_title", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.bookmarks.suggest_bookmark_title")
        _result = _implementation(location)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.bookmarks.suggest_bookmark_title"
        if _error.span is None:
            _error.span = {"end_byte":1679,"end_column":1,"end_line":61,"start_byte":1219,"start_column":1,"start_line":48}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.bookmarks.suggest_bookmark_title", phase="implementation-call", span={"end_byte":1679,"end_column":1,"end_line":61,"start_byte":1219,"start_column":1,"start_line":48}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.bookmarks.suggest_bookmark_title", phase="implementation-call", span={"end_byte":1679,"end_column":1,"end_line":61,"start_byte":1219,"start_column":1,"start_line":48}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not (_cott_contract_condition(((_result in (location).target)), "frogmouth.bookmarks.suggest_bookmark_title", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.bookmarks.suggest_bookmark_title", clause="ensures:1", phase="ensures", span={"end_byte":1621,"end_column":48,"end_line":56,"start_byte":1578,"start_column":5,"start_line":56}, expected="true", actual="false")
    if not (_cott_contract_condition(((not ("/" in _result))), "frogmouth.bookmarks.suggest_bookmark_title", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.bookmarks.suggest_bookmark_title", clause="ensures:2", phase="ensures", span={"end_byte":1661,"end_column":40,"end_line":57,"start_byte":1626,"start_column":5,"start_line":57}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def accept_dialog_text(value: str) -> Option[str]:
    """The value an input dialog accepts: value without leading and trailing
whitespace as Python str.strip() removes it, or Nothing when that is
empty, in which case the dialog stays open."""
    value = _cott_validate_abi(value, str, path="$.value")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/bookmarks/accept_dialog_text.py", "1e4eae1032e73009edee6ce6768ce95b7b13342edda8cceb803c42efc3043116", "accept_dialog_text", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.bookmarks.accept_dialog_text")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.bookmarks.accept_dialog_text"
        if _error.span is None:
            _error.span = {"end_byte":2063,"end_column":1,"end_line":73,"start_byte":1679,"start_column":1,"start_line":61}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.bookmarks.accept_dialog_text", phase="implementation-call", span={"end_byte":2063,"end_column":1,"end_line":73,"start_byte":1679,"start_column":1,"start_line":61}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.bookmarks.accept_dialog_text", phase="implementation-call", span={"end_byte":2063,"end_column":1,"end_line":73,"start_byte":1679,"start_column":1,"start_line":61}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[str], path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            text = _cott_match_value.value
            return (_cott_contract_condition(((len(text) > 0)), "frogmouth.bookmarks.accept_dialog_text", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.bookmarks.accept_dialog_text", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.bookmarks.accept_dialog_text", clause="ensures:1", phase="ensures", span={"end_byte":1990,"end_column":46,"end_line":68,"start_byte":1949,"start_column":5,"start_line":68}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            text = _cott_match_value.value
            return (_cott_contract_condition(((text in value)), "frogmouth.bookmarks.accept_dialog_text", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.bookmarks.accept_dialog_text", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.bookmarks.accept_dialog_text", clause="ensures:2", phase="ensures", span={"end_byte":2045,"end_column":55,"end_line":69,"start_byte":1995,"start_column":5,"start_line":69}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[str], path="$.return", validator=_cott_validate_abi)
    return _result

def bookmark_entries(bookmarks: CottList[Bookmark]) -> CottList[str]:
    """The Rich console markup prompt of each bookmark, in list order:
":page_facing_up: [bold]TITLE[/]\\n[dim]TARGET[/]" for a Local location
and ":globe_with_meridians: [bold]TITLE[/]\\n[dim]TARGET[/]" for a Remote
one. TITLE and TARGET are escaped like rich.markup.escape, so their text
is shown literally."""
    bookmarks = _cott_validate_abi(bookmarks, CottList[Bookmark], path="$.bookmarks")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/bookmarks/bookmark_entries.py", "8d322892206068e875e6c82125d8396588a9407c9f8e54cf433065d16ae7b433", "bookmark_entries", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.bookmarks.bookmark_entries")
        _result = _implementation(bookmarks)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.bookmarks.bookmark_entries"
        if _error.span is None:
            _error.span = {"end_byte":2523,"end_column":1,"end_line":86,"start_byte":2063,"start_column":1,"start_line":73}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.bookmarks.bookmark_entries", phase="implementation-call", span={"end_byte":2523,"end_column":1,"end_line":86,"start_byte":2063,"start_column":1,"start_line":73}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.bookmarks.bookmark_entries", phase="implementation-call", span={"end_byte":2523,"end_column":1,"end_line":86,"start_byte":2063,"start_column":1,"start_line":73}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[str], path="$.return")
    if not (_cott_contract_condition(((len(_result) == len(bookmarks))), "frogmouth.bookmarks.bookmark_entries", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.bookmarks.bookmark_entries", clause="ensures:1", phase="ensures", span={"end_byte":2505,"end_column":40,"end_line":82,"start_byte":2470,"start_column":5,"start_line":82}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["Bookmark", "accept_dialog_text", "add_bookmark", "bookmark_entries", "delete_bookmark", "rename_bookmark", "suggest_bookmark_title"]
