import contextlib
import threading
from typing import Any, Final, cast

from cott_runtime import CottContractViolation, CottList, Err, Nothing, Ok, Result, Some, U64, _cott_fixture_database
from real.harlequin.adapters_types import AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_Postgres, AdapterKind_Sqlite, AdapterKind_Trino, Connection, ConnectionRequest, QueryError, QueryError_Failed, SettingValue_Flag, SettingValue_Text
from real.harlequin.catalog import normalize_catalog
from real.harlequin.catalog_types import CatalogEntry, CatalogKind, CatalogKind_Column, CatalogKind_Database, CatalogKind_Other, CatalogKind_Schema, CatalogKind_Table, CatalogKind_TemporaryTable, CatalogKind_View

_TAG: Final[str] = "harlequin.session"
_TITLE: Final[str] = "Harlequin could not load the data catalog."
_KEYS: Final[str] = "adapter,driver,request,cleanup,lock,closed,transaction_mode,modes,active"


def _fail(message: str) -> Result[CottList[CatalogEntry], QueryError]:
    return Err(error=QueryError_Failed(title=_TITLE, message=message))


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
    if handle.tag != _TAG:
        return None
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return None
    payload = cast(dict[str, object], raw)
    if set(payload) != set(_KEYS.split(",")):
        return None
    adapter = payload["adapter"]
    request = payload["request"]
    if not isinstance(adapter, str) or not isinstance(request, ConnectionRequest):
        return None
    if adapter != _adapter_name(connection.adapter) or adapter != _adapter_name(request.adapter):
        return None
    if connection.read_only != request.read_only or payload["driver"] is None:
        return None
    if not isinstance(payload["cleanup"], contextlib.ExitStack):
        return None
    if not isinstance(payload["lock"], type(threading.RLock())) or not isinstance(payload["closed"], bool):
        return None
    mode = payload["transaction_mode"]
    if mode is not None and not isinstance(mode, str):
        return None
    modes = payload["modes"]
    active = payload["active"]
    if not isinstance(modes, list) or not isinstance(active, list):
        return None
    if any(not isinstance(label, str) for label in cast(list[object], modes)):
        return None
    if mode is not None and mode not in cast(list[str], modes):
        return None
    return payload


def _boundary() -> None:
    try:
        _cott_fixture_database("read")
    except CottContractViolation as error:
        if error.message == "fixture adapters are inactive":
            return
        cause = error.__cause__
        if isinstance(cause, OSError):
            raise cause
        raise RuntimeError(error.message) from error


def _quote(name: str, backtick: bool) -> str:
    if backtick:
        return "`" + name.replace("`", "``") + "`"
    return '"' + name.replace('"', '""') + '"'


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _rows(raw: Any) -> list[list[object]]:
    result: list[list[object]] = []
    for row_raw in raw:
        row: Any = row_raw
        result.append([cast(object, value) for value in row])
    return result


def _query(adapter: str, driver: Any, sql: str) -> list[list[object]]:
    if adapter == "DuckDb":
        return _rows(driver.execute(sql).fetchall())
    if adapter == "Sqlite":
        sqlite_cursor: Any = driver.execute(sql)
        try:
            return _rows(sqlite_cursor.fetchall())
        finally:
            sqlite_cursor.close()
    cursor: Any = driver.cursor()
    try:
        if adapter == "Postgres":
            cursor.execute(sql.encode("utf-8"))
        else:
            cursor.execute(sql)
        return _rows(cursor.fetchall())
    finally:
        cursor.close()


def _setting_text(request: ConnectionRequest, key: str) -> str | None:
    for setting in request.settings:
        value = setting.value
        if setting.name.replace("-", "_") == key and isinstance(value, SettingValue_Text) and value.value != "":
            return value.value
    return None


def _setting_flag(request: ConnectionRequest, key: str) -> bool:
    for setting in request.settings:
        value = setting.value
        if setting.name.replace("-", "_") == key and isinstance(value, SettingValue_Flag):
            return value.value
    return False


