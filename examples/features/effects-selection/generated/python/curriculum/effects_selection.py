from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.effects_selection_types import EffectError, EffectError_InputMissing, EffectError_OperationFailed

def read_text(source: Path) -> Result[str, EffectError]:
    """Read UTF-8 text from a compiler-owned filesystem fixture."""
    source = _cott_validate_abi(source, Path, path="$.source")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/read_text.py", "d49dc5c730538993711988053e8f517f4dbe4cbd6d85846f2171015a361b3f78", "read_text", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.read_text")
        _result = _implementation(source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.read_text"
        if _error.span is None:
            _error.span = {"end_byte":403,"end_column":1,"end_line":19,"start_byte":119,"start_column":1,"start_line":7}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.read_text", phase="implementation-call", span={"end_byte":403,"end_column":1,"end_line":19,"start_byte":119,"start_column":1,"start_line":7}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.read_text", phase="implementation-call", span={"end_byte":403,"end_column":1,"end_line":19,"start_byte":119,"start_column":1,"start_line":7}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, EffectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.effects_selection.read_text", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (EffectError_InputMissing, EffectError_OperationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.effects_selection.read_text", phase="error", span={"end_byte":403,"end_column":1,"end_line":19,"start_byte":119,"start_column":1,"start_line":7}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.effects_selection.read_text", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            text = _cott_match_value.value
            return ((len(text) >= 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.read_text", clause="ensures:1", phase="ensures", span={"end_byte":302,"end_column":45,"end_line":12,"start_byte":262,"start_column":5,"start_line":12}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, EffectError], path="$.return", validator=_cott_validate_abi)
    return _result

def copy_text(source: Path, destination: Path) -> Result[U64, EffectError]:
    """Read source through its public facade and atomically replace destination."""
    source = _cott_validate_abi(source, Path, path="$.source")
    destination = _cott_validate_abi(destination, Path, path="$.destination")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/copy_text.py", "c5ff18231a42b71f8b9196d6d7ec6989aaed91088846195d02bafaf18ce70445", "copy_text", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.copy_text")
        _result = _implementation(source, destination)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.copy_text"
        if _error.span is None:
            _error.span = {"end_byte":736,"end_column":1,"end_line":31,"start_byte":403,"start_column":1,"start_line":19}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.copy_text", phase="implementation-call", span={"end_byte":736,"end_column":1,"end_line":31,"start_byte":403,"start_column":1,"start_line":19}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.copy_text", phase="implementation-call", span={"end_byte":736,"end_column":1,"end_line":31,"start_byte":403,"start_column":1,"start_line":19}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[U64, EffectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.effects_selection.copy_text", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (EffectError_InputMissing, EffectError_OperationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.effects_selection.copy_text", phase="error", span={"end_byte":736,"end_column":1,"end_line":31,"start_byte":403,"start_column":1,"start_line":19}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.effects_selection.copy_text", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            written = _cott_match_value.value
            return ((written >= 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.copy_text", clause="ensures:1", phase="ensures", span={"end_byte":623,"end_column":47,"end_line":24,"start_byte":581,"start_column":5,"start_line":24}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[U64, EffectError], path="$.return", validator=_cott_validate_abi)
    return _result

def fetch_local(url: str) -> Result[str, EffectError]:
    """Fetch UTF-8 text from a compiler-owned local HTTP fixture."""
    url = _cott_validate_abi(url, str, path="$.url")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((url == "")):
        _expected_error = EffectError_OperationFailed
        _expected_error_span = {"end_byte":972,"end_column":53,"end_line":38,"start_byte":924,"start_column":5,"start_line":38}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/fetch_local.py", "6ed42cac122da72ab14a893e6403988a5bb6f30d24544da3fc7ed4aef0fe17db", "fetch_local", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.fetch_local")
        _result = _implementation(url)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.fetch_local"
        if _error.span is None:
            _error.span = {"end_byte":1035,"end_column":1,"end_line":43,"start_byte":736,"start_column":1,"start_line":31}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.fetch_local", phase="implementation-call", span={"end_byte":1035,"end_column":1,"end_line":43,"start_byte":736,"start_column":1,"start_line":31}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.fetch_local", phase="implementation-call", span={"end_byte":1035,"end_column":1,"end_line":43,"start_byte":736,"start_column":1,"start_line":31}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, EffectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.effects_selection.fetch_local", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (EffectError_OperationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.effects_selection.fetch_local", phase="error", span={"end_byte":1035,"end_column":1,"end_line":43,"start_byte":736,"start_column":1,"start_line":31}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.effects_selection.fetch_local", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            text = _cott_match_value.value
            return ((len(text) >= 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.fetch_local", clause="ensures:1", phase="ensures", span={"end_byte":918,"end_column":45,"end_line":36,"start_byte":878,"start_column":5,"start_line":36}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, EffectError], path="$.return", validator=_cott_validate_abi)
    return _result

def text_result_is_ok(result: Result[str, EffectError]) -> bool:
    """Return whether a text effect result is successful."""
    result = _cott_validate_abi(result, Result[str, EffectError], path="$.result")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/text_result_is_ok.py", "1f4b39025cd54974cdbdd1ef62d1d183485fab7d332b641847495a3c26aa5e6f", "text_result_is_ok", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.text_result_is_ok")
        _result = _implementation(result)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.text_result_is_ok"
        if _error.span is None:
            _error.span = {"end_byte":1175,"end_column":1,"end_line":48,"start_byte":1035,"start_column":1,"start_line":43}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.text_result_is_ok", phase="implementation-call", span={"end_byte":1175,"end_column":1,"end_line":48,"start_byte":1035,"start_column":1,"start_line":43}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.text_result_is_ok", phase="implementation-call", span={"end_byte":1175,"end_column":1,"end_line":48,"start_byte":1035,"start_column":1,"start_line":43}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, bool, path="$.return")
    _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=_cott_validate_abi)
    return _result

def text_result_text(result: Result[str, EffectError]) -> str:
    """Return successful text, or an empty string for an error result."""
    result = _cott_validate_abi(result, Result[str, EffectError], path="$.result")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/text_result_text.py", "a636df09801c8c63e565b1b061ed124f0113d02300357893720a08e43d075d18", "text_result_text", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.text_result_text")
        _result = _implementation(result)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.text_result_text"
        if _error.span is None:
            _error.span = {"end_byte":1326,"end_column":1,"end_line":53,"start_byte":1175,"start_column":1,"start_line":48}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.text_result_text", phase="implementation-call", span={"end_byte":1326,"end_column":1,"end_line":53,"start_byte":1175,"start_column":1,"start_line":48}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.text_result_text", phase="implementation-call", span={"end_byte":1326,"end_column":1,"end_line":53,"start_byte":1175,"start_column":1,"start_line":48}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def copy_result_is_ok(result: Result[U64, EffectError]) -> bool:
    """Return whether a copy effect result is successful."""
    result = _cott_validate_abi(result, Result[U64, EffectError], path="$.result")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/copy_result_is_ok.py", "a775989f6cea2667a0edf703995500ead9519a51f8137a0a2832b4654f96943f", "copy_result_is_ok", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.copy_result_is_ok")
        _result = _implementation(result)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.copy_result_is_ok"
        if _error.span is None:
            _error.span = {"end_byte":1466,"end_column":1,"end_line":58,"start_byte":1326,"start_column":1,"start_line":53}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.copy_result_is_ok", phase="implementation-call", span={"end_byte":1466,"end_column":1,"end_line":58,"start_byte":1326,"start_column":1,"start_line":53}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.copy_result_is_ok", phase="implementation-call", span={"end_byte":1466,"end_column":1,"end_line":58,"start_byte":1326,"start_column":1,"start_line":53}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, bool, path="$.return")
    _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=_cott_validate_abi)
    return _result

