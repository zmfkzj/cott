from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.yt_dlp_types import ArchiveRequest as ArchiveRequest, Authentication as Authentication, AuthenticationKind as AuthenticationKind, AuthenticationKind_Anonymous as AuthenticationKind_Anonymous, AuthenticationKind_BrowserCookies as AuthenticationKind_BrowserCookies, AuthenticationKind_Cookies as AuthenticationKind_Cookies, AuthenticationKind_Credentials as AuthenticationKind_Credentials, AuthenticationKind_Netrc as AuthenticationKind_Netrc, CertificatePolicy as CertificatePolicy, CertificatePolicy_Insecure as CertificatePolicy_Insecure, CertificatePolicy_Verify as CertificatePolicy_Verify, CliInput as CliInput, DownloadPlan as DownloadPlan, ExecutionReport as ExecutionReport, ExecutionRequest as ExecutionRequest, ExternalToolRequest as ExternalToolRequest, ExtractorDescriptor as ExtractorDescriptor, ExtractorWorkaround as ExtractorWorkaround, ExtractorWorkaround_ForceGeneric as ExtractorWorkaround_ForceGeneric, ExtractorWorkaround_LegacyServerConnect as ExtractorWorkaround_LegacyServerConnect, ExtractorWorkaround_NoCheckCertificates as ExtractorWorkaround_NoCheckCertificates, ExtractorWorkaround_NoPlaylist as ExtractorWorkaround_NoPlaylist, FormatContainer as FormatContainer, FormatContainer_Any as FormatContainer_Any, FormatContainer_Audio as FormatContainer_Audio, FormatContainer_Best as FormatContainer_Best, FormatContainer_Video as FormatContainer_Video, FormatContainer_Worst as FormatContainer_Worst, FormatDescriptor as FormatDescriptor, FormatRequest as FormatRequest, FragmentPolicy as FragmentPolicy, GeoBypassMode as GeoBypassMode, GeoBypassMode_Country as GeoBypassMode_Country, GeoBypassMode_Default as GeoBypassMode_Default, GeoBypassMode_Disabled as GeoBypassMode_Disabled, GeoBypassMode_IpBlock as GeoBypassMode_IpBlock, InputKind as InputKind, InputKind_Argument as InputKind_Argument, InputKind_BatchFile as InputKind_BatchFile, InputKind_ConfigFile as InputKind_ConfigFile, JsonMode as JsonMode, JsonMode_Lines as JsonMode_Lines, JsonMode_Single as JsonMode_Single, LiveMode as LiveMode, LiveMode_Default as LiveMode_Default, LiveMode_FromStart as LiveMode_FromStart, LiveMode_Wait as LiveMode_Wait, LiveRequest as LiveRequest, LogLevel as LogLevel, LogLevel_Debug as LogLevel_Debug, LogLevel_Info as LogLevel_Info, LogLevel_Quiet as LogLevel_Quiet, LogLevel_Warning as LogLevel_Warning, MediaError as MediaError, MediaError_ArchiveFailure as MediaError_ArchiveFailure, MediaError_AuthenticationFailed as MediaError_AuthenticationFailed, MediaError_BatchReadFailed as MediaError_BatchReadFailed, MediaError_CertificateFailure as MediaError_CertificateFailure, MediaError_CookieFailure as MediaError_CookieFailure, MediaError_ExternalToolMissing as MediaError_ExternalToolMissing, MediaError_ExtractorMissing as MediaError_ExtractorMissing, MediaError_FormatUnavailable as MediaError_FormatUnavailable, MediaError_GeoRestricted as MediaError_GeoRestricted, MediaError_HttpStatus as MediaError_HttpStatus, MediaError_InvalidConfig as MediaError_InvalidConfig, MediaError_InvalidInput as MediaError_InvalidInput, MediaError_InvalidRange as MediaError_InvalidRange, MediaError_InvalidShortcut as MediaError_InvalidShortcut, MediaError_InvalidTemplate as MediaError_InvalidTemplate, MediaError_LogFailure as MediaError_LogFailure, MediaError_NetworkFailure as MediaError_NetworkFailure, MediaError_OutputFailure as MediaError_OutputFailure, MediaError_PathFailure as MediaError_PathFailure, MediaError_PluginRejected as MediaError_PluginRejected, MediaError_PostProcessFailed as MediaError_PostProcessFailed, MediaError_RetryExhausted as MediaError_RetryExhausted, MediaError_SizeLimit as MediaError_SizeLimit, MediaError_SubtitleUnavailable as MediaError_SubtitleUnavailable, MediaError_UnsupportedUrl as MediaError_UnsupportedUrl, MediaError_UpdateUnavailable as MediaError_UpdateUnavailable, MediaError_WorkaroundRejected as MediaError_WorkaroundRejected, MediaItem as MediaItem, MetadataRequest as MetadataRequest, NetworkPolicy as NetworkPolicy, OutputRequest as OutputRequest, PlaylistMode as PlaylistMode, PlaylistMode_Flat as PlaylistMode_Flat, PlaylistMode_Playlist as PlaylistMode_Playlist, PlaylistMode_Random as PlaylistMode_Random, PlaylistMode_Reverse as PlaylistMode_Reverse, PlaylistMode_Single as PlaylistMode_Single, PlaylistRange as PlaylistRange, PlaylistRequest as PlaylistRequest, PluginDescriptor as PluginDescriptor, PostProcessRequest as PostProcessRequest, PostProcessorKind as PostProcessorKind, PostProcessorKind_ConvertThumbnails as PostProcessorKind_ConvertThumbnails, PostProcessorKind_EmbedMetadata as PostProcessorKind_EmbedMetadata, PostProcessorKind_EmbedSubtitle as PostProcessorKind_EmbedSubtitle, PostProcessorKind_EmbedThumbnail as PostProcessorKind_EmbedThumbnail, PostProcessorKind_ExtractAudio as PostProcessorKind_ExtractAudio, PostProcessorKind_Fixup as PostProcessorKind_Fixup, PostProcessorKind_RecodeVideo as PostProcessorKind_RecodeVideo, PostProcessorKind_RemuxVideo as PostProcessorKind_RemuxVideo, PostProcessorKind_SplitChapters as PostProcessorKind_SplitChapters, PostProcessorKind_SponsorBlock as PostProcessorKind_SponsorBlock, PresentationRequest as PresentationRequest, ProxyMode as ProxyMode, ProxyMode_Direct as ProxyMode_Direct, ProxyMode_Http as ProxyMode_Http, ProxyMode_Socks as ProxyMode_Socks, ShortcutKind as ShortcutKind, ShortcutKind_Search as ShortcutKind_Search, ShortcutKind_SearchAll as ShortcutKind_SearchAll, ShortcutKind_Url as ShortcutKind_Url, ShortcutRequest as ShortcutRequest, SimulationMode as SimulationMode, SimulationMode_Download as SimulationMode_Download, SimulationMode_PrintOnly as SimulationMode_PrintOnly, SimulationMode_Simulate as SimulationMode_Simulate, SimulationMode_SkipDownload as SimulationMode_SkipDownload, SubtitleMode as SubtitleMode, SubtitleMode_All as SubtitleMode_All, SubtitleMode_Automatic as SubtitleMode_Automatic, SubtitleMode_Manual as SubtitleMode_Manual, SubtitleMode_None as SubtitleMode_None, SubtitleRequest as SubtitleRequest, ThumbnailRequest as ThumbnailRequest, TransferReceipt as TransferReceipt, TransferRequest as TransferRequest, UpdatePolicy as UpdatePolicy, UpdatePolicy_Apply as UpdatePolicy_Apply, UpdatePolicy_Check as UpdatePolicy_Check, UpdatePolicy_Master as UpdatePolicy_Master, UpdatePolicy_Never as UpdatePolicy_Never, UpdatePolicy_Nightly as UpdatePolicy_Nightly, UpdateRequest as UpdateRequest, VideoFilterRequest as VideoFilterRequest, WorkaroundPolicy as WorkaroundPolicy
def parse_arguments(arguments: CottList[str]) -> Result[CottList[CliInput], MediaError]: ...