def _entry(parent: str | None, depth: U64, label: str, type_label: str, kind: CatalogKind, query_name: str, expandable: bool, loaded: bool, backtick: bool) -> CatalogEntry:
    identifier = (parent + "." if parent is not None else "") + _quote(label, backtick)
    return CatalogEntry(id=identifier, parent=Nothing() if parent is None else Some(value=parent), depth=depth, label=label, type_label=type_label, kind=kind, qualified_identifier=identifier, query_name=query_name, expandable=expandable, loaded=loaded)


def _duckdb(driver: Any) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    databases: set[str] = set()
    for row in _query("DuckDb", driver, "pragma show_databases"):
        name = _text(row[0])
        identifier = _quote(name, False)
        databases.add(identifier)
        entries.append(_entry(None, 0, name, "db", CatalogKind_Database(), identifier, False, True, False))
    for row in _query("DuckDb", driver, "select catalog_name, schema_name from information_schema.schemata where schema_name not in ('pg_catalog', 'information_schema')"):
        database = _quote(_text(row[0]), False)
        if database in databases:
            schema = _text(row[1])
            name = database + "." + _quote(schema, False)
            entries.append(_entry(database, 1, schema, "sch", CatalogKind_Schema(), name, True, False, False))
    return entries


def _flat_databases(adapter: str, driver: Any, sql: str, column: int, backtick: bool) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    for row in _query(adapter, driver, sql):
        name = _text(row[column])
        identifier = _quote(name, backtick)
        entries.append(_entry(None, 0, name, "db", CatalogKind_Database(), identifier, True, False, backtick))
    return entries


def _postgres(driver: Any) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    current = _text(_query("Postgres", driver, "select current_database()")[0][0])
    search_path = {_text(row[0]) for row in _query("Postgres", driver, "select unnest(current_schemas(false))")}
    for row in _query("Postgres", driver, "select datname from pg_database where not datistemplate"):
        name = _text(row[0])
        identifier = _quote(name, False)
        entries.append(_entry(None, 0, name, "db", CatalogKind_Database(), identifier, False, name == current, False))
    database = _quote(current, False)
    schemas: set[str] = set()
    for row in _query("Postgres", driver, "select nspname from pg_namespace where nspname not like 'pg\\_%' and nspname <> 'information_schema'"):
        schema = _text(row[0])
        schemas.add(schema)
        identifier = database + "." + _quote(schema, False)
        in_path = schema in search_path
        entries.append(_entry(database, 1, schema, "sch", CatalogKind_Schema(), identifier, not in_path, in_path, False))
    relations = (
        "select n.nspname, c.relname, c.relkind::text, c.relpersistence::text from pg_class c "
        "join pg_namespace n on n.oid = c.relnamespace "
        "where c.relkind in ('r', 'p', 'v', 'm', 'f') and n.nspname = any(current_schemas(false))"
    )
    for row in _query("Postgres", driver, relations):
        schema, name, relation_type, persistence = (_text(value) for value in row[:4])
        if schema not in schemas:
            continue
        if persistence == "t":
            label, kind = "tmp", CatalogKind_TemporaryTable()
        elif relation_type == "v":
            label, kind = "v", CatalogKind_View()
        elif relation_type == "m":
            label, kind = "mv", CatalogKind_View()
        elif relation_type == "f":
            label, kind = "f", CatalogKind_Table()
        else:
            label, kind = "t", CatalogKind_Table()
        schema_id = database + "." + _quote(schema, False)
        entries.append(_entry(schema_id, 2, name, label, kind, _quote(schema, False) + "." + _quote(name, False), True, False, False))
    return entries


def _odbc(driver: Any) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    seen: set[str] = set()
    cursor: Any = driver.cursor()
    try:
        rows = _rows(cursor.tables())
    finally:
        cursor.close()
    for row in rows:
        catalog, schema = _text(row[0]), _text(row[1])
        database_id = _quote(catalog, False)
        if database_id not in seen:
            seen.add(database_id)
            entries.append(_entry(None, 0, catalog, "db", CatalogKind_Database(), database_id, False, True, False))
        schema_id = database_id + "." + _quote(schema, False)
        if schema_id not in seen:
            seen.add(schema_id)
            entries.append(_entry(database_id, 1, schema, "sch", CatalogKind_Schema(), schema_id, True, False, False))
    return entries


