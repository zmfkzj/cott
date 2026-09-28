import contextlib
import sqlite3
import threading
from typing import Any, Final, Literal, cast

import cassandra
import cassandra.query
import duckdb
import psycopg
import psycopg.errors
import psycopg.pq
from cott_runtime import CottContractViolation, CottList, Nothing, Opaque, Option, Some, U64, _cott_fixture_database

from real.harlequin.adapters_types import AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_Postgres, AdapterKind_Sqlite, AdapterKind_Trino, Connection, ConnectionRequest, ExecutedStatement, QueryFailure
from real.harlequin.results_types import ColumnInfo

_SESSION_TAG: Final[str] = "harlequin.session"
_CANCEL_TITLE: Final[str] = "Query canceled"
_CANCEL_MESSAGE: Final[str] = "The query was canceled."
_CASS_LEVELS: Final[str] = "ANY,ONE,TWO,THREE,QUORUM,ALL,LOCAL_QUORUM,EACH_QUORUM,SERIAL,LOCAL_SERIAL,LOCAL_ONE"


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


def _title(adapter: str) -> str:
    if adapter == "Cassandra":
        return "Cassandra raised an error:"
    if adapter == "NebulaGraph":
        return "NebulaGraph raised an error:"
    if adapter == "DuckDb":
        display = "DuckDB"
    elif adapter == "Sqlite":
        display = "SQLite"
    elif adapter == "MySql":
        display = "MySQL"
    elif adapter == "Odbc":
        display = "ODBC"
    elif adapter == "Adbc":
        display = "ADBC"
    elif adapter == "Chdb":
        display = "chDB"
    else:
        display = adapter
    return f"{display} raised an error when compiling or running your query:"


def _duck_label(dtype: str) -> str:
    text = dtype.strip().upper()
    if text.endswith("[]"):
        return "[" + _duck_label(text[:-2]) + "]"
    base = text.split("(", 1)[0].split("[", 1)[0].strip()
    if base == "SQLNULL":
        return "\\n"
    if base == "BOOLEAN":
        return "t/f"
    if base in ("TINYINT", "SMALLINT", "INTEGER"):
        return "#"
    if base in ("UTINYINT", "USMALLINT", "UINTEGER"):
        return "u#"
    if base == "BIGINT":
        return "##"
    if base == "UBIGINT":
        return "u##"
    if base == "HUGEINT":
        return "###"
    if base == "UUID":
        return "uid"
    if base in ("FLOAT", "DOUBLE", "DECIMAL", "REAL"):
        return "#.#"
    if base == "DATE":
        return "d"
    if base in ("TIME_TZ", "TIMESTAMP_TZ", "TIME WITH TIME ZONE", "TIMESTAMP WITH TIME ZONE"):
        return "ttz"
    if base == "TIME":
        return "t"
    if base.startswith("TIMESTAMP"):
        return "ts"
    if base == "VARCHAR":
        return "s"
    if base == "BLOB":
        return "0b"
    if base == "BIT":
        return "010"
    if base == "INTERVAL":
        return "|-|"
    if base == "STRUCT":
        return "{}"
    if base == "MAP":
        return "{m}"
    return "?"


def _generic_label(code: object) -> str:
    if code is None:
        return "?"
    text = str(code).lower()
    if "bool" in text:
        return "t/f"
    if "timestamp" in text or "datetime" in text:
        return "ts"
    if "date" in text:
        return "d"
    if text in ("int", "long") or text.startswith(("int", "uint", "tinyint", "smallint", "mediumint", "bigint")) or "'int'" in text or "'long'" in text or ".int" in text:
        return "#"
    if any(word in text for word in ("float", "double", "decimal", "numeric", "real")):
        return "#.#"
    if any(word in text for word in ("str", "char", "text", "unicode")):
        return "s"
    if any(word in text for word in ("bytes", "binary", "blob")):
        return "0b"
    return "?"


def _pg_label(code: object) -> str:
    if not isinstance(code, int) or isinstance(code, bool):
        return "?"
    if code == 16:
        return "t/f"
    if code in (20, 21, 23):
        return "#"
    if code in (700, 701, 1700):
        return "#.#"
    if code in (25, 1043, 1042, 19):
        return "s"
    if code == 1082:
        return "d"
    if code in (1114, 1184):
        return "ts"
    if code == 17:
        return "0b"
    return "?"


