from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from frogmouth.layout_types import CycleDirection, CycleDirection_Next, CycleDirection_Previous, EscapeAction, EscapeAction_ClearAddress, EscapeAction_FocusAddress, EscapeAction_HideSidebarAndFocusAddress, EscapeAction_Quit, Focus, Focus_AddressBar, Focus_Document, Focus_Sidebar, Pane, Pane_Bookmarks, Pane_Contents, Pane_History, Pane_Local, Sidebar, Visibility, Visibility_Hidden, Visibility_Shown

def toggle_pane(sidebar: Sidebar, pane: Pane) -> Sidebar:
    """The pane shortcuts (Ctrl+T, Ctrl+L, Ctrl+B, Ctrl+Y and the contents,
local, bookmarks and history commands) toggle: requesting the pane that
is already shown hides the sidebar, any other request shows the sidebar
with pane active."""
    sidebar = _cott_validate_abi(sidebar, Sidebar, path="$.sidebar")
    pane = _cott_validate_abi(pane, Pane, path="$.pane")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/layout/toggle_pane.py", "e50141c96a0b70d46966f7a80bdbada481b723eb5206d233b6d4b9cc20a78100", "toggle_pane", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.layout.toggle_pane")
        _result = _implementation(sidebar, pane)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.layout.toggle_pane"
        if _error.span is None:
            _error.span = {"end_byte":1273,"end_column":1,"end_line":56,"start_byte":640,"start_column":1,"start_line":42}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.layout.toggle_pane", phase="implementation-call", span={"end_byte":1273,"end_column":1,"end_line":56,"start_byte":640,"start_column":1,"start_line":42}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.layout.toggle_pane", phase="implementation-call", span={"end_byte":1273,"end_column":1,"end_line":56,"start_byte":640,"start_column":1,"start_line":42}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Sidebar, path="$.return")
    if not (_cott_contract_condition((((_result).active == pane)), "frogmouth.layout.toggle_pane", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.layout.toggle_pane", clause="ensures:1", phase="ensures", span={"end_byte":998,"end_column":34,"end_line":50,"start_byte":969,"start_column":5,"start_line":50}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (((sidebar).visibility == Visibility_Shown()) and ((sidebar).active == pane))) or ((_result).visibility == Visibility_Hidden()))), "frogmouth.layout.toggle_pane", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.layout.toggle_pane", clause="ensures:2", phase="ensures", span={"end_byte":1124,"end_column":126,"end_line":51,"start_byte":1003,"start_column":5,"start_line":51}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (not (((sidebar).visibility == Visibility_Shown()) and ((sidebar).active == pane)))) or ((_result).visibility == Visibility_Shown()))), "frogmouth.layout.toggle_pane", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.layout.toggle_pane", clause="ensures:3", phase="ensures", span={"end_byte":1255,"end_column":131,"end_line":52,"start_byte":1129,"start_column":5,"start_line":52}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Sidebar, path="$.return", validator=_cott_validate_abi)
    return _result

