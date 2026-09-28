import contextlib
import dataclasses
import threading
from typing import Any, Final, LiteralString, cast

from cott_runtime import CottContractViolation, CottList, Err, Ok, Result, Some, _cott_fixture_database
from real.harlequin.adapters_types import (
    AdapterKind,
    AdapterKind_Adbc,
    AdapterKind_BigQuery,
    AdapterKind_Cassandra,
    AdapterKind_Databricks,
    AdapterKind_DuckDb,
    AdapterKind_MySql,
    AdapterKind_NebulaGraph,
    AdapterKind_Odbc,
    AdapterKind_Postgres,
    AdapterKind_Sqlite,
    AdapterKind_Trino,
    Connection,
    ConnectionRequest,
    QueryError,
    QueryError_Failed,
    SettingValue_Text,
)
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


def _fail(message: str) -> Err[QueryError]:
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


def _valid_payload(payload: dict[str, object], connection: Connection) -> bool:
    if len(payload) != 9:
        return False
    for key in ("adapter", "driver", "request", "cleanup", "lock", "closed", "transaction_mode", "modes", "active"):
        if key not in payload:
            return False
    request = payload["request"]
    adapter = payload["adapter"]
    if not isinstance(request, ConnectionRequest) or not isinstance(adapter, str):
        return False
    if request.adapter != connection.adapter or request.read_only != connection.read_only or adapter != _adapter_name(request.adapter):
        return False
    if payload["driver"] is None or not isinstance(payload["cleanup"], contextlib.ExitStack):
        return False
    if not isinstance(payload["lock"], type(threading.RLock())) or not isinstance(payload["closed"], bool):
        return False
    mode = payload["transaction_mode"]
    modes = payload["modes"]
    if mode is not None and not isinstance(mode, str):
        return False
    if not isinstance(modes, list):
        return False
    for label in cast(list[object], modes):
        if not isinstance(label, str):
            return False
    if isinstance(mode, str) and mode not in cast(list[object], modes):
        return False
    return isinstance(payload["active"], list)


def _quote(name: str, mark: str) -> str:
    return mark + name.replace(mark, mark + mark) + mark


def _literal(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def _parts(identifier: str) -> list[str]:
    parts: list[str] = []
    index = 0
    length = len(identifier)
    while index < length:
        if identifier[index] in ('"', "`"):
            mark = identifier[index]
            index += 1
            chars: list[str] = []
            closed = False
            while index < length:
                if identifier[index] == mark:
                    if index + 1 < length and identifier[index + 1] == mark:
                        chars.append(mark)
                        index += 2
                        continue
                    index += 1
                    closed = True
                    break
                chars.append(identifier[index])
                index += 1
            if not closed or (index < length and identifier[index] != "."):
                return []
            parts.append("".join(chars))
        else:
            end = identifier.find(".", index)
            if end < 0:
                end = length
            if end == index:
                return []
            parts.append(identifier[index:end])
            index = end
        if index < length:
            index += 1
            if index == length:
                return []
    return parts


def _rows(raw: object) -> list[object]:
    if not isinstance(raw, list):
        raise TypeError("The database returned invalid catalog rows.")
    return cast(list[object], raw)


def _field(row: object, index: int) -> object:
    record: Any = row
    return cast(object, record[index])


def _text(value: object) -> str:
    return value if isinstance(value, str) else str(value)


def _duck_rows(driver: Any, sql: str, params: list[str]) -> list[object]:
    relation: Any = driver.execute(sql, params)
    return _rows(cast(object, relation.fetchall()))


def _sqlite_rows(driver: Any, sql: str) -> list[object]:
    cursor: Any = driver.execute(sql)
    try:
        return _rows(cast(object, cursor.fetchall()))
    finally:
        cursor.close()


def _cursor_rows(driver: Any, sql: str, params: list[str] | None) -> list[object]:
    cursor: Any = driver.cursor()
    try:
        if params is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, params)
        return _rows(cast(object, cursor.fetchall()))
    finally:
        cursor.close()


