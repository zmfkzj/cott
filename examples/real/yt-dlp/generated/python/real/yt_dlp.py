from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.yt_dlp_types import ArchiveRequest, Authentication, AuthenticationKind, AuthenticationKind_Anonymous, AuthenticationKind_BrowserCookies, AuthenticationKind_Cookies, AuthenticationKind_Credentials, AuthenticationKind_Netrc, CertificatePolicy, CertificatePolicy_Insecure, CertificatePolicy_Verify, CliInput, DownloadPlan, ExecutionReport, ExecutionRequest, ExternalToolRequest, ExtractorDescriptor, ExtractorWorkaround, ExtractorWorkaround_ForceGeneric, ExtractorWorkaround_LegacyServerConnect, ExtractorWorkaround_NoCheckCertificates, ExtractorWorkaround_NoPlaylist, FormatContainer, FormatContainer_Any, FormatContainer_Audio, FormatContainer_Best, FormatContainer_Video, FormatContainer_Worst, FormatDescriptor, FormatRequest, FragmentPolicy, GeoBypassMode, GeoBypassMode_Country, GeoBypassMode_Default, GeoBypassMode_Disabled, GeoBypassMode_IpBlock, InputKind, InputKind_Argument, InputKind_BatchFile, InputKind_ConfigFile, JsonMode, JsonMode_Lines, JsonMode_Single, LiveMode, LiveMode_Default, LiveMode_FromStart, LiveMode_Wait, LiveRequest, LogLevel, LogLevel_Debug, LogLevel_Info, LogLevel_Quiet, LogLevel_Warning, MediaError, MediaError_ArchiveFailure, MediaError_AuthenticationFailed, MediaError_BatchReadFailed, MediaError_CertificateFailure, MediaError_CookieFailure, MediaError_ExternalToolMissing, MediaError_ExtractorMissing, MediaError_FormatUnavailable, MediaError_GeoRestricted, MediaError_HttpStatus, MediaError_InvalidConfig, MediaError_InvalidInput, MediaError_InvalidRange, MediaError_InvalidShortcut, MediaError_InvalidTemplate, MediaError_LogFailure, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_PathFailure, MediaError_PluginRejected, MediaError_PostProcessFailed, MediaError_RetryExhausted, MediaError_SizeLimit, MediaError_SubtitleUnavailable, MediaError_UnsupportedUrl, MediaError_UpdateUnavailable, MediaError_WorkaroundRejected, MediaItem, MetadataRequest, NetworkPolicy, OutputRequest, PlaylistMode, PlaylistMode_Flat, PlaylistMode_Playlist, PlaylistMode_Random, PlaylistMode_Reverse, PlaylistMode_Single, PlaylistRange, PlaylistRequest, PluginDescriptor, PostProcessRequest, PostProcessorKind, PostProcessorKind_ConvertThumbnails, PostProcessorKind_EmbedMetadata, PostProcessorKind_EmbedSubtitle, PostProcessorKind_EmbedThumbnail, PostProcessorKind_ExtractAudio, PostProcessorKind_Fixup, PostProcessorKind_RecodeVideo, PostProcessorKind_RemuxVideo, PostProcessorKind_SplitChapters, PostProcessorKind_SponsorBlock, PresentationRequest, ProxyMode, ProxyMode_Direct, ProxyMode_Http, ProxyMode_Socks, ShortcutKind, ShortcutKind_Search, ShortcutKind_SearchAll, ShortcutKind_Url, ShortcutRequest, SimulationMode, SimulationMode_Download, SimulationMode_PrintOnly, SimulationMode_Simulate, SimulationMode_SkipDownload, SubtitleMode, SubtitleMode_All, SubtitleMode_Automatic, SubtitleMode_Manual, SubtitleMode_None, SubtitleRequest, ThumbnailRequest, TransferReceipt, TransferRequest, UpdatePolicy, UpdatePolicy_Apply, UpdatePolicy_Check, UpdatePolicy_Master, UpdatePolicy_Never, UpdatePolicy_Nightly, UpdateRequest, VideoFilterRequest, WorkaroundPolicy