"""Search returns `ytsearch{limit}:{query}` using the positive base-10 limit.
SearchAll returns `ytsearchall:{query}` and ignores limit, including zero.
Url ignores limit, strips only outer whitespace, validates the schemes and
authority documented by ShortcutRequest, and returns that stripped URL
unchanged. Do not percent-encode, case-fold, or otherwise normalize output.
Return InvalidShortcut(value=request.query) for an empty search query, a
zero Search limit, or an invalid Url."""
def build_shortcut_url(request: ShortcutRequest) -> Result[str, MediaError]: ...

def validate_workarounds(policy: WorkaroundPolicy) -> Result[WorkaroundPolicy, MediaError]: ...

def configure_presentation(request: PresentationRequest) -> Result[Unit, MediaError]: ...

def load_config(path: Path) -> Result[CottList[CliInput], MediaError]: ...

def parse_batch_urls(batch: str, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]: ...

def load_batch_urls(path: Path, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]: ...

def resolve_inputs(inputs: CottList[CliInput], config: CottList[CliInput]) -> Result[CottList[str], MediaError]: ...

def validate_network(policy: NetworkPolicy) -> Result[NetworkPolicy, MediaError]: ...

def resolve_authentication(request: Authentication) -> Result[Authentication, MediaError]: ...

