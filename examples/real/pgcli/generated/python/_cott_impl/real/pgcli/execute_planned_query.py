from cott_runtime import Err, Result
from real.pgcli_types import ClientError, ClientError_QueryFailed, ExecutedQuery, QueryRequest


def execute_planned_query(request: QueryRequest) -> Result[ExecutedQuery, ClientError]:
    return Err(error=ClientError_QueryFailed(message="query execution requires an unavailable database host binding"))
