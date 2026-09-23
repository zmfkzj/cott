from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputKind_Argument:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputKind_ConfigFile:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputKind_BatchFile:
    pass

InputKind: TypeAlias = Union[InputKind_Argument, InputKind_ConfigFile, InputKind_BatchFile]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ProxyMode_Direct:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ProxyMode_Http:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ProxyMode_Socks:
    pass

ProxyMode: TypeAlias = Union[ProxyMode_Direct, ProxyMode_Http, ProxyMode_Socks]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AuthenticationKind_Anonymous:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AuthenticationKind_Credentials:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AuthenticationKind_Netrc:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AuthenticationKind_Cookies:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AuthenticationKind_BrowserCookies:
    pass

AuthenticationKind: TypeAlias = Union[AuthenticationKind_Anonymous, AuthenticationKind_Credentials, AuthenticationKind_Netrc, AuthenticationKind_Cookies, AuthenticationKind_BrowserCookies]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GeoBypassMode_Disabled:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GeoBypassMode_Default:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GeoBypassMode_Country:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GeoBypassMode_IpBlock:
    pass

GeoBypassMode: TypeAlias = Union[GeoBypassMode_Disabled, GeoBypassMode_Default, GeoBypassMode_Country, GeoBypassMode_IpBlock]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PlaylistMode_Single:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PlaylistMode_Playlist:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PlaylistMode_Flat:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PlaylistMode_Reverse:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PlaylistMode_Random:
    pass

PlaylistMode: TypeAlias = Union[PlaylistMode_Single, PlaylistMode_Playlist, PlaylistMode_Flat, PlaylistMode_Reverse, PlaylistMode_Random]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LiveMode_Default:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LiveMode_FromStart:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LiveMode_Wait:
    pass

LiveMode: TypeAlias = Union[LiveMode_Default, LiveMode_FromStart, LiveMode_Wait]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FormatContainer_Any:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FormatContainer_Video:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FormatContainer_Audio:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FormatContainer_Best:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FormatContainer_Worst:
    pass

FormatContainer: TypeAlias = Union[FormatContainer_Any, FormatContainer_Video, FormatContainer_Audio, FormatContainer_Best, FormatContainer_Worst]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SubtitleMode_None:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SubtitleMode_Manual:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SubtitleMode_Automatic:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SubtitleMode_All:
    pass

SubtitleMode: TypeAlias = Union[SubtitleMode_None, SubtitleMode_Manual, SubtitleMode_Automatic, SubtitleMode_All]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class JsonMode_Lines:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class JsonMode_Single:
    pass

JsonMode: TypeAlias = Union[JsonMode_Lines, JsonMode_Single]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SimulationMode_Download:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SimulationMode_Simulate:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SimulationMode_SkipDownload:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SimulationMode_PrintOnly:
    pass

SimulationMode: TypeAlias = Union[SimulationMode_Download, SimulationMode_Simulate, SimulationMode_SkipDownload, SimulationMode_PrintOnly]

"""UpdatePolicy controls whether and from which official yt-dlp release channel the
portable `yt-dlp` asset is checked or installed. Never performs no I/O. Check
authenticates and verifies the selected channel's current release metadata and
compares it with target without writing. Apply checks and, when different,
installs the channel selected by UpdateRequest.channel. Nightly and Master are
installing policies which force those respective channels and ignore
UpdateRequest.channel."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class UpdatePolicy_Never:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class UpdatePolicy_Check:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class UpdatePolicy_Apply:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class UpdatePolicy_Nightly:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class UpdatePolicy_Master:
    pass

UpdatePolicy: TypeAlias = Union[UpdatePolicy_Never, UpdatePolicy_Check, UpdatePolicy_Apply, UpdatePolicy_Nightly, UpdatePolicy_Master]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LogLevel_Quiet:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LogLevel_Warning:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LogLevel_Info:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LogLevel_Debug:
    pass

LogLevel: TypeAlias = Union[LogLevel_Quiet, LogLevel_Warning, LogLevel_Info, LogLevel_Debug]

"""Search emits yt-dlp's bounded YouTube search prefix, SearchAll emits its
unbounded prefix, and Url validates then passes through an already formed URL.
Search limits results; the limit is irrelevant to SearchAll and Url."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ShortcutKind_Search:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ShortcutKind_SearchAll:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ShortcutKind_Url:
    pass

ShortcutKind: TypeAlias = Union[ShortcutKind_Search, ShortcutKind_SearchAll, ShortcutKind_Url]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CertificatePolicy_Verify:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CertificatePolicy_Insecure:
    pass

CertificatePolicy: TypeAlias = Union[CertificatePolicy_Verify, CertificatePolicy_Insecure]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractorWorkaround_ForceGeneric:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractorWorkaround_NoPlaylist:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractorWorkaround_NoCheckCertificates:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractorWorkaround_LegacyServerConnect:
    pass

ExtractorWorkaround: TypeAlias = Union[ExtractorWorkaround_ForceGeneric, ExtractorWorkaround_NoPlaylist, ExtractorWorkaround_NoCheckCertificates, ExtractorWorkaround_LegacyServerConnect]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostProcessorKind_ExtractAudio:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostProcessorKind_RemuxVideo:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostProcessorKind_RecodeVideo:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostProcessorKind_EmbedSubtitle:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostProcessorKind_EmbedThumbnail:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostProcessorKind_EmbedMetadata:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostProcessorKind_SplitChapters:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostProcessorKind_ConvertThumbnails:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostProcessorKind_SponsorBlock:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostProcessorKind_Fixup:
    pass

