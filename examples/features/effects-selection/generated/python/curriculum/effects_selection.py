from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from curriculum.effects_selection_types import EffectError, EffectError_InputMissing, EffectError_OperationFailed

def read_text(source: Path) -> Result[str, EffectError]:
    """Read UTF-8 text from a compiler-owned filesystem fixture."""
    source = _cott_validate_abi(source, Path, path="$.source")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/read_text.py", "a782361cd747653bc34dad3d8930d57ce01f5e116eb927fb507731c58943a1ff", "read_text", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.read_text")
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
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.effects_selection.read_text", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is EffectError_InputMissing:
        _cott_contract_condition(True, "curriculum.effects_selection.read_text", "error:2")
    if type(_result) is Err and type(_result.error) is EffectError_OperationFailed:
        _cott_contract_condition(True, "curriculum.effects_selection.read_text", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            text = _cott_match_value.value
            return (_cott_contract_condition(((len(text) >= 0)), "curriculum.effects_selection.read_text", "ensures:1"))
        _cott_contract_condition((False), "curriculum.effects_selection.read_text", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.read_text", clause="ensures:1", phase="ensures", span={"end_byte":302,"end_column":45,"end_line":12,"start_byte":262,"start_column":5,"start_line":12}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, EffectError], path="$.return", validator=_cott_validate_abi)
    return _result

def copy_text(source: Path, destination: Path) -> Result[U64, EffectError]:
    """Read source through curriculum.effects_selection.read_text, encode the
successful text as UTF-8 bytes and atomically replace destination with those
bytes. Return the encoded byte count, not the character count. If replacement
fails, return OperationFailed and preserve the previous destination bytes."""
    source = _cott_validate_abi(source, Path, path="$.source")
    destination = _cott_validate_abi(destination, Path, path="$.destination")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/copy_text.py", "98fadbb1f4d70ce9f1be04b92522fc68ac0598c2e8405604c56b3d5c737a3ed0", "copy_text", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.copy_text")
        _result = _implementation(source, destination)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.copy_text"
        if _error.span is None:
            _error.span = {"end_byte":975,"end_column":1,"end_line":34,"start_byte":403,"start_column":1,"start_line":19}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.copy_text", phase="implementation-call", span={"end_byte":975,"end_column":1,"end_line":34,"start_byte":403,"start_column":1,"start_line":19}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.copy_text", phase="implementation-call", span={"end_byte":975,"end_column":1,"end_line":34,"start_byte":403,"start_column":1,"start_line":19}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[U64, EffectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.effects_selection.copy_text", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (EffectError_InputMissing, EffectError_OperationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.effects_selection.copy_text", phase="error", span={"end_byte":975,"end_column":1,"end_line":34,"start_byte":403,"start_column":1,"start_line":19}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.effects_selection.copy_text", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.effects_selection.copy_text", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is EffectError_InputMissing:
        _cott_contract_condition(True, "curriculum.effects_selection.copy_text", "error:2")
    if type(_result) is Err and type(_result.error) is EffectError_OperationFailed:
        _cott_contract_condition(True, "curriculum.effects_selection.copy_text", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            written = _cott_match_value.value
            return (_cott_contract_condition(((written >= 0)), "curriculum.effects_selection.copy_text", "ensures:1"))
        _cott_contract_condition((False), "curriculum.effects_selection.copy_text", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.copy_text", clause="ensures:1", phase="ensures", span={"end_byte":862,"end_column":47,"end_line":27,"start_byte":820,"start_column":5,"start_line":27}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[U64, EffectError], path="$.return", validator=_cott_validate_abi)
    return _result

def fetch_local(url: str) -> Result[str, EffectError]:
    """Fetch UTF-8 text from a compiler-owned local HTTP fixture."""
    url = _cott_validate_abi(url, str, path="$.url")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((url == "")), "curriculum.effects_selection.fetch_local", "error:2:condition")):
        _expected_error = EffectError_OperationFailed
        _expected_error_span = {"end_byte":1211,"end_column":53,"end_line":41,"start_byte":1163,"start_column":5,"start_line":41}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/fetch_local.py", "0da710ed899c4af3ec769e3fed78c07d5f9ebfe80e28bbb21b533eb125ef17c5", "fetch_local", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.fetch_local")
        _result = _implementation(url)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.fetch_local"
        if _error.span is None:
            _error.span = {"end_byte":1274,"end_column":1,"end_line":46,"start_byte":975,"start_column":1,"start_line":34}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.fetch_local", phase="implementation-call", span={"end_byte":1274,"end_column":1,"end_line":46,"start_byte":975,"start_column":1,"start_line":34}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.fetch_local", phase="implementation-call", span={"end_byte":1274,"end_column":1,"end_line":46,"start_byte":975,"start_column":1,"start_line":34}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, EffectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.effects_selection.fetch_local", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (EffectError_OperationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.effects_selection.fetch_local", phase="error", span={"end_byte":1274,"end_column":1,"end_line":46,"start_byte":975,"start_column":1,"start_line":34}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.effects_selection.fetch_local", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.effects_selection.fetch_local", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is EffectError_OperationFailed:
        _cott_contract_condition(True, "curriculum.effects_selection.fetch_local", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            text = _cott_match_value.value
            return (_cott_contract_condition(((len(text) >= 0)), "curriculum.effects_selection.fetch_local", "ensures:1"))
        _cott_contract_condition((False), "curriculum.effects_selection.fetch_local", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.fetch_local", clause="ensures:1", phase="ensures", span={"end_byte":1157,"end_column":45,"end_line":39,"start_byte":1117,"start_column":5,"start_line":39}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, EffectError], path="$.return", validator=_cott_validate_abi)
    return _result

def text_result_is_ok(result: Result[str, EffectError]) -> bool:
    """Return whether a text effect result is successful."""
    result = _cott_validate_abi(result, Result[str, EffectError], path="$.result")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/text_result_is_ok.py", "df68a692f8ea44a87e2dfd99a28d8ba92a0d9880105f8b5d404ae67734951788", "text_result_is_ok", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.text_result_is_ok")
        _result = _implementation(result)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.text_result_is_ok"
        if _error.span is None:
            _error.span = {"end_byte":1414,"end_column":1,"end_line":51,"start_byte":1274,"start_column":1,"start_line":46}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.text_result_is_ok", phase="implementation-call", span={"end_byte":1414,"end_column":1,"end_line":51,"start_byte":1274,"start_column":1,"start_line":46}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.text_result_is_ok", phase="implementation-call", span={"end_byte":1414,"end_column":1,"end_line":51,"start_byte":1274,"start_column":1,"start_line":46}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, bool, path="$.return")
    _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=_cott_validate_abi)
    return _result

