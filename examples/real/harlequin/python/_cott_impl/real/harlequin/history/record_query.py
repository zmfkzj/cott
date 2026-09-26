import os
import sqlite3
from pathlib import Path
from typing import Final

from cott_runtime import I64, Err, Ok, Result, Some
from real.harlequin.history_types import HistoryError, HistoryError_Unavailable, QueryRecord, QueryStatus, QueryStatus_Error, QueryStatus_Ok

_KEEP_ROWS: Final[int] = 100000

_SCHEMA: Final[str] = "CREATE TABLE IF NOT EXISTS queries(id INTEGER PRIMARY KEY, run_at TEXT NOT NULL, program TEXT NOT NULL, connection TEXT, profile TEXT, adapter TEXT, sql TEXT NOT NULL, status TEXT NOT NULL, rows INTEGER, truncated INTEGER, elapsed_ms REAL, error_text TEXT)"

_INDEX: Final[str] = "CREATE INDEX IF NOT EXISTS queries_by_connection ON queries(connection, id DESC)"

_INSERT: Final[str] = "INSERT INTO queries(run_at, program, connection, profile, adapter, sql, status, rows, truncated, elapsed_ms, error_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

_TRIM: Final[str] = "DELETE FROM queries WHERE id NOT IN (SELECT id FROM queries ORDER BY id DESC LIMIT ?)"


def _status_text(status: QueryStatus) -> str:
    if isinstance(status, QueryStatus_Ok):
        return "ok"
    if isinstance(status, QueryStatus_Error):
        return "error"
    return "canceled"


def _unavailable(log_path: Path, message: str) -> Result[I64, HistoryError]:
    return Err(error=HistoryError_Unavailable(path=log_path, message=message))


def _try_wal(conn: sqlite3.Connection) -> None:
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except sqlite3.Error:
        return


def _insert(conn: sqlite3.Connection, record: QueryRecord) -> int:
    with conn:
        conn.execute(_SCHEMA)
        conn.execute(_INDEX)
        version_row = conn.execute("PRAGMA user_version").fetchone()
        if version_row is None or version_row[0] != 1:
            conn.execute("PRAGMA user_version = 1")
        profile = record.profile.value if isinstance(record.profile, Some) else None
        rows = record.rows.value if isinstance(record.rows, Some) else None
        truncated = (1 if record.truncated.value else 0) if isinstance(record.truncated, Some) else None
        elapsed = round(record.elapsed_ms.value, 3) if isinstance(record.elapsed_ms, Some) else None
        error_text = record.error_text.value if isinstance(record.error_text, Some) else None
        cursor = conn.execute(_INSERT, (record.run_at, record.program, record.connection, profile, record.adapter, record.sql, _status_text(record.status), rows, truncated, elapsed, error_text))
        row_id = cursor.lastrowid
        conn.execute(_TRIM, (_KEEP_ROWS,))
    if row_id is None:
        raise sqlite3.OperationalError("insert returned no row id")
    return row_id


def _write_host(log_path: Path, record: QueryRecord) -> int:
    parent = log_path.parent
    if not parent.exists():
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    is_new = not log_path.exists()
    conn = sqlite3.connect(str(log_path), timeout=5.0)
    try:
        if is_new:
            os.chmod(log_path, 0o600)
        conn.execute("PRAGMA busy_timeout = 5000")
        _try_wal(conn)
        conn.execute("PRAGMA synchronous = NORMAL")
        return _insert(conn, record)
    finally:
        conn.close()


def record_query(log_path: Path, record: QueryRecord) -> Result[I64, HistoryError]:
    try:
        row_id = _write_host(log_path, record)
    except Exception as exc:
        return _unavailable(log_path, str(exc))
    return Ok(value=row_id)
