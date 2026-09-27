from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.harlequin.files_types import FileError, FileError_Failed, FileError_InvalidEncoding, FileError_IsADirectory, FileError_NotFound, FileError_PermissionDenied

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def load_text_file(path: Path) -> Result[str, FileError]:
    """Read the file at path as UTF-8 text (universal newlines are NOT translated:
bytes are decoded as they are). A missing file is NotFound(path); a
directory is IsADirectory(path); an access refusal is PermissionDenied(path);
bytes that are not UTF-8 are InvalidEncoding(path); any other OS error is
Failed(path, message) with the OS error text."""
    path = _cott_normalize_f32_abi(path, Path, path="$.path")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/files/load_text_file.py", "170fb737be48340a3617058047c6bf7fb8201ecde82e4b69d20619b2bd00068d", "load_text_file", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.files.load_text_file")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.files.load_text_file"
        if _error.span is None:
            _error.span = {"end_byte":1033,"end_column":1,"end_line":31,"start_byte":202,"start_column":1,"start_line":10}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.files.load_text_file", phase="implementation-call", span={"end_byte":1033,"end_column":1,"end_line":31,"start_byte":202,"start_column":1,"start_line":10}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.files.load_text_file", phase="implementation-call", span={"end_byte":1033,"end_column":1,"end_line":31,"start_byte":202,"start_column":1,"start_line":10}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[str, FileError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.files.load_text_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (FileError_NotFound, FileError_IsADirectory, FileError_PermissionDenied, FileError_InvalidEncoding, FileError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.files.load_text_file", phase="error", span={"end_byte":1033,"end_column":1,"end_line":31,"start_byte":202,"start_column":1,"start_line":10}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.files.load_text_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.files.load_text_file", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is FileError_NotFound:
            _cott_contract_condition(True, "real.harlequin.files.load_text_file", "error:4")
        if type(_result) is Err and type(_result.error) is FileError_IsADirectory:
            _cott_contract_condition(True, "real.harlequin.files.load_text_file", "error:5")
        if type(_result) is Err and type(_result.error) is FileError_PermissionDenied:
            _cott_contract_condition(True, "real.harlequin.files.load_text_file", "error:6")
        if type(_result) is Err and type(_result.error) is FileError_InvalidEncoding:
            _cott_contract_condition(True, "real.harlequin.files.load_text_file", "error:7")
        if type(_result) is Err and type(_result.error) is FileError_Failed:
            _cott_contract_condition(True, "real.harlequin.files.load_text_file", "error:8")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                text = _cott_match_value.value
                return (_cott_contract_condition(((len(text) >= 0)), "real.harlequin.files.load_text_file", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.files.load_text_file", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.files.load_text_file", clause="ensures:1", phase="ensures", span={"end_byte":686,"end_column":45,"end_line":19,"start_byte":646,"start_column":5,"start_line":19}, expected="true", actual="false")
        def _cott_match_ensures_2() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Err and type(_cott_match_value.error) is FileError_NotFound and True:
                missing = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
                return (_cott_contract_condition(((missing == path)), "real.harlequin.files.load_text_file", "ensures:2"))
            _cott_contract_condition((False), "real.harlequin.files.load_text_file", "ensures:2:applicable")
            return True
        if not (_cott_match_ensures_2()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.files.load_text_file", clause="ensures:2", phase="ensures", span={"end_byte":757,"end_column":71,"end_line":20,"start_byte":691,"start_column":5,"start_line":20}, expected="true", actual="false")
        def _cott_match_ensures_3() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Err and type(_cott_match_value.error) is FileError_InvalidEncoding and True:
                undecodable = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
                return (_cott_contract_condition(((undecodable == path)), "real.harlequin.files.load_text_file", "ensures:3"))
            _cott_contract_condition((False), "real.harlequin.files.load_text_file", "ensures:3:applicable")
            return True
        if not (_cott_match_ensures_3()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.files.load_text_file", clause="ensures:3", phase="ensures", span={"end_byte":843,"end_column":86,"end_line":21,"start_byte":762,"start_column":5,"start_line":21}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, FileError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def save_text_file(path: Path, text: str) -> Result[U64, FileError]:
    """Write text to path as UTF-8, creating missing parent directories, through a
temporary file in the same directory that is flushed, fsynced and then
atomically renamed over path (os.replace), so a failed save leaves any
previous file unchanged; the temporary file is removed on failure. Returns
the number of bytes written. An existing directory at path is
IsADirectory(path); an access refusal is PermissionDenied(path); any other
failure is Failed(path, message)."""
    path = _cott_normalize_f32_abi(path, Path, path="$.path")
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/files/save_text_file.py", "43ba6bce7e881baac995007d66728d7a9d33db189815aec44977d307521aed2f", "save_text_file", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.files.save_text_file")
        _result = _implementation(path, text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.files.save_text_file"
        if _error.span is None:
            _error.span = {"end_byte":1883,"end_column":1,"end_line":51,"start_byte":1033,"start_column":1,"start_line":31}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.files.save_text_file", phase="implementation-call", span={"end_byte":1883,"end_column":1,"end_line":51,"start_byte":1033,"start_column":1,"start_line":31}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.files.save_text_file", phase="implementation-call", span={"end_byte":1883,"end_column":1,"end_line":51,"start_byte":1033,"start_column":1,"start_line":31}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[U64, FileError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.files.save_text_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (FileError_IsADirectory, FileError_PermissionDenied, FileError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.files.save_text_file", phase="error", span={"end_byte":1883,"end_column":1,"end_line":51,"start_byte":1033,"start_column":1,"start_line":31}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.files.save_text_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.files.save_text_file", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is FileError_IsADirectory:
            _cott_contract_condition(True, "real.harlequin.files.save_text_file", "error:3")
        if type(_result) is Err and type(_result.error) is FileError_PermissionDenied:
            _cott_contract_condition(True, "real.harlequin.files.save_text_file", "error:4")
        if type(_result) is Err and type(_result.error) is FileError_Failed:
            _cott_contract_condition(True, "real.harlequin.files.save_text_file", "error:5")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                written = _cott_match_value.value
                return (_cott_contract_condition(((written >= len(text))), "real.harlequin.files.save_text_file", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.files.save_text_file", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.files.save_text_file", clause="ensures:1", phase="ensures", span={"end_byte":1667,"end_column":54,"end_line":42,"start_byte":1618,"start_column":5,"start_line":42}, expected="true", actual="false")
        def _cott_match_ensures_2() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Err and type(_cott_match_value.error) is FileError_IsADirectory and True:
                directory = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
                return (_cott_contract_condition(((directory == path)), "real.harlequin.files.save_text_file", "ensures:2"))
            _cott_contract_condition((False), "real.harlequin.files.save_text_file", "ensures:2:applicable")
            return True
        if not (_cott_match_ensures_2()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.files.save_text_file", clause="ensures:2", phase="ensures", span={"end_byte":1746,"end_column":79,"end_line":43,"start_byte":1672,"start_column":5,"start_line":43}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[U64, FileError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def expand_path(text: str, home: Path, cwd: Path) -> Path:
    """Turn what a user typed into a path: surrounding whitespace removed; a
leading "~" or "~/" is replaced by home; a relative path is joined to cwd;
the result is normalized lexically (os.path.normpath) without resolving
symlinks. An empty text is cwd."""
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    home = _cott_normalize_f32_abi(home, Path, path="$.home")
    cwd = _cott_normalize_f32_abi(cwd, Path, path="$.cwd")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/files/expand_path.py", "8e5e9442c346f02b29ab3bf9e9181f9d5df9595ec43973233491c2a0bc42cce4", "expand_path", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.files.expand_path")
        _result = _implementation(text, home, cwd)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.files.expand_path"
        if _error.span is None:
            _error.span = {"end_byte":2243,"end_column":1,"end_line":61,"start_byte":1883,"start_column":1,"start_line":51}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.files.expand_path", phase="implementation-call", span={"end_byte":2243,"end_column":1,"end_line":61,"start_byte":1883,"start_column":1,"start_line":51}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.files.expand_path", phase="implementation-call", span={"end_byte":2243,"end_column":1,"end_line":61,"start_byte":1883,"start_column":1,"start_line":51}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Path, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Path, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def complete_path(text: str, home: Path, cwd: Path) -> CottList[str]:
    """Tab completion for a path input: the directory part of text (up to and
including its last "/", or "" for none) is expanded like expand_path and
listed; entries whose name starts with the remaining text (hidden entries
only when that text starts with ".") are returned as the original directory
part followed by the entry name, with "/" appended for directories, sorted
by name. A directory that cannot be listed yields []."""
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    home = _cott_normalize_f32_abi(home, Path, path="$.home")
    cwd = _cott_normalize_f32_abi(cwd, Path, path="$.cwd")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/files/complete_path.py", "a75e8880446924342d3d7e3a9382ccc394f7cacd7e6a99bf4799287dfd370047", "complete_path", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.files.complete_path")
        _result = _implementation(text, home, cwd)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.files.complete_path"
        if _error.span is None:
            _error.span = {"end_byte":2801,"end_column":1,"end_line":73,"start_byte":2243,"start_column":1,"start_line":61}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.files.complete_path", phase="implementation-call", span={"end_byte":2801,"end_column":1,"end_line":73,"start_byte":2243,"start_column":1,"start_line":61}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.files.complete_path", phase="implementation-call", span={"end_byte":2801,"end_column":1,"end_line":73,"start_byte":2243,"start_column":1,"start_line":61}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["FileError", "FileError_Failed", "FileError_InvalidEncoding", "FileError_IsADirectory", "FileError_NotFound", "FileError_PermissionDenied", "complete_path", "expand_path", "load_text_file", "save_text_file"]
