from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from real.yt_dlp_types import DownloadPlan, JsonMode, JsonMode_Lines, JsonMode_Single, MediaError, MediaError_HttpStatus, MediaError_InvalidInput, MediaError_InvalidRange, MediaError_InvalidTemplate, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_SizeLimit, MediaError_UnsupportedUrl, MediaItem, PlaylistRange, TransferReceipt, TransferRequest

def parse_batch_urls(batch: str, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]:
    """Parse trimmed batch URLs while ignoring configured comment prefixes."""
    batch = _cott_validate_abi(batch, str, path="$.batch")
    comment_prefixes = _cott_validate_abi(comment_prefixes, CottList[str], path="$.comment_prefixes")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/parse_batch_urls.py", "b095174c2b96203cbf7caa1be124b570b788dd4505d6f16215edee8e7a9776aa", "parse_batch_urls", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.parse_batch_urls")
        _result = _implementation(batch, comment_prefixes)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.parse_batch_urls"
        if _error.span is None:
            _error.span = {"end_byte":990,"end_column":1,"end_line":55,"start_byte":696,"start_column":1,"start_line":44}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.parse_batch_urls", phase="implementation-call", span={"end_byte":990,"end_column":1,"end_line":55,"start_byte":696,"start_column":1,"start_line":44}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.parse_batch_urls", phase="implementation-call", span={"end_byte":990,"end_column":1,"end_line":55,"start_byte":696,"start_column":1,"start_line":44}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.parse_batch_urls", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.parse_batch_urls", phase="error", span={"end_byte":990,"end_column":1,"end_line":55,"start_byte":696,"start_column":1,"start_line":44}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.parse_batch_urls", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            urls = _cott_match_value.value
            return ((len(urls) <= len(batch)))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.parse_batch_urls", clause="ensures:1", phase="ensures", span={"end_byte":937,"end_column":53,"end_line":49,"start_byte":889,"start_column":5,"start_line":49}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def expand_playlist_ranges(items: CottList[MediaItem], ranges: CottList[PlaylistRange]) -> Result[CottList[MediaItem], MediaError]:
    """Expand one-based inclusive playlist ranges deterministically."""
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    ranges = _cott_validate_abi(ranges, CottList[PlaylistRange], path="$.ranges")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/expand_playlist_ranges.py", "f857a1e78e07120c4eb4b3b519542cd74276ed26c397d70069eb88e447a1cb0f", "expand_playlist_ranges", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.expand_playlist_ranges")
        _result = _implementation(items, ranges)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.expand_playlist_ranges"
        if _error.span is None:
            _error.span = {"end_byte":1407,"end_column":1,"end_line":69,"start_byte":990,"start_column":1,"start_line":55}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.expand_playlist_ranges", phase="implementation-call", span={"end_byte":1407,"end_column":1,"end_line":69,"start_byte":990,"start_column":1,"start_line":55}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.expand_playlist_ranges", phase="implementation-call", span={"end_byte":1407,"end_column":1,"end_line":69,"start_byte":990,"start_column":1,"start_line":55}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.expand_playlist_ranges", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidRange,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.expand_playlist_ranges", phase="error", span={"end_byte":1407,"end_column":1,"end_line":69,"start_byte":990,"start_column":1,"start_line":55}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.expand_playlist_ranges", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return ((((len(ranges) == 0) and (len(selected) == len(items))) or ((len(ranges) > 0) and (len(selected) <= (len(items) * len(ranges))))))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.expand_playlist_ranges", clause="ensures:1", phase="ensures", span={"end_byte":1354,"end_column":148,"end_line":63,"start_byte":1211,"start_column":5,"start_line":63}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[MediaItem], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def plan_downloads(items: CottList[MediaItem], archive: CottList[str], break_on_existing: bool) -> DownloadPlan:
    """Preserve item order while applying archive and break-on-existing policy."""
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    archive = _cott_validate_abi(archive, CottList[str], path="$.archive")
    break_on_existing = _cott_validate_abi(break_on_existing, bool, path="$.break_on_existing")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/plan_downloads.py", "8509508b32158850209316c9fef39e4a7adb19782eb323929a8732241085eca9", "plan_downloads", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.plan_downloads")
        _result = _implementation(items, archive, break_on_existing)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.plan_downloads"
        if _error.span is None:
            _error.span = {"end_byte":1640,"end_column":1,"end_line":80,"start_byte":1407,"start_column":1,"start_line":69}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_downloads", phase="implementation-call", span={"end_byte":1640,"end_column":1,"end_line":80,"start_byte":1407,"start_column":1,"start_line":69}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_downloads", phase="implementation-call", span={"end_byte":1640,"end_column":1,"end_line":80,"start_byte":1407,"start_column":1,"start_line":69}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, DownloadPlan, path="$.return")
    _result = _cott_wrap_async_protocol(_result, DownloadPlan, path="$.return", validator=_cott_validate_abi)
    return _result

