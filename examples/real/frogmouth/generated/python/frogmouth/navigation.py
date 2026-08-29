from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from frogmouth.navigation_types import NavigationError, NavigationError_EmptyInput, NavigationError_InvalidLocation, NavigationError_MissingBase, NavigationError_UnsupportedScheme
from frogmouth.model_types import Location

def normalize_location_input(value: str) -> Result[str, NavigationError]:
    value = _cott_validate_abi(value, str, path="$.value")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len(value) == 0)):
        _expected_error = NavigationError_EmptyInput
        _expected_error_span = {"end_byte":382,"end_column":57,"end_line":14,"start_byte":330,"start_column":5,"start_line":14}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/navigation/normalize_location_input.py", "824a5c09ca21178fee46d88c61b09c91ffc6364c6a8bed2c4d721fe336e30348", "normalize_location_input", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.navigation.normalize_location_input")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.navigation.normalize_location_input"
        if _error.span is None:
            _error.span = {"end_byte":421,"end_column":1,"end_line":17,"start_byte":196,"start_column":1,"start_line":11}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.navigation.normalize_location_input", phase="implementation-call", span={"end_byte":421,"end_column":1,"end_line":17,"start_byte":196,"start_column":1,"start_line":11}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.navigation.normalize_location_input", phase="implementation-call", span={"end_byte":421,"end_column":1,"end_line":17,"start_byte":196,"start_column":1,"start_line":11}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, NavigationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.navigation.normalize_location_input", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (NavigationError_EmptyInput,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.navigation.normalize_location_input", phase="error", span={"end_byte":421,"end_column":1,"end_line":17,"start_byte":196,"start_column":1,"start_line":11}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.navigation.normalize_location_input", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            normalized = _cott_match_value.value
            return ((len(normalized) > 0))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.navigation.normalize_location_input", clause="ensures:0", phase="ensures", span={"end_byte":324,"end_column":56,"end_line":12,"start_byte":273,"start_column":5,"start_line":12}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, NavigationError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_forge_location(value: str) -> Result[Location, NavigationError]:
    value = _cott_validate_abi(value, str, path="$.value")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len(value) == 0)):
        _expected_error = NavigationError_InvalidLocation
        _expected_error_span = {"end_byte":618,"end_column":62,"end_line":20,"start_byte":561,"start_column":5,"start_line":20}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/navigation/resolve_forge_location.py", "3161b6c000b4d57d50f3a8635c536420a540b45276984fafbf36f85502a9fba9", "resolve_forge_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.navigation.resolve_forge_location")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.navigation.resolve_forge_location"
        if _error.span is None:
            _error.span = {"end_byte":662,"end_column":1,"end_line":23,"start_byte":421,"start_column":1,"start_line":17}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.navigation.resolve_forge_location", phase="implementation-call", span={"end_byte":662,"end_column":1,"end_line":23,"start_byte":421,"start_column":1,"start_line":17}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.navigation.resolve_forge_location", phase="implementation-call", span={"end_byte":662,"end_column":1,"end_line":23,"start_byte":421,"start_column":1,"start_line":17}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Location, NavigationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.navigation.resolve_forge_location", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (NavigationError_InvalidLocation,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.navigation.resolve_forge_location", phase="error", span={"end_byte":662,"end_column":1,"end_line":23,"start_byte":421,"start_column":1,"start_line":17}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.navigation.resolve_forge_location", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            location = _cott_match_value.value
            return ((len((location).target) > 0))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.navigation.resolve_forge_location", clause="ensures:0", phase="ensures", span={"end_byte":555,"end_column":59,"end_line":18,"start_byte":501,"start_column":5,"start_line":18}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Location, NavigationError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_absolute_location(value: str) -> Result[Location, NavigationError]:
    value = _cott_validate_abi(value, str, path="$.value")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len(value) == 0)):
        _expected_error = NavigationError_InvalidLocation
        _expected_error_span = {"end_byte":906,"end_column":62,"end_line":27,"start_byte":849,"start_column":5,"start_line":27}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/navigation/resolve_absolute_location.py", "3e55f3c70e50965d78f9ec41f48c45c7bb42832d13e056f238d84445b710df8f", "resolve_absolute_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.navigation.resolve_absolute_location")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.navigation.resolve_absolute_location"
        if _error.span is None:
            _error.span = {"end_byte":950,"end_column":1,"end_line":30,"start_byte":662,"start_column":1,"start_line":23}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.navigation.resolve_absolute_location", phase="implementation-call", span={"end_byte":950,"end_column":1,"end_line":30,"start_byte":662,"start_column":1,"start_line":23}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.navigation.resolve_absolute_location", phase="implementation-call", span={"end_byte":950,"end_column":1,"end_line":30,"start_byte":662,"start_column":1,"start_line":23}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Location, NavigationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.navigation.resolve_absolute_location", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (NavigationError_UnsupportedScheme, NavigationError_InvalidLocation,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.navigation.resolve_absolute_location", phase="error", span={"end_byte":950,"end_column":1,"end_line":30,"start_byte":662,"start_column":1,"start_line":23}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.navigation.resolve_absolute_location", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            location = _cott_match_value.value
            return ((len((location).target) > 0))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.navigation.resolve_absolute_location", clause="ensures:0", phase="ensures", span={"end_byte":799,"end_column":59,"end_line":24,"start_byte":745,"start_column":5,"start_line":24}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Location, NavigationError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_relative_location(value: str, base: Option[Location], working_directory: Path) -> Result[Location, NavigationError]:
    value = _cott_validate_abi(value, str, path="$.value")
    base = _cott_validate_abi(base, Option[Location], path="$.base")
    working_directory = _cott_validate_abi(working_directory, Path, path="$.working_directory")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len(value) == 0)):
        _expected_error = NavigationError_InvalidLocation
        _expected_error_span = {"end_byte":1252,"end_column":62,"end_line":38,"start_byte":1195,"start_column":5,"start_line":38}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/navigation/resolve_relative_location.py", "44be834165338256c8575481346028c1099a8cb318fe083d9727fd60000c61de", "resolve_relative_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.navigation.resolve_relative_location")
        _result = _implementation(value, base, working_directory)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.navigation.resolve_relative_location"
        if _error.span is None:
            _error.span = {"end_byte":1296,"end_column":1,"end_line":41,"start_byte":950,"start_column":1,"start_line":30}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.navigation.resolve_relative_location", phase="implementation-call", span={"end_byte":1296,"end_column":1,"end_line":41,"start_byte":950,"start_column":1,"start_line":30}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.navigation.resolve_relative_location", phase="implementation-call", span={"end_byte":1296,"end_column":1,"end_line":41,"start_byte":950,"start_column":1,"start_line":30}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Location, NavigationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.navigation.resolve_relative_location", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (NavigationError_MissingBase, NavigationError_InvalidLocation,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.navigation.resolve_relative_location", phase="error", span={"end_byte":1296,"end_column":1,"end_line":41,"start_byte":950,"start_column":1,"start_line":30}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.navigation.resolve_relative_location", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            location = _cott_match_value.value
            return ((len((location).target) > 0))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.navigation.resolve_relative_location", clause="ensures:0", phase="ensures", span={"end_byte":1151,"end_column":59,"end_line":35,"start_byte":1097,"start_column":5,"start_line":35}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Location, NavigationError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_location(value: str, base: Option[Location], working_directory: Path) -> Result[Location, NavigationError]:
    value = _cott_validate_abi(value, str, path="$.value")
    base = _cott_validate_abi(base, Option[Location], path="$.base")
    working_directory = _cott_validate_abi(working_directory, Path, path="$.working_directory")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len(value) == 0)):
        _expected_error = NavigationError_EmptyInput
        _expected_error_span = {"end_byte":1546,"end_column":57,"end_line":48,"start_byte":1494,"start_column":5,"start_line":48}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/navigation/resolve_location.py", "4eac16f569a7a82f1ac802f1c503db6c474662114c3750f3e7d3d7acf7ffe49c", "resolve_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.navigation.resolve_location")
        _result = _implementation(value, base, working_directory)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.navigation.resolve_location"
        if _error.span is None:
            _error.span = {"end_byte":1709,"end_column":1,"end_line":54,"start_byte":1296,"start_column":1,"start_line":41}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.navigation.resolve_location", phase="implementation-call", span={"end_byte":1709,"end_column":1,"end_line":54,"start_byte":1296,"start_column":1,"start_line":41}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.navigation.resolve_location", phase="implementation-call", span={"end_byte":1709,"end_column":1,"end_line":54,"start_byte":1296,"start_column":1,"start_line":41}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Location, NavigationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.navigation.resolve_location", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (NavigationError_EmptyInput, NavigationError_MissingBase, NavigationError_UnsupportedScheme, NavigationError_InvalidLocation,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.navigation.resolve_location", phase="error", span={"end_byte":1709,"end_column":1,"end_line":54,"start_byte":1296,"start_column":1,"start_line":41}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.navigation.resolve_location", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            location = _cott_match_value.value
            return ((len((location).target) > 0))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.navigation.resolve_location", clause="ensures:0", phase="ensures", span={"end_byte":1488,"end_column":59,"end_line":46,"start_byte":1434,"start_column":5,"start_line":46}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Location, NavigationError], path="$.return", validator=_cott_validate_abi)
    return _result

