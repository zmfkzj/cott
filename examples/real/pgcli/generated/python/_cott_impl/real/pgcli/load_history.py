from cott_runtime import CottList, Err, Result
from real.pgcli_types import ClientError, ClientError_HistoryFailed, HistoryEntry, HistoryPolicy


def load_history(policy: HistoryPolicy) -> Result[CottList[HistoryEntry], ClientError]:
    return Err(
        error=ClientError_HistoryFailed(
            path=policy.path,
            message="history loading requires an unavailable file.read host binding",
        )
    )
