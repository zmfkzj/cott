from cott_runtime import Err, Result
from real.pgcli_types import (
    ConnectionSettings,
    DatabaseError,
    DatabaseError_ConnectionFailed,
    QueryResult,
)


def execute_query(connection: ConnectionSettings, sql: str) -> Result[QueryResult, DatabaseError]:
    return Err(
        error=DatabaseError_ConnectionFailed(
            message="query execution requires an unavailable database host binding",
        )
    )
