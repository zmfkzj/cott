from cott_runtime import Err, Ok, Result
from real.pgcli import execute_planned_query
from real.pgcli_types import ClientError, ClientError_QueryFailed, WatchRequest, WatchResult


def watch_query(request: WatchRequest) -> Result[WatchResult, ClientError]:
    if request.max_iterations <= 0:
        return Err(error=ClientError_QueryFailed(message="watch requires at least one iteration"))

    match execute_planned_query(request.query):
        case Ok(value=executed):
            last_result = executed
        case Err(error=error):
            return Err(error=error)

    executions = 1
    while executions < request.max_iterations:
        match execute_planned_query(request.query):
            case Ok(value=executed):
                last_result = executed
            case Err(error=error):
                return Err(error=error)
        executions += 1

    return Ok(value=WatchResult(executions=executions, last_result=last_result))
