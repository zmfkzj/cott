import contextlib
from typing import Any, Final, cast

import psycopg
from cott_runtime import CottList, Err, Nothing, Ok, Result, Some

from real.harlequin.adapters_types import Connection, ConnectionRequest, QueryError, QueryError_Failed, SettingValue_Text
from real.harlequin.catalog_types import CatalogEntry, CatalogKind, CatalogKind_Column, CatalogKind_Database, CatalogKind_Schema, CatalogKind_Table, CatalogKind_TemporaryTable, CatalogKind_View

_TAG: Final[str] = "harlequin.session"
_TITLE: Final[str] = "Harlequin could not search the catalog."
_KEYS: Final[str] = "adapter,driver,request,cleanup,lock,closed,transaction_mode,modes,active"
_DEFAULT_LIMIT: Final[int] = 100

_DUCKDB_SQL: Final[str] = """
with dbs as (select database_name as d from duckdb_databases() where not internal),
sch as (
    select database_name as d, schema_name as s from duckdb_schemas()
    where database_name in (select d from dbs) and schema_name not in ('pg_catalog', 'information_schema')
),
rels as (
    select database_name as d, schema_name as s, table_name as r, case when temporary then 'temp' else 'table' end as k
    from duckdb_tables()
    union all
    select database_name, schema_name, view_name, case when temporary then 'temp' else 'view' end
    from duckdb_views() where not internal
),
rels2 as (select rels.d, rels.s, rels.r, rels.k from rels join sch on rels.d = sch.d and rels.s = sch.s)
select 0 as lvl, d, null::varchar as s, null::varchar as r, null::varchar as k, null::varchar as col, null::varchar as t
from dbs where d ilike $1 escape '\\'
union all
select 1, d, s, null, null, null, null from sch where s ilike $1 escape '\\'
union all
select 2, d, s, r, k, null, null from rels2 where r ilike $1 escape '\\'
union all
select 3, c.database_name, c.schema_name, c.table_name, rels2.k, c.column_name, c.data_type
from duckdb_columns() c join rels2 on c.database_name = rels2.d and c.schema_name = rels2.s and c.table_name = rels2.r
where c.column_name ilike $1 escape '\\'
order by 1, 2, 3, 4, 6
"""

_MYSQL_DBS: Final[str] = """
select schema_name from information_schema.schemata
where schema_name not in ('mysql', 'information_schema', 'performance_schema', 'sys')
and lower(schema_name) like lower(%s) escape '\\\\' order by 1
"""
_MYSQL_RELS: Final[str] = """
select table_schema, table_name, table_type from information_schema.tables
where table_schema not in ('mysql', 'information_schema', 'performance_schema', 'sys')
and lower(table_name) like lower(%s) escape '\\\\' order by 1, 2
"""
_MYSQL_COLS: Final[str] = """
select c.table_schema, c.table_name, t.table_type, c.column_name, c.column_type
from information_schema.columns c join information_schema.tables t
on c.table_schema = t.table_schema and c.table_name = t.table_name
where c.table_schema not in ('mysql', 'information_schema', 'performance_schema', 'sys')
and lower(c.column_name) like lower(%s) escape '\\\\' order by 1, 2, 4
"""

_CHDB_EXCLUDED: Final[str] = "('system', 'INFORMATION_SCHEMA', 'information_schema')"


def _fail(title: str, message: str) -> Result[CottList[CatalogEntry], QueryError]:
    return Err(error=QueryError_Failed(title=title, message=message))


def _display(adapter: str) -> str:
    names: dict[str, str] = {
        "DuckDb": "DuckDB",
        "Sqlite": "SQLite",
        "Postgres": "Postgres",
        "MySql": "MySQL",
        "Odbc": "ODBC",
        "Adbc": "ADBC",
        "Chdb": "chDB",
    }
    return names.get(adapter, adapter)


