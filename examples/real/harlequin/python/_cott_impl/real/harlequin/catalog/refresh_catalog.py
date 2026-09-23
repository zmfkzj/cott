import contextlib
import json
import os
import sqlite3
import threading
import urllib.parse
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Final, Literal, LiteralString, cast

import adbc_driver_manager.dbapi
import duckdb
import psycopg
import pymysql
import pymysql.connections
import pymysql.cursors
import pyodbc
import trino.dbapi
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.cluster import Session as CassandraSession
from cassandra.connection import DefaultEndPoint
from cassandra.metadata import KeyspaceMetadata, Metadata
from databricks import sql as databricks_sql
from databricks.sql.client import Connection as DatabricksConnection
from google.api_core.exceptions import NotFound
from google.cloud import bigquery
from google.cloud.bigquery.table import TableListItem
from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool, Session
from psycopg.rows import TupleRow
from trino.auth import BasicAuthentication

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some
from real.harlequin.catalog_types import CatalogError, CatalogError_ConnectionMissing, CatalogError_Failed, CatalogError_LimitExceeded, CatalogError_NamespaceMissing, CatalogRelation, CatalogScope, CatalogSnapshot, RelationKind_Table, RelationKind_View
from real.harlequin.core_types import AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_Odbc, AdapterKind_PostgreSql, AdapterKind_Sqlite, AdapterKind_Trino, Connection

_LIMIT: Final[int] = 100000
_PROBE: Final[int] = 100001
_TABLE: Final[int] = 0
_VIEW: Final[int] = 1
_SESSION_TAG: Final[str] = "harlequin.session"


def _check(value: object, expected: type) -> bool:
    if expected is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, expected)


def _parse_obj(data: object, required: dict[str, type], optional: dict[str, type]) -> dict[str, object]:
    if not isinstance(data, dict):
        raise ValueError("endpoint")
    raw = cast(dict[object, object], data)
    result: dict[str, object] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            raise ValueError("endpoint")
        expected = required.get(key, optional.get(key))
        if expected is None or not _check(value, expected):
            raise ValueError("endpoint")
        result[key] = value
    for key in required:
        if key not in result:
            raise ValueError("endpoint")
    return result


def _parse_json(text: str, required: dict[str, type], optional: dict[str, type]) -> dict[str, object]:
    return _parse_obj(cast(object, json.loads(text)), required, optional)


