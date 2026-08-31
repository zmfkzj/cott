from cott_runtime import Err, Result, Unit
from real.pgcli_types import ConnectionError, ConnectionError_ConnectionFailed, ConnectionPlan


def connect(plan: ConnectionPlan) -> Result[Unit, ConnectionError]:
    return Err(error=ConnectionError_ConnectionFailed(message="database connection requires an unavailable network host binding"))
