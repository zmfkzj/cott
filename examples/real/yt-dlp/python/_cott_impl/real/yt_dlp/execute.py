from cott_runtime import CottList, Err, Ok, Result, Unit
from real.yt_dlp import apply_update
from real.yt_dlp_types import DownloadPlan, ExecutionReport, ExecutionRequest, MediaError, MediaItem, SimulationMode_Download, SimulationMode_PrintOnly, SimulationMode_Simulate, SimulationMode_SkipDownload


def execute(request: ExecutionRequest) -> Result[ExecutionReport, MediaError]:
    update_result: Result[Unit, MediaError] = apply_update(request.update)
    if isinstance(update_result, Err):
        return Err(error=update_result.error)
    simulated: bool
    match request.simulation:
        case SimulationMode_Download():
            simulated = False
        case SimulationMode_Simulate():
            simulated = True
        case SimulationMode_SkipDownload():
            simulated = True
        case SimulationMode_PrintOnly():
            simulated = True
    selected: CottList[MediaItem] = CottList(values=[])
    planned: CottList[MediaItem] = CottList(values=[])
    return Ok(value=ExecutionReport(selected=selected, downloads=DownloadPlan(items=planned, stopped_on_archive=False), rendered="", simulated=simulated))
