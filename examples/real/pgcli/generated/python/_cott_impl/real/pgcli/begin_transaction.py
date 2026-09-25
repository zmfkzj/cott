from real.pgcli_types import TransactionMode, TransactionState, TransactionStatus_Active


def begin_transaction(mode: TransactionMode) -> TransactionState:
    return TransactionState(mode=mode, status=TransactionStatus_Active())