def render_output_path(item: MediaItem, template: str, missing_placeholder: str) -> Result[str, MediaError]:
    """Substitute a bounded output template with a configurable missing value."""
    item = _cott_validate_abi(item, MediaItem, path="$.item")
    template = _cott_validate_abi(template, str, path="$.template")
    missing_placeholder = _cott_validate_abi(missing_placeholder, str, path="$.missing_placeholder")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/render_output_path.py", "6a6d80930d1149eae708071bad034a207dc70f8e8efa8757b8a6dc5e1665c04b", "render_output_path", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.render_output_path")
        _result = _implementation(item, template, missing_placeholder)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.render_output_path"
        if _error.span is None:
            _error.span = {"end_byte":2052,"end_column":1,"end_line":95,"start_byte":1640,"start_column":1,"start_line":80}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.render_output_path", phase="implementation-call", span={"end_byte":2052,"end_column":1,"end_line":95,"start_byte":1640,"start_column":1,"start_line":80}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.render_output_path", phase="implementation-call", span={"end_byte":2052,"end_column":1,"end_line":95,"start_byte":1640,"start_column":1,"start_line":80}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.render_output_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidTemplate,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.render_output_path", phase="error", span={"end_byte":2052,"end_column":1,"end_line":95,"start_byte":1640,"start_column":1,"start_line":80}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.render_output_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            path = _cott_match_value.value
            return ((len(path) <= (len(template) * ((((len((item).id) + len((item).title)) + len((item).ext)) + len(missing_placeholder)) + 20))))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.render_output_path", clause="ensures:1", phase="ensures", span={"end_byte":1996,"end_column":137,"end_line":89,"start_byte":1864,"start_column":5,"start_line":89}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def render_items(items: CottList[MediaItem], mode: JsonMode) -> str:
    """Render items as compact JSON Lines or one compact JSON array."""
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    mode = _cott_validate_abi(mode, JsonMode, path="$.mode")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/render_items.py", "cb0bac1f35f81afa6e6c2d345c008534984fa62cbd9b318cd98ad3e8b68da224", "render_items", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.render_items")
        _result = _implementation(items, mode)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.render_items"
        if _error.span is None:
            _error.span = {"end_byte":2219,"end_column":1,"end_line":102,"start_byte":2052,"start_column":1,"start_line":95}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.render_items", phase="implementation-call", span={"end_byte":2219,"end_column":1,"end_line":102,"start_byte":2052,"start_column":1,"start_line":95}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.render_items", phase="implementation-call", span={"end_byte":2219,"end_column":1,"end_line":102,"start_byte":2052,"start_column":1,"start_line":95}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def transfer_media(request: TransferRequest) -> Result[TransferReceipt, MediaError]:
    """Simulate or atomically transfer one bounded direct HTTP(S) resource."""
    request = _cott_validate_abi(request, TransferRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (((request).max_bytes == 0)):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":2746,"end_column":62,"end_line":112,"start_byte":2689,"start_column":5,"start_line":112}
        _expected_error_clause = "error:5"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/transfer_media.py", "763dfc5abce9025da462a6333051a10efbc064c50a0c439c288cb32ed01be865", "transfer_media", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.transfer_media")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.transfer_media"
        if _error.span is None:
            _error.span = {"end_byte":2952,"end_column":1,"end_line":120,"start_byte":2219,"start_column":1,"start_line":102}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.transfer_media", phase="implementation-call", span={"end_byte":2952,"end_column":1,"end_line":120,"start_byte":2219,"start_column":1,"start_line":102}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.transfer_media", phase="implementation-call", span={"end_byte":2952,"end_column":1,"end_line":120,"start_byte":2219,"start_column":1,"start_line":102}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransferReceipt, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.transfer_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_UnsupportedUrl, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_SizeLimit,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.transfer_media", phase="error", span={"end_byte":2952,"end_column":1,"end_line":120,"start_byte":2219,"start_column":1,"start_line":102}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.transfer_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (((receipt).url == (request).url))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:1", phase="ensures", span={"end_byte":2457,"end_column":61,"end_line":107,"start_byte":2401,"start_column":5,"start_line":107}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (((receipt).destination == (request).destination))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:2", phase="ensures", span={"end_byte":2534,"end_column":77,"end_line":108,"start_byte":2462,"start_column":5,"start_line":108}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (((receipt).bytes_written <= (request).max_bytes))
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:3", phase="ensures", span={"end_byte":2611,"end_column":77,"end_line":109,"start_byte":2539,"start_column":5,"start_line":109}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (((receipt).simulated == (request).simulate))
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:4", phase="ensures", span={"end_byte":2683,"end_column":72,"end_line":110,"start_byte":2616,"start_column":5,"start_line":110}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransferReceipt, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["DownloadPlan", "JsonMode", "JsonMode_Lines", "JsonMode_Single", "MediaError", "MediaError_HttpStatus", "MediaError_InvalidInput", "MediaError_InvalidRange", "MediaError_InvalidTemplate", "MediaError_NetworkFailure", "MediaError_OutputFailure", "MediaError_SizeLimit", "MediaError_UnsupportedUrl", "MediaItem", "PlaylistRange", "TransferReceipt", "TransferRequest", "expand_playlist_ranges", "parse_batch_urls", "plan_downloads", "render_items", "render_output_path", "transfer_media"]
