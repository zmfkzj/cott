import sqlite3
from pathlib import Path

from cott_runtime import U64, CottList, Err, Nothing, Ok, Option, Result, Some
from real.harlequin.history_types import HistoryError, HistoryError_Unavailable, HistoryFilter, QueryRecord, QueryStatus, QueryStatus_Canceled, QueryStatus_Error, QueryStatus_Ok


def _unavailable(path: Path, message: str) -> Err[HistoryError]:
    return Err(error=HistoryError_Unavailable(path=path, message=message))


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _status_text(status: QueryStatus) -> str:
    if isinstance(status, QueryStatus_Ok):
        return "ok"
    if isinstance(status, QueryStatus_Error):
        return "error"
    return "canceled"


def _parse_status(raw: object) -> QueryStatus | None:
    if raw == "ok":
        return QueryStatus_Ok()
    if raw == "error":
        return QueryStatus_Error()
    if raw == "canceled":
        return QueryStatus_Canceled()
    return None


def _opt_str(raw: object) -> Option[str]:
    return Some(value=raw) if isinstance(raw, str) else Nothing()


def _opt_int(raw: object) -> Option[int]:
    if isinstance(raw, bool) or not isinstance(raw, int):
        return Nothing()
    return Some(value=raw)


def _opt_bool(raw: object) -> Option[bool]:
    if isinstance(raw, bool):
        return Some(value=raw)
    if isinstance(raw, int):
        return Some(value=raw != 0)
    return Nothing()


def _opt_float(raw: object) -> Option[float]:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return Nothing()
    return Some(value=float(raw))


def _text(raw: object) -> str:
    return raw if isinstance(raw, str) else ("" if raw is None else str(raw))


def recent_queries(log_path: Path, filter: HistoryFilter, limit: Option[U64]) -> Result[CottList[QueryRecord], HistoryError]:
    try:
        if not log_path.exists():
            return Ok(value=CottList(values=[]))
        uri = log_path.resolve().as_uri() + "?mode=ro"
    except (OSError, ValueError) as exc:
        return _unavailable(log_path, str(exc))
    clauses: list[str] = []
    params: list[object] = []
    if isinstance(filter.connection, Some):
        clauses.append("connection = ?")
        params.append(filter.connection.value)
    if filter.search != "":
        clauses.append("sql LIKE ? ESCAPE '\\'")
        params.append("%" + _escape_like(filter.search) + "%")
    if isinstance(filter.program, Some):
        clauses.append("program = ?")
        params.append(filter.program.value)
    if isinstance(filter.status, Some):
        clauses.append("status = ?")
        params.append(_status_text(filter.status.value))
    else:
        clauses.append("status IN ('ok', 'error', 'canceled')")
    query = (
        "SELECT run_at, program, connection, profile, adapter, sql, status, rows, truncated, elapsed_ms, error_text "
        "FROM queries WHERE " + " AND ".join(clauses) + " ORDER BY id DESC"
    )
    if isinstance(limit, Some):
        query += " LIMIT ?"
        params.append(int(limit.value))
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=0.25)
    except sqlite3.Error as exc:
        return _unavailable(log_path, str(exc))
    try:
        exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'queries'").fetchone()
        if exists is None:
            return Ok(value=CottList(values=[]))
        fetched: list[tuple[object, ...]] = conn.execute(query, params).fetchall()
    except sqlite3.Error as exc:
        return _unavailable(log_path, str(exc))
    finally:
        conn.close()
    records: list[QueryRecord] = []
    for row in fetched:
        status = _parse_status(row[6])
        if status is None:
            continue
        records.append(
            QueryRecord(
                run_at=_text(row[0]),
                program=_text(row[1]),
                connection=_text(row[2]),
                profile=_opt_str(row[3]),
                adapter=_text(row[4]),
                sql=_text(row[5]),
                status=status,
                rows=_opt_int(row[7]),
                truncated=_opt_bool(row[8]),
                elapsed_ms=_opt_float(row[9]),
                error_text=_opt_str(row[10]),
            )
        )
    return Ok(value=CottList(values=records))
