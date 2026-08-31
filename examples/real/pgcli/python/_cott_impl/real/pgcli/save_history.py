from cott_runtime import CottList, Err, Result, Unit
from real.pgcli_types import ClientError, ClientError_HistoryFailed, HistoryEntry, HistoryPolicy


def save_history(policy: HistoryPolicy, entries: CottList[HistoryEntry]) -> Result[Unit, ClientError]:
    return Err(
        error=ClientError_HistoryFailed(
            path=policy.path,
            message="history saving requires an unavailable file.write host binding",
        )
    )
