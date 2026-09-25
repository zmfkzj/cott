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

from frogmouth.navigation_types import NavigationError, NavigationError_EmptyInput, NavigationError_UnsupportedScheme
from frogmouth.model_types import Location, LocationKind, LocationKind_Http, LocationKind_Local

def resolve_location(value: str, working_directory: Path) -> Result[Location, NavigationError]:
    """Classify address-bar input exactly as typed; it is not trimmed. A value
starting with "http://" or "https://" is an Http location whose target is the
value. Any other value containing "://" is UnsupportedScheme whose scheme is
the text before the first "://". Every other non-empty value is a Local
location: a value starting with "/" is the target unchanged; otherwise the
target is the text of working_directory, one "/" (omitted when that text
already ends with "/") and the value. Local targets are not normalized,
"~"-expanded or checked for existence. The browser passes the process's
absolute working directory."""
    value = _cott_validate_abi(value, str, path="$.value")
    working_directory = _cott_validate_abi(working_directory, Path, path="$.working_directory")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((value == "")), "frogmouth.navigation.resolve_location", "error:7:condition")):
        _expected_error = NavigationError_EmptyInput
        _expected_error_span = {"end_byte":1527,"end_column":54,"end_line":29,"start_byte":1478,"start_column":5,"start_line":29}
        _expected_error_clause = "error:7"
    if _expected_error is None and (_cott_contract_condition(((("://" in value) and (not (_cott_starts_with(value, "http://") or _cott_starts_with(value, "https://"))))), "frogmouth.navigation.resolve_location", "error:8:condition")):
        _expected_error = NavigationError_UnsupportedScheme
        _expected_error_span = {"end_byte":1675,"end_column":148,"end_line":30,"start_byte":1532,"start_column":5,"start_line":30}
        _expected_error_clause = "error:8"
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/navigation/resolve_location.py", "d63312202e7177e5e1fb849b65d4fa612a99b9d1643960fa4b4d9f9a7496e080", "resolve_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.navigation.resolve_location")
        _result = _implementation(value, working_directory)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.navigation.resolve_location"
        if _error.span is None:
            _error.span = {"end_byte":1693,"end_column":1,"end_line":34,"start_byte":148,"start_column":1,"start_line":9}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.navigation.resolve_location", phase="implementation-call", span={"end_byte":1693,"end_column":1,"end_line":34,"start_byte":148,"start_column":1,"start_line":9}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.navigation.resolve_location", phase="implementation-call", span={"end_byte":1693,"end_column":1,"end_line":34,"start_byte":148,"start_column":1,"start_line":9}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Location, NavigationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.navigation.resolve_location", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.navigation.resolve_location", phase="error", span={"end_byte":1693,"end_column":1,"end_line":34,"start_byte":148,"start_column":1,"start_line":9}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.navigation.resolve_location", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "frogmouth.navigation.resolve_location", _expected_error_clause)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            location = _cott_match_value.value
            return (_cott_contract_condition((((not (_cott_starts_with(value, "http://") or _cott_starts_with(value, "https://"))) or ((location).kind == LocationKind_Http()))), "frogmouth.navigation.resolve_location", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.navigation.resolve_location", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.navigation.resolve_location", clause="ensures:1", phase="ensures", span={"end_byte":1057,"end_column":139,"end_line":22,"start_byte":923,"start_column":5,"start_line":22}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            location = _cott_match_value.value
            return (_cott_contract_condition((((not ((location).kind == LocationKind_Http())) or ((location).target == value))), "frogmouth.navigation.resolve_location", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.navigation.resolve_location", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.navigation.resolve_location", clause="ensures:2", phase="ensures", span={"end_byte":1157,"end_column":100,"end_line":23,"start_byte":1062,"start_column":5,"start_line":23}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            location = _cott_match_value.value
            return (_cott_contract_condition((((not ((location).kind == LocationKind_Local())) or _cott_ends_with((location).target, value))), "frogmouth.navigation.resolve_location", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.navigation.resolve_location", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.navigation.resolve_location", clause="ensures:3", phase="ensures", span={"end_byte":1267,"end_column":110,"end_line":24,"start_byte":1162,"start_column":5,"start_line":24}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            location = _cott_match_value.value
            return (_cott_contract_condition((((not _cott_starts_with(value, "/")) or ((location).target == value))), "frogmouth.navigation.resolve_location", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.navigation.resolve_location", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.navigation.resolve_location", clause="ensures:4", phase="ensures", span={"end_byte":1356,"end_column":89,"end_line":25,"start_byte":1272,"start_column":5,"start_line":25}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is NavigationError_UnsupportedScheme and True:
            scheme = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition((_cott_starts_with(value, scheme)), "frogmouth.navigation.resolve_location", "ensures:5"))
        _cott_contract_condition((False), "frogmouth.navigation.resolve_location", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.navigation.resolve_location", clause="ensures:5", phase="ensures", span={"end_byte":1452,"end_column":96,"end_line":26,"start_byte":1361,"start_column":5,"start_line":26}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Location, NavigationError], path="$.return", validator=_cott_validate_abi)
    return _result

def display_location(location: Location) -> str:
    """Address-bar text for a loaded location; reload passes it back to
frogmouth.navigation.resolve_location."""
    location = _cott_validate_abi(location, Location, path="$.location")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/navigation/display_location.py", "fb86541a72fff1945386b9ed76b3f89975cc0424b1ec915fb7de6d3c0569c807", "display_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.navigation.display_location")
        _result = _implementation(location)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.navigation.display_location"
        if _error.span is None:
            _error.span = {"end_byte":1928,"end_column":1,"end_line":43,"start_byte":1693,"start_column":1,"start_line":34}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.navigation.display_location", phase="implementation-call", span={"end_byte":1928,"end_column":1,"end_line":43,"start_byte":1693,"start_column":1,"start_line":34}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.navigation.display_location", phase="implementation-call", span={"end_byte":1928,"end_column":1,"end_line":43,"start_byte":1693,"start_column":1,"start_line":34}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not (_cott_contract_condition(((_result == (location).target)), "frogmouth.navigation.display_location", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.navigation.display_location", clause="ensures:1", phase="ensures", span={"end_byte":1911,"end_column":38,"end_line":40,"start_byte":1878,"start_column":5,"start_line":40}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["NavigationError", "NavigationError_EmptyInput", "NavigationError_UnsupportedScheme", "display_location", "resolve_location"]
