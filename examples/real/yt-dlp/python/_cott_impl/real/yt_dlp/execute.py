from pathlib import Path

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp import apply_update, build_shortcut_url, choose_extractor, configure_presentation, discover_extractors, extract_media, filter_video, load_batch_urls, load_config, plan_downloads, plan_fragments, plan_post_processing, read_download_archive, render_items, resolve_authentication, resolve_inputs, resolve_live_media, resolve_output_path, run_post_processing, select_geo_route, select_playlist, transfer_fragments, validate_network, validate_workarounds, write_download_archive
from real.yt_dlp_types import CliInput, DownloadPlan, ExecutionReport, ExecutionRequest, InputKind_Argument, InputKind_BatchFile, InputKind_ConfigFile, MediaError, MediaError_InvalidInput, MediaItem, SimulationMode_Download, SimulationMode_PrintOnly, SimulationMode_Simulate, SimulationMode_SkipDownload, TransferRequest


def _batch_arguments(path: Path, out: list[CliInput]) -> MediaError | None:
    match load_batch_urls(path, CottList(values=["#"])):
        case Err(error=error):
            return error
        case Ok(value=urls):
            for url in urls:
                out.append(CliInput(kind=InputKind_Argument(), value=url))
            return None


def _expand_config(path: Path, out: list[CliInput]) -> MediaError | None:
    match load_config(path):
        case Err(error=config_error):
            return config_error
        case Ok(value=loaded):
            for nested in loaded:
                match nested.kind:
                    case InputKind_Argument():
                        out.append(CliInput(kind=InputKind_Argument(), value=nested.value))
                    case InputKind_BatchFile():
                        nested_error: MediaError | None = _batch_arguments(Path(nested.value), out)
                        if nested_error is not None:
                            return nested_error
                    case InputKind_ConfigFile():
                        return MediaError_InvalidInput(message="nested config files are not supported")
            return None


def _expand_inputs(request: ExecutionRequest) -> Result[CottList[CliInput], MediaError]:
    out: list[CliInput] = []
    for entry in request.inputs:
        failure: MediaError | None = None
        match entry.kind:
            case InputKind_Argument():
                out.append(CliInput(kind=InputKind_Argument(), value=entry.value))
            case InputKind_BatchFile():
                failure = _batch_arguments(Path(entry.value), out)
            case InputKind_ConfigFile():
                failure = _expand_config(Path(entry.value), out)
        if failure is not None:
            return Err(error=failure)
    return Ok(value=CottList(values=out))


def _download_item(request: ExecutionRequest, item: MediaItem) -> MediaError | None:
    path_result = resolve_output_path(item, request.output)
    if isinstance(path_result, Err):
        return path_result.error
    transfer: TransferRequest = TransferRequest(url=item.url, destination=path_result.value, simulate=False, max_bytes=request.formats.max_file_size)
    fragments = plan_fragments(transfer, request.fragments)
    if isinstance(fragments, Err):
        return fragments.error
    transferred = transfer_fragments(fragments.value, request.fragments)
    if isinstance(transferred, Err):
        return transferred.error
    if len(request.post_processing.kinds) == 0:
        return None
    tools = plan_post_processing(item, request.post_processing)
    if isinstance(tools, Err):
        return tools.error
    processed = run_post_processing(tools.value)
    if isinstance(processed, Err):
        return processed.error
    return None


def _download(request: ExecutionRequest, plan: DownloadPlan) -> MediaError | None:
    for item in plan.items:
        failure: MediaError | None = _download_item(request, item)
        if failure is not None:
            return failure
    return None


def execute(request: ExecutionRequest) -> Result[ExecutionReport, MediaError]:
    updated = apply_update(request.update)
    if isinstance(updated, Err):
        return Err(error=updated.error)
    validated = validate_network(request.network)
    if isinstance(validated, Err):
        return Err(error=validated.error)
    routed = select_geo_route(validated.value)
    if isinstance(routed, Err):
        return Err(error=routed.error)
    network = routed.value
    authenticated = resolve_authentication(request.authentication)
    if isinstance(authenticated, Err):
        return Err(error=authenticated.error)
    authentication = authenticated.value
    workarounds = validate_workarounds(request.workarounds)
    if isinstance(workarounds, Err):
        return Err(error=workarounds.error)
    if Path(request.presentation.log_file) != Path("."):
        logged = configure_presentation(request.presentation)
        if isinstance(logged, Err):
            return Err(error=logged.error)

    expanded = _expand_inputs(request)
    if isinstance(expanded, Err):
        return Err(error=expanded.error)
    resolved = resolve_inputs(expanded.value, CottList(values=[]))
    if isinstance(resolved, Err):
        return Err(error=resolved.error)
    urls: list[str] = []
    for url in resolved.value:
        urls.append(url)
    if len(request.shortcut.query) > 0:
        shortcut = build_shortcut_url(request.shortcut)
        if isinstance(shortcut, Err):
            return Err(error=shortcut.error)
        urls.append(shortcut.value)
    if len(urls) == 0:
        return Err(error=MediaError_InvalidInput(message="no input URLs supplied"))

    extractors = discover_extractors()
    discovered: list[MediaItem] = []
    for target in urls:
        chosen = choose_extractor(target, extractors)
        if isinstance(chosen, Err):
            return Err(error=chosen.error)
        extraction = extract_media(target, chosen.value, authentication, network)
        if isinstance(extraction, Err):
            return Err(error=extraction.error)
        for found in extraction.value:
            discovered.append(found)

    playlist = select_playlist(CottList(values=discovered), request.playlist)
    if isinstance(playlist, Err):
        return Err(error=playlist.error)
    live = resolve_live_media(playlist.value, request.live)
    if isinstance(live, Err):
        return Err(error=live.error)
    filtered = filter_video(live.value, request.video_filter)
    if isinstance(filtered, Err):
        return Err(error=filtered.error)
    selected: CottList[MediaItem] = filtered.value

    archive_enabled: bool = Path(request.archive.path) != Path(".")
    archive_entries: CottList[str] = CottList(values=[])
    if archive_enabled:
        read = read_download_archive(request.archive)
        if isinstance(read, Err):
            return Err(error=read.error)
        archive_entries = read.value
    plan: DownloadPlan = plan_downloads(selected, archive_entries, request.archive.break_on_existing)

    simulated: bool
    match request.simulation:
        case SimulationMode_Download():
            simulated = False
            download_error: MediaError | None = _download(request, plan)
            if download_error is not None:
                return Err(error=download_error)
            if archive_enabled and (len(plan.items) > 0 or request.archive.force_write_archive):
                written = write_download_archive(request.archive.path, plan.items)
                if isinstance(written, Err):
                    return Err(error=written.error)
        case SimulationMode_Simulate() | SimulationMode_SkipDownload() | SimulationMode_PrintOnly():
            simulated = True

    rendered: str = render_items(selected, request.json_mode)
    return Ok(value=ExecutionReport(selected=selected, downloads=plan, rendered=rendered, simulated=simulated))
