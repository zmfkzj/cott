import sys
from pathlib import Path
from typing import Never

from cott_runtime import CottList, Err, Nothing, Ok
from real.yt_dlp import execute, parse_arguments
from real.yt_dlp_types import (
    ArchiveRequest,
    Authentication,
    AuthenticationKind_Anonymous,
    CertificatePolicy_Verify,
    ExecutionRequest,
    FormatRequest,
    FragmentPolicy,
    GeoBypassMode_Default,
    JsonMode_Lines,
    LiveMode_Default,
    LiveRequest,
    LogLevel_Info,
    MetadataRequest,
    NetworkPolicy,
    OutputRequest,
    PlaylistMode_Playlist,
    PlaylistRequest,
    PostProcessRequest,
    PresentationRequest,
    ProxyMode_Direct,
    ShortcutKind_Url,
    ShortcutRequest,
    SimulationMode_Download,
    SubtitleMode_None,
    SubtitleRequest,
    ThumbnailRequest,
    UpdatePolicy_Never,
    UpdateRequest,
    VideoFilterRequest,
    WorkaroundPolicy,
)


def run(arguments: CottList[str]) -> Never:
    match parse_arguments(arguments):
        case Err(error=error):
            sys.stderr.write(f"{error}\n")
            sys.exit(1)
        case Ok(value=inputs):
            request: ExecutionRequest = ExecutionRequest(
                inputs=inputs,
                network=NetworkPolicy(
                    proxy_mode=ProxyMode_Direct(),
                    proxy="",
                    socket_timeout_ms=30000,
                    source_address="",
                    force_ipv4=False,
                    force_ipv6=False,
                    geo_mode=GeoBypassMode_Default(),
                    geo_country="",
                    geo_ip_block="",
                ),
                authentication=Authentication(
                    kind=AuthenticationKind_Anonymous(),
                    username="",
                    password="",
                    netrc_location=Path(),
                    cookie_file=Path(),
                    browser="",
                    profile="",
                ),
                playlist=PlaylistRequest(
                    mode=PlaylistMode_Playlist(),
                    ranges=CottList(values=()),
                    start=0,
                    end=0,
                    items="",
                    reverse=False,
                    random=False,
                ),
                live=LiveRequest(
                    mode=LiveMode_Default(),
                    wait_for_video_ms=0,
                    concurrent_fragments=1,
                ),
                video_filter=VideoFilterRequest(
                    date_after="",
                    date_before="",
                    min_views=0,
                    max_views=0,
                    age_limit=0,
                    match_filter="",
                    reject_live=False,
                    include_ads=True,
                ),
                shortcut=ShortcutRequest(
                    kind=ShortcutKind_Url(),
                    query="",
                    limit=1,
                ),
                formats=FormatRequest(
                    selector="",
                    containers=CottList(values=()),
                    sort_fields=CottList(values=()),
                    merge_output_format="",
                    min_file_size=0,
                    max_file_size=104857600,
                    prefer_free_formats=False,
                ),
                subtitles=SubtitleRequest(
                    mode=SubtitleMode_None(),
                    languages=CottList(values=()),
                    formats=CottList(values=()),
                    convert_format="",
                    embed=False,
                ),
                thumbnails=ThumbnailRequest(
                    write=False,
                    formats=CottList(values=()),
                    convert_format="",
                    embed=False,
                ),
                metadata=MetadataRequest(
                    write_info_json=False,
                    write_description=False,
                    write_comments=False,
                    write_playlist_metadata=False,
                    embed=False,
                ),
                output=OutputRequest(
                    template="%(title)s.%(ext)s",
                    home=Path(),
                    temp=Path(".tmp"),
                    output=Path(),
                    missing_placeholder="NA",
                    restrict_filenames=False,
                    windows_filenames=False,
                    trim_filename_bytes=0,
                ),
                archive=ArchiveRequest(
                    path=Path(),
                    break_on_existing=False,
                    force_write_archive=False,
                ),
                fragments=FragmentPolicy(
                    concurrent_fragments=1,
                    buffer_size=65536,
                    chunk_size=104857600,
                    rate_limit_bytes_per_second=0,
                    retries=3,
                    fragment_retries=3,
                    file_access_retries=3,
                    continue_download=True,
                    part_files=True,
                ),
                post_processing=PostProcessRequest(
                    kinds=CottList(values=()),
                    audio_format="",
                    video_format="",
                    sponsorblock_categories=CottList(values=()),
                    external_tool=Nothing(),
                ),
                simulation=SimulationMode_Download(),
                json_mode=JsonMode_Lines(),
                update=UpdateRequest(
                    policy=UpdatePolicy_Never(),
                    channel="",
                    target=Path(),
                ),
                presentation=PresentationRequest(
                    level=LogLevel_Info(),
                    progress=True,
                    newline_progress=False,
                    color=True,
                    dump_pages=False,
                    write_pages=False,
                    log_file=Path(),
                ),
                workarounds=WorkaroundPolicy(
                    certificate=CertificatePolicy_Verify(),
                    force_generic_extractor=False,
                    legacy_server_connect=False,
                    extractor_args=CottList(values=()),
                ),
            )

    match execute(request):
        case Err(error=error):
            sys.stderr.write(f"{error}\n")
            sys.exit(1)
        case Ok(value=report):
            if report.rendered != "":
                sys.stdout.write(report.rendered + "\n")
            sys.exit(0)