def text_result_text(result: Result[str, EffectError]) -> str:
    """Return successful text, or an empty string for an error result."""
    result = _cott_validate_abi(result, Result[str, EffectError], path="$.result")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/text_result_text.py", "9c3337cf3f05f6b9adec3d4c9ce96cfa7c5e23dd4dec2474484d8c556519fa04", "text_result_text", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.text_result_text")
        _result = _implementation(result)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.text_result_text"
        if _error.span is None:
            _error.span = {"end_byte":1565,"end_column":1,"end_line":56,"start_byte":1414,"start_column":1,"start_line":51}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.text_result_text", phase="implementation-call", span={"end_byte":1565,"end_column":1,"end_line":56,"start_byte":1414,"start_column":1,"start_line":51}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.text_result_text", phase="implementation-call", span={"end_byte":1565,"end_column":1,"end_line":56,"start_byte":1414,"start_column":1,"start_line":51}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def copy_result_is_ok(result: Result[U64, EffectError]) -> bool:
    """Return whether a copy effect result is successful."""
    result = _cott_validate_abi(result, Result[U64, EffectError], path="$.result")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/copy_result_is_ok.py", "84a202a295e9fd72068dc6aee1890313f1ff566cb560d43c8ac0f4c898185609", "copy_result_is_ok", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.copy_result_is_ok")
        _result = _implementation(result)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.copy_result_is_ok"
        if _error.span is None:
            _error.span = {"end_byte":1705,"end_column":1,"end_line":61,"start_byte":1565,"start_column":1,"start_line":56}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.copy_result_is_ok", phase="implementation-call", span={"end_byte":1705,"end_column":1,"end_line":61,"start_byte":1565,"start_column":1,"start_line":56}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.copy_result_is_ok", phase="implementation-call", span={"end_byte":1705,"end_column":1,"end_line":61,"start_byte":1565,"start_column":1,"start_line":56}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
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
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/store_and_load.py", "fe5f5d4315103481e5ad8c325742d795425d75e3de4d18650808b0eac762a17d", "store_and_load", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.store_and_load")
        _result = _implementation(database, key, value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.store_and_load"
        if _error.span is None:
            _error.span = {"end_byte":2020,"end_column":1,"end_line":72,"start_byte":1705,"start_column":1,"start_line":61}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.store_and_load", phase="implementation-call", span={"end_byte":2020,"end_column":1,"end_line":72,"start_byte":1705,"start_column":1,"start_line":61}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.store_and_load", phase="implementation-call", span={"end_byte":2020,"end_column":1,"end_line":72,"start_byte":1705,"start_column":1,"start_line":61}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, EffectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.effects_selection.store_and_load", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (EffectError_OperationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.effects_selection.store_and_load", phase="error", span={"end_byte":2020,"end_column":1,"end_line":72,"start_byte":1705,"start_column":1,"start_line":61}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.effects_selection.store_and_load", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.effects_selection.store_and_load", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is EffectError_OperationFailed:
        _cott_contract_condition(True, "curriculum.effects_selection.store_and_load", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            stored = _cott_match_value.value
            return (_cott_contract_condition(((stored == value)), "curriculum.effects_selection.store_and_load", "ensures:1"))
        _cott_contract_condition((False), "curriculum.effects_selection.store_and_load", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.store_and_load", clause="ensures:1", phase="ensures", span={"end_byte":1934,"end_column":49,"end_line":66,"start_byte":1890,"start_column":5,"start_line":66}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, EffectError], path="$.return", validator=_cott_validate_abi)
    return _result

def clock_ns() -> U64:
    """Return the compiler-owned fixture clock in nanoseconds: the configured
start_ms multiplied by 1000000. Reading the clock does not advance it."""
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/clock_ns.py", "ae301a0ace40c222b6d5685189d1ec45dbbd3cc05d08776245eeee67b4eec0e8", "clock_ns", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.clock_ns")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.clock_ns"
        if _error.span is None:
            _error.span = {"end_byte":2234,"end_column":1,"end_line":80,"start_byte":2020,"start_column":1,"start_line":72}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.clock_ns", phase="implementation-call", span={"end_byte":2234,"end_column":1,"end_line":80,"start_byte":2020,"start_column":1,"start_line":72}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.clock_ns", phase="implementation-call", span={"end_byte":2234,"end_column":1,"end_line":80,"start_byte":2020,"start_column":1,"start_line":72}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, U64, path="$.return")
    _result = _cott_wrap_async_protocol(_result, U64, path="$.return", validator=_cott_validate_abi)
    return _result

def sample_index(limit: U8, seed: U64) -> U8:
    """Choose one index below limit from a deterministic seeded random stream."""
    limit = _cott_validate_abi(limit, U8, path="$.limit")
    seed = _cott_validate_abi(seed, U64, path="$.seed")
    if not (_cott_contract_condition(((limit > 0)), "curriculum.effects_selection.sample_index", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="curriculum.effects_selection.sample_index", clause="requires:1", phase="requires", span={"end_byte":2398,"end_column":23,"end_line":85,"start_byte":2380,"start_column":5,"start_line":85}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/sample_index.py", "27a5c05ebe0976edc0cadb3b2ac113abaa93863759de968285c15543b348c425", "sample_index", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.sample_index")
        _result = _implementation(limit, seed)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.sample_index"
        if _error.span is None:
            _error.span = {"end_byte":2450,"end_column":1,"end_line":91,"start_byte":2234,"start_column":1,"start_line":80}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.sample_index", phase="implementation-call", span={"end_byte":2450,"end_column":1,"end_line":91,"start_byte":2234,"start_column":1,"start_line":80}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.sample_index", phase="implementation-call", span={"end_byte":2450,"end_column":1,"end_line":91,"start_byte":2234,"start_column":1,"start_line":80}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, U8, path="$.return")
    if not (_cott_contract_condition(((_result < limit)), "curriculum.effects_selection.sample_index", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.sample_index", clause="ensures:2", phase="ensures", span={"end_byte":2426,"end_column":27,"end_line":87,"start_byte":2404,"start_column":5,"start_line":87}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, U8, path="$.return", validator=_cott_validate_abi)
    return _result

def exit_with_code(code: U8) -> Never:
    """End the current process with code."""
    code = _cott_validate_abi(code, U8, path="$.code")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/exit_with_code.py", "ec0fb4eab97d890fe4c135064a1569a28c90487760a24a14ec6c75bd8fdfbb1d", "exit_with_code", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.exit_with_code")
        _result = _implementation(code)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.exit_with_code"
        if _error.span is None:
            _error.span = {"end_byte":2576,"end_column":1,"end_line":98,"start_byte":2450,"start_column":1,"start_line":91}
        raise
    except SystemExit:
        raise
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.exit_with_code", phase="implementation-call", span={"end_byte":2576,"end_column":1,"end_line":98,"start_byte":2450,"start_column":1,"start_line":91}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    raise CottContractViolation("Never function returned", symbol="curriculum.effects_selection.exit_with_code", phase="return", span={"end_byte":2576,"end_column":1,"end_line":98,"start_byte":2450,"start_column":1,"start_line":91}, expected="Never", actual=repr(_result))

__all__ = ["EffectError", "EffectError_InputMissing", "EffectError_OperationFailed", "clock_ns", "copy_result_is_ok", "copy_text", "exit_with_code", "fetch_local", "read_text", "sample_index", "store_and_load", "text_result_is_ok", "text_result_text"]
