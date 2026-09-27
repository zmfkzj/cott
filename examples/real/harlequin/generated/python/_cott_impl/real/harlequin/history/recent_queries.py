import sqlite3
from pathlib import Path

from cott_runtime import CottContractViolation, CottList, Err, F64, I64, Nothing, Ok, Option, Result, Some, U64, _cott_fixture_read
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


def _opt_int(raw: object) -> Option[I64]:
    if isinstance(raw, bool) or not isinstance(raw, int):
        return Nothing()
    return Some(value=raw)


def _opt_bool(raw: object) -> Option[bool]:
    if isinstance(raw, bool):
        return Some(value=raw)
    if isinstance(raw, int):
        return Some(value=raw != 0)
    return Nothing()


def _opt_float(raw: object) -> Option[F64]:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return Nothing()
    return Some(value=float(raw))


def _text(raw: object) -> str:
    return raw if isinstance(raw, str) else ("" if raw is None else str(raw))


def recent_queries(log_path: Path, filter: HistoryFilter, limit: Option[U64]) -> Result[CottList[QueryRecord], HistoryError]:
    snapshot: bytes | None = None
    try:
        snapshot = _cott_fixture_read(log_path)
    except CottContractViolation as exc:
        if exc.message != "fixture adapters are inactive":
            cause = exc.__cause__
            if isinstance(cause, FileNotFoundError):
                return Ok(value=CottList(values=[]))
            return _unavailable(log_path, str(cause) if isinstance(cause, OSError) else exc.message)
        try:
            log_path.stat()
            uri = log_path.absolute().as_uri() + "?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=0.25)
        except FileNotFoundError:
            return Ok(value=CottList(values=[]))
        except (OSError, ValueError, sqlite3.Error) as error:
            return _unavailable(log_path, str(error))
    except OSError as error:
        return _unavailable(log_path, str(error))
    else:
        try:
            conn = sqlite3.connect(":memory:", timeout=0.25)
        except sqlite3.Error as error:
            return _unavailable(log_path, str(error))

    try:
        if snapshot is not None:
            conn.deserialize(snapshot)
        exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'queries'").fetchone()
        if exists is None:
            return Ok(value=CottList(values=[]))
        clauses = ["status IN ('ok', 'error', 'canceled')"]
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
        query = (
            "SELECT run_at, program, connection, profile, adapter, sql, status, rows, truncated, elapsed_ms, error_text "
            "FROM queries WHERE " + " AND ".join(clauses) + " ORDER BY id DESC"
        )
        if isinstance(limit, Some) and limit.value <= 9223372036854775807:
            query += " LIMIT ?"
            params.append(limit.value)
        records: list[QueryRecord] = []
        for db_row in conn.execute(query, params):
            row: tuple[object, ...] = db_row
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
    except (sqlite3.Error, ValueError) as error:
        return _unavailable(log_path, str(error))
    finally:
        conn.close()