def _req_str(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError("endpoint")
    return value


def _opt_str(data: dict[str, object], key: str) -> str | None:
    value = data.get(key)
    return value if isinstance(value, str) else None


def _port(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0 or value > 65535:
        raise ValueError("endpoint")
    return value


def _addresses(value: object) -> list[tuple[str, int]]:
    if not isinstance(value, list):
        raise ValueError("endpoint")
    items = cast(list[object], value)
    if len(items) == 0:
        raise ValueError("endpoint")
    result: list[tuple[str, int]] = []
    for item in items:
        entry = _parse_obj(item, {"host": str, "port": int}, {})
        host = _req_str(entry, "host")
        if host == "":
            raise ValueError("endpoint")
        result.append((host, _port(entry["port"])))
    return result


def _str_map(value: object) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("endpoint")
    raw = cast(dict[object, object], value)
    result: dict[str, str] = {}
    for key, item in raw.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise ValueError("endpoint")
        result[key] = item
    return result


def _text(value: object) -> str:
    return "" if value is None else str(value)


def _column(description: object, name: str) -> int:
    if not isinstance(description, (list, tuple)):
        raise ValueError("metadata")
    columns = cast(list[object], description)
    for index, column in enumerate(columns):
        if not isinstance(column, (list, tuple)):
            raise ValueError("metadata")
        parts = cast(list[object], column)
        if len(parts) > 0 and _text(parts[0]).lower() == name.lower():
            return index
    raise ValueError("metadata")


def _row(value: object) -> tuple[object, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(cast(list[object], value))
    if isinstance(value, pyodbc.Row):
        return tuple(cast(list[object], list(value)))
    raise ValueError("metadata")


def _rows(value: object) -> list[tuple[object, ...]]:
    if not isinstance(value, (list, tuple)):
        raise ValueError("metadata")
    return [_row(item) for item in cast(list[object], value)]


def _driver_matches(connection: Connection, driver: object) -> bool:
    adapter = connection.adapter
    if isinstance(adapter, AdapterKind_Sqlite):
        return isinstance(driver, sqlite3.Connection)
    if isinstance(adapter, AdapterKind_DuckDb):
        return isinstance(driver, duckdb.DuckDBPyConnection)
    if isinstance(adapter, AdapterKind_PostgreSql):
        return isinstance(driver, psycopg.Connection)
    if isinstance(adapter, AdapterKind_MySql):
        return isinstance(driver, pymysql.connections.Connection)
    if isinstance(adapter, AdapterKind_Odbc):
        return isinstance(driver, pyodbc.Connection)
    if isinstance(adapter, AdapterKind_BigQuery):
        return isinstance(driver, bigquery.Client)
    if isinstance(adapter, AdapterKind_Trino):
        return isinstance(driver, trino.dbapi.Connection)
    if isinstance(adapter, AdapterKind_Databricks):
        return isinstance(driver, DatabricksConnection)
    if isinstance(adapter, AdapterKind_Adbc):
        return isinstance(driver, adbc_driver_manager.dbapi.Connection)
    if isinstance(adapter, AdapterKind_Cassandra):
        return isinstance(driver, CassandraSession)
    return isinstance(driver, Session)


def _session_payload(connection: Connection) -> dict[str, object] | None:
    handle = connection.session
    if handle.tag != _SESSION_TAG:
        return None
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return None
    data = cast(dict[str, object], raw)
    if set(data.keys()) != {"id", "adapter", "endpoint", "read_only", "driver", "cleanup", "lock", "closed", "transaction"}:
        return None
    read_only = data["read_only"]
    if data["id"] != connection.id or data["adapter"] != connection.adapter or data["endpoint"] != connection.endpoint:
        return None
    if not isinstance(read_only, bool) or read_only != connection.read_only:
        return None
    if not isinstance(data["cleanup"], contextlib.ExitStack) or not isinstance(data["lock"], threading.Lock):
        return None
    return data


def _sqlite(endpoint: str, namespace: str | None) -> list[tuple[str, int, str | None]] | CatalogError:
    if endpoint == "":
        raise ValueError("endpoint")
    if endpoint == ":memory:":
        conn = sqlite3.connect(":memory:")
    elif endpoint.startswith("file:"):
        base, _, query = endpoint.partition("#")[0].partition("?")
        params = [p for p in query.split("&") if p != "" and not p.startswith("mode=")]
        params.append("mode=ro")
        conn = sqlite3.connect(base + "?" + "&".join(params), uri=True)
    else:
        uri = "file:" + urllib.parse.quote(os.path.abspath(endpoint)) + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
    try:
        cur = conn.cursor()
        try:
            cur.execute("PRAGMA query_only = ON")
            cur.execute("PRAGMA database_list")
            names = {_text(r[1]) for r in _rows(cur.fetchall())}
            schema = "main" if namespace is None else namespace
            if schema not in names:
                if namespace is not None:
                    return CatalogError_NamespaceMissing(namespace=namespace)
                raise ValueError("default")
            quoted = '"' + schema.replace('"', '""') + '"'
            cur.execute("SELECT name, type, sql FROM " + quoted + ".sqlite_schema WHERE type IN ('table', 'view') AND substr(name, 1, 7) <> 'sqlite_' LIMIT ?", (_PROBE,))
            return [(_text(r[0]), _TABLE if r[1] == "table" else _VIEW, None if r[2] is None else str(r[2])) for r in _rows(cur.fetchall())]
        finally:
            cur.close()
    finally:
        conn.close()


def _duckdb(endpoint: str, namespace: str | None) -> list[tuple[str, int, str | None]] | CatalogError:
    if endpoint == ":memory:":
        conn = duckdb.connect(":memory:")
    else:
        if endpoint == "" or not os.path.isfile(endpoint):
            raise ValueError("endpoint")
        conn = duckdb.connect(endpoint, read_only=True)
    try:
        row = conn.execute("SELECT current_database()").fetchone()
        if row is None or row[0] is None:
            raise ValueError("default")
        database = str(row[0])
        schema = "main" if namespace is None else namespace
        found = conn.execute("SELECT count(*) FROM duckdb_schemas() WHERE database_name = ? AND schema_name = ?", [database, schema]).fetchone()
        if found is None or found[0] == 0:
            if namespace is not None:
                return CatalogError_NamespaceMissing(namespace=namespace)
            raise ValueError("default")
        rows = _rows(
            conn.execute(
                "SELECT * FROM (SELECT table_name, 0, sql FROM duckdb_tables() WHERE database_name = ? AND schema_name = ? AND NOT internal "
                "UNION ALL SELECT view_name, 1, sql FROM duckdb_views() WHERE database_name = ? AND schema_name = ? AND NOT internal) LIMIT ?",
                [database, schema, database, schema, _PROBE],
            ).fetchall()
        )
        return [(_text(r[0]), _TABLE if r[1] == 0 else _VIEW, None if r[2] is None else str(r[2])) for r in rows]
    finally:
        conn.close()


def _information_schema(cur: psycopg.Cursor[TupleRow] | pymysql.cursors.Cursor, default_sql: LiteralString, namespace: str | None, schemata_sql: LiteralString, tables_sql: LiteralString) -> list[tuple[str, int, str | None]] | CatalogError:
    if namespace is None:
        cur.execute(default_sql)
        fetched = cast(object, cur.fetchone())
        if fetched is None:
            raise ValueError("default")
        row = _row(fetched)
        if len(row) == 0 or row[0] is None:
            raise ValueError("default")
        schema = str(row[0])
    else:
        schema = namespace
    cur.execute(schemata_sql, (schema,))
    if not any(_text(r[0]) == schema for r in _rows(cast(object, cur.fetchall()))):
        if namespace is not None:
            return CatalogError_NamespaceMissing(namespace=namespace)
        raise ValueError("default")
    cur.execute(tables_sql, (schema, _PROBE))
    return [(_text(r[0]), _TABLE if _text(r[1]) == "BASE TABLE" else _VIEW, None) for r in _rows(cast(object, cur.fetchall()))]


def _postgres(endpoint: str, namespace: str | None) -> list[tuple[str, int, str | None]] | CatalogError:
    conn = psycopg.connect(endpoint)
    try:
        with conn.cursor() as cur:
            return _information_schema(
                cur,
                "SELECT current_schema()",
                namespace,
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                "SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = %s AND table_type IN ('BASE TABLE', 'VIEW') LIMIT %s",
            )
    finally:
        conn.close()


def _mysql(endpoint: str, namespace: str | None) -> list[tuple[str, int, str | None]] | CatalogError:
    data = _parse_json(
        endpoint,
        {"host": str, "user": str, "database": str},
        {"password": str, "port": int, "unix_socket": str, "ssl_ca": str, "ssl_cert": str, "ssl_key": str, "ssl_verify_cert": bool, "ssl_verify_identity": bool},
    )
    tls = any(k in data for k in ("ssl_ca", "ssl_cert", "ssl_key", "ssl_verify_cert", "ssl_verify_identity"))
    verify_cert = data.get("ssl_verify_cert", True)
    verify_identity = data.get("ssl_verify_identity", True)
    conn = pymysql.connect(
        host=_req_str(data, "host"),
        user=_req_str(data, "user"),
        password=_opt_str(data, "password") or "",
        database=_req_str(data, "database"),
        port=_port(data.get("port", 3306)),
        unix_socket=_opt_str(data, "unix_socket"),
        ssl_ca=_opt_str(data, "ssl_ca"),
        ssl_cert=_opt_str(data, "ssl_cert"),
        ssl_key=_opt_str(data, "ssl_key"),
        ssl_verify_cert=(verify_cert is True) if tls else None,
        ssl_verify_identity=(verify_identity is True) if tls else None,
    )
    try:
        cur = cast(pymysql.cursors.Cursor, conn.cursor())
        try:
            return _information_schema(
                cur,
                "SELECT DATABASE()",
                namespace,
                "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s",
                "SELECT TABLE_NAME, TABLE_TYPE FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_TYPE IN ('BASE TABLE', 'VIEW') LIMIT %s",
            )
        finally:
            cur.close()
    finally:
        conn.close()


def _odbc(endpoint: str, namespace: str | None) -> list[tuple[str, int, str | None]] | CatalogError:
    conn = pyodbc.connect(endpoint, autocommit=True, readonly=True)
    try:
        try:
            database = _text(cast(object, conn.getinfo(pyodbc.SQL_DATABASE_NAME)))
        except pyodbc.Error:
            database = ""
        schema_usage = cast(object, conn.getinfo(pyodbc.SQL_SCHEMA_USAGE))
        cur = conn.cursor()
        try:
            cur.tables(catalog="%", schema="", table="")
            index = _column(cast(object, cur.description), "table_cat")
            catalogs = {_text(r[index]) for r in _rows(cast(object, cur.fetchall()))}
            if len(catalogs) == 0 or catalogs == {""}:
                catalog = ""
            elif database != "":
                if database not in catalogs:
                    raise ValueError("catalog")
                catalog = database
            elif len(catalogs) == 1:
                catalog = next(iter(catalogs))
            else:
                raise ValueError("catalog")
            if schema_usage == 0:
                schemas = {""}
            else:
                cur.tables(catalog="", schema="%", table="")
                cat_index = _column(cast(object, cur.description), "table_cat")
                sch_index = _column(cast(object, cur.description), "table_schem")
                schemas = {_text(r[sch_index]) for r in _rows(cast(object, cur.fetchall())) if _text(r[cat_index]) in ("", catalog)}
            if namespace is not None:
                if namespace not in schemas:
                    return CatalogError_NamespaceMissing(namespace=namespace)
                schema = namespace
            elif len(schemas) == 1:
                schema = next(iter(schemas))
            else:
                raise ValueError("default")
            cur.tables(tableType="TABLE,VIEW")
            cat_index = _column(cast(object, cur.description), "table_cat")
            sch_index = _column(cast(object, cur.description), "table_schem")
            name_index = _column(cast(object, cur.description), "table_name")
            type_index = _column(cast(object, cur.description), "table_type")
            result: list[tuple[str, int, str | None]] = []
            while len(result) < _PROBE:
                fetched = cast(object, cur.fetchone())
                if fetched is None:
                    break
                row = _row(fetched)
                if _text(row[cat_index]) != catalog or _text(row[sch_index]) != schema:
                    continue
                kind = _text(row[type_index]).upper()
                if kind == "TABLE":
                    result.append((_text(row[name_index]), _TABLE, None))
                elif kind == "VIEW":
                    result.append((_text(row[name_index]), _VIEW, None))
            return result
        finally:
            cur.close()
    finally:
        conn.close()


def _adbc_query(conn: adbc_driver_manager.dbapi.Connection, depth: Literal["db_schemas", "tables"], sql: str, params: list[object]) -> list[tuple[object, ...]]:
    with cast(contextlib.AbstractContextManager[object], conn.adbc_get_objects(depth=depth)) as reader:
        bridge = duckdb.connect(":memory:")
        try:
            bridge.from_arrow(reader).create_view("adbc_objects")
            return _rows(bridge.execute(sql, params).fetchall())
        finally:
            bridge.close()


def _adbc(endpoint: str, namespace: str | None) -> list[tuple[str, int, str | None]] | CatalogError:
    data = _parse_json(endpoint, {"driver": str}, {"uri": str, "entrypoint": str, "db": dict, "connection": dict, "catalog": str})
    conn = adbc_driver_manager.dbapi.connect(
        driver=_req_str(data, "driver"),
        uri=_opt_str(data, "uri"),
        entrypoint=_opt_str(data, "entrypoint"),
        db_kwargs=_str_map(data.get("db")),
        conn_kwargs=_str_map(data.get("connection")),
    )
    try:
        pairs = {
            (_text(r[0]), _text(r[1]))
            for r in _adbc_query(
                conn,
                "db_schemas",
                "SELECT coalesce(catalog_name, ''), coalesce(struct_extract(s, 'db_schema_name'), '') FROM (SELECT catalog_name, UNNEST(catalog_db_schemas) AS s FROM adbc_objects)",
                [],
            )
        }
        wanted_catalog = _opt_str(data, "catalog")
        if wanted_catalog is not None:
            pairs = {p for p in pairs if p[0] == wanted_catalog}
            if len(pairs) == 0:
                raise ValueError("catalog")
        if namespace is not None:
            pairs = {p for p in pairs if p[1] == namespace}
            if len(pairs) == 0:
                return CatalogError_NamespaceMissing(namespace=namespace)
        if len(pairs) != 1:
            raise ValueError("ambiguous")
        catalog, schema = next(iter(pairs))
        rows = _adbc_query(
            conn,
            "tables",
            "SELECT name, kind FROM (SELECT coalesce(struct_extract(t, 'table_name'), '') AS name, upper(struct_extract(t, 'table_type')) AS kind FROM ("
            "SELECT UNNEST(struct_extract(s, 'db_schema_tables')) AS t FROM ("
            "SELECT UNNEST(catalog_db_schemas) AS s FROM adbc_objects WHERE coalesce(catalog_name, '') = ?"
            ") WHERE coalesce(struct_extract(s, 'db_schema_name'), '') = ?"
            ")) WHERE kind IN ('TABLE', 'BASE TABLE', 'VIEW') LIMIT ?",
            [catalog, schema, _PROBE],
        )
        return [(_text(r[0]), _VIEW if r[1] == "VIEW" else _TABLE, None) for r in rows]
    finally:
        conn.close()


def _bigquery(endpoint: str, namespace: str | None) -> list[tuple[str, int, str | None]] | CatalogError:
    data = _parse_json(endpoint, {"project": str, "auth": dict}, {"dataset": str, "location": str})
    if _parse_obj(data["auth"], {"type": str}, {}).get("type") != "adc":
        raise ValueError("auth")
    project = _req_str(data, "project")
    dataset = namespace if namespace is not None else _opt_str(data, "dataset")
    if dataset is None:
        raise ValueError("default")
    client = bigquery.Client(project=project, location=_opt_str(data, "location"))
    try:
        reference = bigquery.DatasetReference(project, dataset)
        try:
            client.get_dataset(reference)
        except NotFound:
            if namespace is not None:
                return CatalogError_NamespaceMissing(namespace=namespace)
            raise
        result: list[tuple[str, int, str | None]] = []
        items = cast(Iterable[TableListItem], client.list_tables(reference, max_results=_PROBE))
        for table in items:
            kind = _text(cast(str | None, table.table_type)).upper()
            if kind in ("VIEW", "MATERIALIZED_VIEW"):
                result.append((_text(table.table_id), _VIEW, None))
            elif kind in ("TABLE", "EXTERNAL", "SNAPSHOT", "CLONE"):
                result.append((_text(table.table_id), _TABLE, None))
        return result
    finally:
        client.close()


def _split_namespace(namespace: str | None, catalog: str | None, schema: str | None) -> tuple[str, str] | None:
    if namespace is None:
        if catalog is None or schema is None:
            raise ValueError("default")
        return (catalog, schema)
    parts = namespace.split(".")
    if len(parts) != 2 or parts[0] == "" or parts[1] == "":
        return None
    return (parts[0], parts[1])


def _trino(endpoint: str, namespace: str | None) -> list[tuple[str, int, str | None]] | CatalogError:
    data = _parse_json(endpoint, {"host": str, "user": str}, {"catalog": str, "schema": str, "scheme": str, "port": int, "auth": dict})
    host = _req_str(data, "host")
    user = _req_str(data, "user")
    scheme = _opt_str(data, "scheme") or "https"
    if scheme not in ("https", "http"):
        raise ValueError("scheme")
    port = _port(data.get("port", 443 if scheme == "https" else 80))
    auth: BasicAuthentication | None = None
    if "auth" in data:
        auth_data = _parse_obj(data["auth"], {"type": str, "password": str}, {})
        if auth_data["type"] != "basic" or scheme != "https":
            raise ValueError("auth")
        auth = BasicAuthentication(user, _req_str(auth_data, "password"))
    target = _split_namespace(namespace, _opt_str(data, "catalog"), _opt_str(data, "schema"))
    conn = trino.dbapi.connect(host=host, port=port, user=user, http_scheme=scheme, auth=auth)
    try:
        cur = conn.cursor()
        try:
            cur.execute("SHOW CATALOGS")
            catalogs = {_text(r[0]) for r in _rows(cast(object, cur.fetchall()))}
            if target is None or target[0] not in catalogs:
                if namespace is not None:
                    return CatalogError_NamespaceMissing(namespace=namespace)
                raise ValueError("default")
            quoted = '"' + target[0].replace('"', '""') + '"'
            cur.execute("SHOW SCHEMAS FROM " + quoted)
            if target[1] not in {_text(r[0]) for r in _rows(cast(object, cur.fetchall()))}:
                if namespace is not None:
                    return CatalogError_NamespaceMissing(namespace=namespace)
                raise ValueError("default")
            cur.execute(
                "SELECT table_name, table_type FROM " + quoted + ".information_schema.tables WHERE table_schema = ? AND table_type IN ('BASE TABLE', 'VIEW', 'MATERIALIZED VIEW') LIMIT " + str(_PROBE),
                [target[1]],
            )
            return [(_text(r[0]), _TABLE if _text(r[1]) == "BASE TABLE" else _VIEW, None) for r in _rows(cast(object, cur.fetchall()))]
        finally:
            cur.close()
    finally:
        conn.close()


def _databricks(endpoint: str, namespace: str | None) -> list[tuple[str, int, str | None]] | CatalogError:
    data = _parse_json(endpoint, {"server_hostname": str, "http_path": str, "auth": dict}, {"catalog": str, "schema": str})
    auth_data = _parse_obj(data["auth"], {"type": str, "access_token": str}, {})
    if auth_data["type"] != "pat":
        raise ValueError("auth")
    target = _split_namespace(namespace, _opt_str(data, "catalog"), _opt_str(data, "schema"))
    conn = databricks_sql.connect(server_hostname=_req_str(data, "server_hostname"), http_path=_req_str(data, "http_path"), access_token=_req_str(auth_data, "access_token"))
    try:
        cur = conn.cursor()
        try:
            cur.catalogs()
            index = _column(cast(object, cur.description), "TABLE_CAT")
            catalogs = {_text(r[index]) for r in _rows(cast(object, cur.fetchall()))}
            if target is None or target[0] not in catalogs:
                if namespace is not None:
                    return CatalogError_NamespaceMissing(namespace=namespace)
                raise ValueError("default")
            catalog, schema = target
            cur.schemas(catalog_name=catalog)
            cat_index = _column(cast(object, cur.description), "TABLE_CATALOG")
            sch_index = _column(cast(object, cur.description), "TABLE_SCHEM")
            if not any(_text(r[cat_index]) == catalog and _text(r[sch_index]) == schema for r in _rows(cast(object, cur.fetchall()))):
                if namespace is not None:
                    return CatalogError_NamespaceMissing(namespace=namespace)
                raise ValueError("default")
            cur.tables(catalog_name=catalog, schema_name=schema)
            cat_index = _column(cast(object, cur.description), "TABLE_CAT")
            sch_index = _column(cast(object, cur.description), "TABLE_SCHEM")
            name_index = _column(cast(object, cur.description), "TABLE_NAME")
            type_index = _column(cast(object, cur.description), "TABLE_TYPE")
            views = ("VIEW", "MATERIALIZED_VIEW", "METRIC_VIEW")
            tables = ("TABLE", "BASE TABLE", "MANAGED", "EXTERNAL", "FOREIGN", "STREAMING_TABLE", "MANAGED_SHALLOW_CLONE", "EXTERNAL_SHALLOW_CLONE")
            result: list[tuple[str, int, str | None]] = []
            while len(result) < _PROBE:
                batch = _rows(cast(object, cur.fetchmany(1000)))
                if len(batch) == 0:
                    break
                for row in batch:
                    if _text(row[cat_index]) != catalog or _text(row[sch_index]) != schema:
                        continue
                    kind = _text(row[type_index]).upper()
                    if kind in views:
                        result.append((_text(row[name_index]), _VIEW, None))
                    elif kind in tables:
                        result.append((_text(row[name_index]), _TABLE, None))
                    if len(result) >= _PROBE:
                        break
            return result
        finally:
            cur.close()
    finally:
        conn.close()


def _cassandra(endpoint: str, namespace: str | None) -> list[tuple[str, int, str | None]] | CatalogError:
    data = _parse_json(endpoint, {"contact_points": list}, {"keyspace": str, "auth": dict})
    points = _addresses(data["contact_points"])
    provider: PlainTextAuthProvider | None = None
    if "auth" in data:
        auth_data = _parse_obj(data["auth"], {"type": str, "username": str, "password": str}, {})
        if auth_data["type"] != "plain":
            raise ValueError("auth")
        provider = PlainTextAuthProvider(username=_req_str(auth_data, "username"), password=_req_str(auth_data, "password"))
    keyspace = namespace if namespace is not None else _opt_str(data, "keyspace")
    if keyspace is None:
        raise ValueError("default")
    cluster = Cluster(contact_points=[DefaultEndPoint(host, port) for host, port in points], auth_provider=provider)
    try:
        session = cluster.connect()
        try:
            metadata: Metadata | None = cluster.metadata
            if metadata is None:
                raise ValueError("metadata")
            keyspaces = cast(dict[object, object], metadata.keyspaces)
            found = keyspaces.get(keyspace)
            if found is None:
                if namespace is not None:
                    return CatalogError_NamespaceMissing(namespace=namespace)
                raise ValueError("default")
            if not isinstance(found, KeyspaceMetadata):
                raise ValueError("metadata")
            tables = cast(dict[object, object], found.tables)
            views = cast(dict[object, object], found.views)
            if len(tables) + len(views) > _LIMIT:
                return CatalogError_LimitExceeded(limit=_LIMIT)
            result: list[tuple[str, int, str | None]] = [(_text(name), _TABLE, None) for name in tables]
            result.extend((_text(name), _VIEW, None) for name in views)
            return result
        finally:
            session.shutdown()
    finally:
        cluster.shutdown()


def _nebula_names(session: Session, statement: str) -> list[str]:
    result = session.execute(statement)
    if not result.is_succeeded():
        raise ValueError("metadata")
    rows = cast(object, result.as_primitive())
    if not isinstance(rows, list):
        raise ValueError("metadata")
    names: list[str] = []
    for row in cast(list[object], rows):
        if not isinstance(row, dict):
            raise ValueError("metadata")
        value = cast(dict[object, object], row).get("Name")
        if not isinstance(value, str):
            raise ValueError("metadata")
        name: str = value
        names.append(name)
    return names


def _nebula(endpoint: str, namespace: str | None) -> list[tuple[str, int, str | None]] | CatalogError:
    data = _parse_json(endpoint, {"addresses": list, "username": str, "password": str}, {"space": str})
    addresses = _addresses(data["addresses"])
    username = _req_str(data, "username")
    password = _req_str(data, "password")
    space = namespace if namespace is not None else _opt_str(data, "space")
    if space is None:
        raise ValueError("default")
    pool = ConnectionPool()
    try:
        if not pool.init(addresses, Config()):
            raise ValueError("transport")
        session = pool.get_session(username, password)
        try:
            if space not in _nebula_names(session, "SHOW SPACES"):
                if namespace is not None:
                    return CatalogError_NamespaceMissing(namespace=namespace)
                raise ValueError("default")
            if any(c in "`\\" or ord(c) < 32 or ord(c) == 127 for c in space):
                raise ValueError("name")
            used = session.execute("USE `" + space + "`")
            if not used.is_succeeded():
                raise ValueError("metadata")
            tags = _nebula_names(session, "SHOW TAGS")
            edges = _nebula_names(session, "SHOW EDGES")
            if len(tags) + len(edges) > _LIMIT:
                return CatalogError_LimitExceeded(limit=_LIMIT)
            result: list[tuple[str, int, str | None]] = [("tag:" + name, _TABLE, None) for name in tags]
            result.extend(("edge:" + name, _TABLE, None) for name in edges)
            return result
        finally:
            session.release()
    finally:
        pool.close()


def _refresh(connection: Connection, namespace: str | None) -> list[tuple[str, int, str | None]] | CatalogError:
    adapter = connection.adapter
    endpoint = connection.endpoint
    label = "catalog"
    try:
        if isinstance(adapter, AdapterKind_Sqlite):
            label = "sqlite"
            return _sqlite(endpoint, namespace)
        if isinstance(adapter, AdapterKind_DuckDb):
            label = "duckdb"
            return _duckdb(endpoint, namespace)
        if isinstance(adapter, AdapterKind_PostgreSql):
            label = "postgresql"
            return _postgres(endpoint, namespace)
        if isinstance(adapter, AdapterKind_MySql):
            label = "mysql"
            return _mysql(endpoint, namespace)
        if isinstance(adapter, AdapterKind_Odbc):
            label = "odbc"
            return _odbc(endpoint, namespace)
        if isinstance(adapter, AdapterKind_BigQuery):
            label = "bigquery"
            return _bigquery(endpoint, namespace)
        if isinstance(adapter, AdapterKind_Trino):
            label = "trino"
            return _trino(endpoint, namespace)
        if isinstance(adapter, AdapterKind_Databricks):
            label = "databricks"
            return _databricks(endpoint, namespace)
        if isinstance(adapter, AdapterKind_Adbc):
            label = "adbc"
            return _adbc(endpoint, namespace)
        if isinstance(adapter, AdapterKind_Cassandra):
            label = "cassandra"
            return _cassandra(endpoint, namespace)
        label = "nebulagraph"
        return _nebula(endpoint, namespace)
    except ImportError:
        return CatalogError_Failed(message=label + " driver unavailable")
    except Exception:
        return CatalogError_Failed(message=label + " catalog refresh failed")


def refresh_catalog(connection: Connection, scope: CatalogScope) -> Result[CatalogSnapshot, CatalogError]:
    if connection.id == "" or scope.connection_id != connection.id:
        return Err(error=CatalogError_ConnectionMissing(connection_id=scope.connection_id))
    payload = _session_payload(connection)
    if payload is None:
        return Err(error=CatalogError_Failed(message="session is invalid"))
    lock = payload["lock"]
    if not isinstance(lock, threading.Lock):
        return Err(error=CatalogError_Failed(message="session is invalid"))
    with lock:
        if payload["closed"] is not False or not _driver_matches(connection, payload["driver"]):
            return Err(error=CatalogError_Failed(message="session is closed or invalid"))
        namespace = scope.namespace.value if isinstance(scope.namespace, Some) else None
        rows = _refresh(connection, namespace)
    if not isinstance(rows, list):
        return Err(error=rows)
    if len(rows) > _LIMIT:
        return Err(error=CatalogError_LimitExceeded(limit=_LIMIT))
    rows.sort(key=lambda r: (r[0], r[1]))
    relations = [
        CatalogRelation(
            name=name,
            kind=RelationKind_Table() if kind == _TABLE else RelationKind_View(),
            sql=Nothing() if sql is None else Some(value=sql),
        )
        for name, kind, sql in rows
    ]
    refreshed_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return Ok(value=CatalogSnapshot(scope=scope, relations=CottList(values=relations), refreshed_at=refreshed_at))
