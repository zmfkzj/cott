import sqlite3
from pathlib import Path

from cott_runtime import CottContractViolation, Err, Ok, Result
from curriculum.effects_selection_types import EffectError, EffectError_OperationFailed


def store_and_load(database: Path, key: str, value: str) -> Result[str, EffectError]:
    try:
        connection = sqlite3.connect(database)
        try:
            with connection:
                connection.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                connection.execute("INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)", (key, value))
            row = connection.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
        finally:
            connection.close()
    except (sqlite3.Error, OSError, CottContractViolation) as error:
        return Err(error=EffectError_OperationFailed(message=str(error)))
    if row is None or not isinstance(row[0], str):
        return Err(error=EffectError_OperationFailed(message="stored value could not be read back"))
    stored: str = row[0]
    return Ok(value=stored)
