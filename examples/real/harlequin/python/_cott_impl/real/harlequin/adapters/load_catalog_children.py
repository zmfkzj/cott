import contextlib
import threading
from typing import Any, Final, cast

from cott_runtime import CottList, Err, Ok, Result, Some

from real.harlequin.adapters_types import Connection, ConnectionRequest, QueryError, QueryError_Failed
from real.harlequin.catalog_types import (
    CatalogEntry,
    CatalogKind,
    CatalogKind_Column,
    CatalogKind_Database,
    CatalogKind_Other,
    CatalogKind_Schema,
    CatalogKind_Table,
    CatalogKind_TemporaryTable,
    CatalogKind_View,
)

_TAG: Final[str] = "harlequin.session"
_TITLE: Final[str] = "Catalog Error"
_KEYS: Final[str] = "adapter,driver,request,cleanup,lock,closed,transaction_mode,modes,active"
_ADAPTERS: Final[str] = "DuckDb,Sqlite,Postgres,MySql,Odbc,BigQuery,Trino,Databricks,Adbc,Cassandra,NebulaGraph,Chdb"


def _fail(message: str) -> Result[CottList[CatalogEntry], QueryError]:
    return Err(error=QueryError_Failed(title=_TITLE, message=message))


def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _lit(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def _parts(text: str) -> list[str]:
    parts: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '"':
            i += 1
            buf: list[str] = []
            while i < n:
                if text[i] == '"':
                    if i + 1 < n and text[i + 1] == '"':
                        buf.append('"')
                        i += 2
                        continue
                    i += 1
                    break
                buf.append(text[i])
                i += 1
            parts.append("".join(buf))
            if i < n and text[i] == ".":
                i += 1
        else:
            j = text.find(".", i)
            if j < 0:
                parts.append(text[i:])
                break
            parts.append(text[i:j])
            i = j + 1
    return parts


def _is_relation(kind: CatalogKind) -> bool:
    return isinstance(kind, (CatalogKind_Table, CatalogKind_View, CatalogKind_TemporaryTable))


def _rel_kind(label: str) -> CatalogKind:
    if label == "v" or label == "mv":
        return CatalogKind_View()
    if label == "tmp":
        return CatalogKind_TemporaryTable()
    if label == "?":
        return CatalogKind_Other()
    return CatalogKind_Table()


def _entry(parent: CatalogEntry, label: str, type_label: str, kind: CatalogKind, qualified: str, query_name: str, expandable: bool) -> CatalogEntry:
    return CatalogEntry(
        id=qualified,
        parent=Some(value=parent.id),
        depth=parent.depth + 1,
        label=label,
        type_label=type_label,
        kind=kind,
        qualified_identifier=qualified,
        query_name=query_name,
        expandable=expandable,
        loaded=not expandable,
    )


def _to_rows(raw: object) -> list[tuple[object, ...]]:
    out: list[tuple[object, ...]] = []
    if raw is None:
        return out
    items: Any = raw
    for item in items:
        row: Any = item
        out.append(tuple(cast(object, v) for v in row))
    return out


def _direct(driver: Any, sql: str, params: list[str] | None) -> list[tuple[object, ...]]:
    result: Any = driver.execute(sql) if params is None else driver.execute(sql, params)
    return _to_rows(cast(object, result.fetchall()))


def _cursor(driver: Any, sql: str, params: list[str] | None) -> list[tuple[object, ...]]:
    cursor: Any = driver.cursor()
    try:
        if params is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, params)
        return _to_rows(cast(object, cursor.fetchall()))
    finally:
        cursor.close()


