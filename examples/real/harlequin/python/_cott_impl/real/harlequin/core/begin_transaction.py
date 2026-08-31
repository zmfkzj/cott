from cott_runtime import Ok, Result
from real.harlequin.core_types import Connection, ConnectionError, Transaction


def begin_transaction(connection: Connection) -> Result[Transaction, ConnectionError]:
    return Ok(value=Transaction(connection_id=connection.id, active=True))
