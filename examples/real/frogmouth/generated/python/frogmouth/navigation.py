from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from frogmouth.navigation_types import NavigationError, NavigationError_EmptyInput, NavigationError_UnsupportedScheme
from frogmouth.model_types import Location

def resolve_location(value: str, working_directory: Path) -> Result[Location, NavigationError]:
    """Return LocationKind.Http for HTTP(S); otherwise return an absolute LocationKind.Local path."""
    value = _cott_validate_abi(value, str, path="$.value")
    working_directory = _cott_validate_abi(working_directory, Path, path="$.working_directory")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/navigation/resolve_location.py", "95a090fa1ec6ef714e0104e911d9255968eab4067ee5184e7e60406a643e2014", "resolve_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.navigation.resolve_location")
        _result = _implementation(value, working_directory)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.navigation.resolve_location"
        if _error.span is None:
            _error.span = {"end_byte":518,"end_column":1,"end_line":21,"start_byte":148,"start_column":1,"start_line":9}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.navigation.resolve_location", phase="implementation-call", span={"end_byte":518,"end_column":1,"end_line":21,"start_byte":148,"start_column":1,"start_line":9}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.navigation.resolve_location", phase="implementation-call", span={"end_byte":518,"end_column":1,"end_line":21,"start_byte":148,"start_column":1,"start_line":9}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Location, NavigationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.navigation.resolve_location", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (NavigationError_EmptyInput, NavigationError_UnsupportedScheme,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.navigation.resolve_location", phase="error", span={"end_byte":518,"end_column":1,"end_line":21,"start_byte":148,"start_column":1,"start_line":9}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.navigation.resolve_location", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            location = _cott_match_value.value
            return ((len((location).target) > 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.navigation.resolve_location", clause="ensures:1", phase="ensures", span={"end_byte":418,"end_column":59,"end_line":14,"start_byte":364,"start_column":5,"start_line":14}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Location, NavigationError], path="$.return", validator=_cott_validate_abi)
    return _result

def display_location(location: Location) -> str:
    location = _cott_validate_abi(location, Location, path="$.location")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/navigation/display_location.py", "08bafd3a41930c309efddab2f5399adabf02ccc88e730a4b057c3607337eac1a", "display_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.navigation.display_location")
        _result = _implementation(location)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.navigation.display_location"
        if _error.span is None:
            _error.span = {"end_byte":609,"end_column":1,"end_line":25,"start_byte":518,"start_column":1,"start_line":21}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.navigation.display_location", phase="implementation-call", span={"end_byte":609,"end_column":1,"end_line":25,"start_byte":518,"start_column":1,"start_line":21}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.navigation.display_location", phase="implementation-call", span={"end_byte":609,"end_column":1,"end_line":25,"start_byte":518,"start_column":1,"start_line":21}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not ((len(_result) > 0)):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.navigation.display_location", clause="ensures:0", phase="ensures", span={"end_byte":592,"end_column":27,"end_line":22,"start_byte":570,"start_column":5,"start_line":22}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["NavigationError", "NavigationError_EmptyInput", "NavigationError_UnsupportedScheme", "display_location", "resolve_location"]