def _duck_label(data_type: str) -> str:
    t = data_type.strip().upper()
    if t.endswith("[]"):
        return "[" + _duck_label(t[:-2]) + "]"
    if t.startswith("TIMESTAMP WITH TIME ZONE"):
        return "ttz"
    base = t.split("(")[0].split("[")[0].strip()
    labels: dict[str, str] = {
        "SQLNULL": "\\n", "BOOLEAN": "t/f", "TINYINT": "#", "SMALLINT": "#", "INTEGER": "#",
        "UTINYINT": "u#", "USMALLINT": "u#", "UINTEGER": "u#", "BIGINT": "##", "UBIGINT": "u##",
        "HUGEINT": "###", "UUID": "uid", "FLOAT": "#.#", "DOUBLE": "#.#", "DECIMAL": "#.#",
        "REAL": "#.#", "DATE": "d", "TIME": "t", "TIME_TZ": "ttz", "TIMESTAMP_TZ": "ttz",
        "TIME WITH TIME ZONE": "ttz", "VARCHAR": "s", "BLOB": "0b", "BIT": "010",
        "INTERVAL": "|-|", "STRUCT": "{}", "MAP": "{m}",
    }
    if base in labels:
        return labels[base]
    if base.startswith("TIMESTAMP"):
        return "ts"
    return "?"


def _sqlite_label(declared: str) -> str:
    t = declared.strip().upper()
    if t == "":
        return ""
    return {"TEXT": "s", "INTEGER": "##", "REAL": "#.#", "NUMERIC": "#.#", "BLOB": "b"}.get(t, "?")


def _generic_label(type_name: str) -> str:
    t = type_name.strip().lower()
    if t.startswith(("bool", "bit")):
        return "t/f"
    if t.startswith("timestamp") or t.startswith("datetime"):
        return "ts"
    if t.startswith("date"):
        return "d"
    if any(k in t for k in ("float", "double", "decimal", "numeric", "real", "money")):
        return "#.#"
    if "int" in t or t in ("serial", "bigserial", "smallserial"):
        return "#"
    if any(k in t for k in ("char", "text", "string", "uuid", "json", "enum")):
        return "s"
    if any(k in t for k in ("binary", "blob", "bytea", "bytes")):
        return "0b"
    return "?"


def _columns(parent: CatalogEntry, rows: list[tuple[object, ...]], mapper: str) -> list[CatalogEntry]:
    out: list[CatalogEntry] = []
    for row in rows:
        name = str(row[0])
        raw_type = "" if row[1] is None else str(row[1])
        if mapper == "duck":
            label = _duck_label(raw_type)
        elif mapper == "sqlite":
            label = _sqlite_label(raw_type)
        elif mapper == "raw":
            label = raw_type
        else:
            label = _generic_label(raw_type)
        out.append(_entry(parent, name, label, CatalogKind_Column(), parent.qualified_identifier + "." + _q(name), _q(name), False))
    return out


def _relations(parent: CatalogEntry, rows: list[tuple[str, str]], query_prefix: str) -> list[CatalogEntry]:
    out: list[CatalogEntry] = []
    for name, label in rows:
        out.append(_entry(parent, name, label, _rel_kind(label), parent.qualified_identifier + "." + _q(name), query_prefix + _q(name), True))
    return out


