from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_any_blank_by, _cott_ends_with, _cott_starts_with

from real.yt_dlp_types import ArchiveRequest, Authentication, AuthenticationKind, AuthenticationKind_Anonymous, AuthenticationKind_BrowserCookies, AuthenticationKind_Cookies, AuthenticationKind_Credentials, AuthenticationKind_Netrc, CertificatePolicy, CertificatePolicy_Insecure, CertificatePolicy_Verify, CliInput, DownloadPlan, ExecutionReport, ExecutionRequest, ExternalToolRequest, ExtractorDescriptor, ExtractorWorkaround, ExtractorWorkaround_ForceGeneric, ExtractorWorkaround_LegacyServerConnect, ExtractorWorkaround_NoCheckCertificates, ExtractorWorkaround_NoPlaylist, FormatContainer, FormatContainer_Any, FormatContainer_Audio, FormatContainer_Best, FormatContainer_Video, FormatContainer_Worst, FormatDescriptor, FormatRequest, FragmentPolicy, GeoBypassMode, GeoBypassMode_Country, GeoBypassMode_Default, GeoBypassMode_Disabled, GeoBypassMode_IpBlock, InputKind, InputKind_Argument, InputKind_BatchFile, InputKind_ConfigFile, JsonMode, JsonMode_Lines, JsonMode_Single, LiveMode, LiveMode_Default, LiveMode_FromStart, LiveMode_Wait, LiveRequest, LogLevel, LogLevel_Debug, LogLevel_Info, LogLevel_Quiet, LogLevel_Warning, MediaError, MediaError_ArchiveFailure, MediaError_AuthenticationFailed, MediaError_BatchReadFailed, MediaError_CertificateFailure, MediaError_CookieFailure, MediaError_ExternalToolMissing, MediaError_ExtractorMissing, MediaError_FormatUnavailable, MediaError_GeoRestricted, MediaError_HttpStatus, MediaError_InvalidConfig, MediaError_InvalidInput, MediaError_InvalidRange, MediaError_InvalidShortcut, MediaError_InvalidTemplate, MediaError_LogFailure, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_PathFailure, MediaError_PluginRejected, MediaError_PostProcessFailed, MediaError_RetryExhausted, MediaError_SizeLimit, MediaError_SubtitleUnavailable, MediaError_UnsupportedUrl, MediaError_UpdateUnavailable, MediaError_WorkaroundRejected, MediaItem, MetadataRequest, NetworkPolicy, OutputRequest, PlaylistMode, PlaylistMode_Flat, PlaylistMode_Playlist, PlaylistMode_Random, PlaylistMode_Reverse, PlaylistMode_Single, PlaylistRange, PlaylistRequest, PluginDescriptor, PostProcessRequest, PostProcessorKind, PostProcessorKind_ConvertThumbnails, PostProcessorKind_EmbedMetadata, PostProcessorKind_EmbedSubtitle, PostProcessorKind_EmbedThumbnail, PostProcessorKind_ExtractAudio, PostProcessorKind_Fixup, PostProcessorKind_RecodeVideo, PostProcessorKind_RemuxVideo, PostProcessorKind_SplitChapters, PostProcessorKind_SponsorBlock, PresentationRequest, ProxyMode, ProxyMode_Direct, ProxyMode_Http, ProxyMode_Socks, ShortcutKind, ShortcutKind_Search, ShortcutKind_SearchAll, ShortcutKind_Url, ShortcutRequest, SimulationMode, SimulationMode_Download, SimulationMode_PrintOnly, SimulationMode_Simulate, SimulationMode_SkipDownload, SubtitleMode, SubtitleMode_All, SubtitleMode_Automatic, SubtitleMode_Manual, SubtitleMode_None, SubtitleRequest, ThumbnailRequest, TransferReceipt, TransferRequest, UpdateOutcome, UpdateOutcome_Available, UpdateOutcome_Current, UpdateOutcome_Disabled, UpdateOutcome_Installed, UpdatePolicy, UpdatePolicy_Apply, UpdatePolicy_Check, UpdatePolicy_Master, UpdatePolicy_Never, UpdatePolicy_Nightly, UpdateRequest, VideoFilterRequest, WorkaroundPolicy

def parse_arguments(arguments: CottList[str]) -> Result[CottList[CliInput], MediaError]:
    """arguments excludes the program name. Scan them left to right and return one
CliInput per input, in argument order. `--batch-file VALUE`, `-a VALUE` and
`--batch-file=VALUE` yield BatchFile(VALUE). `--config-locations VALUE` and
`--config-locations=VALUE` yield ConfigFile(VALUE). A separate VALUE is the
next argument taken verbatim, even when it starts with "-". Every argument
that does not start with "-" yields Argument(argument) unchanged. There are no
other options: an argument starting with "-" that is not one of these forms
(including "-" and "--"), an option without a following value, and an empty
VALUE return InvalidInput with a fixed descriptive message. Values are not
stripped, validated as URLs or read."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/parse_arguments.py", "db7fd2f633afa1b1f280778c4c51a9ad00013cccf60d892040a429272ec5f36a", "parse_arguments", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.parse_arguments")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.parse_arguments"
        if _error.span is None:
            _error.span = {"end_byte":9725,"end_column":1,"end_line":414,"start_byte":8749,"start_column":1,"start_line":394}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.parse_arguments", phase="implementation-call", span={"end_byte":9725,"end_column":1,"end_line":414,"start_byte":8749,"start_column":1,"start_line":394}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.parse_arguments", phase="implementation-call", span={"end_byte":9725,"end_column":1,"end_line":414,"start_byte":8749,"start_column":1,"start_line":394}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CliInput], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.parse_arguments", phase="error", span={"end_byte":9725,"end_column":1,"end_line":414,"start_byte":8749,"start_column":1,"start_line":394}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.parse_arguments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.parse_arguments", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.parse_arguments", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            inputs = _cott_match_value.value
            return (_cott_contract_condition(((len(inputs) <= len(arguments))), "real.yt_dlp.parse_arguments", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.parse_arguments", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.parse_arguments", clause="ensures:1", phase="ensures", span={"end_byte":9672,"end_column":61,"end_line":408,"start_byte":9616,"start_column":5,"start_line":408}, expected="true", actual="false")
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
    if _expected_error is None and (_cott_contract_condition(((len((request).query) == 0)), "real.yt_dlp.build_shortcut_url", "error:6:condition")):
        _expected_error = MediaError_InvalidShortcut
        _expected_error_span = {"end_byte":11145,"end_column":65,"end_line":431,"start_byte":11085,"start_column":5,"start_line":431}
        _expected_error_clause = "error:6"
    if _expected_error is None and (_cott_contract_condition(((((request).kind == ShortcutKind_Search()) and ((request).limit == 0))), "real.yt_dlp.build_shortcut_url", "error:7:condition")):
        _expected_error = MediaError_InvalidShortcut
        _expected_error_span = {"end_byte":11246,"end_column":101,"end_line":432,"start_byte":11150,"start_column":5,"start_line":432}
        _expected_error_clause = "error:7"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/build_shortcut_url.py", "ae0f03f4ddc5e6bc824337b181970d9b9088d2caaf420f093a7b9a39cec7b0d6", "build_shortcut_url", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.build_shortcut_url")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.build_shortcut_url"
        if _error.span is None:
            _error.span = {"end_byte":11301,"end_column":1,"end_line":437,"start_byte":9725,"start_column":1,"start_line":414}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.build_shortcut_url", phase="implementation-call", span={"end_byte":11301,"end_column":1,"end_line":437,"start_byte":9725,"start_column":1,"start_line":414}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.build_shortcut_url", phase="implementation-call", span={"end_byte":11301,"end_column":1,"end_line":437,"start_byte":9725,"start_column":1,"start_line":414}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.build_shortcut_url", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidShortcut,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.build_shortcut_url", phase="error", span={"end_byte":11301,"end_column":1,"end_line":437,"start_byte":9725,"start_column":1,"start_line":414}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.build_shortcut_url", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.build_shortcut_url", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidShortcut:
        _cott_contract_condition(True, "real.yt_dlp.build_shortcut_url", "error:8")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            url = _cott_match_value.value
            return (_cott_contract_condition((((not ((request).kind == ShortcutKind_Search())) or (((_cott_starts_with(url, "ytsearch") and (not _cott_starts_with(url, "ytsearchall:"))) and _cott_ends_with(url, (request).query)) and (len(url) > (len((request).query) + 9))))), "real.yt_dlp.build_shortcut_url", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.build_shortcut_url", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.build_shortcut_url", clause="ensures:1", phase="ensures", span={"end_byte":10545,"end_column":213,"end_line":425,"start_byte":10337,"start_column":5,"start_line":425}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            url = _cott_match_value.value
            return (_cott_contract_condition((((not ((request).kind == ShortcutKind_SearchAll())) or ((_cott_starts_with(url, "ytsearchall:") and _cott_ends_with(url, (request).query)) and (len(url) == (len((request).query) + 12))))), "real.yt_dlp.build_shortcut_url", "ensures:2"))
        _cott_contract_condition((False), "real.yt_dlp.build_shortcut_url", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.build_shortcut_url", clause="ensures:2", phase="ensures", span={"end_byte":10726,"end_column":181,"end_line":426,"start_byte":10550,"start_column":5,"start_line":426}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            url = _cott_match_value.value
            return (_cott_contract_condition((((not ((request).kind == ShortcutKind_Url())) or ((len(url) > 0) and (url in (request).query)))), "real.yt_dlp.build_shortcut_url", "ensures:3"))
        _cott_contract_condition((False), "real.yt_dlp.build_shortcut_url", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.build_shortcut_url", clause="ensures:3", phase="ensures", span={"end_byte":10841,"end_column":115,"end_line":427,"start_byte":10731,"start_column":5,"start_line":427}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is MediaError_InvalidShortcut and True:
            value = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((value == (request).query)), "real.yt_dlp.build_shortcut_url", "ensures:4"))
        _cott_contract_condition((False), "real.yt_dlp.build_shortcut_url", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.build_shortcut_url", clause="ensures:4", phase="ensures", span={"end_byte":10925,"end_column":84,"end_line":428,"start_byte":10846,"start_column":5,"start_line":428}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and True:
            return (_cott_contract_condition((((((request).kind == ShortcutKind_Url()) or (len((request).query) == 0)) or (((request).kind == ShortcutKind_Search()) and ((request).limit == 0)))), "real.yt_dlp.build_shortcut_url", "ensures:5"))
        _cott_contract_condition((False), "real.yt_dlp.build_shortcut_url", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.build_shortcut_url", clause="ensures:5", phase="ensures", span={"end_byte":11079,"end_column":154,"end_line":429,"start_byte":10930,"start_column":5,"start_line":429}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def validate_workarounds(policy: WorkaroundPolicy) -> Result[WorkaroundPolicy, MediaError]:
    """Accept only workarounds this client honors and return the policy unchanged.
Transfers always verify TLS certificates and hostnames, so Insecure returns
CertificateFailure. Legacy TLS server connect is unsupported, and the single
generic extractor takes no extractor arguments, so either request returns
WorkaroundRejected. force_generic_extractor is accepted because the generic
extractor is the only one. Error messages are fixed descriptive text."""
    policy = _cott_validate_abi(policy, WorkaroundPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((policy).certificate == CertificatePolicy_Insecure())), "real.yt_dlp.validate_workarounds", "error:3:condition")):
        _expected_error = MediaError_CertificateFailure
        _expected_error_span = {"end_byte":12048,"end_column":94,"end_line":450,"start_byte":11959,"start_column":5,"start_line":450}
        _expected_error_clause = "error:3"
    if _expected_error is None and (_cott_contract_condition((((policy).legacy_server_connect or (len((policy).extractor_args) > 0))), "real.yt_dlp.validate_workarounds", "error:4:condition")):
        _expected_error = MediaError_WorkaroundRejected
        _expected_error_span = {"end_byte":12157,"end_column":109,"end_line":451,"start_byte":12053,"start_column":5,"start_line":451}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/validate_workarounds.py", "0dde7a5a88897a2e82cc00a64d39d74912c2363646c535873abba72b5b8b88c2", "validate_workarounds", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.validate_workarounds")
        _result = _implementation(policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.validate_workarounds"
        if _error.span is None:
            _error.span = {"end_byte":12175,"end_column":1,"end_line":455,"start_byte":11301,"start_column":1,"start_line":437}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.validate_workarounds", phase="implementation-call", span={"end_byte":12175,"end_column":1,"end_line":455,"start_byte":11301,"start_column":1,"start_line":437}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.validate_workarounds", phase="implementation-call", span={"end_byte":12175,"end_column":1,"end_line":455,"start_byte":11301,"start_column":1,"start_line":437}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[WorkaroundPolicy, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.validate_workarounds", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.validate_workarounds", phase="error", span={"end_byte":12175,"end_column":1,"end_line":455,"start_byte":11301,"start_column":1,"start_line":437}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.validate_workarounds", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.validate_workarounds", _expected_error_clause)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            valid = _cott_match_value.value
            return (_cott_contract_condition(((valid == policy)), "real.yt_dlp.validate_workarounds", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.validate_workarounds", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.validate_workarounds", clause="ensures:1", phase="ensures", span={"end_byte":11933,"end_column":48,"end_line":447,"start_byte":11890,"start_column":5,"start_line":447}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[WorkaroundPolicy, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def configure_presentation(request: PresentationRequest) -> Result[Unit, MediaError]:
    """Prepare the log destination named by request.log_file. Open it for appending
