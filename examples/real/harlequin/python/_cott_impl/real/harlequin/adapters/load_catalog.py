import contextlib
from typing import Any, Final, cast

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some

from real.harlequin.adapters_types import Connection, ConnectionRequest, QueryError, QueryError_Failed, SettingValue_Flag, SettingValue_Text
from real.harlequin.catalog import normalize_catalog
from real.harlequin.catalog_types import CatalogEntry, CatalogKind, CatalogKind_Column, CatalogKind_Database, CatalogKind_Other, CatalogKind_Schema, CatalogKind_Table, CatalogKind_TemporaryTable, CatalogKind_View

_TAG: Final[str] = "harlequin.session"
_TITLE: Final[str] = "Harlequin could not load the data catalog."
_KEYS: Final[str] = "adapter,driver,request,cleanup,lock,closed,transaction_mode,modes,active"


def _fail(message: str) -> Result[CottList[CatalogEntry], QueryError]:
    return Err(error=QueryError_Failed(title=_TITLE, message=message))


def _quote(name: str, backtick: bool) -> str:
    if backtick:
        return "`" + name.replace("`", "``") + "`"
    return '"' + name.replace('"', '""') + '"'


def _s(value: object) -> str:
    return "" if value is None else str(value)


def _rows(raw: Any) -> list[list[object]]:
    out: list[list[object]] = []
    for row in raw:
        item: Any = row
        out.append([cast(object, v) for v in item])
    return out


def _query(adapter: str, driver: Any, sql: str) -> list[list[object]]:
    if adapter in ("DuckDb", "Sqlite", "Postgres"):
        return _rows(driver.execute(sql).fetchall())
    cursor: Any = driver.cursor()
    try:
        cursor.execute(sql)
        return _rows(cursor.fetchall())
    finally:
        cursor.close()


def _text(request: ConnectionRequest, key: str) -> str | None:
    for setting in request.settings:
        value = setting.value
        if setting.name.replace("-", "_") == key and isinstance(value, SettingValue_Text) and value.value != "":
            return value.value
    return None


def _flag(request: ConnectionRequest, key: str) -> bool:
    for setting in request.settings:
        value = setting.value
        if setting.name.replace("-", "_") == key and isinstance(value, SettingValue_Flag):
            return value.value
    return False


def _kind(name: str) -> CatalogKind:
    if name == "Database":
        return CatalogKind_Database()
    if name == "Schema":
        return CatalogKind_Schema()
    if name == "Table":
        return CatalogKind_Table()
    if name == "View":
        return CatalogKind_View()
    if name == "TemporaryTable":
        return CatalogKind_TemporaryTable()
    if name == "Column":
        return CatalogKind_Column()
    return CatalogKind_Other()


def _duckdb(driver: Any) -> list[tuple[int, str, str | None, str, str, str, str, bool, bool]]:
    out: list[tuple[int, str, str | None, str, str, str, str, bool, bool]] = []
    for row in _query("DuckDb", driver, "pragma show_databases"):
        db = _s(row[0])
        qid = _quote(db, False)
        out.append((0, qid, None, db, "db", "Database", qid, True, True))
    known = {r[1] for r in out}
    sql = "select catalog_name, schema_name from information_schema.schemata where schema_name not in ('pg_catalog', 'information_schema')"
    for row in _query("DuckDb", driver, sql):
        db, sch = _s(row[0]), _s(row[1])
        parent = _quote(db, False)
        if parent not in known:
            continue
        qid = parent + "." + _quote(sch, False)
        out.append((1, qid, parent, sch, "sch", "Schema", qid, True, False))
    return out


def _flat_dbs(adapter: str, driver: Any, sql: str, type_label: str, index: int, backtick: bool) -> list[tuple[int, str, str | None, str, str, str, str, bool, bool]]:
    out: list[tuple[int, str, str | None, str, str, str, str, bool, bool]] = []
    for row in _query(adapter, driver, sql):
        name = _s(row[index])
        qid = _quote(name, backtick)
        out.append((0, qid, None, name, type_label, "Database", qid, True, False))
    return out


