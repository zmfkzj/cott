from cott_runtime import Err, Ok, Result
from real.pgcli_types import ClientError, ClientError_TransactionFailed, TransactionState


def rollback_transaction(transaction: TransactionState) -> Result[TransactionState, ClientError]:
    if not transaction.active:
        return Err(error=ClientError_TransactionFailed(message="cannot roll back an inactive transaction"))
    return Ok(value=TransactionState(mode=transaction.mode, active=False, failed=False))
