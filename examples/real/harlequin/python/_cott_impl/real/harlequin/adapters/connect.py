import base64
import contextlib
import json
import math
import sqlite3
import threading
import urllib.parse
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
from cott_runtime import CottContractViolation, Err, Nothing, Ok, Opaque, Result, Some, _cott_fixture_database, _cott_fixture_read
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
_ODBC_INIT_TITLE: Final[str] = "Harlequin could not initialize the ODBC adapter."
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
_PG_KEYS: Final[str] = "host hostaddr port dbname user password passfile connect_timeout client_encoding options application_name fallback_application_name keepalives keepalives_idle keepalives_interval keepalives_count sslmode sslcert sslkey sslrootcert sslcrl sslcrldir channel_binding target_session_attrs gssencmode service servicefile requirepeer replication"


def _failed(title: str, message: str) -> ConnectionError:
    return ConnectionError_Failed(title=title, message=message)


def _invalid(title: str, message: str) -> ConnectionError:
    return ConnectionError_InvalidOption(title=title, message=message)


def _names(kind: AdapterKind) -> tuple[str, str, str]:
    if isinstance(kind, AdapterKind_DuckDb):
        return "DuckDb", "DuckDB", _DUCK_TITLE
    if isinstance(kind, AdapterKind_Sqlite):
        return "Sqlite", "SQLite", _SQLITE_TITLE
    if isinstance(kind, AdapterKind_Postgres):
        return "Postgres", "Postgres", _PG_TITLE
    if isinstance(kind, AdapterKind_MySql):
        return "MySql", "MySQL", _MYSQL_TITLE
    if isinstance(kind, AdapterKind_Odbc):
        return "Odbc", "ODBC", _ODBC_TITLE
    if isinstance(kind, AdapterKind_BigQuery):
        return "BigQuery", "BigQuery", _BQ_TITLE
    if isinstance(kind, AdapterKind_Trino):
        return "Trino", "Trino", _TRINO_TITLE
    if isinstance(kind, AdapterKind_Databricks):
        return "Databricks", "Databricks", _DBX_TITLE
    if isinstance(kind, AdapterKind_Adbc):
        return "Adbc", "ADBC", _ADBC_TITLE
    if isinstance(kind, AdapterKind_Cassandra):
        return "Cassandra", "Cassandra", _CASS_TITLE
    if isinstance(kind, AdapterKind_NebulaGraph):
        return "NebulaGraph", "NebulaGraph", _NEBULA_TITLE
    return "Chdb", "chDB", _CHDB_TITLE


def _text(settings: dict[str, SettingValue], key: str) -> str | None:
    value = settings.get(key)
    if isinstance(value, SettingValue_Text) and value.value != "":
        return value.value
    return None


def _flag(settings: dict[str, SettingValue], key: str) -> bool:
    value = settings.get(key)
    return value.value if isinstance(value, SettingValue_Flag) else False


def _values(settings: dict[str, SettingValue], key: str) -> list[str]:
    value = settings.get(key)
    if isinstance(value, SettingValue_Values):
        return [item for item in value.values]
    return []


def _numeric_keys(variant: str) -> tuple[str, ...]:
    if variant == "Sqlite":
        return ("lock_timeout", "detect_types", "cached_statements")
    if variant == "MySql":
        return ("port", "connection_timeout")
    if variant == "Trino" or variant == "NebulaGraph":
        return ("port",)
    if variant == "Cassandra":
        return ("port", "protocol_version")
    return ()


def _integer(numbers: dict[str, int | float], key: str) -> int | None:
    number = numbers.get(key)
    return number if isinstance(number, int) else None


def _close_resource(resource: object) -> None:
    sdk: Any = resource
    sdk.close()


def _shutdown_resource(resource: object) -> None:
    sdk: Any = resource
    sdk.shutdown()


def _release_resource(resource: object) -> None:
    sdk: Any = resource
    sdk.release()