def _bigquery(driver: Any, request: ConnectionRequest) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    project = _text(cast(object, driver.project))
    location = _setting_text(request, "location") or "US"
    datasets: set[str] = set()
    for dataset_raw in driver.list_datasets():
        dataset: Any = dataset_raw
        name = _text(cast(object, dataset.dataset_id))
        identifier = _quote(name, True)
        datasets.add(identifier)
        entries.append(_entry(None, 0, name, "ds", CatalogKind_Database(), identifier, False, True, True))
    prefix = _quote(project, True) + "." + _quote("region-" + location.lower(), True) + ".INFORMATION_SCHEMA."
    sql = (
        "select t.table_schema, t.table_name, t.table_type, c.column_name, c.data_type from "
        + prefix + "TABLES t left join " + prefix + "COLUMNS c on "
        "c.table_schema = t.table_schema and c.table_name = t.table_name"
    )
    seen: set[str] = set()
    for row in _rows(driver.query(sql, location=location).result()):
        schema, name, table_type, column, data_type = (_text(value) for value in row[:5])
        dataset_id = _quote(schema, True)
        if dataset_id not in datasets:
            continue
        table_id = dataset_id + "." + _quote(name, True)
        if table_id not in seen:
            seen.add(table_id)
            view = "VIEW" in table_type.upper()
            kind: CatalogKind = CatalogKind_View() if view else CatalogKind_Table()
            entries.append(_entry(dataset_id, 1, name, "v" if view else "t", kind, table_id, False, True, True))
        if column != "":
            entries.append(_entry(table_id, 2, column, data_type, CatalogKind_Column(), _quote(column, True), False, True, True))
    return entries


def _databricks_row(entries: list[CatalogEntry], seen: set[str], row: list[object]) -> None:
    catalog, schema, table, table_type, column, data_type = (_text(value) for value in row[:6])
    if catalog == "":
        return
    catalog_id = _quote(catalog, True)
    if catalog_id not in seen:
        seen.add(catalog_id)
        entries.append(_entry(None, 0, catalog, "catalog", CatalogKind_Database(), catalog_id, False, True, True))
    if schema == "":
        return
    schema_id = catalog_id + "." + _quote(schema, True)
    if schema_id not in seen:
        seen.add(schema_id)
        entries.append(_entry(catalog_id, 1, schema, "s", CatalogKind_Schema(), schema_id, False, True, True))
    if table == "":
        return
    table_id = schema_id + "." + _quote(table, True)
    if table_id not in seen:
        seen.add(table_id)
        kind: CatalogKind = CatalogKind_View() if "VIEW" in table_type.upper() else CatalogKind_Table()
        entries.append(_entry(schema_id, 2, table, table_type, kind, table_id, False, True, True))
    if column != "":
        column_id = table_id + "." + _quote(column, True)
        if column_id not in seen:
            seen.add(column_id)
            entries.append(_entry(table_id, 3, column, data_type, CatalogKind_Column(), _quote(column, True), False, True, True))


def _databricks(driver: Any, request: ConnectionRequest) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    seen: set[str] = set()
    for row in _query("Databricks", driver, "select catalog_name from system.information_schema.catalogs"):
        _databricks_row(entries, seen, [row[0], "", "", "", "", ""])
    for row in _query("Databricks", driver, "select catalog_name, schema_name from system.information_schema.schemata"):
        _databricks_row(entries, seen, [row[0], row[1], "", "", "", ""])
    sql = (
        "select t.table_catalog, t.table_schema, t.table_name, t.table_type, c.column_name, c.full_data_type "
        "from system.information_schema.tables t left join system.information_schema.columns c "
        "on c.table_catalog = t.table_catalog and c.table_schema = t.table_schema and c.table_name = t.table_name"
    )
    for row in _query("Databricks", driver, sql):
        _databricks_row(entries, seen, row)
    if not _setting_flag(request, "skip_legacy_indexing"):
        cursor: Any = driver.cursor()
        try:
            cursor.tables(catalog_name="hive_metastore")
            tables = _rows(cursor.fetchall())
            cursor.columns(catalog_name="hive_metastore")
            columns = _rows(cursor.fetchall())
        finally:
            cursor.close()
        table_types: dict[tuple[str, str], str] = {}
        for row in tables:
            table_types[(_text(row[1]), _text(row[2]))] = _text(row[3])
            _databricks_row(entries, seen, [row[0], row[1], row[2], row[3], "", ""])
        for row in columns:
            table_type = table_types.get((_text(row[1]), _text(row[2])), "TABLE")
            _databricks_row(entries, seen, [row[0], row[1], row[2], table_type, row[3], row[5]])
    return entries


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return cast(list[object], value)
    return []


