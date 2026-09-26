import base64
import contextlib
import json
import sqlite3
import threading
import urllib.request
from pathlib import Path
from typing import Any, Final, Literal, cast

import adbc_driver_chdb.dbapi
import adbc_driver_duckdb.dbapi
import adbc_driver_flightsql.dbapi
import adbc_driver_manager.dbapi
import adbc_driver_postgresql.dbapi
import adbc_driver_snowflake.dbapi
import adbc_driver_sqlite.dbapi
import cassandra
import cassandra.auth
import cassandra.cluster
import databricks.sql
import duckdb
import google.auth
import google.auth.transport.requests
import mysql.connector
import nebula3.Config
import nebula3.gclient.net
import psycopg
import psycopg.conninfo
import pyodbc
import trino.auth
import trino.dbapi
from cott_runtime import Err, Nothing, Ok, Opaque, Result, Some
from google.cloud import bigquery

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
    ConnectionError,
    ConnectionError_Failed,
    ConnectionError_InvalidOption,
    ConnectionError_ReadOnlyUnsupported,
    ConnectionRequest,
    SettingValue,
    SettingValue_Flag,
    SettingValue_Text,
    SettingValue_Values,
    TransactionMode,
)

_INIT_TITLE: Final[str] = "Harlequin could not initialize the selected adapter."
_DUCK_TITLE: Final[str] = "DuckDB couldn't connect to your database."
_SQLITE_TITLE: Final[str] = "Harlequin could not connect to your SQLite database."
_PG_TITLE: Final[str] = "Harlequin could not connect to your Postgres database."
_MYSQL_TITLE: Final[str] = "Harlequin could not connect to your MySQL database."
_ODBC_TITLE: Final[str] = "Harlequin could not connect to your ODBC data source."
_BQ_TITLE: Final[str] = "Harlequin could not connect to BigQuery."
_TRINO_TITLE: Final[str] = "Harlequin could not connect to Trino."
_DBX_TITLE: Final[str] = "Harlequin could not connect to Databricks."
_ADBC_INIT_TITLE: Final[str] = "Harlequin could not initialize the ADBC adapter."
_ADBC_TITLE: Final[str] = "Harlequin could not connect via ADBC."
_CASS_TITLE: Final[str] = "Harlequin could not connect to your Cassandra cluster."
_NEBULA_TITLE: Final[str] = "Harlequin could not connect to NebulaGraph."
_CHDB_TITLE: Final[str] = "Harlequin could not connect to chDB."
_CASS_LEVELS: Final[str] = "ANY,ONE,TWO,THREE,QUORUM,ALL,LOCAL_QUORUM,EACH_QUORUM,SERIAL,LOCAL_SERIAL,LOCAL_ONE"


def _fail(title: str, message: str) -> ConnectionError:
    return ConnectionError_Failed(title=title, message=message)


def _invalid(title: str, message: str) -> ConnectionError:
    return ConnectionError_InvalidOption(title=title, message=message)


def _names(kind: AdapterKind) -> tuple[str, str]:
    if isinstance(kind, AdapterKind_DuckDb):
        return ("DuckDb", "DuckDB")
    if isinstance(kind, AdapterKind_Sqlite):
        return ("Sqlite", "SQLite")
    if isinstance(kind, AdapterKind_Postgres):
        return ("Postgres", "Postgres")
    if isinstance(kind, AdapterKind_MySql):
        return ("MySql", "MySQL")
    if isinstance(kind, AdapterKind_Odbc):
        return ("Odbc", "ODBC")
    if isinstance(kind, AdapterKind_BigQuery):
        return ("BigQuery", "BigQuery")
    if isinstance(kind, AdapterKind_Trino):
        return ("Trino", "Trino")
    if isinstance(kind, AdapterKind_Databricks):
        return ("Databricks", "Databricks")
    if isinstance(kind, AdapterKind_Adbc):
        return ("Adbc", "ADBC")
    if isinstance(kind, AdapterKind_Cassandra):
        return ("Cassandra", "Cassandra")
    if isinstance(kind, AdapterKind_NebulaGraph):
        return ("NebulaGraph", "NebulaGraph")
    return ("Chdb", "chDB")


