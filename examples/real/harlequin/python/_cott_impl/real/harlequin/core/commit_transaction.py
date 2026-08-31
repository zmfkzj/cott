from cott_runtime import Ok, Result
from real.harlequin.core_types import ConnectionError, Transaction


def commit_transaction(transaction: Transaction) -> Result[Transaction, ConnectionError]:
    return Ok(value=Transaction(connection_id=transaction.connection_id, active=False))
