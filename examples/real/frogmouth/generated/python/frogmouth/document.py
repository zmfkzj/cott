from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from frogmouth.document_types import LoadError, LoadError_HttpFailure, LoadError_InvalidEncoding, LoadError_InvalidLocation, LoadError_NetworkUnavailable, LoadError_NotFound, LoadError_PermissionDenied, LoadError_ReadFailure, LoadError_TooLarge
from frogmouth.model_types import Document, Location

def strip_front_matter(markdown: str) -> str:
    """Remove YAML front matter from Markdown."""
    markdown = _cott_validate_abi(markdown, str, path="$.markdown")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/strip_front_matter.py", "8652e9c1e31fd4b21a69279126c10901090892260a4ffe0a9c31dfd9b14d1ade", "strip_front_matter", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.strip_front_matter")
        _result = _implementation(markdown)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.strip_front_matter"
        if _error.span is None:
            _error.span = {"end_byte":464,"end_column":1,"end_line":20,"start_byte":354,"start_column":1,"start_line":15}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.strip_front_matter", phase="implementation-call", span={"end_byte":464,"end_column":1,"end_line":20,"start_byte":354,"start_column":1,"start_line":15}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.strip_front_matter", phase="implementation-call", span={"end_byte":464,"end_column":1,"end_line":20,"start_byte":354,"start_column":1,"start_line":15}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def load_local_markdown(path: str) -> Result[str, LoadError]:
    path = _cott_validate_abi(path, str, path="$.path")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/load_local_markdown.py", "c22f59abf76d64914728cf88d88e5afc3dd0704447734e11af73364271abbe5b", "load_local_markdown", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.load_local_markdown")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.load_local_markdown"
        if _error.span is None:
            _error.span = {"end_byte":810,"end_column":1,"end_line":32,"start_byte":464,"start_column":1,"start_line":20}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.load_local_markdown", phase="implementation-call", span={"end_byte":810,"end_column":1,"end_line":32,"start_byte":464,"start_column":1,"start_line":20}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.load_local_markdown", phase="implementation-call", span={"end_byte":810,"end_column":1,"end_line":32,"start_byte":464,"start_column":1,"start_line":20}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, LoadError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.document.load_local_markdown", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (LoadError_NotFound, LoadError_PermissionDenied, LoadError_InvalidEncoding, LoadError_TooLarge, LoadError_InvalidLocation, LoadError_ReadFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.document.load_local_markdown", phase="error", span={"end_byte":810,"end_column":1,"end_line":32,"start_byte":464,"start_column":1,"start_line":20}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.document.load_local_markdown", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            markdown = _cott_match_value.value
            return ((len(markdown) <= 5242880))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_local_markdown", clause="ensures:0", phase="ensures", span={"end_byte":583,"end_column":59,"end_line":21,"start_byte":529,"start_column":5,"start_line":21}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, LoadError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_http_markdown(url: str) -> Result[str, LoadError]:
    url = _cott_validate_abi(url, str, path="$.url")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len(url) == 0)):
        _expected_error = LoadError_InvalidLocation
        _expected_error_span = {"end_byte":982,"end_column":54,"end_line":35,"start_byte":933,"start_column":5,"start_line":35}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/load_http_markdown.py", "471b6035a37922ff2c398d0074ef618680e586f1bdb76a8c31d1ed30f497edb7", "load_http_markdown", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.load_http_markdown")
        _result = _implementation(url)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.load_http_markdown"
        if _error.span is None:
            _error.span = {"end_byte":1277,"end_column":1,"end_line":47,"start_byte":810,"start_column":1,"start_line":32}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.load_http_markdown", phase="implementation-call", span={"end_byte":1277,"end_column":1,"end_line":47,"start_byte":810,"start_column":1,"start_line":32}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.load_http_markdown", phase="implementation-call", span={"end_byte":1277,"end_column":1,"end_line":47,"start_byte":810,"start_column":1,"start_line":32}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, LoadError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.document.load_http_markdown", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (LoadError_NotFound, LoadError_PermissionDenied, LoadError_InvalidEncoding, LoadError_TooLarge, LoadError_HttpFailure, LoadError_NetworkUnavailable, LoadError_InvalidLocation, LoadError_ReadFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.document.load_http_markdown", phase="error", span={"end_byte":1277,"end_column":1,"end_line":47,"start_byte":810,"start_column":1,"start_line":32}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.document.load_http_markdown", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            markdown = _cott_match_value.value
            return ((len(markdown) <= 5242880))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_http_markdown", clause="ensures:0", phase="ensures", span={"end_byte":927,"end_column":59,"end_line":33,"start_byte":873,"start_column":5,"start_line":33}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, LoadError], path="$.return", validator=_cott_validate_abi)
    return _result

