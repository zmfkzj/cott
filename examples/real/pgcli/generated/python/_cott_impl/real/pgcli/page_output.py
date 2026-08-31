from cott_runtime import Err, Result, Unit
from real.pgcli_types import ClientError, ClientError_PagerFailed, PagerRequest


def page_output(request: PagerRequest) -> Result[Unit, ClientError]:
    return Err(
        error=ClientError_PagerFailed(
            message="pager requires an unavailable file host binding",
        )
    )