def select_geo_route(policy: NetworkPolicy) -> Result[NetworkPolicy, MediaError]: ...

"""Return one enabled generic HTTP extractor named "generic", accepting the
prefixes "http://" and "https://", with requires_login false. This is a
direct-media client, not a registry of upstream site-specific extractors."""
def discover_extractors() -> CottList[ExtractorDescriptor]: ...

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
def load_plugins(paths: CottList[Path]) -> Result[CottList[PluginDescriptor], MediaError]: ...

def choose_extractor(url: str, extractors: CottList[ExtractorDescriptor]) -> Result[ExtractorDescriptor, MediaError]: ...

"""Handle every auth kind; HEAD via Request and urlopen; derive one item from final URL."""
def extract_media(url: str, extractor: ExtractorDescriptor, authentication: Authentication, network: NetworkPolicy) -> Result[CottList[MediaItem], MediaError]: ...

"""Empty ranges returns items unchanged. Otherwise validate every range: first
and last are positive inclusive MediaItem.playlist_index values, not list
positions; first greater than last is InvalidRange. Iterate ranges in request
order and items in input order, appending matching items for each range.
Overlapping ranges deliberately repeat occurrences. An out-of-bounds range
contributes no matches. Preserve every MediaItem field, including playlist_index."""
def expand_playlist_ranges(items: CottList[MediaItem], ranges: CottList[PlaylistRange]) -> Result[CottList[MediaItem], MediaError]: ...

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
def select_playlist(items: CottList[MediaItem], request: PlaylistRequest) -> Result[CottList[MediaItem], MediaError]: ...

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
def resolve_live_media(items: CottList[MediaItem], request: LiveRequest) -> Result[CottList[MediaItem], MediaError]: ...

def filter_video(items: CottList[MediaItem], request: VideoFilterRequest) -> Result[CottList[MediaItem], MediaError]: ...

def filter_formats(formats: CottList[FormatDescriptor], request: FormatRequest) -> Result[CottList[FormatDescriptor], MediaError]: ...

def sort_formats(formats: CottList[FormatDescriptor], fields: CottList[str]) -> CottList[FormatDescriptor]: ...

"""None returns typed List[Str]; otherwise preserve requested language order."""
def select_subtitles(item: MediaItem, request: SubtitleRequest) -> Result[CottList[str], MediaError]: ...

"""Return symbolic output names, not URLs or CLI options. When write is true and
formats is empty, append item.id + ".thumbnail". When write is true and formats
is nonempty, append item.id + "." + format for each nonempty format in order.
Independently, a nonempty convert_format appends item.id + "." + convert_format,
even when write is false. Finally embed appends "embed:" + item.id.
Preserve duplicates. No other MediaItem field affects these names."""
def plan_thumbnails(item: MediaItem, request: ThumbnailRequest) -> CottList[str]: ...

"""Return symbolic output names in this flag order: write_info_json appends
item.id + ".info.json"; write_description appends item.id + ".description";
write_comments appends item.id + ".comments.json"; write_playlist_metadata
appends item.id + ".playlist.json"; embed appends "embed:" + item.id.
False flags add nothing. No other MediaItem field changes this pure plan."""
def plan_metadata(item: MediaItem, request: MetadataRequest) -> CottList[str]: ...