def markdown_result_is_ok(value: Result[str, LoadError]) -> bool:
    """Report whether Markdown loading succeeded."""
    value = _cott_validate_abi(value, Result[str, LoadError], path="$.value")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/markdown_result_is_ok.py", "be87e075cf1a23e28a70691afe1735d7882e176f0635dee0f39e81c991289732", "markdown_result_is_ok", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.markdown_result_is_ok")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.markdown_result_is_ok"
        if _error.span is None:
            _error.span = {"end_byte":1410,"end_column":1,"end_line":52,"start_byte":1277,"start_column":1,"start_line":47}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.markdown_result_is_ok", phase="implementation-call", span={"end_byte":1410,"end_column":1,"end_line":52,"start_byte":1277,"start_column":1,"start_line":47}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.markdown_result_is_ok", phase="implementation-call", span={"end_byte":1410,"end_column":1,"end_line":52,"start_byte":1277,"start_column":1,"start_line":47}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, bool, path="$.return")
    _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=_cott_validate_abi)
    return _result

def load_github_markdown(repository: str) -> Result[str, LoadError]:
    repository = _cott_validate_abi(repository, str, path="$.repository")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/load_github_markdown.py", "eb5f1044c0931303df48874a2db20e38f4663da07fb61f4a284a32559cc69779", "load_github_markdown", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.load_github_markdown")
        _result = _implementation(repository)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.load_github_markdown"
        if _error.span is None:
            _error.span = {"end_byte":2160,"end_column":1,"end_line":74,"start_byte":1738,"start_column":1,"start_line":60}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.load_github_markdown", phase="implementation-call", span={"end_byte":2160,"end_column":1,"end_line":74,"start_byte":1738,"start_column":1,"start_line":60}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.load_github_markdown", phase="implementation-call", span={"end_byte":2160,"end_column":1,"end_line":74,"start_byte":1738,"start_column":1,"start_line":60}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, LoadError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.document.load_github_markdown", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (LoadError_NotFound, LoadError_PermissionDenied, LoadError_InvalidEncoding, LoadError_TooLarge, LoadError_HttpFailure, LoadError_NetworkUnavailable, LoadError_InvalidLocation, LoadError_ReadFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.document.load_github_markdown", phase="error", span={"end_byte":2160,"end_column":1,"end_line":74,"start_byte":1738,"start_column":1,"start_line":60}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.document.load_github_markdown", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            markdown = _cott_match_value.value
            return ((len(markdown) <= 5242880))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_github_markdown", clause="ensures:0", phase="ensures", span={"end_byte":1864,"end_column":59,"end_line":61,"start_byte":1810,"start_column":5,"start_line":61}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, LoadError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_codeberg_markdown(repository: str) -> Result[str, LoadError]:
    repository = _cott_validate_abi(repository, str, path="$.repository")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/load_codeberg_markdown.py", "c7521a76cd37dee17ad52af9d1fbd6086332df88f94044004c4ac2da9eaf8bf8", "load_codeberg_markdown", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.load_codeberg_markdown")
        _result = _implementation(repository)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.load_codeberg_markdown"
        if _error.span is None:
            _error.span = {"end_byte":2584,"end_column":1,"end_line":88,"start_byte":2160,"start_column":1,"start_line":74}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.load_codeberg_markdown", phase="implementation-call", span={"end_byte":2584,"end_column":1,"end_line":88,"start_byte":2160,"start_column":1,"start_line":74}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.load_codeberg_markdown", phase="implementation-call", span={"end_byte":2584,"end_column":1,"end_line":88,"start_byte":2160,"start_column":1,"start_line":74}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, LoadError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.document.load_codeberg_markdown", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (LoadError_NotFound, LoadError_PermissionDenied, LoadError_InvalidEncoding, LoadError_TooLarge, LoadError_HttpFailure, LoadError_NetworkUnavailable, LoadError_InvalidLocation, LoadError_ReadFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.document.load_codeberg_markdown", phase="error", span={"end_byte":2584,"end_column":1,"end_line":88,"start_byte":2160,"start_column":1,"start_line":74}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.document.load_codeberg_markdown", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            markdown = _cott_match_value.value
            return ((len(markdown) <= 5242880))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_codeberg_markdown", clause="ensures:0", phase="ensures", span={"end_byte":2288,"end_column":59,"end_line":75,"start_byte":2234,"start_column":5,"start_line":75}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, LoadError], path="$.return", validator=_cott_validate_abi)
    return _result