def _supports_read_only(variant: str) -> bool:
    return variant in ("DuckDb", "Sqlite", "Postgres", "MySql", "Chdb")


def _numeric_keys(variant: str) -> tuple[tuple[str, bool], ...]:
    if variant == "Sqlite":
        return (("lock_timeout", True), ("detect_types", False), ("cached_statements", False))
    if variant == "MySql":
        return (("port", False), ("connection_timeout", False))
    if variant == "Trino":
        return (("port", False),)
    if variant == "Cassandra":
        return (("port", False), ("protocol_version", False))
    if variant == "NebulaGraph":
        return (("port", False),)
    return ()


def _text(s: dict[str, SettingValue], key: str) -> str | None:
    value = s.get(key)
    if isinstance(value, SettingValue_Text) and value.value != "":
        return value.value
    return None


def _flag(s: dict[str, SettingValue], key: str) -> bool:
    value = s.get(key)
    if isinstance(value, SettingValue_Flag):
        return value.value
    return False


def _values(s: dict[str, SettingValue], key: str) -> list[str]:
    value = s.get(key)
    if isinstance(value, SettingValue_Values):
        return [item for item in value.values]
    if isinstance(value, SettingValue_Text) and value.value != "":
        return [value.value]
    return []


def _int(s: dict[str, SettingValue], key: str) -> int | None:
    raw = _text(s, key)
    return None if raw is None else int(raw)


def _close_any(obj: Any) -> None:
    obj.close()


def _shutdown_any(obj: Any) -> None:
    obj.shutdown()


def _release_any(obj: Any) -> None:
    obj.release()


def _read_script(path: Path) -> str:
    try:
        return path.read_text()
    except (OSError, UnicodeDecodeError):
        return ""


def _split_script(script: str, sqlite: bool) -> list[str]:
    commands: list[str] = []
    chunk: list[str] = []
    for line in script.splitlines():
        stripped = line.strip()
        if line.startswith(".") or (sqlite and stripped in ("/", "go")):
            if chunk:
                commands.append("\n".join(chunk))
                chunk = []
            if line.startswith("."):
                commands.append(line)
        else:
            chunk.append(line)
    if chunk:
        commands.append("\n".join(chunk))
    return commands


def _rewrite_dot(line: str, sqlite: bool) -> str:
    parts = line.split()
    if not parts:
        return ""
    command = parts[0]
    args = parts[1:]
    if command == ".open":
        paths = [a for a in args if not a.startswith("--")]
        if sqlite:
            if not paths:
                return "attach '';"
            return f"attach '{paths[0]}' as {Path(paths[0]).stem};"
        if not paths:
            return "attach ':memory:'; use memory;"
        suffix = " (READ_ONLY)" if "--readonly" in args else ""
        stem = Path(paths[0]).stem
        return f"attach '{paths[0]}'{suffix} as {stem}; use {stem};"
    if sqlite and command == ".load" and args:
        entry = f", '{args[1]}'" if len(args) > 1 else ""
        return f"select load_extension('{args[0]}'{entry});"
    return ""


def _script_pieces(script: str, sqlite: bool) -> list[str]:
    pieces: list[str] = []
    for command in _split_script(script, sqlite):
        text = _rewrite_dot(command, sqlite) if command.startswith(".") else command
        pieces.extend(p for p in text.split(";") if p.strip())
    return pieces


def _init_message(count: int, path: Path) -> str:
    if count == 0:
        return ""
    word = "command" if count == 1 else "commands"
    return f"Executed {count} {word} from {path}"


