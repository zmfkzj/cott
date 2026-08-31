from real.pgcli_types import (
    TransactionMode,
    TransactionMode_AutoCommit,
    TransactionMode_Manual,
    TransactionMode_ReadOnly,
    TransactionState,
)


def begin_transaction(mode: TransactionMode) -> TransactionState:
    match mode:
        case TransactionMode_AutoCommit():
            return TransactionState(mode=mode, active=False, failed=False)
        case TransactionMode_Manual():
            return TransactionState(mode=mode, active=True, failed=False)
        case TransactionMode_ReadOnly():
            return TransactionState(mode=mode, active=True, failed=False)
