from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
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

"""Handle every auth kind; HEAD via Request and urlopen; derive one item from final URL."""
"""Handle each playlist mode once; apply ranges, bounds, then requested ordering."""
"""None returns typed List[Str]; otherwise preserve requested language order."""
"""No kinds returns typed List[ExternalToolRequest]; otherwise preserve kind order."""
__all__ = ["ArchiveRequest", "Authentication", "AuthenticationKind", "AuthenticationKind_Anonymous", "AuthenticationKind_BrowserCookies", "AuthenticationKind_Cookies", "AuthenticationKind_Credentials", "AuthenticationKind_Netrc", "CertificatePolicy", "CertificatePolicy_Insecure", "CertificatePolicy_Verify", "CliInput", "DownloadPlan", "ExecutionReport", "ExecutionRequest", "ExternalToolRequest", "ExtractorDescriptor", "ExtractorWorkaround", "ExtractorWorkaround_ForceGeneric", "ExtractorWorkaround_LegacyServerConnect", "ExtractorWorkaround_NoCheckCertificates", "ExtractorWorkaround_NoPlaylist", "FormatContainer", "FormatContainer_Any", "FormatContainer_Audio", "FormatContainer_Best", "FormatContainer_Video", "FormatContainer_Worst", "FormatDescriptor", "FormatRequest", "FragmentPolicy", "GeoBypassMode", "GeoBypassMode_Country", "GeoBypassMode_Default", "GeoBypassMode_Disabled", "GeoBypassMode_IpBlock", "InputKind", "InputKind_Argument", "InputKind_BatchFile", "InputKind_ConfigFile", "JsonMode", "JsonMode_Lines", "JsonMode_Single", "LiveMode", "LiveMode_Default", "LiveMode_FromStart", "LiveMode_Wait", "LiveRequest", "LogLevel", "LogLevel_Debug", "LogLevel_Info", "LogLevel_Quiet", "LogLevel_Warning", "MediaError", "MediaError_ArchiveFailure", "MediaError_AuthenticationFailed", "MediaError_BatchReadFailed", "MediaError_CertificateFailure", "MediaError_CookieFailure", "MediaError_ExternalToolMissing", "MediaError_ExtractorMissing", "MediaError_FormatUnavailable", "MediaError_GeoRestricted", "MediaError_HttpStatus", "MediaError_InvalidConfig", "MediaError_InvalidInput", "MediaError_InvalidRange", "MediaError_InvalidShortcut", "MediaError_InvalidTemplate", "MediaError_LogFailure", "MediaError_NetworkFailure", "MediaError_OutputFailure", "MediaError_PathFailure", "MediaError_PluginRejected", "MediaError_PostProcessFailed", "MediaError_RetryExhausted", "MediaError_SizeLimit", "MediaError_SubtitleUnavailable", "MediaError_UnsupportedUrl", "MediaError_UpdateUnavailable", "MediaError_WorkaroundRejected", "MediaItem", "MetadataRequest", "NetworkPolicy", "OutputRequest", "PlaylistMode", "PlaylistMode_Flat", "PlaylistMode_Playlist", "PlaylistMode_Random", "PlaylistMode_Reverse", "PlaylistMode_Single", "PlaylistRange", "PlaylistRequest", "PluginDescriptor", "PostProcessRequest", "PostProcessorKind", "PostProcessorKind_ConvertThumbnails", "PostProcessorKind_EmbedMetadata", "PostProcessorKind_EmbedSubtitle", "PostProcessorKind_EmbedThumbnail", "PostProcessorKind_ExtractAudio", "PostProcessorKind_Fixup", "PostProcessorKind_RecodeVideo", "PostProcessorKind_RemuxVideo", "PostProcessorKind_SplitChapters", "PostProcessorKind_SponsorBlock", "PresentationRequest", "ProxyMode", "ProxyMode_Direct", "ProxyMode_Http", "ProxyMode_Socks", "ShortcutKind", "ShortcutKind_Search", "ShortcutKind_SearchAll", "ShortcutKind_Url", "ShortcutRequest", "SimulationMode", "SimulationMode_Download", "SimulationMode_PrintOnly", "SimulationMode_Simulate", "SimulationMode_SkipDownload", "SubtitleMode", "SubtitleMode_All", "SubtitleMode_Automatic", "SubtitleMode_Manual", "SubtitleMode_None", "SubtitleRequest", "ThumbnailRequest", "TransferReceipt", "TransferRequest", "UpdatePolicy", "UpdatePolicy_Apply", "UpdatePolicy_Check", "UpdatePolicy_Master", "UpdatePolicy_Never", "UpdatePolicy_Nightly", "UpdateRequest", "VideoFilterRequest", "WorkaroundPolicy"]
