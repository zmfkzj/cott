from cott_runtime import Err, Ok, Result
from real.pgcli_types import ClientError, ClientError_TransactionFailed, TransactionState


def commit_transaction(transaction: TransactionState) -> Result[TransactionState, ClientError]:
    if not transaction.active:
        return Err(error=ClientError_TransactionFailed(message="cannot commit an inactive transaction"))
    if transaction.failed:
        return Err(error=ClientError_TransactionFailed(message="cannot commit a failed transaction"))
    return Ok(value=TransactionState(mode=transaction.mode, active=False, failed=False))
