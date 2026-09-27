from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_starts_with

from real.harlequin.support_types import BufferCache, BufferState, CacheError, CacheError_Unreadable, CacheError_Unwritable, ClipboardError, ClipboardError_Unavailable, CrashContext, ExternalEdit, ExternalEditorError, ExternalEditorError_Failed, ExternalEditorError_NoEditor, LocaleError, LocaleError_Unavailable, LocaleOutcome, SshError, SshError_Failed, SshError_Invalid, SshTunnel
from real.harlequin.cli_types import SshSettings

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def load_buffer_cache(path: Path) -> Result[Option[BufferCache], CacheError]:
    """Read the buffer cache JSON file at path: {"version": 1, "focus_index": int,
"buffers": [{"text": str, "selection": [anchor, cursor]}, ...]}. A missing
file is Ok(Nothing); a file of another version or shape is Ok(Nothing) (an
old or foreign cache is ignored, as Harlequin ignores unreadable caches); a
file that exists but cannot be read is Unreadable(path, message). Offsets are
clamped to the text length and focus_index to the buffers."""
    path = _cott_normalize_f32_abi(path, Path, path="$.path")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/load_buffer_cache.py", "c3365694dabae07d11a469bc325a9a0303b220acdd1a0b6e8693378eb333df49", "load_buffer_cache", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.load_buffer_cache")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.load_buffer_cache"
        if _error.span is None:
            _error.span = {"end_byte":2724,"end_column":1,"end_line":103,"start_byte":2067,"start_column":1,"start_line":87}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.load_buffer_cache", phase="implementation-call", span={"end_byte":2724,"end_column":1,"end_line":103,"start_byte":2067,"start_column":1,"start_line":87}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.load_buffer_cache", phase="implementation-call", span={"end_byte":2724,"end_column":1,"end_line":103,"start_byte":2067,"start_column":1,"start_line":87}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Option[BufferCache], CacheError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.support.load_buffer_cache", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (CacheError_Unreadable,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.support.load_buffer_cache", phase="error", span={"end_byte":2724,"end_column":1,"end_line":103,"start_byte":2067,"start_column":1,"start_line":87}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.support.load_buffer_cache", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.support.load_buffer_cache", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is CacheError_Unreadable:
            _cott_contract_condition(True, "real.harlequin.support.load_buffer_cache", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                cache = _cott_match_value.value
                return (_cott_contract_condition((True), "real.harlequin.support.load_buffer_cache", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.support.load_buffer_cache", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.load_buffer_cache", clause="ensures:1", phase="ensures", span={"end_byte":2664,"end_column":37,"end_line":97,"start_byte":2632,"start_column":5,"start_line":97}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Option[BufferCache], CacheError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def save_buffer_cache(path: Path, cache: BufferCache) -> Result[Unit, CacheError]:
    """Write cache to path in load_buffer_cache's JSON format through a temporary
file in the same directory that is flushed, fsynced and atomically renamed over
path, creating missing parent directories. Failures are Unwritable(path,
message) and leave any previous file unchanged. Name the parent-path local
`parent`, not `dir`: the audit reserves the identifier dir for reflection."""
    path = _cott_normalize_f32_abi(path, Path, path="$.path")
    cache = _cott_normalize_f32_abi(cache, BufferCache, path="$.cache")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/save_buffer_cache.py", "0fceba5c7a2335f710a3e311be9af29de2d27cb0ebc609c88eab2db98027cd53", "save_buffer_cache", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.save_buffer_cache")
        _result = _implementation(path, cache)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.save_buffer_cache"
        if _error.span is None:
            _error.span = {"end_byte":3338,"end_column":1,"end_line":118,"start_byte":2724,"start_column":1,"start_line":103}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.save_buffer_cache", phase="implementation-call", span={"end_byte":3338,"end_column":1,"end_line":118,"start_byte":2724,"start_column":1,"start_line":103}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.save_buffer_cache", phase="implementation-call", span={"end_byte":3338,"end_column":1,"end_line":118,"start_byte":2724,"start_column":1,"start_line":103}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Unit, CacheError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.support.save_buffer_cache", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (CacheError_Unwritable,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.support.save_buffer_cache", phase="error", span={"end_byte":3338,"end_column":1,"end_line":118,"start_byte":2724,"start_column":1,"start_line":103}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.support.save_buffer_cache", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.support.save_buffer_cache", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is CacheError_Unwritable:
            _cott_contract_condition(True, "real.harlequin.support.save_buffer_cache", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                done = _cott_match_value.value
                return (_cott_contract_condition(((done == UNIT)), "real.harlequin.support.save_buffer_cache", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.support.save_buffer_cache", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.save_buffer_cache", clause="ensures:1", phase="ensures", span={"end_byte":3266,"end_column":42,"end_line":112,"start_byte":3229,"start_column":5,"start_line":112}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, CacheError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def adopt_recovery(cache_dir: Path, now_epoch_seconds: F64) -> Result[Option[BufferCache], CacheError]:
    """Find buffers a previous session left behind when it ended unexpectedly, the
way Harlequin adopts them: candidates in cache_dir are recovered-*.json files
(newest modification time first), then recovery-*.json files whose
modification time is more than 180 seconds before now_epoch_seconds (newest
first). The first candidate is renamed to "<name>.replayed" before it is read
(so a corrupt file is never replayed twice) and read like load_buffer_cache;
a candidate with no nonblank buffer yields Nothing. No candidate: Ok(Nothing).
Rename or read failures are Unreadable(path, message)."""
    cache_dir = _cott_normalize_f32_abi(cache_dir, Path, path="$.cache_dir")
    now_epoch_seconds = _cott_normalize_f32_abi(now_epoch_seconds, F64, path="$.now_epoch_seconds")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/adopt_recovery.py", "ffb7f6709a2a67e2605719df9a5f709f280b275c88c0c3b5cd01e8ed3538e8fc", "adopt_recovery", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.adopt_recovery")
        _result = _implementation(cache_dir, now_epoch_seconds)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.adopt_recovery"
        if _error.span is None:
            _error.span = {"end_byte":4203,"end_column":1,"end_line":139,"start_byte":3338,"start_column":1,"start_line":118}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.adopt_recovery", phase="implementation-call", span={"end_byte":4203,"end_column":1,"end_line":139,"start_byte":3338,"start_column":1,"start_line":118}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.adopt_recovery", phase="implementation-call", span={"end_byte":4203,"end_column":1,"end_line":139,"start_byte":3338,"start_column":1,"start_line":118}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Option[BufferCache], CacheError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.support.adopt_recovery", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (CacheError_Unreadable,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.support.adopt_recovery", phase="error", span={"end_byte":4203,"end_column":1,"end_line":139,"start_byte":3338,"start_column":1,"start_line":118}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.support.adopt_recovery", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.support.adopt_recovery", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is CacheError_Unreadable:
            _cott_contract_condition(True, "real.harlequin.support.adopt_recovery", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                recovered = _cott_match_value.value
                return (_cott_contract_condition((True), "real.harlequin.support.adopt_recovery", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.support.adopt_recovery", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.adopt_recovery", clause="ensures:1", phase="ensures", span={"end_byte":4131,"end_column":41,"end_line":133,"start_byte":4095,"start_column":5,"start_line":133}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Option[BufferCache], CacheError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def remove_file(path: Path) -> Result[Unit, CacheError]:
    """Delete the file at path; a missing file is not an error. Other failures are
Unwritable(path, message)."""
    path = _cott_normalize_f32_abi(path, Path, path="$.path")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/remove_file.py", "94040529df9f38add1be6a44950b3bf581e77095d7f1e28dac3a7eb96c46cb5d", "remove_file", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.remove_file")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.remove_file"
        if _error.span is None:
            _error.span = {"end_byte":4493,"end_column":1,"end_line":151,"start_byte":4203,"start_column":1,"start_line":139}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.remove_file", phase="implementation-call", span={"end_byte":4493,"end_column":1,"end_line":151,"start_byte":4203,"start_column":1,"start_line":139}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.remove_file", phase="implementation-call", span={"end_byte":4493,"end_column":1,"end_line":151,"start_byte":4203,"start_column":1,"start_line":139}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Unit, CacheError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.support.remove_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (CacheError_Unwritable,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.support.remove_file", phase="error", span={"end_byte":4493,"end_column":1,"end_line":151,"start_byte":4203,"start_column":1,"start_line":139}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.support.remove_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.support.remove_file", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is CacheError_Unwritable:
            _cott_contract_condition(True, "real.harlequin.support.remove_file", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                done = _cott_match_value.value
                return (_cott_contract_condition(((done == UNIT)), "real.harlequin.support.remove_file", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.support.remove_file", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.remove_file", clause="ensures:1", phase="ensures", span={"end_byte":4432,"end_column":42,"end_line":145,"start_byte":4395,"start_column":5,"start_line":145}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, CacheError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def resolve_editor(environment: FrozenMap[str, str]) -> Result[CottList[str], ExternalEditorError]:
    """The external editor command: the first of VISUAL and EDITOR that is set and
not blank after stripping, split with shlex.split (POSIX rules). Neither set:
NoEditor. A value shlex cannot split (for example an unclosed quote) is
Failed("Harlequin could not run your editor. The editor command {value!r}
could not be parsed: {error}")."""
    environment = _cott_normalize_f32_abi(environment, FrozenMap[str, str], path="$.environment")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/resolve_editor.py", "62c4299c2b1447eb9959f5dcf0adc35c4fd655800095c0dd264e6fe7db049a48", "resolve_editor", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.resolve_editor")
        _result = _implementation(environment)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.resolve_editor"
        if _error.span is None:
            _error.span = {"end_byte":5099,"end_column":1,"end_line":167,"start_byte":4493,"start_column":1,"start_line":151}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.resolve_editor", phase="implementation-call", span={"end_byte":5099,"end_column":1,"end_line":167,"start_byte":4493,"start_column":1,"start_line":151}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.resolve_editor", phase="implementation-call", span={"end_byte":5099,"end_column":1,"end_line":167,"start_byte":4493,"start_column":1,"start_line":151}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[CottList[str], ExternalEditorError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.support.resolve_editor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (ExternalEditorError_NoEditor, ExternalEditorError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.support.resolve_editor", phase="error", span={"end_byte":5099,"end_column":1,"end_line":167,"start_byte":4493,"start_column":1,"start_line":151}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.support.resolve_editor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.support.resolve_editor", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is ExternalEditorError_NoEditor:
            _cott_contract_condition(True, "real.harlequin.support.resolve_editor", "error:2")
        if type(_result) is Err and type(_result.error) is ExternalEditorError_Failed:
            _cott_contract_condition(True, "real.harlequin.support.resolve_editor", "error:3")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                command = _cott_match_value.value
                return (_cott_contract_condition(((len(command) > 0)), "real.harlequin.support.resolve_editor", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.support.resolve_editor", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.resolve_editor", clause="ensures:1", phase="ensures", span={"end_byte":5004,"end_column":50,"end_line":160,"start_byte":4959,"start_column":5,"start_line":160}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], ExternalEditorError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def edit_externally(text: str, command: CottList[str]) -> Result[ExternalEdit, ExternalEditorError]:
    """Round-trip text through the user's editor while it owns the terminal (the
caller suspends the full-screen application first): write text as UTF-8 to a
new temporary file with suffix ".sql", close it, run command plus the file's
path as the last argument with subprocess.run (inheriting stdin, stdout and
stderr) and wait. A nonzero exit status returns ExternalEdit(Nothing, status).
Otherwise read the file back as UTF-8 with universal newlines and return
ExternalEdit(Some(text), 0). The temporary file is always deleted. Failure to
start the editor or to write or read the file is Failed("Harlequin could not
run your editor. {reason}")."""
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    command = _cott_normalize_f32_abi(command, CottList[str], path="$.command")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/edit_externally.py", "c00cbc2bcb729b36b1c01cf134cc69887c7c58ef1098f9568eb82f9b84533505", "edit_externally", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.edit_externally")
        _result = _implementation(text, command)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.edit_externally"
        if _error.span is None:
            _error.span = {"end_byte":6066,"end_column":1,"end_line":186,"start_byte":5099,"start_column":1,"start_line":167}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.edit_externally", phase="implementation-call", span={"end_byte":6066,"end_column":1,"end_line":186,"start_byte":5099,"start_column":1,"start_line":167}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.edit_externally", phase="implementation-call", span={"end_byte":6066,"end_column":1,"end_line":186,"start_byte":5099,"start_column":1,"start_line":167}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[ExternalEdit, ExternalEditorError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.support.edit_externally", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (ExternalEditorError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.support.edit_externally", phase="error", span={"end_byte":6066,"end_column":1,"end_line":186,"start_byte":5099,"start_column":1,"start_line":167}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.support.edit_externally", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.support.edit_externally", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is ExternalEditorError_Failed:
            _cott_contract_condition(True, "real.harlequin.support.edit_externally", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                edit = _cott_match_value.value
                return (_cott_contract_condition(((((edit).returncode >= (-255)) or ((edit).returncode < (-255)))), "real.harlequin.support.edit_externally", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.support.edit_externally", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.edit_externally", clause="ensures:1", phase="ensures", span={"end_byte":5972,"end_column":81,"end_line":180,"start_byte":5896,"start_column":5,"start_line":180}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ExternalEdit, ExternalEditorError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def osc52_sequence(text: str) -> str:
    """The OSC 52 escape sequence that asks the terminal to put text on the system
clipboard: ESC "]52;c;" + base64(UTF-8 text) + BEL ("\\u001b]52;c;...\\u0007")."""
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/osc52_sequence.py", "e753b424c24a4b726b8c67cfcd2dfad41665378958a15750af8f703533ab6e3d", "osc52_sequence", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.osc52_sequence")
        _result = _implementation(text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.osc52_sequence"
        if _error.span is None:
            _error.span = {"end_byte":6353,"end_column":1,"end_line":196,"start_byte":6066,"start_column":1,"start_line":186}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.osc52_sequence", phase="implementation-call", span={"end_byte":6353,"end_column":1,"end_line":196,"start_byte":6066,"start_column":1,"start_line":186}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.osc52_sequence", phase="implementation-call", span={"end_byte":6353,"end_column":1,"end_line":196,"start_byte":6066,"start_column":1,"start_line":186}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((_cott_starts_with(_result, "\u001b]52;c;")), "real.harlequin.support.osc52_sequence", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.osc52_sequence", clause="ensures:1", phase="ensures", span={"end_byte":6335,"end_column":50,"end_line":192,"start_byte":6290,"start_column":5,"start_line":192}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def copy_to_clipboard(text: str) -> Result[Unit, ClipboardError]:
    """Put text on the system clipboard with pyperclip.copy. A pyperclip
PyperclipException (no clipboard mechanism) is Unavailable(message)."""
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/copy_to_clipboard.py", "ca92d25d76de070f4db68a7748215699c28ff7ce8d36469153370c7b9c350be4", "copy_to_clipboard", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.copy_to_clipboard")
        _result = _implementation(text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.copy_to_clipboard"
        if _error.span is None:
            _error.span = {"end_byte":6688,"end_column":1,"end_line":208,"start_byte":6353,"start_column":1,"start_line":196}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.copy_to_clipboard", phase="implementation-call", span={"end_byte":6688,"end_column":1,"end_line":208,"start_byte":6353,"start_column":1,"start_line":196}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.copy_to_clipboard", phase="implementation-call", span={"end_byte":6688,"end_column":1,"end_line":208,"start_byte":6353,"start_column":1,"start_line":196}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Unit, ClipboardError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.support.copy_to_clipboard", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (ClipboardError_Unavailable,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.support.copy_to_clipboard", phase="error", span={"end_byte":6688,"end_column":1,"end_line":208,"start_byte":6353,"start_column":1,"start_line":196}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.support.copy_to_clipboard", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.support.copy_to_clipboard", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is ClipboardError_Unavailable:
            _cott_contract_condition(True, "real.harlequin.support.copy_to_clipboard", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                done = _cott_match_value.value
                return (_cott_contract_condition(((done == UNIT)), "real.harlequin.support.copy_to_clipboard", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.support.copy_to_clipboard", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.copy_to_clipboard", clause="ensures:1", phase="ensures", span={"end_byte":6623,"end_column":42,"end_line":202,"start_byte":6586,"start_column":5,"start_line":202}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, ClipboardError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def paste_from_clipboard() -> Result[str, ClipboardError]:
    """The system clipboard's text via pyperclip.paste; failures are
Unavailable(message)."""
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/paste_from_clipboard.py", "d4dac2a89717df04681fe1f61b02c46ed054a2e4084ad66b730e31b85be5c0a7", "paste_from_clipboard", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.paste_from_clipboard")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.paste_from_clipboard"
        if _error.span is None:
            _error.span = {"end_byte":6972,"end_column":1,"end_line":220,"start_byte":6688,"start_column":1,"start_line":208}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.paste_from_clipboard", phase="implementation-call", span={"end_byte":6972,"end_column":1,"end_line":220,"start_byte":6688,"start_column":1,"start_line":208}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.paste_from_clipboard", phase="implementation-call", span={"end_byte":6972,"end_column":1,"end_line":220,"start_byte":6688,"start_column":1,"start_line":208}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[str, ClipboardError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.support.paste_from_clipboard", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (ClipboardError_Unavailable,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.support.paste_from_clipboard", phase="error", span={"end_byte":6972,"end_column":1,"end_line":220,"start_byte":6688,"start_column":1,"start_line":208}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.support.paste_from_clipboard", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.support.paste_from_clipboard", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is ClipboardError_Unavailable:
            _cott_contract_condition(True, "real.harlequin.support.paste_from_clipboard", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                pasted = _cott_match_value.value
                return (_cott_contract_condition(((len(pasted) >= 0)), "real.harlequin.support.paste_from_clipboard", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.support.paste_from_clipboard", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.paste_from_clipboard", clause="ensures:1", phase="ensures", span={"end_byte":6907,"end_column":49,"end_line":214,"start_byte":6863,"start_column":5,"start_line":214}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, ClipboardError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def apply_locale(requested: Option[str]) -> Result[LocaleOutcome, LocaleError]:
    """Choose the locale for number formatting as Harlequin's --locale does and
report its numeric conventions, using the babel distribution's CLDR data
instead of the process C library (the locale module is unavailable to
implementations). The name is requested, else the first non-empty of the
environment variables LC_ALL, LC_NUMERIC, LANG (os.environ), else "C". A name
that is "C" or "POSIX" or whose part before the first "." is "C" or "POSIX"
means the C conventions: thousands_separator "", decimal_point ".",
grouping empty. Any other name drops its ".encoding" and "@modifier"
suffixes and is parsed with babel.Locale.parse(name, sep="_"); a parse
failure (ValueError or babel.UnknownLocaleError) is Unavailable("unsupported
locale setting: You likely need to install the locale {name} on your OS.")
when requested, while an unparseable environment locale falls back to the
C conventions. A parsed locale gives thousands_separator
babel.numbers.get_group_symbol(locale), decimal_point
babel.numbers.get_decimal_symbol(locale) and grouping [primary, secondary]
from locale.decimal_formats[None].grouping (just [primary] when both are
equal). When nothing was requested and the environment locale is C, use
"en_US": on success the warning is "Harlequin uses the locale of your
device to format numbers. Your device's locale is set to {name}, which is a
POSIX locale for computers, not humans. We assume you are a human and want to
see thousands separators, so we set your locale to en_US.UTF-8. To configure a
different locale or to suppress this warning, set your system locale, or pass
a locale string to Harlequin using the --locale option. To use Harlequin with
the C locale, run Harlequin with the --locale C option. See also
https://harlequin.sh/docs/troubleshooting/locale"; on failure a warning that
thousands separators are unavailable, advising --locale and noting that
--locale C suppresses it, with the same URL."""
    requested = _cott_normalize_f32_abi(requested, Option[str], path="$.requested")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/apply_locale.py", "cfee13d9592ca5427fabf3ad24d6c9eb92fc641a10799fc57e40708f43a5d648", "apply_locale", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.apply_locale")
        _result = _implementation(requested)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.apply_locale"
        if _error.span is None:
            _error.span = {"end_byte":9228,"end_column":1,"end_line":257,"start_byte":6972,"start_column":1,"start_line":220}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.apply_locale", phase="implementation-call", span={"end_byte":9228,"end_column":1,"end_line":257,"start_byte":6972,"start_column":1,"start_line":220}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.apply_locale", phase="implementation-call", span={"end_byte":9228,"end_column":1,"end_line":257,"start_byte":6972,"start_column":1,"start_line":220}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[LocaleOutcome, LocaleError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.support.apply_locale", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (LocaleError_Unavailable,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.support.apply_locale", phase="error", span={"end_byte":9228,"end_column":1,"end_line":257,"start_byte":6972,"start_column":1,"start_line":220}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.support.apply_locale", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.support.apply_locale", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is LocaleError_Unavailable:
            _cott_contract_condition(True, "real.harlequin.support.apply_locale", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                outcome = _cott_match_value.value
                return (_cott_contract_condition(((len((outcome).decimal_point) > 0)), "real.harlequin.support.apply_locale", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.support.apply_locale", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.apply_locale", clause="ensures:1", phase="ensures", span={"end_byte":9169,"end_column":64,"end_line":251,"start_byte":9110,"start_column":5,"start_line":251}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[LocaleOutcome, LocaleError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def ssh_command(settings: SshSettings) -> Result[CottList[str], SshError]:
    """The ssh command line for a tunnel: ["ssh", "-N", "-o",
"ExitOnForwardFailure=yes"], then "-o", "BatchMode=yes" when batch_mode,
then "-L", forward for each forward in order, then the host. host and each
forward are passed verbatim but must not be empty, start with "-", or contain
whitespace, control characters or any of ;&|`$<>(){}'"\\\\; otherwise
Invalid("Refusing to pass {value!r} to ssh: it contains characters ssh would
not take as a {host|forward}.")."""
    settings = _cott_normalize_f32_abi(settings, SshSettings, path="$.settings")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/ssh_command.py", "53b4c980d6bbe465fa2acd6366b62f3681a18d42f651bcb5b82535c9d1dd4fb1", "ssh_command", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.ssh_command")
        _result = _implementation(settings)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.ssh_command"
        if _error.span is None:
            _error.span = {"end_byte":9902,"end_column":1,"end_line":274,"start_byte":9228,"start_column":1,"start_line":257}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.ssh_command", phase="implementation-call", span={"end_byte":9902,"end_column":1,"end_line":274,"start_byte":9228,"start_column":1,"start_line":257}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.ssh_command", phase="implementation-call", span={"end_byte":9902,"end_column":1,"end_line":274,"start_byte":9228,"start_column":1,"start_line":257}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[CottList[str], SshError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.support.ssh_command", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (SshError_Invalid,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.support.ssh_command", phase="error", span={"end_byte":9902,"end_column":1,"end_line":274,"start_byte":9228,"start_column":1,"start_line":257}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.support.ssh_command", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.support.ssh_command", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is SshError_Invalid:
            _cott_contract_condition(True, "real.harlequin.support.ssh_command", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                command = _cott_match_value.value
                return (_cott_contract_condition(((len(command) >= 5)), "real.harlequin.support.ssh_command", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.support.ssh_command", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.ssh_command", clause="ensures:1", phase="ensures", span={"end_byte":9856,"end_column":51,"end_line":268,"start_byte":9810,"start_column":5,"start_line":268}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], SshError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def open_ssh_tunnel(settings: SshSettings) -> Result[SshTunnel, SshError]:
    """Start the tunnel Harlequin opens before connecting: resolve the forwards'
local ports with "ssh -G {host}" (plus the -L options), bounded to 10
seconds, taking LocalForward lines; when a local port is already bound,
allow_reuse gives a warning "Port {port} is already in use; connecting through
the listener that has it." and reuses it, otherwise Failed("Harlequin could not
open the SSH tunnel. Local port {port} is already in use. Pass
--ssh-allow-reuse to connect through it."). Start ssh_command(settings) with
subprocess.Popen (stdin inherited so ssh can prompt unless batch_mode, stderr
captured up to 8192 bytes), adding "-o ServerAliveInterval=30 -o
ServerAliveCountMax=3" when the resolved interval is 0. Wait until every local
port accepts a TCP connection (probe every 0.05 s, each connect bounded to 0.5
s) or timeout_seconds pass (1 s when there are no ports). If ssh exits first or
the deadline passes, terminate it (2 s grace, then kill) and return
Failed("Harlequin could not open the SSH tunnel. {ssh stderr or 'Timed out
waiting for the forwards.'}")."""
    settings = _cott_normalize_f32_abi(settings, SshSettings, path="$.settings")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/open_ssh_tunnel.py", "1266a3b0e450db1d3379b1070e5b993782ca97578f0d467160673f49e830205a", "open_ssh_tunnel", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.open_ssh_tunnel")
        _result = _implementation(settings)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.open_ssh_tunnel"
        if _error.span is None:
            _error.span = {"end_byte":11279,"end_column":1,"end_line":300,"start_byte":9902,"start_column":1,"start_line":274}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.open_ssh_tunnel", phase="implementation-call", span={"end_byte":11279,"end_column":1,"end_line":300,"start_byte":9902,"start_column":1,"start_line":274}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.open_ssh_tunnel", phase="implementation-call", span={"end_byte":11279,"end_column":1,"end_line":300,"start_byte":9902,"start_column":1,"start_line":274}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[SshTunnel, SshError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.support.open_ssh_tunnel", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (SshError_Invalid, SshError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.support.open_ssh_tunnel", phase="error", span={"end_byte":11279,"end_column":1,"end_line":300,"start_byte":9902,"start_column":1,"start_line":274}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.support.open_ssh_tunnel", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.support.open_ssh_tunnel", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is SshError_Invalid:
            _cott_contract_condition(True, "real.harlequin.support.open_ssh_tunnel", "error:2")
        if type(_result) is Err and type(_result.error) is SshError_Failed:
            _cott_contract_condition(True, "real.harlequin.support.open_ssh_tunnel", "error:3")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                tunnel = _cott_match_value.value
                return (_cott_contract_condition((((tunnel).host == (settings).host)), "real.harlequin.support.open_ssh_tunnel", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.support.open_ssh_tunnel", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.open_ssh_tunnel", clause="ensures:1", phase="ensures", span={"end_byte":11188,"end_column":62,"end_line":293,"start_byte":11131,"start_column":5,"start_line":293}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[SshTunnel, SshError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def ssh_tunnel_alive(tunnel: SshTunnel) -> bool:
    """Whether the tunnel's ssh process is still running (a reused tunnel owns no
process and is alive while its ports accept connections)."""
    tunnel = _cott_normalize_f32_abi(tunnel, SshTunnel, path="$.tunnel")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/ssh_tunnel_alive.py", "3f46dc74f648cb3543eb28513b7f80e3de1fe1f421ef1143bff0919e9ebeaf86", "ssh_tunnel_alive", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.ssh_tunnel_alive")
        _result = _implementation(tunnel)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.ssh_tunnel_alive"
        if _error.span is None:
            _error.span = {"end_byte":11524,"end_column":1,"end_line":308,"start_byte":11279,"start_column":1,"start_line":300}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.ssh_tunnel_alive", phase="implementation-call", span={"end_byte":11524,"end_column":1,"end_line":308,"start_byte":11279,"start_column":1,"start_line":300}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.ssh_tunnel_alive", phase="implementation-call", span={"end_byte":11524,"end_column":1,"end_line":308,"start_byte":11279,"start_column":1,"start_line":300}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, bool, path="$.return")
    _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def close_ssh_tunnel(tunnel: SshTunnel) -> Unit:
    """Stop the tunnel's ssh process: terminate, wait up to 2 seconds, then kill.
Does nothing for a reused tunnel or a process that already exited."""
    tunnel = _cott_normalize_f32_abi(tunnel, SshTunnel, path="$.tunnel")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/close_ssh_tunnel.py", "7a1e7a1c14369331da7c8d75b3f4767275bb83e7227ad2d7b131ba9f04a6cf48", "close_ssh_tunnel", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.close_ssh_tunnel")
        _result = _implementation(tunnel)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.close_ssh_tunnel"
        if _error.span is None:
            _error.span = {"end_byte":11795,"end_column":1,"end_line":318,"start_byte":11524,"start_column":1,"start_line":308}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.close_ssh_tunnel", phase="implementation-call", span={"end_byte":11795,"end_column":1,"end_line":318,"start_byte":11524,"start_column":1,"start_line":308}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.close_ssh_tunnel", phase="implementation-call", span={"end_byte":11795,"end_column":1,"end_line":318,"start_byte":11524,"start_column":1,"start_line":308}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Unit, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((_result == UNIT)), "real.harlequin.support.close_ssh_tunnel", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.close_ssh_tunnel", clause="ensures:1", phase="ensures", span={"end_byte":11767,"end_column":25,"end_line":314,"start_byte":11747,"start_column":5,"start_line":314}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Unit, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def crash_report_text(context: CrashContext, error_summary: str, traceback_text: str, reported_at: str, environment_lines: CottList[str]) -> str:
    """The plain-text crash report Harlequin writes: a header "Harlequin crash report,
{reported_at}" and the paragraph "Review and redact as necessary before
sharing this file. It includes your configuration (with passwords masked)
and, if a buffer was open, the SQL in it.", then sections separated by blank
lines, each a title line followed by its lines: "ENVIRONMENT" (the
environment_lines), "CONTEXT" (one "key: value" line per CrashContext field
except active_sql, keys as the field names), "TRACEBACK" (error_summary then
traceback_text) and, when active_sql is Some, "SQL IN THE ACTIVE BUFFER" with
that SQL passed through real.harlequin.sqltext.redact_sql. Prose lines wrap
at 72 characters."""
    context = _cott_normalize_f32_abi(context, CrashContext, path="$.context")
    error_summary = _cott_normalize_f32_abi(error_summary, str, path="$.error_summary")
    traceback_text = _cott_normalize_f32_abi(traceback_text, str, path="$.traceback_text")
    reported_at = _cott_normalize_f32_abi(reported_at, str, path="$.reported_at")
    environment_lines = _cott_normalize_f32_abi(environment_lines, CottList[str], path="$.environment_lines")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/crash_report_text.py", "3452d6bc4afd2ceee85e805902ec7b6a445978685a3dda141880da3396d637bf", "crash_report_text", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.crash_report_text")
        _result = _implementation(context, error_summary, traceback_text, reported_at, environment_lines)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.crash_report_text"
        if _error.span is None:
            _error.span = {"end_byte":12794,"end_column":1,"end_line":342,"start_byte":11795,"start_column":1,"start_line":318}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.crash_report_text", phase="implementation-call", span={"end_byte":12794,"end_column":1,"end_line":342,"start_byte":11795,"start_column":1,"start_line":318}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.crash_report_text", phase="implementation-call", span={"end_byte":12794,"end_column":1,"end_line":342,"start_byte":11795,"start_column":1,"start_line":318}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((_cott_starts_with(_result, "Harlequin crash report, ")), "real.harlequin.support.crash_report_text", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.crash_report_text", clause="ensures:1", phase="ensures", span={"end_byte":12776,"end_column":62,"end_line":338,"start_byte":12719,"start_column":5,"start_line":338}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def write_crash_report(directory: Path, text: str, stamp: str, pid: I64) -> Result[Path, CacheError]:
    """Write text to directory/crash-{stamp}-{pid}.log (stamp is the UTC time as
YYYYMMDDTHHMMSSZ), creating directory, then delete the oldest crash-*.log
files so at most 10 remain. Returns the report path; failures are
Unwritable(path, message)."""
    directory = _cott_normalize_f32_abi(directory, Path, path="$.directory")
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    stamp = _cott_normalize_f32_abi(stamp, str, path="$.stamp")
    pid = _cott_normalize_f32_abi(pid, I64, path="$.pid")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/write_crash_report.py", "48a7460c30f2993b5f20bc80df4d3254ee7f4dfdd48dbcaad2ddf985687ff8fb", "write_crash_report", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.write_crash_report")
        _result = _implementation(directory, text, stamp, pid)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.write_crash_report"
        if _error.span is None:
            _error.span = {"end_byte":13283,"end_column":1,"end_line":356,"start_byte":12794,"start_column":1,"start_line":342}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.write_crash_report", phase="implementation-call", span={"end_byte":13283,"end_column":1,"end_line":356,"start_byte":12794,"start_column":1,"start_line":342}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.write_crash_report", phase="implementation-call", span={"end_byte":13283,"end_column":1,"end_line":356,"start_byte":12794,"start_column":1,"start_line":342}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Path, CacheError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.support.write_crash_report", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (CacheError_Unwritable,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.support.write_crash_report", phase="error", span={"end_byte":13283,"end_column":1,"end_line":356,"start_byte":12794,"start_column":1,"start_line":342}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.support.write_crash_report", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.support.write_crash_report", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is CacheError_Unwritable:
            _cott_contract_condition(True, "real.harlequin.support.write_crash_report", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                written = _cott_match_value.value
                return (_cott_contract_condition((True), "real.harlequin.support.write_crash_report", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.support.write_crash_report", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.write_crash_report", clause="ensures:1", phase="ensures", span={"end_byte":13211,"end_column":39,"end_line":350,"start_byte":13177,"start_column":5,"start_line":350}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Path, CacheError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def crash_message(error_summary: str, buffers_saved: bool, report_path: Option[Path]) -> str:
    """What the terminal shows after a crash instead of a traceback: "Harlequin
encountered an unexpected error and had to quit.\\n\\n{error_summary}\\n\\n",
then when buffers_saved "Your buffers have been saved, and Harlequin will offer
them back the next time you start it.\\n\\n", then "Please report this bug at
https://github.com/tconbeer/harlequin/issues/new?template=crash_report.md",
then, when report_path is Some, " and attach the crash report written to
{path}", then "."."""
    error_summary = _cott_normalize_f32_abi(error_summary, str, path="$.error_summary")
    buffers_saved = _cott_normalize_f32_abi(buffers_saved, bool, path="$.buffers_saved")
    report_path = _cott_normalize_f32_abi(report_path, Option[Path], path="$.report_path")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/support/crash_message.py", "a36a59542a75e6164faf3415ff64b394bedbdf3c0f96f99777b8017cec383526", "crash_message", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.support.crash_message")
        _result = _implementation(error_summary, buffers_saved, report_path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.support.crash_message"
        if _error.span is None:
            _error.span = {"end_byte":14009,"end_column":1,"end_line":371,"start_byte":13283,"start_column":1,"start_line":356}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.support.crash_message", phase="implementation-call", span={"end_byte":14009,"end_column":1,"end_line":371,"start_byte":13283,"start_column":1,"start_line":356}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.support.crash_message", phase="implementation-call", span={"end_byte":14009,"end_column":1,"end_line":371,"start_byte":13283,"start_column":1,"start_line":356}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((_cott_starts_with(_result, "Harlequin encountered an unexpected error and had to quit.")), "real.harlequin.support.crash_message", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.support.crash_message", clause="ensures:1", phase="ensures", span={"end_byte":13991,"end_column":96,"end_line":367,"start_byte":13900,"start_column":5,"start_line":367}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["BufferCache", "BufferState", "CacheError", "CacheError_Unreadable", "CacheError_Unwritable", "ClipboardError", "ClipboardError_Unavailable", "CrashContext", "ExternalEdit", "ExternalEditorError", "ExternalEditorError_Failed", "ExternalEditorError_NoEditor", "LocaleError", "LocaleError_Unavailable", "LocaleOutcome", "SshError", "SshError_Failed", "SshError_Invalid", "SshTunnel", "adopt_recovery", "apply_locale", "close_ssh_tunnel", "copy_to_clipboard", "crash_message", "crash_report_text", "edit_externally", "load_buffer_cache", "open_ssh_tunnel", "osc52_sequence", "paste_from_clipboard", "remove_file", "resolve_editor", "save_buffer_cache", "ssh_command", "ssh_tunnel_alive", "write_crash_report"]
