from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from real.yt_dlp_types import ArchiveRequest, Authentication, AuthenticationKind, AuthenticationKind_Anonymous, AuthenticationKind_BrowserCookies, AuthenticationKind_Cookies, AuthenticationKind_Credentials, AuthenticationKind_Netrc, CertificatePolicy, CertificatePolicy_Insecure, CertificatePolicy_Verify, CliInput, DownloadPlan, ExecutionReport, ExecutionRequest, ExternalToolRequest, ExtractorDescriptor, ExtractorWorkaround, ExtractorWorkaround_ForceGeneric, ExtractorWorkaround_LegacyServerConnect, ExtractorWorkaround_NoCheckCertificates, ExtractorWorkaround_NoPlaylist, FormatContainer, FormatContainer_Any, FormatContainer_Audio, FormatContainer_Best, FormatContainer_Video, FormatContainer_Worst, FormatDescriptor, FormatRequest, FragmentPolicy, GeoBypassMode, GeoBypassMode_Country, GeoBypassMode_Default, GeoBypassMode_Disabled, GeoBypassMode_IpBlock, InputKind, InputKind_Argument, InputKind_BatchFile, InputKind_ConfigFile, JsonMode, JsonMode_Lines, JsonMode_Single, LiveMode, LiveMode_Default, LiveMode_FromStart, LiveMode_Wait, LiveRequest, LogLevel, LogLevel_Debug, LogLevel_Info, LogLevel_Quiet, LogLevel_Warning, MediaError, MediaError_ArchiveFailure, MediaError_AuthenticationFailed, MediaError_BatchReadFailed, MediaError_CertificateFailure, MediaError_CookieFailure, MediaError_ExternalToolMissing, MediaError_ExtractorMissing, MediaError_FormatUnavailable, MediaError_GeoRestricted, MediaError_HttpStatus, MediaError_InvalidConfig, MediaError_InvalidInput, MediaError_InvalidRange, MediaError_InvalidShortcut, MediaError_InvalidTemplate, MediaError_LogFailure, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_PathFailure, MediaError_PluginRejected, MediaError_PostProcessFailed, MediaError_RetryExhausted, MediaError_SizeLimit, MediaError_SubtitleUnavailable, MediaError_UnsupportedUrl, MediaError_UpdateUnavailable, MediaError_WorkaroundRejected, MediaItem, MetadataRequest, NetworkPolicy, OutputRequest, PlaylistMode, PlaylistMode_Flat, PlaylistMode_Playlist, PlaylistMode_Random, PlaylistMode_Reverse, PlaylistMode_Single, PlaylistRange, PlaylistRequest, PluginDescriptor, PostProcessRequest, PostProcessorKind, PostProcessorKind_ConvertThumbnails, PostProcessorKind_EmbedMetadata, PostProcessorKind_EmbedSubtitle, PostProcessorKind_EmbedThumbnail, PostProcessorKind_ExtractAudio, PostProcessorKind_Fixup, PostProcessorKind_RecodeVideo, PostProcessorKind_RemuxVideo, PostProcessorKind_SplitChapters, PostProcessorKind_SponsorBlock, PresentationRequest, ProxyMode, ProxyMode_Direct, ProxyMode_Http, ProxyMode_Socks, ShortcutKind, ShortcutKind_Search, ShortcutKind_SearchAll, ShortcutKind_Url, ShortcutRequest, SimulationMode, SimulationMode_Download, SimulationMode_PrintOnly, SimulationMode_Simulate, SimulationMode_SkipDownload, SubtitleMode, SubtitleMode_All, SubtitleMode_Automatic, SubtitleMode_Manual, SubtitleMode_None, SubtitleRequest, ThumbnailRequest, TransferReceipt, TransferRequest, UpdatePolicy, UpdatePolicy_Apply, UpdatePolicy_Check, UpdatePolicy_Master, UpdatePolicy_Never, UpdatePolicy_Nightly, UpdateRequest, VideoFilterRequest, WorkaroundPolicy

