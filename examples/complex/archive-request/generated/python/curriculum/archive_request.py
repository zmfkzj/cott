from __future__ import annotations

import dataclasses as _dataclasses
from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.archive_request_types import ArchivePlan, ArchiveRequest, ArchiveRequestError, ArchiveRequestError_EmptySelection, ArchiveRequestError_InvalidUrl, CaptureKind, CaptureKind_Html, CaptureKind_Media

def canonicalize_archive_url(url: str) -> Result[str, ArchiveRequestError]:
    """Parse an HTTP or HTTPS URL and return its deterministic canonical form.
The scheme and host are lowercased while user information, port, path,
query, and fragment are retained. Invalid or malformed URLs return
InvalidUrl."""
    url = _cott_validate_abi(url, str, path="$.url")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/archive_request/canonicalize_archive_url.py", "2b7991952431e3d2f0aeaffc4eb01cd99847b184afc485eea47cb9dd1fa78575", "canonicalize_archive_url", expected_project_name="archive-request", expected_cott_symbol="curriculum.archive_request.canonicalize_archive_url")
        _result = _implementation(url)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.archive_request.canonicalize_archive_url"
        if _error.span is None:
            _error.span = {"end_byte":749,"end_column":1,"end_line":34,"start_byte":294,"start_column":1,"start_line":20}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.archive_request.canonicalize_archive_url", phase="implementation-call", span={"end_byte":749,"end_column":1,"end_line":34,"start_byte":294,"start_column":1,"start_line":20}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.archive_request.canonicalize_archive_url", phase="implementation-call", span={"end_byte":749,"end_column":1,"end_line":34,"start_byte":294,"start_column":1,"start_line":20}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, ArchiveRequestError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.archive_request.canonicalize_archive_url", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ArchiveRequestError_InvalidUrl,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.archive_request.canonicalize_archive_url", phase="error", span={"end_byte":749,"end_column":1,"end_line":34,"start_byte":294,"start_column":1,"start_line":20}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.archive_request.canonicalize_archive_url", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        canonical_url = _result.value
        if not ((len(canonical_url) > 0)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.archive_request.canonicalize_archive_url", clause="ensures:1", phase="ensures", span={"end_byte":689,"end_column":62,"end_line":28,"start_byte":632,"start_column":5,"start_line":28}, expected="true", actual="false")
    return _result

def compose_archive_plan(canonical_url: str, include_html: bool, include_media: bool) -> ArchivePlan:
    """Assemble an archive plan from a canonical URL and the requested capture
kinds. HTML precedes media when both kinds are selected."""
    canonical_url = _cott_validate_abi(canonical_url, str, path="$.canonical_url")
    include_html = _cott_validate_abi(include_html, bool, path="$.include_html")
    include_media = _cott_validate_abi(include_media, bool, path="$.include_media")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/archive_request/compose_archive_plan.py", "604e7ebaa251ae4a912ef38dfe394949f155a7c6c58ac5bdc627ec39eea0aa28", "compose_archive_plan", expected_project_name="archive-request", expected_cott_symbol="curriculum.archive_request.compose_archive_plan")
        _result = _implementation(canonical_url, include_html, include_media)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.archive_request.compose_archive_plan"
        if _error.span is None:
            _error.span = {"end_byte":1075,"end_column":1,"end_line":44,"start_byte":749,"start_column":1,"start_line":34}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.archive_request.compose_archive_plan", phase="implementation-call", span={"end_byte":1075,"end_column":1,"end_line":44,"start_byte":749,"start_column":1,"start_line":34}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.archive_request.compose_archive_plan", phase="implementation-call", span={"end_byte":1075,"end_column":1,"end_line":44,"start_byte":749,"start_column":1,"start_line":34}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, ArchivePlan, path="$.return")
    if not (((_result).canonical_url == canonical_url)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.archive_request.compose_archive_plan", clause="ensures:1", phase="ensures", span={"end_byte":1057,"end_column":50,"end_line":40,"start_byte":1012,"start_column":5,"start_line":40}, expected="true", actual="false")
    return _result

def plan_archive(request: ArchiveRequest) -> Result[ArchivePlan, ArchiveRequestError]:
    """Reject a request with neither capture kind selected as EmptySelection before
canonicalizing its URL. Otherwise canonicalize the URL and compose the plan;
malformed URLs return InvalidUrl."""
    request = _cott_validate_abi(request, ArchiveRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (((not (request).include_html) and (not (request).include_media))):
        _expected_error = ArchiveRequestError_EmptySelection
        _expected_error_span = {"end_byte":1573,"end_column":107,"end_line":53,"start_byte":1471,"start_column":5,"start_line":53}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/archive_request/plan_archive.py", "ecc5c760c4838462045d5e3e0547cf6a42aa70577a883e10f84f0aeafb0aacb5", "plan_archive", expected_project_name="archive-request", expected_cott_symbol="curriculum.archive_request.plan_archive")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.archive_request.plan_archive"
        if _error.span is None:
            _error.span = {"end_byte":1631,"end_column":1,"end_line":57,"start_byte":1075,"start_column":1,"start_line":44}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.archive_request.plan_archive", phase="implementation-call", span={"end_byte":1631,"end_column":1,"end_line":57,"start_byte":1075,"start_column":1,"start_line":44}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.archive_request.plan_archive", phase="implementation-call", span={"end_byte":1631,"end_column":1,"end_line":57,"start_byte":1075,"start_column":1,"start_line":44}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ArchivePlan, ArchiveRequestError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.archive_request.plan_archive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ArchiveRequestError_InvalidUrl,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.archive_request.plan_archive", phase="error", span={"end_byte":1631,"end_column":1,"end_line":57,"start_byte":1075,"start_column":1,"start_line":44}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.archive_request.plan_archive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        plan = _result.value
        if not (((len((plan).canonical_url) > 0) and (len((plan).captures) > 0))):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.archive_request.plan_archive", clause="ensures:1", phase="ensures", span={"end_byte":1465,"end_column":84,"end_line":51,"start_byte":1386,"start_column":5,"start_line":51}, expected="true", actual="false")
    return _result

__all__ = ["ArchivePlan", "ArchiveRequest", "ArchiveRequestError", "ArchiveRequestError_EmptySelection", "ArchiveRequestError_InvalidUrl", "CaptureKind", "CaptureKind_Html", "CaptureKind_Media", "canonicalize_archive_url", "compose_archive_plan", "plan_archive"]
