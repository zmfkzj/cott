from real.pgcli_types import TransactionMode, TransactionState


def begin_transaction(mode: TransactionMode) -> TransactionState:
    return TransactionState(mode=mode, active=True, failed=False)