without following a symlink, create a missing file with mode 0600, never
truncate existing content, write nothing and close it. An empty, "." or ".."
leaf, a missing parent directory, a symlink, a nonregular file, and any
open, inspect or close failure return LogFailure(path=request.log_file,
message=a fixed descriptive category). level, progress, newline_progress,
color, dump_pages and write_pages are accepted as given: this client prints
only the rendered report, so they select no other output."""
    request = _cott_validate_abi(request, PresentationRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/configure_presentation.py", "dec5fc704d0b559097a4244d09a3dbf0249fed3b3085880f425c7b7018504562", "configure_presentation", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.configure_presentation")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.configure_presentation"
        if _error.span is None:
            _error.span = {"end_byte":13188,"end_column":1,"end_line":475,"start_byte":12175,"start_column":1,"start_line":455}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.configure_presentation", phase="implementation-call", span={"end_byte":13188,"end_column":1,"end_line":475,"start_byte":12175,"start_column":1,"start_line":455}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.configure_presentation", phase="implementation-call", span={"end_byte":13188,"end_column":1,"end_line":475,"start_byte":12175,"start_column":1,"start_line":455}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.configure_presentation", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_LogFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.configure_presentation", phase="error", span={"end_byte":13188,"end_column":1,"end_line":475,"start_byte":12175,"start_column":1,"start_line":455}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.configure_presentation", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.configure_presentation", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_LogFailure:
        _cott_contract_condition(True, "real.yt_dlp.configure_presentation", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            configured = _cott_match_value.value
            return (_cott_contract_condition(((configured == UNIT)), "real.yt_dlp.configure_presentation", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.configure_presentation", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.configure_presentation", clause="ensures:1", phase="ensures", span={"end_byte":13044,"end_column":54,"end_line":468,"start_byte":12995,"start_column":5,"start_line":468}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is MediaError_LogFailure and True and True:
            path = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((path == (request).log_file)), "real.yt_dlp.configure_presentation", "ensures:2"))
        _cott_contract_condition((False), "real.yt_dlp.configure_presentation", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.configure_presentation", clause="ensures:2", phase="ensures", span={"end_byte":13127,"end_column":83,"end_line":469,"start_byte":13049,"start_column":5,"start_line":469}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_config(path: Path) -> Result[CottList[CliInput], MediaError]:
    """Read path, a regular file of at most 1 MiB, as UTF-8 text; ignore one leading
UTF-8 byte order mark. Split the text into arguments with POSIX shell-like
rules: whitespace separates arguments, single quotes, double quotes and
backslash escapes group them, and an unquoted "#" that starts an argument
comments out the rest of its line. Pass the arguments, in file order, to
real.yt_dlp.parse_arguments and return its inputs unchanged. A missing,
unreadable, nonregular or oversized file, invalid UTF-8, unbalanced quoting,
more than 100000 arguments and a parse_arguments error all return
InvalidConfig(path=path, message=a fixed descriptive category) without file
content."""
    path = _cott_validate_abi(path, Path, path="$.path")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/load_config.py", "65c689d9cb8e5f8b1e95be733483bb17d86c548d26d12f5868fbf9e4a6fb7d3c", "load_config", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.load_config")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.load_config"
        if _error.span is None:
            _error.span = {"end_byte":14181,"end_column":1,"end_line":496,"start_byte":13188,"start_column":1,"start_line":475}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.load_config", phase="implementation-call", span={"end_byte":14181,"end_column":1,"end_line":496,"start_byte":13188,"start_column":1,"start_line":475}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.load_config", phase="implementation-call", span={"end_byte":14181,"end_column":1,"end_line":496,"start_byte":13188,"start_column":1,"start_line":475}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[CliInput], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.load_config", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidConfig,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.load_config", phase="error", span={"end_byte":14181,"end_column":1,"end_line":496,"start_byte":13188,"start_column":1,"start_line":475}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.load_config", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.load_config", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidConfig:
        _cott_contract_condition(True, "real.yt_dlp.load_config", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            inputs = _cott_match_value.value
            return (_cott_contract_condition(((len(inputs) <= 100000)), "real.yt_dlp.load_config", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.load_config", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.load_config", clause="ensures:1", phase="ensures", span={"end_byte":14040,"end_column":54,"end_line":489,"start_byte":13991,"start_column":5,"start_line":489}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is MediaError_InvalidConfig and True and True:
            config = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((config == path)), "real.yt_dlp.load_config", "ensures:2"))
        _cott_contract_condition((False), "real.yt_dlp.load_config", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.load_config", clause="ensures:2", phase="ensures", span={"end_byte":14118,"end_column":78,"end_line":490,"start_byte":14045,"start_column":5,"start_line":490}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CliInput], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def parse_batch_urls(batch: str, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]:
    """Parse batch-file text into URLs. Ignore one leading U+FEFF, split the rest
into lines at LF, CRLF or CR, strip surrounding whitespace from each line,
and drop empty lines and lines starting with any comment prefix. Return the
remaining stripped lines in order, keeping duplicates; they are not validated
as URLs. An empty comment prefix and a result of more than 100000 URLs return
InvalidInput with a fixed descriptive message."""
    batch = _cott_validate_abi(batch, str, path="$.batch")
    comment_prefixes = _cott_validate_abi(comment_prefixes, CottList[str], path="$.comment_prefixes")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/parse_batch_urls.py", "ab6c55b7ab2a4eb91555049fa36e4ec001d0a58982116df7fd8f66a37032d337", "parse_batch_urls", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.parse_batch_urls")
        _result = _implementation(batch, comment_prefixes)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.parse_batch_urls"
        if _error.span is None:
            _error.span = {"end_byte":14855,"end_column":1,"end_line":512,"start_byte":14181,"start_column":1,"start_line":496}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.parse_batch_urls", phase="implementation-call", span={"end_byte":14855,"end_column":1,"end_line":512,"start_byte":14181,"start_column":1,"start_line":496}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.parse_batch_urls", phase="implementation-call", span={"end_byte":14855,"end_column":1,"end_line":512,"start_byte":14181,"start_column":1,"start_line":496}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.parse_batch_urls", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.parse_batch_urls", phase="error", span={"end_byte":14855,"end_column":1,"end_line":512,"start_byte":14181,"start_column":1,"start_line":496}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.parse_batch_urls", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.parse_batch_urls", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.parse_batch_urls", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            urls = _cott_match_value.value
            return (_cott_contract_condition(((len(urls) <= len(batch))), "real.yt_dlp.parse_batch_urls", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.parse_batch_urls", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.parse_batch_urls", clause="ensures:1", phase="ensures", span={"end_byte":14802,"end_column":53,"end_line":506,"start_byte":14754,"start_column":5,"start_line":506}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_batch_urls(path: Path, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]:
    """Read path, a regular file of at most 16 MiB, decode it as UTF-8 and return
real.yt_dlp.parse_batch_urls(text, comment_prefixes) unchanged, including its
InvalidInput. A missing, unreadable, nonregular or oversized file and invalid
UTF-8 return BatchReadFailed(path=path, message=a fixed descriptive category)
without file content."""
    path = _cott_validate_abi(path, Path, path="$.path")
    comment_prefixes = _cott_validate_abi(comment_prefixes, CottList[str], path="$.comment_prefixes")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/load_batch_urls.py", "f9ee673808ebcf0747e1c48085e60c2c11be81df295402f3354affd07fd16cbf", "load_batch_urls", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.load_batch_urls")
        _result = _implementation(path, comment_prefixes)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.load_batch_urls"
        if _error.span is None:
            _error.span = {"end_byte":15547,"end_column":1,"end_line":529,"start_byte":14855,"start_column":1,"start_line":512}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.load_batch_urls", phase="implementation-call", span={"end_byte":15547,"end_column":1,"end_line":529,"start_byte":14855,"start_column":1,"start_line":512}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.load_batch_urls", phase="implementation-call", span={"end_byte":15547,"end_column":1,"end_line":529,"start_byte":14855,"start_column":1,"start_line":512}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.load_batch_urls", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_BatchReadFailed, MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.load_batch_urls", phase="error", span={"end_byte":15547,"end_column":1,"end_line":529,"start_byte":14855,"start_column":1,"start_line":512}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.load_batch_urls", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.load_batch_urls", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_BatchReadFailed:
        _cott_contract_condition(True, "real.yt_dlp.load_batch_urls", "error:3")
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.load_batch_urls", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            urls = _cott_match_value.value
            return (_cott_contract_condition(((len(urls) <= 100000)), "real.yt_dlp.load_batch_urls", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.load_batch_urls", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.load_batch_urls", clause="ensures:1", phase="ensures", span={"end_byte":15370,"end_column":50,"end_line":521,"start_byte":15325,"start_column":5,"start_line":521}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is MediaError_BatchReadFailed and True and True:
            batch = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((batch == path)), "real.yt_dlp.load_batch_urls", "ensures:2"))
        _cott_contract_condition((False), "real.yt_dlp.load_batch_urls", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.load_batch_urls", clause="ensures:2", phase="ensures", span={"end_byte":15448,"end_column":78,"end_line":522,"start_byte":15375,"start_column":5,"start_line":522}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_inputs(inputs: CottList[CliInput], config: CottList[CliInput]) -> Result[CottList[str], MediaError]:
    """Return the values of inputs followed by the values of config, in order and
unchanged, one URL per entry. Callers expand ConfigFile and BatchFile entries
first, so an entry of any other kind than Argument returns InvalidInput, as
does a blank value (empty or only whitespace). Messages are fixed text."""
    inputs = _cott_validate_abi(inputs, CottList[CliInput], path="$.inputs")
    config = _cott_validate_abi(config, CottList[CliInput], path="$.config")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((_cott_any_blank_by(inputs, "value") or _cott_any_blank_by(config, "value"))), "real.yt_dlp.resolve_inputs", "error:2:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":16170,"end_column":118,"end_line":539,"start_byte":16057,"start_column":5,"start_line":539}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/resolve_inputs.py", "387cd73ba490bbfef03a52e997e3ec80eee744b99a68b41ae3716ae0cede5dfa", "resolve_inputs", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.resolve_inputs")
        _result = _implementation(inputs, config)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.resolve_inputs"
        if _error.span is None:
            _error.span = {"end_byte":16222,"end_column":1,"end_line":544,"start_byte":15547,"start_column":1,"start_line":529}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.resolve_inputs", phase="implementation-call", span={"end_byte":16222,"end_column":1,"end_line":544,"start_byte":15547,"start_column":1,"start_line":529}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.resolve_inputs", phase="implementation-call", span={"end_byte":16222,"end_column":1,"end_line":544,"start_byte":15547,"start_column":1,"start_line":529}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.resolve_inputs", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.resolve_inputs", phase="error", span={"end_byte":16222,"end_column":1,"end_line":544,"start_byte":15547,"start_column":1,"start_line":529}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.resolve_inputs", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.resolve_inputs", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.resolve_inputs", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            urls = _cott_match_value.value
            return (_cott_contract_condition(((len(urls) == (len(inputs) + len(config)))), "real.yt_dlp.resolve_inputs", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.resolve_inputs", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_inputs", clause="ensures:1", phase="ensures", span={"end_byte":16051,"end_column":67,"end_line":537,"start_byte":15989,"start_column":5,"start_line":537}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def validate_network(policy: NetworkPolicy) -> Result[NetworkPolicy, MediaError]:
    """Validate network settings and return the policy unchanged. Each of these
returns InvalidInput with a fixed descriptive message: socket_timeout_ms is
zero; force_ipv4 and force_ipv6 are both set; Direct has a nonempty proxy;
Http or Socks has an empty proxy, or a proxy that is not an absolute URL
without whitespace whose scheme is http or https (Http) or socks4, socks4a,
socks5 or socks5h (Socks), with a nonempty host and a valid port;
source_address is nonempty and not a literal IPv4 or IPv6 address, or is of
the other family than a forced one; Disabled or Default has a nonempty
geo_country or geo_ip_block; Country has a geo_ip_block or a geo_country that
is not two ASCII letters; IpBlock has a geo_country, or a geo_ip_block that is
not an IPv4 or IPv6 address with an optional decimal prefix length of at most
32 or 128."""
    policy = _cott_validate_abi(policy, NetworkPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((policy).socket_timeout_ms == 0)), "real.yt_dlp.validate_network", "error:2:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":17321,"end_column":69,"end_line":562,"start_byte":17257,"start_column":5,"start_line":562}
        _expected_error_clause = "error:2"
    if _expected_error is None and (_cott_contract_condition((((policy).force_ipv4 and (policy).force_ipv6)), "real.yt_dlp.validate_network", "error:3:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":17400,"end_column":79,"end_line":563,"start_byte":17326,"start_column":5,"start_line":563}
        _expected_error_clause = "error:3"
    if _expected_error is None and (_cott_contract_condition(((((policy).proxy_mode == ProxyMode_Direct()) and (len((policy).proxy) > 0))), "real.yt_dlp.validate_network", "error:4:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":17504,"end_column":104,"end_line":564,"start_byte":17405,"start_column":5,"start_line":564}
        _expected_error_clause = "error:4"
    if _expected_error is None and (_cott_contract_condition(((((policy).proxy_mode != ProxyMode_Direct()) and (len((policy).proxy) == 0))), "real.yt_dlp.validate_network", "error:5:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":17609,"end_column":105,"end_line":565,"start_byte":17509,"start_column":5,"start_line":565}
        _expected_error_clause = "error:5"
    if _expected_error is None and (_cott_contract_condition((((((policy).geo_mode == GeoBypassMode_Disabled()) or ((policy).geo_mode == GeoBypassMode_Default())) and ((len((policy).geo_country) > 0) or (len((policy).geo_ip_block) > 0)))), "real.yt_dlp.validate_network", "error:6:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":17802,"end_column":193,"end_line":566,"start_byte":17614,"start_column":5,"start_line":566}
        _expected_error_clause = "error:6"
    if _expected_error is None and (_cott_contract_condition(((((policy).geo_mode == GeoBypassMode_Country()) and ((len((policy).geo_ip_block) > 0) or (len((policy).geo_country) != 2)))), "real.yt_dlp.validate_network", "error:7:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":17949,"end_column":147,"end_line":567,"start_byte":17807,"start_column":5,"start_line":567}
        _expected_error_clause = "error:7"
    if _expected_error is None and (_cott_contract_condition(((((policy).geo_mode == GeoBypassMode_IpBlock()) and ((len((policy).geo_country) > 0) or (len((policy).geo_ip_block) == 0)))), "real.yt_dlp.validate_network", "error:8:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":18096,"end_column":147,"end_line":568,"start_byte":17954,"start_column":5,"start_line":568}
        _expected_error_clause = "error:8"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/validate_network.py", "a94cb52453b83c4967708c4671256be04cfbaefcc1e219eae4110ae855debed0", "validate_network", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.validate_network")
        _result = _implementation(policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.validate_network"
        if _error.span is None:
            _error.span = {"end_byte":18148,"end_column":1,"end_line":573,"start_byte":16222,"start_column":1,"start_line":544}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.validate_network", phase="implementation-call", span={"end_byte":18148,"end_column":1,"end_line":573,"start_byte":16222,"start_column":1,"start_line":544}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.validate_network", phase="implementation-call", span={"end_byte":18148,"end_column":1,"end_line":573,"start_byte":16222,"start_column":1,"start_line":544}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[NetworkPolicy, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.validate_network", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.validate_network", phase="error", span={"end_byte":18148,"end_column":1,"end_line":573,"start_byte":16222,"start_column":1,"start_line":544}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.validate_network", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.validate_network", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.validate_network", "error:9")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            valid = _cott_match_value.value
            return (_cott_contract_condition(((valid == policy)), "real.yt_dlp.validate_network", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.validate_network", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.validate_network", clause="ensures:1", phase="ensures", span={"end_byte":17251,"end_column":48,"end_line":560,"start_byte":17208,"start_column":5,"start_line":560}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[NetworkPolicy, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_authentication(request: Authentication) -> Result[Authentication, MediaError]:
    """Check that the requested authentication is one this direct-media client can