def parse_arguments(arguments: CottList[str]) -> Result[CottList[CliInput], MediaError]:
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/parse_arguments.py", "ceab6738cf3a3bb4192de949a361c0c8f2448041a71047ad1801352f06682f57", "parse_arguments", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.parse_arguments")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.parse_arguments"
        if _error.span is None:
            _error.span = {"end_byte":6805,"end_column":1,"end_line":355,"start_byte":6612,"start_column":1,"start_line":348}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.parse_arguments", phase="implementation-call", span={"end_byte":6805,"end_column":1,"end_line":355,"start_byte":6612,"start_column":1,"start_line":348}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.parse_arguments", phase="implementation-call", span={"end_byte":6805,"end_column":1,"end_line":355,"start_byte":6612,"start_column":1,"start_line":348}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CliInput], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.parse_arguments", phase="error", span={"end_byte":6805,"end_column":1,"end_line":355,"start_byte":6612,"start_column":1,"start_line":348}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            inputs = _cott_match_value.value
            return ((len(inputs) <= len(arguments)))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.parse_arguments", clause="ensures:0", phase="ensures", span={"end_byte":6752,"end_column":61,"end_line":349,"start_byte":6696,"start_column":5,"start_line":349}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CliInput], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def build_shortcut_url(request: ShortcutRequest) -> Result[str, MediaError]:
    request = _cott_validate_abi(request, ShortcutRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/build_shortcut_url.py", "a9c3bba68b4c9e1ecfd85a4d4bc225441aaab04212cdb69d4b92ad100e9c0b33", "build_shortcut_url", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.build_shortcut_url")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.build_shortcut_url"
        if _error.span is None:
            _error.span = {"end_byte":6978,"end_column":1,"end_line":362,"start_byte":6805,"start_column":1,"start_line":355}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.build_shortcut_url", phase="implementation-call", span={"end_byte":6978,"end_column":1,"end_line":362,"start_byte":6805,"start_column":1,"start_line":355}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.build_shortcut_url", phase="implementation-call", span={"end_byte":6978,"end_column":1,"end_line":362,"start_byte":6805,"start_column":1,"start_line":355}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.build_shortcut_url", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidShortcut,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.build_shortcut_url", phase="error", span={"end_byte":6978,"end_column":1,"end_line":362,"start_byte":6805,"start_column":1,"start_line":355}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.build_shortcut_url", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            url = _cott_match_value.value
            return ((len(url) > 0))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.build_shortcut_url", clause="ensures:0", phase="ensures", span={"end_byte":6922,"end_column":42,"end_line":356,"start_byte":6885,"start_column":5,"start_line":356}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def validate_workarounds(policy: WorkaroundPolicy) -> Result[WorkaroundPolicy, MediaError]:
    policy = _cott_validate_abi(policy, WorkaroundPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/validate_workarounds.py", "392c5e616d6cf89cd56f9dce4f897dd4eeb1220ef82592e92ad93ce1bf6b8f95", "validate_workarounds", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.validate_workarounds")
        _result = _implementation(policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.validate_workarounds"
        if _error.span is None:
            _error.span = {"end_byte":7239,"end_column":1,"end_line":370,"start_byte":6978,"start_column":1,"start_line":362}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.validate_workarounds", phase="implementation-call", span={"end_byte":7239,"end_column":1,"end_line":370,"start_byte":6978,"start_column":1,"start_line":362}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.validate_workarounds", phase="implementation-call", span={"end_byte":7239,"end_column":1,"end_line":370,"start_byte":6978,"start_column":1,"start_line":362}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[WorkaroundPolicy, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.validate_workarounds", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_CertificateFailure, MediaError_WorkaroundRejected,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.validate_workarounds", phase="error", span={"end_byte":7239,"end_column":1,"end_line":370,"start_byte":6978,"start_column":1,"start_line":362}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.validate_workarounds", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            valid = _cott_match_value.value
            return (((valid).certificate == (policy).certificate))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.validate_workarounds", clause="ensures:0", phase="ensures", span={"end_byte":7140,"end_column":72,"end_line":363,"start_byte":7073,"start_column":5,"start_line":363}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[WorkaroundPolicy, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def configure_presentation(request: PresentationRequest) -> Result[Unit, MediaError]:
    request = _cott_validate_abi(request, PresentationRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/configure_presentation.py", "de8ef510087ede84dc5b4ac70875f831d09a22bde633569ccd43aa41fbd349ab", "configure_presentation", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.configure_presentation")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.configure_presentation"
        if _error.span is None:
            _error.span = {"end_byte":7438,"end_column":1,"end_line":377,"start_byte":7239,"start_column":1,"start_line":370}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.configure_presentation", phase="implementation-call", span={"end_byte":7438,"end_column":1,"end_line":377,"start_byte":7239,"start_column":1,"start_line":370}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.configure_presentation", phase="implementation-call", span={"end_byte":7438,"end_column":1,"end_line":377,"start_byte":7239,"start_column":1,"start_line":370}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.configure_presentation", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_LogFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.configure_presentation", phase="error", span={"end_byte":7438,"end_column":1,"end_line":377,"start_byte":7239,"start_column":1,"start_line":370}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.configure_presentation", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            configured = _cott_match_value.value
            return ((configured == UNIT))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.configure_presentation", clause="ensures:0", phase="ensures", span={"end_byte":7377,"end_column":54,"end_line":371,"start_byte":7328,"start_column":5,"start_line":371}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_config(path: Path) -> Result[CottList[CliInput], MediaError]:
    path = _cott_validate_abi(path, Path, path="$.path")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/load_config.py", "b6a961b0c12513f9a6fa3a6d0f2a99346eee486e49d852ea0413e43db5d8dba9", "load_config", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.load_config")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.load_config"
        if _error.span is None:
            _error.span = {"end_byte":7620,"end_column":1,"end_line":384,"start_byte":7438,"start_column":1,"start_line":377}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.load_config", phase="implementation-call", span={"end_byte":7620,"end_column":1,"end_line":384,"start_byte":7438,"start_column":1,"start_line":377}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.load_config", phase="implementation-call", span={"end_byte":7620,"end_column":1,"end_line":384,"start_byte":7438,"start_column":1,"start_line":377}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CliInput], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.load_config", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidConfig,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.load_config", phase="error", span={"end_byte":7620,"end_column":1,"end_line":384,"start_byte":7438,"start_column":1,"start_line":377}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.load_config", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            inputs = _cott_match_value.value
            return ((len(inputs) <= 100000))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.load_config", clause="ensures:0", phase="ensures", span={"end_byte":7557,"end_column":54,"end_line":378,"start_byte":7508,"start_column":5,"start_line":378}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CliInput], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def parse_batch_urls(batch: str, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]:
    batch = _cott_validate_abi(batch, str, path="$.batch")
    comment_prefixes = _cott_validate_abi(comment_prefixes, CottList[str], path="$.comment_prefixes")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/parse_batch_urls.py", "5914b2b7c99fde3605b5b846253bc08c431233bba2845578e1f7f67d2b5a5a70", "parse_batch_urls", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.parse_batch_urls")
        _result = _implementation(batch, comment_prefixes)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.parse_batch_urls"
        if _error.span is None:
            _error.span = {"end_byte":7820,"end_column":1,"end_line":391,"start_byte":7620,"start_column":1,"start_line":384}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.parse_batch_urls", phase="implementation-call", span={"end_byte":7820,"end_column":1,"end_line":391,"start_byte":7620,"start_column":1,"start_line":384}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.parse_batch_urls", phase="implementation-call", span={"end_byte":7820,"end_column":1,"end_line":391,"start_byte":7620,"start_column":1,"start_line":384}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.parse_batch_urls", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.parse_batch_urls", phase="error", span={"end_byte":7820,"end_column":1,"end_line":391,"start_byte":7620,"start_column":1,"start_line":384}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.parse_batch_urls", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            urls = _cott_match_value.value
            return ((len(urls) <= len(batch)))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.parse_batch_urls", clause="ensures:0", phase="ensures", span={"end_byte":7767,"end_column":53,"end_line":385,"start_byte":7719,"start_column":5,"start_line":385}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_batch_urls(path: Path, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]:
    path = _cott_validate_abi(path, Path, path="$.path")
    comment_prefixes = _cott_validate_abi(comment_prefixes, CottList[str], path="$.comment_prefixes")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/load_batch_urls.py", "54c68310d2d2c02f36aba857ce4fed4e3a322248736aae58f75dc2262519b154", "load_batch_urls", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.load_batch_urls")
        _result = _implementation(path, comment_prefixes)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.load_batch_urls"
        if _error.span is None:
            _error.span = {"end_byte":8062,"end_column":1,"end_line":399,"start_byte":7820,"start_column":1,"start_line":391}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.load_batch_urls", phase="implementation-call", span={"end_byte":8062,"end_column":1,"end_line":399,"start_byte":7820,"start_column":1,"start_line":391}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.load_batch_urls", phase="implementation-call", span={"end_byte":8062,"end_column":1,"end_line":399,"start_byte":7820,"start_column":1,"start_line":391}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.load_batch_urls", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_BatchReadFailed, MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.load_batch_urls", phase="error", span={"end_byte":8062,"end_column":1,"end_line":399,"start_byte":7820,"start_column":1,"start_line":391}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.load_batch_urls", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            urls = _cott_match_value.value
            return ((len(urls) <= 100000))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.load_batch_urls", clause="ensures:0", phase="ensures", span={"end_byte":7963,"end_column":50,"end_line":392,"start_byte":7918,"start_column":5,"start_line":392}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_inputs(inputs: CottList[CliInput], config: CottList[CliInput]) -> Result[CottList[str], MediaError]:
    inputs = _cott_validate_abi(inputs, CottList[CliInput], path="$.inputs")
    config = _cott_validate_abi(config, CottList[CliInput], path="$.config")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/resolve_inputs.py", "62fef463229e2e3e911f37fe78357d518f8c67dd79c6328bc6279220183c007f", "resolve_inputs", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.resolve_inputs")
        _result = _implementation(inputs, config)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.resolve_inputs"
        if _error.span is None:
            _error.span = {"end_byte":8281,"end_column":1,"end_line":406,"start_byte":8062,"start_column":1,"start_line":399}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.resolve_inputs", phase="implementation-call", span={"end_byte":8281,"end_column":1,"end_line":406,"start_byte":8062,"start_column":1,"start_line":399}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.resolve_inputs", phase="implementation-call", span={"end_byte":8281,"end_column":1,"end_line":406,"start_byte":8062,"start_column":1,"start_line":399}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.resolve_inputs", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.resolve_inputs", phase="error", span={"end_byte":8281,"end_column":1,"end_line":406,"start_byte":8062,"start_column":1,"start_line":399}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.resolve_inputs", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            urls = _cott_match_value.value
            return ((len(urls) <= (len(inputs) + len(config))))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_inputs", clause="ensures:0", phase="ensures", span={"end_byte":8228,"end_column":67,"end_line":400,"start_byte":8166,"start_column":5,"start_line":400}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def validate_network(policy: NetworkPolicy) -> Result[NetworkPolicy, MediaError]:
    policy = _cott_validate_abi(policy, NetworkPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/validate_network.py", "507cee9102bf835d8ab0b5631416297871e7043100ff0ef3425aea49d0325ca3", "validate_network", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.validate_network")
        _result = _implementation(policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.validate_network"
        if _error.span is None:
            _error.span = {"end_byte":8474,"end_column":1,"end_line":413,"start_byte":8281,"start_column":1,"start_line":406}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.validate_network", phase="implementation-call", span={"end_byte":8474,"end_column":1,"end_line":413,"start_byte":8281,"start_column":1,"start_line":406}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.validate_network", phase="implementation-call", span={"end_byte":8474,"end_column":1,"end_line":413,"start_byte":8281,"start_column":1,"start_line":406}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[NetworkPolicy, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.validate_network", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.validate_network", phase="error", span={"end_byte":8474,"end_column":1,"end_line":413,"start_byte":8281,"start_column":1,"start_line":406}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.validate_network", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            valid = _cott_match_value.value
            return (((valid).socket_timeout_ms > 0))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.validate_network", clause="ensures:0", phase="ensures", span={"end_byte":8421,"end_column":60,"end_line":407,"start_byte":8366,"start_column":5,"start_line":407}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[NetworkPolicy, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_authentication(request: Authentication) -> Result[Authentication, MediaError]:
    request = _cott_validate_abi(request, Authentication, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/resolve_authentication.py", "eba86aba4378f8dd056c4dae6a43b24fede45a7e4f1e2a140f8e198ddaf1d623", "resolve_authentication", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.resolve_authentication")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.resolve_authentication"
        if _error.span is None:
            _error.span = {"end_byte":8743,"end_column":1,"end_line":421,"start_byte":8474,"start_column":1,"start_line":413}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.resolve_authentication", phase="implementation-call", span={"end_byte":8743,"end_column":1,"end_line":421,"start_byte":8474,"start_column":1,"start_line":413}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.resolve_authentication", phase="implementation-call", span={"end_byte":8743,"end_column":1,"end_line":421,"start_byte":8474,"start_column":1,"start_line":413}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Authentication, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.resolve_authentication", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_AuthenticationFailed, MediaError_CookieFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.resolve_authentication", phase="error", span={"end_byte":8743,"end_column":1,"end_line":421,"start_byte":8474,"start_column":1,"start_line":413}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.resolve_authentication", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            authenticated = _cott_match_value.value
            return (((authenticated).kind == (request).kind))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_authentication", clause="ensures:0", phase="ensures", span={"end_byte":8638,"end_column":75,"end_line":414,"start_byte":8568,"start_column":5,"start_line":414}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Authentication, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def select_geo_route(policy: NetworkPolicy) -> Result[NetworkPolicy, MediaError]:
    policy = _cott_validate_abi(policy, NetworkPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/select_geo_route.py", "713a9d31b333f9ac95f6d965dcb60bc140326e4fd97b9fc30b36e90677498658", "select_geo_route", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.select_geo_route")
        _result = _implementation(policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.select_geo_route"
        if _error.span is None:
            _error.span = {"end_byte":8954,"end_column":1,"end_line":428,"start_byte":8743,"start_column":1,"start_line":421}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.select_geo_route", phase="implementation-call", span={"end_byte":8954,"end_column":1,"end_line":428,"start_byte":8743,"start_column":1,"start_line":421}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.select_geo_route", phase="implementation-call", span={"end_byte":8954,"end_column":1,"end_line":428,"start_byte":8743,"start_column":1,"start_line":421}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[NetworkPolicy, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.select_geo_route", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_GeoRestricted,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.select_geo_route", phase="error", span={"end_byte":8954,"end_column":1,"end_line":428,"start_byte":8743,"start_column":1,"start_line":421}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.select_geo_route", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            route = _cott_match_value.value
            return (((route).proxy_mode == (policy).proxy_mode))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.select_geo_route", clause="ensures:0", phase="ensures", span={"end_byte":8893,"end_column":70,"end_line":422,"start_byte":8828,"start_column":5,"start_line":422}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[NetworkPolicy, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def discover_extractors() -> CottList[ExtractorDescriptor]:
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/discover_extractors.py", "b8bc0ac5820be7ce557263625457739031696f2c72eebf7e0970094d7547ff2e", "discover_extractors", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.discover_extractors")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.discover_extractors"
        if _error.span is None:
            _error.span = {"end_byte":9025,"end_column":1,"end_line":431,"start_byte":8954,"start_column":1,"start_line":428}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.discover_extractors", phase="implementation-call", span={"end_byte":9025,"end_column":1,"end_line":431,"start_byte":8954,"start_column":1,"start_line":428}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.discover_extractors", phase="implementation-call", span={"end_byte":9025,"end_column":1,"end_line":431,"start_byte":8954,"start_column":1,"start_line":428}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[ExtractorDescriptor], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[ExtractorDescriptor], path="$.return", validator=_cott_validate_abi)
    return _result

def load_plugins(paths: CottList[Path]) -> Result[CottList[PluginDescriptor], MediaError]:
    paths = _cott_validate_abi(paths, CottList[Path], path="$.paths")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/load_plugins.py", "d84a959bdb89b7f2029191320d1afb8dec98569f57ca338ee39e91f026cd5397", "load_plugins", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.load_plugins")
        _result = _implementation(paths)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.load_plugins"
        if _error.span is None:
            _error.span = {"end_byte":9226,"end_column":1,"end_line":438,"start_byte":9025,"start_column":1,"start_line":431}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.load_plugins", phase="implementation-call", span={"end_byte":9226,"end_column":1,"end_line":438,"start_byte":9025,"start_column":1,"start_line":431}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.load_plugins", phase="implementation-call", span={"end_byte":9226,"end_column":1,"end_line":438,"start_byte":9025,"start_column":1,"start_line":431}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[PluginDescriptor], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.load_plugins", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_PluginRejected,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.load_plugins", phase="error", span={"end_byte":9226,"end_column":1,"end_line":438,"start_byte":9025,"start_column":1,"start_line":431}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.load_plugins", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plugins = _cott_match_value.value
            return ((len(plugins) <= 100000))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.load_plugins", clause="ensures:0", phase="ensures", span={"end_byte":9162,"end_column":56,"end_line":432,"start_byte":9111,"start_column":5,"start_line":432}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[PluginDescriptor], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def choose_extractor(url: str, extractors: CottList[ExtractorDescriptor]) -> Result[ExtractorDescriptor, MediaError]:
    url = _cott_validate_abi(url, str, path="$.url")
    extractors = _cott_validate_abi(extractors, CottList[ExtractorDescriptor], path="$.extractors")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/choose_extractor.py", "5eef0bfedd5ae064299463beb3fa6c26477bad23690151bee482c94a4da4e6d6", "choose_extractor", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.choose_extractor")
        _result = _implementation(url, extractors)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.choose_extractor"
        if _error.span is None:
            _error.span = {"end_byte":9496,"end_column":1,"end_line":449,"start_byte":9226,"start_column":1,"start_line":438}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.choose_extractor", phase="implementation-call", span={"end_byte":9496,"end_column":1,"end_line":449,"start_byte":9226,"start_column":1,"start_line":438}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.choose_extractor", phase="implementation-call", span={"end_byte":9496,"end_column":1,"end_line":449,"start_byte":9226,"start_column":1,"start_line":438}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ExtractorDescriptor, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.choose_extractor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_UnsupportedUrl, MediaError_ExtractorMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.choose_extractor", phase="error", span={"end_byte":9496,"end_column":1,"end_line":449,"start_byte":9226,"start_column":1,"start_line":438}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.choose_extractor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            extractor = _cott_match_value.value
            return ((extractor).enabled)
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.choose_extractor", clause="ensures:0", phase="ensures", span={"end_byte":9403,"end_column":54,"end_line":442,"start_byte":9354,"start_column":5,"start_line":442}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ExtractorDescriptor, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def extract_media(url: str, extractor: ExtractorDescriptor, authentication: Authentication, network: NetworkPolicy) -> Result[CottList[MediaItem], MediaError]:
    """Handle every auth kind; HEAD via Request and urlopen; derive one item from final URL."""
    url = _cott_validate_abi(url, str, path="$.url")
    extractor = _cott_validate_abi(extractor, ExtractorDescriptor, path="$.extractor")
    authentication = _cott_validate_abi(authentication, Authentication, path="$.authentication")
    network = _cott_validate_abi(network, NetworkPolicy, path="$.network")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/extract_media.py", "a1fa5947a5af6ac000a1386c4bdc2d185274440fb339f759dee048eadb781b7a", "extract_media", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.extract_media")
        _result = _implementation(url, extractor, authentication, network)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.extract_media"
        if _error.span is None:
            _error.span = {"end_byte":10039,"end_column":1,"end_line":469,"start_byte":9496,"start_column":1,"start_line":449}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.extract_media", phase="implementation-call", span={"end_byte":10039,"end_column":1,"end_line":469,"start_byte":9496,"start_column":1,"start_line":449}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.extract_media", phase="implementation-call", span={"end_byte":10039,"end_column":1,"end_line":469,"start_byte":9496,"start_column":1,"start_line":449}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.extract_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_AuthenticationFailed, MediaError_GeoRestricted, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_UnsupportedUrl,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.extract_media", phase="error", span={"end_byte":10039,"end_column":1,"end_line":469,"start_byte":9496,"start_column":1,"start_line":449}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.extract_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            items = _cott_match_value.value
            return ((len(items) <= 100000))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.extract_media", clause="ensures:1", phase="ensures", span={"end_byte":9832,"end_column":52,"end_line":459,"start_byte":9785,"start_column":5,"start_line":459}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[MediaItem], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def expand_playlist_ranges(items: CottList[MediaItem], ranges: CottList[PlaylistRange]) -> Result[CottList[MediaItem], MediaError]:
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    ranges = _cott_validate_abi(ranges, CottList[PlaylistRange], path="$.ranges")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/expand_playlist_ranges.py", "e9959af6ab83f09ce4fb7ed9cb0b49dcadf64470a0abf47e6e293e0e75160c14", "expand_playlist_ranges", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.expand_playlist_ranges")
        _result = _implementation(items, ranges)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.expand_playlist_ranges"
        if _error.span is None:
            _error.span = {"end_byte":10369,"end_column":1,"end_line":479,"start_byte":10039,"start_column":1,"start_line":469}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.expand_playlist_ranges", phase="implementation-call", span={"end_byte":10369,"end_column":1,"end_line":479,"start_byte":10039,"start_column":1,"start_line":469}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.expand_playlist_ranges", phase="implementation-call", span={"end_byte":10369,"end_column":1,"end_line":479,"start_byte":10039,"start_column":1,"start_line":469}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.expand_playlist_ranges", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidRange,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.expand_playlist_ranges", phase="error", span={"end_byte":10369,"end_column":1,"end_line":479,"start_byte":10039,"start_column":1,"start_line":469}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.expand_playlist_ranges", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return ((((len(ranges) == 0) and (len(selected) == len(items))) or ((len(ranges) > 0) and (len(selected) <= (len(items) * len(ranges))))))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.expand_playlist_ranges", clause="ensures:0", phase="ensures", span={"end_byte":10316,"end_column":148,"end_line":473,"start_byte":10173,"start_column":5,"start_line":473}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[MediaItem], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def select_playlist(items: CottList[MediaItem], request: PlaylistRequest) -> Result[CottList[MediaItem], MediaError]:
    """Handle each playlist mode once; apply ranges, bounds, then requested ordering."""
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    request = _cott_validate_abi(request, PlaylistRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/select_playlist.py", "51598ae9a7fbbfc8435f33a76ac45b34ddfea938465bede8245f27323ef7bcc1", "select_playlist", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.select_playlist")
        _result = _implementation(items, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.select_playlist"
        if _error.span is None:
            _error.span = {"end_byte":10746,"end_column":1,"end_line":494,"start_byte":10369,"start_column":1,"start_line":479}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.select_playlist", phase="implementation-call", span={"end_byte":10746,"end_column":1,"end_line":494,"start_byte":10369,"start_column":1,"start_line":479}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.select_playlist", phase="implementation-call", span={"end_byte":10746,"end_column":1,"end_line":494,"start_byte":10369,"start_column":1,"start_line":479}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.select_playlist", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidRange, MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.select_playlist", phase="error", span={"end_byte":10746,"end_column":1,"end_line":494,"start_byte":10369,"start_column":1,"start_line":479}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.select_playlist", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return ((len(selected) <= len(items)))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.select_playlist", clause="ensures:1", phase="ensures", span={"end_byte":10653,"end_column":61,"end_line":487,"start_byte":10597,"start_column":5,"start_line":487}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[MediaItem], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_live_media(items: CottList[MediaItem], request: LiveRequest) -> Result[CottList[MediaItem], MediaError]:
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    request = _cott_validate_abi(request, LiveRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/resolve_live_media.py", "0dff24640ae273f1b28b0b861b6ee88e611a55d0d27d017e9db540eec8a35af1", "resolve_live_media", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.resolve_live_media")
        _result = _implementation(items, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.resolve_live_media"
        if _error.span is None:
            _error.span = {"end_byte":11028,"end_column":1,"end_line":505,"start_byte":10746,"start_column":1,"start_line":494}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.resolve_live_media", phase="implementation-call", span={"end_byte":11028,"end_column":1,"end_line":505,"start_byte":10746,"start_column":1,"start_line":494}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.resolve_live_media", phase="implementation-call", span={"end_byte":11028,"end_column":1,"end_line":505,"start_byte":10746,"start_column":1,"start_line":494}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.resolve_live_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput, MediaError_RetryExhausted,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.resolve_live_media", phase="error", span={"end_byte":11028,"end_column":1,"end_line":505,"start_byte":10746,"start_column":1,"start_line":494}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.resolve_live_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return ((len(selected) <= len(items)))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_live_media", clause="ensures:0", phase="ensures", span={"end_byte":10925,"end_column":61,"end_line":498,"start_byte":10869,"start_column":5,"start_line":498}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[MediaItem], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def filter_video(items: CottList[MediaItem], request: VideoFilterRequest) -> Result[CottList[MediaItem], MediaError]:
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    request = _cott_validate_abi(request, VideoFilterRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/filter_video.py", "9c1dabf59496e599b97cf106c597b33bcdf86fe5b35bea18c7c1fca32e8aaf85", "filter_video", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.filter_video")
        _result = _implementation(items, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.filter_video"
        if _error.span is None:
            _error.span = {"end_byte":11261,"end_column":1,"end_line":515,"start_byte":11028,"start_column":1,"start_line":505}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.filter_video", phase="implementation-call", span={"end_byte":11261,"end_column":1,"end_line":515,"start_byte":11028,"start_column":1,"start_line":505}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.filter_video", phase="implementation-call", span={"end_byte":11261,"end_column":1,"end_line":515,"start_byte":11028,"start_column":1,"start_line":505}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.filter_video", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.filter_video", phase="error", span={"end_byte":11261,"end_column":1,"end_line":515,"start_byte":11028,"start_column":1,"start_line":505}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.filter_video", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return ((len(selected) <= len(items)))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.filter_video", clause="ensures:0", phase="ensures", span={"end_byte":11208,"end_column":61,"end_line":509,"start_byte":11152,"start_column":5,"start_line":509}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[MediaItem], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def filter_formats(formats: CottList[FormatDescriptor], request: FormatRequest) -> Result[CottList[FormatDescriptor], MediaError]:
    formats = _cott_validate_abi(formats, CottList[FormatDescriptor], path="$.formats")
    request = _cott_validate_abi(request, FormatRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/filter_formats.py", "5c79f19042ffbbc809814d886bb372be8aa4c89b3cb4b6ef19a7302a3d3c53f8", "filter_formats", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.filter_formats")
        _result = _implementation(formats, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.filter_formats"
        if _error.span is None:
            _error.span = {"end_byte":11548,"end_column":1,"end_line":526,"start_byte":11261,"start_column":1,"start_line":515}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.filter_formats", phase="implementation-call", span={"end_byte":11548,"end_column":1,"end_line":526,"start_byte":11261,"start_column":1,"start_line":515}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.filter_formats", phase="implementation-call", span={"end_byte":11548,"end_column":1,"end_line":526,"start_byte":11261,"start_column":1,"start_line":515}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[FormatDescriptor], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.filter_formats", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_FormatUnavailable, MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.filter_formats", phase="error", span={"end_byte":11548,"end_column":1,"end_line":526,"start_byte":11261,"start_column":1,"start_line":515}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.filter_formats", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return ((len(selected) <= len(formats)))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.filter_formats", clause="ensures:0", phase="ensures", span={"end_byte":11456,"end_column":63,"end_line":519,"start_byte":11398,"start_column":5,"start_line":519}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[FormatDescriptor], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def sort_formats(formats: CottList[FormatDescriptor], fields: CottList[str]) -> CottList[FormatDescriptor]:
    formats = _cott_validate_abi(formats, CottList[FormatDescriptor], path="$.formats")
    fields = _cott_validate_abi(fields, CottList[str], path="$.fields")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/sort_formats.py", "3fc60dd29fb33d41277342907d8cc2cfa375a865b864bb987e7b8ce016c34f34", "sort_formats", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.sort_formats")
        _result = _implementation(formats, fields)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.sort_formats"
        if _error.span is None:
            _error.span = {"end_byte":11698,"end_column":1,"end_line":531,"start_byte":11548,"start_column":1,"start_line":526}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.sort_formats", phase="implementation-call", span={"end_byte":11698,"end_column":1,"end_line":531,"start_byte":11548,"start_column":1,"start_line":526}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.sort_formats", phase="implementation-call", span={"end_byte":11698,"end_column":1,"end_line":531,"start_byte":11548,"start_column":1,"start_line":526}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[FormatDescriptor], path="$.return")
    if not ((len(_result) == len(formats))):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.sort_formats", clause="ensures:0", phase="ensures", span={"end_byte":11680,"end_column":38,"end_line":527,"start_byte":11647,"start_column":5,"start_line":527}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[FormatDescriptor], path="$.return", validator=_cott_validate_abi)
    return _result

def select_subtitles(item: MediaItem, request: SubtitleRequest) -> Result[CottList[str], MediaError]:
    """None returns typed List[Str]; otherwise preserve requested language order."""
    item = _cott_validate_abi(item, MediaItem, path="$.item")
    request = _cott_validate_abi(request, SubtitleRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/select_subtitles.py", "c59716263e9f39b981faa8afc822f3c6a38a06d0aea88dabd25c0ef204419c35", "select_subtitles", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.select_subtitles")
        _result = _implementation(item, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.select_subtitles"
        if _error.span is None:
            _error.span = {"end_byte":12021,"end_column":1,"end_line":542,"start_byte":11698,"start_column":1,"start_line":531}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.select_subtitles", phase="implementation-call", span={"end_byte":12021,"end_column":1,"end_line":542,"start_byte":11698,"start_column":1,"start_line":531}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.select_subtitles", phase="implementation-call", span={"end_byte":12021,"end_column":1,"end_line":542,"start_byte":11698,"start_column":1,"start_line":531}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.select_subtitles", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_SubtitleUnavailable,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.select_subtitles", phase="error", span={"end_byte":12021,"end_column":1,"end_line":542,"start_byte":11698,"start_column":1,"start_line":531}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.select_subtitles", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            subtitles = _cott_match_value.value
            return ((len(subtitles) <= 100000))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.select_subtitles", clause="ensures:1", phase="ensures", span={"end_byte":11954,"end_column":60,"end_line":536,"start_byte":11899,"start_column":5,"start_line":536}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def plan_thumbnails(item: MediaItem, request: ThumbnailRequest) -> CottList[str]:
    item = _cott_validate_abi(item, MediaItem, path="$.item")
    request = _cott_validate_abi(request, ThumbnailRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/plan_thumbnails.py", "45d4f9798d4f070290bd717297009d84c5d2ca5afafce6671d886f00493d9bc1", "plan_thumbnails", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.plan_thumbnails")
        _result = _implementation(item, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.plan_thumbnails"
        if _error.span is None:
            _error.span = {"end_byte":12114,"end_column":1,"end_line":545,"start_byte":12021,"start_column":1,"start_line":542}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_thumbnails", phase="implementation-call", span={"end_byte":12114,"end_column":1,"end_line":545,"start_byte":12021,"start_column":1,"start_line":542}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_thumbnails", phase="implementation-call", span={"end_byte":12114,"end_column":1,"end_line":545,"start_byte":12021,"start_column":1,"start_line":542}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=_cott_validate_abi)
    return _result

def plan_metadata(item: MediaItem, request: MetadataRequest) -> CottList[str]:
    item = _cott_validate_abi(item, MediaItem, path="$.item")
    request = _cott_validate_abi(request, MetadataRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/plan_metadata.py", "9ad530ae2a600b95692377e0a4f22564ababd1460528456a2a53583d8074b647", "plan_metadata", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.plan_metadata")
        _result = _implementation(item, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.plan_metadata"
        if _error.span is None:
            _error.span = {"end_byte":12204,"end_column":1,"end_line":548,"start_byte":12114,"start_column":1,"start_line":545}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_metadata", phase="implementation-call", span={"end_byte":12204,"end_column":1,"end_line":548,"start_byte":12114,"start_column":1,"start_line":545}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_metadata", phase="implementation-call", span={"end_byte":12204,"end_column":1,"end_line":548,"start_byte":12114,"start_column":1,"start_line":545}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=_cott_validate_abi)
    return _result

def render_output_path(item: MediaItem, template: str, missing_placeholder: str) -> Result[str, MediaError]:
    item = _cott_validate_abi(item, MediaItem, path="$.item")
    template = _cott_validate_abi(template, str, path="$.template")
    missing_placeholder = _cott_validate_abi(missing_placeholder, str, path="$.missing_placeholder")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/render_output_path.py", "92ac239d994b0bbf823c71940cdafa4fa4423dc020c8827c217ddab1e0720519", "render_output_path", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.render_output_path")
        _result = _implementation(item, template, missing_placeholder)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.render_output_path"
        if _error.span is None:
            _error.span = {"end_byte":12519,"end_column":1,"end_line":559,"start_byte":12204,"start_column":1,"start_line":548}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.render_output_path", phase="implementation-call", span={"end_byte":12519,"end_column":1,"end_line":559,"start_byte":12204,"start_column":1,"start_line":548}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.render_output_path", phase="implementation-call", span={"end_byte":12519,"end_column":1,"end_line":559,"start_byte":12204,"start_column":1,"start_line":548}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.render_output_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidTemplate,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.render_output_path", phase="error", span={"end_byte":12519,"end_column":1,"end_line":559,"start_byte":12204,"start_column":1,"start_line":548}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.render_output_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            path = _cott_match_value.value
            return ((len(path) <= (len(template) * ((((len((item).id) + len((item).title)) + len((item).ext)) + len(missing_placeholder)) + 20))))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.render_output_path", clause="ensures:0", phase="ensures", span={"end_byte":12463,"end_column":137,"end_line":553,"start_byte":12331,"start_column":5,"start_line":553}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_output_path(item: MediaItem, request: OutputRequest) -> Result[Path, MediaError]:
    item = _cott_validate_abi(item, MediaItem, path="$.item")
    request = _cott_validate_abi(request, OutputRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/resolve_output_path.py", "1134981c58c8abb7f74124e2dbaaba34cecc32762b2ae4a4a53d1453dd145686", "resolve_output_path", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.resolve_output_path")
        _result = _implementation(item, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.resolve_output_path"
        if _error.span is None:
            _error.span = {"end_byte":12752,"end_column":1,"end_line":567,"start_byte":12519,"start_column":1,"start_line":559}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.resolve_output_path", phase="implementation-call", span={"end_byte":12752,"end_column":1,"end_line":567,"start_byte":12519,"start_column":1,"start_line":559}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.resolve_output_path", phase="implementation-call", span={"end_byte":12752,"end_column":1,"end_line":567,"start_byte":12519,"start_column":1,"start_line":559}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Path, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.resolve_output_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidTemplate, MediaError_PathFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.resolve_output_path", phase="error", span={"end_byte":12752,"end_column":1,"end_line":567,"start_byte":12519,"start_column":1,"start_line":559}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.resolve_output_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            path = _cott_match_value.value
            return ((path != (request).temp))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_output_path", clause="ensures:0", phase="ensures", span={"end_byte":12663,"end_column":52,"end_line":560,"start_byte":12616,"start_column":5,"start_line":560}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Path, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def read_download_archive(request: ArchiveRequest) -> Result[CottList[str], MediaError]:
    request = _cott_validate_abi(request, ArchiveRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/read_download_archive.py", "4ba19cbf6c101d9a2bd8e6485c6dcb3b474301f39e1c404a80a798fe9f49fdd2", "read_download_archive", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.read_download_archive")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.read_download_archive"
        if _error.span is None:
            _error.span = {"end_byte":12955,"end_column":1,"end_line":574,"start_byte":12752,"start_column":1,"start_line":567}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.read_download_archive", phase="implementation-call", span={"end_byte":12955,"end_column":1,"end_line":574,"start_byte":12752,"start_column":1,"start_line":567}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.read_download_archive", phase="implementation-call", span={"end_byte":12955,"end_column":1,"end_line":574,"start_byte":12752,"start_column":1,"start_line":567}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.read_download_archive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_ArchiveFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.read_download_archive", phase="error", span={"end_byte":12955,"end_column":1,"end_line":574,"start_byte":12752,"start_column":1,"start_line":567}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.read_download_archive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            entries = _cott_match_value.value
            return ((len(entries) <= 100000))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.read_download_archive", clause="ensures:0", phase="ensures", span={"end_byte":12891,"end_column":56,"end_line":568,"start_byte":12840,"start_column":5,"start_line":568}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def plan_downloads(items: CottList[MediaItem], archive: CottList[str], break_on_existing: bool) -> DownloadPlan:
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    archive = _cott_validate_abi(archive, CottList[str], path="$.archive")
    break_on_existing = _cott_validate_abi(break_on_existing, bool, path="$.break_on_existing")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/plan_downloads.py", "4aff2239730484bc1e46be15c11b810e34ee4b56a34ab7693c56259577d47cf9", "plan_downloads", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.plan_downloads")
        _result = _implementation(items, archive, break_on_existing)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.plan_downloads"
        if _error.span is None:
            _error.span = {"end_byte":13090,"end_column":1,"end_line":581,"start_byte":12955,"start_column":1,"start_line":574}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_downloads", phase="implementation-call", span={"end_byte":13090,"end_column":1,"end_line":581,"start_byte":12955,"start_column":1,"start_line":574}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_downloads", phase="implementation-call", span={"end_byte":13090,"end_column":1,"end_line":581,"start_byte":12955,"start_column":1,"start_line":574}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, DownloadPlan, path="$.return")
    _result = _cott_wrap_async_protocol(_result, DownloadPlan, path="$.return", validator=_cott_validate_abi)
    return _result

def write_download_archive(path: Path, items: CottList[MediaItem]) -> Result[Unit, MediaError]:
    path = _cott_validate_abi(path, Path, path="$.path")
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/write_download_archive.py", "e4c86df6432d627fef58c587d282183151cf98eacc5a06a03b3e436d46624ad5", "write_download_archive", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.write_download_archive")
        _result = _implementation(path, items)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.write_download_archive"
        if _error.span is None:
            _error.span = {"end_byte":13289,"end_column":1,"end_line":588,"start_byte":13090,"start_column":1,"start_line":581}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.write_download_archive", phase="implementation-call", span={"end_byte":13289,"end_column":1,"end_line":588,"start_byte":13090,"start_column":1,"start_line":581}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.write_download_archive", phase="implementation-call", span={"end_byte":13289,"end_column":1,"end_line":588,"start_byte":13090,"start_column":1,"start_line":581}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.write_download_archive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_ArchiveFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.write_download_archive", phase="error", span={"end_byte":13289,"end_column":1,"end_line":588,"start_byte":13090,"start_column":1,"start_line":581}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.write_download_archive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            saved = _cott_match_value.value
            return ((saved == UNIT))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.write_download_archive", clause="ensures:0", phase="ensures", span={"end_byte":13224,"end_column":44,"end_line":582,"start_byte":13185,"start_column":5,"start_line":582}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def plan_fragments(request: TransferRequest, policy: FragmentPolicy) -> Result[CottList[TransferRequest], MediaError]:
    request = _cott_validate_abi(request, TransferRequest, path="$.request")
    policy = _cott_validate_abi(policy, FragmentPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/plan_fragments.py", "6b42676f05bb13262259e3ae225526ded4f9c482e6dac6a50a76f823ce18e347", "plan_fragments", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.plan_fragments")
        _result = _implementation(request, policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.plan_fragments"
        if _error.span is None:
            _error.span = {"end_byte":13557,"end_column":1,"end_line":599,"start_byte":13289,"start_column":1,"start_line":588}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_fragments", phase="implementation-call", span={"end_byte":13557,"end_column":1,"end_line":599,"start_byte":13289,"start_column":1,"start_line":588}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_fragments", phase="implementation-call", span={"end_byte":13557,"end_column":1,"end_line":599,"start_byte":13289,"start_column":1,"start_line":588}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[TransferRequest], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.plan_fragments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput, MediaError_SizeLimit,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.plan_fragments", phase="error", span={"end_byte":13557,"end_column":1,"end_line":599,"start_byte":13289,"start_column":1,"start_line":588}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.plan_fragments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            fragments = _cott_match_value.value
            return ((len(fragments) <= 100000))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.plan_fragments", clause="ensures:0", phase="ensures", span={"end_byte":13473,"end_column":60,"end_line":592,"start_byte":13418,"start_column":5,"start_line":592}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[TransferRequest], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def transfer_media(request: TransferRequest) -> Result[TransferReceipt, MediaError]:
    request = _cott_validate_abi(request, TransferRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (((request).max_bytes == 0)):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":13990,"end_column":62,"end_line":605,"start_byte":13933,"start_column":5,"start_line":605}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/transfer_media.py", "9eb2fc6d8608073da7e4c1f6eeaba4dd30fae1dfff89be3d5470c4b93b8e2c20", "transfer_media", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.transfer_media")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.transfer_media"
        if _error.span is None:
            _error.span = {"end_byte":14197,"end_column":1,"end_line":614,"start_byte":13557,"start_column":1,"start_line":599}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.transfer_media", phase="implementation-call", span={"end_byte":14197,"end_column":1,"end_line":614,"start_byte":13557,"start_column":1,"start_line":599}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.transfer_media", phase="implementation-call", span={"end_byte":14197,"end_column":1,"end_line":614,"start_byte":13557,"start_column":1,"start_line":599}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransferReceipt, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.transfer_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_UnsupportedUrl, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_SizeLimit,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.transfer_media", phase="error", span={"end_byte":14197,"end_column":1,"end_line":614,"start_byte":13557,"start_column":1,"start_line":599}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.transfer_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (((receipt).url == (request).url))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:0", phase="ensures", span={"end_byte":13701,"end_column":61,"end_line":600,"start_byte":13645,"start_column":5,"start_line":600}, expected="true", actual="false")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (((receipt).destination == (request).destination))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:1", phase="ensures", span={"end_byte":13778,"end_column":77,"end_line":601,"start_byte":13706,"start_column":5,"start_line":601}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (((receipt).bytes_written <= (request).max_bytes))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:2", phase="ensures", span={"end_byte":13855,"end_column":77,"end_line":602,"start_byte":13783,"start_column":5,"start_line":602}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (((receipt).simulated == (request).simulate))
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:3", phase="ensures", span={"end_byte":13927,"end_column":72,"end_line":603,"start_byte":13860,"start_column":5,"start_line":603}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransferReceipt, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def transfer_fragments(fragments: CottList[TransferRequest], policy: FragmentPolicy) -> Result[CottList[TransferReceipt], MediaError]:
    fragments = _cott_validate_abi(fragments, CottList[TransferRequest], path="$.fragments")
    policy = _cott_validate_abi(policy, FragmentPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/transfer_fragments.py", "e30e4120ff83ddd93501aedc36210f09a9f16ea70d35682f4fbf0ec172fad343", "transfer_fragments", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.transfer_fragments")
        _result = _implementation(fragments, policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.transfer_fragments"
        if _error.span is None:
            _error.span = {"end_byte":14647,"end_column":1,"end_line":629,"start_byte":14197,"start_column":1,"start_line":614}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.transfer_fragments", phase="implementation-call", span={"end_byte":14647,"end_column":1,"end_line":629,"start_byte":14197,"start_column":1,"start_line":614}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.transfer_fragments", phase="implementation-call", span={"end_byte":14647,"end_column":1,"end_line":629,"start_byte":14197,"start_column":1,"start_line":614}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[TransferReceipt], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.transfer_fragments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_RetryExhausted, MediaError_SizeLimit,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.transfer_fragments", phase="error", span={"end_byte":14647,"end_column":1,"end_line":629,"start_byte":14197,"start_column":1,"start_line":614}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.transfer_fragments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipts = _cott_match_value.value
            return ((len(receipts) == len(fragments)))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_fragments", clause="ensures:0", phase="ensures", span={"end_byte":14398,"end_column":65,"end_line":618,"start_byte":14338,"start_column":5,"start_line":618}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[TransferReceipt], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def render_items(items: CottList[MediaItem], mode: JsonMode) -> str:
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    mode = _cott_validate_abi(mode, JsonMode, path="$.mode")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/render_items.py", "2f81fec28d6c605789e226b7892f041791a91a8abf7d2634c50b0fd7ef8ea2d0", "render_items", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.render_items")
        _result = _implementation(items, mode)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.render_items"
        if _error.span is None:
            _error.span = {"end_byte":14727,"end_column":1,"end_line":632,"start_byte":14647,"start_column":1,"start_line":629}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.render_items", phase="implementation-call", span={"end_byte":14727,"end_column":1,"end_line":632,"start_byte":14647,"start_column":1,"start_line":629}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.render_items", phase="implementation-call", span={"end_byte":14727,"end_column":1,"end_line":632,"start_byte":14647,"start_column":1,"start_line":629}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def plan_post_processing(item: MediaItem, request: PostProcessRequest) -> Result[CottList[ExternalToolRequest], MediaError]:
    """No kinds returns typed List[ExternalToolRequest]; otherwise preserve kind order."""
    item = _cott_validate_abi(item, MediaItem, path="$.item")
    request = _cott_validate_abi(request, PostProcessRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/plan_post_processing.py", "76554642cc951fd47093225cc7b1ff2804d70d0da634981a68fc36c35247b768", "plan_post_processing", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.plan_post_processing")
        _result = _implementation(item, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.plan_post_processing"
        if _error.span is None:
            _error.span = {"end_byte":15124,"end_column":1,"end_line":647,"start_byte":14727,"start_column":1,"start_line":632}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_post_processing", phase="implementation-call", span={"end_byte":15124,"end_column":1,"end_line":647,"start_byte":14727,"start_column":1,"start_line":632}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_post_processing", phase="implementation-call", span={"end_byte":15124,"end_column":1,"end_line":647,"start_byte":14727,"start_column":1,"start_line":632}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[ExternalToolRequest], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.plan_post_processing", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_ExternalToolMissing, MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.plan_post_processing", phase="error", span={"end_byte":15124,"end_column":1,"end_line":647,"start_byte":14727,"start_column":1,"start_line":632}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.plan_post_processing", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            planned = _cott_match_value.value
            return ((len(planned) <= len((request).kinds)))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.plan_post_processing", clause="ensures:1", phase="ensures", span={"end_byte":15030,"end_column":67,"end_line":640,"start_byte":14968,"start_column":5,"start_line":640}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[ExternalToolRequest], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def run_post_processing(requests: CottList[ExternalToolRequest]) -> Result[Unit, MediaError]:
    requests = _cott_validate_abi(requests, CottList[ExternalToolRequest], path="$.requests")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/run_post_processing.py", "19636461c149b6ec3c32fd90bcd7a1f46c2a53dd8f8c999810ca8eb06a8a5ca6", "run_post_processing", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.run_post_processing")
        _result = _implementation(requests)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.run_post_processing"
        if _error.span is None:
            _error.span = {"end_byte":15384,"end_column":1,"end_line":655,"start_byte":15124,"start_column":1,"start_line":647}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.run_post_processing", phase="implementation-call", span={"end_byte":15384,"end_column":1,"end_line":655,"start_byte":15124,"start_column":1,"start_line":647}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.run_post_processing", phase="implementation-call", span={"end_byte":15384,"end_column":1,"end_line":655,"start_byte":15124,"start_column":1,"start_line":647}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.run_post_processing", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_ExternalToolMissing, MediaError_PostProcessFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.run_post_processing", phase="error", span={"end_byte":15384,"end_column":1,"end_line":655,"start_byte":15124,"start_column":1,"start_line":647}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.run_post_processing", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            completed = _cott_match_value.value
            return ((completed == UNIT))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.run_post_processing", clause="ensures:0", phase="ensures", span={"end_byte":15264,"end_column":52,"end_line":648,"start_byte":15217,"start_column":5,"start_line":648}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def apply_update(request: UpdateRequest) -> Result[Unit, MediaError]:
    request = _cott_validate_abi(request, UpdateRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/apply_update.py", "3eed4402e61a63358bd849c42e04ffe3d2e0a20dea5b75c4325f469a75168b48", "apply_update", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.apply_update")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.apply_update"
        if _error.span is None:
            _error.span = {"end_byte":15648,"end_column":1,"end_line":664,"start_byte":15384,"start_column":1,"start_line":655}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.apply_update", phase="implementation-call", span={"end_byte":15648,"end_column":1,"end_line":664,"start_byte":15384,"start_column":1,"start_line":655}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.apply_update", phase="implementation-call", span={"end_byte":15648,"end_column":1,"end_line":664,"start_byte":15384,"start_column":1,"start_line":655}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.apply_update", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_UpdateUnavailable, MediaError_NetworkFailure, MediaError_OutputFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.apply_update", phase="error", span={"end_byte":15648,"end_column":1,"end_line":664,"start_byte":15384,"start_column":1,"start_line":655}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.apply_update", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return ((updated == UNIT))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.apply_update", clause="ensures:0", phase="ensures", span={"end_byte":15500,"end_column":48,"end_line":656,"start_byte":15457,"start_column":5,"start_line":656}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def execute(request: ExecutionRequest) -> Result[ExecutionReport, MediaError]:
    request = _cott_validate_abi(request, ExecutionRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/execute.py", "212e69c90a16ebcc8331bd66e41ff648e755b8c5d87cad6833673a0aceb1b3ee", "execute", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.execute")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.execute"
        if _error.span is None:
            _error.span = {"end_byte":16876,"end_column":1,"end_line":697,"start_byte":15648,"start_column":1,"start_line":664}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.execute", phase="implementation-call", span={"end_byte":16876,"end_column":1,"end_line":697,"start_byte":15648,"start_column":1,"start_line":664}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.execute", phase="implementation-call", span={"end_byte":16876,"end_column":1,"end_line":697,"start_byte":15648,"start_column":1,"start_line":664}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ExecutionReport, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidConfig, MediaError_InvalidInput, MediaError_AuthenticationFailed, MediaError_BatchReadFailed, MediaError_InvalidShortcut, MediaError_CertificateFailure, MediaError_WorkaroundRejected, MediaError_LogFailure, MediaError_InvalidRange, MediaError_CookieFailure, MediaError_GeoRestricted, MediaError_ExtractorMissing, MediaError_PluginRejected, MediaError_UnsupportedUrl, MediaError_FormatUnavailable, MediaError_SubtitleUnavailable, MediaError_InvalidTemplate, MediaError_ArchiveFailure, MediaError_PathFailure, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_SizeLimit, MediaError_RetryExhausted, MediaError_ExternalToolMissing, MediaError_PostProcessFailed, MediaError_UpdateUnavailable,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.execute", phase="error", span={"end_byte":16876,"end_column":1,"end_line":697,"start_byte":15648,"start_column":1,"start_line":664}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            report = _cott_match_value.value
            return (((report).simulated == ((request).simulation != SimulationMode_Download())))
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.execute", clause="ensures:0", phase="ensures", span={"end_byte":15826,"end_column":101,"end_line":665,"start_byte":15730,"start_column":5,"start_line":665}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ExecutionReport, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def run(arguments: CottList[str]) -> Never:
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/run.py", "34f1f98345f1c33edeb09e5407c2488daa7c014262023534cd2c1c998aa41949", "run", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.run")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.run"
        if _error.span is None:
            _error.span = {"end_byte":16989,"end_column":1,"end_line":699,"start_byte":16876,"start_column":1,"start_line":697}
        raise
    except SystemExit:
        raise
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.run", phase="implementation-call", span={"end_byte":16989,"end_column":1,"end_line":699,"start_byte":16876,"start_column":1,"start_line":697}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    raise CottContractViolation("Never function returned", symbol="real.yt_dlp.run", phase="return", span={"end_byte":16989,"end_column":1,"end_line":699,"start_byte":16876,"start_column":1,"start_line":697}, expected="Never", actual=repr(_result))