def location_title_fallback(location: Location) -> str:
    location = _cott_validate_abi(location, Location, path="$.location")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/location_title_fallback.py", "27242378bdec50447b7945934d9c248490979b6117df096160d41017728cda9b", "location_title_fallback", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.location_title_fallback")
        _result = _implementation(location)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.location_title_fallback"
        if _error.span is None:
            _error.span = {"end_byte":2667,"end_column":1,"end_line":91,"start_byte":2584,"start_column":1,"start_line":88}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.location_title_fallback", phase="implementation-call", span={"end_byte":2667,"end_column":1,"end_line":91,"start_byte":2584,"start_column":1,"start_line":88}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.location_title_fallback", phase="implementation-call", span={"end_byte":2667,"end_column":1,"end_line":91,"start_byte":2584,"start_column":1,"start_line":88}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not ((len(_result) > 0)):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.location_title_fallback", clause="ensures:0", phase="ensures", span={"end_byte":2665,"end_column":27,"end_line":89,"start_byte":2643,"start_column":5,"start_line":89}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def derive_document_title(markdown: str, fallback: str) -> str:
    markdown = _cott_validate_abi(markdown, str, path="$.markdown")
    fallback = _cott_validate_abi(fallback, str, path="$.fallback")
    if not ((len(fallback) > 0)):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.document.derive_document_title", clause="requires:0", phase="requires", span={"end_byte":2759,"end_column":30,"end_line":92,"start_byte":2734,"start_column":5,"start_line":92}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/derive_document_title.py", "5b2283b04cb63d2a735cd66348ef918d5353fa84fe90beb22ad98eb5ab927ade", "derive_document_title", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.derive_document_title")
        _result = _implementation(markdown, fallback)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.derive_document_title"
        if _error.span is None:
            _error.span = {"end_byte":2789,"end_column":1,"end_line":96,"start_byte":2667,"start_column":1,"start_line":91}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.derive_document_title", phase="implementation-call", span={"end_byte":2789,"end_column":1,"end_line":96,"start_byte":2667,"start_column":1,"start_line":91}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.derive_document_title", phase="implementation-call", span={"end_byte":2789,"end_column":1,"end_line":96,"start_byte":2667,"start_column":1,"start_line":91}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not ((len(_result) > 0)):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.derive_document_title", clause="ensures:1", phase="ensures", span={"end_byte":2787,"end_column":27,"end_line":94,"start_byte":2765,"start_column":5,"start_line":94}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def load_document(location: Location) -> Result[Document, LoadError]:
    location = _cott_validate_abi(location, Location, path="$.location")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/load_document.py", "52b98e44f4ea5e60fcb66652165d7e761281efd64128ae45f61e5993aa9f2d1a", "load_document", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.load_document")
        _result = _implementation(location)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.load_document"
        if _error.span is None:
            _error.span = {"end_byte":3354,"end_column":1,"end_line":111,"start_byte":2789,"start_column":1,"start_line":96}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.load_document", phase="implementation-call", span={"end_byte":3354,"end_column":1,"end_line":111,"start_byte":2789,"start_column":1,"start_line":96}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.load_document", phase="implementation-call", span={"end_byte":3354,"end_column":1,"end_line":111,"start_byte":2789,"start_column":1,"start_line":96}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Document, LoadError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.document.load_document", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (LoadError_NotFound, LoadError_PermissionDenied, LoadError_InvalidEncoding, LoadError_TooLarge, LoadError_HttpFailure, LoadError_NetworkUnavailable, LoadError_InvalidLocation, LoadError_ReadFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.document.load_document", phase="error", span={"end_byte":3354,"end_column":1,"end_line":111,"start_byte":2789,"start_column":1,"start_line":96}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.document.load_document", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            document = _cott_match_value.value
            return (((document).location == location))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_document", clause="ensures:0", phase="ensures", span={"end_byte":2922,"end_column":65,"end_line":97,"start_byte":2862,"start_column":5,"start_line":97}, expected="true", actual="false")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            document = _cott_match_value.value
            return ((len((document).markdown) <= 5242880))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_document", clause="ensures:1", phase="ensures", span={"end_byte":2990,"end_column":68,"end_line":98,"start_byte":2927,"start_column":5,"start_line":98}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            document = _cott_match_value.value
            return ((len((document).title) > 0))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_document", clause="ensures:2", phase="ensures", span={"end_byte":3048,"end_column":58,"end_line":99,"start_byte":2995,"start_column":5,"start_line":99}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Document, LoadError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["LoadError", "LoadError_HttpFailure", "LoadError_InvalidEncoding", "LoadError_InvalidLocation", "LoadError_NetworkUnavailable", "LoadError_NotFound", "LoadError_PermissionDenied", "LoadError_ReadFailure", "LoadError_TooLarge", "derive_document_title", "load_codeberg_markdown", "load_document", "load_github_markdown", "load_http_markdown", "load_local_markdown", "location_title_fallback", "markdown_result_is_ok", "strip_front_matter"]
