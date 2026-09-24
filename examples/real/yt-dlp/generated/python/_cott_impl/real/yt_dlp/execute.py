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
                        nested_error = _batch_arguments(Path(nested.value), out)
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
    match resolve_output_path(item, request.output):
        case Err(error=path_error):
            return path_error
        case Ok(value=destination):
            transfer = TransferRequest(url=item.url, destination=destination, simulate=False, max_bytes=request.formats.max_file_size)
    match plan_fragments(transfer, request.fragments):
        case Err(error=plan_error):
            return plan_error
        case Ok(value=fragments):
            transferred = transfer_fragments(fragments, request.fragments)
    if isinstance(transferred, Err):
        return transferred.error
    if len(request.post_processing.kinds) == 0:
        return None
    match plan_post_processing(item, request.post_processing):
        case Err(error=pp_plan_error):
            return pp_plan_error
        case Ok(value=tools):
            processed = run_post_processing(tools)
    if isinstance(processed, Err):
        return processed.error
    return None


def _download(request: ExecutionRequest, plan: DownloadPlan) -> MediaError | None:
    for item in plan.items:
        failure = _download_item(request, item)
        if failure is not None:
            return failure
    return None


def execute(request: ExecutionRequest) -> Result[ExecutionReport, MediaError]:
    updated = apply_update(request.update)
    if isinstance(updated, Err):
        return Err(error=updated.error)
    match validate_network(request.network):
        case Err(error=network_error):
            return Err(error=network_error)
        case Ok(value=validated_network):
            routed = select_geo_route(validated_network)
    match routed:
        case Err(error=geo_error):
            return Err(error=geo_error)
        case Ok(value=network):
            authenticated = resolve_authentication(request.authentication)
    match authenticated:
        case Err(error=auth_error):
            return Err(error=auth_error)
        case Ok(value=authentication):
            workarounds = validate_workarounds(request.workarounds)
    if isinstance(workarounds, Err):
        return Err(error=workarounds.error)
    if Path(request.presentation.log_file) != Path("."):
        configured = configure_presentation(request.presentation)
        if isinstance(configured, Err):
            return Err(error=configured.error)

    match _expand_inputs(request):
        case Err(error=input_error):
            return Err(error=input_error)
        case Ok(value=arguments):
            resolved_result = resolve_inputs(arguments, CottList(values=[]))
    match resolved_result:
        case Err(error=resolve_error):
            return Err(error=resolve_error)
        case Ok(value=resolved):
            urls: list[str] = [url for url in resolved]
    if len(request.shortcut.query) > 0:
        match build_shortcut_url(request.shortcut):
            case Err(error=shortcut_error):
                return Err(error=shortcut_error)
            case Ok(value=shortcut_url):
                urls.append(shortcut_url)
    if len(urls) == 0:
        return Err(error=MediaError_InvalidInput(message="no input URLs supplied"))

    extractors = discover_extractors()
    discovered: list[MediaItem] = []
    for url in urls:
        match choose_extractor(url, extractors):
            case Err(error=choose_error):
                return Err(error=choose_error)
            case Ok(value=extractor):
                extraction = extract_media(url, extractor, authentication, network)
        match extraction:
            case Err(error=extract_error):
                return Err(error=extract_error)
            case Ok(value=extracted):
                discovered.extend(extracted)

    match select_playlist(CottList(values=discovered), request.playlist):
        case Err(error=playlist_error):
            return Err(error=playlist_error)
        case Ok(value=playlist_items):
            live_result = resolve_live_media(playlist_items, request.live)
    match live_result:
        case Err(error=live_error):
            return Err(error=live_error)
        case Ok(value=live_items):
            filtered = filter_video(live_items, request.video_filter)
    match filtered:
        case Err(error=filter_error):
            return Err(error=filter_error)
        case Ok(value=selected):
            archive_enabled: bool = Path(request.archive.path) != Path(".")

    archive_entries: CottList[str] = CottList(values=[])
    if archive_enabled:
        match read_download_archive(request.archive):
            case Err(error=archive_error):
                return Err(error=archive_error)
            case Ok(value=entries):
                archive_entries = entries
    plan: DownloadPlan = plan_downloads(selected, archive_entries, request.archive.break_on_existing)

    simulated: bool
    match request.simulation:
        case SimulationMode_Download():
            simulated = False
            download_error = _download(request, plan)
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