def normalization_is_ok(result: Result[str, NavigationError]) -> bool:
    """Report whether location normalization succeeded."""
    result = _cott_validate_abi(result, Result[str, NavigationError], path="$.result")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/navigation/normalization_is_ok.py", "b26954e4a10003b60c19c0cd1a099153873c59544fbab3ace81e5f1df8f4ab37", "normalization_is_ok", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.navigation.normalization_is_ok")
        _result = _implementation(result)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.navigation.normalization_is_ok"
        if _error.span is None:
            _error.span = {"end_byte":1853,"end_column":1,"end_line":59,"start_byte":1709,"start_column":1,"start_line":54}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.navigation.normalization_is_ok", phase="implementation-call", span={"end_byte":1853,"end_column":1,"end_line":59,"start_byte":1709,"start_column":1,"start_line":54}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.navigation.normalization_is_ok", phase="implementation-call", span={"end_byte":1853,"end_column":1,"end_line":59,"start_byte":1709,"start_column":1,"start_line":54}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, bool, path="$.return")
    _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=_cott_validate_abi)
    return _result

def location_resolution_is_ok(result: Result[Location, NavigationError]) -> bool:
    """Report whether location resolution succeeded."""
    result = _cott_validate_abi(result, Result[Location, NavigationError], path="$.result")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/navigation/location_resolution_is_ok.py", "631b041667e851f33eb081c39e2e2dabdacf68e046fd06fa9e690856596ce4a0", "location_resolution_is_ok", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.navigation.location_resolution_is_ok")
        _result = _implementation(result)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.navigation.location_resolution_is_ok"
        if _error.span is None:
            _error.span = {"end_byte":2005,"end_column":1,"end_line":64,"start_byte":1853,"start_column":1,"start_line":59}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.navigation.location_resolution_is_ok", phase="implementation-call", span={"end_byte":2005,"end_column":1,"end_line":64,"start_byte":1853,"start_column":1,"start_line":59}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.navigation.location_resolution_is_ok", phase="implementation-call", span={"end_byte":2005,"end_column":1,"end_line":64,"start_byte":1853,"start_column":1,"start_line":59}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, bool, path="$.return")
    _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=_cott_validate_abi)
    return _result

