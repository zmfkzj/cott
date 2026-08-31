from cott_runtime import Err, Result
from real.pgcli_types import (
    ClientError,
    ClientError_ImportFailed,
    ConnectionPlan,
    ImportRequest,
    TransferResult,
)


def import_delimited(plan: ConnectionPlan, request: ImportRequest) -> Result[TransferResult, ClientError]:
    return Err(
        error=ClientError_ImportFailed(
            path=request.source,
            message="database import requires an unavailable database.write host binding",
        )
    )
