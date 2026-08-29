from __future__ import annotations

from pathlib import Path
import sqlite3

from cott_runtime import Err, Ok, Result
from curriculum.effects_selection_types import EffectError, EffectError_OperationFailed


def store_and_load(database: Path, key: str, value: str) -> Result[str, EffectError]:
    try:
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS values_table (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            connection.execute("INSERT OR REPLACE INTO values_table (key, value) VALUES (?, ?)", (key, value))
            row: tuple[str] | None = connection.execute("SELECT value FROM values_table WHERE key = ?", (key,)).fetchone()
        if row is None:
            return Err(error=EffectError_OperationFailed(message="stored value was not found"))
        return Ok(value=row[0])
    except sqlite3.Error as error:
        return Err(error=EffectError_OperationFailed(message=str(error)))
