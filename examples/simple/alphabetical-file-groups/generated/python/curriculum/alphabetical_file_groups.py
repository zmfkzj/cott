from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.alphabetical_file_groups_types import FileGroupError, FileGroupError_EmptyFilename, FileMove

def classify_filename(filename: str) -> Result[FileMove, FileGroupError]:
    """Classify one filename by its first Unicode code point.

Return EmptyFilename for an empty filename. Otherwise copy the filename
unchanged and select the full Unicode case-fold of a leading letter as its
folder. Select "misc" when the leading code point is not a letter."""
    filename = _cott_validate_abi(filename, str, path="$.filename")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/alphabetical_file_groups/classify_filename.py", "93fd4b65b654b106907e20e9bc9e0e49eb7578dc722bc92a9a50d896b2301498", "classify_filename", expected_project_name="alphabetical-file-groups", expected_cott_symbol="curriculum.alphabetical_file_groups.classify_filename")
        _result = _implementation(filename)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.alphabetical_file_groups.classify_filename"
        if _error.span is None:
            _error.span = {"end_byte":618,"end_column":1,"end_line":23,"start_byte":136,"start_column":1,"start_line":10}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.alphabetical_file_groups.classify_filename", phase="implementation-call", span={"end_byte":618,"end_column":1,"end_line":23,"start_byte":136,"start_column":1,"start_line":10}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.alphabetical_file_groups.classify_filename", phase="implementation-call", span={"end_byte":618,"end_column":1,"end_line":23,"start_byte":136,"start_column":1,"start_line":10}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[FileMove, FileGroupError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.alphabetical_file_groups.classify_filename", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (FileGroupError_EmptyFilename,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.alphabetical_file_groups.classify_filename", phase="error", span={"end_byte":618,"end_column":1,"end_line":23,"start_byte":136,"start_column":1,"start_line":10}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.alphabetical_file_groups.classify_filename", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            move = _cott_match_value.value
            return (((move).filename == filename))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.alphabetical_file_groups.classify_filename", clause="ensures:1", phase="ensures", span={"end_byte":576,"end_column":57,"end_line":19,"start_byte":524,"start_column":5,"start_line":19}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[FileMove, FileGroupError], path="$.return", validator=_cott_validate_abi)
    return _result

def group_filenames(filenames: CottList[str]) -> Result[CottList[FileMove], FileGroupError]:
    """Classify each filename in input order with classify_filename.

Stop at the first EmptyFilename error and propagate it unchanged. Otherwise
return one FileMove per input in the same order. An empty input list
succeeds with an empty move list."""
    filenames = _cott_validate_abi(filenames, CottList[str], path="$.filenames")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/alphabetical_file_groups/group_filenames.py", "a30ed05dc38cb9b469b964e3f70c3d496e80c5d16673d1234cb62945d7e77cbb", "group_filenames", expected_project_name="alphabetical-file-groups", expected_cott_symbol="curriculum.alphabetical_file_groups.group_filenames")
        _result = _implementation(filenames)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.alphabetical_file_groups.group_filenames"
        if _error.span is None:
            _error.span = {"end_byte":1084,"end_column":1,"end_line":35,"start_byte":618,"start_column":1,"start_line":23}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.alphabetical_file_groups.group_filenames", phase="implementation-call", span={"end_byte":1084,"end_column":1,"end_line":35,"start_byte":618,"start_column":1,"start_line":23}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.alphabetical_file_groups.group_filenames", phase="implementation-call", span={"end_byte":1084,"end_column":1,"end_line":35,"start_byte":618,"start_column":1,"start_line":23}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[FileMove], FileGroupError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.alphabetical_file_groups.group_filenames", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (FileGroupError_EmptyFilename,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.alphabetical_file_groups.group_filenames", phase="error", span={"end_byte":1084,"end_column":1,"end_line":35,"start_byte":618,"start_column":1,"start_line":23}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.alphabetical_file_groups.group_filenames", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            moves = _cott_match_value.value
            return ((len(moves) == len(filenames)))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.alphabetical_file_groups.group_filenames", clause="ensures:1", phase="ensures", span={"end_byte":1043,"end_column":59,"end_line":32,"start_byte":989,"start_column":5,"start_line":32}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[FileMove], FileGroupError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["FileGroupError", "FileGroupError_EmptyFilename", "FileMove", "classify_filename", "group_filenames"]
