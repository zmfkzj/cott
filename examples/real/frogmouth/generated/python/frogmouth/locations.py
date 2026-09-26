from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_ends_with, _cott_starts_with
from frogmouth.model_types import Location, LocationKind, LocationKind_Remote, PathKind

def remote_location(candidate: str) -> Option[Location]:
    """Recognize text that is likely a web URL, the way the address bar, links
and stored locations are classified. candidate is not trimmed. It is a URL
when its scheme, the text before the first "://", is "http" or "https"
compared ASCII case-insensitively, and its authority, the text after that
"://" up to the first "/", "?" or "#", still names a non-empty host once a
leading "userinfo@" part and a trailing ":port" part are removed. Nothing
else is validated. The Remote target is candidate with its scheme
lower-cased and every other character unchanged. Any other candidate,
including "http://", "ftp://host/a.md" and "example.com/a.md", is Nothing."""
    candidate = _cott_validate_abi(candidate, str, path="$.candidate")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/locations/remote_location.py", "50cdde31104b175f1c067538205d9afabea9c9656dcdefbdf2dcdd1cb133f0f2", "remote_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.locations.remote_location")
        _result = _implementation(candidate)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.locations.remote_location"
        if _error.span is None:
            _error.span = {"end_byte":1223,"end_column":1,"end_line":25,"start_byte":84,"start_column":1,"start_line":5}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.locations.remote_location", phase="implementation-call", span={"end_byte":1223,"end_column":1,"end_line":25,"start_byte":84,"start_column":1,"start_line":5}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.locations.remote_location", phase="implementation-call", span={"end_byte":1223,"end_column":1,"end_line":25,"start_byte":84,"start_column":1,"start_line":5}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[Location], path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            location = _cott_match_value.value
            return (_cott_contract_condition((((location).kind == LocationKind_Remote())), "frogmouth.locations.remote_location", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.locations.remote_location", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.remote_location", clause="ensures:1", phase="ensures", span={"end_byte":922,"end_column":74,"end_line":18,"start_byte":853,"start_column":5,"start_line":18}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            location = _cott_match_value.value
            return (_cott_contract_condition(((len((location).target) == len(candidate))), "frogmouth.locations.remote_location", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.locations.remote_location", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.remote_location", clause="ensures:2", phase="ensures", span={"end_byte":996,"end_column":74,"end_line":19,"start_byte":927,"start_column":5,"start_line":19}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            location = _cott_match_value.value
            return (_cott_contract_condition((((not (_cott_starts_with(candidate, "http://") or _cott_starts_with(candidate, "https://"))) or ((location).target == candidate))), "frogmouth.locations.remote_location", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.locations.remote_location", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.remote_location", clause="ensures:3", phase="ensures", span={"end_byte":1141,"end_column":145,"end_line":20,"start_byte":1001,"start_column":5,"start_line":20}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            location = _cott_match_value.value
            return (_cott_contract_condition((("://" in candidate)), "frogmouth.locations.remote_location", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.locations.remote_location", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.remote_location", clause="ensures:4", phase="ensures", span={"end_byte":1205,"end_column":64,"end_line":21,"start_byte":1146,"start_column":5,"start_line":21}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[Location], path="$.return", validator=_cott_validate_abi)
    return _result

def normalize_local_path(directory: str, path: str) -> str:
    """Lexically resolve path against directory without consulting the file
system. A path starting with "/" stands alone; an empty path names
directory; any other path is appended to directory after one "/". The
combined text is split at "/": empty and "." segments are dropped, and a
".." segment removes the nearest preceding kept segment, or is dropped
when there is none. The kept segments are joined with "/", with a leading
"/" when the combined text started with one. An absolute result without
segments is "/"; a relative result without segments is ".". Symbolic links
are not resolved and "~" has no special meaning."""
    directory = _cott_validate_abi(directory, str, path="$.directory")
    path = _cott_validate_abi(path, str, path="$.path")
    if not (_cott_contract_condition(((len(directory) > 0)), "frogmouth.locations.normalize_local_path", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.locations.normalize_local_path", clause="requires:1", phase="requires", span={"end_byte":1989,"end_column":31,"end_line":38,"start_byte":1963,"start_column":5,"start_line":38}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/locations/normalize_local_path.py", "bfd376743511e15da41c598424638ad67b12ae6a747a23a4abfb14f60f361651", "normalize_local_path", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.locations.normalize_local_path")
        _result = _implementation(directory, path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.locations.normalize_local_path"
        if _error.span is None:
            _error.span = {"end_byte":2672,"end_column":1,"end_line":51,"start_byte":1223,"start_column":1,"start_line":25}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.locations.normalize_local_path", phase="implementation-call", span={"end_byte":2672,"end_column":1,"end_line":51,"start_byte":1223,"start_column":1,"start_line":25}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.locations.normalize_local_path", phase="implementation-call", span={"end_byte":2672,"end_column":1,"end_line":51,"start_byte":1223,"start_column":1,"start_line":25}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not (_cott_contract_condition(((len(_result) > 0)), "frogmouth.locations.normalize_local_path", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.normalize_local_path", clause="ensures:2", phase="ensures", span={"end_byte":2017,"end_column":27,"end_line":40,"start_byte":1995,"start_column":5,"start_line":40}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (_cott_starts_with(path, "/") or _cott_starts_with(directory, "/"))) or _cott_starts_with(_result, "/"))), "frogmouth.locations.normalize_local_path", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.normalize_local_path", clause="ensures:3", phase="ensures", span={"end_byte":2115,"end_column":98,"end_line":41,"start_byte":2022,"start_column":5,"start_line":41}, expected="true", actual="false")
    if not (_cott_contract_condition((((not ((not _cott_starts_with(path, "/")) and (not _cott_starts_with(directory, "/")))) or (not _cott_starts_with(_result, "/")))), "frogmouth.locations.normalize_local_path", "ensures:4")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.normalize_local_path", clause="ensures:4", phase="ensures", span={"end_byte":2226,"end_column":111,"end_line":42,"start_byte":2120,"start_column":5,"start_line":42}, expected="true", actual="false")
    if not (_cott_contract_condition(((not ("//" in _result))), "frogmouth.locations.normalize_local_path", "ensures:5")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.normalize_local_path", clause="ensures:5", phase="ensures", span={"end_byte":2267,"end_column":41,"end_line":43,"start_byte":2231,"start_column":5,"start_line":43}, expected="true", actual="false")
    if not (_cott_contract_condition((((not ("/./" in _result)) and (not _cott_ends_with(_result, "/.")))), "frogmouth.locations.normalize_local_path", "ensures:6")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.normalize_local_path", clause="ensures:6", phase="ensures", span={"end_byte":2341,"end_column":74,"end_line":44,"start_byte":2272,"start_column":5,"start_line":44}, expected="true", actual="false")
    if not (_cott_contract_condition(((((not ("/../" in _result)) and (not _cott_ends_with(_result, "/.."))) and (not _cott_starts_with(_result, "../")))), "frogmouth.locations.normalize_local_path", "ensures:7")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.normalize_local_path", clause="ensures:7", phase="ensures", span={"end_byte":2452,"end_column":111,"end_line":45,"start_byte":2346,"start_column":5,"start_line":45}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (_result != "/")) or (not _cott_ends_with(_result, "/")))), "frogmouth.locations.normalize_local_path", "ensures:8")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.normalize_local_path", clause="ensures:8", phase="ensures", span={"end_byte":2510,"end_column":58,"end_line":46,"start_byte":2457,"start_column":5,"start_line":46}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (((_cott_starts_with(path, "/") and (not ("//" in path))) and (not ("/." in path))) and (not _cott_ends_with(path, "/")))) or (_result == path))), "frogmouth.locations.normalize_local_path", "ensures:9")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.normalize_local_path", clause="ensures:9", phase="ensures", span={"end_byte":2654,"end_column":144,"end_line":47,"start_byte":2515,"start_column":5,"start_line":47}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_local_path(text: str, home: str, working_directory: str) -> str:
    """The local path that address-bar or command text names: pathlib's
expanduser() followed by lexical absolutization. Text that is exactly "~"
becomes home and a leading "~/" becomes home followed by "/"; text starting
with "~" otherwise (such as "~user/a.md") is kept literally. The result is
frogmouth.locations.normalize_local_path(working_directory, expanded text)."""
    text = _cott_validate_abi(text, str, path="$.text")
    home = _cott_validate_abi(home, str, path="$.home")
    working_directory = _cott_validate_abi(working_directory, str, path="$.working_directory")
    if not (_cott_contract_condition(((len(home) > 0)), "frogmouth.locations.resolve_local_path", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.locations.resolve_local_path", clause="requires:1", phase="requires", span={"end_byte":3180,"end_column":26,"end_line":60,"start_byte":3159,"start_column":5,"start_line":60}, expected="true", actual="false")
    if not (_cott_contract_condition(((len(working_directory) > 0)), "frogmouth.locations.resolve_local_path", "requires:2")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.locations.resolve_local_path", clause="requires:2", phase="requires", span={"end_byte":3219,"end_column":39,"end_line":61,"start_byte":3185,"start_column":5,"start_line":61}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/locations/resolve_local_path.py", "f5326e0ba91f060d531794a0821350ee215ea10063c7e389d018f191dc6baa09", "resolve_local_path", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.locations.resolve_local_path")
        _result = _implementation(text, home, working_directory)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.locations.resolve_local_path"
        if _error.span is None:
            _error.span = {"end_byte":3467,"end_column":1,"end_line":69,"start_byte":2672,"start_column":1,"start_line":51}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.locations.resolve_local_path", phase="implementation-call", span={"end_byte":3467,"end_column":1,"end_line":69,"start_byte":2672,"start_column":1,"start_line":51}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.locations.resolve_local_path", phase="implementation-call", span={"end_byte":3467,"end_column":1,"end_line":69,"start_byte":2672,"start_column":1,"start_line":51}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not (_cott_contract_condition(((len(_result) > 0)), "frogmouth.locations.resolve_local_path", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.resolve_local_path", clause="ensures:3", phase="ensures", span={"end_byte":3247,"end_column":27,"end_line":63,"start_byte":3225,"start_column":5,"start_line":63}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (_cott_starts_with(home, "/") and _cott_starts_with(working_directory, "/"))) or _cott_starts_with(_result, "/"))), "frogmouth.locations.resolve_local_path", "ensures:4")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.resolve_local_path", clause="ensures:4", phase="ensures", span={"end_byte":3354,"end_column":107,"end_line":64,"start_byte":3252,"start_column":5,"start_line":64}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (_cott_starts_with(text, "~/") and _cott_starts_with(home, "/"))) or _cott_starts_with(_result, "/"))), "frogmouth.locations.resolve_local_path", "ensures:5")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.resolve_local_path", clause="ensures:5", phase="ensures", span={"end_byte":3449,"end_column":95,"end_line":65,"start_byte":3359,"start_column":5,"start_line":65}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def inspect_local_path(path: str) -> PathKind:
    """Classify path in the file system the program runs against, following
symbolic links: the fs fixture root while a Cott scenario with an fs
fixture is active, otherwise the host file system, where a relative path
is relative to the process working directory. File is a regular file, Directory a directory, Other any other
existing kind (FIFO, socket, device). Missing means the path does not
exist or cannot be examined: an absent entry, a non-directory component,
a symbolic-link loop or denied permission."""
    path = _cott_validate_abi(path, str, path="$.path")
    if not (_cott_contract_condition(((len(path) > 0)), "frogmouth.locations.inspect_local_path", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.locations.inspect_local_path", clause="requires:1", phase="requires", span={"end_byte":4093,"end_column":26,"end_line":80,"start_byte":4072,"start_column":5,"start_line":80}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/locations/inspect_local_path.py", "9618963b2befe4092259452b6dda57132f823554c80db62df91fc147168b4d68", "inspect_local_path", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.locations.inspect_local_path")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.locations.inspect_local_path"
        if _error.span is None:
            _error.span = {"end_byte":4120,"end_column":1,"end_line":84,"start_byte":3467,"start_column":1,"start_line":69}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.locations.inspect_local_path", phase="implementation-call", span={"end_byte":4120,"end_column":1,"end_line":84,"start_byte":3467,"start_column":1,"start_line":69}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.locations.inspect_local_path", phase="implementation-call", span={"end_byte":4120,"end_column":1,"end_line":84,"start_byte":3467,"start_column":1,"start_line":69}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, PathKind, path="$.return")
    _result = _cott_wrap_async_protocol(_result, PathKind, path="$.return", validator=_cott_validate_abi)
    return _result

def is_markdown_location(location: Location, extensions: CottList[str]) -> bool:
    """Whether location looks like a Markdown document by its suffix. The name is
the last "/"-separated segment, ignoring trailing "/" characters, of the
Local target or of the Remote URL's path (the text after the authority up
to the first "?" or "#"). With the name's leading "." characters removed,
the suffix is the text from its last "." to the end, or empty when there
is none; so ".md" has no suffix, "a." has the suffix "." and
"archive.tar.gz" has ".gz". The result is true exactly when the ASCII
lower-cased suffix is one of extensions, compared exactly."""
    location = _cott_validate_abi(location, Location, path="$.location")
    extensions = _cott_validate_abi(extensions, CottList[str], path="$.extensions")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/locations/is_markdown_location.py", "e172e13514fed6fa418f59ef652b6c66e684a526c69e7ad63aac75221990af47", "is_markdown_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.locations.is_markdown_location")
        _result = _implementation(location, extensions)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.locations.is_markdown_location"
        if _error.span is None:
            _error.span = {"end_byte":4930,"end_column":1,"end_line":101,"start_byte":4120,"start_column":1,"start_line":84}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.locations.is_markdown_location", phase="implementation-call", span={"end_byte":4930,"end_column":1,"end_line":101,"start_byte":4120,"start_column":1,"start_line":84}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.locations.is_markdown_location", phase="implementation-call", span={"end_byte":4930,"end_column":1,"end_line":101,"start_byte":4120,"start_column":1,"start_line":84}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, bool, path="$.return")
    if not (_cott_contract_condition((((not (len(extensions) == 0)) or (not _result))), "frogmouth.locations.is_markdown_location", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.is_markdown_location", clause="ensures:1", phase="ensures", span={"end_byte":4857,"end_column":50,"end_line":96,"start_byte":4812,"start_column":5,"start_line":96}, expected="true", actual="false")
    if not (_cott_contract_condition((((not _result) or ("." in (location).target))), "frogmouth.locations.is_markdown_location", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.locations.is_markdown_location", clause="ensures:2", phase="ensures", span={"end_byte":4912,"end_column":55,"end_line":97,"start_byte":4862,"start_column":5,"start_line":97}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["inspect_local_path", "is_markdown_location", "normalize_local_path", "remote_location", "resolve_local_path"]