def _postgres(driver: Any) -> list[tuple[int, str, str | None, str, str, str, str, bool, bool]]:
    out: list[tuple[int, str, str | None, str, str, str, str, bool, bool]] = []
    current = _s(_query("Postgres", driver, "select current_database()")[0][0])
    path = {_s(r[0]) for r in _query("Postgres", driver, "select unnest(current_schemas(false))")}
    for row in _query("Postgres", driver, "select datname from pg_database where not datistemplate"):
        db = _s(row[0])
        qid = _quote(db, False)
        out.append((0, qid, None, db, "db", "Database", qid, db == current, db == current))
    parent = _quote(current, False)
    sql = "select nspname from pg_namespace where nspname not like 'pg\\_%' and nspname <> 'information_schema'"
    for row in _query("Postgres", driver, sql):
        sch = _s(row[0])
        qid = parent + "." + _quote(sch, False)
        out.append((1, qid, parent, sch, "sch", "Schema", qid, True, sch in path))
    sql = (
        "select n.nspname, c.relname, c.relkind::text, c.relpersistence::text from pg_class c "
        "join pg_namespace n on n.oid = c.relnamespace "
        "where c.relkind in ('r', 'p', 'v', 'm', 'f') and n.nspname = any(current_schemas(false))"
    )
    labels = {"r": ("t", "Table"), "p": ("t", "Table"), "v": ("v", "View"), "m": ("mv", "View"), "f": ("f", "Table")}
    for row in _query("Postgres", driver, sql):
        sch, rel, kind, persistence = _s(row[0]), _s(row[1]), _s(row[2]), _s(row[3])
        label, kname = ("tmp", "TemporaryTable") if persistence == "t" else labels.get(kind, ("t", "Table"))
        sparent = parent + "." + _quote(sch, False)
        qid = sparent + "." + _quote(rel, False)
        query_name = _quote(sch, False) + "." + _quote(rel, False)
        out.append((2, qid, sparent, rel, label, kname, query_name, True, False))
    return out


def _odbc(driver: Any) -> list[tuple[int, str, str | None, str, str, str, str, bool, bool]]:
    out: list[tuple[int, str, str | None, str, str, str, str, bool, bool]] = []
    seen: set[str] = set()
    cursor: Any = driver.cursor()
    try:
        rows = _rows(cursor.tables())
    finally:
        cursor.close()
    for row in rows:
        cat, sch = _s(row[0]), _s(row[1])
        cid = _quote(cat, False)
        if cid not in seen:
            seen.add(cid)
            out.append((0, cid, None, cat, "db", "Database", cid, True, True))
        sid = cid + "." + _quote(sch, False)
        if sid not in seen:
            seen.add(sid)
            out.append((1, sid, cid, sch, "sch", "Schema", sid, True, False))
    return out


def _bigquery(driver: Any, request: ConnectionRequest) -> list[tuple[int, str, str | None, str, str, str, str, bool, bool]]:
    out: list[tuple[int, str, str | None, str, str, str, str, bool, bool]] = []
    project = _s(cast(object, driver.project))
    location = (_text(request, "location") or "US").lower()
    seen: set[str] = set()
    for ds_raw in driver.list_datasets():
        ds: Any = ds_raw
        name = _s(cast(object, ds.dataset_id))
        qid = _quote(name, True)
        seen.add(qid)
        out.append((0, qid, None, name, "ds", "Database", qid, True, True))
    sql = (
        "select table_schema, table_name, column_name, data_type from "
        + _quote(project, True) + ".`region-" + location + "`.INFORMATION_SCHEMA.COLUMNS"
    )
    job: Any = driver.query(sql, location=location)
    for row in _rows(job.result()):
        sch, table, column, dtype = _s(row[0]), _s(row[1]), _s(row[2]), _s(row[3])
        sid = _quote(sch, True)
        if sid not in seen:
            continue
        tid = sid + "." + _quote(table, True)
        if tid not in seen:
            seen.add(tid)
            out.append((1, tid, sid, table, "t", "Table", tid, True, True))
        cid = tid + "." + _quote(column, True)
        out.append((2, cid, tid, column, dtype, "Column", _quote(column, True), False, True))
    return out