def _mysql_label(code: object) -> str:
    if not isinstance(code, int) or isinstance(code, bool):
        return _generic_label(code)
    if code in (1, 2, 3, 8, 9, 13):
        return "#"
    if code in (0, 4, 5, 246):
        return "#.#"
    if code in (7, 12):
        return "ts"
    if code in (10, 14):
        return "d"
    if code in (16, 249, 250, 251, 252, 255):
        return "0b"
    if code in (15, 245, 247, 248, 253, 254):
        return "s"
    return "?"


def _odbc_label(code: object) -> str:
    if not isinstance(code, int) or isinstance(code, bool):
        return _generic_label(code)
    if code == -7:
        return "t/f"
    if code in (-6, 5, 4, -5):
        return "#"
    if code in (2, 3, 6, 7, 8):
        return "#.#"
    if code in (1, 12, -1, -8, -9, -10):
        return "s"
    if code in (9, 91):
        return "d"
    if code in (11, 93):
        return "ts"
    if code in (-2, -3, -4):
        return "0b"
    return "?"


def _sequence(value: object) -> list[object] | tuple[object, ...] | None:
    if isinstance(value, list):
        return cast(list[object], value)
    if isinstance(value, tuple):
        return cast(tuple[object, ...], value)
    return None


def _description_columns(description: object, adapter: str) -> list[ColumnInfo] | None:
    if description is None:
        return None
    entries = _sequence(description)
    if entries is None:
        raise TypeError("The driver returned an invalid column description.")
    columns: list[ColumnInfo] = []
    for item in entries:
        entry = _sequence(item)
        if entry is None or len(entry) < 2:
            raise TypeError("The driver returned an invalid column description.")
        code = entry[1]
        if adapter == "MySql":
            label = _mysql_label(code)
        elif adapter == "Odbc":
            label = _odbc_label(code)
        else:
            label = _generic_label(code)
        columns.append(ColumnInfo(name=str(entry[0]), type_label=label))
    return columns


def _is_cancel(error: BaseException) -> bool:
    if isinstance(error, (duckdb.InterruptException, psycopg.errors.QueryCanceled, KeyboardInterrupt)):
        return True
    message = str(error).casefold()
    return message == "interrupted" or any(phrase in message for phrase in ("query canceled", "query cancelled", "query was canceled", "query was cancelled", "query was interrupted", "query execution was interrupted", "canceling statement due to user request", "operation canceled", "operation cancelled"))


def _message(error: BaseException) -> str:
    if isinstance(error, CottContractViolation):
        cause = error.__cause__
        return str(cause) if isinstance(cause, OSError) else error.message
    return str(error)


def _failure(index: U64, sql: str, title: str, message: str) -> ExecutedStatement:
    return ExecutedStatement(index=index, sql=sql, cursor=Nothing(), failure=Some(value=QueryFailure(title=title, message=message)), columns=CottList(values=[]))


def _unavailable(statements: CottList[str], title: str, message: str, continue_on_error: bool) -> CottList[ExecutedStatement]:
    results: list[ExecutedStatement] = []
    for index, sql in enumerate(statements):
        results.append(_failure(index, sql, title, message))
        if not continue_on_error:
            break
    return CottList(values=results)


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
    adapter = payload["adapter"]
    request = payload["request"]
    if not isinstance(adapter, str) or adapter != _adapter_name(connection.adapter) or not isinstance(request, ConnectionRequest):
        return None
    if request.adapter != connection.adapter or request.read_only != connection.read_only:
        return None
    if payload["driver"] is None or not isinstance(payload["cleanup"], contextlib.ExitStack) or not isinstance(payload["lock"], type(threading.RLock())) or not isinstance(payload["closed"], bool):
        return None
    mode = payload["transaction_mode"]
    modes = payload["modes"]
    active = payload["active"]
    if (mode is not None and not isinstance(mode, str)) or not isinstance(modes, list) or not isinstance(active, list):
        return None
    labels = cast(list[object], modes)
    if any(not isinstance(label, str) for label in labels):
        return None
    if (mode is None and labels) or (mode is not None and mode not in labels):
        return None
    return payload


