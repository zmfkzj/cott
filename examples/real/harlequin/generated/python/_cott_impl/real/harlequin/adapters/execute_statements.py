import contextlib
import sqlite3
from typing import Any, Final, Literal, cast

import cassandra
import cassandra.query
import duckdb
import psycopg
import psycopg.errors
import psycopg.pq
from cott_runtime import U64, CottList, Nothing, Opaque, Some

from real.harlequin.adapters_types import Connection, ExecutedStatement, QueryFailure
from real.harlequin.results_types import ColumnInfo

_TAG: Final[str] = "harlequin.session"
_KEYS: Final[str] = "adapter,driver,request,cleanup,lock,closed,transaction_mode,modes,active"
_CANCEL_TITLE: Final[str] = "Query canceled"
_CANCEL_MESSAGE: Final[str] = "The query was canceled."
_CASS_LEVELS: Final[str] = "ANY,ONE,TWO,THREE,QUORUM,ALL,LOCAL_QUORUM,EACH_QUORUM,SERIAL,LOCAL_SERIAL,LOCAL_ONE"


def _title(adapter: str) -> str:
    names: dict[str, str] = {
        "DuckDb": "DuckDB",
        "Sqlite": "SQLite",
        "Postgres": "Postgres",
        "MySql": "MySQL",
        "Odbc": "ODBC",
        "BigQuery": "BigQuery",
        "Trino": "Trino",
        "Databricks": "Databricks",
        "Adbc": "ADBC",
        "Chdb": "chDB",
    }
    if adapter == "Cassandra":
        return "Cassandra raised an error:"
    if adapter == "NebulaGraph":
        return "NebulaGraph raised an error:"
    return f"{names.get(adapter, adapter)} raised an error when compiling or running your query:"


def _duck_label(dtype: str) -> str:
    text = dtype.strip().upper()
    if text.endswith("[]"):
        return "[" + _duck_label(text[:-2]) + "]"
    base = text.split("(")[0].split("[")[0].strip()
    labels: dict[str, str] = {
        "SQLNULL": "\\n",
        "NULL": "\\n",
        "BOOLEAN": "t/f",
        "TINYINT": "#",
        "SMALLINT": "#",
        "INTEGER": "#",
        "UTINYINT": "u#",
        "USMALLINT": "u#",
        "UINTEGER": "u#",
        "BIGINT": "##",
        "UBIGINT": "u##",
        "HUGEINT": "###",
        "UUID": "uid",
        "FLOAT": "#.#",
        "DOUBLE": "#.#",
        "DECIMAL": "#.#",
        "REAL": "#.#",
        "DATE": "d",
        "TIME": "t",
        "TIME_TZ": "ttz",
        "TIME WITH TIME ZONE": "ttz",
        "TIMESTAMP_TZ": "ttz",
        "TIMESTAMP WITH TIME ZONE": "ttz",
        "VARCHAR": "s",
        "BLOB": "0b",
        "BIT": "010",
        "INTERVAL": "|-|",
        "STRUCT": "{}",
        "MAP": "{m}",
    }
    if base in labels:
        return labels[base]
    if base.startswith("TIMESTAMP"):
        return "ts"
    return "?"


def _generic_label(code: object) -> str:
    text = str(code).lower()
    if code is None or text == "":
        return "?"
    if "bool" in text:
        return "t/f"
    if "timestamp" in text or "datetime" in text:
        return "ts"
    if "date" in text:
        return "d"
    if "int" in text or "long" in text:
        return "#"
    if any(word in text for word in ("float", "double", "decimal", "numeric", "real")):
        return "#.#"
    if any(word in text for word in ("str", "char", "text", "unicode")):
        return "s"
    if any(word in text for word in ("bytes", "binary", "blob")):
        return "0b"
    return "?"


def _pg_label(oid: object) -> str:
    if not isinstance(oid, int):
        return "?"
    labels: dict[int, str] = {
        16: "t/f",
        20: "#",
        21: "#",
        23: "#",
        700: "#.#",
        701: "#.#",
        1700: "#.#",
        25: "s",
        1043: "s",
        1042: "s",
        19: "s",
        1082: "d",
        1114: "ts",
        1184: "ts",
        17: "0b",
    }
    return labels.get(oid, "?")


