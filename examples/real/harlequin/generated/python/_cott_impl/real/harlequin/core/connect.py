import contextlib
import json
import math
import pathlib
import re
import sqlite3
import threading
import urllib.parse
import uuid
import warnings
from collections.abc import Mapping
from typing import Final, cast

import adbc_driver_manager.dbapi
import duckdb
import google.api_core.exceptions
import google.auth.exceptions
import psycopg
import psycopg.conninfo
import psycopg.errors
import pymysql
import pymysql.cursors
import pymysql.err
import pyodbc
import trino.auth
import trino.dbapi
from cassandra import AuthenticationFailed as CassandraAuthenticationFailed
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, NoHostAvailable
from databricks import sql as dbsql
from google.cloud import bigquery
from nebula3.Config import Config
from nebula3.Exception import AuthFailedException
from nebula3.gclient.net import ConnectionPool

from cott_runtime import Err, Ok, Opaque, Result
from real.harlequin.core_types import AdapterKind, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_PostgreSql, AdapterKind_Sqlite, AdapterKind_Trino, Connection, ConnectionError, ConnectionError_AdapterUnavailable, ConnectionError_AuthenticationFailed, ConnectionError_Failed, ConnectionError_InvalidEndpoint, ConnectionRequest, SessionHandle

_SESSION_TAG: Final[str] = "harlequin.session"


def _invalid() -> ConnectionError:
    return ConnectionError_InvalidEndpoint(endpoint="")