def _read_script(path: Path) -> str:
    try:
        contents = _cott_fixture_read(path)
    except CottContractViolation as error:
        if error.message != "fixture adapters are inactive":
            return ""
        try:
            contents = path.read_bytes()
        except OSError:
            return ""
    except OSError:
        return ""
    try:
        return contents.decode("utf-8")
    except UnicodeDecodeError:
        return ""


def _script_chunks(script: str, sqlite: bool) -> list[str]:
    chunks: list[str] = []
    lines: list[str] = []
    for line in script.splitlines():
        if line.startswith(".") or (sqlite and line in ("/", "go")):
            if lines:
                chunks.append("\n".join(lines))
                lines = []
            if line.startswith("."):
                chunks.append(line)
        else:
            lines.append(line)
    if lines:
        chunks.append("\n".join(lines))
    return chunks


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _sql_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _path_stem(value: str) -> str:
    if value.startswith("file:"):
        return Path(urllib.parse.urlsplit(value).path).stem
    return Path(value).stem


def _dot_command(command: str, sqlite: bool) -> str:
    parts = command.split()
    if not parts:
        return ""
    args = parts[1:]
    if parts[0] == ".open":
        paths = [value for value in args if not value.startswith("--")]
        if sqlite:
            if not paths:
                return "attach '';"
            path = paths[0]
            return f"attach {_sql_literal(path)} as {_sql_identifier(_path_stem(path))};"
        if not paths:
            return "attach ':memory:'; use memory;"
        path = paths[0]
        alias = _sql_identifier(_path_stem(path))
        read_only = " (READ_ONLY)" if "--readonly" in args else ""
        return f"attach {_sql_literal(path)}{read_only} as {alias}; use {alias};"
    if sqlite and parts[0] == ".load" and args:
        entry = ", " + _sql_literal(args[1]) if len(args) > 1 else ""
        return f"select load_extension({_sql_literal(args[0])}{entry});"
    return ""


def _script_pieces(script: str, sqlite: bool) -> list[str]:
    pieces: list[str] = []
    for chunk in _script_chunks(script, sqlite):
        command = _dot_command(chunk, sqlite) if chunk.startswith(".") else chunk
        pieces.extend(piece for piece in command.split(";") if piece.strip())
    return pieces


def _init_message(count: int, path: Path) -> str:
    if count == 0:
        return ""
    return f"Executed {count} {'command' if count == 1 else 'commands'} from {path}"


def _resolved_path(path: str) -> str:
    if path.startswith("file:"):
        parsed = urllib.parse.urlsplit(path)
        return Path(urllib.parse.unquote(parsed.path)).resolve().as_posix()
    return Path(path).resolve().as_posix()


def _sqlite_uri(path: str, read_only: bool, mode: str | None) -> str:
    if path == ":memory:":
        if read_only or mode == "ro":
            return "file::memory:?mode=ro"
        return path
    base = path if path.startswith("file:") else Path(path).resolve().as_uri()
    if read_only:
        return base + "?mode=ro"
    if mode is not None:
        return base + "?mode=" + mode
    return base


def _sqlite_isolation(value: str | None) -> Literal["DEFERRED", "IMMEDIATE", "EXCLUSIVE"] | None:
    upper = (value or "DEFERRED").upper()
    if upper == "IMMEDIATE":
        return "IMMEDIATE"
    if upper == "EXCLUSIVE":
        return "EXCLUSIVE"
    if upper in ("NONE", "AUTOCOMMIT"):
        return None
    return "DEFERRED"


def _built_id(adapter: str, user: str | None, host: str | None, port: str | None, database: str | None) -> str:
    return f"{adapter}://" + (f"{user}@" if user else "") + (host or "") + (f":{port}" if port else "") + (f"/{database}" if database else "")