def _as_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return cast(dict[str, object], value)
    return {}


def _adbc(driver: Any) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    reader: Any = driver.adbc_get_objects()
    try:
        catalogs = _as_list(cast(object, reader.read_all().to_pylist()))
    finally:
        reader.close()
    for raw_catalog in catalogs:
        catalog = _as_dict(raw_catalog)
        name = _text(catalog.get("catalog_name"))
        if name in ("template0", "template1"):
            continue
        catalog_id = _quote(name, False)
        entries.append(_entry(None, 0, name, "db", CatalogKind_Database(), catalog_id, False, True, False))
        for raw_schema in _as_list(catalog.get("catalog_db_schemas")):
            schema = _as_dict(raw_schema)
            schema_name = _text(schema.get("db_schema_name"))
            schema_id = catalog_id + "." + _quote(schema_name, False)
            entries.append(_entry(catalog_id, 1, schema_name, "s", CatalogKind_Schema(), schema_id, False, True, False))
            for raw_table in _as_list(schema.get("db_schema_tables")):
                table = _as_dict(raw_table)
                table_name = _text(table.get("table_name"))
                view = _text(table.get("table_type")).upper() == "VIEW"
                table_id = schema_id + "." + _quote(table_name, False)
                query_name = _quote(schema_name, False) + "." + _quote(table_name, False)
                kind: CatalogKind = CatalogKind_View() if view else CatalogKind_Table()
                entries.append(_entry(schema_id, 2, table_name, "v" if view else "t", kind, query_name, False, True, False))
                for raw_column in _as_list(table.get("table_columns")):
                    column = _as_dict(raw_column)
                    column_name = _text(column.get("column_name"))
                    entries.append(_entry(table_id, 3, column_name, _text(column.get("xdbc_type_name")), CatalogKind_Column(), _quote(column_name, False), False, True, False))
    return entries


def _cassandra(driver: Any) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    keyspaces: Any = driver.cluster.metadata.keyspaces
    for name_raw, keyspace_raw in keyspaces.items():
        keyspace: Any = keyspace_raw
        name = _text(cast(object, name_raw))
        keyspace_id = _quote(name, False)
        entries.append(_entry(None, 0, name, "ks", CatalogKind_Database(), keyspace_id, False, True, False))
        groups: list[tuple[Any, str, CatalogKind]] = [(keyspace.tables, "t", CatalogKind_Table()), (keyspace.views, "v", CatalogKind_View())]
        for group, type_label, kind in groups:
            for relation_raw_name, relation_raw in group.items():
                relation: Any = relation_raw
                relation_name = _text(cast(object, relation_raw_name))
                relation_id = keyspace_id + "." + _quote(relation_name, False)
                entries.append(_entry(keyspace_id, 1, relation_name, type_label, kind, relation_id, False, True, False))
                for column_raw_name, column_raw in relation.columns.items():
                    column: Any = column_raw
                    column_name = _text(cast(object, column_raw_name))
                    data_type = _text(cast(object, column.cql_type))
                    entries.append(_entry(relation_id, 2, column_name, data_type, CatalogKind_Column(), _quote(column_name, False), False, True, False))
    return entries


def _nebula_rows(session: Any, statement: str) -> list[list[str]]:
    response: Any = session.execute(statement)
    if not bool(cast(object, response.is_succeeded())):
        raise RuntimeError(_text(cast(object, response.error_msg())))
    count_raw: object = cast(object, response.row_size())
    count = count_raw if isinstance(count_raw, int) and not isinstance(count_raw, bool) else 0
    rows: list[list[str]] = []
    for index in range(count):
        values: Any = response.row_values(index)
        row: list[str] = []
        for value_raw in values:
            value: Any = value_raw
            raw: object = cast(object, value.as_string()) if bool(cast(object, value.is_string())) else cast(object, value)
            row.append(_text(raw))
        rows.append(row)
    return rows


