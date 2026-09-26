from typing import cast

import psycopg
from psycopg.pq import TransactionStatus as PqTransactionStatus

from real.pgcli.connection_types import Executor, TransactionStatus, TransactionStatus_Active, TransactionStatus_Idle, TransactionStatus_InError, TransactionStatus_InTransaction, TransactionStatus_Unknown


def executor_transaction_status(executor: Executor) -> TransactionStatus:
    conn = cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())
    if conn.closed:
        return TransactionStatus_Unknown()
    status = conn.info.transaction_status
    if status == PqTransactionStatus.IDLE:
        return TransactionStatus_Idle()
    if status == PqTransactionStatus.ACTIVE:
        return TransactionStatus_Active()
    if status == PqTransactionStatus.INTRANS:
        return TransactionStatus_InTransaction()
    if status == PqTransactionStatus.INERROR:
        return TransactionStatus_InError()
    return TransactionStatus_Unknown()