def render_output_path(item: MediaItem, template: str, missing_placeholder: str) -> Result[str, MediaError]: ...

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
def resolve_output_path(item: MediaItem, request: OutputRequest) -> Result[Path, MediaError]: ...

"""This client's archive contains plain media ids, one UTF-8 line per entry,
not upstream yt-dlp's extractor-key-plus-id format. Read request.path with
UTF-8-sig decoding, split lines, strip surrounding whitespace and ignore empty
lines. Preserve nonempty line order and duplicates. Reject more than 100000
entries and files exceeding 16 MiB rather than truncating.
Missing/nonregular/symlink files, decoding and actual I/O errors return
ArchiveFailure(path=request.path, message=a fixed descriptive category).
break_on_existing and force_write_archive affect the caller's execution policy,
not this reader. No extractor key is invented and no content is executed."""
def read_download_archive(request: ArchiveRequest) -> Result[CottList[str], MediaError]: ...

def plan_downloads(items: CottList[MediaItem], archive: CottList[str], break_on_existing: bool) -> DownloadPlan: ...

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
def write_download_archive(path: Path, items: CottList[MediaItem]) -> Result[Unit, MediaError]: ...

def plan_fragments(request: TransferRequest, policy: FragmentPolicy) -> Result[CottList[TransferRequest], MediaError]: ...

def transfer_media(request: TransferRequest) -> Result[TransferReceipt, MediaError]: ...

def transfer_fragments(fragments: CottList[TransferRequest], policy: FragmentPolicy) -> Result[CottList[TransferReceipt], MediaError]: ...

"""Serialize each MediaItem as a JSON object whose keys occur in exactly this
order: url, id, title, ext, playlist_index, with their stored values unchanged.
Use ensure_ascii=False and compact separators (",", ":"). Lines joins the
objects with a single newline and no trailing newline; empty input is "".
Single returns one compact JSON array in item order; empty input is "[]".
Do not invent a playlist envelope, rename keys, or sort/deduplicate items."""
def render_items(items: CottList[MediaItem], mode: JsonMode) -> str: ...

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
def plan_post_processing(item: MediaItem, request: PostProcessRequest) -> Result[CottList[ExternalToolRequest], MediaError]: ...

def run_post_processing(requests: CottList[ExternalToolRequest]) -> Result[Unit, MediaError]: ...

"""Return the empty string for Never without inspecting channel. Nightly returns
`yt-dlp/yt-dlp-nightly-builds` and Master returns
`yt-dlp/yt-dlp-master-builds`, ignoring channel. For Check and Apply, strip
outer whitespace from channel: empty or `stable` maps to `yt-dlp/yt-dlp`,
`nightly` maps to `yt-dlp/yt-dlp-nightly-builds`, and `master` maps to
`yt-dlp/yt-dlp-master-builds`. Matching is case-sensitive. Reject every other
value as UpdateUnavailable; never interpret channel as a repository or URL."""
def resolve_update_repository(policy: UpdatePolicy, channel: str) -> Result[str, MediaError]: ...

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
def apply_update(request: UpdateRequest) -> Result[Unit, MediaError]: ...

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
def execute(request: ExecutionRequest) -> Result[ExecutionReport, MediaError]: ...

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
def run(arguments: CottList[str]) -> Never: ...

