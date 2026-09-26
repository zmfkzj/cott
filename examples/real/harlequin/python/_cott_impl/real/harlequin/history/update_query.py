import pathlib
import sqlite3

from cott_runtime import F64, I64, UNIT, Err, Ok, Option, Result, Some, Unit
from real.harlequin.history_types import HistoryError, HistoryError_Unavailable, QueryStatus, QueryStatus_Error, QueryStatus_Ok


def _status_text(status: QueryStatus) -> str:
    if isinstance(status, QueryStatus_Ok):
        return "ok"
    if isinstance(status, QueryStatus_Error):
        return "error"
    return "canceled"


def _unavailable(log_path: pathlib.Path, message: str) -> Result[Unit, HistoryError]:
    return Err(error=HistoryError_Unavailable(path=log_path, message=message))


def update_query(log_path: pathlib.Path, row: I64, status: QueryStatus, rows: Option[I64], truncated: Option[bool], elapsed_ms: Option[F64], failure: Option[str]) -> Result[Unit, HistoryError]:
    rows_value: int | None = rows.value if isinstance(rows, Some) else None
    truncated_value: int | None = (1 if truncated.value else 0) if isinstance(truncated, Some) else None
    elapsed_value: float | None = round(elapsed_ms.value, 3) if isinstance(elapsed_ms, Some) else None
    error_value: str | None = failure.value if isinstance(failure, Some) else None
    try:
        connection = sqlite3.connect(log_path, timeout=5.0)
        try:
            with connection:
                connection.execute(
                    "UPDATE queries SET status = ?, rows = ?, truncated = ?, elapsed_ms = ?, error_text = ? WHERE id = ?",
                    (_status_text(status), rows_value, truncated_value, elapsed_value, error_value, row),
                )
        finally:
            connection.close()
    except Exception as error:
        return _unavailable(log_path, str(error))
    return Ok(value=UNIT)
