import contextlib
import datetime
import decimal
import sqlite3
import threading
import time
import uuid
from collections.abc import Iterable
from typing import Any, Final, cast

import duckdb
import psycopg.errors
import pyarrow
from cott_runtime import CottContractViolation, CottList, Err, Ok, Opaque, Option, Result, Some, U64, _cott_fixture_database
from real.harlequin.adapters_types import AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_Postgres, AdapterKind_Sqlite, AdapterKind_Trino, Connection, ConnectionRequest, ExecutedStatement, QueryError, QueryError_Failed
from real.harlequin.results_types import ColumnInfo, ResultSet

_SESSION_TAG: Final[str] = "harlequin.session"
_PENDING_TAG: Final[str] = "harlequin.pending_result"
_BAD_TITLE: Final[str] = "Harlequin could not fetch your results."


def _fail(title: str, message: str) -> Err[QueryError]:
    return Err(error=QueryError_Failed(title=title, message=message))


def _adapter_name(kind: AdapterKind) -> str:
    if isinstance(kind, AdapterKind_DuckDb):
        return "DuckDb"
    if isinstance(kind, AdapterKind_Sqlite):
        return "Sqlite"
    if isinstance(kind, AdapterKind_Postgres):
        return "Postgres"
    if isinstance(kind, AdapterKind_MySql):
        return "MySql"
    if isinstance(kind, AdapterKind_Odbc):
        return "Odbc"
    if isinstance(kind, AdapterKind_BigQuery):
        return "BigQuery"
    if isinstance(kind, AdapterKind_Trino):
        return "Trino"
    if isinstance(kind, AdapterKind_Databricks):
        return "Databricks"
    if isinstance(kind, AdapterKind_Adbc):
        return "Adbc"
    if isinstance(kind, AdapterKind_Cassandra):
        return "Cassandra"
    if isinstance(kind, AdapterKind_NebulaGraph):
        return "NebulaGraph"
    return "Chdb"


def _session(connection: Connection) -> dict[str, object] | None:
    handle = connection.session
    if handle.tag != _SESSION_TAG:
        return None
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return None
    payload = cast(dict[str, object], raw)
    if payload.keys() != {"adapter", "driver", "request", "cleanup", "lock", "closed", "transaction_mode", "modes", "active"}:
        return None
    request = payload["request"]
    mode = payload["transaction_mode"]
    modes = payload["modes"]
    if payload["adapter"] != _adapter_name(connection.adapter) or not isinstance(request, ConnectionRequest):
        return None
    if request.adapter != connection.adapter or request.read_only != connection.read_only:
        return None
    if payload["driver"] is None or not isinstance(payload["cleanup"], contextlib.ExitStack):
        return None
    if not isinstance(payload["lock"], type(threading.RLock())) or not isinstance(payload["closed"], bool):
        return None
    if mode is not None and not isinstance(mode, str):
        return None
    if not isinstance(modes, list) or not isinstance(payload["active"], list):
        return None
    if any(not isinstance(label, str) for label in cast(list[object], modes)):
        return None
    if mode is not None and mode not in modes:
        return None
    return payload


def _title(adapter: str) -> str:
    if adapter == "DuckDb":
        return "DuckDB raised an error when running your query:"
    if adapter == "Sqlite":
        return "SQLite raised an error when fetching results for your query:"
    display = {"MySql": "MySQL", "Odbc": "ODBC", "Adbc": "ADBC", "Chdb": "chDB"}.get(adapter, adapter)
    return f"{display} raised an error when fetching results for your query:"


def _is_cancel(error: Exception) -> bool:
    if isinstance(error, (duckdb.InterruptException, psycopg.errors.QueryCanceled)):
        return True
    text = str(error).casefold()
    return (isinstance(error, sqlite3.OperationalError) and "interrupted" in text) or "cancel" in text


def _dedupe(columns: CottList[ColumnInfo]) -> list[str]:
    used: set[str] = set()
    names: list[str] = []
    for column in columns:
        name = column.name
        candidate = name
        suffix = 0
        while candidate in used:
            candidate = f"{name}{suffix}"
            suffix += 1
        used.add(candidate)
        names.append(candidate)
    return names


def _kind(value: object) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, (bytes, bytearray, memoryview)):
        return "binary"
    if isinstance(value, decimal.Decimal):
        return "decimal"
    if isinstance(value, datetime.datetime):
        return "datetime"
    if isinstance(value, datetime.date):
        return "date"
    if isinstance(value, datetime.time):
        return "time"
    if isinstance(value, datetime.timedelta):
        return "timedelta"
    if isinstance(value, uuid.UUID):
        return "uuid"
    return "other"


