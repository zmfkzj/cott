from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from frogmouth.document_types import LoadError, LoadError_InvalidEncoding, LoadError_NetworkFailed, LoadError_NotFound, LoadError_ReadFailed, LoadError_TooLarge
from frogmouth.model_types import Document, Location

def load_document(location: Location) -> Result[Document, LoadError]:
    """Load at most 5 MiB of UTF-8 Markdown and derive a title from its first heading."""
    location = _cott_validate_abi(location, Location, path="$.location")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/load_document.py", "2c7607ae8e78b7596d613188b579fdb5229d093d551131ed2f8c5130e9fc8052", "load_document", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.load_document")
        _result = _implementation(location)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.load_document"
        if _error.span is None:
            _error.span = {"end_byte":817,"end_column":1,"end_line":28,"start_byte":258,"start_column":1,"start_line":12}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.load_document", phase="implementation-call", span={"end_byte":817,"end_column":1,"end_line":28,"start_byte":258,"start_column":1,"start_line":12}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.load_document", phase="implementation-call", span={"end_byte":817,"end_column":1,"end_line":28,"start_byte":258,"start_column":1,"start_line":12}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Document, LoadError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.document.load_document", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (LoadError_NotFound, LoadError_InvalidEncoding, LoadError_TooLarge, LoadError_NetworkFailed, LoadError_ReadFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.document.load_document", phase="error", span={"end_byte":817,"end_column":1,"end_line":28,"start_byte":258,"start_column":1,"start_line":12}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.document.load_document", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            document = _cott_match_value.value
            return (((document).location == location))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_document", clause="ensures:1", phase="ensures", span={"end_byte":496,"end_column":65,"end_line":17,"start_byte":436,"start_column":5,"start_line":17}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            document = _cott_match_value.value
            return ((len((document).title) > 0))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_document", clause="ensures:2", phase="ensures", span={"end_byte":554,"end_column":58,"end_line":18,"start_byte":501,"start_column":5,"start_line":18}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            document = _cott_match_value.value
            return ((len((document).markdown) <= 5242880))
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_document", clause="ensures:3", phase="ensures", span={"end_byte":622,"end_column":68,"end_line":19,"start_byte":559,"start_column":5,"start_line":19}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Document, LoadError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["LoadError", "LoadError_InvalidEncoding", "LoadError_NetworkFailed", "LoadError_NotFound", "LoadError_ReadFailed", "LoadError_TooLarge", "load_document"]
