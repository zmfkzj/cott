from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from frogmouth.persistence_types import StateError, StateError_InvalidData, StateError_IoFailure, StateError_PermissionDenied
from frogmouth.model_types import BrowserState, StateAction

def add_history(history: CottList[str], location: str, history_limit: U64) -> CottList[str]:
    history = _cott_validate_abi(history, CottList[str], path="$.history")
    location = _cott_validate_abi(location, str, path="$.location")
    history_limit = _cott_validate_abi(history_limit, U64, path="$.history_limit")
    if not ((history_limit > 0)):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.persistence.add_history", clause="requires:0", phase="requires", span={"end_byte":312,"end_column":31,"end_line":11,"start_byte":286,"start_column":5,"start_line":11}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/persistence/add_history.py", "16f5663e1c1cca70b0a642e9f858916d3ab87105cf13b55a5dc266b7c12e9013", "add_history", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.persistence.add_history")
        _result = _implementation(history, location, history_limit)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.persistence.add_history"
        if _error.span is None:
            _error.span = {"end_byte":435,"end_column":1,"end_line":16,"start_byte":198,"start_column":1,"start_line":10}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.persistence.add_history", phase="implementation-call", span={"end_byte":435,"end_column":1,"end_line":16,"start_byte":198,"start_column":1,"start_line":10}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.persistence.add_history", phase="implementation-call", span={"end_byte":435,"end_column":1,"end_line":16,"start_byte":198,"start_column":1,"start_line":10}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[str], path="$.return")
    if not (((len(location) != 0) or (len(_result) == len(history)))):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.persistence.add_history", clause="ensures:1", phase="ensures", span={"end_byte":372,"end_column":59,"end_line":13,"start_byte":318,"start_column":5,"start_line":13}, expected="true", actual="false")
    if not (((len(location) == 0) or (len(_result) <= history_limit))):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.persistence.add_history", clause="ensures:2", phase="ensures", span={"end_byte":433,"end_column":61,"end_line":14,"start_byte":377,"start_column":5,"start_line":14}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=_cott_validate_abi)
    return _result

def toggle_bookmark(bookmarks: CottList[str], location: str) -> CottList[str]:
    bookmarks = _cott_validate_abi(bookmarks, CottList[str], path="$.bookmarks")
    location = _cott_validate_abi(location, str, path="$.location")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/persistence/toggle_bookmark.py", "a34ea430646c9a0921a9f6aebba5163a3ea466188e53d42b6ed4d641f83fc776", "toggle_bookmark", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.persistence.toggle_bookmark")
        _result = _implementation(bookmarks, location)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.persistence.toggle_bookmark"
        if _error.span is None:
            _error.span = {"end_byte":550,"end_column":1,"end_line":19,"start_byte":435,"start_column":1,"start_line":16}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.persistence.toggle_bookmark", phase="implementation-call", span={"end_byte":550,"end_column":1,"end_line":19,"start_byte":435,"start_column":1,"start_line":16}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.persistence.toggle_bookmark", phase="implementation-call", span={"end_byte":550,"end_column":1,"end_line":19,"start_byte":435,"start_column":1,"start_line":16}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[str], path="$.return")
    if not ((len(_result) <= (len(bookmarks) + 1))):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.persistence.toggle_bookmark", clause="ensures:0", phase="ensures", span={"end_byte":548,"end_column":44,"end_line":17,"start_byte":509,"start_column":5,"start_line":17}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=_cott_validate_abi)
    return _result

def remove_history(history: CottList[str], location: str) -> CottList[str]:
    history = _cott_validate_abi(history, CottList[str], path="$.history")
    location = _cott_validate_abi(location, str, path="$.location")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/persistence/remove_history.py", "7c1fd9a60595942191231a5ea4377400a0f6fb85d1f54be8c36a1e034fa264dd", "remove_history", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.persistence.remove_history")
        _result = _implementation(history, location)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.persistence.remove_history"
        if _error.span is None:
            _error.span = {"end_byte":656,"end_column":1,"end_line":22,"start_byte":550,"start_column":1,"start_line":19}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.persistence.remove_history", phase="implementation-call", span={"end_byte":656,"end_column":1,"end_line":22,"start_byte":550,"start_column":1,"start_line":19}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.persistence.remove_history", phase="implementation-call", span={"end_byte":656,"end_column":1,"end_line":22,"start_byte":550,"start_column":1,"start_line":19}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[str], path="$.return")
    if not ((len(_result) <= len(history))):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.persistence.remove_history", clause="ensures:0", phase="ensures", span={"end_byte":654,"end_column":38,"end_line":20,"start_byte":621,"start_column":5,"start_line":20}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=_cott_validate_abi)
    return _result