__all__ = ["ArchiveRequest", "Authentication", "AuthenticationKind", "AuthenticationKind_Anonymous", "AuthenticationKind_BrowserCookies", "AuthenticationKind_Cookies", "AuthenticationKind_Credentials", "AuthenticationKind_Netrc", "CertificatePolicy", "CertificatePolicy_Insecure", "CertificatePolicy_Verify", "CliInput", "DownloadPlan", "ExecutionReport", "ExecutionRequest", "ExternalToolRequest", "ExtractorDescriptor", "ExtractorWorkaround", "ExtractorWorkaround_ForceGeneric", "ExtractorWorkaround_LegacyServerConnect", "ExtractorWorkaround_NoCheckCertificates", "ExtractorWorkaround_NoPlaylist", "FormatContainer", "FormatContainer_Any", "FormatContainer_Audio", "FormatContainer_Best", "FormatContainer_Video", "FormatContainer_Worst", "FormatDescriptor", "FormatRequest", "FragmentPolicy", "GeoBypassMode", "GeoBypassMode_Country", "GeoBypassMode_Default", "GeoBypassMode_Disabled", "GeoBypassMode_IpBlock", "InputKind", "InputKind_Argument", "InputKind_BatchFile", "InputKind_ConfigFile", "JsonMode", "JsonMode_Lines", "JsonMode_Single", "LiveMode", "LiveMode_Default", "LiveMode_FromStart", "LiveMode_Wait", "LiveRequest", "LogLevel", "LogLevel_Debug", "LogLevel_Info", "LogLevel_Quiet", "LogLevel_Warning", "MediaError", "MediaError_ArchiveFailure", "MediaError_AuthenticationFailed", "MediaError_BatchReadFailed", "MediaError_CertificateFailure", "MediaError_CookieFailure", "MediaError_ExternalToolMissing", "MediaError_ExtractorMissing", "MediaError_FormatUnavailable", "MediaError_GeoRestricted", "MediaError_HttpStatus", "MediaError_InvalidConfig", "MediaError_InvalidInput", "MediaError_InvalidRange", "MediaError_InvalidShortcut", "MediaError_InvalidTemplate", "MediaError_LogFailure", "MediaError_NetworkFailure", "MediaError_OutputFailure", "MediaError_PathFailure", "MediaError_PluginRejected", "MediaError_PostProcessFailed", "MediaError_RetryExhausted", "MediaError_SizeLimit", "MediaError_SubtitleUnavailable", "MediaError_UnsupportedUrl", "MediaError_UpdateUnavailable", "MediaError_WorkaroundRejected", "MediaItem", "MetadataRequest", "NetworkPolicy", "OutputRequest", "PlaylistMode", "PlaylistMode_Flat", "PlaylistMode_Playlist", "PlaylistMode_Random", "PlaylistMode_Reverse", "PlaylistMode_Single", "PlaylistRange", "PlaylistRequest", "PluginDescriptor", "PostProcessRequest", "PostProcessorKind", "PostProcessorKind_ConvertThumbnails", "PostProcessorKind_EmbedMetadata", "PostProcessorKind_EmbedSubtitle", "PostProcessorKind_EmbedThumbnail", "PostProcessorKind_ExtractAudio", "PostProcessorKind_Fixup", "PostProcessorKind_RecodeVideo", "PostProcessorKind_RemuxVideo", "PostProcessorKind_SplitChapters", "PostProcessorKind_SponsorBlock", "PresentationRequest", "ProxyMode", "ProxyMode_Direct", "ProxyMode_Http", "ProxyMode_Socks", "ShortcutKind", "ShortcutKind_Search", "ShortcutKind_SearchAll", "ShortcutKind_Url", "ShortcutRequest", "SimulationMode", "SimulationMode_Download", "SimulationMode_PrintOnly", "SimulationMode_Simulate", "SimulationMode_SkipDownload", "SubtitleMode", "SubtitleMode_All", "SubtitleMode_Automatic", "SubtitleMode_Manual", "SubtitleMode_None", "SubtitleRequest", "ThumbnailRequest", "TransferReceipt", "TransferRequest", "UpdatePolicy", "UpdatePolicy_Apply", "UpdatePolicy_Check", "UpdatePolicy_Master", "UpdatePolicy_Never", "UpdatePolicy_Nightly", "UpdateRequest", "VideoFilterRequest", "WorkaroundPolicy", "apply_update", "build_shortcut_url", "choose_extractor", "configure_presentation", "discover_extractors", "execute", "expand_playlist_ranges", "extract_media", "filter_formats", "filter_video", "load_batch_urls", "load_config", "load_plugins", "parse_arguments", "parse_batch_urls", "plan_downloads", "plan_fragments", "plan_metadata", "plan_post_processing", "plan_thumbnails", "read_download_archive", "render_items", "render_output_path", "resolve_authentication", "resolve_inputs", "resolve_live_media", "resolve_output_path", "run", "run_post_processing", "select_geo_route", "select_playlist", "select_subtitles", "sort_formats", "transfer_fragments", "transfer_media", "validate_network", "validate_workarounds", "write_download_archive"]