def display_location(location: Location) -> str:
    location = _cott_validate_abi(location, Location, path="$.location")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/navigation/display_location.py", "c137cedac3dff407705e0bdf2398e019752d4401947a0b5d31688001f206c344", "display_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.navigation.display_location")
        _result = _implementation(location)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.navigation.display_location"
        if _error.span is None:
            _error.span = {"end_byte":2081,"end_column":1,"end_line":67,"start_byte":2005,"start_column":1,"start_line":64}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.navigation.display_location", phase="implementation-call", span={"end_byte":2081,"end_column":1,"end_line":67,"start_byte":2005,"start_column":1,"start_line":64}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.navigation.display_location", phase="implementation-call", span={"end_byte":2081,"end_column":1,"end_line":67,"start_byte":2005,"start_column":1,"start_line":64}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not ((len(_result) > 0)):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.navigation.display_location", clause="ensures:0", phase="ensures", span={"end_byte":2079,"end_column":27,"end_line":65,"start_byte":2057,"start_column":5,"start_line":65}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["NavigationError", "NavigationError_EmptyInput", "NavigationError_InvalidLocation", "NavigationError_MissingBase", "NavigationError_UnsupportedScheme", "display_location", "location_resolution_is_ok", "normalization_is_ok", "normalize_location_input", "resolve_absolute_location", "resolve_forge_location", "resolve_location", "resolve_relative_location"]
