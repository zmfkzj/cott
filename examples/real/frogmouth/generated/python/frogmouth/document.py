from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_ends_with, _cott_starts_with

from frogmouth.document_types import LoadError, LoadError_InvalidEncoding, LoadError_NetworkFailed, LoadError_NotFound, LoadError_ReadFailed, LoadError_TooLarge, OpenError, OpenError_Load, OpenError_Navigation
from frogmouth.model_types import Document, Location, LocationKind, LocationKind_Http, LocationKind_Local
from frogmouth.navigation_types import NavigationError

def derive_title(location: Location, markdown: str) -> str:
    """Choose a document title. Split markdown into lines at LF and remove one
trailing CR from each. A heading line starts with a run of one to six "#"
characters (the whole leading run) followed by a space; its text is the rest
of the line with leading and trailing spaces and tabs removed. The title is
the text of the first heading line whose text is non-empty. Without one, the
title is the last non-empty "/"-separated segment of location.target, or
location.target itself when it has no non-empty segment. Only this line rule
applies: code blocks, setext headings and inline markup are not interpreted."""
    location = _cott_validate_abi(location, Location, path="$.location")
    markdown = _cott_validate_abi(markdown, str, path="$.markdown")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/derive_title.py", "f2f2e54bfbb106885b88aa585fd5e2e986fc1695fab756393ee3470ef0d14dfe", "derive_title", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.derive_title")
        _result = _implementation(location, markdown)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.derive_title"
        if _error.span is None:
            _error.span = {"end_byte":1315,"end_column":1,"end_line":35,"start_byte":398,"start_column":1,"start_line":17}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.derive_title", phase="implementation-call", span={"end_byte":1315,"end_column":1,"end_line":35,"start_byte":398,"start_column":1,"start_line":17}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.derive_title", phase="implementation-call", span={"end_byte":1315,"end_column":1,"end_line":35,"start_byte":398,"start_column":1,"start_line":17}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not (_cott_contract_condition(((len(_result) > 0)), "frogmouth.document.derive_title", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.derive_title", clause="ensures:1", phase="ensures", span={"end_byte":1139,"end_column":27,"end_line":29,"start_byte":1117,"start_column":5,"start_line":29}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result in markdown) or (_result in (location).target))), "frogmouth.document.derive_title", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.derive_title", clause="ensures:2", phase="ensures", span={"end_byte":1217,"end_column":78,"end_line":30,"start_byte":1144,"start_column":5,"start_line":30}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (not ("# " in markdown))) or (_result in (location).target))), "frogmouth.document.derive_title", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.derive_title", clause="ensures:3", phase="ensures", span={"end_byte":1297,"end_column":80,"end_line":31,"start_byte":1222,"start_column":5,"start_line":31}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def load_document(location: Location) -> Result[Document, LoadError]:
    """Load Markdown for location, reading at most 5242880 bytes (5 MiB) plus one
byte to detect a larger document.

Local: read the file at location.target from the file system the program
runs against: the fs fixture root while a Cott scenario with an fs fixture
is active, otherwise the host file system, where a relative target is
relative to the process working directory. A missing file is NotFound; any
other open or read failure is ReadFailed. While a scenario fs fixture is
active, a target the fixture does not permit (absolute, or outside the
fixture root) is a contract violation raised by the fixture, not a read
failure.

Http: send one GET to location.target, following redirects, with a 30000
millisecond timeout for the connection attempt and each blocking read. A
final status of 404 or 410 is NotFound. Any other final status outside
200-299 is NetworkFailed whose message contains the decimal status. Name
resolution, connection, timeout and incomplete-response failures are
NetworkFailed.

More than 5242880 bytes is TooLarge. Bytes that are not strict UTF-8 are
InvalidEncoding. The markdown is the decoded text with one leading U+FEFF
removed, otherwise unchanged, and the title is
frogmouth.document.derive_title(location, markdown). Every LoadError's
source is location.target."""
    location = _cott_validate_abi(location, Location, path="$.location")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/load_document.py", "bdb821602149fdbed895e9a2e02e301bd05901a0f43741fdf547dff696e363ae", "load_document", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.load_document")
        _result = _implementation(location)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.load_document"
        if _error.span is None:
            _error.span = {"end_byte":3545,"end_column":1,"end_line":79,"start_byte":1315,"start_column":1,"start_line":35}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.load_document", phase="implementation-call", span={"end_byte":3545,"end_column":1,"end_line":79,"start_byte":1315,"start_column":1,"start_line":35}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.load_document", phase="implementation-call", span={"end_byte":3545,"end_column":1,"end_line":79,"start_byte":1315,"start_column":1,"start_line":35}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Document, LoadError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.document.load_document", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (LoadError_NotFound, LoadError_InvalidEncoding, LoadError_TooLarge, LoadError_NetworkFailed, LoadError_ReadFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.document.load_document", phase="error", span={"end_byte":3545,"end_column":1,"end_line":79,"start_byte":1315,"start_column":1,"start_line":35}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.document.load_document", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "frogmouth.document.load_document", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is LoadError_NotFound:
        _cott_contract_condition(True, "frogmouth.document.load_document", "error:8")
    if type(_result) is Err and type(_result.error) is LoadError_InvalidEncoding:
        _cott_contract_condition(True, "frogmouth.document.load_document", "error:9")
    if type(_result) is Err and type(_result.error) is LoadError_TooLarge:
        _cott_contract_condition(True, "frogmouth.document.load_document", "error:10")
    if type(_result) is Err and type(_result.error) is LoadError_NetworkFailed:
        _cott_contract_condition(True, "frogmouth.document.load_document", "error:11")
    if type(_result) is Err and type(_result.error) is LoadError_ReadFailed:
        _cott_contract_condition(True, "frogmouth.document.load_document", "error:12")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            document = _cott_match_value.value
            return (_cott_contract_condition((((document).location == location)), "frogmouth.document.load_document", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.document.load_document", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_document", clause="ensures:1", phase="ensures", span={"end_byte":2861,"end_column":65,"end_line":63,"start_byte":2801,"start_column":5,"start_line":63}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            document = _cott_match_value.value
            return (_cott_contract_condition(((len((document).markdown) <= 5242880)), "frogmouth.document.load_document", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.document.load_document", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_document", clause="ensures:2", phase="ensures", span={"end_byte":2929,"end_column":68,"end_line":64,"start_byte":2866,"start_column":5,"start_line":64}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is LoadError_NotFound and True:
            source = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((source == (location).target)), "frogmouth.document.load_document", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.document.load_document", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_document", clause="ensures:3", phase="ensures", span={"end_byte":3009,"end_column":80,"end_line":65,"start_byte":2934,"start_column":5,"start_line":65}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is LoadError_InvalidEncoding and True:
            source = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((source == (location).target)), "frogmouth.document.load_document", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.document.load_document", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_document", clause="ensures:4", phase="ensures", span={"end_byte":3096,"end_column":87,"end_line":66,"start_byte":3014,"start_column":5,"start_line":66}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is LoadError_TooLarge and True:
            source = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((source == (location).target)), "frogmouth.document.load_document", "ensures:5"))
        _cott_contract_condition((False), "frogmouth.document.load_document", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_document", clause="ensures:5", phase="ensures", span={"end_byte":3176,"end_column":80,"end_line":67,"start_byte":3101,"start_column":5,"start_line":67}, expected="true", actual="false")
    def _cott_match_ensures_6() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is LoadError_NetworkFailed and True and True:
            source = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((source == (location).target)), "frogmouth.document.load_document", "ensures:6"))
        _cott_contract_condition((False), "frogmouth.document.load_document", "ensures:6:applicable")
        return True
    if not (_cott_match_ensures_6()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_document", clause="ensures:6", phase="ensures", span={"end_byte":3264,"end_column":88,"end_line":68,"start_byte":3181,"start_column":5,"start_line":68}, expected="true", actual="false")
    def _cott_match_ensures_7() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is LoadError_ReadFailed and True and True:
            source = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((source == (location).target)), "frogmouth.document.load_document", "ensures:7"))
        _cott_contract_condition((False), "frogmouth.document.load_document", "ensures:7:applicable")
        return True
    if not (_cott_match_ensures_7()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_document", clause="ensures:7", phase="ensures", span={"end_byte":3349,"end_column":85,"end_line":69,"start_byte":3269,"start_column":5,"start_line":69}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Document, LoadError], path="$.return", validator=_cott_validate_abi)
    return _result

def open_location(value: str, working_directory: Path) -> Result[Document, OpenError]:
    """The frogmouth composition root, used by the address bar and by reload. Call
frogmouth.navigation.resolve_location(value, working_directory); its error is
returned as OpenError.Navigation and nothing is loaded. Otherwise return
frogmouth.document.load_document of the resolved location, with its error
returned as OpenError.Load."""
    value = _cott_validate_abi(value, str, path="$.value")
    working_directory = _cott_validate_abi(working_directory, Path, path="$.working_directory")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((value == "") or (("://" in value) and (not (_cott_starts_with(value, "http://") or _cott_starts_with(value, "https://")))))), "frogmouth.document.open_location", "error:3:condition")):
        _expected_error = OpenError_Navigation
        _expected_error_span = {"end_byte":4399,"end_column":152,"end_line":91,"start_byte":4252,"start_column":5,"start_line":91}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/open_location.py", "b6c092a5f37c2338780c5613c058c33dbcf99ab3979047fd641742e7651c5ad2", "open_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.open_location")
        _result = _implementation(value, working_directory)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.open_location"
        if _error.span is None:
            _error.span = {"end_byte":4460,"end_column":1,"end_line":96,"start_byte":3545,"start_column":1,"start_line":79}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.open_location", phase="implementation-call", span={"end_byte":4460,"end_column":1,"end_line":96,"start_byte":3545,"start_column":1,"start_line":79}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.open_location", phase="implementation-call", span={"end_byte":4460,"end_column":1,"end_line":96,"start_byte":3545,"start_column":1,"start_line":79}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Document, OpenError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.document.open_location", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (OpenError_Load,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.document.open_location", phase="error", span={"end_byte":4460,"end_column":1,"end_line":96,"start_byte":3545,"start_column":1,"start_line":79}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.document.open_location", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "frogmouth.document.open_location", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is OpenError_Load:
        _cott_contract_condition(True, "frogmouth.document.open_location", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            document = _cott_match_value.value
            return (_cott_contract_condition((((not (((document).location).kind == LocationKind_Http())) or (((document).location).target == value))), "frogmouth.document.open_location", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.document.open_location", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.open_location", clause="ensures:1", phase="ensures", span={"end_byte":4118,"end_column":118,"end_line":88,"start_byte":4005,"start_column":5,"start_line":88}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            document = _cott_match_value.value
            return (_cott_contract_condition((((not (((document).location).kind == LocationKind_Local())) or _cott_ends_with(((document).location).target, value))), "frogmouth.document.open_location", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.document.open_location", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.open_location", clause="ensures:2", phase="ensures", span={"end_byte":4246,"end_column":128,"end_line":89,"start_byte":4123,"start_column":5,"start_line":89}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Document, OpenError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["LoadError", "LoadError_InvalidEncoding", "LoadError_NetworkFailed", "LoadError_NotFound", "LoadError_ReadFailed", "LoadError_TooLarge", "OpenError", "OpenError_Load", "OpenError_Navigation", "derive_title", "load_document", "open_location"]