def toggle_sidebar(sidebar: Sidebar) -> Sidebar:
    """Show or hide the sidebar (Ctrl+N), keeping the active pane."""
    sidebar = _cott_validate_abi(sidebar, Sidebar, path="$.sidebar")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/layout/toggle_sidebar.py", "cde82344eed437f387a877705fc3c54f7a9c0ab66ee334e4210aea61a1b98421", "toggle_sidebar", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.layout.toggle_sidebar")
        _result = _implementation(sidebar)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.layout.toggle_sidebar"
        if _error.span is None:
            _error.span = {"end_byte":1535,"end_column":1,"end_line":66,"start_byte":1273,"start_column":1,"start_line":56}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.layout.toggle_sidebar", phase="implementation-call", span={"end_byte":1535,"end_column":1,"end_line":66,"start_byte":1273,"start_column":1,"start_line":56}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.layout.toggle_sidebar", phase="implementation-call", span={"end_byte":1535,"end_column":1,"end_line":66,"start_byte":1273,"start_column":1,"start_line":56}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Sidebar, path="$.return")
    if not (_cott_contract_condition((((_result).active == (sidebar).active)), "frogmouth.layout.toggle_sidebar", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.layout.toggle_sidebar", clause="ensures:1", phase="ensures", span={"end_byte":1465,"end_column":60,"end_line":61,"start_byte":1410,"start_column":5,"start_line":61}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).visibility != (sidebar).visibility)), "frogmouth.layout.toggle_sidebar", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.layout.toggle_sidebar", clause="ensures:2", phase="ensures", span={"end_byte":1517,"end_column":52,"end_line":62,"start_byte":1470,"start_column":5,"start_line":62}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Sidebar, path="$.return", validator=_cott_validate_abi)
    return _result

def cycle_pane(sidebar: Sidebar, direction: CycleDirection) -> Sidebar:
    """Activate the neighbouring pane in tab order, wrapping around at both
ends: Next after History is Contents and Previous before Contents is
History. Visibility is unchanged."""
    sidebar = _cott_validate_abi(sidebar, Sidebar, path="$.sidebar")
    direction = _cott_validate_abi(direction, CycleDirection, path="$.direction")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/layout/cycle_pane.py", "1f116ee2c10972d6604a8e5a1b00574148286492ef95f4daf0d4bb30354ef0fe", "cycle_pane", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.layout.cycle_pane")
        _result = _implementation(sidebar, direction)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.layout.cycle_pane"
        if _error.span is None:
            _error.span = {"end_byte":1928,"end_column":1,"end_line":78,"start_byte":1535,"start_column":1,"start_line":66}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.layout.cycle_pane", phase="implementation-call", span={"end_byte":1928,"end_column":1,"end_line":78,"start_byte":1535,"start_column":1,"start_line":66}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.layout.cycle_pane", phase="implementation-call", span={"end_byte":1928,"end_column":1,"end_line":78,"start_byte":1535,"start_column":1,"start_line":66}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Sidebar, path="$.return")
    if not (_cott_contract_condition((((_result).visibility == (sidebar).visibility)), "frogmouth.layout.cycle_pane", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.layout.cycle_pane", clause="ensures:1", phase="ensures", span={"end_byte":1866,"end_column":56,"end_line":73,"start_byte":1815,"start_column":5,"start_line":73}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).active != (sidebar).active)), "frogmouth.layout.cycle_pane", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.layout.cycle_pane", clause="ensures:2", phase="ensures", span={"end_byte":1910,"end_column":44,"end_line":74,"start_byte":1871,"start_column":5,"start_line":74}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Sidebar, path="$.return", validator=_cott_validate_abi)
    return _result

def escape_action(focus: Focus, address: str) -> EscapeAction:
    """Escape backs out of the application step by step: from the document it
focuses the address bar, from the sidebar it also hides the sidebar, in
the address bar it clears non-empty text and otherwise quits."""
    focus = _cott_validate_abi(focus, Focus, path="$.focus")
    address = _cott_validate_abi(address, str, path="$.address")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/layout/escape_action.py", "0ccaca8911a4eafb5a3977d54de7ebf32badafe95b5b699489a568cff8980cb4", "escape_action", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.layout.escape_action")
        _result = _implementation(focus, address)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.layout.escape_action"
        if _error.span is None:
            _error.span = {"end_byte":2616,"end_column":1,"end_line":92,"start_byte":1928,"start_column":1,"start_line":78}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.layout.escape_action", phase="implementation-call", span={"end_byte":2616,"end_column":1,"end_line":92,"start_byte":1928,"start_column":1,"start_line":78}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.layout.escape_action", phase="implementation-call", span={"end_byte":2616,"end_column":1,"end_line":92,"start_byte":1928,"start_column":1,"start_line":78}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, EscapeAction, path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = focus
        if type(_cott_match_value) is Focus_AddressBar:
            return (_cott_contract_condition((((not (address != "")) or (_result == EscapeAction_ClearAddress()))), "frogmouth.layout.escape_action", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.layout.escape_action", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.layout.escape_action", clause="ensures:1", phase="ensures", span={"end_byte":2330,"end_column":103,"end_line":85,"start_byte":2232,"start_column":5,"start_line":85}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = focus
        if type(_cott_match_value) is Focus_AddressBar:
            return (_cott_contract_condition((((not (address == "")) or (_result == EscapeAction_Quit()))), "frogmouth.layout.escape_action", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.layout.escape_action", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.layout.escape_action", clause="ensures:2", phase="ensures", span={"end_byte":2425,"end_column":95,"end_line":86,"start_byte":2335,"start_column":5,"start_line":86}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = focus
        if type(_cott_match_value) is Focus_Sidebar:
            return (_cott_contract_condition(((_result == EscapeAction_HideSidebarAndFocusAddress())), "frogmouth.layout.escape_action", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.layout.escape_action", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.layout.escape_action", clause="ensures:3", phase="ensures", span={"end_byte":2518,"end_column":93,"end_line":87,"start_byte":2430,"start_column":5,"start_line":87}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = focus
        if type(_cott_match_value) is Focus_Document:
            return (_cott_contract_condition(((_result == EscapeAction_FocusAddress())), "frogmouth.layout.escape_action", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.layout.escape_action", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.layout.escape_action", clause="ensures:4", phase="ensures", span={"end_byte":2598,"end_column":80,"end_line":88,"start_byte":2523,"start_column":5,"start_line":88}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, EscapeAction, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["CycleDirection", "CycleDirection_Next", "CycleDirection_Previous", "EscapeAction", "EscapeAction_ClearAddress", "EscapeAction_FocusAddress", "EscapeAction_HideSidebarAndFocusAddress", "EscapeAction_Quit", "Focus", "Focus_AddressBar", "Focus_Document", "Focus_Sidebar", "Pane", "Pane_Bookmarks", "Pane_Contents", "Pane_History", "Pane_Local", "Sidebar", "Visibility", "Visibility_Hidden", "Visibility_Shown", "cycle_pane", "escape_action", "toggle_pane", "toggle_sidebar"]
