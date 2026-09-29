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

from frogmouth.document_types import BrowserFailure, BrowserFailure_DoesNotExist, BrowserFailure_ForgeUnresolved, BrowserFailure_Load, BrowserFailure_NoSuchDirectory, BrowserFailure_NotADirectory, BrowserFailure_NotBookmarkable, BrowserFailure_UnhandledLink, LinkAction, LinkAction_Anchor, LinkAction_Failed, LinkAction_OpenExternally, LinkAction_Visit, LoadError, LoadError_LocalFailed, LoadError_RemoteFailed, RemoteDocument, RemoteDocument_Markdown, RemoteDocument_NotMarkdown, VisitOutcome, VisitOutcome_Failed, VisitOutcome_Loaded, VisitOutcome_OpenExternally
from frogmouth.model_types import BrowserContext, Dialog, Document, Forge, Forge_BitBucket, Forge_Codeberg, Forge_GitHub, Forge_GitLab, Location, LocationKind, LocationKind_Local, LocationKind_Remote

def load_local_document(path: str) -> Result[Document, LoadError]:
    """Read the Markdown file at path from the file system the program runs
against: the fs fixture root while a Cott scenario with an fs fixture is
active, otherwise the host file system, where a relative path is relative
to the process working directory. The bytes are decoded as UTF-8, with
each invalid sequence replaced by U+FFFD as the remote loader does, so a
file that is not UTF-8 still loads; each "\\r\\n" or lone "\\r" line ending
becomes "\\n", as Python's universal-newline text reading does; nothing
else changes. The document's location is the Local location path. A
failure to open or read the file, a directory included, is
LocalFailed(path, the error text as Python's str() renders the OSError)."""
    path = _cott_validate_abi(path, str, path="$.path")
    if not (_cott_contract_condition(((len(path) > 0)), "frogmouth.document.load_local_document", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.document.load_local_document", clause="requires:1", phase="requires", span={"end_byte":2021,"end_column":26,"end_line":56,"start_byte":2000,"start_column":5,"start_line":56}, expected="true", actual="false")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/load_local_document.py", "b22076d49fe1e7188b706e3904287dd4d4bd27759a2071d3e05b4cad6e983fe5", "load_local_document", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.load_local_document")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.load_local_document"
        if _error.span is None:
            _error.span = {"end_byte":2349,"end_column":1,"end_line":66,"start_byte":1165,"start_column":1,"start_line":42}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.load_local_document", phase="implementation-call", span={"end_byte":2349,"end_column":1,"end_line":66,"start_byte":1165,"start_column":1,"start_line":42}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.load_local_document", phase="implementation-call", span={"end_byte":2349,"end_column":1,"end_line":66,"start_byte":1165,"start_column":1,"start_line":42}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Document, LoadError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.document.load_local_document", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (LoadError_LocalFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.document.load_local_document", phase="error", span={"end_byte":2349,"end_column":1,"end_line":66,"start_byte":1165,"start_column":1,"start_line":42}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.document.load_local_document", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "frogmouth.document.load_local_document", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is LoadError_LocalFailed:
        _cott_contract_condition(True, "frogmouth.document.load_local_document", "error:5")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            document = _cott_match_value.value
            return (_cott_contract_condition((((((document).location).kind == LocationKind_Local()) and (((document).location).target == path))), "frogmouth.document.load_local_document", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.document.load_local_document", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_local_document", clause="ensures:2", phase="ensures", span={"end_byte":2141,"end_column":119,"end_line":58,"start_byte":2027,"start_column":5,"start_line":58}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            document = _cott_match_value.value
            return (_cott_contract_condition(((not ("\r" in (document).markdown))), "frogmouth.document.load_local_document", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.document.load_local_document", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_local_document", clause="ensures:3", phase="ensures", span={"end_byte":2214,"end_column":73,"end_line":59,"start_byte":2146,"start_column":5,"start_line":59}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is LoadError_LocalFailed and True and True:
            failed = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((failed == path)), "frogmouth.document.load_local_document", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.document.load_local_document", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.load_local_document", clause="ensures:4", phase="ensures", span={"end_byte":2289,"end_column":75,"end_line":60,"start_byte":2219,"start_column":5,"start_line":60}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Document, LoadError], path="$.return", validator=_cott_validate_abi)
    return _result

def fetch_remote_document(url: str) -> Result[RemoteDocument, LoadError]:
    """GET url with the header "User-Agent: frogmouth v0.9.1", following
redirects, with a 5 second timeout for connecting and for each read. A
transport failure (name resolution, connection, timeout, redirect loop or
malformed response) is RemoteFailed(url, a description of the failure).
A final status outside 200-299 is RemoteFailed(url, MESSAGE), where
MESSAGE is "KIND 'STATUS REASON' for url 'FINAL'\\nFor more information
check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/STATUS"
with KIND "Informational response" (1xx), "Redirect response" (3xx),
"Client error" (4xx), "Server error" (5xx) or "Invalid status code",
REASON the response's reason phrase and FINAL the URL of the final
request.

On success the Content-Type header, empty when absent, decides. A value
starting with "text/plain", "text/markdown" or "text/x-markdown" gives
Markdown of the document at the Remote location url, whose markdown is
the body decoded with the Content-Type charset parameter when it names a
known codec and UTF-8 otherwise, replacing undecodable bytes with U+FFFD.
Any other value gives NotMarkdown of that value."""
    url = _cott_validate_abi(url, str, path="$.url")
    if not (_cott_contract_condition(((_cott_starts_with(url, "http://") or _cott_starts_with(url, "https://"))), "frogmouth.document.fetch_remote_document", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.document.fetch_remote_document", clause="requires:1", phase="requires", span={"end_byte":3708,"end_column":75,"end_line":88,"start_byte":3638,"start_column":5,"start_line":88}, expected="true", actual="false")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/fetch_remote_document.py", "dbf2a9d3c361c4ea3a27f667a5e492d93460be76e61dffc4f5db8f9ab31184bb", "fetch_remote_document", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.fetch_remote_document")
        _result = _implementation(url)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.fetch_remote_document"
        if _error.span is None:
            _error.span = {"end_byte":4194,"end_column":1,"end_line":98,"start_byte":2349,"start_column":1,"start_line":66}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.fetch_remote_document", phase="implementation-call", span={"end_byte":4194,"end_column":1,"end_line":98,"start_byte":2349,"start_column":1,"start_line":66}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.fetch_remote_document", phase="implementation-call", span={"end_byte":4194,"end_column":1,"end_line":98,"start_byte":2349,"start_column":1,"start_line":66}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[RemoteDocument, LoadError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.document.fetch_remote_document", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (LoadError_RemoteFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.document.fetch_remote_document", phase="error", span={"end_byte":4194,"end_column":1,"end_line":98,"start_byte":2349,"start_column":1,"start_line":66}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.document.fetch_remote_document", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "frogmouth.document.fetch_remote_document", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is LoadError_RemoteFailed:
        _cott_contract_condition(True, "frogmouth.document.fetch_remote_document", "error:5")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and type(_cott_match_value.value) is RemoteDocument_Markdown and True:
            document = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[0].name)
            return (_cott_contract_condition((((((document).location).kind == LocationKind_Remote()) and (((document).location).target == url))), "frogmouth.document.fetch_remote_document", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.document.fetch_remote_document", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.fetch_remote_document", clause="ensures:2", phase="ensures", span={"end_byte":3853,"end_column":144,"end_line":90,"start_byte":3714,"start_column":5,"start_line":90}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and type(_cott_match_value.value) is RemoteDocument_NotMarkdown and True:
            content_type = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[0].name)
            return (_cott_contract_condition(((not ((_cott_starts_with(content_type, "text/plain") or _cott_starts_with(content_type, "text/markdown")) or _cott_starts_with(content_type, "text/x-markdown")))), "frogmouth.document.fetch_remote_document", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.document.fetch_remote_document", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.fetch_remote_document", clause="ensures:3", phase="ensures", span={"end_byte":4060,"end_column":207,"end_line":91,"start_byte":3858,"start_column":5,"start_line":91}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is LoadError_RemoteFailed and True and True:
            failed = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((failed == url)), "frogmouth.document.fetch_remote_document", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.document.fetch_remote_document", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.fetch_remote_document", clause="ensures:4", phase="ensures", span={"end_byte":4135,"end_column":75,"end_line":92,"start_byte":4065,"start_column":5,"start_line":92}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[RemoteDocument, LoadError], path="$.return", validator=_cott_validate_abi)
    return _result

def visit_location(location: Location, context: BrowserContext) -> VisitOutcome:
    """Visit location the way the viewer does.

When frogmouth.locations.is_markdown_location(location,
context.markdown_extensions) holds, a Local location is loaded with
frogmouth.document.load_local_document of PATH, where PATH is
frogmouth.locations.resolve_local_path(location.target, context.home,
context.working_directory); a Remote location is fetched with
frogmouth.document.fetch_remote_document(location.target). A loaded
Markdown document is Loaded; NotMarkdown is OpenExternally of
location.target; a LoadError is Failed(Load(error)).

Any other Remote location is OpenExternally of its target without a
request. Any other Local location is classified with
frogmouth.locations.inspect_local_path(PATH): Missing is
Failed(DoesNotExist(location.target)), any other kind is OpenExternally
of "file://" followed by PATH."""
    location = _cott_validate_abi(location, Location, path="$.location")
    context = _cott_validate_abi(context, BrowserContext, path="$.context")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/visit_location.py", "f62515680f29c8a509ba2c748db3a989caf000c244d252f534795fe90afe3c21", "visit_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.visit_location")
        _result = _implementation(location, context)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.visit_location"
        if _error.span is None:
            _error.span = {"end_byte":5776,"end_column":1,"end_line":126,"start_byte":4194,"start_column":1,"start_line":98}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.visit_location", phase="implementation-call", span={"end_byte":5776,"end_column":1,"end_line":126,"start_byte":4194,"start_column":1,"start_line":98}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.visit_location", phase="implementation-call", span={"end_byte":5776,"end_column":1,"end_line":126,"start_byte":4194,"start_column":1,"start_line":98}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, VisitOutcome, path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is VisitOutcome_Loaded and True:
            document = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            return (_cott_contract_condition(((((document).location).kind == (location).kind)), "frogmouth.document.visit_location", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.document.visit_location", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.visit_location", clause="ensures:1", phase="ensures", span={"end_byte":5267,"end_column":85,"end_line":118,"start_byte":5187,"start_column":5,"start_line":118}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is VisitOutcome_Loaded and True:
            document = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            return (_cott_contract_condition((((not ((location).kind == LocationKind_Remote())) or (((document).location).target == (location).target))), "frogmouth.document.visit_location", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.document.visit_location", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.visit_location", clause="ensures:2", phase="ensures", span={"end_byte":5400,"end_column":133,"end_line":119,"start_byte":5272,"start_column":5,"start_line":119}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is VisitOutcome_OpenExternally and True:
            target = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            return (_cott_contract_condition((((not ((location).kind == LocationKind_Remote())) or (target == (location).target))), "frogmouth.document.visit_location", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.document.visit_location", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.visit_location", clause="ensures:3", phase="ensures", span={"end_byte":5521,"end_column":121,"end_line":120,"start_byte":5405,"start_column":5,"start_line":120}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is VisitOutcome_OpenExternally and True:
            target = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            return (_cott_contract_condition((((not ((location).kind == LocationKind_Local())) or _cott_starts_with(target, "file://"))), "frogmouth.document.visit_location", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.document.visit_location", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.visit_location", clause="ensures:4", phase="ensures", span={"end_byte":5646,"end_column":125,"end_line":121,"start_byte":5526,"start_column":5,"start_line":121}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is VisitOutcome_Failed and type(getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)) is BrowserFailure_DoesNotExist and True:
            path = getattr(getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name), _dataclasses.fields(type(getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)))[0].name)
            return (_cott_contract_condition(((path == (location).target)), "frogmouth.document.visit_location", "ensures:5"))
        _cott_contract_condition((False), "frogmouth.document.visit_location", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.visit_location", clause="ensures:5", phase="ensures", span={"end_byte":5740,"end_column":94,"end_line":122,"start_byte":5651,"start_column":5,"start_line":122}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, VisitOutcome, path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_link(href: str, current: Option[Location], context: BrowserContext) -> LinkAction:
    """Decide where a clicked Markdown link leads. href is already
percent-decoded; current is the location being viewed, if any.

1. An href starting with "#" is Anchor of the rest of href.
2. Otherwise split href at its first "#" into BASE and FRAGMENT. ANCHOR
   is FRAGMENT when href has a "#" and FRAGMENT is not empty, otherwise
   Nothing.
3. When frogmouth.locations.remote_location(BASE) is a location, Visit
   it with ANCHOR.
4. When current is a Remote location, resolve BASE against its target
   as an RFC 3986 reference, as Python urllib.parse.urljoin does. A
   result that remote_location recognizes is Visit of that location with
   ANCHOR; any other result is OpenExternally of it.
5. Otherwise, when frogmouth.locations.normalize_local_path(
   context.working_directory, BASE) is not Missing according to
   frogmouth.locations.inspect_local_path, Visit that Local path with
   ANCHOR.
6. Otherwise, when current is a Local location, let DIR be
   normalize_local_path(context.working_directory, current.target)
   without its last segment and separating "/" ("/" when only the root
   remains, "." when nothing remains). When normalize_local_path(DIR,
   BASE) is not Missing, Visit that Local path with ANCHOR.
7. Otherwise the result is Failed(UnhandledLink(href))."""
    href = _cott_validate_abi(href, str, path="$.href")
    current = _cott_validate_abi(current, Option[Location], path="$.current")
    context = _cott_validate_abi(context, BrowserContext, path="$.context")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/resolve_link.py", "03e71c649ad8893bb4b21ad2a915d2719788ae32e9e6effd80710c5d94c24a70", "resolve_link", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.resolve_link")
        _result = _implementation(href, current, context)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.resolve_link"
        if _error.span is None:
            _error.span = {"end_byte":7519,"end_column":1,"end_line":159,"start_byte":5776,"start_column":1,"start_line":126}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.resolve_link", phase="implementation-call", span={"end_byte":7519,"end_column":1,"end_line":159,"start_byte":5776,"start_column":1,"start_line":126}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.resolve_link", phase="implementation-call", span={"end_byte":7519,"end_column":1,"end_line":159,"start_byte":5776,"start_column":1,"start_line":126}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, LinkAction, path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is LinkAction_Anchor and True:
            anchor = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            return (_cott_contract_condition((_cott_ends_with(href, anchor)), "frogmouth.document.resolve_link", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.document.resolve_link", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.resolve_link", clause="ensures:1", phase="ensures", span={"end_byte":7330,"end_column":65,"end_line":153,"start_byte":7270,"start_column":5,"start_line":153}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is LinkAction_Visit and True and type(getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[1].name)) is Some and True:
            anchor = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[1].name).value
            return (_cott_contract_condition((_cott_ends_with(href, anchor)), "frogmouth.document.resolve_link", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.document.resolve_link", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.resolve_link", clause="ensures:2", phase="ensures", span={"end_byte":7410,"end_column":80,"end_line":154,"start_byte":7335,"start_column":5,"start_line":154}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is LinkAction_Failed and type(getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)) is BrowserFailure_UnhandledLink and True:
            link = getattr(getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name), _dataclasses.fields(type(getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)))[0].name)
            return (_cott_contract_condition(((link == href)), "frogmouth.document.resolve_link", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.document.resolve_link", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.resolve_link", clause="ensures:3", phase="ensures", span={"end_byte":7492,"end_column":82,"end_line":155,"start_byte":7415,"start_column":5,"start_line":155}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, LinkAction, path="$.return", validator=_cott_validate_abi)
    return _result

def select_browsable_entries(paths: CottList[str], extensions: CottList[str]) -> CottList[str]:
    """Filter a directory listing of non-empty paths for the local file
browser, keeping the given order. A path is kept when its name (last
"/"-separated segment) does not start with "." and
frogmouth.locations.inspect_local_path says Directory, or when
inspect_local_path says File and frogmouth.locations.is_markdown_location
of the Local location path holds for extensions, so Markdown files are
kept even when hidden."""
    paths = _cott_validate_abi(paths, CottList[str], path="$.paths")
    extensions = _cott_validate_abi(extensions, CottList[str], path="$.extensions")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/select_browsable_entries.py", "997eaf289bdd8ed78568508baa7881ba9c98dd7dc65cf8dfafb853f67ea32688", "select_browsable_entries", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.select_browsable_entries")
        _result = _implementation(paths, extensions)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.select_browsable_entries"
        if _error.span is None:
            _error.span = {"end_byte":8129,"end_column":1,"end_line":174,"start_byte":7519,"start_column":1,"start_line":159}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.select_browsable_entries", phase="implementation-call", span={"end_byte":8129,"end_column":1,"end_line":174,"start_byte":7519,"start_column":1,"start_line":159}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.select_browsable_entries", phase="implementation-call", span={"end_byte":8129,"end_column":1,"end_line":174,"start_byte":7519,"start_column":1,"start_line":159}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[str], path="$.return")
    if not (_cott_contract_condition(((len(_result) <= len(paths))), "frogmouth.document.select_browsable_entries", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.select_browsable_entries", clause="ensures:1", phase="ensures", span={"end_byte":8102,"end_column":36,"end_line":170,"start_byte":8071,"start_column":5,"start_line":170}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=_cott_validate_abi)
    return _result

def open_external(target: str) -> bool:
    """Ask the desktop to open target, a web, mail or file URL, with its default
application: start the opener program ("open" on macOS, "xdg-open"
elsewhere) with target as its only argument, standard input, output and
error on the null device, in a new session, without waiting for it. The
result is true when the opener process started and false when it could
not be started (for example because the program is not installed)."""
    target = _cott_validate_abi(target, str, path="$.target")
    if not (_cott_contract_condition(((len(target) > 0)), "frogmouth.document.open_external", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.document.open_external", clause="requires:1", phase="requires", span={"end_byte":8663,"end_column":28,"end_line":184,"start_byte":8640,"start_column":5,"start_line":184}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/open_external.py", "b64b1337bab49281007a6cf7f18323c378052182fa33ed1449039fa8a9ac5d1c", "open_external", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.open_external")
        _result = _implementation(target)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.open_external"
        if _error.span is None:
            _error.span = {"end_byte":8693,"end_column":1,"end_line":188,"start_byte":8129,"start_column":1,"start_line":174}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.open_external", phase="implementation-call", span={"end_byte":8693,"end_column":1,"end_line":188,"start_byte":8129,"start_column":1,"start_line":174}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.open_external", phase="implementation-call", span={"end_byte":8693,"end_column":1,"end_line":188,"start_byte":8129,"start_column":1,"start_line":174}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, bool, path="$.return")
    _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=_cott_validate_abi)
    return _result

def failure_dialog(failure: BrowserFailure) -> Dialog:
    """The error dialog that reports failure. Every interpolated value (PATH,
HREF, URL, MESSAGE) is escaped like rich.markup.escape so it is shown
literally; FORGE is "GitHub", "GitLab", "BitBucket" or "Codeberg".

DoesNotExist(PATH): "Does not exist" / "Unable to open PATH because it
does not exist."
NoSuchDirectory(PATH): "No such directory" / "PATH does not exist."
NotADirectory(PATH): "Not a directory" / "PATH is not a directory."
ForgeUnresolved(FORGE): "Unable to work out a FORGE URL" / "After trying
a few options it hasn't been possible to work out the FORGE URL.\\n\\n
Perhaps the file you're after is on an unusual branch, or the spelling is
wrong?" (the two paragraphs are separated by exactly "\\n\\n").
UnhandledLink(HREF): "Unable to handle link" / "Unable to work out how to
handle this link:\\n\\nHREF"
NotBookmarkable: "Not a bookmarkable location" / "The current view can't
be bookmarked."
Load(LocalFailed(PATH, MESSAGE)): "Error loading local document" /
"PATH\\n\\nMESSAGE."
Load(RemoteFailed(URL, MESSAGE)): "Error getting document" / "MESSAGE"
Titles and messages contain nothing else."""
    failure = _cott_validate_abi(failure, BrowserFailure, path="$.failure")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/document/failure_dialog.py", "0ea77c26f972dddf6928eda4a427408ff87777db1be0ed893bd0c6045c6d98d5", "failure_dialog", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.document.failure_dialog")
        _result = _implementation(failure)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.document.failure_dialog"
        if _error.span is None:
            _error.span = {"end_byte":11727,"end_column":1,"end_line":228,"start_byte":8693,"start_column":1,"start_line":188}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.document.failure_dialog", phase="implementation-call", span={"end_byte":11727,"end_column":1,"end_line":228,"start_byte":8693,"start_column":1,"start_line":188}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.document.failure_dialog", phase="implementation-call", span={"end_byte":11727,"end_column":1,"end_line":228,"start_byte":8693,"start_column":1,"start_line":188}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Dialog, path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is BrowserFailure_DoesNotExist and True:
            return (_cott_contract_condition((((_result).title == "Does not exist")), "frogmouth.document.failure_dialog", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.document.failure_dialog", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.failure_dialog", clause="ensures:1", phase="ensures", span={"end_byte":10042,"end_column":95,"end_line":212,"start_byte":9952,"start_column":5,"start_line":212}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is BrowserFailure_NoSuchDirectory and True:
            return (_cott_contract_condition((((_result).title == "No such directory")), "frogmouth.document.failure_dialog", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.document.failure_dialog", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.failure_dialog", clause="ensures:2", phase="ensures", span={"end_byte":10143,"end_column":101,"end_line":213,"start_byte":10047,"start_column":5,"start_line":213}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is BrowserFailure_NotADirectory and True:
            return (_cott_contract_condition((((_result).title == "Not a directory")), "frogmouth.document.failure_dialog", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.document.failure_dialog", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.failure_dialog", clause="ensures:3", phase="ensures", span={"end_byte":10240,"end_column":97,"end_line":214,"start_byte":10148,"start_column":5,"start_line":214}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is BrowserFailure_ForgeUnresolved and True:
            forge = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            return (_cott_contract_condition((((not (forge == Forge_GitHub())) or ((_result).title == "Unable to work out a GitHub URL"))), "frogmouth.document.failure_dialog", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.document.failure_dialog", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.failure_dialog", clause="ensures:4", phase="ensures", span={"end_byte":10388,"end_column":148,"end_line":215,"start_byte":10245,"start_column":5,"start_line":215}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is BrowserFailure_ForgeUnresolved and True:
            forge = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            return (_cott_contract_condition((((not (forge == Forge_GitLab())) or ((_result).title == "Unable to work out a GitLab URL"))), "frogmouth.document.failure_dialog", "ensures:5"))
        _cott_contract_condition((False), "frogmouth.document.failure_dialog", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.failure_dialog", clause="ensures:5", phase="ensures", span={"end_byte":10536,"end_column":148,"end_line":216,"start_byte":10393,"start_column":5,"start_line":216}, expected="true", actual="false")
    def _cott_match_ensures_6() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is BrowserFailure_ForgeUnresolved and True:
            forge = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            return (_cott_contract_condition((((not (forge == Forge_BitBucket())) or ((_result).title == "Unable to work out a BitBucket URL"))), "frogmouth.document.failure_dialog", "ensures:6"))
        _cott_contract_condition((False), "frogmouth.document.failure_dialog", "ensures:6:applicable")
        return True
    if not (_cott_match_ensures_6()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.failure_dialog", clause="ensures:6", phase="ensures", span={"end_byte":10690,"end_column":154,"end_line":217,"start_byte":10541,"start_column":5,"start_line":217}, expected="true", actual="false")
    def _cott_match_ensures_7() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is BrowserFailure_ForgeUnresolved and True:
            forge = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            return (_cott_contract_condition((((not (forge == Forge_Codeberg())) or ((_result).title == "Unable to work out a Codeberg URL"))), "frogmouth.document.failure_dialog", "ensures:7"))
        _cott_contract_condition((False), "frogmouth.document.failure_dialog", "ensures:7:applicable")
        return True
    if not (_cott_match_ensures_7()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.failure_dialog", clause="ensures:7", phase="ensures", span={"end_byte":10842,"end_column":152,"end_line":218,"start_byte":10695,"start_column":5,"start_line":218}, expected="true", actual="false")
    def _cott_match_ensures_8() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is BrowserFailure_UnhandledLink and True:
            return (_cott_contract_condition((((_result).title == "Unable to handle link")), "frogmouth.document.failure_dialog", "ensures:8"))
        _cott_contract_condition((False), "frogmouth.document.failure_dialog", "ensures:8:applicable")
        return True
    if not (_cott_match_ensures_8()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.failure_dialog", clause="ensures:8", phase="ensures", span={"end_byte":10947,"end_column":105,"end_line":219,"start_byte":10847,"start_column":5,"start_line":219}, expected="true", actual="false")
    def _cott_match_ensures_9() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is BrowserFailure_NotBookmarkable:
            return (_cott_contract_condition(((((_result).title == "Not a bookmarkable location") and ((_result).message == "The current view can't be bookmarked."))), "frogmouth.document.failure_dialog", "ensures:9"))
        _cott_contract_condition((False), "frogmouth.document.failure_dialog", "ensures:9:applicable")
        return True
    if not (_cott_match_ensures_9()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.failure_dialog", clause="ensures:9", phase="ensures", span={"end_byte":11119,"end_column":172,"end_line":220,"start_byte":10952,"start_column":5,"start_line":220}, expected="true", actual="false")
    def _cott_match_ensures_10() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is BrowserFailure_Load and type(getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)) is LoadError_LocalFailed and True and True:
            return (_cott_contract_condition((((_result).title == "Error loading local document")), "frogmouth.document.failure_dialog", "ensures:10"))
        _cott_contract_condition((False), "frogmouth.document.failure_dialog", "ensures:10:applicable")
        return True
    if not (_cott_match_ensures_10()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.failure_dialog", clause="ensures:10", phase="ensures", span={"end_byte":11248,"end_column":129,"end_line":221,"start_byte":11124,"start_column":5,"start_line":221}, expected="true", actual="false")
    def _cott_match_ensures_11() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is BrowserFailure_Load and type(getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)) is LoadError_RemoteFailed and True and True:
            return (_cott_contract_condition((((_result).title == "Error getting document")), "frogmouth.document.failure_dialog", "ensures:11"))
        _cott_contract_condition((False), "frogmouth.document.failure_dialog", "ensures:11:applicable")
        return True
    if not (_cott_match_ensures_11()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.failure_dialog", clause="ensures:11", phase="ensures", span={"end_byte":11372,"end_column":124,"end_line":222,"start_byte":11253,"start_column":5,"start_line":222}, expected="true", actual="false")
    def _cott_match_ensures_12() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is BrowserFailure_UnhandledLink and True:
            href = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            return (_cott_contract_condition((((not ((not ("[" in href)) and (not ("\\" in href)))) or _cott_ends_with((_result).message, href))), "frogmouth.document.failure_dialog", "ensures:12"))
        _cott_contract_condition((False), "frogmouth.document.failure_dialog", "ensures:12:applicable")
        return True
    if not (_cott_match_ensures_12()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.failure_dialog", clause="ensures:12", phase="ensures", span={"end_byte":11530,"end_column":158,"end_line":223,"start_byte":11377,"start_column":5,"start_line":223}, expected="true", actual="false")
    def _cott_match_ensures_13() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is BrowserFailure_Load and type(getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)) is LoadError_RemoteFailed and True and True:
            message = getattr(getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name), _dataclasses.fields(type(getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)))[1].name)
            return (_cott_contract_condition((((not ((not ("[" in message)) and (not ("\\" in message)))) or ((_result).message == message))), "frogmouth.document.failure_dialog", "ensures:13"))
        _cott_contract_condition((False), "frogmouth.document.failure_dialog", "ensures:13:applicable")
        return True
    if not (_cott_match_ensures_13()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.document.failure_dialog", clause="ensures:13", phase="ensures", span={"end_byte":11709,"end_column":179,"end_line":224,"start_byte":11535,"start_column":5,"start_line":224}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Dialog, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["BrowserFailure", "BrowserFailure_DoesNotExist", "BrowserFailure_ForgeUnresolved", "BrowserFailure_Load", "BrowserFailure_NoSuchDirectory", "BrowserFailure_NotADirectory", "BrowserFailure_NotBookmarkable", "BrowserFailure_UnhandledLink", "LinkAction", "LinkAction_Anchor", "LinkAction_Failed", "LinkAction_OpenExternally", "LinkAction_Visit", "LoadError", "LoadError_LocalFailed", "LoadError_RemoteFailed", "RemoteDocument", "RemoteDocument_Markdown", "RemoteDocument_NotMarkdown", "VisitOutcome", "VisitOutcome_Failed", "VisitOutcome_Loaded", "VisitOutcome_OpenExternally", "failure_dialog", "fetch_remote_document", "load_local_document", "open_external", "resolve_link", "select_browsable_entries", "visit_location"]
