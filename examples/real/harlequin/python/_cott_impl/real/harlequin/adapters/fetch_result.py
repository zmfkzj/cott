import contextlib
import itertools
import sqlite3
import time
from typing import Any, Final, cast

import duckdb
import psycopg
import pyarrow
from cott_runtime import CottList, Err, Nothing, Ok, Opaque, Result, Some, U64

from real.harlequin.adapters_types import Connection, ExecutedStatement, QueryError, QueryError_Failed
from real.harlequin.results_types import ColumnInfo, ResultSet

_SESSION_TAG: Final[str] = "harlequin.session"
_PENDING_TAG: Final[str] = "harlequin.pending_result"
_KEYS: Final[str] = "adapter,driver,request,cleanup,lock,closed,transaction_mode,modes,active"
_BAD_TITLE: Final[str] = "Harlequin could not fetch your results."


def _fail(title: str, message: str) -> Result[ResultSet, QueryError]:
    return Err(error=QueryError_Failed(title=title, message=message))


def _title(adapter: str) -> str:
    titles: dict[str, str] = {
        "DuckDb": "DuckDB raised an error when running your query:",
        "Sqlite": "SQLite raised an error when fetching results for your query:",
        "Postgres": "Postgres raised an error when fetching results for your query:",
        "MySql": "MySQL raised an error when fetching results for your query:",
        "Odbc": "ODBC raised an error when fetching results for your query:",
        "BigQuery": "BigQuery raised an error when fetching results for your query:",
        "Trino": "Trino raised an error when fetching results for your query:",
        "Databricks": "Databricks raised an error when fetching results for your query:",
        "Adbc": "ADBC raised an error when fetching results for your query:",
        "Cassandra": "Cassandra raised an error when fetching results for your query:",
        "NebulaGraph": "NebulaGraph raised an error when fetching results for your query:",
        "Chdb": "chDB raised an error when fetching results for your query:",
    }
    return titles.get(adapter, "Harlequin raised an error when fetching results for your query:")


def _is_cancel(error: Exception) -> bool:
    if isinstance(error, (duckdb.InterruptException, psycopg.errors.QueryCanceled)):
        return True
    message = str(error).lower()
    if isinstance(error, sqlite3.OperationalError) and "interrupted" in message:
        return True
    return "cancel" in message