def _like_pattern(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _quote(name: str, quote: str) -> str:
    return quote + name.replace(quote, quote + quote) + quote


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return str(value)


def _rows(raw: object) -> list[list[str]]:
    result: list[list[str]] = []
    if not isinstance(raw, (list, tuple)):
        return result
    for row in list(cast(list[object], raw)):
        if isinstance(row, (list, tuple)):
            result.append([_cell(item) for item in list(cast(list[object], row))])
    return result


def _column_label(data_type: str) -> str:
    t = data_type.lower()
    if t.endswith("[]") or t.startswith(("list", "array")):
        return "[]"
    if t.startswith(("struct", "map", "json", "tuple", "object")):
        return "{}"
    if t.startswith(("bool", "tinyint(1)")):
        return "t/f"
    if t.startswith(("decimal", "numeric", "real", "double", "float")):
        return "#.#"
    if "int" in t:
        return "#"
    if t.startswith("timestamp") or t.startswith("datetime"):
        return "ts"
    if t.startswith("date"):
        return "d"
    if t.startswith("time"):
        return "t"
    if t.startswith("interval"):
        return "|-|"
    if t.startswith("uuid"):
        return "uid"
    if t.startswith(("blob", "bytea", "binary", "varbinary", "bit")):
        return "0b"
    if t.startswith(("varchar", "char", "text", "string", "character", "nvarchar", "enum", "fixedstring", "lowcardinality(string")) or "string" in t:
        return "s"
    return "?" if t == "" else t[:3]


def _relation_kind(raw: str) -> str:
    r = raw.lower()
    if "temp" in r:
        return "temp"
    if "view" in r:
        return "view"
    return "table"


def _kind(name: str) -> CatalogKind:
    if name == "db":
        return CatalogKind_Database()
    if name == "sch":
        return CatalogKind_Schema()
    if name == "view":
        return CatalogKind_View()
    if name == "temp":
        return CatalogKind_TemporaryTable()
    if name == "col":
        return CatalogKind_Column()
    return CatalogKind_Table()


def _type_label(kind: str, data_type: str) -> str:
    labels: dict[str, str] = {"db": "db", "sch": "sch", "table": "t", "view": "v", "temp": "tmp"}
    if kind == "col":
        return _column_label(data_type)
    return labels.get(kind, "")


def _add_path(entries: dict[str, CatalogEntry], order: list[str], segments: list[tuple[str, str, str]], quote: str) -> None:
    parent: str | None = None
    parts: list[str] = []
    for depth, (label, kind, data_type) in enumerate(segments):
        quoted = _quote(label, quote)
        parts.append(quoted)
        ident = ".".join(parts)
        if ident not in entries:
            expandable = kind != "col"
            entries[ident] = CatalogEntry(
                id=ident,
                parent=Nothing() if parent is None else Some(value=parent),
                depth=depth,
                label=label,
                type_label=_type_label(kind, data_type),
                kind=_kind(kind),
                qualified_identifier=ident,
                query_name=quoted,
                expandable=expandable,
                loaded=not expandable,
            )
            order.append(ident)
        parent = ident


def _search_duckdb(driver: Any, pattern: str, entries: dict[str, CatalogEntry], order: list[str]) -> None:
    rows = _rows(cast(object, driver.execute(_DUCKDB_SQL, [pattern]).fetchall()))
    for row in rows:
        if len(row) < 7:
            continue
        level = row[0]
        segments: list[tuple[str, str, str]] = [(row[1], "db", "")]
        if level in ("1", "2", "3"):
            segments.append((row[2], "sch", ""))
        if level in ("2", "3"):
            segments.append((row[3], _relation_kind(row[4]), ""))
        if level == "3":
            segments.append((row[5], "col", row[6]))
        _add_path(entries, order, segments, '"')


def _sqlite_like(driver: Any, value: str, pattern: str) -> bool:
    rows = _rows(cast(object, driver.execute("select ? like ? escape '\\'", (value, pattern)).fetchall()))
    return bool(rows) and rows[0][0] == "1"


def _search_sqlite(driver: Any, pattern: str, entries: dict[str, CatalogEntry], order: list[str]) -> None:
    dbs = [row[0] for row in _rows(cast(object, driver.execute("select name from pragma_database_list order by seq").fetchall())) if row]
    for db in dbs:
        if _sqlite_like(driver, db, pattern):
            _add_path(entries, order, [(db, "db", "")], '"')
        schema = _quote(db, '"') + ".sqlite_schema"
        rel_sql = (
            f"select name, type from {schema} where type in ('table', 'view') "
            "and name not like 'sqlite\\_%' escape '\\' and name like ? escape '\\' order by name"
        )
        for row in _rows(cast(object, driver.execute(rel_sql, (pattern,)).fetchall())):
            kind = "temp" if db == "temp" and row[1] == "table" else _relation_kind(row[1])
            _add_path(entries, order, [(db, "db", ""), (row[0], kind, "")], '"')
        col_sql = (
            f"select r.name, r.type, c.name, c.type from {schema} r join pragma_table_info(r.name, ?) c "
            "where r.type in ('table', 'view') and r.name not like 'sqlite\\_%' escape '\\' "
            "and c.name like ? escape '\\' order by r.name, c.cid"
        )
        for row in _rows(cast(object, driver.execute(col_sql, (db, pattern)).fetchall())):
            kind = "temp" if db == "temp" and row[1] == "table" else _relation_kind(row[1])
            _add_path(entries, order, [(db, "db", ""), (row[0], kind, ""), (row[2], "col", row[3])], '"')


def _search_postgres(conn: psycopg.Connection[tuple[object, ...]], pattern: str, entries: dict[str, CatalogEntry], order: list[str]) -> None:
    db_row = conn.execute("select current_database(), current_database() ilike %s escape '\\'", (pattern,)).fetchone()
    if db_row is None:
        return
    db = _cell(db_row[0])
    if db_row[1] is True:
        _add_path(entries, order, [(db, "db", "")], '"')
    schemas = conn.execute(
        "select schema_name from information_schema.schemata where catalog_name = current_database() "
        "and schema_name <> 'information_schema' and left(schema_name, 3) <> 'pg_' "
        "and schema_name ilike %s escape '\\' order by 1",
        (pattern,),
    ).fetchall()
    for row in _rows(schemas):
        _add_path(entries, order, [(db, "db", ""), (row[0], "sch", "")], '"')
    rels = conn.execute(
        "select table_schema, table_name, table_type from information_schema.tables "
        "where table_catalog = current_database() and table_schema <> 'information_schema' "
        "and left(table_schema, 3) <> 'pg_' and table_name ilike %s escape '\\' order by 1, 2",
        (pattern,),
    ).fetchall()
    for row in _rows(rels):
        _add_path(entries, order, [(db, "db", ""), (row[0], "sch", ""), (row[1], _relation_kind(row[2]), "")], '"')
    cols = conn.execute(
        "select c.table_schema, c.table_name, t.table_type, c.column_name, c.data_type "
        "from information_schema.columns c join information_schema.tables t "
        "on c.table_catalog = t.table_catalog and c.table_schema = t.table_schema and c.table_name = t.table_name "
        "where c.table_catalog = current_database() and c.table_schema <> 'information_schema' "
        "and left(c.table_schema, 3) <> 'pg_' and c.column_name ilike %s escape '\\' order by 1, 2, 4",
        (pattern,),
    ).fetchall()
    for row in _rows(cols):
        _add_path(
            entries,
            order,
            [(db, "db", ""), (row[0], "sch", ""), (row[1], _relation_kind(row[2]), ""), (row[3], "col", row[4])],
            '"',
        )


def _mysql_query(driver: Any, sql: str, pattern: str) -> list[list[str]]:
    cursor: Any = driver.cursor()
    try:
        cursor.execute(sql, (pattern,))
        return _rows(cast(object, cursor.fetchall()))
    finally:
        cursor.close()


def _search_mysql(driver: Any, pattern: str, entries: dict[str, CatalogEntry], order: list[str]) -> None:
    for row in _mysql_query(driver, _MYSQL_DBS, pattern):
        _add_path(entries, order, [(row[0], "db", "")], "`")
    for row in _mysql_query(driver, _MYSQL_RELS, pattern):
        _add_path(entries, order, [(row[0], "db", ""), (row[1], _relation_kind(row[2]), "")], "`")
    for row in _mysql_query(driver, _MYSQL_COLS, pattern):
        _add_path(
            entries, order, [(row[0], "db", ""), (row[1], _relation_kind(row[2]), ""), (row[3], "col", row[4])], "`"
        )


def _chdb_limit(request: ConnectionRequest) -> int:
    for setting in request.settings:
        if setting.name.replace("-", "_") == "catalog_search_limit":
            value = setting.value
            if isinstance(value, SettingValue_Text) and value.value.strip().isdigit():
                return max(int(value.value.strip()), 1)
    return _DEFAULT_LIMIT


def _chdb_query(driver: Any, active: list[object], sql: str) -> list[list[str]]:
    cursor: Any = driver.cursor()
    active.append(cast(object, cursor))
    try:
        cursor.execute(sql)
        return _rows(cast(object, cursor.fetchall()))
    finally:
        active.remove(cast(object, cursor))
        cursor.close()


def _search_chdb(driver: Any, active: list[object], term: str, pattern: str, limit: int, entries: dict[str, CatalogEntry], order: list[str]) -> None:
    lit = "'" + term.replace("\\", "\\\\").replace("'", "\\'") + "'"
    like = "'" + pattern.replace("\\", "\\\\").replace("'", "\\'") + "'"
    dbs_sql = (
        f"select name from system.databases where name not in {_CHDB_EXCLUDED} "
        f"and positionCaseInsensitive(name, {lit}) > 0 and name ilike {like} order by name limit {limit}"
    )
    rels_sql = (
        f"select database, name, if(is_temporary, 'temp', engine) from system.tables "
        f"where database not in {_CHDB_EXCLUDED} and positionCaseInsensitive(name, {lit}) > 0 and name ilike {like} "
        f"order by database, name limit {limit}"
    )
    cols_sql = (
        f"select c.database, c.table, if(t.is_temporary, 'temp', t.engine), c.name, c.type "
        f"from system.columns c join system.tables t on c.database = t.database and c.table = t.name "
        f"where c.database not in {_CHDB_EXCLUDED} and positionCaseInsensitive(c.name, {lit}) > 0 and c.name ilike {like} "
        f"order by c.database, c.table, c.position limit {limit}"
    )
    for row in _chdb_query(driver, active, dbs_sql):
        _add_path(entries, order, [(row[0], "db", "")], "`")
    for row in _chdb_query(driver, active, rels_sql):
        _add_path(entries, order, [(row[0], "db", ""), (row[1], _relation_kind(row[2]), "")], "`")
    for row in _chdb_query(driver, active, cols_sql):
        _add_path(
            entries, order, [(row[0], "db", ""), (row[1], _relation_kind(row[2]), ""), (row[3], "col", row[4])], "`"
        )


def search_catalog(connection: Connection, term: str) -> Result[CottList[CatalogEntry], QueryError]:
    handle = connection.session
    if handle.tag != _TAG:
        return _fail(_TITLE, "The connection handle is not a Harlequin session.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail(_TITLE, "The connection handle is malformed.")
    payload = cast(dict[str, object], raw)
    if set(payload.keys()) != set(_KEYS.split(",")):
        return _fail(_TITLE, "The connection handle is malformed.")
    adapter = payload["adapter"]
    lock = payload["lock"]
    active_raw = payload["active"]
    request = payload["request"]
    if (
        not isinstance(adapter, str)
        or not isinstance(lock, contextlib.AbstractContextManager)
        or not isinstance(payload["closed"], bool)
        or not isinstance(active_raw, list)
        or not isinstance(request, ConnectionRequest)
    ):
        return _fail(_TITLE, "The connection handle is malformed.")
    active = cast(list[object], active_raw)
    if adapter not in ("DuckDb", "Sqlite", "Postgres", "MySql", "Chdb"):
        return _fail(_TITLE, f"The {_display(adapter)} adapter does not support catalog search.")
    pattern = _like_pattern(term)
    entries: dict[str, CatalogEntry] = {}
    order: list[str] = []
    with cast(contextlib.AbstractContextManager[object], lock):
        if payload["closed"] is True:
            return _fail(_TITLE, "The connection is closed.")
        driver: Any = payload["driver"]
        try:
            if adapter == "DuckDb":
                _search_duckdb(driver, pattern, entries, order)
            elif adapter == "Sqlite":
                _search_sqlite(driver, pattern, entries, order)
            elif adapter == "Postgres":
                _search_postgres(cast(psycopg.Connection[tuple[object, ...]], driver), pattern, entries, order)
            elif adapter == "MySql":
                _search_mysql(driver, pattern, entries, order)
            else:
                _search_chdb(driver, active, term, pattern, _chdb_limit(request), entries, order)
        except Exception as error:
            return _fail(f"{_display(adapter)} raised an error searching the catalog:", str(error))
    return Ok(value=CottList(values=[entries[ident] for ident in order]))