def _trino(driver: Any, request: ConnectionRequest) -> list[tuple[int, str, str | None, str, str, str, str, bool, bool]]:
    configured = _text(request, "catalog")
    out: list[tuple[int, str, str | None, str, str, str, str, bool, bool]] = []
    for row in _query("Trino", driver, "show catalogs"):
        name = _s(row[0])
        if name in ("jmx", "memory", "system") or (configured is not None and name != configured):
            continue
        qid = _quote(name, False)
        out.append((0, qid, None, name, "c", "Database", qid, True, False))
    return out


def _add_column_tree(out: list[tuple[int, str, str | None, str, str, str, str, bool, bool]], seen: set[str], row: list[object], backtick: bool) -> None:
    cat, sch, table, ttype, column, dtype = (_s(v) for v in row[:6])
    ids: list[str] = []
    levels = (
        (cat, "catalog", "Database"),
        (sch, "s", "Schema"),
        (table, ttype, "View" if "VIEW" in ttype.upper() else "Table"),
    )
    for depth, (name, label, kname) in enumerate(levels):
        if name == "":
            return
        parent = ids[-1] if ids else None
        qid = (parent + "." if parent else "") + _quote(name, backtick)
        ids.append(qid)
        if qid not in seen:
            seen.add(qid)
            out.append((depth, qid, parent, name, label, kname, qid, True, True))
    if column != "":
        cid = ids[-1] + "." + _quote(column, backtick)
        if cid not in seen:
            seen.add(cid)
            out.append((3, cid, ids[-1], column, dtype, "Column", _quote(column, backtick), False, True))


def _databricks(driver: Any, request: ConnectionRequest) -> list[tuple[int, str, str | None, str, str, str, str, bool, bool]]:
    out: list[tuple[int, str, str | None, str, str, str, str, bool, bool]] = []
    seen: set[str] = set()
    for row in _query("Databricks", driver, "select catalog_name from system.information_schema.catalogs"):
        _add_column_tree(out, seen, [row[0], "", "", "", "", ""], True)
    for row in _query("Databricks", driver, "select catalog_name, schema_name from system.information_schema.schemata"):
        _add_column_tree(out, seen, [row[0], row[1], "", "", "", ""], True)
    sql = (
        "select t.table_catalog, t.table_schema, t.table_name, t.table_type, c.column_name, c.full_data_type "
        "from system.information_schema.tables t left join system.information_schema.columns c "
        "on c.table_catalog = t.table_catalog and c.table_schema = t.table_schema and c.table_name = t.table_name"
    )
    for row in _query("Databricks", driver, sql):
        _add_column_tree(out, seen, row, True)
    if not _flag(request, "skip_legacy_indexing"):
        cursor: Any = driver.cursor()
        try:
            cursor.tables(catalog_name="hive_metastore")
            tables = _rows(cursor.fetchall())
            cursor.columns(catalog_name="hive_metastore")
            columns = _rows(cursor.fetchall())
        finally:
            cursor.close()
        types: dict[tuple[str, str], str] = {}
        for row in tables:
            types[(_s(row[1]), _s(row[2]))] = _s(row[3])
            _add_column_tree(out, seen, [row[0], row[1], row[2], row[3], "", ""], True)
        for row in columns:
            ttype = types.get((_s(row[1]), _s(row[2])), "TABLE")
            _add_column_tree(out, seen, [row[0], row[1], row[2], ttype, row[3], row[5]], True)
    return out


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return cast(list[object], value)
    return []