def _remove_active(active: list[object], item: object) -> None:
    for index, candidate in enumerate(active):
        if candidate is item:
            del active[index]
            break


def _discard(active: list[object], item: object, adapter: str) -> Exception | None:
    _remove_active(active, item)
    if adapter not in ("Sqlite", "Postgres", "MySql", "Odbc", "Trino", "Databricks", "Adbc", "Chdb"):
        return None
    cursor: Any = item
    try:
        cursor.close()
    except Exception as error:
        return error
    return None


def _chdb_bounded(sql: str, limit: int | None) -> str:
    if limit is None:
        return sql
    body = sql.strip().rstrip(";").rstrip()
    words = body.split()
    if not words or words[0].lower() not in ("select", "with"):
        return sql
    if " settings " in f" {body.lower()} ":
        return body + f", max_result_rows={limit + 1}, result_overflow_mode='break'"
    return body + f" SETTINGS max_result_rows={limit + 1}, result_overflow_mode='break'"


def _run_one(adapter: str, driver: object, payload: dict[str, object], active: list[object], sql: str, limit: int | None) -> tuple[object | None, list[ColumnInfo]]:
    sdk: Any = driver
    if adapter == "DuckDb":
        active.append(driver)
        relation: Any = sdk.sql(sql)
        if relation is None:
            return None, []
        if limit is not None:
            relation = relation.limit(limit + 1)
        duck_names_raw: object = cast(object, relation.columns)
        duck_types_raw: object = cast(object, relation.dtypes)
        duck_names = _sequence(duck_names_raw)
        duck_types = _sequence(duck_types_raw)
        if duck_names is None or duck_types is None or len(duck_names) != len(duck_types):
            raise TypeError("DuckDB returned invalid column metadata.")
        produced: object = cast(object, relation)
        active.append(produced)
        return produced, [ColumnInfo(name=str(name), type_label=_duck_label(str(dtype))) for name, dtype in zip(duck_names, duck_types)]
    if adapter == "Sqlite":
        conn = cast(sqlite3.Connection, driver)
        if payload["transaction_mode"] == "Manual":
            if not conn.in_transaction:
                conn.execute("begin;")
            begin = sql.strip().rstrip(";").strip().casefold()
            if begin in ("begin", "begin transaction", "begin deferred", "begin deferred transaction", "begin immediate", "begin immediate transaction", "begin exclusive", "begin exclusive transaction"):
                return None, []
        cursor = conn.cursor()
        active.append(cursor)
        cursor.execute(sql)
        if cursor.description is None:
            return None, []
        return cursor, [ColumnInfo(name=str(entry[0]), type_label="?") for entry in cursor.description]
    if adapter == "Postgres":
        pg = cast(psycopg.Connection[tuple[object, ...]], driver)
        if payload["transaction_mode"] == "Manual" and pg.info.transaction_status == psycopg.pq.TransactionStatus.IDLE:
            pg.execute("BEGIN")
        pg_cursor = pg.cursor()
        active.append(pg_cursor)
        pg_cursor.execute(sql.encode("utf-8"))
        if pg_cursor.description is None:
            return None, []
        return pg_cursor, [ColumnInfo(name=entry.name, type_label=_pg_label(entry.type_code)) for entry in pg_cursor.description]
    if adapter == "BigQuery":
        job: Any = sdk.query(sql)
        current: object = cast(object, job)
        active.append(current)
        rows: Any = job.result(max_results=0)
        schema_raw: object = cast(object, rows.schema)
        fields = _sequence(schema_raw)
        if fields is None or not fields:
            return None, []
        columns_bq: list[ColumnInfo] = []
        for raw_field in fields:
            field: Any = raw_field
            columns_bq.append(ColumnInfo(name=str(cast(object, field.name)), type_label=_generic_label(cast(object, field.field_type))))
        return current, columns_bq
    if adapter == "Cassandra":
        mode = payload["transaction_mode"]
        level_name = "LOCAL_ONE"
        for name in _CASS_LEVELS.split(","):
            if isinstance(mode, str) and name[:10] == mode:
                level_name = name
                break
        levels: Any = cassandra.ConsistencyLevel
        query_sdk: Any = cassandra.query
        statement: object = cast(object, query_sdk.SimpleStatement(sql, consistency_level=levels.name_to_value[level_name]))
        active.append(statement)
        returned: Any = sdk.execute(statement)
        cass_names_raw: object = cast(object, returned.column_names)
        cass_names = _sequence(cass_names_raw)
        if cass_names is None or not cass_names:
            return None, []
        cass_types_raw: object = cast(object, returned.column_types)
        cass_types = _sequence(cass_types_raw)
        columns_cql = [ColumnInfo(name=str(name), type_label=_generic_label(cass_types[index]) if cass_types is not None and index < len(cass_types) else "?") for index, name in enumerate(cass_names)]
        produced_cql: object = cast(object, returned)
        active.append(produced_cql)
        return produced_cql, columns_cql
    if adapter == "NebulaGraph":
        active.append(driver)
        response: Any = sdk.execute(sql)
        if not bool(cast(object, response.is_succeeded())):
            raise RuntimeError(str(cast(object, response.error_msg())))
        nebula_keys_raw: object = cast(object, response.keys())
        nebula_keys = _sequence(nebula_keys_raw)
        if nebula_keys is None:
            raise TypeError("NebulaGraph returned invalid column metadata.")
        if not nebula_keys:
            return None, []
        columns_nebula = [ColumnInfo(name=key.decode("utf-8") if isinstance(key, bytes) else str(key), type_label="?") for key in nebula_keys]
        produced_nebula: object = cast(object, response)
        active.append(produced_nebula)
        return produced_nebula, columns_nebula
    kwargs: dict[str, object] = {"buffered": False} if adapter == "MySql" else {}
    dbapi_cursor: Any = sdk.cursor(**kwargs)
    current_cursor: object = cast(object, dbapi_cursor)
    active.append(current_cursor)
    dbapi_cursor.execute(_chdb_bounded(sql, limit) if adapter == "Chdb" else sql)
    dbapi_columns = _description_columns(cast(object, dbapi_cursor.description), adapter)
    if dbapi_columns is None:
        return None, []
    return current_cursor, dbapi_columns