def _description_columns(description: object, adapter: str) -> list[ColumnInfo] | None:
    if description is None:
        return None
    if not isinstance(description, (list, tuple)):
        return None
    columns: list[ColumnInfo] = []
    for raw in list(cast(list[object], description)):
        entry: Any = raw
        name = str(cast(object, entry[0]))
        code = cast(object, entry[1])
        label = _pg_label(code) if adapter == "Postgres" else _generic_label(code)
        columns.append(ColumnInfo(name=name, type_label=label))
    return columns


def _is_cancel(error: BaseException) -> bool:
    if isinstance(error, (duckdb.InterruptException, psycopg.errors.QueryCanceled, KeyboardInterrupt)):
        return True
    text = str(error).lower()
    return "interrupted" in text or "cancel" in text


def _chdb_bounded(sql: str, limit: int | None) -> str:
    if limit is None:
        return sql
    body = sql.strip().rstrip(";").rstrip()
    words = body.split()
    if not words or words[0].lower() not in ("select", "with") or " settings " in f" {body.lower()} ":
        return sql
    return f"{body} SETTINGS max_result_rows={limit + 1}, result_overflow_mode='break'"


def _run_one(adapter: str, driver: Any, payload: dict[str, object], active: list[object], sql: str, limit: int | None) -> tuple[object | None, list[ColumnInfo]]:
    if adapter == "DuckDb":
        relation: Any = driver.sql(sql)
        if relation is None:
            return (None, [])
        if limit is not None:
            relation = relation.limit(limit + 1)
        names = [str(n) for n in cast(list[object], relation.columns)]
        types = [str(t) for t in cast(list[object], relation.dtypes)]
        return (cast(object, relation), [ColumnInfo(name=n, type_label=_duck_label(t)) for n, t in zip(names, types)])
    if adapter == "Sqlite":
        conn = cast(sqlite3.Connection, driver)
        if payload["transaction_mode"] == "Manual":
            if not conn.in_transaction:
                conn.execute("begin;")
            words = sql.strip().rstrip(";").split()
            if words and words[0].lower() == "begin":
                return (None, [])
        cur = conn.cursor()
        active.append(cur)
        cur.execute(sql)
        if cur.description is None:
            return (None, [])
        return (cur, [ColumnInfo(name=str(d[0]), type_label="?") for d in cur.description])
    if adapter == "Postgres":
        pconn = cast("psycopg.Connection[tuple[object, ...]]", driver)
        if payload["transaction_mode"] == "Manual" and pconn.info.transaction_status == psycopg.pq.TransactionStatus.IDLE:
            pconn.execute("BEGIN")
        pcur = pconn.cursor()
        active.append(pcur)
        pcur.execute(sql.encode("utf-8"))
        if pcur.description is None:
            return (None, [])
        return (pcur, [ColumnInfo(name=d.name, type_label=_pg_label(d.type_code)) for d in pcur.description])
    if adapter == "BigQuery":
        job: Any = driver.query(sql)
        active.append(cast(object, job))
        rows: Any = job.result()
        schema = cast(object, rows.schema)
        if not isinstance(schema, list) or not schema:
            return (None, [])
        bcols: list[ColumnInfo] = []
        for field_raw in cast(list[object], schema):
            field: Any = field_raw
            bcols.append(ColumnInfo(name=str(cast(object, field.name)), type_label=_generic_label(cast(object, field.field_type))))
        return (cast(object, job), bcols)
    if adapter == "Cassandra":
        mode = payload["transaction_mode"]
        level_name = "LOCAL_ONE"
        for name in _CASS_LEVELS.split(","):
            if isinstance(mode, str) and name[:10] == mode:
                level_name = name
        levels: Any = cassandra.ConsistencyLevel
        query_sdk: Any = cassandra.query
        statement: Any = query_sdk.SimpleStatement(sql, consistency_level=levels.name_to_value[level_name])
        result: Any = driver.execute(statement)
        names_raw = cast(object, result.column_names)
        if not isinstance(names_raw, list) or not names_raw:
            return (None, [])
        types_raw = cast(object, result.column_types)
        ctypes = cast(list[object], types_raw) if isinstance(types_raw, list) else []
        ccols: list[ColumnInfo] = []
        for i, n in enumerate(cast(list[object], names_raw)):
            ccols.append(ColumnInfo(name=str(n), type_label=_generic_label(ctypes[i]) if i < len(ctypes) else "?"))
        return (cast(object, result), ccols)
    if adapter == "NebulaGraph":
        rs: Any = driver.execute(sql)
        if not bool(cast(object, rs.is_succeeded())):
            raise RuntimeError(str(cast(object, rs.error_msg())))
        keys = cast(object, rs.keys())
        if not isinstance(keys, list) or not keys:
            return (None, [])
        return (cast(object, rs), [ColumnInfo(name=str(k), type_label="?") for k in cast(list[object], keys)])
    kwargs: dict[str, object] = {"buffered": False} if adapter == "MySql" else {}
    cursor: Any = driver.cursor(**kwargs)
    active.append(cast(object, cursor))
    cursor.execute(_chdb_bounded(sql, limit) if adapter == "Chdb" else sql)
    gcols = _description_columns(cast(object, cursor.description), adapter)
    if gcols is None:
        return (None, [])
    return (cast(object, cursor), gcols)