def _binary(value: object) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, memoryview):
        return bytes(cast(memoryview[int], value))
    raise TypeError("Invalid binary value")


def _array(values: list[object]) -> object:
    arrow: Any = pyarrow
    kind = ""
    for value in values:
        if value is None:
            continue
        current = _kind(value)
        if kind and current != kind:
            return cast(object, arrow.array([None if item is None else str(item) for item in values], type=arrow.string()))
        kind = current
    if kind == "uuid":
        return cast(object, arrow.array([None if item is None else cast(uuid.UUID, item).bytes for item in values], type=arrow.uuid()))
    if kind == "binary":
        return cast(object, arrow.array([None if item is None else _binary(item) for item in values], type=arrow.binary()))
    try:
        return cast(object, arrow.array(values))
    except (TypeError, ValueError, pyarrow.ArrowInvalid, pyarrow.ArrowTypeError):
        return cast(object, arrow.array([None if item is None else str(item) for item in values], type=arrow.string()))


def _table_rows(rows: list[list[object]], names: list[str]) -> object:
    arrow: Any = pyarrow
    if not names:
        empty: object = cast(object, arrow.StructArray.from_buffers(arrow.struct([]), len(rows), [None], null_count=0, children=[]))
        return cast(object, arrow.Table.from_struct_array(empty))
    arrays = [_array([row[index] if index < len(row) else None for row in rows]) for index in range(len(names))]
    return cast(object, arrow.Table.from_arrays(arrays, names=names))


def _row(row: object) -> list[object]:
    if isinstance(row, (str, bytes)) or not isinstance(row, Iterable):
        raise TypeError("The driver returned a non-iterable result row.")
    return [value for value in cast(Iterable[object], row)]


def _rows(adapter: str, cursor: Any, cap: int | None) -> list[list[object]]:
    rows: list[list[object]] = []
    if adapter == "NebulaGraph":
        size = int(cursor.row_size())
        for index in range(size if cap is None else min(size, cap)):
            raw: object = cast(object, cursor.row_values(index))
            converted: list[object] = []
            for value in _row(raw):
                wrapper: Any = value
                try:
                    converted.append(cast(object, wrapper.cast()))
                except Exception:
                    converted.append(str(value))
            rows.append(converted)
        return rows
    if adapter == "BigQuery":
        source: object = cast(object, cursor.result()) if cap is None else cast(object, cursor.result(max_results=cap))
    elif adapter == "Cassandra":
        source = cast(object, cursor)
    elif cap is None:
        source = cast(object, cursor.fetchall())
    else:
        while len(rows) < cap:
            batch: object = cast(object, cursor.fetchmany(cap - len(rows)))
            if not isinstance(batch, Iterable):
                raise TypeError("The driver returned a non-iterable result batch.")
            received = 0
            for item in cast(Iterable[object], batch):
                rows.append(_row(item))
                received += 1
                if len(rows) == cap:
                    break
            if received == 0:
                break
        return rows
    if not isinstance(source, Iterable):
        raise TypeError("The driver returned a non-iterable result.")
    for item in cast(Iterable[object], source):
        if cap is not None and len(rows) >= cap:
            break
        rows.append(_row(item))
    return rows


def _reader(reader: Any, cap: int) -> object:
    arrow: Any = pyarrow
    batches: list[object] = []
    count = 0
    try:
        schema: object = cast(object, reader.schema)
        if not isinstance(schema, arrow.Schema):
            raise TypeError("The driver returned an invalid Arrow schema.")
        for batch in cast(Iterable[object], reader):
            if not isinstance(batch, arrow.RecordBatch):
                raise TypeError("The driver returned an invalid Arrow batch.")
            current: Any = batch
            size = int(current.num_rows)
            if size > cap - count:
                current = current.slice(0, cap - count)
                size = cap - count
            batches.append(cast(object, current))
            count += size
            if count >= cap:
                break
        return cast(object, arrow.Table.from_batches(batches, schema=schema))
    finally:
        reader.close()