def _nebula(driver: Any) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    for row in _nebula_rows(driver, "SHOW SPACES"):
        space = row[0]
        space_id = _quote(space, False)
        entries.append(_entry(None, 0, space, "space", CatalogKind_Database(), space_id, False, True, False))
        _nebula_rows(driver, "USE " + _quote(space, True))
        for command, type_label, singular in (("TAGS", "tag", "TAG"), ("EDGES", "edge", "EDGE")):
            for relation in _nebula_rows(driver, "SHOW " + command):
                name = relation[0]
                relation_id = space_id + "." + _quote(name, False)
                entries.append(_entry(space_id, 1, name, type_label, CatalogKind_Other(), _quote(name, False), False, True, False))
                for field in _nebula_rows(driver, "DESC " + singular + " " + _quote(name, True)):
                    column = field[0]
                    entries.append(_entry(relation_id, 2, column, field[1], CatalogKind_Column(), _quote(column, False), False, True, False))
    return entries


def _chdb(driver: Any, request: ConnectionRequest) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    show_system = _setting_flag(request, "show_system")
    for row in _query("Chdb", driver, "select name from system.databases"):
        name = _text(row[0])
        if not show_system and name in ("system", "INFORMATION_SCHEMA", "information_schema"):
            continue
        identifier = _quote(name, True)
        entries.append(_entry(None, 0, name, "db", CatalogKind_Database(), identifier, True, False, True))
    return entries


def _collect(adapter: str, driver: Any, request: ConnectionRequest) -> list[CatalogEntry]:
    if adapter == "DuckDb":
        return _duckdb(driver)
    if adapter == "Sqlite":
        return _flat_databases("Sqlite", driver, "pragma database_list", 1, False)
    if adapter == "Postgres":
        return _postgres(driver)
    if adapter == "MySql":
        sql = "select schema_name from information_schema.schemata where schema_name not in ('sys', 'information_schema', 'performance_schema', 'mysql')"
        return _flat_databases("MySql", driver, sql, 0, True)
    if adapter == "Odbc":
        return _odbc(driver)
    if adapter == "BigQuery":
        return _bigquery(driver, request)
    if adapter == "Trino":
        return _trino(driver, request)
    if adapter == "Databricks":
        return _databricks(driver, request)
    if adapter == "Adbc":
        return _adbc(driver)
    if adapter == "Cassandra":
        return _cassandra(driver)
    if adapter == "NebulaGraph":
        return _nebula(driver)
    return _chdb(driver, request)


def _trino(driver: Any, request: ConnectionRequest) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    selected = _setting_text(request, "catalog")
    for row in _query("Trino", driver, "show catalogs"):
        name = _text(row[0])
        if name in ("jmx", "memory", "system") or (selected is not None and selected != name):
            continue
        identifier = _quote(name, False)
        entries.append(_entry(None, 0, name, "c", CatalogKind_Database(), identifier, True, False, False))
    return entries


def load_catalog(connection: Connection) -> Result[CottList[CatalogEntry], QueryError]:
    payload = _session(connection)
    if payload is None:
        return _fail("The connection handle is not a valid Harlequin session.")
    guard = cast(contextlib.AbstractContextManager[object], payload["lock"])
    try:
        with guard:
            if payload["closed"] is True:
                return _fail("The connection is closed.")
            _boundary()
            driver: Any = payload["driver"]
            request = cast(ConnectionRequest, payload["request"])
            adapter = cast(str, payload["adapter"])
            entries = _collect(adapter, driver, request)
            if adapter != "Odbc":
                entries.sort(key=lambda entry: (entry.depth, entry.label.casefold(), entry.label))
            return Ok(value=normalize_catalog(CottList(values=entries)))
    except KeyboardInterrupt:
        return _fail("interrupted")
    except Exception as error:
        return _fail(str(error))