def _dedupe(names: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for name in names:
        candidate = name
        k = 0
        while candidate in seen:
            candidate = f"{name}{k}"
            k += 1
        seen.add(candidate)
        out.append(candidate)
    return out


def _column_array(values: list[object]) -> object:
    pa: Any = pyarrow
    try:
        return cast(object, pa.array(values))
    except Exception:
        return cast(object, pa.array([None if v is None else str(v) for v in values], type=pa.string()))


def _table_from_rows(rows: list[list[object]], names: list[str]) -> object:
    pa: Any = pyarrow
    arrays: list[object] = []
    for i in range(len(names)):
        arrays.append(_column_array([row[i] if i < len(row) else None for row in rows]))
    return cast(object, pa.Table.from_arrays(arrays, names=names))


def _read_reader(reader: Any, cap: int | None) -> object:
    pa: Any = pyarrow
    batches: list[object] = []
    count = 0
    for batch in reader:
        b: Any = batch
        batches.append(cast(object, b))
        count += int(cast(int, b.num_rows))
        if cap is not None and count >= cap:
            break
    return cast(object, pa.Table.from_batches(batches, schema=reader.schema))


def _nebula_value(value: Any) -> object:
    try:
        return cast(object, value.cast())
    except Exception:
        return str(value)


def _fetch_rows(adapter: str, cursor: Any, cap: int | None) -> list[list[object]]:
    rows: list[list[object]] = []
    if adapter == "NebulaGraph":
        size = int(cast(int, cursor.row_size()))
        end = size if cap is None else min(size, cap)
        for i in range(end):
            values: Any = cursor.row_values(i)
            rows.append([_nebula_value(v) for v in values])
        return rows
    if adapter == "Cassandra":
        source: Any = cursor if cap is None else itertools.islice(cursor, cap)
    elif cap is None:
        source = cursor.fetchall()
    else:
        source = cursor.fetchmany(cap)
    for row in source:
        rows.append([cast(object, v) for v in row])
    return rows


def _fetch_table(adapter: str, cursor: Any, cap: int | None, names: list[str]) -> object:
    if adapter == "DuckDb":
        if isinstance(cursor, duckdb.DuckDBPyRelation):
            rel: Any = cursor if cap is None else cursor.limit(cap)
            return cast(object, rel.to_arrow_table())
        return _read_reader(cursor.fetch_record_batch(), cap)
    if adapter in ("Adbc", "Chdb"):
        return _read_reader(cursor.fetch_record_batch(), cap)
    return _table_from_rows(_fetch_rows(adapter, cursor, cap), names)


def _close_cursor(adapter: str, cursor: Any) -> None:
    if adapter in ("Cassandra", "NebulaGraph"):
        return
    try:
        cursor.close()
    except Exception:
        return


def fetch_result(connection: Connection, executed: ExecutedStatement, limit: Some[U64] | Nothing, viewer_max_rows: Some[U64] | Nothing) -> Result[ResultSet, QueryError]:
    pending = executed.cursor
    if not isinstance(pending, Some):
        return _fail("Nothing to fetch", "The statement did not return a result set.")
    handle = connection.session
    if handle.tag != _SESSION_TAG:
        return _fail(_BAD_TITLE, "The connection handle is malformed.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail(_BAD_TITLE, "The connection handle is malformed.")
    payload = cast(dict[str, object], raw)
    if set(payload.keys()) != set(_KEYS.split(",")):
        return _fail(_BAD_TITLE, "The connection handle is malformed.")
    adapter = payload["adapter"]
    lock = payload["lock"]
    active_raw = payload["active"]
    if not isinstance(adapter, str) or not isinstance(lock, contextlib.AbstractContextManager) or not isinstance(active_raw, list):
        return _fail(_BAD_TITLE, "The connection handle is malformed.")
    active = cast(list[object], active_raw)
    guard = cast(contextlib.AbstractContextManager[object], lock)
    pending_handle = pending.value
    if pending_handle.tag != _PENDING_TAG:
        return _fail(_BAD_TITLE, "The result handle is malformed.")
    cursor_obj = pending_handle.unwrap()
    cursor: Any = cursor_obj
    names = _dedupe([c.name for c in executed.columns])
    cap: int | None = limit.value + 1 if isinstance(limit, Some) else None
    with guard:
        if payload["closed"] is not False:
            return _fail(_BAD_TITLE, "The connection is closed.")
        start = time.perf_counter()
        try:
            table: Any = _fetch_table(adapter, cursor, cap, names)
            if len(names) == int(cast(int, table.num_columns)):
                table = table.rename_columns(names)
        except Exception as error:
            if _is_cancel(error):
                return _fail("Query canceled", "The query was canceled.")
            return _fail(_title(adapter), str(error))
        finally:
            _close_cursor(adapter, cursor)
            for i, item in enumerate(active):
                if item is cursor_obj:
                    del active[i]
                    break
        elapsed = int((time.perf_counter() - start) * 1000)
    fetched = int(cast(int, table.num_rows))
    truncated = False
    if isinstance(limit, Some) and fetched > limit.value:
        table = table.slice(0, limit.value)
        fetched = limit.value
        truncated = True
    row_count = min(fetched, viewer_max_rows.value) if isinstance(viewer_max_rows, Some) else fetched
    columns = CottList(values=[ColumnInfo(name=n, type_label=c.type_label) for n, c in zip(names, executed.columns)])
    return Ok(
        value=ResultSet(
            statement=executed.sql,
            columns=columns,
            data=Opaque(tag="harlequin.arrow_table", value=cast(object, table)),
            row_count=row_count,
            fetched_row_count=fetched,
            truncated=truncated,
            elapsed_ms=elapsed,
        )
    )
