import time

from cott_runtime import Err, Ok, Result, U64
from real.pgcli import execute_planned_query
from real.pgcli_types import ClientError, WatchRequest, WatchResult


def watch_query(request: WatchRequest) -> Result[WatchResult, ClientError]:
    outcome = execute_planned_query(request.query)
    if not isinstance(outcome, Ok):
        return Err(error=outcome.error)
    last = outcome.value
    executions: U64 = 1
    while executions < request.max_iterations:
        time.sleep(request.interval_ms / 1000)
        outcome = execute_planned_query(request.query)
        if not isinstance(outcome, Ok):
            return Err(error=outcome.error)
        last = outcome.value
        executions += 1
    return Ok(value=WatchResult(executions=executions, last_result=last))