def _postgres_rows(driver: Any, sql: LiteralString, params: tuple[str, ...] | None) -> list[object]:
    cursor: Any = driver.cursor()
    try:
        if params is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, params)
        return _rows(cast(object, cursor.fetchall()))
    finally:
        cursor.close()


def _duck_label(data_type: str) -> str:
    name = data_type.strip().upper()
    if name.endswith("[]"):
        return "[" + _duck_label(name[:-2]) + "]"
    if name.startswith("TIMESTAMP WITH TIME ZONE"):
        return "ttz"
    base = name.split("(", 1)[0].split("[", 1)[0].strip()
    match base:
        case "SQLNULL":
            return "\\n"
        case "BOOLEAN":
            return "t/f"
        case "TINYINT" | "SMALLINT" | "INTEGER":
            return "#"
        case "UTINYINT" | "USMALLINT" | "UINTEGER":
            return "u#"
        case "BIGINT":
            return "##"
        case "UBIGINT":
            return "u##"
        case "HUGEINT":
            return "###"
        case "UUID":
            return "uid"
        case "FLOAT" | "DOUBLE" | "DECIMAL" | "REAL":
            return "#.#"
        case "DATE":
            return "d"
        case "TIMESTAMP_TZ" | "TIME_TZ" | "TIME WITH TIME ZONE":
            return "ttz"
        case "TIME":
            return "t"
        case "VARCHAR":
            return "s"
        case "BLOB":
            return "0b"
        case "BIT":
            return "010"
        case "INTERVAL":
            return "|-|"
        case "STRUCT":
            return "{}"
        case "MAP":
            return "{m}"
        case _:
            return "ts" if base.startswith("TIMESTAMP") else "?"


def _sqlite_label(declared: str) -> str:
    name = declared.strip().upper()
    if name == "TEXT":
        return "s"
    if name == "INTEGER":
        return "##"
    if name in ("REAL", "NUMERIC"):
        return "#.#"
    if name == "BLOB":
        return "b"
    return "" if name == "" else "?"


def _generic_label(type_name: str) -> str:
    name = type_name.strip().lower()
    base = name.split("(", 1)[0].split("[", 1)[0].strip()
    if name.startswith(("bool", "bit")):
        return "t/f"
    if name.startswith(("timestamp", "datetime")):
        return "ts"
    if name.startswith("date"):
        return "d"
    if any(part in name for part in ("float", "double", "decimal", "numeric", "real", "money")):
        return "#.#"
    if base in ("tinyint", "smallint", "integer", "int", "bigint", "mediumint", "int2", "int4", "int8", "serial", "bigserial", "smallserial"):
        return "#"
    if any(part in name for part in ("char", "text", "string", "uuid", "json", "enum")):
        return "s"
    if any(part in name for part in ("binary", "blob", "bytea", "bytes")):
        return "0b"
    return "?"


def _relation_kind(label: str) -> CatalogKind:
    if label in ("v", "mv"):
        return CatalogKind_View()
    if label == "tmp":
        return CatalogKind_TemporaryTable()
    if label in ("?", "dic"):
        return CatalogKind_Other()
    return CatalogKind_Table()


def _is_relation(parent: CatalogEntry) -> bool:
    if isinstance(parent.kind, (CatalogKind_Table, CatalogKind_View, CatalogKind_TemporaryTable)):
        return True
    return isinstance(parent.kind, CatalogKind_Other) and parent.type_label in ("?", "dic", "f", "st")


def _entry(parent: CatalogEntry, name: str, label: str, kind: CatalogKind, qualified: str, query_name: str, expandable: bool) -> CatalogEntry:
    return CatalogEntry(
        id=qualified,
        parent=Some(value=parent.id),
        depth=parent.depth + 1,
        label=name,
        type_label=label,
        kind=kind,
        qualified_identifier=qualified,
        query_name=query_name,
        expandable=expandable,
        loaded=not expandable,
    )


def _ordered(entries: list[CatalogEntry], alphabetic: bool) -> list[CatalogEntry]:
    if alphabetic:
        entries.sort(key=lambda entry: (entry.label.casefold(), entry.label))
    return entries


