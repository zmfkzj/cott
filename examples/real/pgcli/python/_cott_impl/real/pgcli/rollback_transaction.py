import cott_runtime
from cott_runtime import Result
from real.pgcli_types import ClientError, ClientError_TransactionFailed, TransactionState, TransactionStatus_Idle


def rollback_transaction(transaction: TransactionState) -> Result[TransactionState, ClientError]:
    if isinstance(transaction.status, TransactionStatus_Idle):
        return cott_runtime.Err(error=ClientError_TransactionFailed(message="no transaction is open"))
    return cott_runtime.Ok(value=TransactionState(mode=transaction.mode, status=TransactionStatus_Idle()))