def decode_state(source: str, path: Path) -> Result[BrowserState, StateError]:
    source = _cott_validate_abi(source, str, path="$.source")
    path = _cott_validate_abi(path, Path, path="$.path")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len(source) == 0)):
        _expected_error = StateError_InvalidData
        _expected_error_span = {"end_byte":880,"end_column":54,"end_line":25,"start_byte":831,"start_column":5,"start_line":25}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/persistence/decode_state.py", "e867322078d5a8158bf4a00765d045d5ac81839b0f8a4aedf2e7c0fa20eb8d35", "decode_state", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.persistence.decode_state")
        _result = _implementation(source, path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.persistence.decode_state"
        if _error.span is None:
            _error.span = {"end_byte":915,"end_column":1,"end_line":28,"start_byte":656,"start_column":1,"start_line":22}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.persistence.decode_state", phase="implementation-call", span={"end_byte":915,"end_column":1,"end_line":28,"start_byte":656,"start_column":1,"start_line":22}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.persistence.decode_state", phase="implementation-call", span={"end_byte":915,"end_column":1,"end_line":28,"start_byte":656,"start_column":1,"start_line":22}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[BrowserState, StateError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.persistence.decode_state", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (StateError_InvalidData,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.persistence.decode_state", phase="error", span={"end_byte":915,"end_column":1,"end_line":28,"start_byte":656,"start_column":1,"start_line":22}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.persistence.decode_state", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            decoded = _cott_match_value.value
            return (((len((decoded).history) + len((decoded).bookmarks)) <= len(source)))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.persistence.decode_state", clause="ensures:0", phase="ensures", span={"end_byte":825,"end_column":92,"end_line":23,"start_byte":738,"start_column":5,"start_line":23}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[BrowserState, StateError], path="$.return", validator=_cott_validate_abi)
    return _result

def encode_state(current: BrowserState) -> str:
    current = _cott_validate_abi(current, BrowserState, path="$.current")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/persistence/encode_state.py", "94d86913ceafef3a4037b1f560bc9e6b1240d5d40f4e6e81254a09eaf58c77e0", "encode_state", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.persistence.encode_state")
        _result = _implementation(current)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.persistence.encode_state"
        if _error.span is None:
            _error.span = {"end_byte":990,"end_column":1,"end_line":31,"start_byte":915,"start_column":1,"start_line":28}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.persistence.encode_state", phase="implementation-call", span={"end_byte":990,"end_column":1,"end_line":31,"start_byte":915,"start_column":1,"start_line":28}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.persistence.encode_state", phase="implementation-call", span={"end_byte":990,"end_column":1,"end_line":31,"start_byte":915,"start_column":1,"start_line":28}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not ((len(_result) > 0)):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.persistence.encode_state", clause="ensures:0", phase="ensures", span={"end_byte":988,"end_column":27,"end_line":29,"start_byte":966,"start_column":5,"start_line":29}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def update_state(current: BrowserState, action: StateAction, history_limit: U64) -> BrowserState:
    current = _cott_validate_abi(current, BrowserState, path="$.current")
    action = _cott_validate_abi(action, StateAction, path="$.action")
    history_limit = _cott_validate_abi(history_limit, U64, path="$.history_limit")
    if not ((history_limit > 0)):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.persistence.update_state", clause="requires:0", phase="requires", span={"end_byte":1117,"end_column":31,"end_line":32,"start_byte":1091,"start_column":5,"start_line":32}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/persistence/update_state.py", "10c1ce6a4324a8e66fc1580457026102a75586eeb1eae789da155c58b393e37d", "update_state", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.persistence.update_state")
        _result = _implementation(current, action, history_limit)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.persistence.update_state"
        if _error.span is None:
            _error.span = {"end_byte":1178,"end_column":1,"end_line":36,"start_byte":990,"start_column":1,"start_line":31}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.persistence.update_state", phase="implementation-call", span={"end_byte":1178,"end_column":1,"end_line":36,"start_byte":990,"start_column":1,"start_line":31}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.persistence.update_state", phase="implementation-call", span={"end_byte":1178,"end_column":1,"end_line":36,"start_byte":990,"start_column":1,"start_line":31}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, BrowserState, path="$.return")
    if not ((len((_result).history) <= (len((current).history) + 1))):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.persistence.update_state", clause="ensures:1", phase="ensures", span={"end_byte":1176,"end_column":58,"end_line":34,"start_byte":1123,"start_column":5,"start_line":34}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, BrowserState, path="$.return", validator=_cott_validate_abi)
    return _result

