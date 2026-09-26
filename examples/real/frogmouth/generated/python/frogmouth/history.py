from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from frogmouth.history_types import History, HistoryEntry, MAXIMUM_HISTORY_LENGTH
from frogmouth.model_types import Location

def start_history(locations: CottList[Location]) -> History:
    """A history holding the newest MAXIMUM_HISTORY_LENGTH of locations (the
oldest are dropped), in order, positioned at the newest location."""
    locations = _cott_validate_abi(locations, CottList[Location], path="$.locations")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/history/start_history.py", "65c2bc5957d4560906790a02692e68c37ba6757a8468054cbed7a6d01f78b41f", "start_history", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.history.start_history")
        _result = _implementation(locations)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.history.start_history"
        if _error.span is None:
            _error.span = {"end_byte":1291,"end_column":1,"end_line":42,"start_byte":772,"start_column":1,"start_line":30}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.history.start_history", phase="implementation-call", span={"end_byte":1291,"end_column":1,"end_line":42,"start_byte":772,"start_column":1,"start_line":30}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.history.start_history", phase="implementation-call", span={"end_byte":1291,"end_column":1,"end_line":42,"start_byte":772,"start_column":1,"start_line":30}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, History, path="$.return")
    if not (_cott_contract_condition((((not (len(locations) <= MAXIMUM_HISTORY_LENGTH)) or ((_result).locations == locations))), "frogmouth.history.start_history", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.start_history", clause="ensures:1", phase="ensures", span={"end_byte":1081,"end_column":89,"end_line":36,"start_byte":997,"start_column":5,"start_line":36}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (len(locations) > MAXIMUM_HISTORY_LENGTH)) or (len((_result).locations) == MAXIMUM_HISTORY_LENGTH))), "frogmouth.history.start_history", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.start_history", clause="ensures:2", phase="ensures", span={"end_byte":1186,"end_column":105,"end_line":37,"start_byte":1086,"start_column":5,"start_line":37}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (len((_result).locations) > 0)) or (((_result).current + 1) == len((_result).locations)))), "frogmouth.history.start_history", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.start_history", clause="ensures:3", phase="ensures", span={"end_byte":1273,"end_column":87,"end_line":38,"start_byte":1191,"start_column":5,"start_line":38}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, History, path="$.return", validator=_cott_validate_abi)
    return _result