PostProcessorKind: TypeAlias = Union[PostProcessorKind_ExtractAudio, PostProcessorKind_RemuxVideo, PostProcessorKind_RecodeVideo, PostProcessorKind_EmbedSubtitle, PostProcessorKind_EmbedThumbnail, PostProcessorKind_EmbedMetadata, PostProcessorKind_SplitChapters, PostProcessorKind_ConvertThumbnails, PostProcessorKind_SponsorBlock, PostProcessorKind_Fixup]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_InvalidInput:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_InvalidRange:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_InvalidTemplate:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_InvalidConfig:
    __hash__ = None
    path: Path
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_BatchReadFailed:
    __hash__ = None
    path: Path
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_AuthenticationFailed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_CookieFailure:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_GeoRestricted:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_ExtractorMissing:
    __hash__ = None
    name: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_PluginRejected:
    __hash__ = None
    path: Path
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_UnsupportedUrl:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_FormatUnavailable:
    __hash__ = None
    selector: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_SubtitleUnavailable:
    __hash__ = None
    language: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_ArchiveFailure:
    __hash__ = None
    path: Path
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_PathFailure:
    __hash__ = None
    path: Path
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_HttpStatus:
    __hash__ = None
    status: U16

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_NetworkFailure:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_OutputFailure:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_SizeLimit:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_RetryExhausted:
    __hash__ = None
    attempts: U32

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_ExternalToolMissing:
    __hash__ = None
    name: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_PostProcessFailed:
    __hash__ = None
    name: str
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_UpdateUnavailable:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_InvalidShortcut:
    __hash__ = None
    value: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_LogFailure:
    __hash__ = None
    path: Path
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_CertificateFailure:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_WorkaroundRejected:
    __hash__ = None
    message: str

