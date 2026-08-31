from pathlib import Path

from cott_runtime import CottList, Err, Ok, Result, Unit
from real.yt_dlp import (
    apply_update,
    build_shortcut_url,
    choose_extractor,
    configure_presentation,
    discover_extractors,
    extract_media,
    filter_video,
    load_batch_urls,
    load_config,
    plan_downloads,
    plan_fragments,
    plan_metadata,
    plan_post_processing,
    plan_thumbnails,
    read_download_archive,
    render_items,
    resolve_authentication,
    resolve_inputs,
    resolve_live_media,
    resolve_output_path,
    run_post_processing,
    select_geo_route,
    select_playlist,
    select_subtitles,
    transfer_fragments,
    validate_network,
    validate_workarounds,
    write_download_archive,
)
from real.yt_dlp_types import (
    Authentication,
    CliInput,
    DownloadPlan,
    ExecutionReport,
    ExecutionRequest,
    ExternalToolRequest,
    ExtractorDescriptor,
    InputKind_Argument,
    InputKind_BatchFile,
    InputKind_ConfigFile,
    MediaError,
    MediaError_InvalidInput,
    MediaItem,
    NetworkPolicy,
    SimulationMode_Download,
    SimulationMode_PrintOnly,
    SimulationMode_Simulate,
    SimulationMode_SkipDownload,
    TransferReceipt,
    TransferRequest,
)


def _finalize_execution(request: ExecutionRequest, selected: CottList[MediaItem], downloads: DownloadPlan, simulated: bool) -> Result[ExecutionReport, MediaError]:
    if request.archive.path != Path() and (not simulated or request.archive.force_write_archive):
        match write_download_archive(request.archive.path, downloads.items):
            case Err(error=error):
                return Err(error=error)
            case Ok():
                rendered: str = render_items(selected, request.json_mode)
    else:
        rendered = render_items(selected, request.json_mode)

    return Ok(
        value=ExecutionReport(
            selected=selected,
            downloads=downloads,
            rendered=rendered,
            simulated=simulated,
        )
    )