def _columns(parent: CatalogEntry, rows: list[object], name_index: int, type_index: int, mapping: str, mark: str, alphabetic: bool) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    for row in rows:
        name = _text(_field(row, name_index))
        raw_type = _field(row, type_index)
        type_name = "" if raw_type is None else _text(raw_type)
        if mapping == "duck":
            label = _duck_label(type_name)
        elif mapping == "sqlite":
            label = _sqlite_label(type_name)
        elif mapping == "raw":
            label = type_name
        else:
            label = _generic_label(type_name)
        quoted = _quote(name, mark)
        entries.append(_entry(parent, name, label, CatalogKind_Column(), parent.qualified_identifier + "." + quoted, quoted, False))
    return _ordered(entries, alphabetic)


def _relations(parent: CatalogEntry, relations: list[tuple[str, str]], prefix: str, mark: str, alphabetic: bool) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    for name, label in relations:
        quoted = _quote(name, mark)
        entries.append(_entry(parent, name, label, _relation_kind(label), parent.qualified_identifier + "." + quoted, prefix + quoted, True))
    return _ordered(entries, alphabetic)


def _schemas(parent: CatalogEntry, names: list[str], prefix: str, type_label: str) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    for name in names:
        quoted = _quote(name, '"')
        entries.append(_entry(parent, name, type_label, CatalogKind_Schema(), parent.qualified_identifier + "." + quoted, prefix + quoted, True))
    return _ordered(entries, True)


def _configured_schema(request: ConnectionRequest) -> str | None:
    configured: str | None = None
    for setting in request.settings:
        if setting.name == "schema" and isinstance(setting.value, SettingValue_Text):
            configured = setting.value.value
    return configured


def _postgres_relations(driver: Any, schema: CatalogEntry) -> list[CatalogEntry]:
    rows = _postgres_rows(driver, "select c.relname, c.relkind, c.relpersistence from pg_catalog.pg_class c join pg_catalog.pg_namespace n on n.oid = c.relnamespace where n.nspname = %s and c.relkind in ('r','p','v','m','f') order by c.relname", (schema.label,))
    relations: list[tuple[str, str]] = []
    for row in rows:
        relkind = _text(_field(row, 1))
        persistence = _text(_field(row, 2))
        if persistence == "t":
            label = "tmp"
        elif relkind == "v":
            label = "v"
        elif relkind == "m":
            label = "mv"
        elif relkind == "f":
            label = "f"
        else:
            label = "t"
        relations.append((_text(_field(row, 0)), label))
    return _relations(schema, relations, _quote(schema.label, '"') + ".", '"', True)


