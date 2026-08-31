from cott_runtime import Err, Result, Unit
from real.pgcli_types import ClientError, ClientError_TerminalFailed, InteractiveRequest


def run_interactive(request: InteractiveRequest) -> Result[Unit, ClientError]:
    return Err(
        error=ClientError_TerminalFailed(
            message="interactive terminal support is unavailable",
        )
    )