def _open_duckdb(conn_str: list[str], read_only: bool, s: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    paths = conn_str if conn_str and conn_str != [""] else [":memory:"]
    primary = paths[0]
    database = primary
    token = _text(s, "md_token")
    if token is not None:
        database += "?token=" + token
    if _flag(s, "md_saas"):
        database += "?saas_mode=true"
    unsigned = "true" if _flag(s, "allow_unsigned_extensions") else "false"
    try:
        conn = duckdb.connect(database=database, read_only=read_only, config={"allow_unsigned_extensions": unsigned})
    except duckdb.Error as e:
        message = str(e)
        if "sqlite_scanner" in message:
            message = (
                "DuckDB raised the following error when trying to open one or more database files:\n"
                f"---\n{message}\n---\n\nDid you mean to use Harlequin's sqlite adapter instead? "
                f"Maybe try:\nharlequin -a sqlite {' '.join(conn_str)}"
            )
        return _fail(_DUCK_TITLE, message)
    cleanup.callback(lambda: _close_any(conn))
    try:
        for path in paths[1:]:
            conn.execute(f"attach '{path}'" + (" (READ_ONLY)" if read_only else ""))
    except duckdb.Error as e:
        return _fail(_DUCK_TITLE, str(e))
    try:
        repo = _text(s, "custom_extension_repo")
        if repo is not None:
            conn.execute(f"SET custom_extension_repository='{repo}';")
        force = _flag(s, "force_install_extensions")
        for extension in _values(s, "extension"):
            conn.install_extension(extension, force_install=force)
            conn.load_extension(extension)
    except duckdb.Error as e:
        return _fail("DuckDB couldn't install or load your extension.", str(e))
    message = ""
    if not _flag(s, "no_init"):
        init_path = Path(_text(s, "init_path") or "~/.duckdbrc").expanduser()
        count = 0
        try:
            for piece in _script_pieces(_read_script(init_path), False):
                conn.execute(piece)
                count += 1
        except duckdb.Error as e:
            return _fail(
                "DuckDB could not execute your initialization script.",
                f"Attempted to execute script at {init_path}\n{e}",
            )
        message = _init_message(count, init_path)
    connection_id = "" if paths == [":memory:"] else ",".join(sorted(Path(p).resolve().as_posix() for p in paths))
    return (conn, connection_id, message, f"Connected to database `{primary}`")


def _sqlite_isolation(value: str | None) -> Literal["DEFERRED", "EXCLUSIVE", "IMMEDIATE"] | None:
    upper = (value or "DEFERRED").upper()
    if upper == "EXCLUSIVE":
        return "EXCLUSIVE"
    if upper == "IMMEDIATE":
        return "IMMEDIATE"
    if upper in ("NONE", "AUTOCOMMIT"):
        return None
    return "DEFERRED"


def _sqlite_uri(path: str, read_only: bool, mode: str | None) -> str:
    if path.startswith("file:") or path == ":memory:":
        base = path
    else:
        base = Path(path).resolve().as_uri()
    if read_only:
        return base + "?mode=ro"
    if mode is not None:
        return base + f"?mode={mode}"
    return base


def _open_sqlite(conn_str: list[str], read_only: bool, s: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    mode = _text(s, "mode")
    if read_only and mode is not None and mode != "ro":
        return _invalid(_INIT_TITLE, "Cannot specify readonly flag and a connection mode.")
    paths = [":memory:"] if not conn_str or conn_str == [""] or mode == "memory" else conn_str
    uris = [_sqlite_uri(p, read_only, mode) for p in paths]
    lock_timeout = _text(s, "lock_timeout")
    try:
        conn = sqlite3.connect(
            uris[0],
            timeout=float(lock_timeout) if lock_timeout is not None else 5.0,
            detect_types=_int(s, "detect_types") or 0,
            isolation_level=_sqlite_isolation(_text(s, "isolation_level")),
            check_same_thread=False,
            cached_statements=_int(s, "cached_statements") or 128,
            uri=True,
            autocommit=True,
        )
    except sqlite3.Error as e:
        return _fail(_SQLITE_TITLE, str(e))
    cleanup.callback(lambda: _close_any(conn))
    try:
        conn.execute("pragma database_list")
    except sqlite3.DatabaseError as e:
        return _fail(
            _SQLITE_TITLE,
            f"{e}\n\nThe file at {paths[0]} does not look like a SQLite database. "
            f"If it is a DuckDB database, try: harlequin -a duckdb {paths[0]}",
        )
    try:
        for path, uri in zip(paths[1:], uris[1:]):
            alias = "memory" if path == ":memory:" else Path(path).stem
            conn.execute(f"attach database '{uri}' as {alias}")
    except sqlite3.Error as e:
        return _fail(_SQLITE_TITLE, str(e))
    extensions = _values(s, "extension")
    if extensions:
        try:
            conn.enable_load_extension(True)
            for extension in extensions:
                conn.load_extension(extension)
        except (sqlite3.Error, AttributeError) as e:
            return _fail("SQLite couldn't load your extension.", str(e))
    message = ""
    if not _flag(s, "no_init"):
        init_path = Path(_text(s, "init_path") or "~/.sqliterc").expanduser()
        count = 0
        try:
            for piece in _script_pieces(_read_script(init_path), True):
                conn.execute(piece)
                count += 1
        except sqlite3.Error as e:
            return _fail(
                "SQLite could not execute your initialization script.",
                f"Attempted to execute script at {init_path}\n{e}",
            )
        message = _init_message(count, init_path)
    connection_id = "" if paths == [":memory:"] else ",".join(sorted(Path(p).resolve().as_posix() for p in paths))
    return (conn, connection_id, message, f"Connected to database `{paths[0]}`")


def _built_id(scheme: str, user: str | None, host: str | None, port: str | None, database: str | None) -> str:
    return f"{scheme}://{user or ''}@{host or ''}:{port or ''}/{database or ''}"


def _open_postgres(conn_str: list[str], read_only: bool, s: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    if len(conn_str) > 1:
        return _invalid(
            _INIT_TITLE,
            f"Cannot provide multiple connection strings to the Postgres adapter. {tuple(conn_str)}",
        )
    dsn = conn_str[0] if conn_str else ""
    options: dict[str, str] = {}
    for key, value in s.items():
        if isinstance(value, SettingValue_Text) and value.value != "":
            options[key] = value.value
    try:
        conninfo = psycopg.conninfo.make_conninfo(dsn, **options)
        conn: psycopg.Connection[tuple[object, ...]] = psycopg.connect(conninfo, autocommit=True)
    except psycopg.Error as e:
        return _fail(_PG_TITLE, str(e))
    cleanup.callback(lambda: _close_any(conn))
    if read_only:
        try:
            conn.execute("set session characteristics as transaction read only;")
            row = conn.execute("select current_setting('default_transaction_read_only')").fetchone()
        except psycopg.Error as e:
            return _fail(_PG_TITLE, str(e))
        if row is None or row[0] != "on":
            return _fail(
                "Harlequin could not open a read-only connection to Postgres.",
                "The server did not accept a read-only session, so writes would not be prevented.",
            )
    connection_id = dsn or _built_id(
        "postgres", _text(s, "user"), _text(s, "host"), _text(s, "port"), _text(s, "dbname")
    )
    return (conn, connection_id, "", "Connected to Postgres")


def _open_mysql(conn_str: list[str], read_only: bool, s: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    if conn_str:
        return _invalid(_INIT_TITLE, f"Cannot provide a DSN to the MySQL adapter. Got:\n{tuple(conn_str)}")
    kwargs: dict[str, object] = {"autocommit": True}
    for key in (
        "host",
        "unix_socket",
        "database",
        "user",
        "password2",
        "password3",
        "ssl_ca",
        "ssl_cert",
        "ssl_key",
        "openid_token_file",
    ):
        value = _text(s, key)
        if value is not None:
            kwargs[key] = value
    password = _text(s, "password") or _text(s, "password1")
    if password is not None:
        kwargs["password"] = password
    port = _int(s, "port")
    if port is not None:
        kwargs["port"] = port
    timeout = _int(s, "connection_timeout")
    if timeout is not None:
        kwargs["connection_timeout"] = timeout
    if _flag(s, "ssl_disabled"):
        kwargs["ssl_disabled"] = True
    if _flag(s, "enable_cleartext_plugin"):
        kwargs["allow_local_infile"] = True
    try:
        sdk: Any = mysql.connector
        raw: Any = sdk.connect(**kwargs)
    except Exception as e:
        return _fail(_MYSQL_TITLE, str(e))
    cleanup.callback(lambda: _close_any(raw))
    if read_only:
        try:
            cursor: Any = raw.cursor()
            cursor.execute("set session transaction read only")
            cursor.close()
        except Exception as e:
            return _fail(_MYSQL_TITLE, str(e))
    connection_id = _built_id(
        "mysql", _text(s, "user"), _text(s, "host"), _text(s, "port"), _text(s, "database")
    )
    return (cast(object, raw), connection_id, "", "Connected to MySQL")


def _open_odbc(conn_str: list[str], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    if len(conn_str) != 1:
        return _invalid(
            "Harlequin could not initialize the ODBC adapter.",
            f"The ODBC adapter expects exactly one connection string. It received:\n{tuple(conn_str)}",
        )
    try:
        sdk: Any = pyodbc
        raw: Any = sdk.connect(conn_str[0], autocommit=True)
    except Exception as e:
        return _fail(_ODBC_TITLE, str(e))
    cleanup.callback(lambda: _close_any(raw))
    return (cast(object, raw), conn_str[0], "", "Connected to ODBC data source")


def _open_bigquery(s: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    project = _text(s, "project")
    location = _text(s, "location")
    try:
        sdk: Any = bigquery
        raw: Any = sdk.Client(project=project, location=location)
    except Exception as e:
        return _fail(_BQ_TITLE, str(e))
    cleanup.callback(lambda: _close_any(raw))
    connection_id = _built_id("bigquery", None, None, None, project)
    return (cast(object, raw), connection_id, "", "Connected to BigQuery")


def _open_trino(s: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    user = _text(s, "user")
    host = _text(s, "host")
    kwargs: dict[str, object] = {}
    if host is not None:
        kwargs["host"] = host
    port = _int(s, "port")
    if port is not None:
        kwargs["port"] = port
    if user is not None:
        kwargs["user"] = user
    catalog = _text(s, "catalog")
    if catalog is not None:
        kwargs["catalog"] = catalog
    schema = _text(s, "schema")
    if schema is not None:
        kwargs["schema"] = schema
    auth = _text(s, "require_auth")
    try:
        auth_sdk: Any = trino.auth
        if auth == "password":
            kwargs["auth"] = auth_sdk.BasicAuthentication(user, _text(s, "password"))
            kwargs["http_scheme"] = "https"
            kwargs["verify"] = _text(s, "sslcert") or False
        elif auth == "google":
            gauth: Any = google.auth
            greq: Any = google.auth.transport.requests
            credentials: Any = gauth.default()[0]
            credentials.refresh(greq.Request())
            kwargs["auth"] = auth_sdk.JWTAuthentication(credentials.token)
            kwargs["http_scheme"] = "https"
            kwargs["verify"] = True
        sdk: Any = trino.dbapi
        raw: Any = sdk.connect(**kwargs)
    except Exception as e:
        return _fail(_TRINO_TITLE, str(e))
    cleanup.callback(lambda: _close_any(raw))
    connection_id = _built_id("trino", user, host, _text(s, "port"), catalog)
    return (cast(object, raw), connection_id, "", "Connected to Trino")


def _m2m_token(hostname: str, client_id: str, client_secret: str) -> str:
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request(
        f"https://{hostname}/oidc/v1/token",
        data=b"grant_type=client_credentials&scope=all-apis",
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        body = cast(object, json.loads(cast(bytes, resp.read())))
    if not isinstance(body, dict):
        raise ValueError("The Databricks token endpoint returned an unexpected reply.")
    token = cast(dict[str, object], body).get("access_token")
    if not isinstance(token, str) or token == "":
        raise ValueError("The Databricks token endpoint did not return an access token.")
    return token


def _open_databricks(s: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    hostname = _text(s, "server_hostname")
    client_id = _text(s, "client_id")
    client_secret = _text(s, "client_secret")
    if (client_id is None) != (client_secret is None):
        return _invalid(
            _INIT_TITLE,
            "To use OAuth M2M you must supply both --client-id and --client-secret CLI arguments.",
        )
    kwargs: dict[str, object] = {"server_hostname": hostname, "http_path": _text(s, "http_path")}
    token = _text(s, "access_token")
    username = _text(s, "username")
    auth_type = _text(s, "auth_type")
    try:
        if token is not None:
            kwargs["access_token"] = token
        elif username is not None:
            kwargs["username"] = username
            kwargs["password"] = _text(s, "password")
        elif auth_type is not None:
            kwargs["auth_type"] = auth_type
        elif client_id is not None and client_secret is not None:
            kwargs["access_token"] = _m2m_token(hostname or "", client_id, client_secret)
        sdk: Any = databricks.sql
        raw: Any = sdk.connect(**kwargs)
    except Exception as e:
        return _fail(_DBX_TITLE, str(e))
    cleanup.callback(lambda: _close_any(raw))
    message = ""
    if not _flag(s, "no_init"):
        init_path = Path(_text(s, "init_path") or "~/.databricksrc").expanduser()
        count = 0
        try:
            cursor: Any = raw.cursor()
            for piece in _read_script(init_path).split(";"):
                if piece.strip():
                    cursor.execute(piece)
                    count += 1
            cursor.close()
        except Exception as e:
            return _fail("Databricks errored while executing your initialization script.", str(e))
        message = _init_message(count, init_path)
    connection_id = _built_id("databricks", username, hostname, None, _text(s, "http_path"))
    return (cast(object, raw), connection_id, message, "Connected to Databricks")


def _adbc_connect(driver_type: str, uri: str, kwargs: dict[str, str]) -> Any:
    if driver_type == "flightsql":
        flight: Any = adbc_driver_flightsql.dbapi
        return flight.connect(uri, db_kwargs=kwargs)
    if driver_type == "postgresql":
        pg: Any = adbc_driver_postgresql.dbapi
        return pg.connect(uri, db_kwargs=kwargs)
    if driver_type == "snowflake":
        snow: Any = adbc_driver_snowflake.dbapi
        return snow.connect(uri, db_kwargs=kwargs)
    if driver_type == "sqlite":
        lite: Any = adbc_driver_sqlite.dbapi
        return lite.connect(uri, db_kwargs=kwargs)
    if driver_type == "duckdb":
        duck: Any = adbc_driver_duckdb.dbapi
        return duck.connect(uri, db_kwargs=kwargs)
    raise ValueError(f"Unknown ADBC driver type: {driver_type}")


def _open_adbc(conn_str: list[str], s: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    if len(conn_str) != 1:
        return _invalid(
            _ADBC_INIT_TITLE,
            f"The ADBC adapter expects exactly one connection string. It received:\n{tuple(conn_str)}",
        )
    driver_type = _text(s, "driver_type")
    driver_path = _text(s, "driver_path")
    if driver_type is None and driver_path is None:
        return _invalid(
            _ADBC_INIT_TITLE,
            "The ADBC adapter expects either at least a driver type or a driver path and neither was provided.",
        )
    kwargs: dict[str, str] = {}
    for pair in (_text(s, "db_kwargs_str") or "").split(";"):
        if "=" in pair:
            key, _, value = pair.partition("=")
            kwargs[key.strip()] = value.strip()
    try:
        if driver_path is not None:
            manager: Any = adbc_driver_manager.dbapi
            raw: Any = manager.connect(driver=driver_path, db_kwargs={**kwargs, "uri": conn_str[0]})
        else:
            raw = _adbc_connect(driver_type or "", conn_str[0], kwargs)
    except Exception as e:
        return _fail(_ADBC_TITLE, str(e))
    cleanup.callback(lambda: _close_any(raw))
    return (cast(object, raw), conn_str[0], "", "Connected via ADBC")


def _open_cassandra(s: dict[str, SettingValue], level_name: str, cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    host = _text(s, "host")
    kwargs: dict[str, object] = {"port": _int(s, "port") or 9042}
    protocol = _int(s, "protocol_version")
    if protocol is not None:
        kwargs["protocol_version"] = protocol
    user = _text(s, "user")
    keyspace = _text(s, "keyspace")
    try:
        if user is not None:
            auth: Any = cassandra.auth
            kwargs["auth_provider"] = auth.PlainTextAuthProvider(username=user, password=_text(s, "password"))
        cluster_sdk: Any = cassandra.cluster
        cluster: Any = cluster_sdk.Cluster([host or "localhost"], **kwargs)
        cleanup.callback(lambda: _shutdown_any(cluster))
        session: Any = cluster.connect(keyspace)
        levels: Any = cassandra.ConsistencyLevel
        session.default_consistency_level = levels.name_to_value[level_name]
    except Exception as e:
        return _fail(_CASS_TITLE, str(e))
    connection_id = _built_id("cassandra", user, host, _text(s, "port"), keyspace)
    return (cast(object, session), connection_id, "", "Connected to Cassandra")


def _open_nebula(s: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    host = _text(s, "host") or "127.0.0.1"
    port = _int(s, "port") or 9669
    user = _text(s, "user") or "root"
    try:
        config_sdk: Any = nebula3.Config
        net: Any = nebula3.gclient.net
        pool: Any = net.ConnectionPool()
        config: Any = config_sdk.Config()
        ok = bool(cast(object, pool.init([(host, port)], config)))
        cleanup.callback(lambda: _close_any(pool))
        if not ok:
            return _fail(_NEBULA_TITLE, f"Could not initialize a connection pool to {host}:{port}.")
        session: Any = pool.get_session(user, _text(s, "password") or "nebula")
        cleanup.callback(lambda: _release_any(session))
    except Exception as e:
        return _fail(_NEBULA_TITLE, str(e))
    connection_id = _built_id("nebulagraph", user, host, str(port), None)
    return (cast(object, session), connection_id, "", "Connected to NebulaGraph")


def _chdb_uri(value: str) -> str:
    if value in ("", ":memory:", "chdb://:memory:", "chdb::memory:"):
        return "chdb://"
    if "://" in value or value.startswith(("chdb:", "file:", "local:")):
        return value
    return "file:" + Path(value).resolve().as_posix()


def _open_chdb(conn_str: list[str], read_only: bool, s: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    candidates = [c for c in conn_str if c.strip()]
    for key in ("uri", "path"):
        value = _text(s, key)
        if value is not None and value.strip():
            candidates.append(value)
    if len(candidates) > 1:
        return _invalid(_INIT_TITLE, "Pass only one of a positional database path, --path, or --uri.")
    uri = _chdb_uri(candidates[0] if candidates else "")
    try:
        sdk: Any = adbc_driver_chdb.dbapi
        if read_only:
            raw: Any = sdk.connect(uri, conn_kwargs={"adbc.connection.readonly": "true"})
        else:
            raw = sdk.connect(uri)
    except Exception as e:
        return _fail(_CHDB_TITLE, str(e))
    cleanup.callback(lambda: _close_any(raw))
    return (cast(object, raw), uri, "", f"Connected to chDB `{uri}`")


def _dispatch(variant: str, conn_str: list[str], read_only: bool, s: dict[str, SettingValue], level: str, cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    if variant == "DuckDb":
        return _open_duckdb(conn_str, read_only, s, cleanup)
    if variant == "Sqlite":
        return _open_sqlite(conn_str, read_only, s, cleanup)
    if variant == "Postgres":
        return _open_postgres(conn_str, read_only, s, cleanup)
    if variant == "MySql":
        return _open_mysql(conn_str, read_only, s, cleanup)
    if variant == "Odbc":
        return _open_odbc(conn_str, cleanup)
    if variant == "BigQuery":
        return _open_bigquery(s, cleanup)
    if variant == "Trino":
        return _open_trino(s, cleanup)
    if variant == "Databricks":
        return _open_databricks(s, cleanup)
    if variant == "Adbc":
        return _open_adbc(conn_str, s, cleanup)
    if variant == "Cassandra":
        return _open_cassandra(s, level, cleanup)
    if variant == "NebulaGraph":
        return _open_nebula(s, cleanup)
    return _open_chdb(conn_str, read_only, s, cleanup)


def connect(request: ConnectionRequest) -> Result[Connection, ConnectionError]:
    variant, display = _names(request.adapter)
    if request.read_only and not _supports_read_only(variant):
        return Err(error=ConnectionError_ReadOnlyUnsupported(adapter=display))
    s: dict[str, SettingValue] = {}
    for setting in request.settings:
        s[setting.name.replace("-", "_")] = setting.value
    for key, is_float in _numeric_keys(variant):
        raw = _text(s, key)
        if raw is None:
            continue
        try:
            if is_float:
                float(raw)
            else:
                int(raw)
        except ValueError as e:
            return Err(error=_invalid(_INIT_TITLE, f"{display} adapter received bad config value: {e}"))
    level = (_text(s, "consistency_level") or "LOCAL_ONE").upper()
    if level not in _CASS_LEVELS.split(","):
        level = "LOCAL_ONE"
    conn_str = [item for item in request.conn_str]
    cleanup: contextlib.ExitStack[bool | None] = contextlib.ExitStack()
    try:
        opened = _dispatch(variant, conn_str, request.read_only, s, level, cleanup)
    except BaseException:
        cleanup.close()
        raise
    if not isinstance(opened, tuple):
        cleanup.close()
        return Err(error=opened)
    driver, connection_id, init_message, driver_details = opened
    modes: list[str] = []
    current: str | None = None
    mode_option: Some[TransactionMode] | Nothing = Nothing()
    if variant in ("Sqlite", "Postgres"):
        modes = ["Auto", "Manual"]
        current = "Auto"
        mode_option = Some(value=TransactionMode(label="Auto", can_commit=False, can_rollback=False))
    elif variant == "Cassandra":
        modes = [name[:10] for name in _CASS_LEVELS.split(",")]
        current = level[:10]
        mode_option = Some(value=TransactionMode(label=current, can_commit=False, can_rollback=False))
    payload: dict[str, object] = {
        "adapter": variant,
        "driver": driver,
        "request": request,
        "cleanup": cleanup,
        "lock": threading.RLock(),
        "closed": False,
        "transaction_mode": current,
        "modes": modes,
        "active": [],
    }
    return Ok(
        value=Connection(
            adapter=request.adapter,
            connection_id=connection_id,
            init_message=init_message,
            driver_details=driver_details,
            read_only=request.read_only,
            transaction_mode=mode_option,
            session=Opaque(tag="harlequin.session", value=payload),
        )
    )
