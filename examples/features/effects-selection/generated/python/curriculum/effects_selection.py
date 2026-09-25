from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from curriculum.effects_selection_types import CopyReceipt, EffectError, EffectError_InputMissing, EffectError_OperationFailed, FileText, PageText

def read_text(source: Path) -> Result[FileText, EffectError]:
    """Read the file at source and decode its bytes as strict UTF-8. The result
pairs the decoded text with source. An absent source returns InputMissing
carrying source; any other read failure and bytes that are not valid UTF-8
return OperationFailed."""
    source = _cott_validate_abi(source, Path, path="$.source")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/read_text.py", "f5b69da089d5fc067f2a38d23bcfd8fc0bc02d795603a4cde29dfa055b9e310f", "read_text", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.read_text")
        _result = _implementation(source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.read_text"
        if _error.span is None:
            _error.span = {"end_byte":851,"end_column":1,"end_line":35,"start_byte":277,"start_column":1,"start_line":19}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.read_text", phase="implementation-call", span={"end_byte":851,"end_column":1,"end_line":35,"start_byte":277,"start_column":1,"start_line":19}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.read_text", phase="implementation-call", span={"end_byte":851,"end_column":1,"end_line":35,"start_byte":277,"start_column":1,"start_line":19}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[FileText, EffectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.effects_selection.read_text", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (EffectError_InputMissing, EffectError_OperationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.effects_selection.read_text", phase="error", span={"end_byte":851,"end_column":1,"end_line":35,"start_byte":277,"start_column":1,"start_line":19}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.effects_selection.read_text", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.effects_selection.read_text", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is EffectError_InputMissing:
        _cott_contract_condition(True, "curriculum.effects_selection.read_text", "error:3")
    if type(_result) is Err and type(_result.error) is EffectError_OperationFailed:
        _cott_contract_condition(True, "curriculum.effects_selection.read_text", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            file = _cott_match_value.value
            return (_cott_contract_condition((((file).path == source)), "curriculum.effects_selection.read_text", "ensures:1"))
        _cott_contract_condition((False), "curriculum.effects_selection.read_text", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.read_text", clause="ensures:1", phase="ensures", span={"end_byte":671,"end_column":51,"end_line":27,"start_byte":625,"start_column":5,"start_line":27}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is EffectError_InputMissing and True:
            missing = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((missing == source)), "curriculum.effects_selection.read_text", "ensures:2"))
        _cott_contract_condition((False), "curriculum.effects_selection.read_text", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.read_text", clause="ensures:2", phase="ensures", span={"end_byte":750,"end_column":79,"end_line":28,"start_byte":676,"start_column":5,"start_line":28}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[FileText, EffectError], path="$.return", validator=_cott_validate_abi)
    return _result

def copy_text(source: Path, destination: Path) -> Result[CopyReceipt, EffectError]:
    """Copy the text of source to destination as UTF-8 bytes. bytes_written is
the encoded byte count, not the character count. A read_text error is
returned unchanged and destination is left untouched."""
    source = _cott_validate_abi(source, Path, path="$.source")
    destination = _cott_validate_abi(destination, Path, path="$.destination")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/copy_text.py", "2bf1195f5ead63e9d6ab325b81e9651d68040ad81db6decddde0b5d7aaf3f52e", "copy_text", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.copy_text")
        _result = _implementation(source, destination)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.copy_text"
        if _error.span is None:
            _error.span = {"end_byte":1423,"end_column":1,"end_line":50,"start_byte":851,"start_column":1,"start_line":35}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.copy_text", phase="implementation-call", span={"end_byte":1423,"end_column":1,"end_line":50,"start_byte":851,"start_column":1,"start_line":35}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.copy_text", phase="implementation-call", span={"end_byte":1423,"end_column":1,"end_line":50,"start_byte":851,"start_column":1,"start_line":35}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CopyReceipt, EffectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.effects_selection.copy_text", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (EffectError_InputMissing, EffectError_OperationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.effects_selection.copy_text", phase="error", span={"end_byte":1423,"end_column":1,"end_line":50,"start_byte":851,"start_column":1,"start_line":35}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.effects_selection.copy_text", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.effects_selection.copy_text", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is EffectError_InputMissing:
        _cott_contract_condition(True, "curriculum.effects_selection.copy_text", "error:3")
    if type(_result) is Err and type(_result.error) is EffectError_OperationFailed:
        _cott_contract_condition(True, "curriculum.effects_selection.copy_text", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (_cott_contract_condition((((receipt).destination == destination)), "curriculum.effects_selection.copy_text", "ensures:1"))
        _cott_contract_condition((False), "curriculum.effects_selection.copy_text", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.copy_text", clause="ensures:1", phase="ensures", span={"end_byte":1231,"end_column":69,"end_line":42,"start_byte":1167,"start_column":5,"start_line":42}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is EffectError_InputMissing and True:
            missing = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((missing == source)), "curriculum.effects_selection.copy_text", "ensures:2"))
        _cott_contract_condition((False), "curriculum.effects_selection.copy_text", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.copy_text", clause="ensures:2", phase="ensures", span={"end_byte":1310,"end_column":79,"end_line":43,"start_byte":1236,"start_column":5,"start_line":43}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CopyReceipt, EffectError], path="$.return", validator=_cott_validate_abi)
    return _result

def fetch_local(url: str) -> Result[PageText, EffectError]:
    """GET url over HTTP, following redirects, and decode the final response body
as strict UTF-8. The result pairs the text with the requested url. An empty
url returns OperationFailed without sending a request; a connection or read
failure, a timeout, a final status outside 200-299 and a body that is not
valid UTF-8 return OperationFailed."""
    url = _cott_validate_abi(url, str, path="$.url")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((url == "")), "curriculum.effects_selection.fetch_local", "error:2:condition")):
        _expected_error = EffectError_OperationFailed
        _expected_error_span = {"end_byte":1960,"end_column":53,"end_line":61,"start_byte":1912,"start_column":5,"start_line":61}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/fetch_local.py", "65a14f46b5949b5d171aacae5bea973a1603e8746b27d867cc110b4ccdf6196a", "fetch_local", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.fetch_local")
        _result = _implementation(url)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.fetch_local"
        if _error.span is None:
            _error.span = {"end_byte":2023,"end_column":1,"end_line":66,"start_byte":1423,"start_column":1,"start_line":50}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.fetch_local", phase="implementation-call", span={"end_byte":2023,"end_column":1,"end_line":66,"start_byte":1423,"start_column":1,"start_line":50}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.fetch_local", phase="implementation-call", span={"end_byte":2023,"end_column":1,"end_line":66,"start_byte":1423,"start_column":1,"start_line":50}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[PageText, EffectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.effects_selection.fetch_local", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (EffectError_OperationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.effects_selection.fetch_local", phase="error", span={"end_byte":2023,"end_column":1,"end_line":66,"start_byte":1423,"start_column":1,"start_line":50}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.effects_selection.fetch_local", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.effects_selection.fetch_local", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is EffectError_OperationFailed:
        _cott_contract_condition(True, "curriculum.effects_selection.fetch_local", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            page = _cott_match_value.value
            return (_cott_contract_condition((((page).url == url)), "curriculum.effects_selection.fetch_local", "ensures:1"))
        _cott_contract_condition((False), "curriculum.effects_selection.fetch_local", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.fetch_local", clause="ensures:1", phase="ensures", span={"end_byte":1906,"end_column":47,"end_line":59,"start_byte":1864,"start_column":5,"start_line":59}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[PageText, EffectError], path="$.return", validator=_cott_validate_abi)
    return _result

def store_and_load(database: Path, key: str, value: str) -> Result[str, EffectError]:
    """Store value under key in the SQLite database file at database, replacing
any previous value for key, then read the value stored under key back from
that database. Any SQLite failure returns OperationFailed."""
    database = _cott_validate_abi(database, Path, path="$.database")
    key = _cott_validate_abi(key, str, path="$.key")
    value = _cott_validate_abi(value, str, path="$.value")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/store_and_load.py", "45f601a0f5c61e4c11048956972ccf627b0d7ee2d6ba31029a0f789e8adb7555", "store_and_load", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.store_and_load")
        _result = _implementation(database, key, value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.store_and_load"
        if _error.span is None:
            _error.span = {"end_byte":2482,"end_column":1,"end_line":79,"start_byte":2023,"start_column":1,"start_line":66}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.store_and_load", phase="implementation-call", span={"end_byte":2482,"end_column":1,"end_line":79,"start_byte":2023,"start_column":1,"start_line":66}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.store_and_load", phase="implementation-call", span={"end_byte":2482,"end_column":1,"end_line":79,"start_byte":2023,"start_column":1,"start_line":66}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, EffectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.effects_selection.store_and_load", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (EffectError_OperationFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.effects_selection.store_and_load", phase="error", span={"end_byte":2482,"end_column":1,"end_line":79,"start_byte":2023,"start_column":1,"start_line":66}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
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
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.store_and_load", clause="ensures:1", phase="ensures", span={"end_byte":2396,"end_column":49,"end_line":73,"start_byte":2352,"start_column":5,"start_line":73}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, EffectError], path="$.return", validator=_cott_validate_abi)
    return _result

def clock_ns() -> U64:
    """Read the compiler-owned clock fixture and return its time in nanoseconds.
The fixture is configured in milliseconds, so start_ms 17 reads as
17000000. Reading does not advance the clock."""
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/clock_ns.py", "ae301a0ace40c222b6d5685189d1ec45dbbd3cc05d08776245eeee67b4eec0e8", "clock_ns", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.clock_ns")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.clock_ns"
        if _error.span is None:
            _error.span = {"end_byte":2745,"end_column":1,"end_line":88,"start_byte":2482,"start_column":1,"start_line":79}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.clock_ns", phase="implementation-call", span={"end_byte":2745,"end_column":1,"end_line":88,"start_byte":2482,"start_column":1,"start_line":79}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.clock_ns", phase="implementation-call", span={"end_byte":2745,"end_column":1,"end_line":88,"start_byte":2482,"start_column":1,"start_line":79}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, U64, path="$.return")
    _result = _cott_wrap_async_protocol(_result, U64, path="$.return", validator=_cott_validate_abi)
    return _result

def sample_index(limit: U8, seed: U64) -> U8:
    """Choose an index below limit from seed."""
    limit = _cott_validate_abi(limit, U8, path="$.limit")
    seed = _cott_validate_abi(seed, U64, path="$.seed")
    if not (_cott_contract_condition(((limit > 0)), "curriculum.effects_selection.sample_index", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="curriculum.effects_selection.sample_index", clause="requires:1", phase="requires", span={"end_byte":2876,"end_column":23,"end_line":93,"start_byte":2858,"start_column":5,"start_line":93}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/sample_index.py", "27a5c05ebe0976edc0cadb3b2ac113abaa93863759de968285c15543b348c425", "sample_index", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.sample_index")
        _result = _implementation(limit, seed)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.sample_index"
        if _error.span is None:
            _error.span = {"end_byte":2928,"end_column":1,"end_line":99,"start_byte":2745,"start_column":1,"start_line":88}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.effects_selection.sample_index", phase="implementation-call", span={"end_byte":2928,"end_column":1,"end_line":99,"start_byte":2745,"start_column":1,"start_line":88}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.sample_index", phase="implementation-call", span={"end_byte":2928,"end_column":1,"end_line":99,"start_byte":2745,"start_column":1,"start_line":88}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, U8, path="$.return")
    if not (_cott_contract_condition(((_result < limit)), "curriculum.effects_selection.sample_index", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.effects_selection.sample_index", clause="ensures:2", phase="ensures", span={"end_byte":2904,"end_column":27,"end_line":95,"start_byte":2882,"start_column":5,"start_line":95}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, U8, path="$.return", validator=_cott_validate_abi)
    return _result

def exit_with_code(code: U8) -> Never:
    """Terminate the current process."""
    code = _cott_validate_abi(code, U8, path="$.code")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/effects_selection/exit_with_code.py", "ec0fb4eab97d890fe4c135064a1569a28c90487760a24a14ec6c75bd8fdfbb1d", "exit_with_code", expected_project_name="effects-selection", expected_cott_symbol="curriculum.effects_selection.exit_with_code")
        _result = _implementation(code)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.effects_selection.exit_with_code"
        if _error.span is None:
            _error.span = {"end_byte":3050,"end_column":1,"end_line":106,"start_byte":2928,"start_column":1,"start_line":99}
        raise
    except SystemExit:
        raise
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.effects_selection.exit_with_code", phase="implementation-call", span={"end_byte":3050,"end_column":1,"end_line":106,"start_byte":2928,"start_column":1,"start_line":99}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    raise CottContractViolation("Never function returned", symbol="curriculum.effects_selection.exit_with_code", phase="return", span={"end_byte":3050,"end_column":1,"end_line":106,"start_byte":2928,"start_column":1,"start_line":99}, expected="Never", actual=repr(_result))

__all__ = ["CopyReceipt", "EffectError", "EffectError_InputMissing", "EffectError_OperationFailed", "FileText", "PageText", "clock_ns", "copy_text", "exit_with_code", "fetch_local", "read_text", "sample_index", "store_and_load"]
