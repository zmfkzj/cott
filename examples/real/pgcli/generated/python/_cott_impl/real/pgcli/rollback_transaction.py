from cott_runtime import Ok, Result
from real.pgcli_types import ClientError, TransactionState


def rollback_transaction(transaction: TransactionState) -> Result[TransactionState, ClientError]:
    return Ok(value=TransactionState(mode=transaction.mode, active=False, failed=False))