def _load(adapter: str, driver: Any, request: ConnectionRequest, parent: CatalogEntry) -> list[CatalogEntry]:
    if adapter in ("BigQuery", "Databricks", "Adbc", "Cassandra", "NebulaGraph"):
        return []
    parts = _parts(parent.qualified_identifier)
    kind = parent.kind
    if adapter == "DuckDb":
        if isinstance(kind, CatalogKind_Schema) and len(parts) >= 2:
            rows = _duck_rows(driver, "select table_name, table_type from information_schema.tables where table_catalog = ? and table_schema = ? order by table_name", [parts[0], parts[1]])
            relations: list[tuple[str, str]] = []
            for row in rows:
                table_type = _text(_field(row, 1))
                if table_type == "BASE TABLE":
                    label = "t"
                elif table_type == "LOCAL TEMPORARY":
                    label = "tmp"
                elif table_type == "VIEW":
                    label = "v"
                else:
                    label = "?"
                relations.append((_text(_field(row, 0)), label))
            return _relations(parent, relations, _quote(parts[1], '"') + ".", '"', False)
        if _is_relation(parent) and len(parts) >= 3:
            rows = _duck_rows(driver, "select column_name, data_type from information_schema.columns where table_catalog = ? and table_schema = ? and table_name = ? order by column_name", [parts[0], parts[1], parts[2]])
            return _columns(parent, rows, 0, 1, "duck", '"', False)
        return []
    if adapter == "Sqlite":
        if isinstance(kind, CatalogKind_Database) and parts:
            rows = _sqlite_rows(driver, "select type, name from " + _quote(parts[0], '"') + ".sqlite_schema")
            relations = []
            for row in rows:
                table_type = _field(row, 0)
                if table_type in ("table", "view"):
                    relations.append((_text(_field(row, 1)), "t" if table_type == "table" else "v"))
            return _relations(parent, relations, _quote(parts[0], '"') + ".", '"', True)
        if _is_relation(parent) and len(parts) >= 2:
            rows = _sqlite_rows(driver, "pragma " + _quote(parts[0], '"') + ".table_info(" + _literal(parts[1]) + ")")
            return _columns(parent, rows, 1, 2, "sqlite", '"', True)
        return []
    if adapter == "Postgres":
        if not parts or not (isinstance(kind, (CatalogKind_Database, CatalogKind_Schema)) or _is_relation(parent)):
            return []
        current = _postgres_rows(driver, "select current_database()", None)
        if not current or _text(_field(current[0], 0)) != parts[0]:
            return []
        if isinstance(kind, CatalogKind_Database):
            rows = _postgres_rows(driver, "select nspname from pg_catalog.pg_namespace where nspname not like 'pg\\_%' and nspname <> 'information_schema' order by nspname", None)
            schemas = _schemas(parent, [_text(_field(row, 0)) for row in rows], "", "sch")
            search_path_rows = _postgres_rows(driver, "select unnest(current_schemas(false))", None)
            search_path = {_text(_field(row, 0)) for row in search_path_rows}
            children: list[CatalogEntry] = []
            for schema in schemas:
                if schema.label in search_path:
                    children.append(dataclasses.replace(schema, loaded=True))
                    children.extend(_postgres_relations(driver, schema))
                else:
                    children.append(schema)
            return children
        if isinstance(kind, CatalogKind_Schema) and len(parts) >= 2:
            return _postgres_relations(driver, parent)
        if _is_relation(parent) and len(parts) >= 3:
            rows = _postgres_rows(driver, "select a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod) from pg_catalog.pg_attribute a join pg_catalog.pg_class c on c.oid = a.attrelid join pg_catalog.pg_namespace n on n.oid = c.relnamespace where n.nspname = %s and c.relname = %s and a.attnum > 0 and not a.attisdropped order by a.attnum", (parts[1], parts[2]))
            return _columns(parent, rows, 0, 1, "generic", '"', True)
        return []
    if adapter == "MySql":
        if isinstance(kind, CatalogKind_Database) and parts:
            rows = _cursor_rows(driver, "select table_name, table_type from information_schema.tables where table_schema = %s order by table_name", [parts[0]])
            relations = [(_text(_field(row, 0)), "v" if _field(row, 1) == "VIEW" else "t") for row in rows]
            return _relations(parent, relations, _quote(parts[0], "`") + ".", "`", True)
        if _is_relation(parent) and len(parts) >= 2:
            rows = _cursor_rows(driver, "select column_name, data_type from information_schema.columns where table_schema = %s and table_name = %s order by ordinal_position", [parts[0], parts[1]])
            return _columns(parent, rows, 0, 1, "generic", "`", True)
        return []
    if adapter == "Odbc":
        if isinstance(kind, CatalogKind_Schema) and parts:
            cursor: Any = driver.cursor()
            try:
                if len(parts) >= 2:
                    rows = _rows(cast(object, cursor.tables(catalog=parts[-2], schema=parts[-1]).fetchall()))
                else:
                    rows = _rows(cast(object, cursor.tables(schema=parts[-1]).fetchall()))
            finally:
                cursor.close()
            relations = []
            for row in rows:
                table_type = _text(_field(row, 3)).upper()
                if table_type == "VIEW":
                    label = "v"
                elif table_type == "SYSTEM TABLE":
                    label = "st"
                elif table_type in ("GLOBAL TEMPORARY", "LOCAL TEMPORARY"):
                    label = "tmp"
                else:
                    label = "t"
                relations.append((_text(_field(row, 2)), label))
            return _relations(parent, relations, _quote(parts[-1], '"') + ".", '"', False)
        if _is_relation(parent) and len(parts) >= 2:
            cursor = driver.cursor()
            try:
                if len(parts) >= 3:
                    rows = _rows(cast(object, cursor.columns(table=parts[-1], catalog=parts[-3], schema=parts[-2]).fetchall()))
                else:
                    rows = _rows(cast(object, cursor.columns(table=parts[-1], schema=parts[-2]).fetchall()))
            finally:
                cursor.close()
            return _columns(parent, rows, 3, 5, "raw", '"', False)
        return []
    if adapter == "Trino":
        if (isinstance(kind, CatalogKind_Database) or (isinstance(kind, CatalogKind_Other) and parent.type_label == "c")) and parts:
            rows = _cursor_rows(driver, "select schema_name from " + _quote(parts[0], '"') + ".information_schema.schemata where schema_name <> 'information_schema' order by schema_name", None)
            configured = _configured_schema(request)
            names = [_text(_field(row, 0)) for row in rows]
            return _schemas(parent, [name for name in names if configured is None or name == configured], _quote(parts[0], '"') + ".", "s")
        if isinstance(kind, CatalogKind_Schema) and len(parts) >= 2:
            rows = _cursor_rows(driver, "select table_name, table_type from " + _quote(parts[0], '"') + ".information_schema.tables where table_schema = " + _literal(parts[1]) + " order by table_name", None)
            relations = [(_text(_field(row, 0)), "t" if _text(_field(row, 1)).endswith("TABLE") else "v") for row in rows]
            return _relations(parent, relations, _quote(parts[0], '"') + "." + _quote(parts[1], '"') + ".", '"', True)
        if _is_relation(parent) and len(parts) >= 3:
            rows = _cursor_rows(driver, "select column_name, data_type from " + _quote(parts[0], '"') + ".information_schema.columns where table_schema = " + _literal(parts[1]) + " and table_name = " + _literal(parts[2]) + " order by ordinal_position", None)
            return _columns(parent, rows, 0, 1, "generic", '"', True)
        return []
    if adapter == "Chdb":
        if isinstance(kind, CatalogKind_Database) and parts:
            rows = _cursor_rows(driver, f"select name, engine from system.tables where database = {_literal(parts[0])} order by name", None)
            relations = []
            for row in rows:
                engine = _text(_field(row, 1))
                if engine == "View":
                    label = "v"
                elif engine == "MaterializedView":
                    label = "mv"
                elif engine == "Dictionary":
                    label = "dic"
                else:
                    label = "t"
                relations.append((_text(_field(row, 0)), label))
            return _relations(parent, relations, _quote(parts[0], "`") + ".", "`", True)
        if _is_relation(parent) and len(parts) >= 2:
            rows = _cursor_rows(driver, f"select name, type from system.columns where database = {_literal(parts[0])} and table = {_literal(parts[1])} order by position", None)
            return _columns(parent, rows, 0, 1, "raw", "`", False)
    return []


def load_catalog_children(connection: Connection, parent: CatalogEntry) -> Result[CottList[CatalogEntry], QueryError]:
    handle = connection.session
    if handle.tag != _TAG:
        return _fail("The connection handle is not a Harlequin session.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail("The connection handle is malformed.")
    payload = cast(dict[str, object], raw)
    if not _valid_payload(payload, connection):
        return _fail("The connection handle is malformed.")
    lock: Any = payload["lock"]
    with lock:
        if payload["closed"] is True:
            return _fail("The connection is closed.")
        adapter = payload["adapter"]
        request = payload["request"]
        if not isinstance(adapter, str) or not isinstance(request, ConnectionRequest):
            return _fail("The connection handle is malformed.")
        driver: Any = payload["driver"]
        try:
            try:
                _cott_fixture_database("read")
            except CottContractViolation as violation:
                if violation.message != "fixture adapters are inactive":
                    cause = violation.__cause__
                    if isinstance(cause, OSError):
                        raise cause
                    raise
            children = _load(adapter, driver, request, parent)
        except (Exception, KeyboardInterrupt) as error:
            return _fail(str(error))
    return Ok(value=CottList(values=children))