send and return it unchanged. Anonymous is accepted. Credentials needs a
nonempty username and password, which extract_media sends as HTTP Basic
authorization. Netrc is unsupported and returns AuthenticationFailed;
Cookies and BrowserCookies are unsupported and return CookieFailure. Fields
the selected kind does not use are ignored. Messages are fixed text and never
contain the username, password or file paths."""
    request = _cott_validate_abi(request, Authentication, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((((request).kind == AuthenticationKind_Credentials()) and ((len((request).username) == 0) or (len((request).password) == 0)))), "real.yt_dlp.resolve_authentication", "error:3:condition")):
        _expected_error = MediaError_AuthenticationFailed
        _expected_error_span = {"end_byte":19020,"end_column":157,"end_line":587,"start_byte":18868,"start_column":5,"start_line":587}
        _expected_error_clause = "error:3"
    if _expected_error is None and (_cott_contract_condition((((request).kind == AuthenticationKind_Netrc())), "real.yt_dlp.resolve_authentication", "error:4:condition")):
        _expected_error = MediaError_AuthenticationFailed
        _expected_error_span = {"end_byte":19108,"end_column":88,"end_line":588,"start_byte":19025,"start_column":5,"start_line":588}
        _expected_error_clause = "error:4"
    if _expected_error is None and (_cott_contract_condition(((((request).kind == AuthenticationKind_Cookies()) or ((request).kind == AuthenticationKind_BrowserCookies()))), "real.yt_dlp.resolve_authentication", "error:5:condition")):
        _expected_error = MediaError_CookieFailure
        _expected_error_span = {"end_byte":19246,"end_column":138,"end_line":589,"start_byte":19113,"start_column":5,"start_line":589}
        _expected_error_clause = "error:5"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/resolve_authentication.py", "bd699804fea999ef5031281b6642dbef2022edc949f732c2eda85eecf1381222", "resolve_authentication", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.resolve_authentication")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.resolve_authentication"
        if _error.span is None:
            _error.span = {"end_byte":19264,"end_column":1,"end_line":593,"start_byte":18148,"start_column":1,"start_line":573}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.resolve_authentication", phase="implementation-call", span={"end_byte":19264,"end_column":1,"end_line":593,"start_byte":18148,"start_column":1,"start_line":573}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.resolve_authentication", phase="implementation-call", span={"end_byte":19264,"end_column":1,"end_line":593,"start_byte":18148,"start_column":1,"start_line":573}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Authentication, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.resolve_authentication", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.resolve_authentication", phase="error", span={"end_byte":19264,"end_column":1,"end_line":593,"start_byte":18148,"start_column":1,"start_line":573}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.resolve_authentication", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.resolve_authentication", _expected_error_clause)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            authenticated = _cott_match_value.value
            return (_cott_contract_condition(((authenticated == request)), "real.yt_dlp.resolve_authentication", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.resolve_authentication", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_authentication", clause="ensures:1", phase="ensures", span={"end_byte":18842,"end_column":65,"end_line":584,"start_byte":18782,"start_column":5,"start_line":584}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Authentication, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def select_geo_route(policy: NetworkPolicy) -> Result[NetworkPolicy, MediaError]:
    """Choose the geo-bypass route used for extraction and return the policy
unchanged. Disabled and Default send no geo header. IpBlock is routed by
extract_media, which sends the block's network address as X-Forwarded-For;
a geo_ip_block that is not an IPv4 or IPv6 address with an optional decimal
prefix length of at most 32 or 128 returns GeoRestricted. Country bypass
needs a country-to-address table this client does not have, so Country
returns GeoRestricted. Messages are fixed text."""
    policy = _cott_validate_abi(policy, NetworkPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((policy).geo_mode == GeoBypassMode_Country())), "real.yt_dlp.select_geo_route", "error:2:condition")):
        _expected_error = MediaError_GeoRestricted
        _expected_error_span = {"end_byte":20009,"end_column":81,"end_line":606,"start_byte":19933,"start_column":5,"start_line":606}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/select_geo_route.py", "8514e583ce355bf1c19ee68198d11a8b44ef6e2deffe5a074e5a8b27819b53ac", "select_geo_route", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.select_geo_route")
        _result = _implementation(policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.select_geo_route"
        if _error.span is None:
            _error.span = {"end_byte":20062,"end_column":1,"end_line":611,"start_byte":19264,"start_column":1,"start_line":593}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.select_geo_route", phase="implementation-call", span={"end_byte":20062,"end_column":1,"end_line":611,"start_byte":19264,"start_column":1,"start_line":593}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.select_geo_route", phase="implementation-call", span={"end_byte":20062,"end_column":1,"end_line":611,"start_byte":19264,"start_column":1,"start_line":593}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[NetworkPolicy, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.select_geo_route", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_GeoRestricted,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.select_geo_route", phase="error", span={"end_byte":20062,"end_column":1,"end_line":611,"start_byte":19264,"start_column":1,"start_line":593}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.select_geo_route", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.select_geo_route", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_GeoRestricted:
        _cott_contract_condition(True, "real.yt_dlp.select_geo_route", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            route = _cott_match_value.value
            return (_cott_contract_condition(((route == policy)), "real.yt_dlp.select_geo_route", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.select_geo_route", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.select_geo_route", clause="ensures:1", phase="ensures", span={"end_byte":19927,"end_column":48,"end_line":604,"start_byte":19884,"start_column":5,"start_line":604}, expected="true", actual="false")
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
            _error.span = {"end_byte":20385,"end_column":1,"end_line":620,"start_byte":20062,"start_column":1,"start_line":611}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.discover_extractors", phase="implementation-call", span={"end_byte":20385,"end_column":1,"end_line":620,"start_byte":20062,"start_column":1,"start_line":611}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.discover_extractors", phase="implementation-call", span={"end_byte":20385,"end_column":1,"end_line":620,"start_byte":20062,"start_column":1,"start_line":611}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
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
    if _expected_error is None and (_cott_contract_condition(((len(paths) > 100000)), "real.yt_dlp.load_plugins", "error:2:condition")):
        _expected_error = MediaError_PluginRejected
        _expected_error_span = {"end_byte":21895,"end_column":60,"end_line":642,"start_byte":21840,"start_column":5,"start_line":642}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/load_plugins.py", "b8d843b23090669aac3a571a5e8d20b9ed3a428b37b392ef80d9e9f999bcbee8", "load_plugins", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.load_plugins")
        _result = _implementation(paths)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.load_plugins"
        if _error.span is None:
            _error.span = {"end_byte":21958,"end_column":1,"end_line":647,"start_byte":20385,"start_column":1,"start_line":620}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.load_plugins", phase="implementation-call", span={"end_byte":21958,"end_column":1,"end_line":647,"start_byte":20385,"start_column":1,"start_line":620}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.load_plugins", phase="implementation-call", span={"end_byte":21958,"end_column":1,"end_line":647,"start_byte":20385,"start_column":1,"start_line":620}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[PluginDescriptor], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.load_plugins", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_PluginRejected,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.load_plugins", phase="error", span={"end_byte":21958,"end_column":1,"end_line":647,"start_byte":20385,"start_column":1,"start_line":620}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.load_plugins", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.load_plugins", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_PluginRejected:
        _cott_contract_condition(True, "real.yt_dlp.load_plugins", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plugins = _cott_match_value.value
            return (_cott_contract_condition(((len(plugins) == len(paths))), "real.yt_dlp.load_plugins", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.load_plugins", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.load_plugins", clause="ensures:1", phase="ensures", span={"end_byte":21834,"end_column":59,"end_line":640,"start_byte":21780,"start_column":5,"start_line":640}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[PluginDescriptor], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def choose_extractor(url: str, extractors: CottList[ExtractorDescriptor]) -> Result[ExtractorDescriptor, MediaError]:
    """An extractor matches url when one of its nonempty urls entries is a