__all__ = ["ArchiveRequest", "Authentication", "AuthenticationKind", "AuthenticationKind_Anonymous", "AuthenticationKind_BrowserCookies", "AuthenticationKind_Cookies", "AuthenticationKind_Credentials", "AuthenticationKind_Netrc", "CertificatePolicy", "CertificatePolicy_Insecure", "CertificatePolicy_Verify", "CliInput", "DownloadPlan", "ExecutionReport", "ExecutionRequest", "ExternalToolRequest", "ExtractorDescriptor", "ExtractorWorkaround", "ExtractorWorkaround_ForceGeneric", "ExtractorWorkaround_LegacyServerConnect", "ExtractorWorkaround_NoCheckCertificates", "ExtractorWorkaround_NoPlaylist", "FormatContainer", "FormatContainer_Any", "FormatContainer_Audio", "FormatContainer_Best", "FormatContainer_Video", "FormatContainer_Worst", "FormatDescriptor", "FormatRequest", "FragmentPolicy", "GeoBypassMode", "GeoBypassMode_Country", "GeoBypassMode_Default", "GeoBypassMode_Disabled", "GeoBypassMode_IpBlock", "InputKind", "InputKind_Argument", "InputKind_BatchFile", "InputKind_ConfigFile", "JsonMode", "JsonMode_Lines", "JsonMode_Single", "LiveMode", "LiveMode_Default", "LiveMode_FromStart", "LiveMode_Wait", "LiveRequest", "LogLevel", "LogLevel_Debug", "LogLevel_Info", "LogLevel_Quiet", "LogLevel_Warning", "MediaError", "MediaError_ArchiveFailure", "MediaError_AuthenticationFailed", "MediaError_BatchReadFailed", "MediaError_CertificateFailure", "MediaError_CookieFailure", "MediaError_ExternalToolMissing", "MediaError_ExtractorMissing", "MediaError_FormatUnavailable", "MediaError_GeoRestricted", "MediaError_HttpStatus", "MediaError_InvalidConfig", "MediaError_InvalidInput", "MediaError_InvalidRange", "MediaError_InvalidShortcut", "MediaError_InvalidTemplate", "MediaError_LogFailure", "MediaError_NetworkFailure", "MediaError_OutputFailure", "MediaError_PathFailure", "MediaError_PluginRejected", "MediaError_PostProcessFailed", "MediaError_RetryExhausted", "MediaError_SizeLimit", "MediaError_SubtitleUnavailable", "MediaError_UnsupportedUrl", "MediaError_UpdateUnavailable", "MediaError_WorkaroundRejected", "MediaItem", "MetadataRequest", "NetworkPolicy", "OutputRequest", "PlaylistMode", "PlaylistMode_Flat", "PlaylistMode_Playlist", "PlaylistMode_Random", "PlaylistMode_Reverse", "PlaylistMode_Single", "PlaylistRange", "PlaylistRequest", "PluginDescriptor", "PostProcessRequest", "PostProcessorKind", "PostProcessorKind_ConvertThumbnails", "PostProcessorKind_EmbedMetadata", "PostProcessorKind_EmbedSubtitle", "PostProcessorKind_EmbedThumbnail", "PostProcessorKind_ExtractAudio", "PostProcessorKind_Fixup", "PostProcessorKind_RecodeVideo", "PostProcessorKind_RemuxVideo", "PostProcessorKind_SplitChapters", "PostProcessorKind_SponsorBlock", "PresentationRequest", "ProxyMode", "ProxyMode_Direct", "ProxyMode_Http", "ProxyMode_Socks", "ShortcutKind", "ShortcutKind_Search", "ShortcutKind_SearchAll", "ShortcutKind_Url", "ShortcutRequest", "SimulationMode", "SimulationMode_Download", "SimulationMode_PrintOnly", "SimulationMode_Simulate", "SimulationMode_SkipDownload", "SubtitleMode", "SubtitleMode_All", "SubtitleMode_Automatic", "SubtitleMode_Manual", "SubtitleMode_None", "SubtitleRequest", "ThumbnailRequest", "TransferReceipt", "TransferRequest", "UpdatePolicy", "UpdatePolicy_Apply", "UpdatePolicy_Check", "UpdatePolicy_Master", "UpdatePolicy_Never", "UpdatePolicy_Nightly", "UpdateRequest", "VideoFilterRequest", "WorkaroundPolicy", "apply_update", "build_shortcut_url", "choose_extractor", "configure_presentation", "discover_extractors", "execute", "expand_playlist_ranges", "extract_media", "filter_formats", "filter_video", "load_batch_urls", "load_config", "load_plugins", "parse_arguments", "parse_batch_urls", "plan_downloads", "plan_fragments", "plan_metadata", "plan_post_processing", "plan_thumbnails", "read_download_archive", "render_items", "render_output_path", "resolve_authentication", "resolve_inputs", "resolve_live_media", "resolve_output_path", "resolve_update_repository", "run", "run_post_processing", "select_geo_route", "select_playlist", "select_subtitles", "sort_formats", "transfer_fragments", "transfer_media", "validate_network", "validate_workarounds", "write_download_archive"]
