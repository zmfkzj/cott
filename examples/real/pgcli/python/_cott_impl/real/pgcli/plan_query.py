from cott_runtime import Err, Result

from real.pgcli_types import ClientError, ClientError_InvalidSql, InputBuffer, QueryPlan


def plan_query(buffer: InputBuffer) -> Result[QueryPlan, ClientError]:
    return Err(error=ClientError_InvalidSql(message=""))
