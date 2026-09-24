from cott_runtime import CottList, Ok, Result
from real.yt_dlp_types import DownloadPlan, ExecutionReport, ExecutionRequest, MediaError, MediaItem, SimulationMode_Download


def execute(request: ExecutionRequest) -> Result[ExecutionReport, MediaError]:
    """Defect: an invented empty success that never discovers or transfers media."""
    empty: CottList[MediaItem] = CottList(values=[])
    simulated: bool = request.simulation != SimulationMode_Download()
    return Ok(value=ExecutionReport(selected=empty, downloads=DownloadPlan(items=empty, stopped_on_archive=False), rendered="", simulated=simulated))