def _connection_id(conn_str: list[str], adapter: str, user: str | None, host: str | None, port: str | None, database: str | None) -> str:
    return conn_str[0] if len(conn_str) == 1 else _built_id(adapter, user, host, port, database)


def _duck_error(error: duckdb.Error, paths: list[str]) -> ConnectionError:
    message = str(error)
    if "sqlite_scanner" in message:
        message = ("DuckDB raised the following error when trying to open one or more database files:\n"
                   f"---\n{message}\n---\n\nDid you mean to use Harlequin's sqlite adapter instead? "
                   f"Maybe try:\nharlequin -a sqlite {' '.join(paths)}")
    return _failed(_DUCK_TITLE, message)


def _open_duckdb(conn_str: list[str], read_only: bool, settings: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    paths = conn_str if conn_str and conn_str != [""] else [":memory:"]
    primary = paths[0]
    database = primary
    token = _text(settings, "md_token")
    if token is not None:
        database += "?token=" + token
    if _flag(settings, "md_saas"):
        database += "?saas_mode=true"
    unsigned = "true" if _flag(settings, "allow_unsigned_extensions") else "false"
    try:
        driver = duckdb.connect(database=database, read_only=read_only, config={"allow_unsigned_extensions": unsigned})
    except duckdb.Error as error:
        return _duck_error(error, conn_str)
    cleanup.callback(lambda: _close_resource(driver))
    try:
        for path in paths[1:]:
            driver.execute(f"attach {_sql_literal(path)}" + (" (READ_ONLY)" if read_only else ""))
    except duckdb.Error as error:
        return _duck_error(error, conn_str)
    try:
        repository = _text(settings, "custom_extension_repo")
        if repository is not None:
            driver.execute(f"SET custom_extension_repository={_sql_literal(repository)};")
        force = _flag(settings, "force_install_extensions")
        for extension in _values(settings, "extension"):
            driver.install_extension(extension, force_install=force)
            driver.load_extension(extension)
    except duckdb.Error as error:
        return _failed("DuckDB couldn't install or load your extension.", str(error))
    message = ""
    if not _flag(settings, "no_init"):
        init_path = Path(_text(settings, "init_path") or "~/.duckdbrc").expanduser()
        count = 0
        try:
            for piece in _script_pieces(_read_script(init_path), False):
                driver.execute(piece)
                count += 1
        except duckdb.Error as error:
            return _failed("DuckDB could not execute your initialization script.", f"Attempted to execute script at {init_path}\n{error}")
        message = _init_message(count, init_path)
    identity = "" if paths == [":memory:"] else ",".join(sorted(_resolved_path(path) for path in paths))
    return driver, identity, message, f"Connected to database `{primary}`"


def _open_sqlite(conn_str: list[str], read_only: bool, settings: dict[str, SettingValue], numbers: dict[str, int | float], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    mode = _text(settings, "mode")
    if read_only and mode is not None and mode != "ro":
        return _invalid(_INIT_TITLE, "Cannot specify readonly flag and a connection mode.")
    paths = [":memory:"] if not conn_str or conn_str == [""] or mode == "memory" else conn_str
    uris = [_sqlite_uri(path, read_only, mode) for path in paths]
    try:
        driver = sqlite3.connect(uris[0], timeout=float(numbers.get("lock_timeout") or 5.0),
                                 detect_types=_integer(numbers, "detect_types") or 0,
                                 isolation_level=_sqlite_isolation(_text(settings, "isolation_level")),
                                 cached_statements=_integer(numbers, "cached_statements") or 128,
                                 check_same_thread=False, uri=True, autocommit=True)
    except sqlite3.Error as error:
        return _failed(_SQLITE_TITLE, str(error))
    cleanup.callback(lambda: _close_resource(driver))
    try:
        cursor = driver.execute("pragma database_list")
        cursor.close()
    except sqlite3.DatabaseError as error:
        return _failed(_SQLITE_TITLE, f"{error}\n\nThe file at {paths[0]} does not look like a SQLite database. If it is a DuckDB database, try: harlequin -a duckdb {paths[0]}")
    try:
        for path, uri in zip(paths[1:], uris[1:]):
            alias = "memory" if path == ":memory:" else _path_stem(path)
            cursor = driver.execute(f"attach database {_sql_literal(uri)} as {_sql_identifier(alias)}")
            cursor.close()
    except sqlite3.Error as error:
        return _failed(_SQLITE_TITLE, str(error))
    extensions = _values(settings, "extension")
    if extensions:
        try:
            driver.enable_load_extension(True)
            for extension in extensions:
                driver.load_extension(extension)
        except (sqlite3.Error, AttributeError) as error:
            return _failed("SQLite couldn't load your extension.", str(error))
    message = ""
    if not _flag(settings, "no_init"):
        init_path = Path(_text(settings, "init_path") or "~/.sqliterc").expanduser()
        count = 0
        try:
            for piece in _script_pieces(_read_script(init_path), True):
                cursor = driver.execute(piece)
                cursor.close()
                count += 1
        except sqlite3.Error as error:
            return _failed("SQLite could not execute your initialization script.", f"Attempted to execute script at {init_path}\n{error}")
        message = _init_message(count, init_path)
    identity = "" if paths == [":memory:"] or (len(paths) == 1 and paths[0].startswith("file::memory:")) else ",".join(sorted(_resolved_path(path) for path in paths))
    return driver, identity, message, f"Connected to database `{paths[0]}`"


def _open_postgres(conn_str: list[str], read_only: bool, settings: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    if len(conn_str) > 1:
        return _invalid(_INIT_TITLE, f"Cannot provide multiple connection strings to the Postgres adapter. {tuple(conn_str)}")
    options: dict[str, str] = {}
    for key in _PG_KEYS.split():
        value = _text(settings, key)
        if value is not None:
            options[key] = value
    try:
        conninfo = psycopg.conninfo.make_conninfo(conn_str[0] if conn_str else "", **options)
        driver: psycopg.Connection[tuple[object, ...]] = psycopg.connect(conninfo, autocommit=True)
    except psycopg.Error as error:
        return _failed(_PG_TITLE, str(error))
    cleanup.callback(lambda: _close_resource(driver))
    if read_only:
        try:
            with driver.cursor() as cursor:
                cursor.execute("set session characteristics as transaction read only;")
                cursor.execute("select current_setting('default_transaction_read_only')")
                row = cursor.fetchone()
        except psycopg.Error as error:
            return _failed(_PG_TITLE, str(error))
        if row is None or row[0] != "on":
            return _failed("Harlequin could not open a read-only connection to Postgres.", "The server did not accept a read-only session, so writes would not be prevented.")
    identity = _connection_id(conn_str, "postgres", _text(settings, "user"), _text(settings, "host"), _text(settings, "port"), _text(settings, "dbname"))
    return driver, identity, "", "Connected to Postgres"


def _open_mysql(conn_str: list[str], read_only: bool, settings: dict[str, SettingValue], numbers: dict[str, int | float], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    if conn_str:
        return _invalid(_INIT_TITLE, f"Cannot provide a DSN to the MySQL adapter. Got:\n{tuple(conn_str)}")
    kwargs: dict[str, object] = {"autocommit": True}
    for key in ("host", "unix_socket", "database", "user", "password2", "password3", "ssl_ca", "ssl_cert", "ssl_key", "openid_token_file"):
        value = _text(settings, key)
        if value is not None:
            kwargs[key] = value
    password = _text(settings, "password1")
    if password is not None:
        kwargs["password"] = password
    port = _integer(numbers, "port")
    if port is not None:
        kwargs["port"] = port
    timeout = _integer(numbers, "connection_timeout")
    if timeout is not None:
        kwargs["connection_timeout"] = timeout
    disabled = settings.get("ssl_disabled")
    if isinstance(disabled, SettingValue_Flag):
        kwargs["ssl_disabled"] = disabled.value
    cleartext = settings.get("enable_cleartext_plugin")
    if isinstance(cleartext, SettingValue_Flag):
        kwargs["allow_local_infile"] = cleartext.value
    sdk: Any = mysql.connector
    driver: Any = sdk.connect(**kwargs)
    cleanup.callback(lambda: _close_resource(cast(object, driver)))
    if read_only:
        cursor: Any = driver.cursor()
        try:
            cursor.execute("set session transaction read only")
        finally:
            cursor.close()
    identity = _built_id("mysql", _text(settings, "user"), _text(settings, "host"), _text(settings, "port"), _text(settings, "database"))
    return cast(object, driver), identity, "", "Connected to MySQL"


def _open_odbc(conn_str: list[str], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    if len(conn_str) != 1:
        return _invalid(_ODBC_INIT_TITLE, f"The ODBC adapter expects exactly one connection string. It received:\n{tuple(conn_str)}")
    sdk: Any = pyodbc
    driver: Any = sdk.connect(conn_str[0], autocommit=True)
    cleanup.callback(lambda: _close_resource(cast(object, driver)))
    return cast(object, driver), conn_str[0], "", "Connected to ODBC data source"


def _open_bigquery(conn_str: list[str], settings: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    project = _text(settings, "project")
    sdk: Any = bigquery
    driver: Any = sdk.Client(project=project, location=_text(settings, "location"))
    cleanup.callback(lambda: _close_resource(cast(object, driver)))
    identity = _connection_id(conn_str, "bigquery", None, None, None, project)
    return cast(object, driver), identity, "", "Connected to BigQuery"


def _open_trino(conn_str: list[str], settings: dict[str, SettingValue], numbers: dict[str, int | float], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    kwargs: dict[str, object] = {}
    for key in ("host", "user", "catalog", "schema"):
        value = _text(settings, key)
        if value is not None:
            kwargs[key] = value
    port = _integer(numbers, "port")
    if port is not None:
        kwargs["port"] = port
    auth = _text(settings, "require_auth")
    auth_sdk: Any = trino.auth
    if auth == "password":
        kwargs["auth"] = cast(object, auth_sdk.BasicAuthentication(_text(settings, "user"), _text(settings, "password")))
        kwargs["http_scheme"] = "https"
        kwargs["verify"] = _text(settings, "sslcert") or False
    elif auth == "google":
        google_sdk: Any = google.auth
        request_sdk: Any = google.auth.transport.requests
        credentials: Any = google_sdk.default()[0]
        credentials.refresh(request_sdk.Request())
        kwargs["auth"] = cast(object, auth_sdk.JWTAuthentication(credentials.token))
        kwargs["http_scheme"] = "https"
        kwargs["verify"] = True
    sdk: Any = trino.dbapi
    driver: Any = sdk.connect(**kwargs)
    cleanup.callback(lambda: _close_resource(cast(object, driver)))
    identity = _connection_id(conn_str, "trino", _text(settings, "user"), _text(settings, "host"), _text(settings, "port"), _text(settings, "catalog"))
    return cast(object, driver), identity, "", "Connected to Trino"


def _m2m_token(host: str, client_id: str, client_secret: str) -> str:
    authorization = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    request = urllib.request.Request(f"https://{host}/oidc/v1/token", data=b"grant_type=client_credentials&scope=all-apis", headers={"Authorization": f"Basic {authorization}", "Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urllib.request.urlopen(request) as response:
        body: object = cast(object, json.loads(response.read()))
    if not isinstance(body, dict):
        raise ValueError("The Databricks token endpoint returned an unexpected reply.")
    token = cast(dict[str, object], body).get("access_token")
    if not isinstance(token, str) or token == "":
        raise ValueError("The Databricks token endpoint did not return an access token.")
    return token


def _open_databricks(conn_str: list[str], settings: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    host = _text(settings, "server_hostname")
    client_id = _text(settings, "client_id")
    client_secret = _text(settings, "client_secret")
    if (client_id is None) != (client_secret is None):
        return _invalid(_INIT_TITLE, "To use OAuth M2M you must supply both --client-id and --client-secret CLI arguments.")
    kwargs: dict[str, object] = {"server_hostname": host, "http_path": _text(settings, "http_path")}
    token = _text(settings, "access_token")
    username = _text(settings, "username")
    auth_type = _text(settings, "auth_type")
    if client_id is not None and client_secret is not None:
        kwargs["access_token"] = _m2m_token(host or "", client_id, client_secret)
    elif token is not None:
        kwargs["access_token"] = token
    elif username is not None:
        kwargs["username"] = username
        kwargs["password"] = _text(settings, "password")
    elif auth_type is not None:
        kwargs["auth_type"] = auth_type
    sdk: Any = databricks.sql
    driver: Any = sdk.connect(**kwargs)
    cleanup.callback(lambda: _close_resource(cast(object, driver)))
    message = ""
    if not _flag(settings, "no_init"):
        init_path = Path(_text(settings, "init_path") or "~/.databricksrc").expanduser()
        count = 0
        try:
            with contextlib.ExitStack() as cursors:
                cursor: Any = driver.cursor()
                cursors.callback(lambda: _close_resource(cast(object, cursor)))
                for piece in _read_script(init_path).split(";"):
                    if piece.strip():
                        cursor.execute(piece)
                        count += 1
        except Exception as error:
            return _failed("Databricks errored while executing your initialization script.", str(error))
        message = _init_message(count, init_path)
    identity = _connection_id(conn_str, "databricks", username, host, None, _text(settings, "http_path"))
    return cast(object, driver), identity, message, "Connected to Databricks"


def _adbc_connect(driver_type: str, uri: str, kwargs: dict[str, str]) -> object:
    if driver_type == "flightsql":
        sdk: Any = adbc_driver_flightsql.dbapi
        return cast(object, sdk.connect(uri, db_kwargs=kwargs))
    if driver_type == "postgresql":
        sdk = adbc_driver_postgresql.dbapi
        return cast(object, sdk.connect(uri, db_kwargs=kwargs))
    if driver_type == "snowflake":
        sdk = adbc_driver_snowflake.dbapi
        return cast(object, sdk.connect(uri, db_kwargs=kwargs))
    if driver_type == "sqlite":
        sdk = adbc_driver_sqlite.dbapi
        return cast(object, sdk.connect(uri, db_kwargs=kwargs))
    if driver_type == "duckdb":
        sdk = adbc_driver_duckdb.dbapi
        return cast(object, sdk.connect(uri, db_kwargs=kwargs))
    raise ValueError(f"Unknown ADBC driver type: {driver_type}")


def _open_adbc(conn_str: list[str], settings: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    if len(conn_str) != 1:
        return _invalid(_ADBC_INIT_TITLE, f"The ADBC adapter expects exactly one connection string. It received:\n{tuple(conn_str)}")
    driver_type = _text(settings, "driver_type")
    driver_path = _text(settings, "driver_path")
    if driver_type is None and driver_path is None:
        return _invalid(_ADBC_INIT_TITLE, "The ADBC adapter expects either at least a driver type or a driver path and neither was provided.")
    kwargs: dict[str, str] = {}
    for pair in (_text(settings, "db_kwargs_str") or "").split(";"):
        if "=" in pair:
            key, _, value = pair.partition("=")
            kwargs[key.strip()] = value.strip()
    if driver_path is not None:
        sdk: Any = adbc_driver_manager.dbapi
        driver: object = cast(object, sdk.connect(driver=driver_path, db_kwargs={**kwargs, "uri": conn_str[0]}))
    else:
        driver = _adbc_connect(driver_type or "", conn_str[0], kwargs)
    cleanup.callback(lambda: _close_resource(driver))
    return driver, conn_str[0], "", "Connected via ADBC"


def _open_cassandra(conn_str: list[str], settings: dict[str, SettingValue], numbers: dict[str, int | float], level: str, cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    host = _text(settings, "host")
    port = _integer(numbers, "port")
    kwargs: dict[str, object] = {"port": port if port is not None else 9042}
    protocol = _integer(numbers, "protocol_version")
    if protocol is not None:
        kwargs["protocol_version"] = protocol
    user = _text(settings, "user")
    if user is not None:
        auth_sdk: Any = cassandra.auth
        kwargs["auth_provider"] = cast(object, auth_sdk.PlainTextAuthProvider(username=user, password=_text(settings, "password")))
    sdk: Any = cassandra.cluster
    cluster: Any = sdk.Cluster([host or "localhost"], **kwargs)
    cleanup.callback(lambda: _shutdown_resource(cast(object, cluster)))
    keyspace = _text(settings, "keyspace")
    driver: Any = cluster.connect(keyspace)
    cleanup.callback(lambda: _shutdown_resource(cast(object, driver)))
    consistency: Any = cassandra.ConsistencyLevel
    driver.default_consistency_level = consistency.name_to_value[level]
    identity = _connection_id(conn_str, "cassandra", user, host, _text(settings, "port"), keyspace)
    return cast(object, driver), identity, "", "Connected to Cassandra"


def _open_nebula(conn_str: list[str], settings: dict[str, SettingValue], numbers: dict[str, int | float], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    host = _text(settings, "host") or "127.0.0.1"
    configured_port = _integer(numbers, "port")
    port = configured_port if configured_port is not None else 9669
    user = _text(settings, "user") or "root"
    config_sdk: Any = nebula3.Config
    network_sdk: Any = nebula3.gclient.net
    pool: Any = network_sdk.ConnectionPool()
    cleanup.callback(lambda: _close_resource(cast(object, pool)))
    config: Any = config_sdk.Config()
    if not bool(cast(object, pool.init([(host, port)], config))):
        return _failed(_NEBULA_TITLE, f"Could not initialize a connection pool to {host}:{port}.")
    driver: Any = pool.get_session(user, _text(settings, "password") or "nebula")
    cleanup.callback(lambda: _release_resource(cast(object, driver)))
    identity = _connection_id(conn_str, "nebulagraph", user, host, str(port), None)
    return cast(object, driver), identity, "", "Connected to NebulaGraph"


def _chdb_uri(value: str) -> str:
    if value in ("", ":memory:", "chdb://:memory:", "chdb::memory:"):
        return "chdb://"
    if "://" in value or value.startswith(("chdb:", "file:", "local:")):
        return value
    return "file:" + Path(value).resolve().as_posix()


def _open_chdb(conn_str: list[str], read_only: bool, settings: dict[str, SettingValue], cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    candidates = [item for item in conn_str if item.strip()]
    for key in ("uri", "path"):
        value = _text(settings, key)
        if value is not None and value.strip():
            candidates.append(value)
    if len(candidates) > 1:
        return _invalid(_INIT_TITLE, "Pass only one of a positional database path, --path, or --uri.")
    uri = _chdb_uri(candidates[0] if candidates else "")
    sdk: Any = adbc_driver_chdb.dbapi
    driver: object = cast(object, sdk.connect(uri, conn_kwargs={"adbc.connection.readonly": "true"})) if read_only else cast(object, sdk.connect(uri))
    cleanup.callback(lambda: _close_resource(driver))
    return driver, uri, "", f"Connected to chDB `{uri}`"


def _dispatch(variant: str, conn_str: list[str], read_only: bool, settings: dict[str, SettingValue], numbers: dict[str, int | float], level: str, cleanup: contextlib.ExitStack[bool | None]) -> tuple[object, str, str, str] | ConnectionError:
    if variant == "DuckDb":
        return _open_duckdb(conn_str, read_only, settings, cleanup)
    if variant == "Sqlite":
        return _open_sqlite(conn_str, read_only, settings, numbers, cleanup)
    if variant == "Postgres":
        return _open_postgres(conn_str, read_only, settings, cleanup)
    if variant == "MySql":
        return _open_mysql(conn_str, read_only, settings, numbers, cleanup)
    if variant == "Odbc":
        return _open_odbc(conn_str, cleanup)
    if variant == "BigQuery":
        return _open_bigquery(conn_str, settings, cleanup)
    if variant == "Trino":
        return _open_trino(conn_str, settings, numbers, cleanup)
    if variant == "Databricks":
        return _open_databricks(conn_str, settings, cleanup)
    if variant == "Adbc":
        return _open_adbc(conn_str, settings, cleanup)
    if variant == "Cassandra":
        return _open_cassandra(conn_str, settings, numbers, level, cleanup)
    if variant == "NebulaGraph":
        return _open_nebula(conn_str, settings, numbers, cleanup)
    return _open_chdb(conn_str, read_only, settings, cleanup)


def connect(request: ConnectionRequest) -> Result[Connection, ConnectionError]:
    variant, display, title = _names(request.adapter)
    if request.read_only and variant not in ("DuckDb", "Sqlite", "Postgres", "MySql", "Chdb"):
        return Err(error=ConnectionError_ReadOnlyUnsupported(adapter=display))
    settings: dict[str, SettingValue] = {}
    for setting in request.settings:
        settings[setting.name.replace("-", "_")] = setting.value
    numbers: dict[str, int | float] = {}
    for key in _numeric_keys(variant):
        value = settings.get(key)
        if not isinstance(value, SettingValue_Text):
            continue
        raw = value.value
        try:
            if key == "lock_timeout":
                number = float(raw)
                if not math.isfinite(number):
                    raise ValueError(f"could not convert string to float: {raw!r}")
                numbers[key] = number
            else:
                numbers[key] = int(raw)
        except ValueError as error:
            return Err(error=_invalid(_INIT_TITLE, f"{display} adapter received bad config value: {error}"))
    level = (_text(settings, "consistency_level") or "LOCAL_ONE").upper()
    if level not in _CASS_LEVELS.split(","):
        level = "LOCAL_ONE"
    conn_str = [item for item in request.conn_str]
    try:
        with contextlib.ExitStack() as cleanup:
            try:
                _cott_fixture_database("connect")
            except CottContractViolation as error:
                if error.message != "fixture adapters are inactive":
                    raise
            opened = _dispatch(variant, conn_str, request.read_only, settings, numbers, level, cleanup)
            if not isinstance(opened, tuple):
                return Err(error=opened)
            driver, identity, message, details = opened
            modes: list[str] = []
            current: str | None = None
            transaction: Some[TransactionMode] | Nothing = Nothing()
            if variant in ("Sqlite", "Postgres"):
                modes = ["Auto", "Manual"]
                current = "Auto"
                transaction = Some(value=TransactionMode(label=current, can_commit=False, can_rollback=False))
            elif variant == "Cassandra":
                modes = [name[:10] for name in _CASS_LEVELS.split(",")]
                current = level[:10]
                transaction = Some(value=TransactionMode(label=current, can_commit=False, can_rollback=False))
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
            connection = Connection(adapter=request.adapter, connection_id=identity, init_message=message,
                                    driver_details=details, read_only=request.read_only, transaction_mode=transaction,
                                    session=Opaque(tag="harlequin.session", value=payload))
            payload["cleanup"] = cleanup.pop_all()
            return Ok(value=connection)
    except CottContractViolation as error:
        cause = error.__cause__
        return Err(error=_failed(title, str(cause) if isinstance(cause, OSError) else error.message))
    except Exception as error:
        return Err(error=_failed(title, str(error)))