def _as_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return cast(dict[str, object], value)
    return {}


def _adbc(driver: Any) -> list[tuple[int, str, str | None, str, str, str, str, bool, bool]]:
    out: list[tuple[int, str, str | None, str, str, str, str, bool, bool]] = []
    reader: Any = driver.adbc_get_objects()
    objects = _as_list(cast(object, reader.read_all().to_pylist()))
    for cat_raw in objects:
        cat = _as_dict(cat_raw)
        cname = _s(cat.get("catalog_name"))
        if cname in ("template0", "template1"):
            continue
        cid = _quote(cname, False)
        out.append((0, cid, None, cname, "db", "Database", cid, True, True))
        for sch_raw in _as_list(cat.get("catalog_db_schemas")):
            sch = _as_dict(sch_raw)
            sname = _s(sch.get("db_schema_name"))
            sid = cid + "." + _quote(sname, False)
            out.append((1, sid, cid, sname, "s", "Schema", sid, True, True))
            for tab_raw in _as_list(sch.get("db_schema_tables")):
                tab = _as_dict(tab_raw)
                tname = _s(tab.get("table_name"))
                view = _s(tab.get("table_type")).upper() == "VIEW"
                tid = sid + "." + _quote(tname, False)
                qn = _quote(sname, False) + "." + _quote(tname, False)
                out.append((2, tid, sid, tname, "v" if view else "t", "View" if view else "Table", qn, True, True))
                for col_raw in _as_list(tab.get("table_columns")):
                    col = _as_dict(col_raw)
                    colname = _s(col.get("column_name"))
                    colid = tid + "." + _quote(colname, False)
                    out.append((3, colid, tid, colname, _s(col.get("xdbc_type_name")), "Column", _quote(colname, False), False, True))
    return out


def _cassandra(driver: Any) -> list[tuple[int, str, str | None, str, str, str, str, bool, bool]]:
    out: list[tuple[int, str, str | None, str, str, str, str, bool, bool]] = []
    keyspaces: Any = driver.cluster.metadata.keyspaces
    for ks_name_raw, ks_raw in keyspaces.items():
        ks: Any = ks_raw
        ksname = _s(cast(object, ks_name_raw))
        kid = _quote(ksname, False)
        out.append((0, kid, None, ksname, "ks", "Database", kid, True, True))
        groups: list[tuple[Any, str, str]] = [(ks.tables, "t", "Table"), (ks.views, "v", "View")]
        for group, label, kname in groups:
            for rel_name_raw, rel_raw in group.items():
                rel: Any = rel_raw
                rname = _s(cast(object, rel_name_raw))
                rid = kid + "." + _quote(rname, False)
                out.append((1, rid, kid, rname, label, kname, rid, True, True))
                for col_name_raw, col_raw in rel.columns.items():
                    col: Any = col_raw
                    cname = _s(cast(object, col_name_raw))
                    cid = rid + "." + _quote(cname, False)
                    out.append((2, cid, rid, cname, _s(cast(object, col.cql_type)), "Column", _quote(cname, False), False, True))
    return out


def _nebula_rows(session: Any, statement: str) -> list[list[str]]:
    result: Any = session.execute(statement)
    if not bool(cast(object, result.is_succeeded())):
        raise RuntimeError(_s(cast(object, result.error_msg())))
    size = cast(object, result.row_size())
    count = size if isinstance(size, int) else 0
    out: list[list[str]] = []
    for index in range(count):
        values: Any = result.row_values(index)
        out.append([_s(cast(object, v.as_string())) if bool(cast(object, v.is_string())) else _s(cast(object, v)) for v in values])
    return out


