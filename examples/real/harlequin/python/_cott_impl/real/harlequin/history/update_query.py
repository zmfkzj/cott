import pathlib
import sqlite3

from cott_runtime import CottContractViolation, F64, I64, UNIT, Err, Ok, Option, Result, Some, Unit, _cott_fixture_read, _cott_fixture_replace
from real.harlequin.history_types import HistoryError, HistoryError_Unavailable, QueryStatus, QueryStatus_Error, QueryStatus_Ok


def _status_text(status: QueryStatus) -> str:
    if isinstance(status, QueryStatus_Ok):
        return "ok"
    if isinstance(status, QueryStatus_Error):
        return "error"
    return "canceled"


def _unavailable(log_path: pathlib.Path, error: Exception) -> Result[Unit, HistoryError]:
    if isinstance(error, CottContractViolation):
        cause = error.__cause__
        if isinstance(cause, OSError):
            return Err(error=HistoryError_Unavailable(path=log_path, message=str(cause)))
    return Err(error=HistoryError_Unavailable(path=log_path, message=str(error)))


def _apply_update(connection: sqlite3.Connection, row: I64, status: QueryStatus, rows_value: int | None, truncated_value: int | None, elapsed_value: float | None, error_value: str | None) -> bool:
    with connection:
        cursor = connection.execute(
            "UPDATE queries SET status = ?, rows = ?, truncated = ?, elapsed_ms = ?, error_text = ? WHERE id = ?",
            (_status_text(status), rows_value, truncated_value, elapsed_value, error_value, row),
        )
    return cursor.rowcount != 0


def _update_host(log_path: pathlib.Path, row: I64, status: QueryStatus, rows_value: int | None, truncated_value: int | None, elapsed_value: float | None, error_value: str | None) -> Result[Unit, HistoryError]:
    try:
        connection = sqlite3.connect(log_path, timeout=5.0)
        try:
            _apply_update(connection, row, status, rows_value, truncated_value, elapsed_value, error_value)
        finally:
            connection.close()
    except Exception as error:
        return _unavailable(log_path, error)
    return Ok(value=UNIT)


def update_query(log_path: pathlib.Path, row: I64, status: QueryStatus, rows: Option[I64], truncated: Option[bool], elapsed_ms: Option[F64], failure: Option[str]) -> Result[Unit, HistoryError]:
    rows_value: int | None = rows.value if isinstance(rows, Some) else None
    truncated_value: int | None = (1 if truncated.value else 0) if isinstance(truncated, Some) else None
    elapsed_value: float | None = round(elapsed_ms.value, 3) if isinstance(elapsed_ms, Some) else None
    error_value: str | None = failure.value if isinstance(failure, Some) else None

    try:
        contents = _cott_fixture_read(log_path)
    except CottContractViolation as error:
        if error.message == "fixture adapters are inactive":
            return _update_host(log_path, row, status, rows_value, truncated_value, elapsed_value, error_value)
        return _unavailable(log_path, error)
    except Exception as error:
        return _unavailable(log_path, error)

    try:
        connection = sqlite3.connect(":memory:", timeout=5.0)
        try:
            connection.deserialize(contents)
            if not _apply_update(connection, row, status, rows_value, truncated_value, elapsed_value, error_value):
                return Ok(value=UNIT)
            updated = connection.serialize()
        finally:
            connection.close()
        _cott_fixture_replace(log_path, updated)
    except Exception as error:
        return _unavailable(log_path, error)
    return Ok(value=UNIT)
