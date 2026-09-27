import os
import sqlite3
from pathlib import Path
from typing import Final

from cott_runtime import CottContractViolation, Err, I64, Ok, Result, Some, _cott_fixture_read, _cott_fixture_replace
from real.harlequin.history_types import HistoryError, HistoryError_Unavailable, QueryRecord, QueryStatus, QueryStatus_Error, QueryStatus_Ok

_KEEP_ROWS: Final[int] = 100000
_SCHEMA: Final[str] = "CREATE TABLE IF NOT EXISTS queries(id INTEGER PRIMARY KEY, run_at TEXT NOT NULL, program TEXT NOT NULL, connection TEXT, profile TEXT, adapter TEXT, sql TEXT NOT NULL, status TEXT NOT NULL, rows INTEGER, truncated INTEGER, elapsed_ms REAL, error_text TEXT)"
_INDEX: Final[str] = "CREATE INDEX IF NOT EXISTS queries_by_connection ON queries(connection, id DESC)"
_INSERT: Final[str] = "INSERT INTO queries(run_at, program, connection, profile, adapter, sql, status, rows, truncated, elapsed_ms, error_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
_TRIM: Final[str] = "DELETE FROM queries WHERE id <= (SELECT id FROM queries ORDER BY id DESC LIMIT 1 OFFSET ?)"


def _status_text(status: QueryStatus) -> str:
    if isinstance(status, QueryStatus_Ok):
        return "ok"
    if isinstance(status, QueryStatus_Error):
        return "error"
    return "canceled"


def _enable_wal(conn: sqlite3.Connection) -> None:
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except sqlite3.Error:
        return


def _configure(conn: sqlite3.Connection, file_backed: bool) -> None:
    conn.execute("PRAGMA busy_timeout = 5000")
    if file_backed:
        _enable_wal(conn)
    conn.execute("PRAGMA synchronous = NORMAL")


def _insert(conn: sqlite3.Connection, record: QueryRecord) -> I64:
    with conn:
        conn.execute(_SCHEMA)
        conn.execute(_INDEX)
        if conn.execute("PRAGMA user_version").fetchone() != (1,):
            conn.execute("PRAGMA user_version = 1")
        profile = record.profile.value if isinstance(record.profile, Some) else None
        rows = record.rows.value if isinstance(record.rows, Some) else None
        truncated = (1 if record.truncated.value else 0) if isinstance(record.truncated, Some) else None
        elapsed = round(record.elapsed_ms.value, 3) if isinstance(record.elapsed_ms, Some) else None
        error_text = record.error_text.value if isinstance(record.error_text, Some) else None
        cursor = conn.execute(_INSERT, (record.run_at, record.program, record.connection, profile, record.adapter, record.sql, _status_text(record.status), rows, truncated, elapsed, error_text))
        row_id = cursor.lastrowid
        if row_id is None or row_id <= 0:
            raise sqlite3.OperationalError("insert returned no positive row id")
        conn.execute(_TRIM, (_KEEP_ROWS,))
    return row_id


def _make_parents(parent: Path) -> None:
    if parent.exists():
        return
    missing: list[Path] = []
    current = parent
    while not current.exists():
        missing.append(current)
        if current == current.parent:
            raise FileNotFoundError(str(current))
        current = current.parent
    for directory in reversed(missing):
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            if not directory.is_dir():
                raise
        else:
            directory.chmod(0o700)


def _create_private_file(log_path: Path) -> None:
    try:
        fd = os.open(log_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return
    try:
        os.fchmod(fd, 0o600)
    finally:
        os.close(fd)


def _write_host(log_path: Path, record: QueryRecord) -> I64:
    _make_parents(log_path.parent)
    _create_private_file(log_path)
    conn = sqlite3.connect(str(log_path), timeout=5.0)
    try:
        _configure(conn, True)
        return _insert(conn, record)
    finally:
        conn.close()


def _write_fixture(log_path: Path, record: QueryRecord, data: bytes | None) -> I64:
    conn = sqlite3.connect(":memory:", timeout=5.0)
    try:
        if data:
            conn.deserialize(data)
        _configure(conn, False)
        row_id = _insert(conn, record)
        _cott_fixture_replace(log_path, conn.serialize())
        return row_id
    finally:
        conn.close()


def record_query(log_path: Path, record: QueryRecord) -> Result[I64, HistoryError]:
    try:
        try:
            data = _cott_fixture_read(log_path)
        except CottContractViolation as exc:
            if exc.message == "fixture adapters are inactive":
                return Ok(value=_write_host(log_path, record))
            if not isinstance(exc.__cause__, FileNotFoundError):
                raise
            data = None
        return Ok(value=_write_fixture(log_path, record, data))
    except Exception as exc:
        return Err(error=HistoryError_Unavailable(path=log_path, message=str(exc)))