def current_location(history: History) -> Option[Location]:
    """The location at history.current, or Nothing for an empty history."""
    history = _cott_validate_abi(history, History, path="$.history")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/history/current_location.py", "6d515b6a711cf017a073f0ee554e2491961574452d29c59a58b9bba3f5a8dd39", "current_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.history.current_location")
        _result = _implementation(history)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.history.current_location"
        if _error.span is None:
            _error.span = {"end_byte":1571,"end_column":1,"end_line":52,"start_byte":1291,"start_column":1,"start_line":42}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.history.current_location", phase="implementation-call", span={"end_byte":1571,"end_column":1,"end_line":52,"start_byte":1291,"start_column":1,"start_line":42}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.history.current_location", phase="implementation-call", span={"end_byte":1571,"end_column":1,"end_line":52,"start_byte":1291,"start_column":1,"start_line":42}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[Location], path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            return (_cott_contract_condition(((len((history).locations) > 0)), "frogmouth.history.current_location", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.history.current_location", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.current_location", clause="ensures:1", phase="ensures", span={"end_byte":1496,"end_column":56,"end_line":47,"start_byte":1445,"start_column":5,"start_line":47}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Nothing:
            return (_cott_contract_condition(((len((history).locations) == 0)), "frogmouth.history.current_location", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.history.current_location", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.current_location", clause="ensures:2", phase="ensures", span={"end_byte":1553,"end_column":57,"end_line":48,"start_byte":1501,"start_column":5,"start_line":48}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[Location], path="$.return", validator=_cott_validate_abi)
    return _result

def remember_location(history: History, location: Location) -> History:
    """Record a newly viewed location: append it as the newest entry, even when
it equals an existing entry, drop the oldest entry when the history would
exceed MAXIMUM_HISTORY_LENGTH, and move current to the newest entry.
Entries after current are kept."""
    history = _cott_validate_abi(history, History, path="$.history")
    location = _cott_validate_abi(location, Location, path="$.location")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/history/remember_location.py", "4b25fd5c8fe02811d973b9d121f3f080f93594877eb4fe78ffab52c4503c7454", "remember_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.history.remember_location")
        _result = _implementation(history, location)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.history.remember_location"
        if _error.span is None:
            _error.span = {"end_byte":2229,"end_column":1,"end_line":66,"start_byte":1571,"start_column":1,"start_line":52}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.history.remember_location", phase="implementation-call", span={"end_byte":2229,"end_column":1,"end_line":66,"start_byte":1571,"start_column":1,"start_line":52}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.history.remember_location", phase="implementation-call", span={"end_byte":2229,"end_column":1,"end_line":66,"start_byte":1571,"start_column":1,"start_line":52}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, History, path="$.return")
    if not (_cott_contract_condition(((((_result).current + 1) == len((_result).locations))), "frogmouth.history.remember_location", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.remember_location", clause="ensures:1", phase="ensures", span={"end_byte":1981,"end_column":55,"end_line":60,"start_byte":1931,"start_column":5,"start_line":60}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (len((history).locations) < MAXIMUM_HISTORY_LENGTH)) or (len((_result).locations) == (len((history).locations) + 1)))), "frogmouth.history.remember_location", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.remember_location", clause="ensures:2", phase="ensures", span={"end_byte":2097,"end_column":116,"end_line":61,"start_byte":1986,"start_column":5,"start_line":61}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (len((history).locations) == MAXIMUM_HISTORY_LENGTH)) or (len((_result).locations) == MAXIMUM_HISTORY_LENGTH))), "frogmouth.history.remember_location", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.remember_location", clause="ensures:3", phase="ensures", span={"end_byte":2211,"end_column":114,"end_line":62,"start_byte":2102,"start_column":5,"start_line":62}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, History, path="$.return", validator=_cott_validate_abi)
    return _result

def step_back(history: History) -> Option[History]:
    """Move one entry toward the oldest location, or Nothing when already at the
oldest (or empty)."""
    history = _cott_validate_abi(history, History, path="$.history")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/history/step_back.py", "5a11713dfd53a012d5d9dbb3548cace5fdc94f7f70ec0330121d01e71cfc09be", "step_back", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.history.step_back")
        _result = _implementation(history)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.history.step_back"
        if _error.span is None:
            _error.span = {"end_byte":2612,"end_column":1,"end_line":78,"start_byte":2229,"start_column":1,"start_line":66}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.history.step_back", phase="implementation-call", span={"end_byte":2612,"end_column":1,"end_line":78,"start_byte":2229,"start_column":1,"start_line":66}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.history.step_back", phase="implementation-call", span={"end_byte":2612,"end_column":1,"end_line":78,"start_byte":2229,"start_column":1,"start_line":66}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[History], path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            moved = _cott_match_value.value
            return (_cott_contract_condition(((((moved).current + 1) == (history).current)), "frogmouth.history.step_back", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.history.step_back", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.step_back", clause="ensures:1", phase="ensures", span={"end_byte":2472,"end_column":71,"end_line":72,"start_byte":2406,"start_column":5,"start_line":72}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            moved = _cott_match_value.value
            return (_cott_contract_condition((((moved).locations == (history).locations)), "frogmouth.history.step_back", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.history.step_back", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.step_back", clause="ensures:2", phase="ensures", span={"end_byte":2543,"end_column":71,"end_line":73,"start_byte":2477,"start_column":5,"start_line":73}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Nothing:
            return (_cott_contract_condition((((history).current == 0)), "frogmouth.history.step_back", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.history.step_back", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.step_back", clause="ensures:3", phase="ensures", span={"end_byte":2594,"end_column":51,"end_line":74,"start_byte":2548,"start_column":5,"start_line":74}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[History], path="$.return", validator=_cott_validate_abi)
    return _result

def step_forward(history: History) -> Option[History]:
    """Move one entry toward the newest location, or Nothing when already at the
newest (or empty)."""
    history = _cott_validate_abi(history, History, path="$.history")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/history/step_forward.py", "8ae49bcdd7ed380959d165c52bf1e66a7c055803f6d627f23402e00cbd38395b", "step_forward", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.history.step_forward")
        _result = _implementation(history)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.history.step_forward"
        if _error.span is None:
            _error.span = {"end_byte":3022,"end_column":1,"end_line":90,"start_byte":2612,"start_column":1,"start_line":78}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.history.step_forward", phase="implementation-call", span={"end_byte":3022,"end_column":1,"end_line":90,"start_byte":2612,"start_column":1,"start_line":78}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.history.step_forward", phase="implementation-call", span={"end_byte":3022,"end_column":1,"end_line":90,"start_byte":2612,"start_column":1,"start_line":78}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[History], path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            moved = _cott_match_value.value
            return (_cott_contract_condition((((moved).current == ((history).current + 1))), "frogmouth.history.step_forward", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.history.step_forward", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.step_forward", clause="ensures:1", phase="ensures", span={"end_byte":2858,"end_column":71,"end_line":84,"start_byte":2792,"start_column":5,"start_line":84}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            moved = _cott_match_value.value
            return (_cott_contract_condition((((moved).locations == (history).locations)), "frogmouth.history.step_forward", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.history.step_forward", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.step_forward", clause="ensures:2", phase="ensures", span={"end_byte":2929,"end_column":71,"end_line":85,"start_byte":2863,"start_column":5,"start_line":85}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Nothing:
            return (_cott_contract_condition(((((history).current + 1) >= len((history).locations))), "frogmouth.history.step_forward", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.history.step_forward", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.step_forward", clause="ensures:3", phase="ensures", span={"end_byte":3004,"end_column":75,"end_line":86,"start_byte":2934,"start_column":5,"start_line":86}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[History], path="$.return", validator=_cott_validate_abi)
    return _result

def delete_history_entry(history: History, history_id: U64) -> Option[History]:
    """Remove the entry at index history_id, or Nothing when there is no such
entry. An entry older than current moves current down by one, so the same
location stays current. Deleting the current entry keeps current at the
same index, clamped to the new newest entry (0 when the history becomes
empty)."""
    history = _cott_validate_abi(history, History, path="$.history")
    history_id = _cott_validate_abi(history_id, U64, path="$.history_id")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/history/delete_history_entry.py", "37618c96911e6473d6debdc8c9e13611521d1fa6c7664f40d473fe1aa0c2685b", "delete_history_entry", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.history.delete_history_entry")
        _result = _implementation(history, history_id)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.history.delete_history_entry"
        if _error.span is None:
            _error.span = {"end_byte":3839,"end_column":1,"end_line":106,"start_byte":3022,"start_column":1,"start_line":90}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.history.delete_history_entry", phase="implementation-call", span={"end_byte":3839,"end_column":1,"end_line":106,"start_byte":3022,"start_column":1,"start_line":90}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.history.delete_history_entry", phase="implementation-call", span={"end_byte":3839,"end_column":1,"end_line":106,"start_byte":3022,"start_column":1,"start_line":90}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[History], path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            remaining = _cott_match_value.value
            return (_cott_contract_condition((((len((remaining).locations) + 1) == len((history).locations))), "frogmouth.history.delete_history_entry", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.history.delete_history_entry", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.delete_history_entry", clause="ensures:1", phase="ensures", span={"end_byte":3529,"end_column":91,"end_line":99,"start_byte":3443,"start_column":5,"start_line":99}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Nothing:
            return (_cott_contract_condition(((history_id >= len((history).locations))), "frogmouth.history.delete_history_entry", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.history.delete_history_entry", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.delete_history_entry", clause="ensures:2", phase="ensures", span={"end_byte":3595,"end_column":66,"end_line":100,"start_byte":3534,"start_column":5,"start_line":100}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            remaining = _cott_match_value.value
            return (_cott_contract_condition((((not (history_id < (history).current)) or (((remaining).current + 1) == (history).current))), "frogmouth.history.delete_history_entry", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.history.delete_history_entry", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.delete_history_entry", clause="ensures:3", phase="ensures", span={"end_byte":3710,"end_column":115,"end_line":101,"start_byte":3600,"start_column":5,"start_line":101}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            remaining = _cott_match_value.value
            return (_cott_contract_condition((((not (history_id > (history).current)) or ((remaining).current == (history).current))), "frogmouth.history.delete_history_entry", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.history.delete_history_entry", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.delete_history_entry", clause="ensures:4", phase="ensures", span={"end_byte":3821,"end_column":111,"end_line":102,"start_byte":3715,"start_column":5,"start_line":102}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[History], path="$.return", validator=_cott_validate_abi)
    return _result

def history_entries(history: History) -> CottList[HistoryEntry]:
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
    history = _cott_validate_abi(history, History, path="$.history")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/history/history_entries.py", "c15160539affcd2a2aeff133c58a0a2d3e06efa8bd77733543e4c672bf87087c", "history_entries", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.history.history_entries")
        _result = _implementation(history)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.history.history_entries"
        if _error.span is None:
            _error.span = {"end_byte":4743,"end_column":1,"end_line":125,"start_byte":3839,"start_column":1,"start_line":106}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.history.history_entries", phase="implementation-call", span={"end_byte":4743,"end_column":1,"end_line":125,"start_byte":3839,"start_column":1,"start_line":106}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.history.history_entries", phase="implementation-call", span={"end_byte":4743,"end_column":1,"end_line":125,"start_byte":3839,"start_column":1,"start_line":106}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[HistoryEntry], path="$.return")
    if not (_cott_contract_condition(((len(_result) == len((history).locations))), "frogmouth.history.history_entries", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.history.history_entries", clause="ensures:1", phase="ensures", span={"end_byte":4725,"end_column":48,"end_line":121,"start_byte":4682,"start_column":5,"start_line":121}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[HistoryEntry], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["History", "HistoryEntry", "MAXIMUM_HISTORY_LENGTH", "current_location", "delete_history_entry", "history_entries", "remember_location", "start_history", "step_back", "step_forward"]