def _discard(active: list[object], item: object) -> None:
    for index, candidate in enumerate(active):
        if candidate is item:
            del active[index]
            break
    closer: Any = item
    with contextlib.suppress(Exception):
        closer.close()


def execute_statements(connection: Connection, statements: CottList[str], limit: Some[U64] | Nothing, continue_on_error: bool) -> CottList[ExecutedStatement]:
    empty: list[ExecutedStatement] = []
    handle = connection.session
    if handle.tag != _TAG:
        return CottList(values=empty)
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return CottList(values=empty)
    payload = cast(dict[str, object], raw)
    if set(payload.keys()) != set(_KEYS.split(",")):
        return CottList(values=empty)
    adapter = payload["adapter"]
    lock = payload["lock"]
    active_raw = payload["active"]
    if not isinstance(adapter, str) or not isinstance(active_raw, list) or not isinstance(lock, contextlib.AbstractContextManager):
        return CottList(values=empty)
    active = cast(list[object], active_raw)
    guard = cast(contextlib.AbstractContextManager[object], lock)
    bound: int | None = limit.value if isinstance(limit, Some) else None
    results: list[ExecutedStatement] = []
    title = _title(adapter)
    with guard:
        if payload["closed"] is not False:
            return CottList(values=empty)
        driver: Any = payload["driver"]
        for index, sql in enumerate(statements):
            before = len(active)
            try:
                produced, columns = _run_one(adapter, driver, payload, active, sql, bound)
            except Exception as error:
                for item in list(active[before:]):
                    _discard(active, item)
                if _is_cancel(error):
                    failure = QueryFailure(title=_CANCEL_TITLE, message=_CANCEL_MESSAGE)
                else:
                    failure = QueryFailure(title=title, message=str(error))
                results.append(ExecutedStatement(index=index, sql=sql, cursor=Nothing(), failure=Some(value=failure), columns=CottList(values=[])))
                if not continue_on_error:
                    break
                continue
            if produced is None:
                for item in list(active[before:]):
                    _discard(active, item)
                results.append(ExecutedStatement(index=index, sql=sql, cursor=Nothing(), failure=Nothing(), columns=CottList(values=[])))
                continue
            if not any(item is produced for item in active):
                active.append(produced)
            pending: Opaque[Literal["harlequin.pending_result"]] = Opaque(tag="harlequin.pending_result", value=produced)
            results.append(ExecutedStatement(index=index, sql=sql, cursor=Some(value=pending), failure=Nothing(), columns=CottList(values=columns)))
    return CottList(values=results)