def execute(request: ExecutionRequest) -> Result[ExecutionReport, MediaError]:
    match validate_workarounds(request.workarounds):
        case Err(error=error):
            return Err(error=error)
        case Ok(value=workarounds):
            network_result: Result[NetworkPolicy, MediaError] = validate_network(request.network)

    match network_result:
        case Err(error=error):
            return Err(error=error)
        case Ok(value=network):
            route_result: Result[NetworkPolicy, MediaError] = select_geo_route(network)

    match route_result:
        case Err(error=error):
            return Err(error=error)
        case Ok(value=routed_network):
            authentication_result: Result[Authentication, MediaError] = resolve_authentication(request.authentication)

    match authentication_result:
        case Err(error=error):
            return Err(error=error)
        case Ok(value=authentication):
            presentation_result: Result[Unit, MediaError] = configure_presentation(request.presentation)

    match presentation_result:
        case Err(error=error):
            return Err(error=error)
        case Ok():
            update_result: Result[Unit, MediaError] = apply_update(request.update)

    match update_result:
        case Err(error=error):
            return Err(error=error)
        case Ok():
            comment_prefixes: CottList[str] = CottList(values=("#", ";", "]"))
            pending_inputs: list[tuple[CliInput, bool]] = [(item, False) for item in request.inputs]

    command_inputs: list[CliInput] = []
    config_inputs: list[CliInput] = []
    pending_index: int = 0
    while pending_index < len(pending_inputs):
        if pending_index == 100000:
            return Err(error=MediaError_InvalidInput(message="input expansion contains more than 100000 entries"))
        input_item: CliInput
        from_config: bool
        input_item, from_config = pending_inputs[pending_index]
        pending_index += 1
        match input_item.kind:
            case InputKind_Argument():
                if from_config:
                    config_inputs.append(input_item)
                else:
                    command_inputs.append(input_item)
            case InputKind_ConfigFile():
                match load_config(Path(input_item.value)):
                    case Err(error=error):
                        return Err(error=error)
                    case Ok(value=loaded_inputs):
                        loaded_input: CliInput
                        for loaded_input in loaded_inputs:
                            pending_inputs.append((loaded_input, True))
            case InputKind_BatchFile():
                match load_batch_urls(Path(input_item.value), comment_prefixes):
                    case Err(error=error):
                        return Err(error=error)
                    case Ok(value=batch_urls):
                        batch_url: str
                        for batch_url in batch_urls:
                            expanded_input: CliInput = CliInput(kind=InputKind_Argument(), value=batch_url)
                            if from_config:
                                config_inputs.append(expanded_input)
                            else:
                                command_inputs.append(expanded_input)

    if request.shortcut.query != "":
        match build_shortcut_url(request.shortcut):
            case Err(error=error):
                return Err(error=error)
            case Ok(value=shortcut_url):
                command_inputs.append(CliInput(kind=InputKind_Argument(), value=shortcut_url))

    match resolve_inputs(CottList(values=tuple(command_inputs)), CottList(values=tuple(config_inputs))):
        case Err(error=error):
            return Err(error=error)
        case Ok(value=urls):
            discovered_extractors: CottList[ExtractorDescriptor] = discover_extractors()

    if workarounds.force_generic_extractor:
        generic_extractors: list[ExtractorDescriptor] = []
        discovered_extractor: ExtractorDescriptor
        for discovered_extractor in discovered_extractors:
            if discovered_extractor.name == "generic":
                generic_extractors.append(discovered_extractor)
        available_extractors: CottList[ExtractorDescriptor] = CottList(values=tuple(generic_extractors))
    else:
        available_extractors = discovered_extractors

    extracted_items: list[MediaItem] = []
    url: str
    for url in urls:
        match choose_extractor(url, available_extractors):
            case Err(error=error):
                return Err(error=error)
            case Ok(value=extractor):
                extraction_result: Result[CottList[MediaItem], MediaError] = extract_media(
                    url,
                    extractor,
                    authentication,
                    routed_network,
                )
        match extraction_result:
            case Err(error=error):
                return Err(error=error)
            case Ok(value=media_items):
                media_item: MediaItem
                for media_item in media_items:
                    extracted_items.append(media_item)

    all_items: CottList[MediaItem] = CottList(values=tuple(extracted_items))
    match select_playlist(all_items, request.playlist):
        case Err(error=error):
            return Err(error=error)
        case Ok(value=playlist_items):
            live_result: Result[CottList[MediaItem], MediaError] = resolve_live_media(playlist_items, request.live)

    match live_result:
        case Err(error=error):
            return Err(error=error)
        case Ok(value=live_items):
            video_result: Result[CottList[MediaItem], MediaError] = filter_video(live_items, request.video_filter)

    match video_result:
        case Err(error=error):
            return Err(error=error)
        case Ok(value=selected):
            selected_item: MediaItem
            for selected_item in selected:
                match select_subtitles(selected_item, request.subtitles):
                    case Err(error=error):
                        return Err(error=error)
                    case Ok():
                        plan_thumbnails(selected_item, request.thumbnails)
                        plan_metadata(selected_item, request.metadata)

    if request.archive.path == Path():
        archive_entries: CottList[str] = CottList(values=())
    else:
        match read_download_archive(request.archive):
            case Err(error=error):
                return Err(error=error)
            case Ok(value=loaded_archive_entries):
                archive_entries = loaded_archive_entries

    downloads: DownloadPlan = plan_downloads(selected, archive_entries, request.archive.break_on_existing)
    match request.simulation:
        case SimulationMode_Download():
            simulated: bool = False
            perform_transfers: bool = True
        case SimulationMode_Simulate():
            simulated = True
            perform_transfers = True
        case SimulationMode_SkipDownload() | SimulationMode_PrintOnly():
            simulated = True
            perform_transfers = False

    post_processing_requests: list[ExternalToolRequest] = []
    download_item: MediaItem
    for download_item in downloads.items:
        match resolve_output_path(download_item, request.output):
            case Err(error=error):
                return Err(error=error)
            case Ok(value=destination):
                if request.formats.max_file_size > 0:
                    maximum_bytes: int = request.formats.max_file_size
                else:
                    maximum_bytes = 18446744073709551615

        post_processing_result: Result[CottList[ExternalToolRequest], MediaError]
        if perform_transfers:
            transfer_request: TransferRequest = TransferRequest(
                url=download_item.url,
                destination=destination,
                simulate=simulated,
                max_bytes=maximum_bytes,
            )
            match plan_fragments(transfer_request, request.fragments):
                case Err(error=error):
                    return Err(error=error)
                case Ok(value=fragment_requests):
                    fragment_transfer_result: Result[CottList[TransferReceipt], MediaError] = transfer_fragments(
                        fragment_requests,
                        request.fragments,
                    )
            match fragment_transfer_result:
                case Err(error=error):
                    return Err(error=error)
                case Ok():
                    post_processing_result = plan_post_processing(download_item, request.post_processing)
        else:
            post_processing_result = plan_post_processing(download_item, request.post_processing)

        match post_processing_result:
            case Err(error=error):
                return Err(error=error)
            case Ok(value=planned_post_processing):
                post_processing_request: ExternalToolRequest
                for post_processing_request in planned_post_processing:
                    post_processing_requests.append(post_processing_request)

    if simulated:
        return _finalize_execution(request, selected, downloads, simulated)

    match run_post_processing(CottList(values=tuple(post_processing_requests))):
        case Err(error=error):
            return Err(error=error)
        case Ok():
            final_result: Result[ExecutionReport, MediaError] = _finalize_execution(request, selected, downloads, simulated)
    return final_result