def parse_arguments(arguments: CottList[str]) -> Result[CottList[CliInput], MediaError]:
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/parse_arguments.py", "813abe8e2c88652f918152270586b42b8141bae160d7f9e5ea28f625c95833cd", "parse_arguments", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.parse_arguments")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.parse_arguments"
        if _error.span is None:
            _error.span = {"end_byte":8511,"end_column":1,"end_line":388,"start_byte":8318,"start_column":1,"start_line":381}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.parse_arguments", phase="implementation-call", span={"end_byte":8511,"end_column":1,"end_line":388,"start_byte":8318,"start_column":1,"start_line":381}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.parse_arguments", phase="implementation-call", span={"end_byte":8511,"end_column":1,"end_line":388,"start_byte":8318,"start_column":1,"start_line":381}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CliInput], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.parse_arguments", phase="error", span={"end_byte":8511,"end_column":1,"end_line":388,"start_byte":8318,"start_column":1,"start_line":381}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.parse_arguments", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.parse_arguments", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            inputs = _cott_match_value.value
            return (_cott_contract_condition(((len(inputs) <= len(arguments))), "real.yt_dlp.parse_arguments", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.parse_arguments", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.parse_arguments", clause="ensures:0", phase="ensures", span={"end_byte":8458,"end_column":61,"end_line":382,"start_byte":8402,"start_column":5,"start_line":382}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CliInput], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def build_shortcut_url(request: ShortcutRequest) -> Result[str, MediaError]:
    """Search returns `ytsearch{limit}:{query}` using the positive base-10 limit.
SearchAll returns `ytsearchall:{query}` and ignores limit, including zero.
Url ignores limit, strips only outer whitespace, validates the schemes and
authority documented by ShortcutRequest, and returns that stripped URL
unchanged. Do not percent-encode, case-fold, or otherwise normalize output.
Return InvalidShortcut(value=request.query) for an empty search query, a
zero Search limit, or an invalid Url."""
    request = _cott_validate_abi(request, ShortcutRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((len((request).query) == 0)), "real.yt_dlp.build_shortcut_url", "error:2:condition")):
        _expected_error = MediaError_InvalidShortcut
        _expected_error_span = {"end_byte":9226,"end_column":65,"end_line":401,"start_byte":9166,"start_column":5,"start_line":401}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/build_shortcut_url.py", "ae0f03f4ddc5e6bc824337b181970d9b9088d2caaf420f093a7b9a39cec7b0d6", "build_shortcut_url", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.build_shortcut_url")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.build_shortcut_url"
        if _error.span is None:
            _error.span = {"end_byte":9281,"end_column":1,"end_line":406,"start_byte":8511,"start_column":1,"start_line":388}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.build_shortcut_url", phase="implementation-call", span={"end_byte":9281,"end_column":1,"end_line":406,"start_byte":8511,"start_column":1,"start_line":388}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.build_shortcut_url", phase="implementation-call", span={"end_byte":9281,"end_column":1,"end_line":406,"start_byte":8511,"start_column":1,"start_line":388}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.build_shortcut_url", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidShortcut,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.build_shortcut_url", phase="error", span={"end_byte":9281,"end_column":1,"end_line":406,"start_byte":8511,"start_column":1,"start_line":388}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.build_shortcut_url", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.build_shortcut_url", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidShortcut:
        _cott_contract_condition(True, "real.yt_dlp.build_shortcut_url", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            url = _cott_match_value.value
            return (_cott_contract_condition(((len(url) > 0)), "real.yt_dlp.build_shortcut_url", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.build_shortcut_url", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.build_shortcut_url", clause="ensures:1", phase="ensures", span={"end_byte":9160,"end_column":42,"end_line":399,"start_byte":9123,"start_column":5,"start_line":399}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def validate_workarounds(policy: WorkaroundPolicy) -> Result[WorkaroundPolicy, MediaError]:
    policy = _cott_validate_abi(policy, WorkaroundPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/validate_workarounds.py", "46cdf00a7d6bbbd2f0df5bff360bfcb0b8e209c4d5298c2a0ec0a8f144e3beab", "validate_workarounds", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.validate_workarounds")
        _result = _implementation(policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.validate_workarounds"
        if _error.span is None:
            _error.span = {"end_byte":9542,"end_column":1,"end_line":414,"start_byte":9281,"start_column":1,"start_line":406}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.validate_workarounds", phase="implementation-call", span={"end_byte":9542,"end_column":1,"end_line":414,"start_byte":9281,"start_column":1,"start_line":406}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.validate_workarounds", phase="implementation-call", span={"end_byte":9542,"end_column":1,"end_line":414,"start_byte":9281,"start_column":1,"start_line":406}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[WorkaroundPolicy, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.validate_workarounds", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_CertificateFailure, MediaError_WorkaroundRejected,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.validate_workarounds", phase="error", span={"end_byte":9542,"end_column":1,"end_line":414,"start_byte":9281,"start_column":1,"start_line":406}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.validate_workarounds", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.validate_workarounds", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_CertificateFailure:
        _cott_contract_condition(True, "real.yt_dlp.validate_workarounds", "error:1")
    if type(_result) is Err and type(_result.error) is MediaError_WorkaroundRejected:
        _cott_contract_condition(True, "real.yt_dlp.validate_workarounds", "error:2")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            valid = _cott_match_value.value
            return (_cott_contract_condition((((valid).certificate == (policy).certificate)), "real.yt_dlp.validate_workarounds", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.validate_workarounds", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.validate_workarounds", clause="ensures:0", phase="ensures", span={"end_byte":9443,"end_column":72,"end_line":407,"start_byte":9376,"start_column":5,"start_line":407}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[WorkaroundPolicy, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def configure_presentation(request: PresentationRequest) -> Result[Unit, MediaError]:
    request = _cott_validate_abi(request, PresentationRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/configure_presentation.py", "769dbbe041b63e242ce2e5cccbaa3a31d169c79c1e9322c5d4c5e19a43d674d3", "configure_presentation", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.configure_presentation")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.configure_presentation"
        if _error.span is None:
            _error.span = {"end_byte":9741,"end_column":1,"end_line":421,"start_byte":9542,"start_column":1,"start_line":414}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.configure_presentation", phase="implementation-call", span={"end_byte":9741,"end_column":1,"end_line":421,"start_byte":9542,"start_column":1,"start_line":414}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.configure_presentation", phase="implementation-call", span={"end_byte":9741,"end_column":1,"end_line":421,"start_byte":9542,"start_column":1,"start_line":414}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.configure_presentation", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_LogFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.configure_presentation", phase="error", span={"end_byte":9741,"end_column":1,"end_line":421,"start_byte":9542,"start_column":1,"start_line":414}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.configure_presentation", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.configure_presentation", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_LogFailure:
        _cott_contract_condition(True, "real.yt_dlp.configure_presentation", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            configured = _cott_match_value.value
            return (_cott_contract_condition(((configured == UNIT)), "real.yt_dlp.configure_presentation", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.configure_presentation", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.configure_presentation", clause="ensures:0", phase="ensures", span={"end_byte":9680,"end_column":54,"end_line":415,"start_byte":9631,"start_column":5,"start_line":415}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_config(path: Path) -> Result[CottList[CliInput], MediaError]:
    path = _cott_validate_abi(path, Path, path="$.path")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/load_config.py", "5235646a03b2976279eb0d0080e8334a7651684bf52f3e7dbeb97ebf71dceab1", "load_config", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.load_config")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.load_config"
        if _error.span is None:
            _error.span = {"end_byte":9923,"end_column":1,"end_line":428,"start_byte":9741,"start_column":1,"start_line":421}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.load_config", phase="implementation-call", span={"end_byte":9923,"end_column":1,"end_line":428,"start_byte":9741,"start_column":1,"start_line":421}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.load_config", phase="implementation-call", span={"end_byte":9923,"end_column":1,"end_line":428,"start_byte":9741,"start_column":1,"start_line":421}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CliInput], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.load_config", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidConfig,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.load_config", phase="error", span={"end_byte":9923,"end_column":1,"end_line":428,"start_byte":9741,"start_column":1,"start_line":421}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.load_config", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.load_config", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidConfig:
        _cott_contract_condition(True, "real.yt_dlp.load_config", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            inputs = _cott_match_value.value
            return (_cott_contract_condition(((len(inputs) <= 100000)), "real.yt_dlp.load_config", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.load_config", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.load_config", clause="ensures:0", phase="ensures", span={"end_byte":9860,"end_column":54,"end_line":422,"start_byte":9811,"start_column":5,"start_line":422}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CliInput], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def parse_batch_urls(batch: str, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]:
    batch = _cott_validate_abi(batch, str, path="$.batch")
    comment_prefixes = _cott_validate_abi(comment_prefixes, CottList[str], path="$.comment_prefixes")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/parse_batch_urls.py", "311436ff253be6fc1b7919e798f8c5cdb4feca1419b63b28ac9af10585b39654", "parse_batch_urls", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.parse_batch_urls")
        _result = _implementation(batch, comment_prefixes)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.parse_batch_urls"
        if _error.span is None:
            _error.span = {"end_byte":10123,"end_column":1,"end_line":435,"start_byte":9923,"start_column":1,"start_line":428}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.parse_batch_urls", phase="implementation-call", span={"end_byte":10123,"end_column":1,"end_line":435,"start_byte":9923,"start_column":1,"start_line":428}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.parse_batch_urls", phase="implementation-call", span={"end_byte":10123,"end_column":1,"end_line":435,"start_byte":9923,"start_column":1,"start_line":428}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.parse_batch_urls", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.parse_batch_urls", phase="error", span={"end_byte":10123,"end_column":1,"end_line":435,"start_byte":9923,"start_column":1,"start_line":428}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.parse_batch_urls", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.parse_batch_urls", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.parse_batch_urls", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            urls = _cott_match_value.value
            return (_cott_contract_condition(((len(urls) <= len(batch))), "real.yt_dlp.parse_batch_urls", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.parse_batch_urls", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.parse_batch_urls", clause="ensures:0", phase="ensures", span={"end_byte":10070,"end_column":53,"end_line":429,"start_byte":10022,"start_column":5,"start_line":429}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_batch_urls(path: Path, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]:
    path = _cott_validate_abi(path, Path, path="$.path")
    comment_prefixes = _cott_validate_abi(comment_prefixes, CottList[str], path="$.comment_prefixes")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/load_batch_urls.py", "644dc91a5d71c642da597214a7e48db7e0bf8806d6c4d72bb86b6850716ca663", "load_batch_urls", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.load_batch_urls")
        _result = _implementation(path, comment_prefixes)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.load_batch_urls"
        if _error.span is None:
            _error.span = {"end_byte":10365,"end_column":1,"end_line":443,"start_byte":10123,"start_column":1,"start_line":435}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.load_batch_urls", phase="implementation-call", span={"end_byte":10365,"end_column":1,"end_line":443,"start_byte":10123,"start_column":1,"start_line":435}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.load_batch_urls", phase="implementation-call", span={"end_byte":10365,"end_column":1,"end_line":443,"start_byte":10123,"start_column":1,"start_line":435}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.load_batch_urls", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_BatchReadFailed, MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.load_batch_urls", phase="error", span={"end_byte":10365,"end_column":1,"end_line":443,"start_byte":10123,"start_column":1,"start_line":435}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.load_batch_urls", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.load_batch_urls", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_BatchReadFailed:
        _cott_contract_condition(True, "real.yt_dlp.load_batch_urls", "error:1")
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.load_batch_urls", "error:2")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            urls = _cott_match_value.value
            return (_cott_contract_condition(((len(urls) <= 100000)), "real.yt_dlp.load_batch_urls", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.load_batch_urls", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.load_batch_urls", clause="ensures:0", phase="ensures", span={"end_byte":10266,"end_column":50,"end_line":436,"start_byte":10221,"start_column":5,"start_line":436}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_inputs(inputs: CottList[CliInput], config: CottList[CliInput]) -> Result[CottList[str], MediaError]:
    inputs = _cott_validate_abi(inputs, CottList[CliInput], path="$.inputs")
    config = _cott_validate_abi(config, CottList[CliInput], path="$.config")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/resolve_inputs.py", "7d0c007d26ac8f5b996dfce25f5dca4485134644873433da274d2e325b99e042", "resolve_inputs", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.resolve_inputs")
        _result = _implementation(inputs, config)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.resolve_inputs"
        if _error.span is None:
            _error.span = {"end_byte":10584,"end_column":1,"end_line":450,"start_byte":10365,"start_column":1,"start_line":443}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.resolve_inputs", phase="implementation-call", span={"end_byte":10584,"end_column":1,"end_line":450,"start_byte":10365,"start_column":1,"start_line":443}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.resolve_inputs", phase="implementation-call", span={"end_byte":10584,"end_column":1,"end_line":450,"start_byte":10365,"start_column":1,"start_line":443}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.resolve_inputs", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.resolve_inputs", phase="error", span={"end_byte":10584,"end_column":1,"end_line":450,"start_byte":10365,"start_column":1,"start_line":443}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.resolve_inputs", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.resolve_inputs", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.resolve_inputs", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            urls = _cott_match_value.value
            return (_cott_contract_condition(((len(urls) <= (len(inputs) + len(config)))), "real.yt_dlp.resolve_inputs", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.resolve_inputs", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_inputs", clause="ensures:0", phase="ensures", span={"end_byte":10531,"end_column":67,"end_line":444,"start_byte":10469,"start_column":5,"start_line":444}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def validate_network(policy: NetworkPolicy) -> Result[NetworkPolicy, MediaError]:
    policy = _cott_validate_abi(policy, NetworkPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/validate_network.py", "297c7a3a9dae00d22191b2ebbd7dfbde9669b0256897ad93cea48f41d326fa44", "validate_network", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.validate_network")
        _result = _implementation(policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.validate_network"
        if _error.span is None:
            _error.span = {"end_byte":10777,"end_column":1,"end_line":457,"start_byte":10584,"start_column":1,"start_line":450}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.validate_network", phase="implementation-call", span={"end_byte":10777,"end_column":1,"end_line":457,"start_byte":10584,"start_column":1,"start_line":450}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.validate_network", phase="implementation-call", span={"end_byte":10777,"end_column":1,"end_line":457,"start_byte":10584,"start_column":1,"start_line":450}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[NetworkPolicy, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.validate_network", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.validate_network", phase="error", span={"end_byte":10777,"end_column":1,"end_line":457,"start_byte":10584,"start_column":1,"start_line":450}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.validate_network", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.validate_network", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.validate_network", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            valid = _cott_match_value.value
            return (_cott_contract_condition((((valid).socket_timeout_ms > 0)), "real.yt_dlp.validate_network", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.validate_network", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.validate_network", clause="ensures:0", phase="ensures", span={"end_byte":10724,"end_column":60,"end_line":451,"start_byte":10669,"start_column":5,"start_line":451}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[NetworkPolicy, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_authentication(request: Authentication) -> Result[Authentication, MediaError]:
    request = _cott_validate_abi(request, Authentication, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/resolve_authentication.py", "d2dd4268ea412a05d7afea46c643c9c38f1b19aa904a774b1fb47c7ea9e20595", "resolve_authentication", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.resolve_authentication")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.resolve_authentication"
        if _error.span is None:
            _error.span = {"end_byte":11046,"end_column":1,"end_line":465,"start_byte":10777,"start_column":1,"start_line":457}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.resolve_authentication", phase="implementation-call", span={"end_byte":11046,"end_column":1,"end_line":465,"start_byte":10777,"start_column":1,"start_line":457}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.resolve_authentication", phase="implementation-call", span={"end_byte":11046,"end_column":1,"end_line":465,"start_byte":10777,"start_column":1,"start_line":457}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Authentication, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.resolve_authentication", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_AuthenticationFailed, MediaError_CookieFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.resolve_authentication", phase="error", span={"end_byte":11046,"end_column":1,"end_line":465,"start_byte":10777,"start_column":1,"start_line":457}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.resolve_authentication", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.resolve_authentication", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_AuthenticationFailed:
        _cott_contract_condition(True, "real.yt_dlp.resolve_authentication", "error:1")
    if type(_result) is Err and type(_result.error) is MediaError_CookieFailure:
        _cott_contract_condition(True, "real.yt_dlp.resolve_authentication", "error:2")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            authenticated = _cott_match_value.value
            return (_cott_contract_condition((((authenticated).kind == (request).kind)), "real.yt_dlp.resolve_authentication", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.resolve_authentication", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_authentication", clause="ensures:0", phase="ensures", span={"end_byte":10941,"end_column":75,"end_line":458,"start_byte":10871,"start_column":5,"start_line":458}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Authentication, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def select_geo_route(policy: NetworkPolicy) -> Result[NetworkPolicy, MediaError]:
    policy = _cott_validate_abi(policy, NetworkPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/select_geo_route.py", "ee67afafd88ea6557a9ade1a364d23f68d6ed6c6840d8c04c6fdf27f1e76ae17", "select_geo_route", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.select_geo_route")
        _result = _implementation(policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.select_geo_route"
        if _error.span is None:
            _error.span = {"end_byte":11257,"end_column":1,"end_line":472,"start_byte":11046,"start_column":1,"start_line":465}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.select_geo_route", phase="implementation-call", span={"end_byte":11257,"end_column":1,"end_line":472,"start_byte":11046,"start_column":1,"start_line":465}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.select_geo_route", phase="implementation-call", span={"end_byte":11257,"end_column":1,"end_line":472,"start_byte":11046,"start_column":1,"start_line":465}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[NetworkPolicy, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.select_geo_route", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_GeoRestricted,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.select_geo_route", phase="error", span={"end_byte":11257,"end_column":1,"end_line":472,"start_byte":11046,"start_column":1,"start_line":465}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.select_geo_route", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.select_geo_route", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_GeoRestricted:
        _cott_contract_condition(True, "real.yt_dlp.select_geo_route", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            route = _cott_match_value.value
            return (_cott_contract_condition((((route).proxy_mode == (policy).proxy_mode)), "real.yt_dlp.select_geo_route", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.select_geo_route", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.select_geo_route", clause="ensures:0", phase="ensures", span={"end_byte":11196,"end_column":70,"end_line":466,"start_byte":11131,"start_column":5,"start_line":466}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[NetworkPolicy, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def discover_extractors() -> CottList[ExtractorDescriptor]:
    """Return one enabled generic HTTP extractor named "generic", accepting the
prefixes "http://" and "https://", with requires_login false. This is a
direct-media client, not a registry of upstream site-specific extractors."""
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/discover_extractors.py", "1a728279216552f89f9753c29437016f1d0da22c3bcad47234dc165deccc1d32", "discover_extractors", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.discover_extractors")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.discover_extractors"
        if _error.span is None:
            _error.span = {"end_byte":11580,"end_column":1,"end_line":481,"start_byte":11257,"start_column":1,"start_line":472}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.discover_extractors", phase="implementation-call", span={"end_byte":11580,"end_column":1,"end_line":481,"start_byte":11257,"start_column":1,"start_line":472}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.discover_extractors", phase="implementation-call", span={"end_byte":11580,"end_column":1,"end_line":481,"start_byte":11257,"start_column":1,"start_line":472}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[ExtractorDescriptor], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[ExtractorDescriptor], path="$.return", validator=_cott_validate_abi)
    return _result

def load_plugins(paths: CottList[Path]) -> Result[CottList[PluginDescriptor], MediaError]:
    """Read declarative UTF-8-sig text manifests, never Python modules or executable
plugins. Each input Path names one regular non-symlink file, not a directory.
Process input paths in order without recursion or deduplication. The descriptor
name is path.stem, and its path is the original input Path.
Strip each line; ignore blank lines and lines beginning "#". Remaining lines
use TYPE:NAME, splitting at the first colon and stripping NAME. TYPE is exactly
extractor, postprocessor or post_processor; NAME is nonempty. Append names in
declaration order to the corresponding list, preserving duplicates.
At least one extractor or postprocessor declaration and a nonempty stem are
required. Do not import, inspect, execute or discover code from these names.
Reject more than 100000 input paths before I/O using paths[100000] as the error
path. Each file has a bounded 1 MiB read limit and at most 100000 declarations;
oversized input is rejected, not truncated. Empty input returns an empty list.
Any missing/nonregular/symlink file, I/O/decoding/format/size/declaration error
fails the entire call as PluginRejected(path=the offending path, message=a
fixed descriptive category), with no partial result and no content in errors."""
    paths = _cott_validate_abi(paths, CottList[Path], path="$.paths")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/load_plugins.py", "da32e2462049af99bb467abbd76b718619b7fe2e2c84d49f4daadffc4fc31e2d", "load_plugins", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.load_plugins")
        _result = _implementation(paths)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.load_plugins"
        if _error.span is None:
            _error.span = {"end_byte":13090,"end_column":1,"end_line":507,"start_byte":11580,"start_column":1,"start_line":481}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.load_plugins", phase="implementation-call", span={"end_byte":13090,"end_column":1,"end_line":507,"start_byte":11580,"start_column":1,"start_line":481}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.load_plugins", phase="implementation-call", span={"end_byte":13090,"end_column":1,"end_line":507,"start_byte":11580,"start_column":1,"start_line":481}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[PluginDescriptor], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.load_plugins", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_PluginRejected,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.load_plugins", phase="error", span={"end_byte":13090,"end_column":1,"end_line":507,"start_byte":11580,"start_column":1,"start_line":481}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.load_plugins", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.load_plugins", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_PluginRejected:
        _cott_contract_condition(True, "real.yt_dlp.load_plugins", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plugins = _cott_match_value.value
            return (_cott_contract_condition(((len(plugins) <= 100000)), "real.yt_dlp.load_plugins", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.load_plugins", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.load_plugins", clause="ensures:1", phase="ensures", span={"end_byte":13026,"end_column":56,"end_line":501,"start_byte":12975,"start_column":5,"start_line":501}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[PluginDescriptor], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def choose_extractor(url: str, extractors: CottList[ExtractorDescriptor]) -> Result[ExtractorDescriptor, MediaError]:
    url = _cott_validate_abi(url, str, path="$.url")
    extractors = _cott_validate_abi(extractors, CottList[ExtractorDescriptor], path="$.extractors")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/choose_extractor.py", "98dcc114c31867a685da7c2ad7e3ed749bb5f9bf7ff7d830ecbb00fec134df1d", "choose_extractor", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.choose_extractor")
        _result = _implementation(url, extractors)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.choose_extractor"
        if _error.span is None:
            _error.span = {"end_byte":13360,"end_column":1,"end_line":518,"start_byte":13090,"start_column":1,"start_line":507}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.choose_extractor", phase="implementation-call", span={"end_byte":13360,"end_column":1,"end_line":518,"start_byte":13090,"start_column":1,"start_line":507}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.choose_extractor", phase="implementation-call", span={"end_byte":13360,"end_column":1,"end_line":518,"start_byte":13090,"start_column":1,"start_line":507}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ExtractorDescriptor, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.choose_extractor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_UnsupportedUrl, MediaError_ExtractorMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.choose_extractor", phase="error", span={"end_byte":13360,"end_column":1,"end_line":518,"start_byte":13090,"start_column":1,"start_line":507}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.choose_extractor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.choose_extractor", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_UnsupportedUrl:
        _cott_contract_condition(True, "real.yt_dlp.choose_extractor", "error:1")
    if type(_result) is Err and type(_result.error) is MediaError_ExtractorMissing:
        _cott_contract_condition(True, "real.yt_dlp.choose_extractor", "error:2")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            extractor = _cott_match_value.value
            return (_cott_contract_condition(((extractor).enabled), "real.yt_dlp.choose_extractor", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.choose_extractor", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.choose_extractor", clause="ensures:0", phase="ensures", span={"end_byte":13267,"end_column":54,"end_line":511,"start_byte":13218,"start_column":5,"start_line":511}, expected="true", actual="false")
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
        _implementation = _cott_load("_cott_impl/real/yt_dlp/extract_media.py", "04f8a0a998c22cf540b7e3c9feef775bbfc658521a6d23d25110705ff3b95fff", "extract_media", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.extract_media")
        _result = _implementation(url, extractor, authentication, network)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.extract_media"
        if _error.span is None:
            _error.span = {"end_byte":13903,"end_column":1,"end_line":538,"start_byte":13360,"start_column":1,"start_line":518}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.extract_media", phase="implementation-call", span={"end_byte":13903,"end_column":1,"end_line":538,"start_byte":13360,"start_column":1,"start_line":518}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.extract_media", phase="implementation-call", span={"end_byte":13903,"end_column":1,"end_line":538,"start_byte":13360,"start_column":1,"start_line":518}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.extract_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_AuthenticationFailed, MediaError_GeoRestricted, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_UnsupportedUrl,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.extract_media", phase="error", span={"end_byte":13903,"end_column":1,"end_line":538,"start_byte":13360,"start_column":1,"start_line":518}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.extract_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.extract_media", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_AuthenticationFailed:
        _cott_contract_condition(True, "real.yt_dlp.extract_media", "error:2")
    if type(_result) is Err and type(_result.error) is MediaError_GeoRestricted:
        _cott_contract_condition(True, "real.yt_dlp.extract_media", "error:3")
    if type(_result) is Err and type(_result.error) is MediaError_HttpStatus:
        _cott_contract_condition(True, "real.yt_dlp.extract_media", "error:4")
    if type(_result) is Err and type(_result.error) is MediaError_NetworkFailure:
        _cott_contract_condition(True, "real.yt_dlp.extract_media", "error:5")
    if type(_result) is Err and type(_result.error) is MediaError_UnsupportedUrl:
        _cott_contract_condition(True, "real.yt_dlp.extract_media", "error:6")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            items = _cott_match_value.value
            return (_cott_contract_condition(((len(items) <= 100000)), "real.yt_dlp.extract_media", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.extract_media", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.extract_media", clause="ensures:1", phase="ensures", span={"end_byte":13696,"end_column":52,"end_line":528,"start_byte":13649,"start_column":5,"start_line":528}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[MediaItem], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def expand_playlist_ranges(items: CottList[MediaItem], ranges: CottList[PlaylistRange]) -> Result[CottList[MediaItem], MediaError]:
    """Empty ranges returns items unchanged. Otherwise validate every range: first
and last are positive inclusive MediaItem.playlist_index values, not list
positions; first greater than last is InvalidRange. Iterate ranges in request
order and items in input order, appending matching items for each range.
Overlapping ranges deliberately repeat occurrences. An out-of-bounds range
contributes no matches. Preserve every MediaItem field, including playlist_index."""
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    ranges = _cott_validate_abi(ranges, CottList[PlaylistRange], path="$.ranges")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/expand_playlist_ranges.py", "cc4992ee11bbcec5ac83c54b4bcc9171a792d73a28b35974ed74d931e6cba6f8", "expand_playlist_ranges", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.expand_playlist_ranges")
        _result = _implementation(items, ranges)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.expand_playlist_ranges"
        if _error.span is None:
            _error.span = {"end_byte":14736,"end_column":1,"end_line":557,"start_byte":13903,"start_column":1,"start_line":538}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.expand_playlist_ranges", phase="implementation-call", span={"end_byte":14736,"end_column":1,"end_line":557,"start_byte":13903,"start_column":1,"start_line":538}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.expand_playlist_ranges", phase="implementation-call", span={"end_byte":14736,"end_column":1,"end_line":557,"start_byte":13903,"start_column":1,"start_line":538}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.expand_playlist_ranges", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidRange,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.expand_playlist_ranges", phase="error", span={"end_byte":14736,"end_column":1,"end_line":557,"start_byte":13903,"start_column":1,"start_line":538}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.expand_playlist_ranges", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.expand_playlist_ranges", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidRange:
        _cott_contract_condition(True, "real.yt_dlp.expand_playlist_ranges", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return (_cott_contract_condition(((((len(ranges) == 0) and (len(selected) == len(items))) or ((len(ranges) > 0) and (len(selected) <= (len(items) * len(ranges)))))), "real.yt_dlp.expand_playlist_ranges", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.expand_playlist_ranges", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.expand_playlist_ranges", clause="ensures:1", phase="ensures", span={"end_byte":14683,"end_column":148,"end_line":551,"start_byte":14540,"start_column":5,"start_line":551}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[MediaItem], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def select_playlist(items: CottList[MediaItem], request: PlaylistRequest) -> Result[CottList[MediaItem], MediaError]:
    """Reject positive start/end with start greater than end as InvalidRange before
any selection. Zero start/end means the corresponding bound is absent.
Call real.yt_dlp.expand_playlist_ranges and propagate InvalidRange.
Scan the expanded result in its order, keeping no more occurrences of an exact
MediaItem value (all five fields) than appeared in the original input. Consume
that occurrence allowance before testing inclusive start/end playlist_index
bounds; this prevents overlap expansion from exceeding the input length.
An empty request.items string adds no filter. Otherwise split it on commas,
strip each token, require a nonempty str.isdecimal() token with integer value
1..2^64-1, and form a set of requested playlist_index values. Invalid selectors
return InvalidInput with a fixed descriptive message; ranges, negative indices
and step syntax in this string are not supported. Filter the selected list by
membership without changing its current order or renumbering indices.
Then Single keeps only the first selected item; Playlist and Flat keep all
descriptor values (Flat does not perform an additional metadata fetch).
Reverse requests a reversal, Random requests a shuffle. Apply one reversal
when either mode Reverse or flag reverse is set, then one random.shuffle when
either mode Random or flag random is set. Both can be requested together in
that order. Single truncation happens before flags. Preserve duplicates up to
their original multiplicity and keep item fields unchanged."""
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    request = _cott_validate_abi(request, PlaylistRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/select_playlist.py", "c040807bbcbb438f7bbd06833367baf4ff023a90a1098e75dcd6264ba9470b81", "select_playlist", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.select_playlist")
        _result = _implementation(items, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.select_playlist"
        if _error.span is None:
            _error.span = {"end_byte":16608,"end_column":1,"end_line":591,"start_byte":14736,"start_column":1,"start_line":557}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.select_playlist", phase="implementation-call", span={"end_byte":16608,"end_column":1,"end_line":591,"start_byte":14736,"start_column":1,"start_line":557}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.select_playlist", phase="implementation-call", span={"end_byte":16608,"end_column":1,"end_line":591,"start_byte":14736,"start_column":1,"start_line":557}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.select_playlist", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidRange, MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.select_playlist", phase="error", span={"end_byte":16608,"end_column":1,"end_line":591,"start_byte":14736,"start_column":1,"start_line":557}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.select_playlist", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.select_playlist", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidRange:
        _cott_contract_condition(True, "real.yt_dlp.select_playlist", "error:2")
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.select_playlist", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return (_cott_contract_condition(((len(selected) <= len(items))), "real.yt_dlp.select_playlist", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.select_playlist", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.select_playlist", clause="ensures:1", phase="ensures", span={"end_byte":16515,"end_column":61,"end_line":584,"start_byte":16459,"start_column":5,"start_line":584}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[MediaItem], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_live_media(items: CottList[MediaItem], request: LiveRequest) -> Result[CottList[MediaItem], MediaError]:
    """This stage validates a snapshot of already-discovered live-media candidates;
it is not a downloader, live-status probe or polling loop. MediaItem contains
no start-time or live-state field, so do not infer such state from its text.
concurrent_fragments zero returns InvalidInput. Otherwise Default and
FromStart retain every supplied item unchanged and in order: retrieval from
the beginning is a downstream transfer choice, not a change to these descriptors.
Wait additionally requires wait_for_video_ms greater than zero; zero is
InvalidInput. With a positive wait budget, a nonempty snapshot succeeds
unchanged; an empty snapshot returns RetryExhausted(attempts=1), referring to
this one completed discovery snapshot. This function does not sleep, repeat
discovery or claim a network observation; clock/network are permitted effects,
not a requirement to invent a request endpoint."""
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    request = _cott_validate_abi(request, LiveRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/resolve_live_media.py", "de65ee2cf37c94b828d9d9b2a1e26fcb9ea90695597eeed364469d44f4774f4a", "resolve_live_media", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.resolve_live_media")
        _result = _implementation(items, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.resolve_live_media"
        if _error.span is None:
            _error.span = {"end_byte":17844,"end_column":1,"end_line":617,"start_byte":16608,"start_column":1,"start_line":591}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.resolve_live_media", phase="implementation-call", span={"end_byte":17844,"end_column":1,"end_line":617,"start_byte":16608,"start_column":1,"start_line":591}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.resolve_live_media", phase="implementation-call", span={"end_byte":17844,"end_column":1,"end_line":617,"start_byte":16608,"start_column":1,"start_line":591}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.resolve_live_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput, MediaError_RetryExhausted,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.resolve_live_media", phase="error", span={"end_byte":17844,"end_column":1,"end_line":617,"start_byte":16608,"start_column":1,"start_line":591}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.resolve_live_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.resolve_live_media", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.resolve_live_media", "error:2")
    if type(_result) is Err and type(_result.error) is MediaError_RetryExhausted:
        _cott_contract_condition(True, "real.yt_dlp.resolve_live_media", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return (_cott_contract_condition(((len(selected) <= len(items))), "real.yt_dlp.resolve_live_media", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.resolve_live_media", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_live_media", clause="ensures:1", phase="ensures", span={"end_byte":17741,"end_column":61,"end_line":610,"start_byte":17685,"start_column":5,"start_line":610}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[MediaItem], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def filter_video(items: CottList[MediaItem], request: VideoFilterRequest) -> Result[CottList[MediaItem], MediaError]:
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    request = _cott_validate_abi(request, VideoFilterRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/filter_video.py", "a4175aa62741bdd847bd6ce2ee80ed9b2a20f704964b5e2c60d6b2eaa1a53922", "filter_video", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.filter_video")
        _result = _implementation(items, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.filter_video"
        if _error.span is None:
            _error.span = {"end_byte":18077,"end_column":1,"end_line":627,"start_byte":17844,"start_column":1,"start_line":617}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.filter_video", phase="implementation-call", span={"end_byte":18077,"end_column":1,"end_line":627,"start_byte":17844,"start_column":1,"start_line":617}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.filter_video", phase="implementation-call", span={"end_byte":18077,"end_column":1,"end_line":627,"start_byte":17844,"start_column":1,"start_line":617}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.filter_video", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.filter_video", phase="error", span={"end_byte":18077,"end_column":1,"end_line":627,"start_byte":17844,"start_column":1,"start_line":617}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.filter_video", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.filter_video", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.filter_video", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return (_cott_contract_condition(((len(selected) <= len(items))), "real.yt_dlp.filter_video", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.filter_video", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.filter_video", clause="ensures:0", phase="ensures", span={"end_byte":18024,"end_column":61,"end_line":621,"start_byte":17968,"start_column":5,"start_line":621}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[MediaItem], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def filter_formats(formats: CottList[FormatDescriptor], request: FormatRequest) -> Result[CottList[FormatDescriptor], MediaError]:
    formats = _cott_validate_abi(formats, CottList[FormatDescriptor], path="$.formats")
    request = _cott_validate_abi(request, FormatRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/filter_formats.py", "131e478259cd38f291ed163df9adf0f6448dc1f5d76197f425e828fd6d653742", "filter_formats", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.filter_formats")
        _result = _implementation(formats, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.filter_formats"
        if _error.span is None:
            _error.span = {"end_byte":18364,"end_column":1,"end_line":638,"start_byte":18077,"start_column":1,"start_line":627}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.filter_formats", phase="implementation-call", span={"end_byte":18364,"end_column":1,"end_line":638,"start_byte":18077,"start_column":1,"start_line":627}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.filter_formats", phase="implementation-call", span={"end_byte":18364,"end_column":1,"end_line":638,"start_byte":18077,"start_column":1,"start_line":627}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[FormatDescriptor], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.filter_formats", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_FormatUnavailable, MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.filter_formats", phase="error", span={"end_byte":18364,"end_column":1,"end_line":638,"start_byte":18077,"start_column":1,"start_line":627}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.filter_formats", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.filter_formats", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_FormatUnavailable:
        _cott_contract_condition(True, "real.yt_dlp.filter_formats", "error:1")
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.filter_formats", "error:2")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return (_cott_contract_condition(((len(selected) <= len(formats))), "real.yt_dlp.filter_formats", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.filter_formats", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.filter_formats", clause="ensures:0", phase="ensures", span={"end_byte":18272,"end_column":63,"end_line":631,"start_byte":18214,"start_column":5,"start_line":631}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[FormatDescriptor], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def sort_formats(formats: CottList[FormatDescriptor], fields: CottList[str]) -> CottList[FormatDescriptor]:
    formats = _cott_validate_abi(formats, CottList[FormatDescriptor], path="$.formats")
    fields = _cott_validate_abi(fields, CottList[str], path="$.fields")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/sort_formats.py", "bd657a95994de74357d3bf618ce3b8a27330d42c600442d1ab913bdfa535cff5", "sort_formats", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.sort_formats")
        _result = _implementation(formats, fields)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.sort_formats"
        if _error.span is None:
            _error.span = {"end_byte":18514,"end_column":1,"end_line":643,"start_byte":18364,"start_column":1,"start_line":638}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.sort_formats", phase="implementation-call", span={"end_byte":18514,"end_column":1,"end_line":643,"start_byte":18364,"start_column":1,"start_line":638}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.sort_formats", phase="implementation-call", span={"end_byte":18514,"end_column":1,"end_line":643,"start_byte":18364,"start_column":1,"start_line":638}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[FormatDescriptor], path="$.return")
    if not (_cott_contract_condition(((len(_result) == len(formats))), "real.yt_dlp.sort_formats", "ensures:0")):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.sort_formats", clause="ensures:0", phase="ensures", span={"end_byte":18496,"end_column":38,"end_line":639,"start_byte":18463,"start_column":5,"start_line":639}, expected="true", actual="false")
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
        _implementation = _cott_load("_cott_impl/real/yt_dlp/select_subtitles.py", "33f0ebab39f0efb42a0f3e301e85df2a13953bbd062b800dcde51f234a68817a", "select_subtitles", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.select_subtitles")
        _result = _implementation(item, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.select_subtitles"
        if _error.span is None:
            _error.span = {"end_byte":18837,"end_column":1,"end_line":654,"start_byte":18514,"start_column":1,"start_line":643}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.select_subtitles", phase="implementation-call", span={"end_byte":18837,"end_column":1,"end_line":654,"start_byte":18514,"start_column":1,"start_line":643}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.select_subtitles", phase="implementation-call", span={"end_byte":18837,"end_column":1,"end_line":654,"start_byte":18514,"start_column":1,"start_line":643}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.select_subtitles", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_SubtitleUnavailable,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.select_subtitles", phase="error", span={"end_byte":18837,"end_column":1,"end_line":654,"start_byte":18514,"start_column":1,"start_line":643}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.select_subtitles", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.select_subtitles", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_SubtitleUnavailable:
        _cott_contract_condition(True, "real.yt_dlp.select_subtitles", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            subtitles = _cott_match_value.value
            return (_cott_contract_condition(((len(subtitles) <= 100000)), "real.yt_dlp.select_subtitles", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.select_subtitles", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.select_subtitles", clause="ensures:1", phase="ensures", span={"end_byte":18770,"end_column":60,"end_line":648,"start_byte":18715,"start_column":5,"start_line":648}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def plan_thumbnails(item: MediaItem, request: ThumbnailRequest) -> CottList[str]:
    """Return symbolic output names, not URLs or CLI options. When write is true and
formats is empty, append item.id + ".thumbnail". When write is true and formats
is nonempty, append item.id + "." + format for each nonempty format in order.
Independently, a nonempty convert_format appends item.id + "." + convert_format,
even when write is false. Finally embed appends "embed:" + item.id.
Preserve duplicates. No other MediaItem field affects these names."""
    item = _cott_validate_abi(item, MediaItem, path="$.item")
    request = _cott_validate_abi(request, ThumbnailRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/plan_thumbnails.py", "9c1a8cfffd569c306703cd7576ca71f1a34f374d2d58189903c7509a4ec6123e", "plan_thumbnails", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.plan_thumbnails")
        _result = _implementation(item, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.plan_thumbnails"
        if _error.span is None:
            _error.span = {"end_byte":19427,"end_column":1,"end_line":666,"start_byte":18837,"start_column":1,"start_line":654}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_thumbnails", phase="implementation-call", span={"end_byte":19427,"end_column":1,"end_line":666,"start_byte":18837,"start_column":1,"start_line":654}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_thumbnails", phase="implementation-call", span={"end_byte":19427,"end_column":1,"end_line":666,"start_byte":18837,"start_column":1,"start_line":654}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=_cott_validate_abi)
    return _result

def plan_metadata(item: MediaItem, request: MetadataRequest) -> CottList[str]:
    """Return symbolic output names in this flag order: write_info_json appends
item.id + ".info.json"; write_description appends item.id + ".description";
write_comments appends item.id + ".comments.json"; write_playlist_metadata
appends item.id + ".playlist.json"; embed appends "embed:" + item.id.
False flags add nothing. No other MediaItem field changes this pure plan."""
    item = _cott_validate_abi(item, MediaItem, path="$.item")
    request = _cott_validate_abi(request, MetadataRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/plan_metadata.py", "f008bdf56d383734f9a9de74ad3dfb049c9d55e3eec919c235419b0f1be7ae4a", "plan_metadata", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.plan_metadata")
        _result = _implementation(item, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.plan_metadata"
        if _error.span is None:
            _error.span = {"end_byte":19926,"end_column":1,"end_line":677,"start_byte":19427,"start_column":1,"start_line":666}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_metadata", phase="implementation-call", span={"end_byte":19926,"end_column":1,"end_line":677,"start_byte":19427,"start_column":1,"start_line":666}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_metadata", phase="implementation-call", span={"end_byte":19926,"end_column":1,"end_line":677,"start_byte":19427,"start_column":1,"start_line":666}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
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
        _implementation = _cott_load("_cott_impl/real/yt_dlp/render_output_path.py", "6b356d3321f7640a205e5ed461e1e43348a77d5aa1319f0d817b5851bbeab99d", "render_output_path", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.render_output_path")
        _result = _implementation(item, template, missing_placeholder)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.render_output_path"
        if _error.span is None:
            _error.span = {"end_byte":20241,"end_column":1,"end_line":688,"start_byte":19926,"start_column":1,"start_line":677}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.render_output_path", phase="implementation-call", span={"end_byte":20241,"end_column":1,"end_line":688,"start_byte":19926,"start_column":1,"start_line":677}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.render_output_path", phase="implementation-call", span={"end_byte":20241,"end_column":1,"end_line":688,"start_byte":19926,"start_column":1,"start_line":677}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.render_output_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidTemplate,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.render_output_path", phase="error", span={"end_byte":20241,"end_column":1,"end_line":688,"start_byte":19926,"start_column":1,"start_line":677}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.render_output_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.render_output_path", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidTemplate:
        _cott_contract_condition(True, "real.yt_dlp.render_output_path", "error:1")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            path = _cott_match_value.value
            return (_cott_contract_condition(((len(path) <= (len(template) * ((((len((item).id) + len((item).title)) + len((item).ext)) + len(missing_placeholder)) + 20)))), "real.yt_dlp.render_output_path", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.render_output_path", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.render_output_path", clause="ensures:0", phase="ensures", span={"end_byte":20185,"end_column":137,"end_line":682,"start_byte":20053,"start_column":5,"start_line":682}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_output_path(item: MediaItem, request: OutputRequest) -> Result[Path, MediaError]:
    """Call real.yt_dlp.render_output_path(item, request.template,
request.missing_placeholder) and propagate its InvalidTemplate unchanged.
The resulting string is a path, not a URL. Split it on "/" and sanitize each
ordinary component, leaving empty, "." and ".." components unchanged.
restrict_filenames replaces every character except ASCII letters/digits and
".", "_" and "-" with "_". windows_filenames also replaces ASCII controls
and < > : double-quote backslash | ? * with "_", replaces trailing spaces/dots
with "_", and prefixes "_" when the case-insensitive stem before the first
dot is CON, PRN, AUX, NUL, COM1..COM9 or LPT1..LPT9.
Reject an empty/NUL-containing path or a path without a filename as PathFailure.
trim_filename_bytes zero means no limit; otherwise trim only the final name
to that many UTF-8 bytes without splitting a code point. Preserve the last
extension when it fits while leaving a nonempty stem; otherwise trim the entire
filename. An empty trimmed filename is PathFailure.
An absolute rendered path stays absolute. A relative path is joined beneath
request.output unless it is Path("."), otherwise beneath request.home.
Parent components are not a confinement check; this pure function does no
filesystem lookup, symlink resolution or directory creation. Reject a final
path equal to request.temp. PathFailure carries the offending computed path
and a fixed descriptive message, not raw exception text."""
    item = _cott_validate_abi(item, MediaItem, path="$.item")
    request = _cott_validate_abi(request, OutputRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/resolve_output_path.py", "2d19c0f90e6ed62bd2418f29e6e960414d0f8167a72937cfbcc2311b8f0075c5", "resolve_output_path", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.resolve_output_path")
        _result = _implementation(item, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.resolve_output_path"
        if _error.span is None:
            _error.span = {"end_byte":22007,"end_column":1,"end_line":719,"start_byte":20241,"start_column":1,"start_line":688}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.resolve_output_path", phase="implementation-call", span={"end_byte":22007,"end_column":1,"end_line":719,"start_byte":20241,"start_column":1,"start_line":688}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.resolve_output_path", phase="implementation-call", span={"end_byte":22007,"end_column":1,"end_line":719,"start_byte":20241,"start_column":1,"start_line":688}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Path, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.resolve_output_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidTemplate, MediaError_PathFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.resolve_output_path", phase="error", span={"end_byte":22007,"end_column":1,"end_line":719,"start_byte":20241,"start_column":1,"start_line":688}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.resolve_output_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.resolve_output_path", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidTemplate:
        _cott_contract_condition(True, "real.yt_dlp.resolve_output_path", "error:2")
    if type(_result) is Err and type(_result.error) is MediaError_PathFailure:
        _cott_contract_condition(True, "real.yt_dlp.resolve_output_path", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            path = _cott_match_value.value
            return (_cott_contract_condition(((path != (request).temp)), "real.yt_dlp.resolve_output_path", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.resolve_output_path", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_output_path", clause="ensures:1", phase="ensures", span={"end_byte":21918,"end_column":52,"end_line":712,"start_byte":21871,"start_column":5,"start_line":712}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Path, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def read_download_archive(request: ArchiveRequest) -> Result[CottList[str], MediaError]:
    """This client's archive contains plain media ids, one UTF-8 line per entry,
not upstream yt-dlp's extractor-key-plus-id format. Read request.path with
UTF-8-sig decoding, split lines, strip surrounding whitespace and ignore empty
lines. Preserve nonempty line order and duplicates. Reject more than 100000
entries and files exceeding 16 MiB rather than truncating.
Missing/nonregular/symlink files, decoding and actual I/O errors return
ArchiveFailure(path=request.path, message=a fixed descriptive category).
break_on_existing and force_write_archive affect the caller's execution policy,
not this reader. No extractor key is invented and no content is executed."""
    request = _cott_validate_abi(request, ArchiveRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/read_download_archive.py", "2da66b5985a258fe084c279ee01fac35a339004006638d2342143fdd49229c0b", "read_download_archive", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.read_download_archive")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.read_download_archive"
        if _error.span is None:
            _error.span = {"end_byte":22929,"end_column":1,"end_line":738,"start_byte":22007,"start_column":1,"start_line":719}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.read_download_archive", phase="implementation-call", span={"end_byte":22929,"end_column":1,"end_line":738,"start_byte":22007,"start_column":1,"start_line":719}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.read_download_archive", phase="implementation-call", span={"end_byte":22929,"end_column":1,"end_line":738,"start_byte":22007,"start_column":1,"start_line":719}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.read_download_archive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_ArchiveFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.read_download_archive", phase="error", span={"end_byte":22929,"end_column":1,"end_line":738,"start_byte":22007,"start_column":1,"start_line":719}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.read_download_archive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.read_download_archive", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_ArchiveFailure:
        _cott_contract_condition(True, "real.yt_dlp.read_download_archive", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            entries = _cott_match_value.value
            return (_cott_contract_condition(((len(entries) <= 100000)), "real.yt_dlp.read_download_archive", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.read_download_archive", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.read_download_archive", clause="ensures:1", phase="ensures", span={"end_byte":22865,"end_column":56,"end_line":732,"start_byte":22814,"start_column":5,"start_line":732}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def plan_downloads(items: CottList[MediaItem], archive: CottList[str], break_on_existing: bool) -> DownloadPlan:
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    archive = _cott_validate_abi(archive, CottList[str], path="$.archive")
    break_on_existing = _cott_validate_abi(break_on_existing, bool, path="$.break_on_existing")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/plan_downloads.py", "02a08f0811d78e2108f9774e4f08d390dd60148f8554f7c590b5ee1226eb496d", "plan_downloads", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.plan_downloads")
        _result = _implementation(items, archive, break_on_existing)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.plan_downloads"
        if _error.span is None:
            _error.span = {"end_byte":23064,"end_column":1,"end_line":745,"start_byte":22929,"start_column":1,"start_line":738}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_downloads", phase="implementation-call", span={"end_byte":23064,"end_column":1,"end_line":745,"start_byte":22929,"start_column":1,"start_line":738}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_downloads", phase="implementation-call", span={"end_byte":23064,"end_column":1,"end_line":745,"start_byte":22929,"start_column":1,"start_line":738}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, DownloadPlan, path="$.return")
    _result = _cott_wrap_async_protocol(_result, DownloadPlan, path="$.return", validator=_cott_validate_abi)
    return _result

def write_download_archive(path: Path, items: CottList[MediaItem]) -> Result[Unit, MediaError]:
    """Atomically replace the complete archive with plain MediaItem.id values, not
upstream extractor-key/id pairs. Preserve input order and duplicates; do not
read or merge a prior archive. Reject more than 100000 items and ids that are
empty, have surrounding whitespace, or contain CR/LF. No other item field
contributes to the archive. Encode UTF-8 without BOM with one LF after each
id; empty input writes an empty file. Reject output exceeding 16 MiB.
Validate before publication. Refuse symlink path components and nonregular
existing leaves using descriptor-relative no-follow traversal; do not create
parent directories. Write an exclusive same-directory temporary file with
mode 0600, flush/fsync it, atomically replace the target and fsync the parent.
Clean up temporary files and preserve the prior target on precommit failure.
Map validation, path, encoding, unsupported safety primitives and genuine I/O
failures to ArchiveFailure(path=path, message=a fixed descriptive category).
Never emit a partial archive or infer an extractor from the URL."""
    path = _cott_validate_abi(path, Path, path="$.path")
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/write_download_archive.py", "388ab8c1a23aa2764b8563e8483032cd3b537c339245129ed9f472ce855448fb", "write_download_archive", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.write_download_archive")
        _result = _implementation(path, items)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.write_download_archive"
        if _error.span is None:
            _error.span = {"end_byte":24393,"end_column":1,"end_line":769,"start_byte":23064,"start_column":1,"start_line":745}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.write_download_archive", phase="implementation-call", span={"end_byte":24393,"end_column":1,"end_line":769,"start_byte":23064,"start_column":1,"start_line":745}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.write_download_archive", phase="implementation-call", span={"end_byte":24393,"end_column":1,"end_line":769,"start_byte":23064,"start_column":1,"start_line":745}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.write_download_archive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_ArchiveFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.write_download_archive", phase="error", span={"end_byte":24393,"end_column":1,"end_line":769,"start_byte":23064,"start_column":1,"start_line":745}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.write_download_archive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.write_download_archive", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_ArchiveFailure:
        _cott_contract_condition(True, "real.yt_dlp.write_download_archive", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            saved = _cott_match_value.value
            return (_cott_contract_condition(((saved == UNIT)), "real.yt_dlp.write_download_archive", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.write_download_archive", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.write_download_archive", clause="ensures:1", phase="ensures", span={"end_byte":24328,"end_column":44,"end_line":763,"start_byte":24289,"start_column":5,"start_line":763}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def plan_fragments(request: TransferRequest, policy: FragmentPolicy) -> Result[CottList[TransferRequest], MediaError]:
    request = _cott_validate_abi(request, TransferRequest, path="$.request")
    policy = _cott_validate_abi(policy, FragmentPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/plan_fragments.py", "dfc0c44d66d7e2e68d9f20cc9c563ed86766220df16f00b6677f6b1def8b6692", "plan_fragments", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.plan_fragments")
        _result = _implementation(request, policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.plan_fragments"
        if _error.span is None:
            _error.span = {"end_byte":24661,"end_column":1,"end_line":780,"start_byte":24393,"start_column":1,"start_line":769}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_fragments", phase="implementation-call", span={"end_byte":24661,"end_column":1,"end_line":780,"start_byte":24393,"start_column":1,"start_line":769}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_fragments", phase="implementation-call", span={"end_byte":24661,"end_column":1,"end_line":780,"start_byte":24393,"start_column":1,"start_line":769}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[TransferRequest], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.plan_fragments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput, MediaError_SizeLimit,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.plan_fragments", phase="error", span={"end_byte":24661,"end_column":1,"end_line":780,"start_byte":24393,"start_column":1,"start_line":769}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.plan_fragments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.plan_fragments", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.plan_fragments", "error:1")
    if type(_result) is Err and type(_result.error) is MediaError_SizeLimit:
        _cott_contract_condition(True, "real.yt_dlp.plan_fragments", "error:2")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            fragments = _cott_match_value.value
            return (_cott_contract_condition(((len(fragments) <= 100000)), "real.yt_dlp.plan_fragments", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.plan_fragments", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.plan_fragments", clause="ensures:0", phase="ensures", span={"end_byte":24577,"end_column":60,"end_line":773,"start_byte":24522,"start_column":5,"start_line":773}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[TransferRequest], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def transfer_media(request: TransferRequest) -> Result[TransferReceipt, MediaError]:
    request = _cott_validate_abi(request, TransferRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((request).max_bytes == 0)), "real.yt_dlp.transfer_media", "error:4:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":25094,"end_column":62,"end_line":786,"start_byte":25037,"start_column":5,"start_line":786}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/transfer_media.py", "9308b8abd06b07860f5d1528b35647528ab2f40a059e750aad317cde5974b642", "transfer_media", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.transfer_media")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.transfer_media"
        if _error.span is None:
            _error.span = {"end_byte":25301,"end_column":1,"end_line":795,"start_byte":24661,"start_column":1,"start_line":780}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.transfer_media", phase="implementation-call", span={"end_byte":25301,"end_column":1,"end_line":795,"start_byte":24661,"start_column":1,"start_line":780}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.transfer_media", phase="implementation-call", span={"end_byte":25301,"end_column":1,"end_line":795,"start_byte":24661,"start_column":1,"start_line":780}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransferReceipt, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.transfer_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_UnsupportedUrl, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_SizeLimit,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.transfer_media", phase="error", span={"end_byte":25301,"end_column":1,"end_line":795,"start_byte":24661,"start_column":1,"start_line":780}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.transfer_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.transfer_media", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_UnsupportedUrl:
        _cott_contract_condition(True, "real.yt_dlp.transfer_media", "error:5")
    if type(_result) is Err and type(_result.error) is MediaError_HttpStatus:
        _cott_contract_condition(True, "real.yt_dlp.transfer_media", "error:6")
    if type(_result) is Err and type(_result.error) is MediaError_NetworkFailure:
        _cott_contract_condition(True, "real.yt_dlp.transfer_media", "error:7")
    if type(_result) is Err and type(_result.error) is MediaError_OutputFailure:
        _cott_contract_condition(True, "real.yt_dlp.transfer_media", "error:8")
    if type(_result) is Err and type(_result.error) is MediaError_SizeLimit:
        _cott_contract_condition(True, "real.yt_dlp.transfer_media", "error:9")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (_cott_contract_condition((((receipt).url == (request).url)), "real.yt_dlp.transfer_media", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.transfer_media", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:0", phase="ensures", span={"end_byte":24805,"end_column":61,"end_line":781,"start_byte":24749,"start_column":5,"start_line":781}, expected="true", actual="false")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (_cott_contract_condition((((receipt).destination == (request).destination)), "real.yt_dlp.transfer_media", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.transfer_media", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:1", phase="ensures", span={"end_byte":24882,"end_column":77,"end_line":782,"start_byte":24810,"start_column":5,"start_line":782}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (_cott_contract_condition((((receipt).bytes_written <= (request).max_bytes)), "real.yt_dlp.transfer_media", "ensures:2"))
        _cott_contract_condition((False), "real.yt_dlp.transfer_media", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:2", phase="ensures", span={"end_byte":24959,"end_column":77,"end_line":783,"start_byte":24887,"start_column":5,"start_line":783}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (_cott_contract_condition((((receipt).simulated == (request).simulate)), "real.yt_dlp.transfer_media", "ensures:3"))
        _cott_contract_condition((False), "real.yt_dlp.transfer_media", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:3", phase="ensures", span={"end_byte":25031,"end_column":72,"end_line":784,"start_byte":24964,"start_column":5,"start_line":784}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransferReceipt, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def transfer_fragments(fragments: CottList[TransferRequest], policy: FragmentPolicy) -> Result[CottList[TransferReceipt], MediaError]:
    fragments = _cott_validate_abi(fragments, CottList[TransferRequest], path="$.fragments")
    policy = _cott_validate_abi(policy, FragmentPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/transfer_fragments.py", "835dbe026ce37caa94bc72febdbfd21703bede22db1b45337d390793e148f43f", "transfer_fragments", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.transfer_fragments")
        _result = _implementation(fragments, policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.transfer_fragments"
        if _error.span is None:
            _error.span = {"end_byte":25751,"end_column":1,"end_line":810,"start_byte":25301,"start_column":1,"start_line":795}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.transfer_fragments", phase="implementation-call", span={"end_byte":25751,"end_column":1,"end_line":810,"start_byte":25301,"start_column":1,"start_line":795}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.transfer_fragments", phase="implementation-call", span={"end_byte":25751,"end_column":1,"end_line":810,"start_byte":25301,"start_column":1,"start_line":795}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[TransferReceipt], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.transfer_fragments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_RetryExhausted, MediaError_SizeLimit,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.transfer_fragments", phase="error", span={"end_byte":25751,"end_column":1,"end_line":810,"start_byte":25301,"start_column":1,"start_line":795}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.transfer_fragments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.transfer_fragments", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.transfer_fragments", "error:1")
    if type(_result) is Err and type(_result.error) is MediaError_HttpStatus:
        _cott_contract_condition(True, "real.yt_dlp.transfer_fragments", "error:2")
    if type(_result) is Err and type(_result.error) is MediaError_NetworkFailure:
        _cott_contract_condition(True, "real.yt_dlp.transfer_fragments", "error:3")
    if type(_result) is Err and type(_result.error) is MediaError_OutputFailure:
        _cott_contract_condition(True, "real.yt_dlp.transfer_fragments", "error:4")
    if type(_result) is Err and type(_result.error) is MediaError_RetryExhausted:
        _cott_contract_condition(True, "real.yt_dlp.transfer_fragments", "error:5")
    if type(_result) is Err and type(_result.error) is MediaError_SizeLimit:
        _cott_contract_condition(True, "real.yt_dlp.transfer_fragments", "error:6")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipts = _cott_match_value.value
            return (_cott_contract_condition(((len(receipts) == len(fragments))), "real.yt_dlp.transfer_fragments", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.transfer_fragments", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_fragments", clause="ensures:0", phase="ensures", span={"end_byte":25502,"end_column":65,"end_line":799,"start_byte":25442,"start_column":5,"start_line":799}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[TransferReceipt], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def render_items(items: CottList[MediaItem], mode: JsonMode) -> str:
    """Serialize each MediaItem as a JSON object whose keys occur in exactly this
order: url, id, title, ext, playlist_index, with their stored values unchanged.
Use ensure_ascii=False and compact separators (",", ":"). Lines joins the
objects with a single newline and no trailing newline; empty input is "".
Single returns one compact JSON array in item order; empty input is "[]".
Do not invent a playlist envelope, rename keys, or sort/deduplicate items."""
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    mode = _cott_validate_abi(mode, JsonMode, path="$.mode")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/render_items.py", "f71f05ff14275de9176a13b2aa82cd18fee1cecbaefcacfd65d0d0573e68a082", "render_items", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.render_items")
        _result = _implementation(items, mode)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.render_items"
        if _error.span is None:
            _error.span = {"end_byte":26328,"end_column":1,"end_line":822,"start_byte":25751,"start_column":1,"start_line":810}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.render_items", phase="implementation-call", span={"end_byte":26328,"end_column":1,"end_line":822,"start_byte":25751,"start_column":1,"start_line":810}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.render_items", phase="implementation-call", span={"end_byte":26328,"end_column":1,"end_line":822,"start_byte":25751,"start_column":1,"start_line":810}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def plan_post_processing(item: MediaItem, request: PostProcessRequest) -> Result[CottList[ExternalToolRequest], MediaError]:
    """Empty kinds returns an empty success without inspecting external_tool.
Otherwise external_tool is required: Nothing returns ExternalToolMissing("ffmpeg").
An empty executable returns ExternalToolMissing(name=the empty executable).
input or output equal to Path(".") and timeout_ms zero are InvalidInput.
This is a pure plan for an explicitly supplied command-protocol adapter, not
raw ffmpeg argv: no executable lookup, subprocess or filesystem work occurs.
Preserve kind order and duplicates. Produce exactly one request per kind,
retaining the supplied tool's executable, input, output and timeout_ms, and
appending these protocol arguments to a copy of its arguments:
ExtractAudio: ["extract-audio", audio_format], requiring nonempty audio_format.
RemuxVideo: ["remux-video", video_format], requiring nonempty video_format.
RecodeVideo: ["recode-video", video_format], requiring nonempty video_format.
EmbedSubtitle: ["embed-subtitle"]. EmbedThumbnail: ["embed-thumbnail"].
EmbedMetadata: ["embed-metadata"]. SplitChapters: ["split-chapters"].
ConvertThumbnails: ["convert-thumbnails", video_format], requiring nonempty video_format.
SponsorBlock: ["sponsorblock", comma-joined sponsorblock_categories], requiring
a nonempty list with no empty category. Fixup: ["fixup"].
Missing required format/categories returns InvalidInput with a descriptive
fixed message and no partial plan. item does not affect this protocol plan:
the explicit external tool request already supplies the input and output."""
    item = _cott_validate_abi(item, MediaItem, path="$.item")
    request = _cott_validate_abi(request, PostProcessRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/plan_post_processing.py", "e7bd91c1cc78932910c8dd533e2b1b3a845621e6b57c890c3a9045cc267ba3ce", "plan_post_processing", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.plan_post_processing")
        _result = _implementation(item, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.plan_post_processing"
        if _error.span is None:
            _error.span = {"end_byte":28220,"end_column":1,"end_line":856,"start_byte":26328,"start_column":1,"start_line":822}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_post_processing", phase="implementation-call", span={"end_byte":28220,"end_column":1,"end_line":856,"start_byte":26328,"start_column":1,"start_line":822}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_post_processing", phase="implementation-call", span={"end_byte":28220,"end_column":1,"end_line":856,"start_byte":26328,"start_column":1,"start_line":822}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[ExternalToolRequest], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.plan_post_processing", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_ExternalToolMissing, MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.plan_post_processing", phase="error", span={"end_byte":28220,"end_column":1,"end_line":856,"start_byte":26328,"start_column":1,"start_line":822}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.plan_post_processing", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.plan_post_processing", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_ExternalToolMissing:
        _cott_contract_condition(True, "real.yt_dlp.plan_post_processing", "error:2")
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.plan_post_processing", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            planned = _cott_match_value.value
            return (_cott_contract_condition(((len(planned) <= len((request).kinds))), "real.yt_dlp.plan_post_processing", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.plan_post_processing", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.plan_post_processing", clause="ensures:1", phase="ensures", span={"end_byte":28126,"end_column":67,"end_line":849,"start_byte":28064,"start_column":5,"start_line":849}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[ExternalToolRequest], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def run_post_processing(requests: CottList[ExternalToolRequest]) -> Result[Unit, MediaError]:
    requests = _cott_validate_abi(requests, CottList[ExternalToolRequest], path="$.requests")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/run_post_processing.py", "016ac6a5c5c36c2c465e5633e52adb6677548cd8beb117270983f957d955239f", "run_post_processing", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.run_post_processing")
        _result = _implementation(requests)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.run_post_processing"
        if _error.span is None:
            _error.span = {"end_byte":28480,"end_column":1,"end_line":864,"start_byte":28220,"start_column":1,"start_line":856}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.run_post_processing", phase="implementation-call", span={"end_byte":28480,"end_column":1,"end_line":864,"start_byte":28220,"start_column":1,"start_line":856}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.run_post_processing", phase="implementation-call", span={"end_byte":28480,"end_column":1,"end_line":864,"start_byte":28220,"start_column":1,"start_line":856}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.run_post_processing", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_ExternalToolMissing, MediaError_PostProcessFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.run_post_processing", phase="error", span={"end_byte":28480,"end_column":1,"end_line":864,"start_byte":28220,"start_column":1,"start_line":856}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.run_post_processing", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.run_post_processing", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_ExternalToolMissing:
        _cott_contract_condition(True, "real.yt_dlp.run_post_processing", "error:1")
    if type(_result) is Err and type(_result.error) is MediaError_PostProcessFailed:
        _cott_contract_condition(True, "real.yt_dlp.run_post_processing", "error:2")
    def _cott_match_ensures_0() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            completed = _cott_match_value.value
            return (_cott_contract_condition(((completed == UNIT)), "real.yt_dlp.run_post_processing", "ensures:0"))
        _cott_contract_condition((False), "real.yt_dlp.run_post_processing", "ensures:0:applicable")
        return True
    if not (_cott_match_ensures_0()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.run_post_processing", clause="ensures:0", phase="ensures", span={"end_byte":28360,"end_column":52,"end_line":857,"start_byte":28313,"start_column":5,"start_line":857}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_update_repository(policy: UpdatePolicy, channel: str) -> Result[str, MediaError]:
    """Return the empty string for Never without inspecting channel. Nightly returns
`yt-dlp/yt-dlp-nightly-builds` and Master returns
`yt-dlp/yt-dlp-master-builds`, ignoring channel. For Check and Apply, strip
outer whitespace from channel: empty or `stable` maps to `yt-dlp/yt-dlp`,
`nightly` maps to `yt-dlp/yt-dlp-nightly-builds`, and `master` maps to
`yt-dlp/yt-dlp-master-builds`. Matching is case-sensitive. Reject every other
value as UpdateUnavailable; never interpret channel as a repository or URL."""
    policy = _cott_validate_abi(policy, UpdatePolicy, path="$.policy")
    channel = _cott_validate_abi(channel, str, path="$.channel")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/resolve_update_repository.py", "ff241d9ce58219710c95081e7623babde6171abb7eb931f7ce4be3024b5d453f", "resolve_update_repository", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.resolve_update_repository")
        _result = _implementation(policy, channel)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.resolve_update_repository"
        if _error.span is None:
            _error.span = {"end_byte":29366,"end_column":1,"end_line":881,"start_byte":28480,"start_column":1,"start_line":864}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.resolve_update_repository", phase="implementation-call", span={"end_byte":29366,"end_column":1,"end_line":881,"start_byte":28480,"start_column":1,"start_line":864}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.resolve_update_repository", phase="implementation-call", span={"end_byte":29366,"end_column":1,"end_line":881,"start_byte":28480,"start_column":1,"start_line":864}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.resolve_update_repository", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_UpdateUnavailable,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.resolve_update_repository", phase="error", span={"end_byte":29366,"end_column":1,"end_line":881,"start_byte":28480,"start_column":1,"start_line":864}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.resolve_update_repository", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.resolve_update_repository", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_UpdateUnavailable:
        _cott_contract_condition(True, "real.yt_dlp.resolve_update_repository", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            repository = _cott_match_value.value
            return (_cott_contract_condition((((((repository == "") or (repository == "yt-dlp/yt-dlp")) or (repository == "yt-dlp/yt-dlp-nightly-builds")) or (repository == "yt-dlp/yt-dlp-master-builds"))), "real.yt_dlp.resolve_update_repository", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.resolve_update_repository", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_update_repository", clause="ensures:1", phase="ensures", span={"end_byte":29308,"end_column":184,"end_line":875,"start_byte":29129,"start_column":5,"start_line":875}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def apply_update(request: UpdateRequest) -> Result[Unit, MediaError]:
    """Never returns Ok immediately without validating channel or target and without
network or filesystem access: success means updates are disabled, not that an
update was installed. Otherwise call
real.yt_dlp.resolve_update_repository(request.policy, request.channel).

Use only the selected official repository's latest release assets at fixed
HTTPS GitHub release URLs: `SHA2-256SUMS` and the platform-independent
`yt-dlp` zipimport executable documented by upstream. Stable is
yt-dlp/yt-dlp, nightly is yt-dlp/yt-dlp-nightly-builds, and master is
yt-dlp/yt-dlp-master-builds. Do not accept a repository, asset name, tag, or
URL from input. Use certificate- and hostname-verifying TLS, a finite timeout,
at most five redirects, and permit redirects only to github.com or
release-assets.githubusercontent.com over HTTPS. Send no credentials.

Read each response incrementally. Cap SHA2-256SUMS at 1 MiB and the yt-dlp
asset at 64 MiB, rejecting an excessive Content-Length or a cap-plus-one
byte. Reject HTML masquerading as an asset. Parse exactly one GNU-style
SHA-256 entry for filename `yt-dlp`; require exactly 64 hexadecimal digits.
The authenticated HTTPS checksum manifest is mandatory: missing, malformed,
duplicate, or absent checksums are not optional. Never trust or install bytes
until their streaming SHA-256 digest matches that entry.

The target is an explicit leaf. Refuse an empty/root/dot leaf, every symlink
in its path, and an existing non-regular target. Use no-follow, directory-fd
filesystem operations so validation and use are not separated by a symlink
race; if the platform cannot provide those guarantees, fail closed. A missing
target represents an available update. For an existing target, hash it
incrementally without following links; a digest equal to the release checksum
means it is current.

Check performs the authenticated manifest fetch and target comparison above,
then returns Ok whether the target is current or an update is available. It
never downloads the executable, creates a temporary file, changes metadata,
or replaces target; Unit intentionally reports only successful completion of
the read-only check.

Apply, Nightly, and Master return Ok without writing when target already
matches. Otherwise create an unpredictable exclusive no-follow temporary
regular file in target's directory, stream the bounded asset into it while
hashing, verify the digest, flush and fsync it, set its mode, then atomically
replace target within that same directory and fsync the directory. Preserve
an existing target's ordinary rwx permission bits while dropping special
bits; use 0755 for a new target. Recheck the target identity before commit,
clean up the temporary leaf on every pre-commit failure, and never move or
truncate the old target before verified replacement. Do not leave a partial
target or follow a target swapped to a symlink.

Map unknown channels, missing releases/assets or checksum entries, malformed
metadata, forbidden redirects, oversized/HTML payloads, and integrity
failures to UpdateUnavailable. Map DNS, timeout, TLS, connection, and
non-404 HTTP transport failures to NetworkFailure. Map target/path/type,
permission, local read/write, flush, chmod, fsync, race, cleanup, and atomic
replacement failures to OutputFailure. Error messages may identify the
operation, selected channel, HTTP status, and target path, but must never
include response bodies, redirect query strings, authorization material, or
raw exception text that may contain secrets."""
    request = _cott_validate_abi(request, UpdateRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/apply_update.py", "1b253984912be4c56603e1e6b5e8461ca283cdfe81563426114a235234278399", "apply_update", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.apply_update")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.apply_update"
        if _error.span is None:
            _error.span = {"end_byte":33397,"end_column":1,"end_line":949,"start_byte":29366,"start_column":1,"start_line":881}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.apply_update", phase="implementation-call", span={"end_byte":33397,"end_column":1,"end_line":949,"start_byte":29366,"start_column":1,"start_line":881}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.apply_update", phase="implementation-call", span={"end_byte":33397,"end_column":1,"end_line":949,"start_byte":29366,"start_column":1,"start_line":881}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.apply_update", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_UpdateUnavailable, MediaError_NetworkFailure, MediaError_OutputFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.apply_update", phase="error", span={"end_byte":33397,"end_column":1,"end_line":949,"start_byte":29366,"start_column":1,"start_line":881}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.apply_update", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.apply_update", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_UpdateUnavailable:
        _cott_contract_condition(True, "real.yt_dlp.apply_update", "error:2")
    if type(_result) is Err and type(_result.error) is MediaError_NetworkFailure:
        _cott_contract_condition(True, "real.yt_dlp.apply_update", "error:3")
    if type(_result) is Err and type(_result.error) is MediaError_OutputFailure:
        _cott_contract_condition(True, "real.yt_dlp.apply_update", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            updated = _cott_match_value.value
            return (_cott_contract_condition(((updated == UNIT)), "real.yt_dlp.apply_update", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.apply_update", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.apply_update", clause="ensures:1", phase="ensures", span={"end_byte":33238,"end_column":48,"end_line":941,"start_byte":33195,"start_column":5,"start_line":941}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def execute(request: ExecutionRequest) -> Result[ExecutionReport, MediaError]:
    """Execute the direct-media pipeline and return its actual selected items,
download plan and rendered output, never an invented empty success.
Propagate each failing stage's declared MediaError unchanged and stop before
later stages. Do not perform effects outside these stages.

First call real.yt_dlp.apply_update(request.update), then validate_network,
select_geo_route, resolve_authentication and validate_workarounds on their
corresponding request values. Use the returned network and authentication
for extraction. Path(".") in presentation.log_file disables logging;
otherwise call configure_presentation.

Expand input entries in order. Argument contributes its value. ConfigFile
calls load_config(Path(value)); its returned Argument entries contribute
values and BatchFile entries call load_batch_urls with comment prefixes
List("#"). Reject a nested ConfigFile as InvalidInput rather than recursing.
BatchFile calls load_batch_urls directly. Pass the resulting Argument
entries to resolve_inputs with an empty config list. If shortcut.query is
nonempty, append build_shortcut_url(request.shortcut)'s successful value.
Require at least one resulting URL, otherwise return InvalidInput.
Discover descriptors through discover_extractors. For each URL in order
call choose_extractor and extract_media; concatenate their actual items.
Apply select_playlist, then resolve_live_media, then filter_video to these
items using their respective request settings.

Path(".") in archive.path disables archive reading and writing and supplies
an empty archive. Otherwise call read_download_archive; do not turn its
failure into an empty success. Call plan_downloads with the selected items,
archive entries and break_on_existing. Preserve the returned plan unchanged.

Only SimulationMode.Download transfers media. For each planned item in
order, resolve_output_path with request.output, construct TransferRequest
with the item's URL, that path, simulate false and formats.max_file_size,
then call plan_fragments and transfer_fragments using request.fragments.
On successful transfer call plan_post_processing then run_post_processing
when kinds is nonempty. Do not use these symbolic plans as raw ffmpeg argv.
Only after all planned transfers and requested post-processing succeed,
write_download_archive when the archive is enabled and either downloads
occurred or force_write_archive is true. Supply the successfully planned
items; this writer replaces rather than merges an earlier archive.
Simulate, SkipDownload and PrintOnly perform discovery, selection and
planning but no media transfer, post-processing or archive write.

Render the selected items through render_items with request.json_mode,
including when the archive removed every item from the download plan.
Return ExecutionReport(selected=the selected items, downloads=the actual
plan, rendered=that string, simulated=simulation is not Download).
This pipeline uses the existing direct-media descriptor model: it does not
invent format/subtitle/thumbnail discovery or metadata that MediaItem does
not contain. Those independently declared planning APIs are not silently
represented as completed work by this report."""
    request = _cott_validate_abi(request, ExecutionRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/execute.py", "84c0af01c2a001947db17d9584bec0fa94cfb7bd0165b27858be433629f3b931", "execute", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.execute")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.execute"
        if _error.span is None:
            _error.span = {"end_byte":38021,"end_column":1,"end_line":1035,"start_byte":33397,"start_column":1,"start_line":949}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.execute", phase="implementation-call", span={"end_byte":38021,"end_column":1,"end_line":1035,"start_byte":33397,"start_column":1,"start_line":949}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.execute", phase="implementation-call", span={"end_byte":38021,"end_column":1,"end_line":1035,"start_byte":33397,"start_column":1,"start_line":949}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ExecutionReport, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidConfig, MediaError_InvalidInput, MediaError_AuthenticationFailed, MediaError_BatchReadFailed, MediaError_InvalidShortcut, MediaError_CertificateFailure, MediaError_WorkaroundRejected, MediaError_LogFailure, MediaError_InvalidRange, MediaError_CookieFailure, MediaError_GeoRestricted, MediaError_ExtractorMissing, MediaError_PluginRejected, MediaError_UnsupportedUrl, MediaError_FormatUnavailable, MediaError_SubtitleUnavailable, MediaError_InvalidTemplate, MediaError_ArchiveFailure, MediaError_PathFailure, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_SizeLimit, MediaError_RetryExhausted, MediaError_ExternalToolMissing, MediaError_PostProcessFailed, MediaError_UpdateUnavailable,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.execute", phase="error", span={"end_byte":38021,"end_column":1,"end_line":1035,"start_byte":33397,"start_column":1,"start_line":949}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.execute", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidConfig:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:2")
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:3")
    if type(_result) is Err and type(_result.error) is MediaError_AuthenticationFailed:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:4")
    if type(_result) is Err and type(_result.error) is MediaError_BatchReadFailed:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:5")
    if type(_result) is Err and type(_result.error) is MediaError_InvalidShortcut:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:6")
    if type(_result) is Err and type(_result.error) is MediaError_CertificateFailure:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:7")
    if type(_result) is Err and type(_result.error) is MediaError_WorkaroundRejected:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:8")
    if type(_result) is Err and type(_result.error) is MediaError_LogFailure:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:9")
    if type(_result) is Err and type(_result.error) is MediaError_InvalidRange:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:10")
    if type(_result) is Err and type(_result.error) is MediaError_CookieFailure:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:11")
    if type(_result) is Err and type(_result.error) is MediaError_GeoRestricted:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:12")
    if type(_result) is Err and type(_result.error) is MediaError_ExtractorMissing:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:13")
    if type(_result) is Err and type(_result.error) is MediaError_PluginRejected:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:14")
    if type(_result) is Err and type(_result.error) is MediaError_UnsupportedUrl:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:15")
    if type(_result) is Err and type(_result.error) is MediaError_FormatUnavailable:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:16")
    if type(_result) is Err and type(_result.error) is MediaError_SubtitleUnavailable:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:17")
    if type(_result) is Err and type(_result.error) is MediaError_InvalidTemplate:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:18")
    if type(_result) is Err and type(_result.error) is MediaError_ArchiveFailure:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:19")
    if type(_result) is Err and type(_result.error) is MediaError_PathFailure:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:20")
    if type(_result) is Err and type(_result.error) is MediaError_HttpStatus:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:21")
    if type(_result) is Err and type(_result.error) is MediaError_NetworkFailure:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:22")
    if type(_result) is Err and type(_result.error) is MediaError_OutputFailure:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:23")
    if type(_result) is Err and type(_result.error) is MediaError_SizeLimit:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:24")
    if type(_result) is Err and type(_result.error) is MediaError_RetryExhausted:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:25")
    if type(_result) is Err and type(_result.error) is MediaError_ExternalToolMissing:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:26")
    if type(_result) is Err and type(_result.error) is MediaError_PostProcessFailed:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:27")
    if type(_result) is Err and type(_result.error) is MediaError_UpdateUnavailable:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:28")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            report = _cott_match_value.value
            return (_cott_contract_condition((((report).simulated == ((request).simulation != SimulationMode_Download()))), "real.yt_dlp.execute", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.execute", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.execute", clause="ensures:1", phase="ensures", span={"end_byte":36971,"end_column":101,"end_line":1003,"start_byte":36875,"start_column":5,"start_line":1003}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ExecutionReport, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def run(arguments: CottList[str]) -> Never:
    """arguments excludes argv[0]. Call real.yt_dlp.parse_arguments, then
real.yt_dlp.execute with an ExecutionRequest whose inputs are the parsed values.
Every list starts empty, string "", integer 0, boolean false, optional value
Nothing, and Path "." unless an override below states otherwise.
Enum choices are: network proxy Direct and geo Default; authentication
Anonymous; playlist Playlist; live Default; shortcut Url; subtitles None;
simulation Download; json_mode Lines; update Never; presentation Info;
workarounds certificate Verify. There are no other inferred CLI defaults.
Override network.socket_timeout_ms=30000; live.concurrent_fragments=1;
video_filter.include_ads=true; shortcut.limit=1;
formats.max_file_size=104857600; output.template="%(title)s.%(ext)s";
output.temp=Path(".tmp"); output.missing_placeholder="NA";
fragments.concurrent_fragments=1, buffer_size=65536, chunk_size=104857600,
retries=3, fragment_retries=3, file_access_retries=3, continue_download=true,
part_files=true; presentation.progress=true and presentation.color=true.
On a parsing or execution Err, write a fixed nonsecret "media operation failed"
message to stderr and exit 1 without subsequent stages. On success, write the
report's rendered string plus one newline only when it is nonempty, then exit 0.
Do not run updater or download code outside the declared execute pipeline, and
do not expand the argument grammar beyond the parse_arguments contract."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/run.py", "78dd4ae6ad76cd511d984667ce21081a916c3020a395408f1f68eaf9b33e17f4", "run", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.run")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.run"
        if _error.span is None:
            _error.span = {"end_byte":39681,"end_column":1,"end_line":1061,"start_byte":38021,"start_column":1,"start_line":1035}
        raise
    except SystemExit:
        raise
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.run", phase="implementation-call", span={"end_byte":39681,"end_column":1,"end_line":1061,"start_byte":38021,"start_column":1,"start_line":1035}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    raise CottContractViolation("Never function returned", symbol="real.yt_dlp.run", phase="return", span={"end_byte":39681,"end_column":1,"end_line":1061,"start_byte":38021,"start_column":1,"start_line":1035}, expected="Never", actual=repr(_result))

__all__ = ["ArchiveRequest", "Authentication", "AuthenticationKind", "AuthenticationKind_Anonymous", "AuthenticationKind_BrowserCookies", "AuthenticationKind_Cookies", "AuthenticationKind_Credentials", "AuthenticationKind_Netrc", "CertificatePolicy", "CertificatePolicy_Insecure", "CertificatePolicy_Verify", "CliInput", "DownloadPlan", "ExecutionReport", "ExecutionRequest", "ExternalToolRequest", "ExtractorDescriptor", "ExtractorWorkaround", "ExtractorWorkaround_ForceGeneric", "ExtractorWorkaround_LegacyServerConnect", "ExtractorWorkaround_NoCheckCertificates", "ExtractorWorkaround_NoPlaylist", "FormatContainer", "FormatContainer_Any", "FormatContainer_Audio", "FormatContainer_Best", "FormatContainer_Video", "FormatContainer_Worst", "FormatDescriptor", "FormatRequest", "FragmentPolicy", "GeoBypassMode", "GeoBypassMode_Country", "GeoBypassMode_Default", "GeoBypassMode_Disabled", "GeoBypassMode_IpBlock", "InputKind", "InputKind_Argument", "InputKind_BatchFile", "InputKind_ConfigFile", "JsonMode", "JsonMode_Lines", "JsonMode_Single", "LiveMode", "LiveMode_Default", "LiveMode_FromStart", "LiveMode_Wait", "LiveRequest", "LogLevel", "LogLevel_Debug", "LogLevel_Info", "LogLevel_Quiet", "LogLevel_Warning", "MediaError", "MediaError_ArchiveFailure", "MediaError_AuthenticationFailed", "MediaError_BatchReadFailed", "MediaError_CertificateFailure", "MediaError_CookieFailure", "MediaError_ExternalToolMissing", "MediaError_ExtractorMissing", "MediaError_FormatUnavailable", "MediaError_GeoRestricted", "MediaError_HttpStatus", "MediaError_InvalidConfig", "MediaError_InvalidInput", "MediaError_InvalidRange", "MediaError_InvalidShortcut", "MediaError_InvalidTemplate", "MediaError_LogFailure", "MediaError_NetworkFailure", "MediaError_OutputFailure", "MediaError_PathFailure", "MediaError_PluginRejected", "MediaError_PostProcessFailed", "MediaError_RetryExhausted", "MediaError_SizeLimit", "MediaError_SubtitleUnavailable", "MediaError_UnsupportedUrl", "MediaError_UpdateUnavailable", "MediaError_WorkaroundRejected", "MediaItem", "MetadataRequest", "NetworkPolicy", "OutputRequest", "PlaylistMode", "PlaylistMode_Flat", "PlaylistMode_Playlist", "PlaylistMode_Random", "PlaylistMode_Reverse", "PlaylistMode_Single", "PlaylistRange", "PlaylistRequest", "PluginDescriptor", "PostProcessRequest", "PostProcessorKind", "PostProcessorKind_ConvertThumbnails", "PostProcessorKind_EmbedMetadata", "PostProcessorKind_EmbedSubtitle", "PostProcessorKind_EmbedThumbnail", "PostProcessorKind_ExtractAudio", "PostProcessorKind_Fixup", "PostProcessorKind_RecodeVideo", "PostProcessorKind_RemuxVideo", "PostProcessorKind_SplitChapters", "PostProcessorKind_SponsorBlock", "PresentationRequest", "ProxyMode", "ProxyMode_Direct", "ProxyMode_Http", "ProxyMode_Socks", "ShortcutKind", "ShortcutKind_Search", "ShortcutKind_SearchAll", "ShortcutKind_Url", "ShortcutRequest", "SimulationMode", "SimulationMode_Download", "SimulationMode_PrintOnly", "SimulationMode_Simulate", "SimulationMode_SkipDownload", "SubtitleMode", "SubtitleMode_All", "SubtitleMode_Automatic", "SubtitleMode_Manual", "SubtitleMode_None", "SubtitleRequest", "ThumbnailRequest", "TransferReceipt", "TransferRequest", "UpdatePolicy", "UpdatePolicy_Apply", "UpdatePolicy_Check", "UpdatePolicy_Master", "UpdatePolicy_Never", "UpdatePolicy_Nightly", "UpdateRequest", "VideoFilterRequest", "WorkaroundPolicy", "apply_update", "build_shortcut_url", "choose_extractor", "configure_presentation", "discover_extractors", "execute", "expand_playlist_ranges", "extract_media", "filter_formats", "filter_video", "load_batch_urls", "load_config", "load_plugins", "parse_arguments", "parse_batch_urls", "plan_downloads", "plan_fragments", "plan_metadata", "plan_post_processing", "plan_thumbnails", "read_download_archive", "render_items", "render_output_path", "resolve_authentication", "resolve_inputs", "resolve_live_media", "resolve_output_path", "resolve_update_repository", "run", "run_post_processing", "select_geo_route", "select_playlist", "select_subtitles", "sort_formats", "transfer_fragments", "transfer_media", "validate_network", "validate_workarounds", "write_download_archive"]