def execute_statements(connection: Connection, statements: CottList[str], limit: Option[U64], continue_on_error: bool) -> CottList[ExecutedStatement]:
    title = _title(_adapter_name(connection.adapter))
    payload = _session(connection)
    if payload is None:
        return _unavailable(statements, title, "Invalid session handle.", continue_on_error)
    guard = cast(contextlib.AbstractContextManager[object], payload["lock"])
    active = cast(list[object], payload["active"])
    adapter = cast(str, payload["adapter"])
    bound: int | None = limit.value if isinstance(limit, Some) else None
    results: list[ExecutedStatement] = []
    with guard:
        if payload["closed"] is True:
            return _unavailable(statements, title, "The connection is closed.", continue_on_error)
        for index, sql in enumerate(statements):
            before = len(active)
            try:
                if index == 0:
                    try:
                        _cott_fixture_database("write")
                    except CottContractViolation as violation:
                        if violation.message != "fixture adapters are inactive":
                            raise
                produced, columns = _run_one(adapter, payload["driver"], payload, active, sql, bound)
                for item in active[before:]:
                    if produced is not item:
                        close_error = _discard(active, item, adapter)
                        if close_error is not None:
                            raise close_error
            except (Exception, KeyboardInterrupt) as error:
                message = _message(error)
                for item in active[before:]:
                    close_error = _discard(active, item, adapter)
                    if close_error is not None:
                        message += f"\nCursor close failed: {close_error}"
                if _is_cancel(error):
                    results.append(_failure(index, sql, _CANCEL_TITLE, _CANCEL_MESSAGE))
                else:
                    results.append(_failure(index, sql, title, message))
                if not continue_on_error:
                    break
                continue
            if produced is None:
                results.append(ExecutedStatement(index=index, sql=sql, cursor=Nothing(), failure=Nothing(), columns=CottList(values=[])))
            else:
                pending: Opaque[Literal["harlequin.pending_result"]] = Opaque(tag="harlequin.pending_result", value=produced)
                results.append(ExecutedStatement(index=index, sql=sql, cursor=Some(value=pending), failure=Nothing(), columns=CottList(values=columns)))
    return CottList(values=results)