MediaError: TypeAlias = Union[MediaError_InvalidInput, MediaError_InvalidRange, MediaError_InvalidTemplate, MediaError_InvalidConfig, MediaError_BatchReadFailed, MediaError_AuthenticationFailed, MediaError_CookieFailure, MediaError_GeoRestricted, MediaError_ExtractorMissing, MediaError_PluginRejected, MediaError_UnsupportedUrl, MediaError_FormatUnavailable, MediaError_SubtitleUnavailable, MediaError_ArchiveFailure, MediaError_PathFailure, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_SizeLimit, MediaError_RetryExhausted, MediaError_ExternalToolMissing, MediaError_PostProcessFailed, MediaError_UpdateUnavailable, MediaError_InvalidShortcut, MediaError_LogFailure, MediaError_CertificateFailure, MediaError_WorkaroundRejected]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CliInput:
    __hash__ = None
    kind: InputKind
    value: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, InputKind, path="$.kind"))
        if not _cott_validated_construction():
            object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NetworkPolicy:
    __hash__ = None
    proxy_mode: ProxyMode
    proxy: str
    socket_timeout_ms: U32
    source_address: str
    force_ipv4: bool
    force_ipv6: bool
    geo_mode: GeoBypassMode
    geo_country: str
    geo_ip_block: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "proxy_mode", _cott_validate_abi(self.proxy_mode, ProxyMode, path="$.proxy_mode"))
        if not _cott_validated_construction():
            object.__setattr__(self, "proxy", _cott_validate_abi(self.proxy, str, path="$.proxy"))
        if not _cott_validated_construction():
            object.__setattr__(self, "socket_timeout_ms", _cott_validate_abi(self.socket_timeout_ms, U32, path="$.socket_timeout_ms"))
        if not _cott_validated_construction():
            object.__setattr__(self, "source_address", _cott_validate_abi(self.source_address, str, path="$.source_address"))
        if not _cott_validated_construction():
            object.__setattr__(self, "force_ipv4", _cott_validate_abi(self.force_ipv4, bool, path="$.force_ipv4"))
        if not _cott_validated_construction():
            object.__setattr__(self, "force_ipv6", _cott_validate_abi(self.force_ipv6, bool, path="$.force_ipv6"))
        if not _cott_validated_construction():
            object.__setattr__(self, "geo_mode", _cott_validate_abi(self.geo_mode, GeoBypassMode, path="$.geo_mode"))
        if not _cott_validated_construction():
            object.__setattr__(self, "geo_country", _cott_validate_abi(self.geo_country, str, path="$.geo_country"))
        if not _cott_validated_construction():
            object.__setattr__(self, "geo_ip_block", _cott_validate_abi(self.geo_ip_block, str, path="$.geo_ip_block"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Authentication:
    __hash__ = None
    kind: AuthenticationKind
    username: str
    password: str
    netrc_location: Path
    cookie_file: Path
    browser: str
    profile: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, AuthenticationKind, path="$.kind"))
        if not _cott_validated_construction():
            object.__setattr__(self, "username", _cott_validate_abi(self.username, str, path="$.username"))
        if not _cott_validated_construction():
            object.__setattr__(self, "password", _cott_validate_abi(self.password, str, path="$.password"))
        if not _cott_validated_construction():
            object.__setattr__(self, "netrc_location", _cott_validate_abi(self.netrc_location, Path, path="$.netrc_location"))
        if not _cott_validated_construction():
            object.__setattr__(self, "cookie_file", _cott_validate_abi(self.cookie_file, Path, path="$.cookie_file"))
        if not _cott_validated_construction():
            object.__setattr__(self, "browser", _cott_validate_abi(self.browser, str, path="$.browser"))
        if not _cott_validated_construction():
            object.__setattr__(self, "profile", _cott_validate_abi(self.profile, str, path="$.profile"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractorDescriptor:
    __hash__ = None
    name: str
    urls: CottList[str]
    enabled: bool
    requires_login: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "urls", _cott_validate_abi(self.urls, CottList[str], path="$.urls"))
        if not _cott_validated_construction():
            object.__setattr__(self, "enabled", _cott_validate_abi(self.enabled, bool, path="$.enabled"))
        if not _cott_validated_construction():
            object.__setattr__(self, "requires_login", _cott_validate_abi(self.requires_login, bool, path="$.requires_login"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PluginDescriptor:
    __hash__ = None
    name: str
    path: Path
    extractor_names: CottList[str]
    post_processor_names: CottList[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, Path, path="$.path"))
        if not _cott_validated_construction():
            object.__setattr__(self, "extractor_names", _cott_validate_abi(self.extractor_names, CottList[str], path="$.extractor_names"))
        if not _cott_validated_construction():
            object.__setattr__(self, "post_processor_names", _cott_validate_abi(self.post_processor_names, CottList[str], path="$.post_processor_names"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaItem:
    __hash__ = None
    url: str
    id: str
    title: str
    ext: str
    playlist_index: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "url", _cott_validate_abi(self.url, str, path="$.url"))
        if not _cott_validated_construction():
            object.__setattr__(self, "id", _cott_validate_abi(self.id, str, path="$.id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "title", _cott_validate_abi(self.title, str, path="$.title"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ext", _cott_validate_abi(self.ext, str, path="$.ext"))
        if not _cott_validated_construction():
            object.__setattr__(self, "playlist_index", _cott_validate_abi(self.playlist_index, U64, path="$.playlist_index"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PlaylistRange:
    __hash__ = None
    first: U64
    last: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "first", _cott_validate_abi(self.first, U64, path="$.first"))
        if not _cott_validated_construction():
            object.__setattr__(self, "last", _cott_validate_abi(self.last, U64, path="$.last"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PlaylistRequest:
    __hash__ = None
    mode: PlaylistMode
    ranges: CottList[PlaylistRange]
    start: U64
    end: U64
    items: str
    reverse: bool
    random: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "mode", _cott_validate_abi(self.mode, PlaylistMode, path="$.mode"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ranges", _cott_validate_abi(self.ranges, CottList[PlaylistRange], path="$.ranges"))
        if not _cott_validated_construction():
            object.__setattr__(self, "start", _cott_validate_abi(self.start, U64, path="$.start"))
        if not _cott_validated_construction():
            object.__setattr__(self, "end", _cott_validate_abi(self.end, U64, path="$.end"))
        if not _cott_validated_construction():
            object.__setattr__(self, "items", _cott_validate_abi(self.items, str, path="$.items"))
        if not _cott_validated_construction():
            object.__setattr__(self, "reverse", _cott_validate_abi(self.reverse, bool, path="$.reverse"))
        if not _cott_validated_construction():
            object.__setattr__(self, "random", _cott_validate_abi(self.random, bool, path="$.random"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LiveRequest:
    __hash__ = None
    mode: LiveMode
    wait_for_video_ms: U32
    concurrent_fragments: U16

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "mode", _cott_validate_abi(self.mode, LiveMode, path="$.mode"))
        if not _cott_validated_construction():
            object.__setattr__(self, "wait_for_video_ms", _cott_validate_abi(self.wait_for_video_ms, U32, path="$.wait_for_video_ms"))
        if not _cott_validated_construction():
            object.__setattr__(self, "concurrent_fragments", _cott_validate_abi(self.concurrent_fragments, U16, path="$.concurrent_fragments"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class VideoFilterRequest:
    __hash__ = None
    date_after: str
    date_before: str
    min_views: U64
    max_views: U64
    age_limit: U16
    match_filter: str
    reject_live: bool
    include_ads: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "date_after", _cott_validate_abi(self.date_after, str, path="$.date_after"))
        if not _cott_validated_construction():
            object.__setattr__(self, "date_before", _cott_validate_abi(self.date_before, str, path="$.date_before"))
        if not _cott_validated_construction():
            object.__setattr__(self, "min_views", _cott_validate_abi(self.min_views, U64, path="$.min_views"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_views", _cott_validate_abi(self.max_views, U64, path="$.max_views"))
        if not _cott_validated_construction():
            object.__setattr__(self, "age_limit", _cott_validate_abi(self.age_limit, U16, path="$.age_limit"))
        if not _cott_validated_construction():
            object.__setattr__(self, "match_filter", _cott_validate_abi(self.match_filter, str, path="$.match_filter"))
        if not _cott_validated_construction():
            object.__setattr__(self, "reject_live", _cott_validate_abi(self.reject_live, bool, path="$.reject_live"))
        if not _cott_validated_construction():
            object.__setattr__(self, "include_ads", _cott_validate_abi(self.include_ads, bool, path="$.include_ads"))

"""For Search and SearchAll, query must be non-empty and is preserved byte-for-byte,
including leading, trailing, or all-whitespace text; it is not stripped or URL
encoded. Search requires a nonzero limit. For Url, limit is ignored, outer
whitespace is stripped, and the stripped URL is returned without normalization.
Valid URL schemes use yt-dlp's url_or_none family: http, https, ftp, ftps,
rtmp, rtmpe, rtmps, rtmpt, rtmpte, rtmpts, rtmfp, ws, wss, or a
scheme-relative `//` URL; the
authority must be non-empty and the URL must contain no whitespace or control
characters."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ShortcutRequest:
    __hash__ = None
    kind: ShortcutKind
    query: str
    limit: U16

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, ShortcutKind, path="$.kind"))
        if not _cott_validated_construction():
            object.__setattr__(self, "query", _cott_validate_abi(self.query, str, path="$.query"))
        if not _cott_validated_construction():
            object.__setattr__(self, "limit", _cott_validate_abi(self.limit, U16, path="$.limit"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PresentationRequest:
    __hash__ = None
    level: LogLevel
    progress: bool
    newline_progress: bool
    color: bool
    dump_pages: bool
    write_pages: bool
    log_file: Path

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "level", _cott_validate_abi(self.level, LogLevel, path="$.level"))
        if not _cott_validated_construction():
            object.__setattr__(self, "progress", _cott_validate_abi(self.progress, bool, path="$.progress"))
        if not _cott_validated_construction():
            object.__setattr__(self, "newline_progress", _cott_validate_abi(self.newline_progress, bool, path="$.newline_progress"))
        if not _cott_validated_construction():
            object.__setattr__(self, "color", _cott_validate_abi(self.color, bool, path="$.color"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dump_pages", _cott_validate_abi(self.dump_pages, bool, path="$.dump_pages"))
        if not _cott_validated_construction():
            object.__setattr__(self, "write_pages", _cott_validate_abi(self.write_pages, bool, path="$.write_pages"))
        if not _cott_validated_construction():
            object.__setattr__(self, "log_file", _cott_validate_abi(self.log_file, Path, path="$.log_file"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class WorkaroundPolicy:
    __hash__ = None
    certificate: CertificatePolicy
    force_generic_extractor: bool
    legacy_server_connect: bool
    extractor_args: CottList[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "certificate", _cott_validate_abi(self.certificate, CertificatePolicy, path="$.certificate"))
        if not _cott_validated_construction():
            object.__setattr__(self, "force_generic_extractor", _cott_validate_abi(self.force_generic_extractor, bool, path="$.force_generic_extractor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "legacy_server_connect", _cott_validate_abi(self.legacy_server_connect, bool, path="$.legacy_server_connect"))
        if not _cott_validated_construction():
            object.__setattr__(self, "extractor_args", _cott_validate_abi(self.extractor_args, CottList[str], path="$.extractor_args"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FormatDescriptor:
    __hash__ = None
    id: str
    extension: str
    container: FormatContainer
    video_height: U32
    audio_bitrate: U32
    file_size: U64
    has_video: bool
    has_audio: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "id", _cott_validate_abi(self.id, str, path="$.id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "extension", _cott_validate_abi(self.extension, str, path="$.extension"))
        if not _cott_validated_construction():
            object.__setattr__(self, "container", _cott_validate_abi(self.container, FormatContainer, path="$.container"))
        if not _cott_validated_construction():
            object.__setattr__(self, "video_height", _cott_validate_abi(self.video_height, U32, path="$.video_height"))
        if not _cott_validated_construction():
            object.__setattr__(self, "audio_bitrate", _cott_validate_abi(self.audio_bitrate, U32, path="$.audio_bitrate"))
        if not _cott_validated_construction():
            object.__setattr__(self, "file_size", _cott_validate_abi(self.file_size, U64, path="$.file_size"))
        if not _cott_validated_construction():
            object.__setattr__(self, "has_video", _cott_validate_abi(self.has_video, bool, path="$.has_video"))
        if not _cott_validated_construction():
            object.__setattr__(self, "has_audio", _cott_validate_abi(self.has_audio, bool, path="$.has_audio"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FormatRequest:
    __hash__ = None
    selector: str
    containers: CottList[FormatContainer]
    sort_fields: CottList[str]
    merge_output_format: str
    min_file_size: U64
    max_file_size: U64
    prefer_free_formats: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "selector", _cott_validate_abi(self.selector, str, path="$.selector"))
        if not _cott_validated_construction():
            object.__setattr__(self, "containers", _cott_validate_abi(self.containers, CottList[FormatContainer], path="$.containers"))
        if not _cott_validated_construction():
            object.__setattr__(self, "sort_fields", _cott_validate_abi(self.sort_fields, CottList[str], path="$.sort_fields"))
        if not _cott_validated_construction():
            object.__setattr__(self, "merge_output_format", _cott_validate_abi(self.merge_output_format, str, path="$.merge_output_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "min_file_size", _cott_validate_abi(self.min_file_size, U64, path="$.min_file_size"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_file_size", _cott_validate_abi(self.max_file_size, U64, path="$.max_file_size"))
        if not _cott_validated_construction():
            object.__setattr__(self, "prefer_free_formats", _cott_validate_abi(self.prefer_free_formats, bool, path="$.prefer_free_formats"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SubtitleRequest:
    __hash__ = None
    mode: SubtitleMode
    languages: CottList[str]
    formats: CottList[str]
    convert_format: str
    embed: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "mode", _cott_validate_abi(self.mode, SubtitleMode, path="$.mode"))
        if not _cott_validated_construction():
            object.__setattr__(self, "languages", _cott_validate_abi(self.languages, CottList[str], path="$.languages"))
        if not _cott_validated_construction():
            object.__setattr__(self, "formats", _cott_validate_abi(self.formats, CottList[str], path="$.formats"))
        if not _cott_validated_construction():
            object.__setattr__(self, "convert_format", _cott_validate_abi(self.convert_format, str, path="$.convert_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "embed", _cott_validate_abi(self.embed, bool, path="$.embed"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThumbnailRequest:
    __hash__ = None
    write: bool
    formats: CottList[str]
    convert_format: str
    embed: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "write", _cott_validate_abi(self.write, bool, path="$.write"))
        if not _cott_validated_construction():
            object.__setattr__(self, "formats", _cott_validate_abi(self.formats, CottList[str], path="$.formats"))
        if not _cott_validated_construction():
            object.__setattr__(self, "convert_format", _cott_validate_abi(self.convert_format, str, path="$.convert_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "embed", _cott_validate_abi(self.embed, bool, path="$.embed"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MetadataRequest:
    __hash__ = None
    write_info_json: bool
    write_description: bool
    write_comments: bool
    write_playlist_metadata: bool
    embed: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "write_info_json", _cott_validate_abi(self.write_info_json, bool, path="$.write_info_json"))
        if not _cott_validated_construction():
            object.__setattr__(self, "write_description", _cott_validate_abi(self.write_description, bool, path="$.write_description"))
        if not _cott_validated_construction():
            object.__setattr__(self, "write_comments", _cott_validate_abi(self.write_comments, bool, path="$.write_comments"))
        if not _cott_validated_construction():
            object.__setattr__(self, "write_playlist_metadata", _cott_validate_abi(self.write_playlist_metadata, bool, path="$.write_playlist_metadata"))
        if not _cott_validated_construction():
            object.__setattr__(self, "embed", _cott_validate_abi(self.embed, bool, path="$.embed"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OutputRequest:
    __hash__ = None
    template: str
    home: Path
    temp: Path
    output: Path
    missing_placeholder: str
    restrict_filenames: bool
    windows_filenames: bool
    trim_filename_bytes: U16

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "template", _cott_validate_abi(self.template, str, path="$.template"))
        if not _cott_validated_construction():
            object.__setattr__(self, "home", _cott_validate_abi(self.home, Path, path="$.home"))
        if not _cott_validated_construction():
            object.__setattr__(self, "temp", _cott_validate_abi(self.temp, Path, path="$.temp"))
        if not _cott_validated_construction():
            object.__setattr__(self, "output", _cott_validate_abi(self.output, Path, path="$.output"))
        if not _cott_validated_construction():
            object.__setattr__(self, "missing_placeholder", _cott_validate_abi(self.missing_placeholder, str, path="$.missing_placeholder"))
        if not _cott_validated_construction():
            object.__setattr__(self, "restrict_filenames", _cott_validate_abi(self.restrict_filenames, bool, path="$.restrict_filenames"))
        if not _cott_validated_construction():
            object.__setattr__(self, "windows_filenames", _cott_validate_abi(self.windows_filenames, bool, path="$.windows_filenames"))
        if not _cott_validated_construction():
            object.__setattr__(self, "trim_filename_bytes", _cott_validate_abi(self.trim_filename_bytes, U16, path="$.trim_filename_bytes"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ArchiveRequest:
    __hash__ = None
    path: Path
    break_on_existing: bool
    force_write_archive: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, Path, path="$.path"))
        if not _cott_validated_construction():
            object.__setattr__(self, "break_on_existing", _cott_validate_abi(self.break_on_existing, bool, path="$.break_on_existing"))
        if not _cott_validated_construction():
            object.__setattr__(self, "force_write_archive", _cott_validate_abi(self.force_write_archive, bool, path="$.force_write_archive"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FragmentPolicy:
    __hash__ = None
    concurrent_fragments: U16
    buffer_size: U32
    chunk_size: U32
    rate_limit_bytes_per_second: U64
    retries: U32
    fragment_retries: U32
    file_access_retries: U32
    continue_download: bool
    part_files: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "concurrent_fragments", _cott_validate_abi(self.concurrent_fragments, U16, path="$.concurrent_fragments"))
        if not _cott_validated_construction():
            object.__setattr__(self, "buffer_size", _cott_validate_abi(self.buffer_size, U32, path="$.buffer_size"))
        if not _cott_validated_construction():
            object.__setattr__(self, "chunk_size", _cott_validate_abi(self.chunk_size, U32, path="$.chunk_size"))
        if not _cott_validated_construction():
            object.__setattr__(self, "rate_limit_bytes_per_second", _cott_validate_abi(self.rate_limit_bytes_per_second, U64, path="$.rate_limit_bytes_per_second"))
        if not _cott_validated_construction():
            object.__setattr__(self, "retries", _cott_validate_abi(self.retries, U32, path="$.retries"))
        if not _cott_validated_construction():
            object.__setattr__(self, "fragment_retries", _cott_validate_abi(self.fragment_retries, U32, path="$.fragment_retries"))
        if not _cott_validated_construction():
            object.__setattr__(self, "file_access_retries", _cott_validate_abi(self.file_access_retries, U32, path="$.file_access_retries"))
        if not _cott_validated_construction():
            object.__setattr__(self, "continue_download", _cott_validate_abi(self.continue_download, bool, path="$.continue_download"))
        if not _cott_validated_construction():
            object.__setattr__(self, "part_files", _cott_validate_abi(self.part_files, bool, path="$.part_files"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DownloadPlan:
    __hash__ = None
    items: CottList[MediaItem]
    stopped_on_archive: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "items", _cott_validate_abi(self.items, CottList[MediaItem], path="$.items"))
        if not _cott_validated_construction():
            object.__setattr__(self, "stopped_on_archive", _cott_validate_abi(self.stopped_on_archive, bool, path="$.stopped_on_archive"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransferRequest:
    __hash__ = None
    url: str
    destination: Path
    simulate: bool
    max_bytes: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "url", _cott_validate_abi(self.url, str, path="$.url"))
        if not _cott_validated_construction():
            object.__setattr__(self, "destination", _cott_validate_abi(self.destination, Path, path="$.destination"))
        if not _cott_validated_construction():
            object.__setattr__(self, "simulate", _cott_validate_abi(self.simulate, bool, path="$.simulate"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_bytes", _cott_validate_abi(self.max_bytes, U64, path="$.max_bytes"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransferReceipt:
    __hash__ = None
    url: str
    destination: Path
    bytes_written: U64
    simulated: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "url", _cott_validate_abi(self.url, str, path="$.url"))
        if not _cott_validated_construction():
            object.__setattr__(self, "destination", _cott_validate_abi(self.destination, Path, path="$.destination"))
        if not _cott_validated_construction():
            object.__setattr__(self, "bytes_written", _cott_validate_abi(self.bytes_written, U64, path="$.bytes_written"))
        if not _cott_validated_construction():
            object.__setattr__(self, "simulated", _cott_validate_abi(self.simulated, bool, path="$.simulated"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExternalToolRequest:
    __hash__ = None
    executable: str
    arguments: CottList[str]
    input: Path
    output: Path
    timeout_ms: U32

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "executable", _cott_validate_abi(self.executable, str, path="$.executable"))
        if not _cott_validated_construction():
            object.__setattr__(self, "arguments", _cott_validate_abi(self.arguments, CottList[str], path="$.arguments"))
        if not _cott_validated_construction():
            object.__setattr__(self, "input", _cott_validate_abi(self.input, Path, path="$.input"))
        if not _cott_validated_construction():
            object.__setattr__(self, "output", _cott_validate_abi(self.output, Path, path="$.output"))
        if not _cott_validated_construction():
            object.__setattr__(self, "timeout_ms", _cott_validate_abi(self.timeout_ms, U32, path="$.timeout_ms"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostProcessRequest:
    __hash__ = None
    kinds: CottList[PostProcessorKind]
    audio_format: str
    video_format: str
    sponsorblock_categories: CottList[str]
    external_tool: Option[ExternalToolRequest]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "kinds", _cott_validate_abi(self.kinds, CottList[PostProcessorKind], path="$.kinds"))
        if not _cott_validated_construction():
            object.__setattr__(self, "audio_format", _cott_validate_abi(self.audio_format, str, path="$.audio_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "video_format", _cott_validate_abi(self.video_format, str, path="$.video_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "sponsorblock_categories", _cott_validate_abi(self.sponsorblock_categories, CottList[str], path="$.sponsorblock_categories"))
        if not _cott_validated_construction():
            object.__setattr__(self, "external_tool", _cott_validate_abi(self.external_tool, Option[ExternalToolRequest], path="$.external_tool"))

"""channel is a case-sensitive official channel name after stripping outer
whitespace: stable, nightly, or master; an empty channel means stable. It is
consulted only by Check and Apply. Nightly and Master override it, and Never
ignores both channel and target. target is the explicit filesystem leaf checked
or atomically replaced; it is never inferred from the running program."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateRequest:
    __hash__ = None
    policy: UpdatePolicy
    channel: str
    target: Path

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "policy", _cott_validate_abi(self.policy, UpdatePolicy, path="$.policy"))
        if not _cott_validated_construction():
            object.__setattr__(self, "channel", _cott_validate_abi(self.channel, str, path="$.channel"))
        if not _cott_validated_construction():
            object.__setattr__(self, "target", _cott_validate_abi(self.target, Path, path="$.target"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionRequest:
    __hash__ = None
    inputs: CottList[CliInput]
    network: NetworkPolicy
    authentication: Authentication
    playlist: PlaylistRequest
    live: LiveRequest
    video_filter: VideoFilterRequest
    shortcut: ShortcutRequest
    formats: FormatRequest
    subtitles: SubtitleRequest
    thumbnails: ThumbnailRequest
    metadata: MetadataRequest
    output: OutputRequest
    archive: ArchiveRequest
    fragments: FragmentPolicy
    post_processing: PostProcessRequest
    simulation: SimulationMode
    json_mode: JsonMode
    update: UpdateRequest
    presentation: PresentationRequest
    workarounds: WorkaroundPolicy

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "inputs", _cott_validate_abi(self.inputs, CottList[CliInput], path="$.inputs"))
        if not _cott_validated_construction():
            object.__setattr__(self, "network", _cott_validate_abi(self.network, NetworkPolicy, path="$.network"))
        if not _cott_validated_construction():
            object.__setattr__(self, "authentication", _cott_validate_abi(self.authentication, Authentication, path="$.authentication"))
        if not _cott_validated_construction():
            object.__setattr__(self, "playlist", _cott_validate_abi(self.playlist, PlaylistRequest, path="$.playlist"))
        if not _cott_validated_construction():
            object.__setattr__(self, "live", _cott_validate_abi(self.live, LiveRequest, path="$.live"))
        if not _cott_validated_construction():
            object.__setattr__(self, "video_filter", _cott_validate_abi(self.video_filter, VideoFilterRequest, path="$.video_filter"))
        if not _cott_validated_construction():
            object.__setattr__(self, "shortcut", _cott_validate_abi(self.shortcut, ShortcutRequest, path="$.shortcut"))
        if not _cott_validated_construction():
            object.__setattr__(self, "formats", _cott_validate_abi(self.formats, FormatRequest, path="$.formats"))
        if not _cott_validated_construction():
            object.__setattr__(self, "subtitles", _cott_validate_abi(self.subtitles, SubtitleRequest, path="$.subtitles"))
        if not _cott_validated_construction():
            object.__setattr__(self, "thumbnails", _cott_validate_abi(self.thumbnails, ThumbnailRequest, path="$.thumbnails"))
        if not _cott_validated_construction():
            object.__setattr__(self, "metadata", _cott_validate_abi(self.metadata, MetadataRequest, path="$.metadata"))
        if not _cott_validated_construction():
            object.__setattr__(self, "output", _cott_validate_abi(self.output, OutputRequest, path="$.output"))
        if not _cott_validated_construction():
            object.__setattr__(self, "archive", _cott_validate_abi(self.archive, ArchiveRequest, path="$.archive"))
        if not _cott_validated_construction():
            object.__setattr__(self, "fragments", _cott_validate_abi(self.fragments, FragmentPolicy, path="$.fragments"))
        if not _cott_validated_construction():
            object.__setattr__(self, "post_processing", _cott_validate_abi(self.post_processing, PostProcessRequest, path="$.post_processing"))
        if not _cott_validated_construction():
            object.__setattr__(self, "simulation", _cott_validate_abi(self.simulation, SimulationMode, path="$.simulation"))
        if not _cott_validated_construction():
            object.__setattr__(self, "json_mode", _cott_validate_abi(self.json_mode, JsonMode, path="$.json_mode"))
        if not _cott_validated_construction():
            object.__setattr__(self, "update", _cott_validate_abi(self.update, UpdateRequest, path="$.update"))
        if not _cott_validated_construction():
            object.__setattr__(self, "presentation", _cott_validate_abi(self.presentation, PresentationRequest, path="$.presentation"))
        if not _cott_validated_construction():
            object.__setattr__(self, "workarounds", _cott_validate_abi(self.workarounds, WorkaroundPolicy, path="$.workarounds"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionReport:
    __hash__ = None
    selected: CottList[MediaItem]
    downloads: DownloadPlan
    rendered: str
    simulated: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "selected", _cott_validate_abi(self.selected, CottList[MediaItem], path="$.selected"))
        if not _cott_validated_construction():
            object.__setattr__(self, "downloads", _cott_validate_abi(self.downloads, DownloadPlan, path="$.downloads"))
        if not _cott_validated_construction():
            object.__setattr__(self, "rendered", _cott_validate_abi(self.rendered, str, path="$.rendered"))
        if not _cott_validated_construction():
            object.__setattr__(self, "simulated", _cott_validate_abi(self.simulated, bool, path="$.simulated"))

"""Search returns `ytsearch{limit}:{query}` using the positive base-10 limit.
SearchAll returns `ytsearchall:{query}` and ignores limit, including zero.
Url ignores limit, strips only outer whitespace, validates the schemes and
authority documented by ShortcutRequest, and returns that stripped URL
unchanged. Do not percent-encode, case-fold, or otherwise normalize output.
Return InvalidShortcut(value=request.query) for an empty search query, a
zero Search limit, or an invalid Url."""
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
"""Handle every auth kind; HEAD via Request and urlopen; derive one item from final URL."""
"""Empty ranges returns items unchanged. Otherwise validate every range: first
and last are positive inclusive MediaItem.playlist_index values, not list
positions; first greater than last is InvalidRange. Iterate ranges in request
order and items in input order, appending matching items for each range.
Overlapping ranges deliberately repeat occurrences. An out-of-bounds range
contributes no matches. Preserve every MediaItem field, including playlist_index."""
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
"""None returns typed List[Str]; otherwise preserve requested language order."""
"""Return symbolic output names, not URLs or CLI options. When write is true and
formats is empty, append item.id + ".thumbnail". When write is true and formats
is nonempty, append item.id + "." + format for each nonempty format in order.
Independently, a nonempty convert_format appends item.id + "." + convert_format,
even when write is false. Finally embed appends "embed:" + item.id.
Preserve duplicates. No other MediaItem field affects these names."""
"""Return symbolic output names in this flag order: write_info_json appends
item.id + ".info.json"; write_description appends item.id + ".description";
write_comments appends item.id + ".comments.json"; write_playlist_metadata
appends item.id + ".playlist.json"; embed appends "embed:" + item.id.
False flags add nothing. No other MediaItem field changes this pure plan."""
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
"""This client's archive contains plain media ids, one UTF-8 line per entry,
not upstream yt-dlp's extractor-key-plus-id format. Read request.path with
UTF-8-sig decoding, split lines, strip surrounding whitespace and ignore empty
lines. Preserve nonempty line order and duplicates. Reject more than 100000
entries and files exceeding 16 MiB rather than truncating.
Missing/nonregular/symlink files, decoding and actual I/O errors return
ArchiveFailure(path=request.path, message=a fixed descriptive category).
break_on_existing and force_write_archive affect the caller's execution policy,
not this reader. No extractor key is invented and no content is executed."""
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
"""Serialize each MediaItem as a JSON object whose keys occur in exactly this
order: url, id, title, ext, playlist_index, with their stored values unchanged.
Use ensure_ascii=False and compact separators (",", ":"). Lines joins the
objects with a single newline and no trailing newline; empty input is "".
Single returns one compact JSON array in item order; empty input is "[]".
Do not invent a playlist envelope, rename keys, or sort/deduplicate items."""
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
"""Return the empty string for Never without inspecting channel. Nightly returns
`yt-dlp/yt-dlp-nightly-builds` and Master returns
`yt-dlp/yt-dlp-master-builds`, ignoring channel. For Check and Apply, strip
outer whitespace from channel: empty or `stable` maps to `yt-dlp/yt-dlp`,
`nightly` maps to `yt-dlp/yt-dlp-nightly-builds`, and `master` maps to
`yt-dlp/yt-dlp-master-builds`. Matching is case-sensitive. Reject every other
value as UpdateUnavailable; never interpret channel as a repository or URL."""
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
__all__ = ["ArchiveRequest", "Authentication", "AuthenticationKind", "AuthenticationKind_Anonymous", "AuthenticationKind_BrowserCookies", "AuthenticationKind_Cookies", "AuthenticationKind_Credentials", "AuthenticationKind_Netrc", "CertificatePolicy", "CertificatePolicy_Insecure", "CertificatePolicy_Verify", "CliInput", "DownloadPlan", "ExecutionReport", "ExecutionRequest", "ExternalToolRequest", "ExtractorDescriptor", "ExtractorWorkaround", "ExtractorWorkaround_ForceGeneric", "ExtractorWorkaround_LegacyServerConnect", "ExtractorWorkaround_NoCheckCertificates", "ExtractorWorkaround_NoPlaylist", "FormatContainer", "FormatContainer_Any", "FormatContainer_Audio", "FormatContainer_Best", "FormatContainer_Video", "FormatContainer_Worst", "FormatDescriptor", "FormatRequest", "FragmentPolicy", "GeoBypassMode", "GeoBypassMode_Country", "GeoBypassMode_Default", "GeoBypassMode_Disabled", "GeoBypassMode_IpBlock", "InputKind", "InputKind_Argument", "InputKind_BatchFile", "InputKind_ConfigFile", "JsonMode", "JsonMode_Lines", "JsonMode_Single", "LiveMode", "LiveMode_Default", "LiveMode_FromStart", "LiveMode_Wait", "LiveRequest", "LogLevel", "LogLevel_Debug", "LogLevel_Info", "LogLevel_Quiet", "LogLevel_Warning", "MediaError", "MediaError_ArchiveFailure", "MediaError_AuthenticationFailed", "MediaError_BatchReadFailed", "MediaError_CertificateFailure", "MediaError_CookieFailure", "MediaError_ExternalToolMissing", "MediaError_ExtractorMissing", "MediaError_FormatUnavailable", "MediaError_GeoRestricted", "MediaError_HttpStatus", "MediaError_InvalidConfig", "MediaError_InvalidInput", "MediaError_InvalidRange", "MediaError_InvalidShortcut", "MediaError_InvalidTemplate", "MediaError_LogFailure", "MediaError_NetworkFailure", "MediaError_OutputFailure", "MediaError_PathFailure", "MediaError_PluginRejected", "MediaError_PostProcessFailed", "MediaError_RetryExhausted", "MediaError_SizeLimit", "MediaError_SubtitleUnavailable", "MediaError_UnsupportedUrl", "MediaError_UpdateUnavailable", "MediaError_WorkaroundRejected", "MediaItem", "MetadataRequest", "NetworkPolicy", "OutputRequest", "PlaylistMode", "PlaylistMode_Flat", "PlaylistMode_Playlist", "PlaylistMode_Random", "PlaylistMode_Reverse", "PlaylistMode_Single", "PlaylistRange", "PlaylistRequest", "PluginDescriptor", "PostProcessRequest", "PostProcessorKind", "PostProcessorKind_ConvertThumbnails", "PostProcessorKind_EmbedMetadata", "PostProcessorKind_EmbedSubtitle", "PostProcessorKind_EmbedThumbnail", "PostProcessorKind_ExtractAudio", "PostProcessorKind_Fixup", "PostProcessorKind_RecodeVideo", "PostProcessorKind_RemuxVideo", "PostProcessorKind_SplitChapters", "PostProcessorKind_SponsorBlock", "PresentationRequest", "ProxyMode", "ProxyMode_Direct", "ProxyMode_Http", "ProxyMode_Socks", "ShortcutKind", "ShortcutKind_Search", "ShortcutKind_SearchAll", "ShortcutKind_Url", "ShortcutRequest", "SimulationMode", "SimulationMode_Download", "SimulationMode_PrintOnly", "SimulationMode_Simulate", "SimulationMode_SkipDownload", "SubtitleMode", "SubtitleMode_All", "SubtitleMode_Automatic", "SubtitleMode_Manual", "SubtitleMode_None", "SubtitleRequest", "ThumbnailRequest", "TransferReceipt", "TransferRequest", "UpdatePolicy", "UpdatePolicy_Apply", "UpdatePolicy_Check", "UpdatePolicy_Master", "UpdatePolicy_Never", "UpdatePolicy_Nightly", "UpdateRequest", "VideoFilterRequest", "WorkaroundPolicy"]