def load_state(path: Path) -> Result[BrowserState, StateError]:
    path = _cott_validate_abi(path, Path, path="$.path")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/persistence/load_state.py", "2d9c29aad736f4eb3e7db901ec083b841ec1b4bd3c6bb974ece13dede39f39a7", "load_state", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.persistence.load_state")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.persistence.load_state"
        if _error.span is None:
            _error.span = {"end_byte":1408,"end_column":1,"end_line":45,"start_byte":1178,"start_column":1,"start_line":36}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.persistence.load_state", phase="implementation-call", span={"end_byte":1408,"end_column":1,"end_line":45,"start_byte":1178,"start_column":1,"start_line":36}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.persistence.load_state", phase="implementation-call", span={"end_byte":1408,"end_column":1,"end_line":45,"start_byte":1178,"start_column":1,"start_line":36}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[BrowserState, StateError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.persistence.load_state", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (StateError_PermissionDenied, StateError_InvalidData, StateError_IoFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.persistence.load_state", phase="error", span={"end_byte":1408,"end_column":1,"end_line":45,"start_byte":1178,"start_column":1,"start_line":36}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.persistence.load_state", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            loaded = _cott_match_value.value
            return (True)
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.persistence.load_state", clause="ensures:0", phase="ensures", span={"end_byte":1278,"end_column":38,"end_line":37,"start_byte":1245,"start_column":5,"start_line":37}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[BrowserState, StateError], path="$.return", validator=_cott_validate_abi)
    return _result

def save_state(path: Path, current: BrowserState) -> Result[Unit, StateError]:
    path = _cott_validate_abi(path, Path, path="$.path")
    current = _cott_validate_abi(current, BrowserState, path="$.current")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/persistence/save_state.py", "d9abfd49db8fe503343bb84a7d1bfef5b348f53efe7f253e4f46742642893ac0", "save_state", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.persistence.save_state")
        _result = _implementation(path, current)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.persistence.save_state"
        if _error.span is None:
            _error.span = {"end_byte":1619,"end_column":1,"end_line":52,"start_byte":1408,"start_column":1,"start_line":45}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.persistence.save_state", phase="implementation-call", span={"end_byte":1619,"end_column":1,"end_line":52,"start_byte":1408,"start_column":1,"start_line":45}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.persistence.save_state", phase="implementation-call", span={"end_byte":1619,"end_column":1,"end_line":52,"start_byte":1408,"start_column":1,"start_line":45}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, StateError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.persistence.save_state", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (StateError_PermissionDenied, StateError_IoFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.persistence.save_state", phase="error", span={"end_byte":1619,"end_column":1,"end_line":52,"start_byte":1408,"start_column":1,"start_line":45}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.persistence.save_state", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            saved = _cott_match_value.value
            return (True)
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.persistence.save_state", clause="ensures:0", phase="ensures", span={"end_byte":1522,"end_column":37,"end_line":46,"start_byte":1490,"start_column":5,"start_line":46}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, StateError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["StateError", "StateError_InvalidData", "StateError_IoFailure", "StateError_PermissionDenied", "add_history", "decode_state", "encode_state", "load_state", "remove_history", "save_state", "toggle_bookmark", "update_state"]
