from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from frogmouth.application_types import SIDEBAR_DOCK_LEFT, SIDEBAR_DOCK_RIGHT, SIDEBAR_HELP, SIDEBAR_HIDDEN, SIDEBAR_HISTORY, SidebarDock, SidebarDock_Left, SidebarDock_Right, SidebarMode, SidebarMode_Bookmarks, SidebarMode_Help, SidebarMode_Hidden, SidebarMode_History

def toggle_sidebar(current: SidebarMode, requested: SidebarMode) -> SidebarMode:
    current = _cott_validate_abi(current, SidebarMode, path="$.current")
    requested = _cott_validate_abi(requested, SidebarMode, path="$.requested")
    if not ((requested != SidebarMode_Hidden())):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.application.toggle_sidebar", clause="requires:0", phase="requires", span={"end_byte":257,"end_column":45,"end_line":14,"start_byte":217,"start_column":5,"start_line":14}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/application/toggle_sidebar.py", "4a9a572aa5d2a477c11129321c8942a4fdb767a8334b064421e644b17acdbe6f", "toggle_sidebar", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.application.toggle_sidebar")
        _result = _implementation(current, requested)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.application.toggle_sidebar"
        if _error.span is None:
            _error.span = {"end_byte":409,"end_column":1,"end_line":21,"start_byte":133,"start_column":1,"start_line":13}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.application.toggle_sidebar", phase="implementation-call", span={"end_byte":409,"end_column":1,"end_line":21,"start_byte":133,"start_column":1,"start_line":13}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.application.toggle_sidebar", phase="implementation-call", span={"end_byte":409,"end_column":1,"end_line":21,"start_byte":133,"start_column":1,"start_line":13}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SidebarMode, path="$.return")
    if not (((_result == SidebarMode_Hidden()) or (_result == requested))):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.application.toggle_sidebar", clause="ensures:1", phase="ensures", span={"end_byte":322,"end_column":64,"end_line":16,"start_byte":263,"start_column":5,"start_line":16}, expected="true", actual="false")
    if not (((_result == SidebarMode_Hidden()) == (current == requested))):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.application.toggle_sidebar", clause="ensures:2", phase="ensures", span={"end_byte":391,"end_column":69,"end_line":17,"start_byte":327,"start_column":5,"start_line":17}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, SidebarMode, path="$.return", validator=_cott_validate_abi)
    return _result

def toggle_sidebar_dock(current: SidebarDock) -> SidebarDock:
    current = _cott_validate_abi(current, SidebarDock, path="$.current")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/application/toggle_sidebar_dock.py", "cc52a0c9ecad9b6b725466eac0fd7bce369667311b02fb7e4f8cf5ace70bd4cf", "toggle_sidebar_dock", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.application.toggle_sidebar_dock")
        _result = _implementation(current)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.application.toggle_sidebar_dock"
        if _error.span is None:
            _error.span = {"end_byte":517,"end_column":1,"end_line":26,"start_byte":409,"start_column":1,"start_line":21}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.application.toggle_sidebar_dock", phase="implementation-call", span={"end_byte":517,"end_column":1,"end_line":26,"start_byte":409,"start_column":1,"start_line":21}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.application.toggle_sidebar_dock", phase="implementation-call", span={"end_byte":517,"end_column":1,"end_line":26,"start_byte":409,"start_column":1,"start_line":21}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SidebarDock, path="$.return")
    if not ((_result != current)):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.application.toggle_sidebar_dock", clause="ensures:0", phase="ensures", span={"end_byte":499,"end_column":30,"end_line":22,"start_byte":474,"start_column":5,"start_line":22}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, SidebarDock, path="$.return", validator=_cott_validate_abi)
    return _result

def parse_initial_location(arguments: CottList[str]) -> Option[str]:
    """Parse an optional initial location argument."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/application/parse_initial_location.py", "70fba934a2ad783bae784175db7f2185a3e584d9846a02f61cac2519ff96af97", "parse_initial_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.application.parse_initial_location")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.application.parse_initial_location"
        if _error.span is None:
            _error.span = {"end_byte":651,"end_column":1,"end_line":31,"start_byte":517,"start_column":1,"start_line":26}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.application.parse_initial_location", phase="implementation-call", span={"end_byte":651,"end_column":1,"end_line":31,"start_byte":517,"start_column":1,"start_line":26}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.application.parse_initial_location", phase="implementation-call", span={"end_byte":651,"end_column":1,"end_line":31,"start_byte":517,"start_column":1,"start_line":26}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Option[str], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_state_path(platform_name: str, home: Path, app_data: Option[str], xdg_data_home: Option[str]) -> Path:
    """Resolve the application state storage path."""
    platform_name = _cott_validate_abi(platform_name, str, path="$.platform_name")
    home = _cott_validate_abi(home, Path, path="$.home")
    app_data = _cott_validate_abi(app_data, Option[str], path="$.app_data")
    xdg_data_home = _cott_validate_abi(xdg_data_home, Option[str], path="$.xdg_data_home")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/application/resolve_state_path.py", "9ecc875d1ad18d0fa2d13b6b98b6635efc1160b6788a0e3e04b5bb7fd032924b", "resolve_state_path", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.application.resolve_state_path")
        _result = _implementation(platform_name, home, app_data, xdg_data_home)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.application.resolve_state_path"
        if _error.span is None:
            _error.span = {"end_byte":853,"end_column":1,"end_line":41,"start_byte":651,"start_column":1,"start_line":31}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.application.resolve_state_path", phase="implementation-call", span={"end_byte":853,"end_column":1,"end_line":41,"start_byte":651,"start_column":1,"start_line":31}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.application.resolve_state_path", phase="implementation-call", span={"end_byte":853,"end_column":1,"end_line":41,"start_byte":651,"start_column":1,"start_line":31}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Path, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Path, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["SIDEBAR_DOCK_LEFT", "SIDEBAR_DOCK_RIGHT", "SIDEBAR_HELP", "SIDEBAR_HIDDEN", "SIDEBAR_HISTORY", "SidebarDock", "SidebarDock_Left", "SidebarDock_Right", "SidebarMode", "SidebarMode_Bookmarks", "SidebarMode_Help", "SidebarMode_Hidden", "SidebarMode_History", "parse_initial_location", "resolve_state_path", "toggle_sidebar", "toggle_sidebar_dock"]
