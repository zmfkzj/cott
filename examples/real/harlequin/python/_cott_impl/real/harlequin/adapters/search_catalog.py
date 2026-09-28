import contextlib
import threading
from collections.abc import Sequence
from typing import Any, Final, cast

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some
from real.harlequin.adapters_types import AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_Postgres, AdapterKind_Sqlite, AdapterKind_Trino, Connection, ConnectionRequest, QueryError, QueryError_Failed, SettingValue_Flag, SettingValue_Text
from real.harlequin.catalog import normalize_catalog
from real.harlequin.catalog_types import CatalogEntry, CatalogKind, CatalogKind_Column, CatalogKind_Database, CatalogKind_Other, CatalogKind_Schema, CatalogKind_Table, CatalogKind_TemporaryTable, CatalogKind_View

_TAG: Final[str] = "harlequin.session"
_TITLE: Final[str] = "Harlequin could not search the catalog."


def _fail(title: str, message: str) -> Err[QueryError]:
    return Err(error=QueryError_Failed(title=title, message=message))


def _adapter_name(adapter: AdapterKind) -> str:
    if isinstance(adapter, AdapterKind_DuckDb):
        return "DuckDb"
    if isinstance(adapter, AdapterKind_Sqlite):
        return "Sqlite"
    if isinstance(adapter, AdapterKind_Postgres):
        return "Postgres"
    if isinstance(adapter, AdapterKind_MySql):
        return "MySql"
    if isinstance(adapter, AdapterKind_Odbc):
        return "Odbc"
    if isinstance(adapter, AdapterKind_BigQuery):
        return "BigQuery"
    if isinstance(adapter, AdapterKind_Trino):
        return "Trino"
    if isinstance(adapter, AdapterKind_Databricks):
        return "Databricks"
    if isinstance(adapter, AdapterKind_Adbc):
        return "Adbc"
    if isinstance(adapter, AdapterKind_Cassandra):
        return "Cassandra"
    if isinstance(adapter, AdapterKind_NebulaGraph):
        return "NebulaGraph"
    return "Chdb"


def _display(adapter: str) -> str:
    if adapter == "DuckDb":
        return "DuckDB"
    if adapter == "Sqlite":
        return "SQLite"
    if adapter == "MySql":
        return "MySQL"
    if adapter == "Chdb":
        return "chDB"
    if adapter == "Odbc":
        return "ODBC"
    if adapter == "Adbc":
        return "ADBC"
    return adapter


def _pattern(term: str) -> str:
    return "%" + term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def _quote(name: str, mark: str) -> str:
    return mark + name.replace(mark, mark + mark) + mark