def store_and_load(database: Path, key: str, value: str) -> Result[str, EffectError]:
    """Store value under key in a SQLite database, then read that value back."""
    database = _cott_validate_abi(database, Path, path="$.database")
    key = _cott_validate_abi(key, str, path="$.key")
    value = _cott_validate_abi(value, str, path="$.value")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/store_and_load.py", "68635efce80fe98ea77b9dc2face364d9ca568a9e5246da55cb4df3d90fb3061", "store_and_load", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.store_and_load")
        _result = _implementation(database, key, value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.store_and_load"
        if _error.span is None:
            _error.span = {"end_byte":1781,"end_column":1,"end_line":69,"start_byte":1466,"start_column":1,"start_line":58}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.store_and_load", phase="implementation-call", span={"end_byte":1781,"end_column":1,"end_line":69,"start_byte":1466,"start_column":1,"start_line":58}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.store_and_load", phase="implementation-call", span={"end_byte":1781,"end_column":1,"end_line":69,"start_byte":1466,"start_column":1,"start_line":58}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, EffectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.effects_selection.store_and_load", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (EffectError_OperationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.effects_selection.store_and_load", phase="error", span={"end_byte":1781,"end_column":1,"end_line":69,"start_byte":1466,"start_column":1,"start_line":58}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.effects_selection.store_and_load", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            stored = _cott_match_value.value
            return ((stored == value))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.store_and_load", clause="ensures:1", phase="ensures", span={"end_byte":1695,"end_column":49,"end_line":63,"start_byte":1651,"start_column":5,"start_line":63}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, EffectError], path="$.return", validator=_cott_validate_abi)
    return _result

def clock_ns() -> U64:
    """Return a compiler-owned deterministic fixture clock in nanoseconds."""
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/clock_ns.py", "a8337c833e573162234dee1fe2d657a6a315f98f8bf4f4cf381df29fd10c494d", "clock_ns", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.clock_ns")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.clock_ns"
        if _error.span is None:
            _error.span = {"end_byte":1917,"end_column":1,"end_line":76,"start_byte":1781,"start_column":1,"start_line":69}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.clock_ns", phase="implementation-call", span={"end_byte":1917,"end_column":1,"end_line":76,"start_byte":1781,"start_column":1,"start_line":69}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.clock_ns", phase="implementation-call", span={"end_byte":1917,"end_column":1,"end_line":76,"start_byte":1781,"start_column":1,"start_line":69}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, U64, path="$.return")
    _result = _cott_wrap_async_protocol(_result, U64, path="$.return", validator=_cott_validate_abi)
    return _result