def _load(adapter: str, driver: Any, parent: CatalogEntry) -> list[CatalogEntry]:
    parts = _parts(parent.qualified_identifier)
    kind = parent.kind
    rows: list[tuple[object, ...]]
    rels: list[tuple[str, str]]
    if adapter == "DuckDb":
        if isinstance(kind, CatalogKind_Schema) and len(parts) >= 2:
            rows = _direct(driver, "select table_name, table_type from information_schema.tables where table_catalog = ? and table_schema = ? order by table_name", [parts[0], parts[1]])
            duck_types = {"BASE TABLE": "t", "LOCAL TEMPORARY": "tmp", "VIEW": "v"}
            rels = [(str(r[0]), duck_types.get(str(r[1]), "?")) for r in rows]
            return _relations(parent, rels, _q(parts[1]) + ".")
        if _is_relation(kind) and len(parts) >= 3:
            rows = _direct(driver, "select column_name, data_type from information_schema.columns where table_catalog = ? and table_schema = ? and table_name = ? order by column_name", [parts[0], parts[1], parts[2]])
            return _columns(parent, rows, "duck")
        return []
    if adapter == "Sqlite":
        if isinstance(kind, CatalogKind_Database) and len(parts) >= 1:
            rows = _direct(driver, f"select type, name from {_q(parts[0])}.sqlite_schema", None)
            rels = [(str(r[1]), "t" if r[0] == "table" else "v") for r in rows if r[0] in ("table", "view")]
            return _relations(parent, rels, _q(parts[0]) + ".")
        if _is_relation(kind) and len(parts) >= 2:
            rows = _direct(driver, f"pragma {_q(parts[0])}.table_info({_lit(parts[1])})", None)
            return _columns(parent, [(r[1], r[2]) for r in rows], "sqlite")
        return []
    if adapter == "Postgres":
        current = _direct(driver, "select current_database()", None)
        if not parts or not current or str(current[0][0]) != parts[0]:
            return []
        if isinstance(kind, CatalogKind_Database):
            rows = _direct(driver, "select nspname from pg_catalog.pg_namespace where nspname not like 'pg\\_%' and nspname <> 'information_schema' order by nspname", None)
            return [_entry(parent, str(r[0]), "sch", CatalogKind_Schema(), parent.qualified_identifier + "." + _q(str(r[0])), _q(str(r[0])), True) for r in rows]
        if isinstance(kind, CatalogKind_Schema) and len(parts) >= 2:
            rows = _direct(driver, "select c.relname, c.relkind, c.relpersistence from pg_catalog.pg_class c join pg_catalog.pg_namespace n on n.oid = c.relnamespace where n.nspname = %s and c.relkind in ('r','p','v','m','f') order by c.relname", [parts[1]])
            rels = []
            for r in rows:
                rk = str(r[1])
                label = "tmp" if str(r[2]) == "t" else {"v": "v", "m": "mv", "f": "f"}.get(rk, "t")
                rels.append((str(r[0]), label))
            return _relations(parent, rels, _q(parts[1]) + ".")
        if _is_relation(kind) and len(parts) >= 3:
            rows = _direct(driver, "select a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod) from pg_catalog.pg_attribute a join pg_catalog.pg_class c on c.oid = a.attrelid join pg_catalog.pg_namespace n on n.oid = c.relnamespace where n.nspname = %s and c.relname = %s and a.attnum > 0 and not a.attisdropped order by a.attnum", [parts[1], parts[2]])
            return _columns(parent, rows, "generic")
        return []
    if adapter == "MySql":
        if isinstance(kind, CatalogKind_Database) and parts:
            rows = _cursor(driver, "select table_name, table_type from information_schema.tables where table_schema = %s order by table_name", [parts[0]])
            rels = [(str(r[0]), "v" if str(r[1]) == "VIEW" else "t") for r in rows]
            return _relations(parent, rels, _q(parts[0]) + ".")
        if _is_relation(kind) and len(parts) >= 2:
            rows = _cursor(driver, "select column_name, data_type from information_schema.columns where table_schema = %s and table_name = %s order by ordinal_position", [parts[0], parts[1]])
            return _columns(parent, rows, "generic")
        return []
    if adapter == "Odbc":
        if isinstance(kind, CatalogKind_Schema) and parts:
            cursor: Any = driver.cursor()
            try:
                if len(parts) >= 2:
                    rows = _to_rows(cast(object, cursor.tables(catalog=parts[-2], schema=parts[-1]).fetchall()))
                else:
                    rows = _to_rows(cast(object, cursor.tables(schema=parts[-1]).fetchall()))
            finally:
                cursor.close()
            odbc_types = {"TABLE": "t", "VIEW": "v", "SYSTEM TABLE": "st", "GLOBAL TEMPORARY": "tmp", "LOCAL TEMPORARY": "tmp"}
            rels = [(str(r[2]), odbc_types.get(str(r[3]).upper(), "t")) for r in rows]
            return _relations(parent, rels, _q(parts[-1]) + ".")
        if _is_relation(kind) and len(parts) >= 2:
            cursor2: Any = driver.cursor()
            try:
                if len(parts) >= 3:
                    rows = _to_rows(cast(object, cursor2.columns(table=parts[-1], catalog=parts[-3], schema=parts[-2]).fetchall()))
                else:
                    rows = _to_rows(cast(object, cursor2.columns(table=parts[-1], schema=parts[-2]).fetchall()))
            finally:
                cursor2.close()
            return _columns(parent, [(r[3], r[5]) for r in rows], "raw")
        return []
    if adapter == "Trino":
        if isinstance(kind, CatalogKind_Database) and parts:
            rows = _cursor(driver, f"select schema_name from {_q(parts[0])}.information_schema.schemata where schema_name <> 'information_schema' order by schema_name", None)
            configured = ""
            session_schema = cast(object, driver.schema)
            if isinstance(session_schema, str):
                configured = session_schema
            names = [str(r[0]) for r in rows if configured == "" or str(r[0]) == configured]
            return [_entry(parent, n, "s", CatalogKind_Schema(), parent.qualified_identifier + "." + _q(n), _q(parts[0]) + "." + _q(n), True) for n in names]
        if isinstance(kind, CatalogKind_Schema) and len(parts) >= 2:
            rows = _cursor(driver, f"select table_name, table_type from {_q(parts[0])}.information_schema.tables where table_schema = {_lit(parts[1])} order by table_name", None)
            rels = [(str(r[0]), "t" if str(r[1]).endswith("TABLE") else "v") for r in rows]
            return _relations(parent, rels, _q(parts[0]) + "." + _q(parts[1]) + ".")
        if _is_relation(kind) and len(parts) >= 3:
            rows = _cursor(driver, f"select column_name, data_type from {_q(parts[0])}.information_schema.columns where table_schema = {_lit(parts[1])} and table_name = {_lit(parts[2])} order by ordinal_position", None)
            return _columns(parent, rows, "generic")
        return []
    if adapter == "Chdb":
        if isinstance(kind, CatalogKind_Database) and parts:
            rows = _cursor(driver, f"select name, engine from system.tables where database = {_lit(parts[0])} order by name", None)
            engines = {"View": "v", "MaterializedView": "mv", "Dictionary": "dic"}
            rels = [(str(r[0]), engines.get(str(r[1]), "t")) for r in rows]
            return _relations(parent, rels, _q(parts[0]) + ".")
        if _is_relation(kind) and len(parts) >= 2:
            rows = _cursor(driver, f"select name, type from system.columns where database = {_lit(parts[0])} and table = {_lit(parts[1])} order by position", None)
            return _columns(parent, rows, "raw")
        return []
    return []