def _fetch(adapter: str, cursor: Any, cap: int | None, names: list[str]) -> object:
    if adapter == "DuckDb":
        if isinstance(cursor, duckdb.DuckDBPyRelation):
            relation: Any = cursor if cap is None else cursor.limit(cap)
            return cast(object, relation.to_arrow_table())
        if cap is None:
            return cast(object, cursor.arrow().read_all())
        return _reader(cursor.fetch_record_batch(), cap)
    if adapter in ("Adbc", "Chdb"):
        if cap is None:
            return cast(object, cursor.fetch_arrow_table())
        return _reader(cursor.fetch_record_batch(), cap)
    return _table_rows(_rows(adapter, cursor, cap), names)


def _close(adapter: str, cursor: Any, driver: object) -> None:
    if cursor is driver or adapter in ("BigQuery", "Cassandra", "NebulaGraph") or (adapter == "DuckDb" and isinstance(cursor, duckdb.DuckDBPyRelation)):
        return
    cursor.close()


def fetch_result(connection: Connection, executed: ExecutedStatement, limit: Option[U64], viewer_max_rows: Option[U64]) -> Result[ResultSet, QueryError]:
    pending = executed.cursor
    if not isinstance(pending, Some):
        return _fail("Nothing to fetch", "The statement did not return a result set.")
    payload = _session(connection)
    if payload is None:
        return _fail(_BAD_TITLE, "The connection handle is malformed.")
    handle = pending.value
    if handle.tag != _PENDING_TAG:
        return _fail(_BAD_TITLE, "The result handle is malformed.")
    cursor_obj = handle.unwrap()
    if cursor_obj is None:
        return _fail(_BAD_TITLE, "The result handle is malformed.")
    adapter = cast(str, payload["adapter"])
    active = cast(list[object], payload["active"])
    lock = cast(contextlib.AbstractContextManager[object], payload["lock"])
    names = _dedupe(executed.columns)
    bound: int | None = limit.value if isinstance(limit, Some) else None
    cap = bound + 1 if bound is not None else None
    maximum: int | None = viewer_max_rows.value if isinstance(viewer_max_rows, Some) else None
    cursor: Any = cursor_obj
    result: ResultSet | None = None
    problem: Exception | KeyboardInterrupt | None = None
    with lock:
        if payload["closed"] is not False:
            return _fail(_BAD_TITLE, "The connection is closed.")
        if not any(item is cursor_obj for item in active):
            return _fail(_BAD_TITLE, "The result does not belong to this connection.")
        start = time.perf_counter_ns()
        try:
            try:
                _cott_fixture_database("read")
            except CottContractViolation as violation:
                if violation.message != "fixture adapters are inactive":
                    cause = violation.__cause__
                    if isinstance(cause, OSError):
                        raise cause
                    raise
            raw_table = _fetch(adapter, cursor, cap, names)
            arrow: Any = pyarrow
            if not isinstance(raw_table, arrow.Table):
                raise TypeError("The driver did not return a pyarrow.Table.")
            table: Any = raw_table
            if int(table.num_columns) != len(names):
                raise ValueError("The driver returned a different number of columns.")
            table = table.rename_columns(names)
            fetched = int(table.num_rows)
            truncated = bound is not None and fetched > bound
            if truncated and bound is not None:
                table = table.slice(0, bound)
                fetched = bound
            row_count = min(fetched, maximum) if maximum is not None else fetched
            columns = CottList(values=[ColumnInfo(name=name, type_label=column.type_label) for name, column in zip(names, executed.columns)])
            elapsed = max(0, (time.perf_counter_ns() - start) // 1_000_000)
            result = ResultSet(statement=executed.sql, columns=columns, data=Opaque(tag="harlequin.arrow_table", value=cast(object, table)), row_count=row_count, fetched_row_count=fetched, truncated=truncated, elapsed_ms=elapsed)
        except (Exception, KeyboardInterrupt) as error:
            problem = error
        finally:
            try:
                _close(adapter, cursor, payload["driver"])
            except (Exception, KeyboardInterrupt) as error:
                if problem is None:
                    problem = error
            for index in range(len(active) - 1, -1, -1):
                if active[index] is cursor_obj:
                    del active[index]
                    break
    if isinstance(problem, KeyboardInterrupt):
        return _fail("Query canceled", "The query was canceled.")
    if isinstance(problem, CottContractViolation):
        return _fail(_title(adapter), problem.message)
    if problem is not None:
        if _is_cancel(problem):
            return _fail("Query canceled", "The query was canceled.")
        return _fail(_title(adapter), str(problem))
    if result is None:
        return _fail(_title(adapter), "The driver did not return a pyarrow.Table.")
    return Ok(value=result)