def sample_index(limit: U8, seed: U64) -> U8:
    """Choose one index below limit from a deterministic seeded random stream."""
    limit = _cott_validate_abi(limit, U8, path="$.limit")
    seed = _cott_validate_abi(seed, U64, path="$.seed")
    if not ((limit > 0)):
        raise CottContractViolation("requires clause failed", symbol="curriculum.effects_selection.sample_index", clause="requires:1", phase="requires", span={"end_byte":2081,"end_column":23,"end_line":81,"start_byte":2063,"start_column":5,"start_line":81}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/sample_index.py", "79454884c5715cdff59e8d82a15c581d2dd6b7c36bb4ba532ec97c8ec5b9c9ff", "sample_index", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.sample_index")
        _result = _implementation(limit, seed)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.sample_index"
        if _error.span is None:
            _error.span = {"end_byte":2133,"end_column":1,"end_line":87,"start_byte":1917,"start_column":1,"start_line":76}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.sample_index", phase="implementation-call", span={"end_byte":2133,"end_column":1,"end_line":87,"start_byte":1917,"start_column":1,"start_line":76}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.sample_index", phase="implementation-call", span={"end_byte":2133,"end_column":1,"end_line":87,"start_byte":1917,"start_column":1,"start_line":76}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, U8, path="$.return")
    if not ((_result < limit)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.sample_index", clause="ensures:2", phase="ensures", span={"end_byte":2109,"end_column":27,"end_line":83,"start_byte":2087,"start_column":5,"start_line":83}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, U8, path="$.return", validator=_cott_validate_abi)
    return _result

def exit_with_code(code: U8) -> Never:
    """End the current process with code."""
    code = _cott_validate_abi(code, U8, path="$.code")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/exit_with_code.py", "c8a31111517f4e2ae52470c5f96e6677920dd19fe80aa3c551a662272b795d30", "exit_with_code", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.exit_with_code")
        _result = _implementation(code)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.exit_with_code"
        if _error.span is None:
            _error.span = {"end_byte":2259,"end_column":1,"end_line":94,"start_byte":2133,"start_column":1,"start_line":87}
        raise
    except SystemExit:
        raise
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.exit_with_code", phase="implementation-call", span={"end_byte":2259,"end_column":1,"end_line":94,"start_byte":2133,"start_column":1,"start_line":87}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    raise CottContractViolation("Never function returned", symbol="curriculum.effects_selection.exit_with_code", phase="return", span={"end_byte":2259,"end_column":1,"end_line":94,"start_byte":2133,"start_column":1,"start_line":87}, expected="Never", actual=repr(_result))

__all__ = ["EffectError", "EffectError_InputMissing", "EffectError_OperationFailed", "clock_ns", "copy_result_is_ok", "copy_text", "exit_with_code", "fetch_local", "read_text", "sample_index", "store_and_load", "text_result_is_ok", "text_result_text"]