def _canonical(obj: dict[str, object]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _port(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and 0 < value < 65536:
        return value
    return None


def _json_fields(adapter: AdapterKind) -> tuple[dict[str, str], set[str]]:
    if isinstance(adapter, AdapterKind_MySql):
        return ({"host": "str", "user": "str", "database": "str", "password": "str", "port": "int", "unix_socket": "str", "ssl_ca": "str", "ssl_cert": "str", "ssl_key": "str", "ssl_verify_cert": "bool", "ssl_verify_identity": "bool"}, {"host", "user", "database"})
    if isinstance(adapter, AdapterKind_BigQuery):
        return ({"project": "str", "dataset": "str", "location": "str", "auth": "json"}, {"project", "auth"})
    if isinstance(adapter, AdapterKind_Trino):
        return ({"host": "str", "user": "str", "catalog": "str", "schema": "str", "scheme": "str", "port": "int", "auth": "json"}, {"host", "user"})
    if isinstance(adapter, AdapterKind_Databricks):
        return ({"server_hostname": "str", "http_path": "str", "auth": "json", "catalog": "str", "schema": "str"}, {"server_hostname", "http_path", "auth"})
    if isinstance(adapter, AdapterKind_Cassandra):
        return ({"contact_points": "json", "keyspace": "str", "auth": "json"}, {"contact_points"})
    if isinstance(adapter, AdapterKind_NebulaGraph):
        return ({"addresses": "json", "username": "str", "password": "str", "space": "str"}, {"addresses", "username", "password"})
    return ({"driver": "str", "uri": "str", "entrypoint": "str", "db": "json", "connection": "json", "catalog": "str"}, {"driver"})


def _json_endpoint(endpoint: str, settings: dict[str, str], kinds: dict[str, str], required: set[str]) -> dict[str, object] | None:
    try:
        parsed: object = json.loads(endpoint)
    except ValueError:
        return None
    if not isinstance(parsed, dict):
        return None
    obj: dict[str, object] = dict(cast(dict[str, object], parsed))
    for name, text in settings.items():
        kind = kinds.get(name)
        if kind is None:
            return None
        if kind == "str":
            obj[name] = text
        elif kind == "int":
            if re.fullmatch(r"[+-]?[0-9]+", text, re.ASCII) is None:
                return None
            obj[name] = int(text)
        elif kind == "bool":
            if text not in ("true", "false"):
                return None
            obj[name] = text == "true"
        else:
            try:
                obj[name] = json.loads(text)
            except ValueError:
                return None
    keys: set[str] = set(obj.keys())
    known: set[str] = set(kinds.keys())
    if not required <= keys or not keys <= known:
        return None
    for key, value in obj.items():
        kind = kinds[key]
        if kind == "str" and not isinstance(value, str):
            return None
        if kind == "int" and (not isinstance(value, int) or isinstance(value, bool)):
            return None
        if kind == "bool" and not isinstance(value, bool):
            return None
    return obj


def _host_ports(value: object) -> list[tuple[str, int]] | None:
    if not isinstance(value, list):
        return None
    items = cast(list[object], value)
    if len(items) == 0:
        return None
    result: list[tuple[str, int]] = []
    for item in items:
        if not isinstance(item, dict):
            return None
        entry = cast(dict[str, object], item)
        entry_keys: set[str] = set(entry.keys())
        if entry_keys != {"host", "port"}:
            return None
        host = entry["host"]
        port = _port(entry["port"])
        if not isinstance(host, str) or not host or port is None:
            return None
        result.append((host, port))
    return result


def _string_map(value: object) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    result: dict[str, str] = {}
    for key, item in cast(dict[str, object], value).items():
        if not isinstance(item, str):
            return None
        result[key] = item
    return result


def _auth_object(value: object, auth_type: str, fields: set[str]) -> dict[str, str] | None:
    mapping = _string_map(value)
    if mapping is None:
        return None
    keys: set[str] = set(mapping.keys())
    if keys != (fields | {"type"}) or mapping["type"] != auth_type:
        return None
    return mapping


def _opt_str(obj: dict[str, object], key: str) -> str | None:
    value = obj.get(key)
    return value if isinstance(value, str) else None


def _req_str(obj: dict[str, object], key: str) -> str:
    value = obj[key]
    return value if isinstance(value, str) else ""


def _opt_bool(obj: dict[str, object], key: str, default: bool) -> bool:
    value = obj.get(key, default)
    return value if isinstance(value, bool) else default


def _open_sqlite(endpoint: str, read_only: bool, settings: dict[str, str], stack: contextlib.ExitStack[bool | None]) -> tuple[str, object] | ConnectionError:
    timeout = 5.0
    for name, text in settings.items():
        if name != "timeout":
            return _invalid()
        try:
            timeout = float(text)
        except ValueError:
            return _invalid()
        if not math.isfinite(timeout) or timeout <= 0:
            return _invalid()
    if not endpoint:
        return _invalid()
    mode = "ro" if read_only else "rw"
    if endpoint == ":memory:":
        conn = sqlite3.connect(":memory:", timeout=timeout, isolation_level=None, check_same_thread=False)
    else:
        if endpoint.startswith("file:"):
            base, _, query = endpoint.partition("?")
            params: list[tuple[str, str]] = []
            for key, value in urllib.parse.parse_qsl(query, keep_blank_values=True):
                if key == "mode":
                    if value not in ("ro", "rw"):
                        return _invalid()
                    continue
                params.append((key, value))
            params.append(("mode", mode))
            target = base + "?" + urllib.parse.urlencode(params)
        else:
            target = pathlib.Path(endpoint).absolute().as_uri() + "?mode=" + mode
        conn = sqlite3.connect(target, uri=True, timeout=timeout, isolation_level=None, check_same_thread=False)
    stack.callback(conn.close)
    if read_only:
        conn.execute("PRAGMA query_only = ON")
    return (endpoint, conn)


def _open_duckdb(endpoint: str, read_only: bool, settings: dict[str, str], stack: contextlib.ExitStack[bool | None]) -> tuple[str, object] | ConnectionError:
    config: dict[str, str | bool | int | float | list[str]] = {}
    for name, text in settings.items():
        if name == "threads":
            if re.fullmatch(r"[0-9]+", text, re.ASCII) is None or int(text) <= 0:
                return _invalid()
        elif name == "memory_limit":
            if re.fullmatch(r"[0-9]+(\.[0-9]+)?\s*(B|KB|MB|GB|TB|KIB|MIB|GIB|TIB)?|[0-9]+(\.[0-9]+)?%", text.upper(), re.ASCII) is None:
                return _invalid()
        else:
            return _invalid()
        config[name] = text
    if not endpoint:
        return _invalid()
    if endpoint == ":memory:":
        conn = duckdb.connect(database=":memory:", config=config)
    else:
        conn = duckdb.connect(database=endpoint, read_only=read_only, config=config)
    stack.callback(conn.close)
    return (endpoint, conn)


def _open_postgres(endpoint: str, read_only: bool, settings: dict[str, str], stack: contextlib.ExitStack[bool | None]) -> tuple[str, object] | ConnectionError:
    try:
        conninfo = psycopg.conninfo.make_conninfo(endpoint, **settings)
        psycopg.conninfo.conninfo_to_dict(conninfo)
    except psycopg.ProgrammingError:
        return _invalid()
    conn = psycopg.connect(conninfo, autocommit=False)
    stack.callback(conn.close)
    conn.read_only = read_only
    return (conninfo, conn)


def _open_mysql(obj: dict[str, object], read_only: bool, stack: contextlib.ExitStack[bool | None]) -> tuple[str, object] | ConnectionError:
    port = _port(obj.get("port", 3306))
    if port is None:
        return _invalid()
    tls = any(key in obj for key in ("ssl_ca", "ssl_cert", "ssl_key", "ssl_verify_cert", "ssl_verify_identity"))
    verify_cert: bool | None = _opt_bool(obj, "ssl_verify_cert", True) if tls else None
    verify_identity: bool | None = _opt_bool(obj, "ssl_verify_identity", True) if tls else None
    conn = pymysql.connect(host=_req_str(obj, "host"), user=_req_str(obj, "user"), password=_opt_str(obj, "password") or "", database=_req_str(obj, "database"), port=port, unix_socket=_opt_str(obj, "unix_socket"), ssl_ca=_opt_str(obj, "ssl_ca"), ssl_cert=_opt_str(obj, "ssl_cert"), ssl_key=_opt_str(obj, "ssl_key"), ssl_verify_cert=verify_cert, ssl_verify_identity=verify_identity, autocommit=False)
    stack.callback(conn.close)
    if read_only:
        cur = cast(pymysql.cursors.Cursor, conn.cursor())
        try:
            cur.execute("SET SESSION TRANSACTION READ ONLY")
        finally:
            cur.close()
    return (_canonical(obj), conn)


def _odbc_pairs(text: str) -> list[tuple[str, str]] | None:
    pairs: list[tuple[str, str]] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == ";":
            i += 1
            continue
        eq = text.find("=", i)
        if eq < 0:
            if text[i:].strip():
                return None
            break
        key = text[i:eq]
        if ";" in key or not key.strip():
            return None
        k = eq + 1
        if k < n and text[k] == "{":
            m = k + 1
            while True:
                if m >= n:
                    return None
                if text[m] == "}":
                    if m + 1 < n and text[m + 1] == "}":
                        m += 2
                        continue
                    break
                m += 1
            raw = text[k:m + 1]
            i = m + 1
            while i < n and text[i] in " \t":
                i += 1
            if i < n and text[i] != ";":
                return None
        else:
            end = text.find(";", k)
            if end < 0:
                end = n
            raw = text[k:end]
            i = end
        pairs.append((key, raw))
    return pairs


def _open_odbc(endpoint: str, read_only: bool, settings: dict[str, str], stack: contextlib.ExitStack[bool | None]) -> tuple[str, object] | ConnectionError:
    pairs = _odbc_pairs(endpoint)
    if pairs is None or len(pairs) == 0:
        return _invalid()
    for name, value in settings.items():
        if re.fullmatch(r"[A-Za-z0-9_ ]+", name, re.ASCII) is None or not name.strip():
            return _invalid()
        folded = name.strip().casefold()
        pairs = [pair for pair in pairs if pair[0].strip().casefold() != folded]
        pairs.append((name, "{" + value.replace("}", "}}") + "}"))
    conn_str = ";".join(key + "=" + raw for key, raw in pairs)
    conn = pyodbc.connect(conn_str, autocommit=False, readonly=read_only)
    stack.callback(conn.close)
    return (conn_str, conn)


def _open_bigquery(obj: dict[str, object], stack: contextlib.ExitStack[bool | None]) -> tuple[str, object] | ConnectionError:
    if _auth_object(obj["auth"], "adc", set()) is None:
        return _invalid()
    project = _req_str(obj, "project")
    dataset = _opt_str(obj, "dataset")
    job_config = bigquery.QueryJobConfig(default_dataset=f"{project}.{dataset}") if dataset is not None else None
    client = bigquery.Client(project=project, location=_opt_str(obj, "location"), default_query_job_config=job_config)
    stack.callback(client.close)
    return (_canonical(obj), client)


def _open_trino(obj: dict[str, object], stack: contextlib.ExitStack[bool | None]) -> tuple[str, object] | ConnectionError:
    scheme = _opt_str(obj, "scheme") or "https"
    if scheme not in ("https", "http"):
        return _invalid()
    port = _port(obj.get("port", 443 if scheme == "https" else 80))
    if port is None:
        return _invalid()
    user = _req_str(obj, "user")
    auth: trino.auth.BasicAuthentication | None = None
    if "auth" in obj:
        basic = _auth_object(obj["auth"], "basic", {"password"})
        if basic is None or scheme != "https":
            return _invalid()
        auth = trino.auth.BasicAuthentication(user, basic["password"])
    conn = trino.dbapi.connect(host=_req_str(obj, "host"), port=port, user=user, catalog=_opt_str(obj, "catalog"), schema=_opt_str(obj, "schema"), http_scheme=scheme, auth=auth)
    stack.callback(conn.close)
    return (_canonical(obj), conn)


def _open_databricks(obj: dict[str, object], stack: contextlib.ExitStack[bool | None]) -> tuple[str, object] | ConnectionError:
    auth = _auth_object(obj["auth"], "pat", {"access_token"})
    if auth is None:
        return _invalid()
    conn = dbsql.connect(server_hostname=_req_str(obj, "server_hostname"), http_path=_req_str(obj, "http_path"), access_token=auth["access_token"], catalog=_opt_str(obj, "catalog"), schema=_opt_str(obj, "schema"))
    stack.callback(conn.close)
    return (_canonical(obj), conn)


def _open_cassandra(obj: dict[str, object], stack: contextlib.ExitStack[bool | None]) -> tuple[str, object] | ConnectionError:
    points = _host_ports(obj["contact_points"])
    if points is None:
        return _invalid()
    provider: PlainTextAuthProvider | None = None
    if "auth" in obj:
        auth = _auth_object(obj["auth"], "plain", {"username", "password"})
        if auth is None:
            return _invalid()
        provider = PlainTextAuthProvider(username=auth["username"], password=auth["password"])
    cluster = Cluster(contact_points=points, auth_provider=provider)
    stack.callback(cluster.shutdown)
    try:
        session = cluster.connect(_opt_str(obj, "keyspace"))
    except NoHostAvailable as exc:
        errors: object = exc.errors
        if isinstance(errors, Mapping):
            for inner in cast(Mapping[object, object], errors).values():
                if isinstance(inner, CassandraAuthenticationFailed):
                    return ConnectionError_AuthenticationFailed(message="authentication failed")
        raise
    stack.callback(session.shutdown)
    return (_canonical(obj), session)


def _open_nebula(obj: dict[str, object], stack: contextlib.ExitStack[bool | None]) -> tuple[str, object] | ConnectionError:
    addresses = _host_ports(obj["addresses"])
    space = _opt_str(obj, "space")
    if addresses is None or (space is not None and (not space or "`" in space)):
        return _invalid()
    pool = ConnectionPool()
    stack.callback(pool.close)
    if not pool.init(addresses, Config()):
        return ConnectionError_Failed(message="connection failed")
    session = pool.get_session(_req_str(obj, "username"), _req_str(obj, "password"))
    stack.callback(session.release)
    if space is not None:
        response = session.execute(f"USE `{space}`")
        if not response.is_succeeded():
            return ConnectionError_Failed(message="connection failed")
    return (_canonical(obj), session)


def _open_adbc(obj: dict[str, object], read_only: bool, stack: contextlib.ExitStack[bool | None]) -> tuple[str, object] | ConnectionError:
    driver = _req_str(obj, "driver")
    db_kwargs = _string_map(obj.get("db", {}))
    conn_kwargs = _string_map(obj.get("connection", {}))
    if not driver or db_kwargs is None or conn_kwargs is None:
        return _invalid()
    if read_only:
        conn_kwargs["adbc.connection.readonly"] = "true"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        conn = adbc_driver_manager.dbapi.connect(driver=driver, uri=_opt_str(obj, "uri"), entrypoint=_opt_str(obj, "entrypoint"), db_kwargs=db_kwargs, conn_kwargs=conn_kwargs, autocommit=False)
    stack.callback(conn.close)
    for warning in caught:
        if "autocommit" in str(warning.message).lower():
            return ConnectionError_Failed(message="adapter does not support manual commit")
    return (_canonical(obj), conn)


def _open(request: ConnectionRequest, settings: dict[str, str], stack: contextlib.ExitStack[bool | None]) -> tuple[str, object] | ConnectionError:
    adapter = request.adapter
    endpoint = request.endpoint
    read_only = request.read_only
    if isinstance(adapter, AdapterKind_Sqlite):
        return _open_sqlite(endpoint, read_only, settings, stack)
    if isinstance(adapter, AdapterKind_DuckDb):
        return _open_duckdb(endpoint, read_only, settings, stack)
    if isinstance(adapter, AdapterKind_PostgreSql):
        return _open_postgres(endpoint, read_only, settings, stack)
    if isinstance(adapter, AdapterKind_Odbc):
        return _open_odbc(endpoint, read_only, settings, stack)
    kinds, required = _json_fields(adapter)
    obj = _json_endpoint(endpoint, settings, kinds, required)
    if obj is None:
        return _invalid()
    if isinstance(adapter, AdapterKind_MySql):
        return _open_mysql(obj, read_only, stack)
    if isinstance(adapter, AdapterKind_BigQuery):
        return _open_bigquery(obj, stack)
    if isinstance(adapter, AdapterKind_Trino):
        return _open_trino(obj, stack)
    if isinstance(adapter, AdapterKind_Databricks):
        return _open_databricks(obj, stack)
    if isinstance(adapter, AdapterKind_Cassandra):
        return _open_cassandra(obj, stack)
    if isinstance(adapter, AdapterKind_NebulaGraph):
        return _open_nebula(obj, stack)
    return _open_adbc(obj, read_only, stack)


def _is_auth_error(error: Exception) -> bool:
    if isinstance(error, (psycopg.errors.InvalidPassword, psycopg.errors.InvalidAuthorizationSpecification)):
        return True
    if isinstance(error, psycopg.Error) and error.sqlstate in ("28000", "28P01"):
        return True
    if isinstance(error, (google.auth.exceptions.DefaultCredentialsError, google.auth.exceptions.RefreshError)):
        return True
    if isinstance(error, (google.api_core.exceptions.Unauthorized, google.api_core.exceptions.Forbidden)):
        return True
    if isinstance(error, (CassandraAuthenticationFailed, AuthFailedException)):
        return True
    if isinstance(error, pymysql.err.OperationalError) and len(error.args) > 0 and error.args[0] in (1044, 1045, 1698):
        return True
    if isinstance(error, pyodbc.Error) and len(error.args) > 0 and error.args[0] == "28000":
        return True
    return False


def _is_unavailable(error: Exception) -> bool:
    return isinstance(error, pyodbc.Error) and len(error.args) > 0 and error.args[0] in ("IM002", "IM003")


def connect(request: ConnectionRequest) -> Result[Connection, ConnectionError]:
    settings: dict[str, str] = {}
    for setting in request.settings:
        if not setting.name.strip() or setting.name in settings:
            return Err(error=_invalid())
        settings[setting.name] = setting.value
    try:
        with contextlib.ExitStack() as stack:
            opened = _open(request, settings, stack)
            if isinstance(opened, ConnectionError):
                return Err(error=opened)
            cleanup = stack.pop_all()
    except Exception as exc:
        if _is_unavailable(exc):
            return Err(error=ConnectionError_AdapterUnavailable(adapter=request.adapter))
        if _is_auth_error(exc):
            return Err(error=ConnectionError_AuthenticationFailed(message="authentication failed"))
        return Err(error=ConnectionError_Failed(message="connection failed"))
    endpoint, driver = opened
    session_id = uuid.uuid4().hex
    payload: dict[str, object] = {"id": session_id, "adapter": request.adapter, "endpoint": endpoint, "read_only": request.read_only, "driver": driver, "cleanup": cleanup, "lock": threading.Lock(), "closed": False, "transaction": None}
    session: SessionHandle = Opaque(tag=_SESSION_TAG, value=payload)
    return Ok(value=Connection(id=session_id, adapter=request.adapter, endpoint=endpoint, read_only=request.read_only, session=session))
