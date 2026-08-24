from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.page_build_types import BuiltPage, PageBuildError, PageBuildError_BlankTitle, PageBuildError_InvalidSlug, PageSource

def escape_page_text(value: str) -> str:
    """Escape text for safe inclusion in generated page HTML.

Ampersands, angle brackets, and both quote characters are replaced with
their HTML character references. All other characters are preserved."""
    value = _cott_validate_abi(value, str, path="$.value")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/page_build/escape_page_text.py", "c9cd0f2d5c6c3f5b5335207003c6fcdf5986b27414cdd8e0678641ea8526c430", "escape_page_text", expected_project_name="page-build", expected_cott_symbol="curriculum.page_build.escape_page_text")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.page_build.escape_page_text"
        if _error.span is None:
            _error.span = {"end_byte":475,"end_column":1,"end_line":24,"start_byte":201,"start_column":1,"start_line":16}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.page_build.escape_page_text", phase="implementation-call", span={"end_byte":475,"end_column":1,"end_line":24,"start_byte":201,"start_column":1,"start_line":16}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.page_build.escape_page_text", phase="implementation-call", span={"end_byte":475,"end_column":1,"end_line":24,"start_byte":201,"start_column":1,"start_line":16}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    return _result

def render_page_html(title: str, body: str) -> str:
    """Render a page title and body as deterministic HTML.

The escaped title becomes one `h1`. Every nonempty body line becomes one
escaped `p` in source order; empty lines are omitted."""
    title = _cott_validate_abi(title, str, path="$.title")
    body = _cott_validate_abi(body, str, path="$.body")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/page_build/render_page_html.py", "2e3bd65d3fb5dd4238f73f23cb85bd14e586171d29a06d593d73f0f5db3fbd7a", "render_page_html", expected_project_name="page-build", expected_cott_symbol="curriculum.page_build.render_page_html")
        _result = _implementation(title, body)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.page_build.render_page_html"
        if _error.span is None:
            _error.span = {"end_byte":771,"end_column":1,"end_line":34,"start_byte":475,"start_column":1,"start_line":24}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.page_build.render_page_html", phase="implementation-call", span={"end_byte":771,"end_column":1,"end_line":34,"start_byte":475,"start_column":1,"start_line":24}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.page_build.render_page_html", phase="implementation-call", span={"end_byte":771,"end_column":1,"end_line":34,"start_byte":475,"start_column":1,"start_line":24}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not ((len(_result) > 0)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.page_build.render_page_html", clause="ensures:1", phase="ensures", span={"end_byte":769,"end_column":27,"end_line":32,"start_byte":747,"start_column":5,"start_line":32}, expected="true", actual="false")
    return _result

def build_page(source: PageSource) -> Result[BuiltPage, PageBuildError]:
    """Validate a page source and build its output path and HTML.

The slug must contain lowercase ASCII letters or digits in nonempty
segments separated by single hyphens. Slug validation precedes title
validation. A title containing only Unicode whitespace is rejected, while
accepted text is preserved. The output path is `<slug>/index.html`, and
`render_page_html` produces the page content."""
    source = _cott_validate_abi(source, PageSource, path="$.source")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/page_build/build_page.py", "d76084bc7d4e3c258aad5a9558e4d7a1512a054c088247457803b58fc9dafda7", "build_page", expected_project_name="page-build", expected_cott_symbol="curriculum.page_build.build_page")
        _result = _implementation(source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.page_build.build_page"
        if _error.span is None:
            _error.span = {"end_byte":1404,"end_column":1,"end_line":49,"start_byte":771,"start_column":1,"start_line":34}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.page_build.build_page", phase="implementation-call", span={"end_byte":1404,"end_column":1,"end_line":49,"start_byte":771,"start_column":1,"start_line":34}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.page_build.build_page", phase="implementation-call", span={"end_byte":1404,"end_column":1,"end_line":49,"start_byte":771,"start_column":1,"start_line":34}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[BuiltPage, PageBuildError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.page_build.build_page", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PageBuildError_InvalidSlug, PageBuildError_BlankTitle,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.page_build.build_page", phase="error", span={"end_byte":1404,"end_column":1,"end_line":49,"start_byte":771,"start_column":1,"start_line":34}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.page_build.build_page", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        page = _result.value
        if not ((len((page).html) > 0)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.page_build.build_page", clause="ensures:1", phase="ensures", span={"end_byte":1329,"end_column":49,"end_line":45,"start_byte":1285,"start_column":5,"start_line":45}, expected="true", actual="false")
    return _result

__all__ = ["BuiltPage", "PageBuildError", "PageBuildError_BlankTitle", "PageBuildError_InvalidSlug", "PageSource", "build_page", "escape_page_text", "render_page_html"]
