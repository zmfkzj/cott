from cott_runtime import Err, Ok, Result
from real.pgcli_types import ClientError, ClientError_TransactionFailed, TransactionState, TransactionStatus_Active, TransactionStatus_Failed, TransactionStatus_Idle


def commit_transaction(transaction: TransactionState) -> Result[TransactionState, ClientError]:
    status = transaction.status
    if isinstance(status, TransactionStatus_Failed):
        return Err(error=ClientError_TransactionFailed(message="cannot commit a failed transaction"))
    if not isinstance(status, TransactionStatus_Active):
        return Err(error=ClientError_TransactionFailed(message="no active transaction to commit"))
    return Ok(value=TransactionState(mode=transaction.mode, status=TransactionStatus_Idle()))