def _cell(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return "" if value is None else str(value)


def _rows(raw: object) -> list[list[str]]:
    source: Sequence[object]
    if isinstance(raw, list):
        source = cast(list[object], raw)
    elif isinstance(raw, tuple):
        source = cast(tuple[object, ...], raw)
    else:
        raise TypeError("Database metadata did not return rows.")
    result: list[list[str]] = []
    for item in source:
        cells: Sequence[object]
        if isinstance(item, list):
            cells = cast(list[object], item)
        elif isinstance(item, tuple):
            cells = cast(tuple[object, ...], item)
        else:
            raise TypeError("Database metadata contained a non-row value.")
        result.append([_cell(value) for value in cells])
    return result


def _sqlite_rows(driver: Any, sql: str, parameters: tuple[object, ...]) -> list[list[str]]:
    cursor: Any = driver.execute(sql, parameters)
    try:
        return _rows(cast(object, cursor.fetchall()))
    finally:
        cursor.close()


def _postgres_rows(driver: Any, sql: str, parameters: tuple[object, ...]) -> list[list[str]]:
    cursor: Any = driver.cursor()
    try:
        cursor.execute(sql.encode("utf-8"), parameters)
        return _rows(cast(object, cursor.fetchall()))
    finally:
        cursor.close()


def _mysql_rows(driver: Any, sql: str, pattern: str) -> list[list[str]]:
    cursor: Any = driver.cursor()
    try:
        cursor.execute(sql, (pattern,))
        return _rows(cast(object, cursor.fetchall()))
    finally:
        cursor.close()


def _chdb_rows(driver: Any, active: list[object], sql: str) -> list[list[str]]:
    cursor: Any = driver.cursor()
    executing: object = cast(object, cursor)
    active.append(executing)
    try:
        cursor.execute(sql)
        return _rows(cast(object, cursor.fetchall()))
    finally:
        active.remove(executing)
        cursor.close()


def _duck_type(data_type: str) -> str:
    raw = data_type.strip().upper()
    if raw.endswith("[]"):
        return "[" + _duck_type(raw[:-2]) + "]"
    base = raw.split("(", 1)[0].split("[", 1)[0].strip()
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
    if base.startswith("TIMESTAMP"):
        return "ts"
    if base == "TIME":
        return "t"
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


def _sqlite_type(data_type: str) -> str:
    base = data_type.strip().upper().split("(", 1)[0].strip()
    if base == "TEXT":
        return "s"
    if base == "INTEGER":
        return "##"
    if base in ("REAL", "NUMERIC"):
        return "#.#"
    if base == "BLOB":
        return "b"
    return "" if base == "" else "?"


def _sql_type(data_type: str) -> str:
    base = data_type.strip().lower()
    if base.startswith(("bool", "tinyint(1)")):
        return "t/f"
    if base.startswith(("decimal", "numeric", "real", "double", "float")):
        return "#.#"
    if base.startswith(("tinyint", "smallint", "mediumint", "integer", "bigint", "serial", "number", "int2", "int4", "int8")) or base == "int" or base.startswith(("int(", "int ")):
        return "#"
    if base.startswith(("timestamp", "datetime")):
        return "ts"
    if base.startswith("date"):
        return "d"
    if base.startswith("time"):
        return "t"
    if base.startswith(("blob", "binary", "bytea", "varbinary")) or base.endswith("blob"):
        return "0b"
    if base.startswith(("varchar", "char", "character", "text", "string", "uuid", "citext", "json")) or base.endswith("text"):
        return "s"
    return "?"


def _kind(kind: str) -> CatalogKind:
    if kind == "db":
        return CatalogKind_Database()
    if kind == "sch":
        return CatalogKind_Schema()
    if kind == "col":
        return CatalogKind_Column()
    if kind in ("view", "mv"):
        return CatalogKind_View()
    if kind == "temp":
        return CatalogKind_TemporaryTable()
    if kind == "dic":
        return CatalogKind_Other()
    return CatalogKind_Table()


def _label(kind: str, data_type: str, adapter: str) -> str:
    if kind == "col":
        if adapter == "DuckDb":
            return _duck_type(data_type)
        if adapter == "Sqlite":
            return _sqlite_type(data_type)
        if adapter == "Chdb":
            return data_type
        return _sql_type(data_type)
    if kind == "db":
        return "db"
    if kind == "sch":
        return "sch"
    if kind == "view":
        return "v"
    if kind == "temp":
        return "tmp"
    if kind == "mv":
        return "mv"
    if kind == "dic":
        return "dic"
    if kind == "foreign":
        return "f"
    return "t"


def _add(entries: dict[str, CatalogEntry], path: list[tuple[str, str, str]], mark: str, adapter: str) -> None:
    parent: str | None = None
    parts: list[str] = []
    for depth, (name, kind, data_type) in enumerate(path):
        quoted = _quote(name, mark)
        parts.append(quoted)
        ident = ".".join(parts)
        if ident not in entries:
            expandable = kind != "col"
            query_name = quoted if kind in ("db", "col") else ".".join(parts[-2:])
            entries[ident] = CatalogEntry(id=ident, parent=Nothing() if parent is None else Some(value=parent), depth=depth, label=name, type_label=_label(kind, data_type, adapter), kind=_kind(kind), qualified_identifier=ident, query_name=query_name, expandable=expandable, loaded=not expandable)
        parent = ident


def _sorted_entries(entries: dict[str, CatalogEntry]) -> list[CatalogEntry]:
    children: dict[str, list[CatalogEntry]] = {}
    roots: list[CatalogEntry] = []
    for entry in entries.values():
        parent = entry.parent
        if isinstance(parent, Some):
            children.setdefault(parent.value, []).append(entry)
        else:
            roots.append(entry)
    roots.sort(key=lambda entry: (entry.label.casefold(), entry.label))
    stack = list(reversed(roots))
    ordered: list[CatalogEntry] = []
    while stack:
        entry = stack.pop()
        ordered.append(entry)
        siblings = children.get(entry.id)
        if siblings is not None:
            siblings.sort(key=lambda child: (child.label.casefold(), child.label))
            stack.extend(reversed(siblings))
    return ordered


def _relation(table_type: str) -> str:
    lower = table_type.lower()
    if "temp" in lower:
        return "temp"
    if "materialized" in lower:
        return "mv"
    if "view" in lower:
        return "view"
    if "foreign" in lower:
        return "foreign"
    return "table"


def _chdb_relation(engine: str) -> str:
    lower = engine.lower()
    if lower in ("materializedview", "materialized view"):
        return "mv"
    if lower == "view":
        return "view"
    if lower == "dictionary":
        return "dic"
    return "table"


def _duck(driver: Any, pattern: str, entries: dict[str, CatalogEntry]) -> None:
    sql = """WITH db AS (SELECT database_name d FROM duckdb_databases() WHERE NOT internal),
sch AS (SELECT database_name d, schema_name s FROM duckdb_schemas() WHERE database_name IN (SELECT d FROM db) AND schema_name NOT IN ('pg_catalog', 'information_schema')),
rel AS (SELECT database_name d, schema_name s, table_name r, CASE WHEN temporary THEN 'temp' ELSE 'table' END k FROM duckdb_tables() WHERE NOT internal UNION ALL SELECT database_name, schema_name, view_name, 'view' FROM duckdb_views() WHERE NOT internal),
r AS (SELECT rel.* FROM rel JOIN sch ON rel.d = sch.d AND rel.s = sch.s)
SELECT 0 lvl, d, NULL::VARCHAR s, NULL::VARCHAR r, NULL::VARCHAR k, NULL::VARCHAR col, NULL::VARCHAR t FROM db WHERE d ILIKE $1 ESCAPE '\\'
UNION ALL SELECT 1, d, s, NULL, NULL, NULL, NULL FROM sch WHERE s ILIKE $1 ESCAPE '\\'
UNION ALL SELECT 2, d, s, r, k, NULL, NULL FROM r WHERE r ILIKE $1 ESCAPE '\\'
UNION ALL SELECT 3, c.database_name, c.schema_name, c.table_name, r.k, c.column_name, c.data_type FROM duckdb_columns() c JOIN r ON c.database_name = r.d AND c.schema_name = r.s AND c.table_name = r.r WHERE c.column_name ILIKE $1 ESCAPE '\\'
ORDER BY 1, 2, 3, 4, 6"""
    for row in _rows(cast(object, driver.execute(sql, [pattern]).fetchall())):
        if len(row) != 7:
            raise TypeError("DuckDB returned malformed catalog metadata.")
        path = [(row[1], "db", "")]
        if row[0] in ("1", "2", "3"):
            path.append((row[2], "sch", ""))
        if row[0] in ("2", "3"):
            path.append((row[3], row[4], ""))
        if row[0] == "3":
            path.append((row[5], "col", row[6]))
        _add(entries, path, '"', "DuckDb")


def _sqlite(driver: Any, pattern: str, entries: dict[str, CatalogEntry]) -> None:
    databases = _sqlite_rows(driver, "SELECT name, lower(name) LIKE lower(?) ESCAPE '\\' FROM pragma_database_list ORDER BY name", (pattern,))
    for db_row in databases:
        if len(db_row) != 2:
            raise TypeError("SQLite returned malformed database metadata.")
        db = db_row[0]
        if db_row[1] == "1":
            _add(entries, [(db, "db", "")], '"', "Sqlite")
        schema = _quote(db, '"') + ".sqlite_schema"
        relations = _sqlite_rows(driver, f"SELECT name, type FROM {schema} WHERE type IN ('table', 'view') AND lower(name) LIKE lower(?) ESCAPE '\\' ORDER BY name", (pattern,))
        for row in relations:
            if len(row) != 2:
                raise TypeError("SQLite returned malformed relation metadata.")
            _add(entries, [(db, "db", ""), (row[0], _relation(row[1]), "")], '"', "Sqlite")
        columns = _sqlite_rows(driver, f"SELECT r.name, r.type, c.name, c.type FROM {schema} r JOIN pragma_table_info(r.name, ?) c WHERE r.type IN ('table', 'view') AND lower(c.name) LIKE lower(?) ESCAPE '\\' ORDER BY r.name, c.name", (db, pattern))
        for row in columns:
            if len(row) != 4:
                raise TypeError("SQLite returned malformed column metadata.")
            _add(entries, [(db, "db", ""), (row[0], _relation(row[1]), ""), (row[2], "col", row[3])], '"', "Sqlite")


def _postgres(driver: Any, pattern: str, entries: dict[str, CatalogEntry]) -> None:
    current = _postgres_rows(driver, "SELECT current_database()", ())
    if len(current) != 1 or len(current[0]) != 1:
        raise TypeError("Postgres returned no current database.")
    connected = current[0][0]
    for row in _postgres_rows(driver, "SELECT datname FROM pg_database WHERE NOT datistemplate AND datname ILIKE %s ESCAPE '\\' ORDER BY datname", (pattern,)):
        if len(row) != 1:
            raise TypeError("Postgres returned malformed database metadata.")
        _add(entries, [(row[0], "db", "")], '"', "Postgres")
    for row in _postgres_rows(driver, "SELECT nspname FROM pg_namespace WHERE nspname ILIKE %s ESCAPE '\\' ORDER BY nspname", (pattern,)):
        if len(row) != 1:
            raise TypeError("Postgres returned malformed schema metadata.")
        _add(entries, [(connected, "db", ""), (row[0], "sch", "")], '"', "Postgres")
    relation_sql = """SELECT n.nspname, c.relname, CASE WHEN c.relpersistence = 't' THEN 'temp' WHEN c.relkind = 'v' THEN 'view' WHEN c.relkind = 'm' THEN 'mv' WHEN c.relkind = 'f' THEN 'foreign' ELSE 'table' END
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind IN ('r', 'p', 'v', 'm', 'f') AND c.relname ILIKE %s ESCAPE '\\' ORDER BY n.nspname, c.relname"""
    for row in _postgres_rows(driver, relation_sql, (pattern,)):
        if len(row) != 3:
            raise TypeError("Postgres returned malformed relation metadata.")
        _add(entries, [(connected, "db", ""), (row[0], "sch", ""), (row[1], row[2], "")], '"', "Postgres")
    column_sql = """SELECT n.nspname, c.relname, CASE WHEN c.relpersistence = 't' THEN 'temp' WHEN c.relkind = 'v' THEN 'view' WHEN c.relkind = 'm' THEN 'mv' WHEN c.relkind = 'f' THEN 'foreign' ELSE 'table' END, a.attname, format_type(a.atttypid, a.atttypmod)
FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('r', 'p', 'v', 'm', 'f') AND a.attnum > 0 AND NOT a.attisdropped AND a.attname ILIKE %s ESCAPE '\\' ORDER BY n.nspname, c.relname, a.attname"""
    for row in _postgres_rows(driver, column_sql, (pattern,)):
        if len(row) != 5:
            raise TypeError("Postgres returned malformed column metadata.")
        _add(entries, [(connected, "db", ""), (row[0], "sch", ""), (row[1], row[2], ""), (row[3], "col", row[4])], '"', "Postgres")


def _mysql(driver: Any, pattern: str, entries: dict[str, CatalogEntry]) -> None:
    db_sql = "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys') AND lower(schema_name) LIKE lower(%s) ESCAPE '\\\\' ORDER BY schema_name"
    for row in _mysql_rows(driver, db_sql, pattern):
        if len(row) != 1:
            raise TypeError("MySQL returned malformed database metadata.")
        _add(entries, [(row[0], "db", "")], "`", "MySql")
    relation_sql = """SELECT table_schema, table_name, table_type FROM information_schema.tables
WHERE table_schema NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys') AND lower(table_name) LIKE lower(%s) ESCAPE '\\\\' ORDER BY table_schema, table_name"""
    for row in _mysql_rows(driver, relation_sql, pattern):
        if len(row) != 3:
            raise TypeError("MySQL returned malformed relation metadata.")
        _add(entries, [(row[0], "db", ""), (row[1], _relation(row[2]), "")], "`", "MySql")
    column_sql = """SELECT c.table_schema, c.table_name, t.table_type, c.column_name, c.data_type FROM information_schema.columns c
JOIN information_schema.tables t ON c.table_schema = t.table_schema AND c.table_name = t.table_name
WHERE c.table_schema NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys') AND lower(c.column_name) LIKE lower(%s) ESCAPE '\\\\' ORDER BY c.table_schema, c.table_name, c.column_name"""
    for row in _mysql_rows(driver, column_sql, pattern):
        if len(row) != 5:
            raise TypeError("MySQL returned malformed column metadata.")
        _add(entries, [(row[0], "db", ""), (row[1], _relation(row[2]), ""), (row[3], "col", row[4])], "`", "MySql")


def _chdb(driver: Any, active: list[object], request: ConnectionRequest, term: str, entries: dict[str, CatalogEntry]) -> None:
    limit = 100
    show_system = False
    for setting in request.settings:
        if setting.name == "catalog_search_limit" and isinstance(setting.value, SettingValue_Text):
            limit = max(0, int(setting.value.value))
        if setting.name == "show_system" and isinstance(setting.value, SettingValue_Flag):
            show_system = setting.value.value
    literal = "'" + term.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r") + "'"
    db_filter = "" if show_system else "name NOT IN ('system', 'INFORMATION_SCHEMA', 'information_schema') AND "
    table_filter = "" if show_system else "database NOT IN ('system', 'INFORMATION_SCHEMA', 'information_schema') AND "
    column_filter = "" if show_system else "c.database NOT IN ('system', 'INFORMATION_SCHEMA', 'information_schema') AND "
    db_sql = f"SELECT name FROM system.databases WHERE {db_filter}positionCaseInsensitive(name, {literal}) > 0 ORDER BY name LIMIT {limit}"
    for row in _chdb_rows(driver, active, db_sql):
        if len(row) != 1:
            raise TypeError("chDB returned malformed database metadata.")
        _add(entries, [(row[0], "db", "")], "`", "Chdb")
    relation_sql = f"SELECT database, name, engine FROM system.tables WHERE {table_filter}positionCaseInsensitive(name, {literal}) > 0 ORDER BY database, name LIMIT {limit}"
    for row in _chdb_rows(driver, active, relation_sql):
        if len(row) != 3:
            raise TypeError("chDB returned malformed relation metadata.")
        _add(entries, [(row[0], "db", ""), (row[1], _chdb_relation(row[2]), "")], "`", "Chdb")
    column_sql = f"SELECT c.database, c.table, t.engine, c.name, c.type FROM system.columns c JOIN system.tables t ON c.database = t.database AND c.table = t.name WHERE {column_filter}positionCaseInsensitive(c.name, {literal}) > 0 ORDER BY c.database, c.table, c.position LIMIT {limit}"
    for row in _chdb_rows(driver, active, column_sql):
        if len(row) != 5:
            raise TypeError("chDB returned malformed column metadata.")
        _add(entries, [(row[0], "db", ""), (row[1], _chdb_relation(row[2]), ""), (row[3], "col", row[4])], "`", "Chdb")


def search_catalog(connection: Connection, term: str) -> Result[CottList[CatalogEntry], QueryError]:
    handle = connection.session
    if handle.tag != _TAG:
        return _fail(_TITLE, "The connection handle is not a Harlequin session.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail(_TITLE, "The connection handle is malformed.")
    payload = cast(dict[str, object], raw)
    if len(payload) != 9 or any(key not in payload for key in ("adapter", "driver", "request", "cleanup", "lock", "closed", "transaction_mode", "modes", "active")):
        return _fail(_TITLE, "The connection handle is malformed.")
    adapter = payload["adapter"]
    lock = payload["lock"]
    request = payload["request"]
    active_raw = payload["active"]
    modes = payload["modes"]
    if (
        not isinstance(adapter, str)
        or not isinstance(lock, type(threading.RLock()))
        or not isinstance(request, ConnectionRequest)
        or not isinstance(active_raw, list)
        or not isinstance(payload["closed"], bool)
        or not isinstance(payload["cleanup"], contextlib.ExitStack)
        or not isinstance(modes, list)
        or (payload["transaction_mode"] is not None and not isinstance(payload["transaction_mode"], str))
        or payload["driver"] is None
    ):
        return _fail(_TITLE, "The connection handle is malformed.")
    if any(not isinstance(mode, str) for mode in cast(list[object], modes)) or adapter != _adapter_name(connection.adapter) or request.adapter != connection.adapter:
        return _fail(_TITLE, "The connection handle is malformed.")
    active = cast(list[object], active_raw)
    with cast(contextlib.AbstractContextManager[object], lock):
        if payload["closed"]:
            return _fail(_TITLE, "The connection is closed.")
        if adapter not in ("DuckDb", "Sqlite", "Postgres", "MySql", "Chdb"):
            return _fail(_TITLE, f"The {_display(adapter)} adapter does not support catalog search.")
        driver: Any = payload["driver"]
        entries: dict[str, CatalogEntry] = {}
        pattern = _pattern(term)
        try:
            if adapter == "DuckDb":
                _duck(driver, pattern, entries)
            elif adapter == "Sqlite":
                _sqlite(driver, pattern, entries)
            elif adapter == "Postgres":
                _postgres(driver, pattern, entries)
            elif adapter == "MySql":
                _mysql(driver, pattern, entries)
            else:
                _chdb(driver, active, request, term, entries)
        except Exception as error:
            return _fail(f"{_display(adapter)} raised an error searching the catalog:", str(error))
    return Ok(value=normalize_catalog(CottList(values=_sorted_entries(entries))))