def _nebula(driver: Any) -> list[tuple[int, str, str | None, str, str, str, str, bool, bool]]:
    out: list[tuple[int, str, str | None, str, str, str, str, bool, bool]] = []
    for row in _nebula_rows(driver, "SHOW SPACES"):
        space = row[0]
        sid = _quote(space, False)
        out.append((0, sid, None, space, "space", "Database", sid, True, True))
        for kind, label in (("TAGS", "tag"), ("EDGES", "edge")):
            for item in _nebula_rows(driver, "USE `" + space + "`; SHOW " + kind):
                name = item[0]
                iid = sid + "." + _quote(name, False)
                out.append((1, iid, sid, name, label, "Other", _quote(name, False), True, True))
                desc = "USE `" + space + "`; DESC " + kind[:-1] + " `" + name + "`"
                for field in _nebula_rows(driver, desc):
                    fid = iid + "." + _quote(field[0], False)
                    out.append((2, fid, iid, field[0], field[1], "Column", _quote(field[0], False), False, True))
    return out


def _chdb(driver: Any, request: ConnectionRequest) -> list[tuple[int, str, str | None, str, str, str, str, bool, bool]]:
    show_system = _flag(request, "show_system")
    out: list[tuple[int, str, str | None, str, str, str, str, bool, bool]] = []
    for row in _query("Chdb", driver, "select name from system.databases"):
        name = _s(row[0])
        if not show_system and name in ("system", "INFORMATION_SCHEMA", "information_schema"):
            continue
        qid = _quote(name, True)
        out.append((0, qid, None, name, "db", "Database", qid, True, False))
    return out


def _collect(adapter: str, driver: Any, request: ConnectionRequest) -> list[tuple[int, str, str | None, str, str, str, str, bool, bool]]:
    if adapter == "DuckDb":
        return _duckdb(driver)
    if adapter == "Sqlite":
        return _flat_dbs("Sqlite", driver, "pragma database_list", "db", 1, False)
    if adapter == "Postgres":
        return _postgres(driver)
    if adapter == "MySql":
        sql = "select schema_name from information_schema.schemata where schema_name not in ('sys', 'information_schema', 'performance_schema', 'mysql')"
        return _flat_dbs("MySql", driver, sql, "db", 0, True)
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


def _to_entry(row: tuple[int, str, str | None, str, str, str, str, bool, bool]) -> CatalogEntry:
    depth, eid, parent, label, type_label, kind, query_name, expandable, loaded = row
    return CatalogEntry(
        id=eid,
        parent=Nothing() if parent is None else Some(value=parent),
        depth=depth,
        label=label,
        type_label=type_label,
        kind=_kind(kind),
        qualified_identifier=eid,
        query_name=query_name,
        expandable=expandable,
        loaded=loaded,
    )


def _sort_key(row: tuple[int, str, str | None, str, str, str, str, bool, bool]) -> tuple[int, str, str]:
    return (row[0], row[3].casefold(), row[3])


def load_catalog(connection: Connection) -> Result[CottList[CatalogEntry], QueryError]:
    handle = connection.session
    if handle.tag != _TAG:
        return _fail("The connection handle is not a Harlequin session.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail("The connection handle is malformed.")
    payload = cast(dict[str, object], raw)
    if set(payload.keys()) != set(_KEYS.split(",")):
        return _fail("The connection handle is malformed.")
    adapter = payload["adapter"]
    lock = payload["lock"]
    request = payload["request"]
    if not isinstance(adapter, str) or not isinstance(lock, contextlib.AbstractContextManager) or not isinstance(request, ConnectionRequest):
        return _fail("The connection handle is malformed.")
    guard = cast(contextlib.AbstractContextManager[object], lock)
    with guard:
        if payload["closed"] is not False:
            return _fail("The connection is closed.")
        driver: Any = payload["driver"]
        try:
            rows = _collect(adapter, driver, request)
        except Exception as error:
            return _fail(str(error))
    if adapter != "Odbc":
        rows.sort(key=lambda r: _sort_key(r))
    entries = CottList(values=[_to_entry(r) for r in rows])
    return Ok(value=normalize_catalog(entries))