case-sensitive prefix of url. Return the first enabled matching extractor in
list order, unchanged. When only disabled extractors match, return
ExtractorMissing(name=the first matching disabled extractor's name). When
nothing matches, return UnsupportedUrl."""
    url = _cott_validate_abi(url, str, path="$.url")
    extractors = _cott_validate_abi(extractors, CottList[ExtractorDescriptor], path="$.extractors")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((len(extractors) == 0)), "real.yt_dlp.choose_extractor", "error:2:condition")):
        _expected_error = MediaError_UnsupportedUrl
        _expected_error_span = {"end_byte":22564,"end_column":61,"end_line":661,"start_byte":22508,"start_column":5,"start_line":661}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/choose_extractor.py", "98dcc114c31867a685da7c2ad7e3ed749bb5f9bf7ff7d830ecbb00fec134df1d", "choose_extractor", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.choose_extractor")
        _result = _implementation(url, extractors)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.choose_extractor"
        if _error.span is None:
            _error.span = {"end_byte":22656,"end_column":1,"end_line":667,"start_byte":21958,"start_column":1,"start_line":647}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.choose_extractor", phase="implementation-call", span={"end_byte":22656,"end_column":1,"end_line":667,"start_byte":21958,"start_column":1,"start_line":647}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.choose_extractor", phase="implementation-call", span={"end_byte":22656,"end_column":1,"end_line":667,"start_byte":21958,"start_column":1,"start_line":647}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ExtractorDescriptor, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.choose_extractor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_UnsupportedUrl, MediaError_ExtractorMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.choose_extractor", phase="error", span={"end_byte":22656,"end_column":1,"end_line":667,"start_byte":21958,"start_column":1,"start_line":647}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.choose_extractor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.choose_extractor", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_UnsupportedUrl:
        _cott_contract_condition(True, "real.yt_dlp.choose_extractor", "error:3")
    if type(_result) is Err and type(_result.error) is MediaError_ExtractorMissing:
        _cott_contract_condition(True, "real.yt_dlp.choose_extractor", "error:4")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            extractor = _cott_match_value.value
            return (_cott_contract_condition(((extractor).enabled), "real.yt_dlp.choose_extractor", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.choose_extractor", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.choose_extractor", clause="ensures:1", phase="ensures", span={"end_byte":22502,"end_column":54,"end_line":659,"start_byte":22453,"start_column":5,"start_line":659}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ExtractorDescriptor, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def extract_media(url: str, extractor: ExtractorDescriptor, authentication: Authentication, network: NetworkPolicy) -> Result[CottList[MediaItem], MediaError]:
    """Discover one direct media item without downloading it. url must be an
absolute URL with lowercase scheme http or https, a nonempty host and no
whitespace or control characters, accepted by the enabled extractor through
one of its nonempty urls prefixes; otherwise return UnsupportedUrl before
any request.
Authentication: Anonymous sends none, but an extractor with requires_login
returns AuthenticationFailed. Credentials sends HTTP Basic authorization and
needs a nonempty username and password, else AuthenticationFailed. Netrc,
Cookies and BrowserCookies are unsupported and return AuthenticationFailed.
Network: socket_timeout_ms is the request timeout. Http sends the request
through proxy; Socks is unsupported and returns NetworkFailure. IpBlock sends
the block's network address as X-Forwarded-For; Country returns GeoRestricted.
Send exactly one HTTP HEAD request with certificate-verifying TLS, following
at most five redirects. Never send GET or read a response body.
On a 2xx response return exactly one MediaItem built from the final URL: url
is the final URL; title is its percent-decoded last path segment; id is title
without its last "." extension; ext is that extension without the dot,
lowercased. When the path has no last segment, title and id are the host.
When there is no extension, ext is the Content-Type subtype when it is
alphanumeric, otherwise "unknown_video". playlist_index is 1.
Map 401 or 403 after sending credentials to AuthenticationFailed, 451 to
GeoRestricted, any other non-2xx status to HttpStatus(status), and DNS,
connection, TLS, timeout and redirect-limit failures to NetworkFailure with a
fixed message that contains no credentials or query strings."""
    url = _cott_validate_abi(url, str, path="$.url")
    extractor = _cott_validate_abi(extractor, ExtractorDescriptor, path="$.extractor")
    authentication = _cott_validate_abi(authentication, Authentication, path="$.authentication")
    network = _cott_validate_abi(network, NetworkPolicy, path="$.network")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((not (extractor).enabled) or (not (_cott_starts_with(url, "http://") or _cott_starts_with(url, "https://"))))), "real.yt_dlp.extract_media", "error:2:condition")):
        _expected_error = MediaError_UnsupportedUrl
        _expected_error_span = {"end_byte":24825,"end_column":134,"end_line":702,"start_byte":24696,"start_column":5,"start_line":702}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/extract_media.py", "c308c50c1283962fab81c9a99a581c7e920bf6ca5c81b1d602889e3d20308e63", "extract_media", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.extract_media")
        _result = _implementation(url, extractor, authentication, network)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.extract_media"
        if _error.span is None:
            _error.span = {"end_byte":25031,"end_column":1,"end_line":711,"start_byte":22656,"start_column":1,"start_line":667}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.extract_media", phase="implementation-call", span={"end_byte":25031,"end_column":1,"end_line":711,"start_byte":22656,"start_column":1,"start_line":667}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.extract_media", phase="implementation-call", span={"end_byte":25031,"end_column":1,"end_line":711,"start_byte":22656,"start_column":1,"start_line":667}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.extract_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_AuthenticationFailed, MediaError_GeoRestricted, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_UnsupportedUrl,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.extract_media", phase="error", span={"end_byte":25031,"end_column":1,"end_line":711,"start_byte":22656,"start_column":1,"start_line":667}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.extract_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.extract_media", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_AuthenticationFailed:
        _cott_contract_condition(True, "real.yt_dlp.extract_media", "error:3")
    if type(_result) is Err and type(_result.error) is MediaError_GeoRestricted:
        _cott_contract_condition(True, "real.yt_dlp.extract_media", "error:4")
    if type(_result) is Err and type(_result.error) is MediaError_HttpStatus:
        _cott_contract_condition(True, "real.yt_dlp.extract_media", "error:5")
    if type(_result) is Err and type(_result.error) is MediaError_NetworkFailure:
        _cott_contract_condition(True, "real.yt_dlp.extract_media", "error:6")
    if type(_result) is Err and type(_result.error) is MediaError_UnsupportedUrl:
        _cott_contract_condition(True, "real.yt_dlp.extract_media", "error:7")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            items = _cott_match_value.value
            return (_cott_contract_condition(((len(items) == 1)), "real.yt_dlp.extract_media", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.extract_media", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.extract_media", clause="ensures:1", phase="ensures", span={"end_byte":24690,"end_column":47,"end_line":700,"start_byte":24648,"start_column":5,"start_line":700}, expected="true", actual="false")
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
            _error.span = {"end_byte":25864,"end_column":1,"end_line":730,"start_byte":25031,"start_column":1,"start_line":711}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.expand_playlist_ranges", phase="implementation-call", span={"end_byte":25864,"end_column":1,"end_line":730,"start_byte":25031,"start_column":1,"start_line":711}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.expand_playlist_ranges", phase="implementation-call", span={"end_byte":25864,"end_column":1,"end_line":730,"start_byte":25031,"start_column":1,"start_line":711}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.expand_playlist_ranges", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidRange,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.expand_playlist_ranges", phase="error", span={"end_byte":25864,"end_column":1,"end_line":730,"start_byte":25031,"start_column":1,"start_line":711}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
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
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.expand_playlist_ranges", clause="ensures:1", phase="ensures", span={"end_byte":25811,"end_column":148,"end_line":724,"start_byte":25668,"start_column":5,"start_line":724}, expected="true", actual="false")
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
    if _expected_error is None and (_cott_contract_condition((((((request).start > 0) and ((request).end > 0)) and ((request).start > (request).end))), "real.yt_dlp.select_playlist", "error:3:condition")):
        _expected_error = MediaError_InvalidRange
        _expected_error_span = {"end_byte":27849,"end_column":111,"end_line":760,"start_byte":27743,"start_column":5,"start_line":760}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/select_playlist.py", "c040807bbcbb438f7bbd06833367baf4ff023a90a1098e75dcd6264ba9470b81", "select_playlist", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.select_playlist")
        _result = _implementation(items, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.select_playlist"
        if _error.span is None:
            _error.span = {"end_byte":27941,"end_column":1,"end_line":766,"start_byte":25864,"start_column":1,"start_line":730}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.select_playlist", phase="implementation-call", span={"end_byte":27941,"end_column":1,"end_line":766,"start_byte":25864,"start_column":1,"start_line":730}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.select_playlist", phase="implementation-call", span={"end_byte":27941,"end_column":1,"end_line":766,"start_byte":25864,"start_column":1,"start_line":730}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.select_playlist", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidRange, MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.select_playlist", phase="error", span={"end_byte":27941,"end_column":1,"end_line":766,"start_byte":25864,"start_column":1,"start_line":730}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.select_playlist", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.select_playlist", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidRange:
        _cott_contract_condition(True, "real.yt_dlp.select_playlist", "error:4")
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.select_playlist", "error:5")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return (_cott_contract_condition(((len(selected) <= len(items))), "real.yt_dlp.select_playlist", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.select_playlist", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.select_playlist", clause="ensures:1", phase="ensures", span={"end_byte":27643,"end_column":61,"end_line":757,"start_byte":27587,"start_column":5,"start_line":757}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return (_cott_contract_condition((((not ((request).mode == PlaylistMode_Single())) or (len(selected) <= 1))), "real.yt_dlp.select_playlist", "ensures:2"))
        _cott_contract_condition((False), "real.yt_dlp.select_playlist", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.select_playlist", clause="ensures:2", phase="ensures", span={"end_byte":27737,"end_column":94,"end_line":758,"start_byte":27648,"start_column":5,"start_line":758}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[MediaItem], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def resolve_live_media(items: CottList[MediaItem], request: LiveRequest) -> Result[CottList[MediaItem], MediaError]:
    """This stage validates a snapshot of already-discovered live-media candidates;
it is not a downloader, live-status probe or polling loop, and it neither
sleeps nor repeats discovery. MediaItem contains no start-time or live-state
field, so do not infer such state from its text. Default, FromStart and Wait
keep every supplied item unchanged and in order: retrieval from the
beginning is a downstream transfer choice, not a change to these descriptors.
Under Wait with a positive wait budget, an empty snapshot returns
RetryExhausted(attempts=1), referring to the one completed discovery
snapshot. InvalidInput messages are fixed text."""
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    request = _cott_validate_abi(request, LiveRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((request).concurrent_fragments == 0)), "real.yt_dlp.resolve_live_media", "error:4:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":28974,"end_column":73,"end_line":786,"start_byte":28906,"start_column":5,"start_line":786}
        _expected_error_clause = "error:4"
    if _expected_error is None and (_cott_contract_condition(((((request).mode == LiveMode_Wait()) and ((request).wait_for_video_ms == 0))), "real.yt_dlp.resolve_live_media", "error:5:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":29080,"end_column":106,"end_line":787,"start_byte":28979,"start_column":5,"start_line":787}
        _expected_error_clause = "error:5"
    if _expected_error is None and (_cott_contract_condition(((((request).mode == LiveMode_Wait()) and (len(items) == 0))), "real.yt_dlp.resolve_live_media", "error:6:condition")):
        _expected_error = MediaError_RetryExhausted
        _expected_error_span = {"end_byte":29170,"end_column":90,"end_line":788,"start_byte":29085,"start_column":5,"start_line":788}
        _expected_error_clause = "error:6"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/resolve_live_media.py", "b37386f637bba2b24014373193a0efeacca5ce705f4519c02382b04a5e3517c6", "resolve_live_media", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.resolve_live_media")
        _result = _implementation(items, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.resolve_live_media"
        if _error.span is None:
            _error.span = {"end_byte":29188,"end_column":1,"end_line":792,"start_byte":27941,"start_column":1,"start_line":766}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.resolve_live_media", phase="implementation-call", span={"end_byte":29188,"end_column":1,"end_line":792,"start_byte":27941,"start_column":1,"start_line":766}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.resolve_live_media", phase="implementation-call", span={"end_byte":29188,"end_column":1,"end_line":792,"start_byte":27941,"start_column":1,"start_line":766}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.resolve_live_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.resolve_live_media", phase="error", span={"end_byte":29188,"end_column":1,"end_line":792,"start_byte":27941,"start_column":1,"start_line":766}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.resolve_live_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.resolve_live_media", _expected_error_clause)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return (_cott_contract_condition(((selected == items)), "real.yt_dlp.resolve_live_media", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.resolve_live_media", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_live_media", clause="ensures:1", phase="ensures", span={"end_byte":28803,"end_column":53,"end_line":782,"start_byte":28755,"start_column":5,"start_line":782}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is MediaError_RetryExhausted and True:
            attempts = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((attempts == 1)), "real.yt_dlp.resolve_live_media", "ensures:2"))
        _cott_contract_condition((False), "real.yt_dlp.resolve_live_media", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_live_media", clause="ensures:2", phase="ensures", span={"end_byte":28880,"end_column":77,"end_line":783,"start_byte":28808,"start_column":5,"start_line":783}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[MediaItem], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def filter_video(items: CottList[MediaItem], request: VideoFilterRequest) -> Result[CottList[MediaItem], MediaError]:
    """MediaItem carries no upload date, view count, age limit or live state, so
this client cannot evaluate those filters and rejects them instead of
silently ignoring them: a nonempty date_after, date_before or match_filter, a
nonzero min_views, max_views or age_limit, or reject_live returns InvalidInput
with a fixed message. include_ads has no effect because no item is marked as
an advertisement. Otherwise return items unchanged."""
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    request = _cott_validate_abi(request, VideoFilterRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((((((((len((request).date_after) > 0) or (len((request).date_before) > 0)) or (len((request).match_filter) > 0)) or ((request).min_views > 0)) or ((request).max_views > 0)) or ((request).age_limit > 0)) or (request).reject_live)), "real.yt_dlp.filter_video", "error:3:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":30085,"end_column":229,"end_line":808,"start_byte":29861,"start_column":5,"start_line":808}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/filter_video.py", "36daf2581b16f3e73c8c343cb8760ce9d0fcc0395b0ec9788c01a33e9544a6fc", "filter_video", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.filter_video")
        _result = _implementation(items, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.filter_video"
        if _error.span is None:
            _error.span = {"end_byte":30103,"end_column":1,"end_line":812,"start_byte":29188,"start_column":1,"start_line":792}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.filter_video", phase="implementation-call", span={"end_byte":30103,"end_column":1,"end_line":812,"start_byte":29188,"start_column":1,"start_line":792}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.filter_video", phase="implementation-call", span={"end_byte":30103,"end_column":1,"end_line":812,"start_byte":29188,"start_column":1,"start_line":792}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[MediaItem], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.filter_video", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.filter_video", phase="error", span={"end_byte":30103,"end_column":1,"end_line":812,"start_byte":29188,"start_column":1,"start_line":792}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.filter_video", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.filter_video", _expected_error_clause)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return (_cott_contract_condition(((selected == items)), "real.yt_dlp.filter_video", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.filter_video", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.filter_video", clause="ensures:1", phase="ensures", span={"end_byte":29835,"end_column":53,"end_line":805,"start_byte":29787,"start_column":5,"start_line":805}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[MediaItem], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def filter_formats(formats: CottList[FormatDescriptor], request: FormatRequest) -> Result[CottList[FormatDescriptor], MediaError]:
    """Keep, unchanged and in input order, each format whose file_size is at least
min_file_size and, when max_file_size is nonzero, at most max_file_size, and
that matches containers. An empty containers list matches every format;
otherwise a format matches when any listed container matches it: Any always,
Video when has_video, Audio when has_audio, and Best or Worst when the
format's own container is that value. selector, sort_fields,
merge_output_format and prefer_free_formats do not filter. A nonzero
max_file_size below min_file_size returns InvalidInput with a fixed message;
an empty result returns FormatUnavailable(selector=request.selector)."""
    formats = _cott_validate_abi(formats, CottList[FormatDescriptor], path="$.formats")
    request = _cott_validate_abi(request, FormatRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((((request).max_file_size > 0) and ((request).min_file_size > (request).max_file_size))), "real.yt_dlp.filter_formats", "error:3:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":31239,"end_column":117,"end_line":831,"start_byte":31127,"start_column":5,"start_line":831}
        _expected_error_clause = "error:3"
    if _expected_error is None and (_cott_contract_condition(((len(formats) == 0)), "real.yt_dlp.filter_formats", "error:4:condition")):
        _expected_error = MediaError_FormatUnavailable
        _expected_error_span = {"end_byte":31300,"end_column":61,"end_line":832,"start_byte":31244,"start_column":5,"start_line":832}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/filter_formats.py", "131e478259cd38f291ed163df9adf0f6448dc1f5d76197f425e828fd6d653742", "filter_formats", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.filter_formats")
        _result = _implementation(formats, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.filter_formats"
        if _error.span is None:
            _error.span = {"end_byte":31357,"end_column":1,"end_line":837,"start_byte":30103,"start_column":1,"start_line":812}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.filter_formats", phase="implementation-call", span={"end_byte":31357,"end_column":1,"end_line":837,"start_byte":30103,"start_column":1,"start_line":812}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.filter_formats", phase="implementation-call", span={"end_byte":31357,"end_column":1,"end_line":837,"start_byte":30103,"start_column":1,"start_line":812}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[FormatDescriptor], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.filter_formats", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_FormatUnavailable,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.filter_formats", phase="error", span={"end_byte":31357,"end_column":1,"end_line":837,"start_byte":30103,"start_column":1,"start_line":812}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.filter_formats", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.filter_formats", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_FormatUnavailable:
        _cott_contract_condition(True, "real.yt_dlp.filter_formats", "error:5")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            selected = _cott_match_value.value
            return (_cott_contract_condition((((len(selected) > 0) and (len(selected) <= len(formats)))), "real.yt_dlp.filter_formats", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.filter_formats", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.filter_formats", clause="ensures:1", phase="ensures", span={"end_byte":31026,"end_column":84,"end_line":828,"start_byte":30947,"start_column":5,"start_line":828}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is MediaError_FormatUnavailable and True:
            selector = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((selector == (request).selector)), "real.yt_dlp.filter_formats", "ensures:2"))
        _cott_contract_condition((False), "real.yt_dlp.filter_formats", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.filter_formats", clause="ensures:2", phase="ensures", span={"end_byte":31121,"end_column":95,"end_line":829,"start_byte":31031,"start_column":5,"start_line":829}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[FormatDescriptor], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def sort_formats(formats: CottList[FormatDescriptor], fields: CottList[str]) -> CottList[FormatDescriptor]:
    """Stable sort, best first. fields names sort keys in priority order: "res"
(video_height), "abr" (audio_bitrate) and "size" (file_size), each compared
in descending order. Unknown and repeated names are ignored. Formats equal on
every recognized key keep their input order, so without a recognized key the
input order is returned unchanged."""
    formats = _cott_validate_abi(formats, CottList[FormatDescriptor], path="$.formats")
    fields = _cott_validate_abi(fields, CottList[str], path="$.fields")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/sort_formats.py", "6a49089a64f0561b9aafa382d439e9b1ef977e2ed6aa8db17c76f705b28ee3d3", "sort_formats", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.sort_formats")
        _result = _implementation(formats, fields)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.sort_formats"
        if _error.span is None:
            _error.span = {"end_byte":31938,"end_column":1,"end_line":851,"start_byte":31357,"start_column":1,"start_line":837}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.sort_formats", phase="implementation-call", span={"end_byte":31938,"end_column":1,"end_line":851,"start_byte":31357,"start_column":1,"start_line":837}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.sort_formats", phase="implementation-call", span={"end_byte":31938,"end_column":1,"end_line":851,"start_byte":31357,"start_column":1,"start_line":837}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[FormatDescriptor], path="$.return")
    if not (_cott_contract_condition(((len(_result) == len(formats))), "real.yt_dlp.sort_formats", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.sort_formats", clause="ensures:1", phase="ensures", span={"end_byte":31869,"end_column":38,"end_line":846,"start_byte":31836,"start_column":5,"start_line":846}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (len(fields) == 0)) or (_result == formats))), "real.yt_dlp.sort_formats", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.sort_formats", clause="ensures:2", phase="ensures", span={"end_byte":31920,"end_column":51,"end_line":847,"start_byte":31874,"start_column":5,"start_line":847}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[FormatDescriptor], path="$.return", validator=_cott_validate_abi)
    return _result

def select_subtitles(item: MediaItem, request: SubtitleRequest) -> Result[CottList[str], MediaError]:
    """Plan subtitle languages. This does not fetch or verify tracks: MediaItem
carries no subtitle information, so item does not affect the plan. None
returns an empty plan. Manual, Automatic and All return request.languages in
request order, keeping duplicates; an empty languages list or an empty
language code returns SubtitleUnavailable(language="")."""
    item = _cott_validate_abi(item, MediaItem, path="$.item")
    request = _cott_validate_abi(request, SubtitleRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((((request).mode != SubtitleMode_None()) and (len((request).languages) == 0))), "real.yt_dlp.select_subtitles", "error:4:condition")):
        _expected_error = MediaError_SubtitleUnavailable
        _expected_error_span = {"end_byte":32821,"end_column":113,"end_line":864,"start_byte":32713,"start_column":5,"start_line":864}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/select_subtitles.py", "082180e71338d8404f43603ac27eb7550440c719f411c2a85dec6068fc740ad7", "select_subtitles", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.select_subtitles")
        _result = _implementation(item, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.select_subtitles"
        if _error.span is None:
            _error.span = {"end_byte":32880,"end_column":1,"end_line":869,"start_byte":31938,"start_column":1,"start_line":851}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.select_subtitles", phase="implementation-call", span={"end_byte":32880,"end_column":1,"end_line":869,"start_byte":31938,"start_column":1,"start_line":851}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.select_subtitles", phase="implementation-call", span={"end_byte":32880,"end_column":1,"end_line":869,"start_byte":31938,"start_column":1,"start_line":851}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.select_subtitles", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_SubtitleUnavailable,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.select_subtitles", phase="error", span={"end_byte":32880,"end_column":1,"end_line":869,"start_byte":31938,"start_column":1,"start_line":851}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.select_subtitles", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.select_subtitles", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_SubtitleUnavailable:
        _cott_contract_condition(True, "real.yt_dlp.select_subtitles", "error:5")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            subtitles = _cott_match_value.value
            return (_cott_contract_condition((((not ((request).mode == SubtitleMode_None())) or (len(subtitles) == 0))), "real.yt_dlp.select_subtitles", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.select_subtitles", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.select_subtitles", clause="ensures:1", phase="ensures", span={"end_byte":32518,"end_column":94,"end_line":860,"start_byte":32429,"start_column":5,"start_line":860}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            subtitles = _cott_match_value.value
            return (_cott_contract_condition((((not ((request).mode != SubtitleMode_None())) or (subtitles == (request).languages))), "real.yt_dlp.select_subtitles", "ensures:2"))
        _cott_contract_condition((False), "real.yt_dlp.select_subtitles", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.select_subtitles", clause="ensures:2", phase="ensures", span={"end_byte":32624,"end_column":106,"end_line":861,"start_byte":32523,"start_column":5,"start_line":861}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is MediaError_SubtitleUnavailable and True:
            language = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((language == "")), "real.yt_dlp.select_subtitles", "ensures:3"))
        _cott_contract_condition((False), "real.yt_dlp.select_subtitles", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.select_subtitles", clause="ensures:3", phase="ensures", span={"end_byte":32707,"end_column":83,"end_line":862,"start_byte":32629,"start_column":5,"start_line":862}, expected="true", actual="false")
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
            _error.span = {"end_byte":33470,"end_column":1,"end_line":881,"start_byte":32880,"start_column":1,"start_line":869}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_thumbnails", phase="implementation-call", span={"end_byte":33470,"end_column":1,"end_line":881,"start_byte":32880,"start_column":1,"start_line":869}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_thumbnails", phase="implementation-call", span={"end_byte":33470,"end_column":1,"end_line":881,"start_byte":32880,"start_column":1,"start_line":869}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
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
            _error.span = {"end_byte":33969,"end_column":1,"end_line":892,"start_byte":33470,"start_column":1,"start_line":881}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_metadata", phase="implementation-call", span={"end_byte":33969,"end_column":1,"end_line":892,"start_byte":33470,"start_column":1,"start_line":881}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_metadata", phase="implementation-call", span={"end_byte":33969,"end_column":1,"end_line":892,"start_byte":33470,"start_column":1,"start_line":881}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=_cott_validate_abi)
    return _result

def render_output_path(item: MediaItem, template: str, missing_placeholder: str) -> Result[str, MediaError]:
    """Render an output template in this subset of yt-dlp's syntax. "%%" renders
"%". "%(NAME)s" renders item.id, item.title or item.ext for NAME id, title or
ext, the decimal playlist_index for playlist_index, and missing_placeholder
for any other NAME. "%(playlist_index)d" also renders the decimal index.
Other text is copied unchanged, and values are inserted verbatim: path
sanitization belongs to resolve_output_path. An empty template, a "%" that
starts none of these forms, an empty or unterminated NAME, a NAME containing
"%" or "(", a conversion other than s or d, and d with a NAME other than
playlist_index return InvalidTemplate."""
    item = _cott_validate_abi(item, MediaItem, path="$.item")
    template = _cott_validate_abi(template, str, path="$.template")
    missing_placeholder = _cott_validate_abi(missing_placeholder, str, path="$.missing_placeholder")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((len(template) == 0)), "real.yt_dlp.render_output_path", "error:2:condition")):
        _expected_error = MediaError_InvalidTemplate
        _expected_error_span = {"end_byte":34926,"end_column":60,"end_line":911,"start_byte":34871,"start_column":5,"start_line":911}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/render_output_path.py", "ea4739f6cb6c287a264ba280584236998041c545fabd45b8bdfc7df0349a3040", "render_output_path", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.render_output_path")
        _result = _implementation(item, template, missing_placeholder)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.render_output_path"
        if _error.span is None:
            _error.span = {"end_byte":34981,"end_column":1,"end_line":916,"start_byte":33969,"start_column":1,"start_line":892}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.render_output_path", phase="implementation-call", span={"end_byte":34981,"end_column":1,"end_line":916,"start_byte":33969,"start_column":1,"start_line":892}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.render_output_path", phase="implementation-call", span={"end_byte":34981,"end_column":1,"end_line":916,"start_byte":33969,"start_column":1,"start_line":892}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.render_output_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidTemplate,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.render_output_path", phase="error", span={"end_byte":34981,"end_column":1,"end_line":916,"start_byte":33969,"start_column":1,"start_line":892}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.render_output_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.render_output_path", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidTemplate:
        _cott_contract_condition(True, "real.yt_dlp.render_output_path", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            path = _cott_match_value.value
            return (_cott_contract_condition((((not (not ("%" in template))) or (path == template))), "real.yt_dlp.render_output_path", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.render_output_path", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.render_output_path", clause="ensures:1", phase="ensures", span={"end_byte":34865,"end_column":81,"end_line":909,"start_byte":34789,"start_column":5,"start_line":909}, expected="true", actual="false")
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
            _error.span = {"end_byte":36747,"end_column":1,"end_line":947,"start_byte":34981,"start_column":1,"start_line":916}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.resolve_output_path", phase="implementation-call", span={"end_byte":36747,"end_column":1,"end_line":947,"start_byte":34981,"start_column":1,"start_line":916}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.resolve_output_path", phase="implementation-call", span={"end_byte":36747,"end_column":1,"end_line":947,"start_byte":34981,"start_column":1,"start_line":916}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Path, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.resolve_output_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidTemplate, MediaError_PathFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.resolve_output_path", phase="error", span={"end_byte":36747,"end_column":1,"end_line":947,"start_byte":34981,"start_column":1,"start_line":916}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
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
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_output_path", clause="ensures:1", phase="ensures", span={"end_byte":36658,"end_column":52,"end_line":940,"start_byte":36611,"start_column":5,"start_line":940}, expected="true", actual="false")
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
            _error.span = {"end_byte":37669,"end_column":1,"end_line":966,"start_byte":36747,"start_column":1,"start_line":947}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.read_download_archive", phase="implementation-call", span={"end_byte":37669,"end_column":1,"end_line":966,"start_byte":36747,"start_column":1,"start_line":947}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.read_download_archive", phase="implementation-call", span={"end_byte":37669,"end_column":1,"end_line":966,"start_byte":36747,"start_column":1,"start_line":947}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.read_download_archive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_ArchiveFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.read_download_archive", phase="error", span={"end_byte":37669,"end_column":1,"end_line":966,"start_byte":36747,"start_column":1,"start_line":947}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
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
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.read_download_archive", clause="ensures:1", phase="ensures", span={"end_byte":37605,"end_column":56,"end_line":960,"start_byte":37554,"start_column":5,"start_line":960}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def plan_downloads(items: CottList[MediaItem], archive: CottList[str], break_on_existing: bool) -> DownloadPlan:
    """archive holds plain media ids as returned by read_download_archive. An item
is already downloaded when its id equals an archive entry exactly. Without
break_on_existing, the plan keeps every other item unchanged, in order and
with duplicates, and stopped_on_archive is false. With break_on_existing, the
plan holds the items before the first already-downloaded item and
stopped_on_archive is true; when no item is already downloaded, the plan
holds every item and stopped_on_archive is false."""
    items = _cott_validate_abi(items, CottList[MediaItem], path="$.items")
    archive = _cott_validate_abi(archive, CottList[str], path="$.archive")
    break_on_existing = _cott_validate_abi(break_on_existing, bool, path="$.break_on_existing")
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/plan_downloads.py", "bf177f14d4cd6bdb09785bdff4eab1c2e3185cc1f82949aece57507b771ff2e5", "plan_downloads", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.plan_downloads")
        _result = _implementation(items, archive, break_on_existing)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.plan_downloads"
        if _error.span is None:
            _error.span = {"end_byte":38542,"end_column":1,"end_line":987,"start_byte":37669,"start_column":1,"start_line":966}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_downloads", phase="implementation-call", span={"end_byte":38542,"end_column":1,"end_line":987,"start_byte":37669,"start_column":1,"start_line":966}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_downloads", phase="implementation-call", span={"end_byte":38542,"end_column":1,"end_line":987,"start_byte":37669,"start_column":1,"start_line":966}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, DownloadPlan, path="$.return")
    if not (_cott_contract_condition(((len((_result).items) <= len(items))), "real.yt_dlp.plan_downloads", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.plan_downloads", clause="ensures:1", phase="ensures", span={"end_byte":38371,"end_column":42,"end_line":981,"start_byte":38334,"start_column":5,"start_line":981}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (len(archive) == 0)) or (((_result).items == items) and (not (_result).stopped_on_archive)))), "real.yt_dlp.plan_downloads", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.plan_downloads", clause="ensures:2", phase="ensures", span={"end_byte":38463,"end_column":92,"end_line":982,"start_byte":38376,"start_column":5,"start_line":982}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (_result).stopped_on_archive) or break_on_existing)), "real.yt_dlp.plan_downloads", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.plan_downloads", clause="ensures:3", phase="ensures", span={"end_byte":38524,"end_column":61,"end_line":983,"start_byte":38468,"start_column":5,"start_line":983}, expected="true", actual="false")
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
        _implementation = _cott_load("_cott_impl/real/yt_dlp/write_download_archive.py", "823aeed5aa224b6483e9f6a043b7f9e94352df5d5720c65575f3b72fcd46c131", "write_download_archive", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.write_download_archive")
        _result = _implementation(path, items)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.write_download_archive"
        if _error.span is None:
            _error.span = {"end_byte":40040,"end_column":1,"end_line":1013,"start_byte":38542,"start_column":1,"start_line":987}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.write_download_archive", phase="implementation-call", span={"end_byte":40040,"end_column":1,"end_line":1013,"start_byte":38542,"start_column":1,"start_line":987}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.write_download_archive", phase="implementation-call", span={"end_byte":40040,"end_column":1,"end_line":1013,"start_byte":38542,"start_column":1,"start_line":987}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.write_download_archive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_ArchiveFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.write_download_archive", phase="error", span={"end_byte":40040,"end_column":1,"end_line":1013,"start_byte":38542,"start_column":1,"start_line":987}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.write_download_archive", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.write_download_archive", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_ArchiveFailure:
        _cott_contract_condition(True, "real.yt_dlp.write_download_archive", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            saved = _cott_match_value.value
            return (_cott_contract_condition(((saved == UNIT)), "real.yt_dlp.write_download_archive", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.write_download_archive", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.write_download_archive", clause="ensures:1", phase="ensures", span={"end_byte":39894,"end_column":44,"end_line":1006,"start_byte":39855,"start_column":5,"start_line":1006}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is MediaError_ArchiveFailure and True and True:
            archive = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((archive == path)), "real.yt_dlp.write_download_archive", "ensures:2"))
        _cott_contract_condition((False), "real.yt_dlp.write_download_archive", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.write_download_archive", clause="ensures:2", phase="ensures", span={"end_byte":39975,"end_column":81,"end_line":1007,"start_byte":39899,"start_column":5,"start_line":1007}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def plan_fragments(request: TransferRequest, policy: FragmentPolicy) -> Result[CottList[TransferRequest], MediaError]:
    """TransferRequest has no byte-range field, so this client transfers each media
item as a single fragment: return a list holding request unchanged. A zero
max_bytes, concurrent_fragments or buffer_size returns InvalidInput with a
fixed message. chunk_size, rate limit, retry, continue and part-file settings
apply in transfer_fragments, not here."""
    request = _cott_validate_abi(request, TransferRequest, path="$.request")
    policy = _cott_validate_abi(policy, FragmentPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((((request).max_bytes == 0) or ((policy).concurrent_fragments == 0)) or ((policy).buffer_size == 0))), "real.yt_dlp.plan_fragments", "error:3:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":40752,"end_column":127,"end_line":1028,"start_byte":40630,"start_column":5,"start_line":1028}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/plan_fragments.py", "7419da140a606e1ae448324d51f2d221bcbe56704643f6ed926e515196be9b66", "plan_fragments", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.plan_fragments")
        _result = _implementation(request, policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.plan_fragments"
        if _error.span is None:
            _error.span = {"end_byte":40770,"end_column":1,"end_line":1032,"start_byte":40040,"start_column":1,"start_line":1013}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_fragments", phase="implementation-call", span={"end_byte":40770,"end_column":1,"end_line":1032,"start_byte":40040,"start_column":1,"start_line":1013}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_fragments", phase="implementation-call", span={"end_byte":40770,"end_column":1,"end_line":1032,"start_byte":40040,"start_column":1,"start_line":1013}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[TransferRequest], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.plan_fragments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.plan_fragments", phase="error", span={"end_byte":40770,"end_column":1,"end_line":1032,"start_byte":40040,"start_column":1,"start_line":1013}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.plan_fragments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.plan_fragments", _expected_error_clause)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            fragments = _cott_match_value.value
            return (_cott_contract_condition(((len(fragments) == 1)), "real.yt_dlp.plan_fragments", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.plan_fragments", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.plan_fragments", clause="ensures:1", phase="ensures", span={"end_byte":40604,"end_column":55,"end_line":1025,"start_byte":40554,"start_column":5,"start_line":1025}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[TransferRequest], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def transfer_media(request: TransferRequest) -> Result[TransferReceipt, MediaError]:
    """Transfer one media resource. A simulate request performs no network or file
access and returns bytes_written 0. Otherwise send one HTTP GET with
certificate-verifying TLS, following at most five redirects, and stream the
body into an exclusive temporary file in destination's directory, creating
missing parent directories; on success atomically replace destination with
it. Reject a declared Content-Length above max_bytes, and stop at the first
byte beyond max_bytes, with SizeLimit. A non-2xx final status returns
HttpStatus(status); DNS, connection, TLS, timeout, redirect and read failures
return NetworkFailure; local directory, open, write and replace failures
return OutputFailure. Every failure removes the temporary file and leaves an
existing destination untouched. Messages are fixed descriptive text without
response bodies or query strings."""
    request = _cott_validate_abi(request, TransferRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((((request).max_bytes == 0)), "real.yt_dlp.transfer_media", "error:6:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":42210,"end_column":62,"end_line":1054,"start_byte":42153,"start_column":5,"start_line":1054}
        _expected_error_clause = "error:6"
    if _expected_error is None and (_cott_contract_condition(((not (_cott_starts_with((request).url, "http://") or _cott_starts_with((request).url, "https://")))), "real.yt_dlp.transfer_media", "error:7:condition")):
        _expected_error = MediaError_UnsupportedUrl
        _expected_error_span = {"end_byte":42333,"end_column":123,"end_line":1055,"start_byte":42215,"start_column":5,"start_line":1055}
        _expected_error_clause = "error:7"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/transfer_media.py", "ef10faeabd760a4f28d3bbf4328d0b3c91722a60de4c452e71a406e4c3cf981f", "transfer_media", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.transfer_media")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.transfer_media"
        if _error.span is None:
            _error.span = {"end_byte":42540,"end_column":1,"end_line":1064,"start_byte":40770,"start_column":1,"start_line":1032}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.transfer_media", phase="implementation-call", span={"end_byte":42540,"end_column":1,"end_line":1064,"start_byte":40770,"start_column":1,"start_line":1032}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.transfer_media", phase="implementation-call", span={"end_byte":42540,"end_column":1,"end_line":1064,"start_byte":40770,"start_column":1,"start_line":1032}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TransferReceipt, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.transfer_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_UnsupportedUrl, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_SizeLimit,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.transfer_media", phase="error", span={"end_byte":42540,"end_column":1,"end_line":1064,"start_byte":40770,"start_column":1,"start_line":1032}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.transfer_media", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.transfer_media", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_UnsupportedUrl:
        _cott_contract_condition(True, "real.yt_dlp.transfer_media", "error:8")
    if type(_result) is Err and type(_result.error) is MediaError_HttpStatus:
        _cott_contract_condition(True, "real.yt_dlp.transfer_media", "error:9")
    if type(_result) is Err and type(_result.error) is MediaError_NetworkFailure:
        _cott_contract_condition(True, "real.yt_dlp.transfer_media", "error:10")
    if type(_result) is Err and type(_result.error) is MediaError_OutputFailure:
        _cott_contract_condition(True, "real.yt_dlp.transfer_media", "error:11")
    if type(_result) is Err and type(_result.error) is MediaError_SizeLimit:
        _cott_contract_condition(True, "real.yt_dlp.transfer_media", "error:12")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (_cott_contract_condition((((receipt).url == (request).url)), "real.yt_dlp.transfer_media", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.transfer_media", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:1", phase="ensures", span={"end_byte":41838,"end_column":61,"end_line":1048,"start_byte":41782,"start_column":5,"start_line":1048}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (_cott_contract_condition((((receipt).destination == (request).destination)), "real.yt_dlp.transfer_media", "ensures:2"))
        _cott_contract_condition((False), "real.yt_dlp.transfer_media", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:2", phase="ensures", span={"end_byte":41915,"end_column":77,"end_line":1049,"start_byte":41843,"start_column":5,"start_line":1049}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (_cott_contract_condition((((receipt).bytes_written <= (request).max_bytes)), "real.yt_dlp.transfer_media", "ensures:3"))
        _cott_contract_condition((False), "real.yt_dlp.transfer_media", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:3", phase="ensures", span={"end_byte":41992,"end_column":77,"end_line":1050,"start_byte":41920,"start_column":5,"start_line":1050}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (_cott_contract_condition((((receipt).simulated == (request).simulate)), "real.yt_dlp.transfer_media", "ensures:4"))
        _cott_contract_condition((False), "real.yt_dlp.transfer_media", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:4", phase="ensures", span={"end_byte":42064,"end_column":72,"end_line":1051,"start_byte":41997,"start_column":5,"start_line":1051}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipt = _cott_match_value.value
            return (_cott_contract_condition((((not (request).simulate) or ((receipt).bytes_written == 0))), "real.yt_dlp.transfer_media", "ensures:5"))
        _cott_contract_condition((False), "real.yt_dlp.transfer_media", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_media", clause="ensures:5", phase="ensures", span={"end_byte":42147,"end_column":83,"end_line":1052,"start_byte":42069,"start_column":5,"start_line":1052}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[TransferReceipt, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def transfer_fragments(fragments: CottList[TransferRequest], policy: FragmentPolicy) -> Result[CottList[TransferReceipt], MediaError]:
    """Download each fragment in order and return one receipt per fragment, in
order. Before any transfer, a zero concurrent_fragments or buffer_size, a
fragment URL that is not an absolute http or https URL with a host, a
destination without a file name, and two fragments with the same destination
return InvalidInput. A simulate fragment performs no I/O and yields a receipt
with bytes_written 0 and simulated true.
Otherwise send one HTTP GET with certificate-verifying TLS, following at most
five redirects, and stream the body in reads of at most buffer_size bytes
(and at most chunk_size when nonzero), sleeping as needed to stay under a
nonzero rate_limit_bytes_per_second. With part_files the body goes to
destination + ".part", which is renamed over destination after the whole body
arrived; otherwise it goes to destination directly. With continue_download an
existing work file is resumed with a Range request, and a 416 reply means it
is already complete; otherwise the work file is truncated. Open files without
following symlinks and fsync them before the rename.
A declared Content-Length or received byte count above max_bytes is
SizeLimit. A non-2xx final status other than 206 for a resumed transfer is
HttpStatus(status); a short body and transport failures are NetworkFailure.
NetworkFailure and 429 or 5xx statuses are retried with exponential backoff
up to retries times for a single fragment and fragment_retries times for
several; when retries run out the result is RetryExhausted(attempts=attempts
made), except that zero allowed retries return the original error. Local
open and rename failures are retried up to file_access_retries times, then
OutputFailure, as are write and fsync failures. A successful receipt holds
the fragment's url and destination, the destination's final byte size as
bytes_written, and simulated false. Messages are fixed descriptive text
without response bodies or query strings."""
    fragments = _cott_validate_abi(fragments, CottList[TransferRequest], path="$.fragments")
    policy = _cott_validate_abi(policy, FragmentPolicy, path="$.policy")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition(((((policy).concurrent_fragments == 0) or ((policy).buffer_size == 0))), "real.yt_dlp.transfer_fragments", "error:2:condition")):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":44897,"end_column":99,"end_line":1100,"start_byte":44803,"start_column":5,"start_line":1100}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/transfer_fragments.py", "a5a600957a425147feec470ef57a9163a0f7503379768dd9e6661eee22276698", "transfer_fragments", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.transfer_fragments")
        _result = _implementation(fragments, policy)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.transfer_fragments"
        if _error.span is None:
            _error.span = {"end_byte":45145,"end_column":1,"end_line":1110,"start_byte":42540,"start_column":1,"start_line":1064}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.transfer_fragments", phase="implementation-call", span={"end_byte":45145,"end_column":1,"end_line":1110,"start_byte":42540,"start_column":1,"start_line":1064}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.transfer_fragments", phase="implementation-call", span={"end_byte":45145,"end_column":1,"end_line":1110,"start_byte":42540,"start_column":1,"start_line":1064}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[TransferReceipt], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.transfer_fragments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_RetryExhausted, MediaError_SizeLimit,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.transfer_fragments", phase="error", span={"end_byte":45145,"end_column":1,"end_line":1110,"start_byte":42540,"start_column":1,"start_line":1064}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.transfer_fragments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.transfer_fragments", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.transfer_fragments", "error:3")
    if type(_result) is Err and type(_result.error) is MediaError_HttpStatus:
        _cott_contract_condition(True, "real.yt_dlp.transfer_fragments", "error:4")
    if type(_result) is Err and type(_result.error) is MediaError_NetworkFailure:
        _cott_contract_condition(True, "real.yt_dlp.transfer_fragments", "error:5")
    if type(_result) is Err and type(_result.error) is MediaError_OutputFailure:
        _cott_contract_condition(True, "real.yt_dlp.transfer_fragments", "error:6")
    if type(_result) is Err and type(_result.error) is MediaError_RetryExhausted:
        _cott_contract_condition(True, "real.yt_dlp.transfer_fragments", "error:7")
    if type(_result) is Err and type(_result.error) is MediaError_SizeLimit:
        _cott_contract_condition(True, "real.yt_dlp.transfer_fragments", "error:8")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            receipts = _cott_match_value.value
            return (_cott_contract_condition(((len(receipts) == len(fragments))), "real.yt_dlp.transfer_fragments", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.transfer_fragments", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.transfer_fragments", clause="ensures:1", phase="ensures", span={"end_byte":44797,"end_column":65,"end_line":1098,"start_byte":44737,"start_column":5,"start_line":1098}, expected="true", actual="false")
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
        _implementation = _cott_load("_cott_impl/real/yt_dlp/render_items.py", "1f788d92d60ad3cea529e983b7695c852bda037f606ee5f67bf66a40bb6c2053", "render_items", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.render_items")
        _result = _implementation(items, mode)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.render_items"
        if _error.span is None:
            _error.span = {"end_byte":45722,"end_column":1,"end_line":1122,"start_byte":45145,"start_column":1,"start_line":1110}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.render_items", phase="implementation-call", span={"end_byte":45722,"end_column":1,"end_line":1122,"start_byte":45145,"start_column":1,"start_line":1110}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.render_items", phase="implementation-call", span={"end_byte":45722,"end_column":1,"end_line":1122,"start_byte":45145,"start_column":1,"start_line":1110}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
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
    def _cott_match_error_3() -> bool:
        _cott_match_value = (request).external_tool
        if type(_cott_match_value) is Nothing:
            return (_cott_contract_condition(((len((request).kinds) > 0)), "real.yt_dlp.plan_post_processing", "error:3:condition"))
        _cott_contract_condition((False), "real.yt_dlp.plan_post_processing", "error:3:applicable")
        return False
    if _expected_error is None and (_cott_match_error_3()):
        _expected_error = MediaError_ExternalToolMissing
        _expected_error_span = {"end_byte":47736,"end_column":120,"end_line":1152,"start_byte":47621,"start_column":5,"start_line":1152}
        _expected_error_clause = "error:3"
    def _cott_match_error_4() -> bool:
        _cott_match_value = (request).external_tool
        if type(_cott_match_value) is Some and True:
            tool = _cott_match_value.value
            return (_cott_contract_condition((((len((request).kinds) > 0) and (len((tool).executable) == 0))), "real.yt_dlp.plan_post_processing", "error:4:condition"))
        _cott_contract_condition((False), "real.yt_dlp.plan_post_processing", "error:4:applicable")
        return False
    if _expected_error is None and (_cott_match_error_4()):
        _expected_error = MediaError_ExternalToolMissing
        _expected_error_span = {"end_byte":47888,"end_column":152,"end_line":1153,"start_byte":47741,"start_column":5,"start_line":1153}
        _expected_error_clause = "error:4"
    def _cott_match_error_5() -> bool:
        _cott_match_value = (request).external_tool
        if type(_cott_match_value) is Some and True:
            tool = _cott_match_value.value
            return (_cott_contract_condition((((len((request).kinds) > 0) and ((tool).timeout_ms == 0))), "real.yt_dlp.plan_post_processing", "error:5:condition"))
        _cott_contract_condition((False), "real.yt_dlp.plan_post_processing", "error:5:applicable")
        return False
    if _expected_error is None and (_cott_match_error_5()):
        _expected_error = MediaError_InvalidInput
        _expected_error_span = {"end_byte":48029,"end_column":141,"end_line":1154,"start_byte":47893,"start_column":5,"start_line":1154}
        _expected_error_clause = "error:5"
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/plan_post_processing.py", "9cc615b451e8a4998c70ea91f20c2337be39c5bea659b6cd19e07264f811ec69", "plan_post_processing", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.plan_post_processing")
        _result = _implementation(item, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.plan_post_processing"
        if _error.span is None:
            _error.span = {"end_byte":48081,"end_column":1,"end_line":1159,"start_byte":45722,"start_column":1,"start_line":1122}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.plan_post_processing", phase="implementation-call", span={"end_byte":48081,"end_column":1,"end_line":1159,"start_byte":45722,"start_column":1,"start_line":1122}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.plan_post_processing", phase="implementation-call", span={"end_byte":48081,"end_column":1,"end_line":1159,"start_byte":45722,"start_column":1,"start_line":1122}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[ExternalToolRequest], MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.plan_post_processing", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidInput,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.plan_post_processing", phase="error", span={"end_byte":48081,"end_column":1,"end_line":1159,"start_byte":45722,"start_column":1,"start_line":1122}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.plan_post_processing", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.plan_post_processing", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.plan_post_processing", "error:6")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            planned = _cott_match_value.value
            return (_cott_contract_condition(((len(planned) == len((request).kinds))), "real.yt_dlp.plan_post_processing", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.plan_post_processing", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.plan_post_processing", clause="ensures:1", phase="ensures", span={"end_byte":47520,"end_column":67,"end_line":1149,"start_byte":47458,"start_column":5,"start_line":1149}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is MediaError_ExternalToolMissing and True:
            name = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition((((name == "ffmpeg") or (name == ""))), "real.yt_dlp.plan_post_processing", "ensures:2"))
        _cott_contract_condition((False), "real.yt_dlp.plan_post_processing", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.plan_post_processing", clause="ensures:2", phase="ensures", span={"end_byte":47615,"end_column":95,"end_line":1150,"start_byte":47525,"start_column":5,"start_line":1150}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[ExternalToolRequest], MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def run_post_processing(requests: CottList[ExternalToolRequest]) -> Result[Unit, MediaError]:
    """Run each request in order, one at a time, and stop at the first failure.
An executable containing a path separator is used as given; otherwise it is
looked up on PATH. An empty, missing or non-executable executable returns
ExternalToolMissing(name=executable). Start the tool directly, never through
a shell, with its arguments verbatim, stdin closed and output discarded, and
wait at most timeout_ms milliseconds (zero means no limit). A missing or
nonregular input before starting, a timeout, a nonzero exit status and a
missing output afterwards return PostProcessFailed(name=executable,
message=a fixed descriptive category)."""
    requests = _cott_validate_abi(requests, CottList[ExternalToolRequest], path="$.requests")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/yt_dlp/run_post_processing.py", "06a262f88ba58f6b8b52230f914f00f3f262ddbf599a6ba00df43867c4ebd99d", "run_post_processing", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.run_post_processing")
        _result = _implementation(requests)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.run_post_processing"
        if _error.span is None:
            _error.span = {"end_byte":49129,"end_column":1,"end_line":1180,"start_byte":48081,"start_column":1,"start_line":1159}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.run_post_processing", phase="implementation-call", span={"end_byte":49129,"end_column":1,"end_line":1180,"start_byte":48081,"start_column":1,"start_line":1159}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.run_post_processing", phase="implementation-call", span={"end_byte":49129,"end_column":1,"end_line":1180,"start_byte":48081,"start_column":1,"start_line":1159}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.run_post_processing", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_ExternalToolMissing, MediaError_PostProcessFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.run_post_processing", phase="error", span={"end_byte":49129,"end_column":1,"end_line":1180,"start_byte":48081,"start_column":1,"start_line":1159}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.run_post_processing", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.run_post_processing", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_ExternalToolMissing:
        _cott_contract_condition(True, "real.yt_dlp.run_post_processing", "error:2")
    if type(_result) is Err and type(_result.error) is MediaError_PostProcessFailed:
        _cott_contract_condition(True, "real.yt_dlp.run_post_processing", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            completed = _cott_match_value.value
            return (_cott_contract_condition(((completed == UNIT)), "real.yt_dlp.run_post_processing", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.run_post_processing", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.run_post_processing", clause="ensures:1", phase="ensures", span={"end_byte":49009,"end_column":52,"end_line":1173,"start_byte":48962,"start_column":5,"start_line":1173}, expected="true", actual="false")
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
            _error.span = {"end_byte":50427,"end_column":1,"end_line":1201,"start_byte":49129,"start_column":1,"start_line":1180}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.resolve_update_repository", phase="implementation-call", span={"end_byte":50427,"end_column":1,"end_line":1201,"start_byte":49129,"start_column":1,"start_line":1180}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.resolve_update_repository", phase="implementation-call", span={"end_byte":50427,"end_column":1,"end_line":1201,"start_byte":49129,"start_column":1,"start_line":1180}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.resolve_update_repository", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_UpdateUnavailable,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.resolve_update_repository", phase="error", span={"end_byte":50427,"end_column":1,"end_line":1201,"start_byte":49129,"start_column":1,"start_line":1180}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.resolve_update_repository", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.resolve_update_repository", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_UpdateUnavailable:
        _cott_contract_condition(True, "real.yt_dlp.resolve_update_repository", "error:6")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            repository = _cott_match_value.value
            return (_cott_contract_condition((((((repository == "") or (repository == "yt-dlp/yt-dlp")) or (repository == "yt-dlp/yt-dlp-nightly-builds")) or (repository == "yt-dlp/yt-dlp-master-builds"))), "real.yt_dlp.resolve_update_repository", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.resolve_update_repository", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_update_repository", clause="ensures:1", phase="ensures", span={"end_byte":49957,"end_column":184,"end_line":1191,"start_byte":49778,"start_column":5,"start_line":1191}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            repository = _cott_match_value.value
            return (_cott_contract_condition((((not (policy == UpdatePolicy_Never())) or (repository == ""))), "real.yt_dlp.resolve_update_repository", "ensures:2"))
        _cott_contract_condition((False), "real.yt_dlp.resolve_update_repository", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_update_repository", clause="ensures:2", phase="ensures", span={"end_byte":50045,"end_column":88,"end_line":1192,"start_byte":49962,"start_column":5,"start_line":1192}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            repository = _cott_match_value.value
            return (_cott_contract_condition((((not (policy == UpdatePolicy_Nightly())) or (repository == "yt-dlp/yt-dlp-nightly-builds"))), "real.yt_dlp.resolve_update_repository", "ensures:3"))
        _cott_contract_condition((False), "real.yt_dlp.resolve_update_repository", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_update_repository", clause="ensures:3", phase="ensures", span={"end_byte":50163,"end_column":118,"end_line":1193,"start_byte":50050,"start_column":5,"start_line":1193}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            repository = _cott_match_value.value
            return (_cott_contract_condition((((not (policy == UpdatePolicy_Master())) or (repository == "yt-dlp/yt-dlp-master-builds"))), "real.yt_dlp.resolve_update_repository", "ensures:4"))
        _cott_contract_condition((False), "real.yt_dlp.resolve_update_repository", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_update_repository", clause="ensures:4", phase="ensures", span={"end_byte":50279,"end_column":116,"end_line":1194,"start_byte":50168,"start_column":5,"start_line":1194}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and True:
            return (_cott_contract_condition((((policy == UpdatePolicy_Check()) or (policy == UpdatePolicy_Apply()))), "real.yt_dlp.resolve_update_repository", "ensures:5"))
        _cott_contract_condition((False), "real.yt_dlp.resolve_update_repository", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.resolve_update_repository", clause="ensures:5", phase="ensures", span={"end_byte":50369,"end_column":90,"end_line":1195,"start_byte":50284,"start_column":5,"start_line":1195}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def apply_update(request: UpdateRequest) -> Result[UpdateOutcome, MediaError]:
    """Never returns Ok(Disabled) immediately without validating channel or target
and without network or filesystem access: updates are disabled, not
installed. Otherwise call
real.yt_dlp.resolve_update_repository(request.policy, request.channel).

Use only the selected official repository's latest release assets at fixed
HTTPS GitHub release URLs: `SHA2-256SUMS` and the platform-independent
`yt-dlp` zipimport executable documented by upstream. Stable is
yt-dlp/yt-dlp, nightly is yt-dlp/yt-dlp-nightly-builds, and master is
yt-dlp/yt-dlp-master-builds. Do not accept a repository, asset name, tag, or
URL from input. Use certificate- and hostname-verifying TLS, a finite timeout,
at most five redirects, and permit redirects only to github.com or
release-assets.githubusercontent.com over HTTPS. Send no credentials.
Perform HTTPS, SHA-256 and filesystem work in-process; never run a
subprocess, shell, package manager or other executable.

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
race; if the platform cannot provide those guarantees, including fsync and
same-directory atomic replacement, fail closed. A missing target represents
an available update. For an existing target, hash it incrementally without
following links; a digest equal to the release checksum means it is current.

Check performs the authenticated manifest fetch and target comparison above,
then returns Ok(Current) or Ok(Available). It never downloads the executable,
creates a temporary file, changes metadata, or replaces target.

Apply, Nightly, and Master return Ok(Current) without writing when target
already matches. Otherwise create an unpredictable exclusive no-follow
temporary regular file in target's directory, stream the bounded asset into
it while hashing, verify the digest, flush and fsync it, set its mode, then
atomically replace target within that same directory, fsync the directory
and return Ok(Installed). Preserve an existing target's ordinary rwx
permission bits while dropping special bits; use 0755 for a new target.
Recheck the target identity before commit, clean up the temporary leaf on
every pre-commit failure, and never move or truncate the old target before
verified replacement. Do not leave a partial target or follow a target
swapped to a symlink.

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
        _implementation = _cott_load("_cott_impl/real/yt_dlp/apply_update.py", "65f5696ac3c65fcec6ac8f99cc2de45e43b163dc1f43473c6cf717a96638ec53", "apply_update", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.apply_update")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.apply_update"
        if _error.span is None:
            _error.span = {"end_byte":55060,"end_column":1,"end_line":1273,"start_byte":50427,"start_column":1,"start_line":1201}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.apply_update", phase="implementation-call", span={"end_byte":55060,"end_column":1,"end_line":1273,"start_byte":50427,"start_column":1,"start_line":1201}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.apply_update", phase="implementation-call", span={"end_byte":55060,"end_column":1,"end_line":1273,"start_byte":50427,"start_column":1,"start_line":1201}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[UpdateOutcome, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.apply_update", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_UpdateUnavailable, MediaError_NetworkFailure, MediaError_OutputFailure,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.apply_update", phase="error", span={"end_byte":55060,"end_column":1,"end_line":1273,"start_byte":50427,"start_column":1,"start_line":1201}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.apply_update", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.apply_update", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_UpdateUnavailable:
        _cott_contract_condition(True, "real.yt_dlp.apply_update", "error:5")
    if type(_result) is Err and type(_result.error) is MediaError_NetworkFailure:
        _cott_contract_condition(True, "real.yt_dlp.apply_update", "error:6")
    if type(_result) is Err and type(_result.error) is MediaError_OutputFailure:
        _cott_contract_condition(True, "real.yt_dlp.apply_update", "error:7")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            outcome = _cott_match_value.value
            return (_cott_contract_condition((((not ((request).policy == UpdatePolicy_Never())) or (outcome == UpdateOutcome_Disabled()))), "real.yt_dlp.apply_update", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.apply_update", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.apply_update", clause="ensures:1", phase="ensures", span={"end_byte":54452,"end_column":110,"end_line":1262,"start_byte":54347,"start_column":5,"start_line":1262}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            outcome = _cott_match_value.value
            return (_cott_contract_condition((((not ((request).policy == UpdatePolicy_Check())) or ((outcome == UpdateOutcome_Current()) or (outcome == UpdateOutcome_Available())))), "real.yt_dlp.apply_update", "ensures:2"))
        _cott_contract_condition((False), "real.yt_dlp.apply_update", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.apply_update", clause="ensures:2", phase="ensures", span={"end_byte":54601,"end_column":149,"end_line":1263,"start_byte":54457,"start_column":5,"start_line":1263}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            outcome = _cott_match_value.value
            return (_cott_contract_condition((((not ((((request).policy == UpdatePolicy_Apply()) or ((request).policy == UpdatePolicy_Nightly())) or ((request).policy == UpdatePolicy_Master()))) or ((outcome == UpdateOutcome_Current()) or (outcome == UpdateOutcome_Installed())))), "real.yt_dlp.apply_update", "ensures:3"))
        _cott_contract_condition((False), "real.yt_dlp.apply_update", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.apply_update", clause="ensures:3", phase="ensures", span={"end_byte":54835,"end_column":234,"end_line":1264,"start_byte":54606,"start_column":5,"start_line":1264}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and True:
            return (_cott_contract_condition((((request).policy != UpdatePolicy_Never())), "real.yt_dlp.apply_update", "ensures:4"))
        _cott_contract_condition((False), "real.yt_dlp.apply_update", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.apply_update", clause="ensures:4", phase="ensures", span={"end_byte":54901,"end_column":66,"end_line":1265,"start_byte":54840,"start_column":5,"start_line":1265}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[UpdateOutcome, MediaError], path="$.return", validator=_cott_validate_abi)
    return _result

def execute(request: ExecutionRequest) -> Result[ExecutionReport, MediaError]:
    """Execute the direct-media pipeline and return its actual selected items,
download plan and rendered output, never an invented empty success.
Propagate each failing stage's declared MediaError unchanged and stop before
later stages. Do not perform effects outside these stages.

First call real.yt_dlp.apply_update(request.update); its UpdateOutcome is not
part of the report. Then call validate_network, select_geo_route on the
validated network, resolve_authentication and validate_workarounds on their
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
        _implementation = _cott_load("_cott_impl/real/yt_dlp/execute.py", "fe0eb71475b972bba5d262b08ace142358b35df1d6612aad3bcedb9b787ea437", "execute", expected_project_name="real-yt-dlp", expected_cott_symbol="real.yt_dlp.execute")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.yt_dlp.execute"
        if _error.span is None:
            _error.span = {"end_byte":59730,"end_column":1,"end_line":1358,"start_byte":55060,"start_column":1,"start_line":1273}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.yt_dlp.execute", phase="implementation-call", span={"end_byte":59730,"end_column":1,"end_line":1358,"start_byte":55060,"start_column":1,"start_line":1273}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.execute", phase="implementation-call", span={"end_byte":59730,"end_column":1,"end_line":1358,"start_byte":55060,"start_column":1,"start_line":1273}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ExecutionReport, MediaError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.yt_dlp.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (MediaError_InvalidConfig, MediaError_InvalidInput, MediaError_AuthenticationFailed, MediaError_BatchReadFailed, MediaError_InvalidShortcut, MediaError_CertificateFailure, MediaError_WorkaroundRejected, MediaError_LogFailure, MediaError_InvalidRange, MediaError_CookieFailure, MediaError_GeoRestricted, MediaError_ExtractorMissing, MediaError_UnsupportedUrl, MediaError_InvalidTemplate, MediaError_ArchiveFailure, MediaError_PathFailure, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_SizeLimit, MediaError_RetryExhausted, MediaError_ExternalToolMissing, MediaError_PostProcessFailed, MediaError_UpdateUnavailable,):
            raise CottContractViolation("returned error is not allowed", symbol="real.yt_dlp.execute", phase="error", span={"end_byte":59730,"end_column":1,"end_line":1358,"start_byte":55060,"start_column":1,"start_line":1273}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.yt_dlp.execute", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.yt_dlp.execute", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is MediaError_InvalidConfig:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:3")
    if type(_result) is Err and type(_result.error) is MediaError_InvalidInput:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:4")
    if type(_result) is Err and type(_result.error) is MediaError_AuthenticationFailed:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:5")
    if type(_result) is Err and type(_result.error) is MediaError_BatchReadFailed:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:6")
    if type(_result) is Err and type(_result.error) is MediaError_InvalidShortcut:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:7")
    if type(_result) is Err and type(_result.error) is MediaError_CertificateFailure:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:8")
    if type(_result) is Err and type(_result.error) is MediaError_WorkaroundRejected:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:9")
    if type(_result) is Err and type(_result.error) is MediaError_LogFailure:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:10")
    if type(_result) is Err and type(_result.error) is MediaError_InvalidRange:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:11")
    if type(_result) is Err and type(_result.error) is MediaError_CookieFailure:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:12")
    if type(_result) is Err and type(_result.error) is MediaError_GeoRestricted:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:13")
    if type(_result) is Err and type(_result.error) is MediaError_ExtractorMissing:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:14")
    if type(_result) is Err and type(_result.error) is MediaError_UnsupportedUrl:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:15")
    if type(_result) is Err and type(_result.error) is MediaError_InvalidTemplate:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:16")
    if type(_result) is Err and type(_result.error) is MediaError_ArchiveFailure:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:17")
    if type(_result) is Err and type(_result.error) is MediaError_PathFailure:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:18")
    if type(_result) is Err and type(_result.error) is MediaError_HttpStatus:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:19")
    if type(_result) is Err and type(_result.error) is MediaError_NetworkFailure:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:20")
    if type(_result) is Err and type(_result.error) is MediaError_OutputFailure:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:21")
    if type(_result) is Err and type(_result.error) is MediaError_SizeLimit:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:22")
    if type(_result) is Err and type(_result.error) is MediaError_RetryExhausted:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:23")
    if type(_result) is Err and type(_result.error) is MediaError_ExternalToolMissing:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:24")
    if type(_result) is Err and type(_result.error) is MediaError_PostProcessFailed:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:25")
    if type(_result) is Err and type(_result.error) is MediaError_UpdateUnavailable:
        _cott_contract_condition(True, "real.yt_dlp.execute", "error:26")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            report = _cott_match_value.value
            return (_cott_contract_condition((((report).simulated == ((request).simulation != SimulationMode_Download()))), "real.yt_dlp.execute", "ensures:1"))
        _cott_contract_condition((False), "real.yt_dlp.execute", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.execute", clause="ensures:1", phase="ensures", span={"end_byte":58713,"end_column":101,"end_line":1328,"start_byte":58617,"start_column":5,"start_line":1328}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            report = _cott_match_value.value
            return (_cott_contract_condition(((len(((report).downloads).items) <= len((report).selected))), "real.yt_dlp.execute", "ensures:2"))
        _cott_contract_condition((False), "real.yt_dlp.execute", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.yt_dlp.execute", clause="ensures:2", phase="ensures", span={"end_byte":58796,"end_column":83,"end_line":1329,"start_byte":58718,"start_column":5,"start_line":1329}, expected="true", actual="false")
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
            _error.span = {"end_byte":61390,"end_column":1,"end_line":1384,"start_byte":59730,"start_column":1,"start_line":1358}
        raise
    except SystemExit:
        raise
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.yt_dlp.run", phase="implementation-call", span={"end_byte":61390,"end_column":1,"end_line":1384,"start_byte":59730,"start_column":1,"start_line":1358}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    raise CottContractViolation("Never function returned", symbol="real.yt_dlp.run", phase="return", span={"end_byte":61390,"end_column":1,"end_line":1384,"start_byte":59730,"start_column":1,"start_line":1358}, expected="Never", actual=repr(_result))

__all__ = ["ArchiveRequest", "Authentication", "AuthenticationKind", "AuthenticationKind_Anonymous", "AuthenticationKind_BrowserCookies", "AuthenticationKind_Cookies", "AuthenticationKind_Credentials", "AuthenticationKind_Netrc", "CertificatePolicy", "CertificatePolicy_Insecure", "CertificatePolicy_Verify", "CliInput", "DownloadPlan", "ExecutionReport", "ExecutionRequest", "ExternalToolRequest", "ExtractorDescriptor", "ExtractorWorkaround", "ExtractorWorkaround_ForceGeneric", "ExtractorWorkaround_LegacyServerConnect", "ExtractorWorkaround_NoCheckCertificates", "ExtractorWorkaround_NoPlaylist", "FormatContainer", "FormatContainer_Any", "FormatContainer_Audio", "FormatContainer_Best", "FormatContainer_Video", "FormatContainer_Worst", "FormatDescriptor", "FormatRequest", "FragmentPolicy", "GeoBypassMode", "GeoBypassMode_Country", "GeoBypassMode_Default", "GeoBypassMode_Disabled", "GeoBypassMode_IpBlock", "InputKind", "InputKind_Argument", "InputKind_BatchFile", "InputKind_ConfigFile", "JsonMode", "JsonMode_Lines", "JsonMode_Single", "LiveMode", "LiveMode_Default", "LiveMode_FromStart", "LiveMode_Wait", "LiveRequest", "LogLevel", "LogLevel_Debug", "LogLevel_Info", "LogLevel_Quiet", "LogLevel_Warning", "MediaError", "MediaError_ArchiveFailure", "MediaError_AuthenticationFailed", "MediaError_BatchReadFailed", "MediaError_CertificateFailure", "MediaError_CookieFailure", "MediaError_ExternalToolMissing", "MediaError_ExtractorMissing", "MediaError_FormatUnavailable", "MediaError_GeoRestricted", "MediaError_HttpStatus", "MediaError_InvalidConfig", "MediaError_InvalidInput", "MediaError_InvalidRange", "MediaError_InvalidShortcut", "MediaError_InvalidTemplate", "MediaError_LogFailure", "MediaError_NetworkFailure", "MediaError_OutputFailure", "MediaError_PathFailure", "MediaError_PluginRejected", "MediaError_PostProcessFailed", "MediaError_RetryExhausted", "MediaError_SizeLimit", "MediaError_SubtitleUnavailable", "MediaError_UnsupportedUrl", "MediaError_UpdateUnavailable", "MediaError_WorkaroundRejected", "MediaItem", "MetadataRequest", "NetworkPolicy", "OutputRequest", "PlaylistMode", "PlaylistMode_Flat", "PlaylistMode_Playlist", "PlaylistMode_Random", "PlaylistMode_Reverse", "PlaylistMode_Single", "PlaylistRange", "PlaylistRequest", "PluginDescriptor", "PostProcessRequest", "PostProcessorKind", "PostProcessorKind_ConvertThumbnails", "PostProcessorKind_EmbedMetadata", "PostProcessorKind_EmbedSubtitle", "PostProcessorKind_EmbedThumbnail", "PostProcessorKind_ExtractAudio", "PostProcessorKind_Fixup", "PostProcessorKind_RecodeVideo", "PostProcessorKind_RemuxVideo", "PostProcessorKind_SplitChapters", "PostProcessorKind_SponsorBlock", "PresentationRequest", "ProxyMode", "ProxyMode_Direct", "ProxyMode_Http", "ProxyMode_Socks", "ShortcutKind", "ShortcutKind_Search", "ShortcutKind_SearchAll", "ShortcutKind_Url", "ShortcutRequest", "SimulationMode", "SimulationMode_Download", "SimulationMode_PrintOnly", "SimulationMode_Simulate", "SimulationMode_SkipDownload", "SubtitleMode", "SubtitleMode_All", "SubtitleMode_Automatic", "SubtitleMode_Manual", "SubtitleMode_None", "SubtitleRequest", "ThumbnailRequest", "TransferReceipt", "TransferRequest", "UpdateOutcome", "UpdateOutcome_Available", "UpdateOutcome_Current", "UpdateOutcome_Disabled", "UpdateOutcome_Installed", "UpdatePolicy", "UpdatePolicy_Apply", "UpdatePolicy_Check", "UpdatePolicy_Master", "UpdatePolicy_Never", "UpdatePolicy_Nightly", "UpdateRequest", "VideoFilterRequest", "WorkaroundPolicy", "apply_update", "build_shortcut_url", "choose_extractor", "configure_presentation", "discover_extractors", "execute", "expand_playlist_ranges", "extract_media", "filter_formats", "filter_video", "load_batch_urls", "load_config", "load_plugins", "parse_arguments", "parse_batch_urls", "plan_downloads", "plan_fragments", "plan_metadata", "plan_post_processing", "plan_thumbnails", "read_download_archive", "render_items", "render_output_path", "resolve_authentication", "resolve_inputs", "resolve_live_media", "resolve_output_path", "resolve_update_repository", "run", "run_post_processing", "select_geo_route", "select_playlist", "select_subtitles", "sort_formats", "transfer_fragments", "transfer_media", "validate_network", "validate_workarounds", "write_download_archive"]
