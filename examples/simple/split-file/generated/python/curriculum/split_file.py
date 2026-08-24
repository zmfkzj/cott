from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.split_file_types import SplitFileError, SplitFileError_InvalidChunkSize, SplitFileError_OutputLimitExceeded, SplitRequest

def validate_split_request(request: SplitRequest) -> Result[Unit, SplitFileError]:
    """Validates the requested chunk size and output budget. Chunk size must be
from 1 through 10000 inclusive. A valid request may produce at most 10000
chunks. InvalidChunkSize is checked before OutputLimitExceeded."""
    request = _cott_validate_abi(request, SplitRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((((request).chunk_size < 1) or ((request).chunk_size > 10000))):
        _expected_error = SplitFileError_InvalidChunkSize
        _expected_error_span = {"end_byte":587,"end_column":102,"end_line":18,"start_byte":490,"start_column":5,"start_line":18}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/split_file/validate_split_request.py", "b3a43d3df5820026fe9a5a8773b6354db750b0e66194e348be67bd0db77dc586", "validate_split_request", expected_project_name="split-file", expected_cott_symbol="curriculum.split_file.validate_split_request")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.split_file.validate_split_request"
        if _error.span is None:
            _error.span = {"end_byte":634,"end_column":1,"end_line":21,"start_byte":160,"start_column":1,"start_line":11}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.split_file.validate_split_request", phase="implementation-call", span={"end_byte":634,"end_column":1,"end_line":21,"start_byte":160,"start_column":1,"start_line":11}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.split_file.validate_split_request", phase="implementation-call", span={"end_byte":634,"end_column":1,"end_line":21,"start_byte":160,"start_column":1,"start_line":11}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, SplitFileError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.split_file.validate_split_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SplitFileError_OutputLimitExceeded,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.split_file.validate_split_request", phase="error", span={"end_byte":634,"end_column":1,"end_line":21,"start_byte":160,"start_column":1,"start_line":11}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.split_file.validate_split_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    return _result

def split_lines(request: SplitRequest) -> Result[CottList[CottList[str]], SplitFileError]:
    """Validates the request, then splits its lines into consecutive chunks in
input order. A valid empty line list produces an empty outer list. Every
chunk except possibly the last has exactly chunk_size lines, and no line is
omitted or duplicated."""
    request = _cott_validate_abi(request, SplitRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((((request).chunk_size < 1) or ((request).chunk_size > 10000))):
        _expected_error = SplitFileError_InvalidChunkSize
        _expected_error_span = {"end_byte":1098,"end_column":102,"end_line":29,"start_byte":1001,"start_column":5,"start_line":29}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/split_file/split_lines.py", "129718918a81c6fc7b3d1dd2bd717d6c087b36f9ed72b02aafc6405705085606", "split_lines", expected_project_name="split-file", expected_cott_symbol="curriculum.split_file.split_lines")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.split_file.split_lines"
        if _error.span is None:
            _error.span = {"end_byte":1144,"end_column":1,"end_line":31,"start_byte":634,"start_column":1,"start_line":21}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.split_file.split_lines", phase="implementation-call", span={"end_byte":1144,"end_column":1,"end_line":31,"start_byte":634,"start_column":1,"start_line":21}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.split_file.split_lines", phase="implementation-call", span={"end_byte":1144,"end_column":1,"end_line":31,"start_byte":634,"start_column":1,"start_line":21}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CottList[str]], SplitFileError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.split_file.split_lines", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (SplitFileError_OutputLimitExceeded,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.split_file.split_lines", phase="error", span={"end_byte":1144,"end_column":1,"end_line":31,"start_byte":634,"start_column":1,"start_line":21}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.split_file.split_lines", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    return _result

__all__ = ["SplitFileError", "SplitFileError_InvalidChunkSize", "SplitFileError_OutputLimitExceeded", "SplitRequest", "split_lines", "validate_split_request"]
