from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from real.posting.client_types import CollectionEntry, Header, HttpMethod, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, HttpResponse, PostingError, PostingError_CollectionRootMissing, PostingError_InvalidHeader, PostingError_InvalidJson, PostingError_InvalidRequest, PostingError_InvalidYaml, PostingError_NetworkFailed, PostingError_ReadFailed, PostingError_RequestMissing, PostingError_SaveFailed, PostingError_TimedOut, PostingError_UnresolvedVariable, RequestDocument

def discover_collections(root: Path) -> Result[CottList[CollectionEntry], PostingError]:
    root = _cott_validate_abi(root, Path, path="$.root")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/discover_collections.py", "ba3008072defa95f50d6693be2e42ccd7603160968eaf6ae7fa5e5051209dd83", "discover_collections", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.discover_collections")
        _result = _implementation(root)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.discover_collections"
        if _error.span is None:
            _error.span = {"end_byte":1089,"end_column":1,"end_line":54,"start_byte":843,"start_column":1,"start_line":46}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.discover_collections", phase="implementation-call", span={"end_byte":1089,"end_column":1,"end_line":54,"start_byte":843,"start_column":1,"start_line":46}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.discover_collections", phase="implementation-call", span={"end_byte":1089,"end_column":1,"end_line":54,"start_byte":843,"start_column":1,"start_line":46}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CollectionEntry], PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.discover_collections", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_CollectionRootMissing, PostingError_ReadFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.discover_collections", phase="error", span={"end_byte":1089,"end_column":1,"end_line":54,"start_byte":843,"start_column":1,"start_line":46}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.discover_collections", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            entries = _cott_match_value.value
            return ((len(entries) <= 100000))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.discover_collections", clause="ensures:0", phase="ensures", span={"end_byte":982,"end_column":56,"end_line":47,"start_byte":931,"start_column":5,"start_line":47}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CollectionEntry], PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_request(path: Path) -> Result[RequestDocument, PostingError]:
    path = _cott_validate_abi(path, Path, path="$.path")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/load_request.py", "7f706086df5e169ff694c06b8270fae82abc6e4682bcc1e79f29e1ede057af9d", "load_request", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.load_request")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.load_request"
        if _error.span is None:
            _error.span = {"end_byte":1440,"end_column":1,"end_line":65,"start_byte":1089,"start_column":1,"start_line":54}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.load_request", phase="implementation-call", span={"end_byte":1440,"end_column":1,"end_line":65,"start_byte":1089,"start_column":1,"start_line":54}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.load_request", phase="implementation-call", span={"end_byte":1440,"end_column":1,"end_line":65,"start_byte":1089,"start_column":1,"start_line":54}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[RequestDocument, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.load_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_RequestMissing, PostingError_InvalidYaml, PostingError_InvalidRequest, PostingError_ReadFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.load_request", phase="error", span={"end_byte":1440,"end_column":1,"end_line":65,"start_byte":1089,"start_column":1,"start_line":54}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.load_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return ((len((request).name) > 0))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.load_request", clause="ensures:0", phase="ensures", span={"end_byte":1213,"end_column":55,"end_line":55,"start_byte":1163,"start_column":5,"start_line":55}, expected="true", actual="false")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return ((len((request).url) > 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.load_request", clause="ensures:1", phase="ensures", span={"end_byte":1267,"end_column":54,"end_line":56,"start_byte":1218,"start_column":5,"start_line":56}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[RequestDocument, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def save_request(path: Path, request: RequestDocument) -> Result[Unit, PostingError]:
    path = _cott_validate_abi(path, Path, path="$.path")
    request = _cott_validate_abi(request, RequestDocument, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/save_request.py", "9b162da631f28af5581b37662c2707137bc57f2210b82b9b1e4770c5f926c3f8", "save_request", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.save_request")
        _result = _implementation(path, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.save_request"
        if _error.span is None:
            _error.span = {"end_byte":1631,"end_column":1,"end_line":72,"start_byte":1440,"start_column":1,"start_line":65}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.save_request", phase="implementation-call", span={"end_byte":1631,"end_column":1,"end_line":72,"start_byte":1440,"start_column":1,"start_line":65}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.save_request", phase="implementation-call", span={"end_byte":1631,"end_column":1,"end_line":72,"start_byte":1440,"start_column":1,"start_line":65}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.save_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_SaveFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.save_request", phase="error", span={"end_byte":1631,"end_column":1,"end_line":72,"start_byte":1440,"start_column":1,"start_line":65}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.save_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            saved = _cott_match_value.value
            return ((saved == UNIT))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.save_request", clause="ensures:0", phase="ensures", span={"end_byte":1568,"end_column":44,"end_line":66,"start_byte":1529,"start_column":5,"start_line":66}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def parse_method(value: str) -> Result[HttpMethod, PostingError]:
    value = _cott_validate_abi(value, str, path="$.value")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/parse_method.py", "08cdf0be0782df10319755547f0854b0bd6171ed622097921dd771502f865fa5", "parse_method", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.parse_method")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.parse_method"
        if _error.span is None:
            _error.span = {"end_byte":2149,"end_column":1,"end_line":79,"start_byte":1631,"start_column":1,"start_line":72}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.parse_method", phase="implementation-call", span={"end_byte":2149,"end_column":1,"end_line":79,"start_byte":1631,"start_column":1,"start_line":72}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.parse_method", phase="implementation-call", span={"end_byte":2149,"end_column":1,"end_line":79,"start_byte":1631,"start_column":1,"start_line":72}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[HttpMethod, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.parse_method", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidRequest,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.parse_method", phase="error", span={"end_byte":2149,"end_column":1,"end_line":79,"start_byte":1631,"start_column":1,"start_line":72}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.parse_method", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            method = _cott_match_value.value
            return (((((((((value == "GET") and (method == HttpMethod_Get())) or ((value == "POST") and (method == HttpMethod_Post()))) or ((value == "PUT") and (method == HttpMethod_Put()))) or ((value == "PATCH") and (method == HttpMethod_Patch()))) or ((value == "DELETE") and (method == HttpMethod_Delete()))) or ((value == "HEAD") and (method == HttpMethod_Head()))) or ((value == "OPTIONS") and (method == HttpMethod_Options()))))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.parse_method", clause="ensures:0", phase="ensures", span={"end_byte":2092,"end_column":397,"end_line":73,"start_byte":1700,"start_column":5,"start_line":73}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[HttpMethod, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def make_request(name: str, method: HttpMethod, url: str, header_lines: str, body: str, json_body: bool) -> Result[RequestDocument, PostingError]:
    name = _cott_validate_abi(name, str, path="$.name")
    method = _cott_validate_abi(method, HttpMethod, path="$.method")
    url = _cott_validate_abi(url, str, path="$.url")
    header_lines = _cott_validate_abi(header_lines, str, path="$.header_lines")
    body = _cott_validate_abi(body, str, path="$.body")
    json_body = _cott_validate_abi(json_body, bool, path="$.json_body")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/make_request.py", "d45be9a470b929cfadd75e74dc263b5f513a1c91ea02d96eb3e225a3c9f8134b", "make_request", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.make_request")
        _result = _implementation(name, method, url, header_lines, body, json_body)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.make_request"
        if _error.span is None:
            _error.span = {"end_byte":2702,"end_column":1,"end_line":98,"start_byte":2149,"start_column":1,"start_line":79}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.make_request", phase="implementation-call", span={"end_byte":2702,"end_column":1,"end_line":98,"start_byte":2149,"start_column":1,"start_line":79}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.make_request", phase="implementation-call", span={"end_byte":2702,"end_column":1,"end_line":98,"start_byte":2149,"start_column":1,"start_line":79}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[RequestDocument, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.make_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidRequest, PostingError_InvalidHeader,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.make_request", phase="error", span={"end_byte":2702,"end_column":1,"end_line":98,"start_byte":2149,"start_column":1,"start_line":79}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.make_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return (((request).name == name))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.make_request", clause="ensures:0", phase="ensures", span={"end_byte":2376,"end_column":55,"end_line":87,"start_byte":2326,"start_column":5,"start_line":87}, expected="true", actual="false")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return (((request).method == method))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.make_request", clause="ensures:1", phase="ensures", span={"end_byte":2435,"end_column":59,"end_line":88,"start_byte":2381,"start_column":5,"start_line":88}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return (((request).url == url))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.make_request", clause="ensures:2", phase="ensures", span={"end_byte":2488,"end_column":53,"end_line":89,"start_byte":2440,"start_column":5,"start_line":89}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return (((request).body == body))
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.make_request", clause="ensures:3", phase="ensures", span={"end_byte":2543,"end_column":55,"end_line":90,"start_byte":2493,"start_column":5,"start_line":90}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            request = _cott_match_value.value
            return (((request).json_body == json_body))
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.make_request", clause="ensures:4", phase="ensures", span={"end_byte":2608,"end_column":65,"end_line":91,"start_byte":2548,"start_column":5,"start_line":91}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[RequestDocument, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def extract_url_variables(url: str) -> CottList[str]:
    url = _cott_validate_abi(url, str, path="$.url")
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/extract_url_variables.py", "1b58232ba1e40023f57a9ccb5c45cb317d1dc6745841d308f1f1037edf1f685d", "extract_url_variables", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.extract_url_variables")
        _result = _implementation(url)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.extract_url_variables"
        if _error.span is None:
            _error.span = {"end_byte":2767,"end_column":1,"end_line":101,"start_byte":2702,"start_column":1,"start_line":98}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.extract_url_variables", phase="implementation-call", span={"end_byte":2767,"end_column":1,"end_line":101,"start_byte":2702,"start_column":1,"start_line":98}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.extract_url_variables", phase="implementation-call", span={"end_byte":2767,"end_column":1,"end_line":101,"start_byte":2702,"start_column":1,"start_line":98}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_request(request: RequestDocument, variables: str) -> Result[RequestDocument, PostingError]:
    request = _cott_validate_abi(request, RequestDocument, path="$.request")
    variables = _cott_validate_abi(variables, str, path="$.variables")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/resolve_request.py", "b1337d1c931622e63f6a2f4618bc18bc7ae2235717e74f06bd0e909858dfc94c", "resolve_request", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.resolve_request")
        _result = _implementation(request, variables)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.resolve_request"
        if _error.span is None:
            _error.span = {"end_byte":3187,"end_column":1,"end_line":114,"start_byte":2767,"start_column":1,"start_line":101}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.resolve_request", phase="implementation-call", span={"end_byte":3187,"end_column":1,"end_line":114,"start_byte":2767,"start_column":1,"start_line":101}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.resolve_request", phase="implementation-call", span={"end_byte":3187,"end_column":1,"end_line":114,"start_byte":2767,"start_column":1,"start_line":101}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[RequestDocument, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.resolve_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidHeader, PostingError_UnresolvedVariable,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.resolve_request", phase="error", span={"end_byte":3187,"end_column":1,"end_line":114,"start_byte":2767,"start_column":1,"start_line":101}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.resolve_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            resolved = _cott_match_value.value
            return (((resolved).name == (request).name))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.resolve_request", clause="ensures:0", phase="ensures", span={"end_byte":2945,"end_column":65,"end_line":105,"start_byte":2885,"start_column":5,"start_line":105}, expected="true", actual="false")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            resolved = _cott_match_value.value
            return (((resolved).method == (request).method))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.resolve_request", clause="ensures:1", phase="ensures", span={"end_byte":3014,"end_column":69,"end_line":106,"start_byte":2950,"start_column":5,"start_line":106}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            resolved = _cott_match_value.value
            return (((resolved).json_body == (request).json_body))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.resolve_request", clause="ensures:2", phase="ensures", span={"end_byte":3089,"end_column":75,"end_line":107,"start_byte":3019,"start_column":5,"start_line":107}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[RequestDocument, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def normalize_json_content(request: RequestDocument) -> Result[RequestDocument, PostingError]:
    request = _cott_validate_abi(request, RequestDocument, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/normalize_json_content.py", "484f3f97b916849e3d04d1a1a14def0fda681e619f1e54f1f67d0d9070941d8d", "normalize_json_content", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.normalize_json_content")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.normalize_json_content"
        if _error.span is None:
            _error.span = {"end_byte":3622,"end_column":1,"end_line":124,"start_byte":3187,"start_column":1,"start_line":114}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.normalize_json_content", phase="implementation-call", span={"end_byte":3622,"end_column":1,"end_line":124,"start_byte":3187,"start_column":1,"start_line":114}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.normalize_json_content", phase="implementation-call", span={"end_byte":3622,"end_column":1,"end_line":124,"start_byte":3187,"start_column":1,"start_line":114}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[RequestDocument, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.normalize_json_content", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidJson,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.normalize_json_content", phase="error", span={"end_byte":3622,"end_column":1,"end_line":124,"start_byte":3187,"start_column":1,"start_line":114}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.normalize_json_content", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            normalized = _cott_match_value.value
            return (((normalized).name == (request).name))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.normalize_json_content", clause="ensures:0", phase="ensures", span={"end_byte":3349,"end_column":69,"end_line":115,"start_byte":3285,"start_column":5,"start_line":115}, expected="true", actual="false")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            normalized = _cott_match_value.value
            return (((normalized).method == (request).method))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.normalize_json_content", clause="ensures:1", phase="ensures", span={"end_byte":3422,"end_column":73,"end_line":116,"start_byte":3354,"start_column":5,"start_line":116}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            normalized = _cott_match_value.value
            return (((normalized).url == (request).url))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.normalize_json_content", clause="ensures:2", phase="ensures", span={"end_byte":3489,"end_column":67,"end_line":117,"start_byte":3427,"start_column":5,"start_line":117}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            normalized = _cott_match_value.value
            return (((normalized).json_body == (request).json_body))
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.normalize_json_content", clause="ensures:3", phase="ensures", span={"end_byte":3568,"end_column":79,"end_line":118,"start_byte":3494,"start_column":5,"start_line":118}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[RequestDocument, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def export_curl(request: RequestDocument, variables: str) -> Result[str, PostingError]:
    request = _cott_validate_abi(request, RequestDocument, path="$.request")
    variables = _cott_validate_abi(variables, str, path="$.variables")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/export_curl.py", "59e976387687c4832b49928d2931fb7c3a07746e1f90a810d6a27827d7b94186", "export_curl", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.export_curl")
        _result = _implementation(request, variables)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.export_curl"
        if _error.span is None:
            _error.span = {"end_byte":3885,"end_column":1,"end_line":133,"start_byte":3622,"start_column":1,"start_line":124}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.export_curl", phase="implementation-call", span={"end_byte":3885,"end_column":1,"end_line":133,"start_byte":3622,"start_column":1,"start_line":124}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.export_curl", phase="implementation-call", span={"end_byte":3885,"end_column":1,"end_line":133,"start_byte":3622,"start_column":1,"start_line":124}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.export_curl", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidHeader, PostingError_InvalidJson, PostingError_UnresolvedVariable,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.export_curl", phase="error", span={"end_byte":3885,"end_column":1,"end_line":133,"start_byte":3622,"start_column":1,"start_line":124}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.export_curl", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            curl = _cott_match_value.value
            return ((len(curl) > 0))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.export_curl", clause="ensures:0", phase="ensures", span={"end_byte":3752,"end_column":44,"end_line":125,"start_byte":3713,"start_column":5,"start_line":125}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

def export_yaml(request: RequestDocument) -> str:
    request = _cott_validate_abi(request, RequestDocument, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/export_yaml.py", "1be40c54e92964f3ebc69ea38cc9fccbb1cb034852a124b6f906f178de1a45b4", "export_yaml", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.export_yaml")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.export_yaml"
        if _error.span is None:
            _error.span = {"end_byte":3950,"end_column":1,"end_line":136,"start_byte":3885,"start_column":1,"start_line":133}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.export_yaml", phase="implementation-call", span={"end_byte":3950,"end_column":1,"end_line":136,"start_byte":3885,"start_column":1,"start_line":133}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.export_yaml", phase="implementation-call", span={"end_byte":3950,"end_column":1,"end_line":136,"start_byte":3885,"start_column":1,"start_line":133}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def send_request(request: RequestDocument, timeout_ms: U32) -> Result[HttpResponse, PostingError]:
    request = _cott_validate_abi(request, RequestDocument, path="$.request")
    timeout_ms = _cott_validate_abi(timeout_ms, U32, path="$.timeout_ms")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/posting/client/send_request.py", "bba6069f56f406057c75b147d5040724a4b4ec155ae711e7ddce66364fec0252", "send_request", expected_project_name="real-posting", expected_cott_symbol="real.posting.client.send_request")
        _result = _implementation(request, timeout_ms)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.posting.client.send_request"
        if _error.span is None:
            _error.span = {"end_byte":4306,"end_column":1,"end_line":146,"start_byte":3950,"start_column":1,"start_line":136}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.posting.client.send_request", phase="implementation-call", span={"end_byte":4306,"end_column":1,"end_line":146,"start_byte":3950,"start_column":1,"start_line":136}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.posting.client.send_request", phase="implementation-call", span={"end_byte":4306,"end_column":1,"end_line":146,"start_byte":3950,"start_column":1,"start_line":136}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[HttpResponse, PostingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.posting.client.send_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PostingError_InvalidHeader, PostingError_InvalidJson, PostingError_InvalidRequest, PostingError_NetworkFailed, PostingError_TimedOut,):
            raise CottContractViolation("returned error is not allowed", symbol="real.posting.client.send_request", phase="error", span={"end_byte":4306,"end_column":1,"end_line":146,"start_byte":3950,"start_column":1,"start_line":136}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.posting.client.send_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            response = _cott_match_value.value
            return (((response).status > 0))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.posting.client.send_request", clause="ensures:0", phase="ensures", span={"end_byte":4102,"end_column":55,"end_line":137,"start_byte":4052,"start_column":5,"start_line":137}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[HttpResponse, PostingError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["CollectionEntry", "Header", "HttpMethod", "HttpMethod_Delete", "HttpMethod_Get", "HttpMethod_Head", "HttpMethod_Options", "HttpMethod_Patch", "HttpMethod_Post", "HttpMethod_Put", "HttpResponse", "PostingError", "PostingError_CollectionRootMissing", "PostingError_InvalidHeader", "PostingError_InvalidJson", "PostingError_InvalidRequest", "PostingError_InvalidYaml", "PostingError_NetworkFailed", "PostingError_ReadFailed", "PostingError_RequestMissing", "PostingError_SaveFailed", "PostingError_TimedOut", "PostingError_UnresolvedVariable", "RequestDocument", "discover_collections", "export_curl", "export_yaml", "extract_url_variables", "load_request", "make_request", "normalize_json_content", "parse_method", "resolve_request", "save_request", "send_request"]