def _valid_payload(payload: dict[str, object]) -> bool:
    if set(payload.keys()) != set(_KEYS.split(",")):
        return False
    adapter = payload["adapter"]
    if not isinstance(adapter, str) or adapter not in _ADAPTERS.split(","):
        return False
    if payload["driver"] is None:
        return False
    if not isinstance(payload["request"], ConnectionRequest):
        return False
    if not isinstance(payload["cleanup"], contextlib.ExitStack):
        return False
    if not isinstance(payload["lock"], type(threading.RLock())):
        return False
    if not isinstance(payload["closed"], bool):
        return False
    mode = payload["transaction_mode"]
    if mode is not None and not isinstance(mode, str):
        return False
    modes = payload["modes"]
    if not isinstance(modes, list):
        return False
    for item in cast(list[object], modes):
        if not isinstance(item, str):
            return False
    if isinstance(mode, str) and mode not in cast(list[object], modes):
        return False
    return isinstance(payload["active"], list)


def load_catalog_children(connection: Connection, parent: CatalogEntry) -> Result[CottList[CatalogEntry], QueryError]:
    handle = connection.session
    if handle.tag != _TAG:
        return _fail("The connection handle is not a Harlequin session.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail("The connection handle is malformed.")
    payload = cast(dict[str, object], raw)
    if not _valid_payload(payload):
        return _fail("The connection handle is malformed.")
    adapter = payload["adapter"]
    if not isinstance(adapter, str):
        return _fail("The connection handle is malformed.")
    lock: Any = payload["lock"]
    with lock:
        if payload["closed"] is True:
            return _fail("The connection is closed.")
        driver: Any = payload["driver"]
        try:
            children = _load(adapter, driver, parent)
        except Exception as error:
            return _fail(str(error))
    return Ok(value=CottList(values=children))
