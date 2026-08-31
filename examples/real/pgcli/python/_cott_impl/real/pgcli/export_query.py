from cott_runtime import Err, Result
from real.pgcli_types import (
    ClientError,
    ClientError_ExportFailed,
    ConnectionPlan,
    ExportRequest,
    TransferResult,
)


def export_query(plan: ConnectionPlan, request: ExportRequest) -> Result[TransferResult, ClientError]:
    return Err(
        error=ClientError_ExportFailed(
            path=request.target,
            message="database export requires an unavailable database.read host binding",
        )
    )
