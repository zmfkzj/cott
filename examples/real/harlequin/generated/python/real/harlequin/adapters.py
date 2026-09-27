from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_unique_by

from real.harlequin.adapters_types import AdapterDescriptor, AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Chdb, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_Postgres, AdapterKind_Sqlite, AdapterKind_Trino, AdapterOption, AdapterSetting, Connection, ConnectionError, ConnectionError_Failed, ConnectionError_InvalidOption, ConnectionError_ReadOnlyUnsupported, ConnectionRequest, ExecutedStatement, InteractionPlan, InteractionPlan_Execute, InteractionPlan_InsertChildNames, InteractionPlan_InsertText, InteractionPlan_NewBuffer, InteractionPlan_NewBufferFromQuery, OptionKind, OptionKind_Choice, OptionKind_FilePath, OptionKind_Flag, OptionKind_Repeated, OptionKind_Text, PendingResult, QueryError, QueryError_Failed, QueryFailure, SessionHandle, SettingValue, SettingValue_Flag, SettingValue_Text, SettingValue_Values, TransactionMode
from real.harlequin.catalog_types import CatalogEntry
from real.harlequin.results_types import ColumnInfo, ResultSet

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def adapter_descriptors() -> CottList[AdapterDescriptor]:
    """Every shipped adapter, in this order. Columns: kind | name | display_name |
distribution | read_only | cancel | catalog_search | validate_sql | details.
DuckDb | duckdb | DuckDB | harlequin | true | true | true | true | This is a DuckDB adapter part of Harlequin core.
Sqlite | sqlite | SQLite | harlequin | true | true | true | false | This is an SQLite adapter part of Harlequin core.
Postgres | postgres | PostgreSQL | harlequin-postgres | true | true | true | false | A Harlequin adapter for Postgres.
MySql | mysql | MySQL | harlequin-mysql | true | true | true | false | A Harlequin adapter for MySQL and MariaDB.
Odbc | odbc | ODBC | harlequin-odbc | false | false | false | false | A Harlequin adapter for ODBC data sources.
BigQuery | bigquery | BigQuery | harlequin-bigquery | false | false | false | false | A Harlequin adapter for Google BigQuery.
Trino | trino | Trino | harlequin-trino | false | false | false | false | A Harlequin adapter for Trino.
Databricks | databricks | Databricks | harlequin-databricks | false | true | false | false | A Harlequin adapter for Databricks.
Adbc | adbc | ADBC | harlequin-adbc | false | false | false | false | A Harlequin adapter for ADBC drivers.
Cassandra | cassandra | Cassandra | harlequin-cassandra | false | false | false | false | A Harlequin adapter for Apache Cassandra.
NebulaGraph | nebulagraph | NebulaGraph | harlequin-nebulagraph | false | false | false | false | A Harlequin adapter for NebulaGraph.
Chdb | chdb | chDB | harlequin-chdb | true | true | true | false | A Harlequin adapter for chDB, in-process ClickHouse."""
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/adapter_descriptors.py", "feb43c4d584f144748b97b5c749c567618ba5cddd985f7b56a3fd5d5fbe17d08", "adapter_descriptors", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.adapter_descriptors")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.adapter_descriptors"
        if _error.span is None:
            _error.span = {"end_byte":9616,"end_column":1,"end_line":239,"start_byte":7797,"start_column":1,"start_line":216}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.adapter_descriptors", phase="implementation-call", span={"end_byte":9616,"end_column":1,"end_line":239,"start_byte":7797,"start_column":1,"start_line":216}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.adapter_descriptors", phase="implementation-call", span={"end_byte":9616,"end_column":1,"end_line":239,"start_byte":7797,"start_column":1,"start_line":216}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[AdapterDescriptor], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) == 12)), "real.harlequin.adapters.adapter_descriptors", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.adapter_descriptors", clause="ensures:1", phase="ensures", span={"end_byte":9544,"end_column":29,"end_line":234,"start_byte":9520,"start_column":5,"start_line":234}, expected="true", actual="false")
        if not (_cott_contract_condition((_cott_unique_by(_result, "name")), "real.harlequin.adapters.adapter_descriptors", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.adapter_descriptors", clause="ensures:2", phase="ensures", span={"end_byte":9598,"end_column":54,"end_line":235,"start_byte":9549,"start_column":5,"start_line":235}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[AdapterDescriptor], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def find_adapter(name: str) -> Option[AdapterDescriptor]:
    """The descriptor from adapter_descriptors whose name equals name compared
ignoring ASCII case."""
    name = _cott_normalize_f32_abi(name, str, path="$.name")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/find_adapter.py", "b0f01919c452042f67bfd19a8e6961d9dd962a35025b94a17e0a567aa3ac3f0b", "find_adapter", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.find_adapter")
        _result = _implementation(name)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.find_adapter"
        if _error.span is None:
            _error.span = {"end_byte":9811,"end_column":1,"end_line":247,"start_byte":9616,"start_column":1,"start_line":239}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.find_adapter", phase="implementation-call", span={"end_byte":9811,"end_column":1,"end_line":247,"start_byte":9616,"start_column":1,"start_line":239}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.find_adapter", phase="implementation-call", span={"end_byte":9811,"end_column":1,"end_line":247,"start_byte":9616,"start_column":1,"start_line":239}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Option[AdapterDescriptor], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Option[AdapterDescriptor], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def adapter_options(kind: AdapterKind) -> CottList[AdapterOption]:
    """The declared options of each adapter, in declaration order. Columns: name |
short_decls | kind | default | label | description. Kinds: text, flag,
repeated, path, choice(...). No option is secret except where "secret" is
written. Labels are the name with "-"/"_" replaced by spaces and each word
capitalized unless given.
DuckDb:
  init-path | -i -init | path | Nothing | Init Path | The path to an initialization script. On startup, Harlequin will execute the commands in the script against the attached database.
  no-init | | flag | Nothing | No Init | Start Harlequin without executing the initialization script.
  allow-unsigned-extensions | -u -unsigned | flag | Nothing | Allow Unsigned Extensions | Allow loading unsigned extensions
  extension | -e | repeated | Nothing | Extension | Install and load the named DuckDB extension when starting Harlequin. To install multiple extensions, repeat this option.
  force-install-extensions | | flag | Nothing | Force Install Extensions | Force install all extensions passed with -e.
  custom-extension-repo | | text | Nothing | Custom Extension Repo | A value to pass to DuckDB's custom_extension_repository variable. Will be set before installing any extensions that are passed using -e.
  md_token | | text (secret) | Nothing | Md Token | MotherDuck Token. Pass your MotherDuck service token in this option, or set the `motherduck_token` environment variable.
  md_saas | | flag | Nothing | Md Saas | Run MotherDuck in SaaS mode (no local privileges).
Sqlite:
  init-path | -i -init | path | Nothing | Init Path | (as DuckDb, for SQLite)
  no-init | | flag | Nothing | No Init | Start Harlequin without executing the initialization script.
  mode | -mode -m | choice(ro, rw, rwc, memory) | rwc | Mode | The mode parameter may be set to either 'ro', 'rw', 'rwc', or 'memory'.
  lock-timeout | | text | Nothing | Lock Timeout | How many seconds the connection should wait before raising an OperationalError when a table is locked. Default five seconds.
  detect-types | | text | Nothing | Detect Types | Control whether and how data types not natively supported by SQLite are looked up (PARSE_DECLTYPES | PARSE_COLNAMES as an int). By default (0), type detection is disabled.
  cached-statements | | text | Nothing | Cached Statements | The number of statements that sqlite3 should internally cache for this connection. By default, 128 statements.
  extension | -e | repeated | Nothing | Extension | Load the SQLite extension from the passed path when starting Harlequin. To install multiple extensions, repeat this option.
Postgres:
  host | -h | text | localhost | Host | Specifies the host name of the machine on which the server is running.
  port | -p | text | 5432 | Port | Port number to connect to at the server host.
  dbname | -d | text | postgres | Database | The database name to use when connecting with the Postgres server.
  user | -u --username -U | text | Nothing | User | PostgreSQL user name to connect as.
  password | | text | Nothing | Password | Password to be used if the server demands password authentication.
  passfile | | path | Nothing | Passfile | Specifies the name of the file used to store passwords.
  require_auth | | choice(password, md5, gss, sspi, scram-sha-256, none) | Nothing | Require Auth | Specifies the authentication method that the client requires from the server.
  channel_binding | | choice(require, prefer, disable) | Nothing | Channel Binding | This option controls the client's use of channel binding.
  connect_timeout | | text | Nothing | Connect Timeout | Maximum time to wait while connecting, in seconds (write as a decimal integer).
  sslmode | | choice(disable, allow, prefer, require, verify-ca, verify-full) | prefer | SSL Mode | Determines whether or with what priority a secure SSL TCP/IP connection will be negotiated with the server.
  sslcert | | path | ~/.postgresql/postgresql.crt | SSL Cert | Specifies the file name of the client SSL certificate.
  sslkey | | text | Nothing | SSL Key | Specifies the location for the secret key used for the client certificate.
MySql:
  host | -h | text | localhost | Host | The host name or IP address of the MySQL server.
  port | -p | text | 3306 | Port | The TCP/IP port of the MySQL server. Must be an integer.
  unix_socket | | text | Nothing | Unix Socket | The location of the Unix socket file.
  database | -d -db | text | postgres | Database | The database (schema) name to use when connecting with the MySQL server.
  user | -u --username -U | text | Nothing | User | The user name used to authenticate with the MySQL server.
  password | --password1 | text | Nothing | Password | The password to authenticate the user with the MySQL server.
  password2 | | text | Nothing | Password 2 | For Multi-Factor Authentication (MFA); password for the second authentication factor.
  password3 | | text | Nothing | Password 3 | For Multi-Factor Authentication (MFA); password for the third authentication factor.
  connection_timeout | --connect_timeout | text | Nothing | Connection Timeout | Timeout for the TCP and Unix socket connections. Must be an integer.
  ssl-ca | | path | Nothing | SSL CA | File containing the SSL certificate authority.
  ssl-cert | --sslcert | path | Nothing | SSL Cert | File containing the SSL certificate file.
  ssl-disabled | | flag | Nothing | SSL Disabled | True disables SSL/TLS usage.
  ssl-key | --sslkey | path | Nothing | SSL Key | File containing the SSL key.
  openid-token-file | --oid | path | Nothing | OpenID Token File | File containing the OpenID Connect token.
  pool-size | -n | text | 5 | Pool Size | The number of connections to open in the pool. Must be an integer.
  enable-cleartext-plugin | | flag | Nothing | Enable Cleartext Plugin | Enables the mysql_clear_password plugin.
Odbc: no options.
BigQuery:
  project | -p | text | Nothing | Project | The GCP project ID to use when connecting to BigQuery.
  location | -l | text | Nothing | Location | The GCP location (region) to use for queries and catalog.
Trino:
  host | -h | text | localhost | Host | Specifies the host name of the machine on which the server is running.
  port | -p | text | 8080 | Port | Port number to connect to at the server host.
  user | -u --username -U | text | trino | User | Trino user name to connect as.
  password | | text | Nothing | Password | Password to be used if the server demands password authentication.
  require_auth | | choice(password, google, none) | Nothing | Require Auth | Specifies the authentication method that the client requires from the server.
  sslcert | | path | Nothing | SSL Cert | Specifies the file name of the client SSL certificate.
  schema | | text | Nothing | Schema | Specifies the schema to browse.
  catalog | | text | Nothing | Catalog | Specifies the catalog to browse.
Databricks:
  server-hostname | | text | Nothing | Server Hostname | The Server Hostname value for your cluster or SQL warehouse.
  http-path | | text | Nothing | HTTP Path | The HTTP Path value for your cluster or SQL warehouse.
  access-token | | text | Nothing | Access Token | Your Databricks personal access token.
  username | | text | Nothing | Username | Your Databricks username (basic auth).
  password | | text | Nothing | Password | Your Databricks password (basic auth).
  auth-type | | choice(databricks-oauth, azure-oauth) | Nothing | Auth Type | The OAuth U2M flow to use.
  skip-legacy-indexing | | flag | Nothing | Skip Legacy Indexing | Do not index legacy (non Unity Catalog) metastores for the Data Catalog.
  client-id | | text | Nothing | Client ID | The OAuth M2M client id.
  client-secret | | text | Nothing | Client Secret | The OAuth M2M client secret.
  init-path | -i -init | path | Nothing | Init Path | The path to an initialization script (default ~/.databricksrc).
  no-init | | flag | Nothing | No Init | Start Harlequin without executing the initialization script.
Adbc:
  driver-type | | choice(flightsql, postgresql, snowflake, sqlite, duckdb) | Nothing | Driver Type | The ADBC driver package to use (adbc_driver_<type>).
  driver-path | | path | Nothing | Driver Path | The path to an ADBC driver shared library to load with the driver manager.
  db-kwargs-str | | text | Nothing | Database Kwargs | Driver options as semicolon-separated key=value pairs.
Cassandra:
  host | -h | text | localhost | Host | The contact point of the Cassandra cluster.
  port | -p | text | 9042 | Port | The native protocol port. Must be an integer.
  keyspace | -k | text | Nothing | Keyspace | The keyspace to use.
  user | -u --username | text | Nothing | User | The user name for plain-text authentication.
  password | | text | Nothing | Password | The password for plain-text authentication.
  protocol-version | -P | text | Nothing | Protocol Version | The native protocol version. Must be an integer.
  consistency-level | -C | choice(ANY, ONE, TWO, THREE, QUORUM, ALL, LOCAL_QUORUM, EACH_QUORUM, SERIAL, LOCAL_SERIAL, LOCAL_ONE) | LOCAL_ONE | Consistency Level | The default consistency level of queries.
NebulaGraph:
  host | -h | text | localhost | Host | The host of the NebulaGraph graphd service.
  port | -p | text | 9669 | Port | The port of the graphd service.
  user | -u | text | root | User | The user name.
  password | -pw | text | nebula | Password | The password.
Chdb:
  uri | | text | Nothing | URI | A chDB connection URI.
  path | -p | path | Nothing | Path | A directory holding a persistent chDB database.
  show-system | | flag | Nothing | Show System | Show the system, INFORMATION_SCHEMA and information_schema databases in the Data Catalog.
  catalog-search-limit | | text | 200 | Catalog Search Limit | The maximum number of catalog search matches per level. Must be an integer of at least 1."""
    kind = _cott_normalize_f32_abi(kind, AdapterKind, path="$.kind")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/adapter_options.py", "bd7d8c83e1b2f7be523c816b378729e769d0ca23085042db99132ae161a52081", "adapter_options", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.adapter_options")
        _result = _implementation(kind)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.adapter_options"
        if _error.span is None:
            _error.span = {"end_byte":20119,"end_column":1,"end_line":354,"start_byte":9811,"start_column":1,"start_line":247}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.adapter_options", phase="implementation-call", span={"end_byte":20119,"end_column":1,"end_line":354,"start_byte":9811,"start_column":1,"start_line":247}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.adapter_options", phase="implementation-call", span={"end_byte":20119,"end_column":1,"end_line":354,"start_byte":9811,"start_column":1,"start_line":247}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[AdapterOption], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((_cott_unique_by(_result, "name")), "real.harlequin.adapters.adapter_options", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.adapter_options", clause="ensures:1", phase="ensures", span={"end_byte":20101,"end_column":50,"end_line":350,"start_byte":20056,"start_column":5,"start_line":350}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[AdapterOption], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def connect(request: ConnectionRequest) -> Result[Connection, ConnectionError]:
    """Open and retain a live SDK session exactly as the corresponding Harlequin
adapter does, and return it with a SessionHandle holding the documented
payload, including its original "request". Settings are looked up by profile key (option name with "-" as "_");
Flag values are booleans, Repeated values lists, others text; unknown
settings are ignored (the command line and config validated them). Text
values that must be numbers are converted and a bad value is
InvalidOption("Harlequin could not initialize the selected adapter.", "{Name}
adapter received bad config value: {error}"). A read_only request for an
adapter whose descriptor does not implement read-only is
ReadOnlyUnsupported(name). A driver failure is Failed(title, message) with the
title below and the driver's message; the message never adds credentials that
the driver did not print. On any failure every acquired resource is closed.
connection_id: DuckDb, Sqlite: "" for in-memory, otherwise the sorted resolved
POSIX paths of conn_str joined by ","; Chdb: the normalized URI; others: the
single conn_str, or "{adapter}://{user}@{host}:{port}/{database}" built from
the options that exist ("" parts omitted).
DuckDb: conn_str empty or [""] means [":memory:"]. duckdb.connect(database=
primary + ("?token=" + md_token if md_token) + ("?saas_mode=true" if md_saas),
read_only=read_only, config={"allow_unsigned_extensions": "true"|"false"});
attach each further path with "attach '{db}'" plus " (READ_ONLY)" when
read_only. Connect errors (CatalogException, IOException) are Failed("DuckDB
couldn't connect to your database.", message), where a message mentioning
sqlite_scanner is replaced by "DuckDB raised the following error when trying
to open one or more database files:\\n---\\n{msg}\\n---\\n\\nDid you mean to use
Harlequin's sqlite adapter instead? Maybe try:\\nharlequin -a sqlite
{conn_str joined by spaces}". Then "SET custom_extension_repository='{repo}';"
when given, then install_extension(ext, force_install=force_install_extensions)
and load_extension(ext) for each extension (failure: Failed("DuckDB couldn't
install or load your extension.", message)). Then, unless no_init, run the init
script at init_path (default ~/.duckdbrc; a missing or unreadable file is an
empty script): lines starting with "." are single commands and other lines
group into SQL chunks between them; ".open" with no argument becomes "attach
':memory:'; use memory;", ".open [--readonly] PATH" becomes "attach 'PATH'[
(READ_ONLY)] as STEM; use STEM;", other dot commands are ignored; each chunk is
split on ";" and every nonblank piece executed. Failure: Failed("DuckDB could
not execute your initialization script.", "Attempted to execute script at
{path}\\n{error}"); success with n > 0 commands sets init_message "Executed {n}
command(s)" spelled "command" for 1 and "commands" otherwise, " from {path}".
driver_details "Connected to database `{primary}`". No transaction mode.
Sqlite: conn_str empty, [""] or mode "memory" means [":memory:"]. read_only
with a mode other than "ro" set explicitly is InvalidOption("Harlequin could
not initialize the selected adapter.", "Cannot specify readonly flag and a
connection mode."). Each path becomes a URI: "file:" URIs as given,
":memory:" as is, other paths the resolved file URI; append "?mode=ro" when
read_only else "?mode={mode}" when mode was given. sqlite3.connect(primary,
timeout=lock_timeout or 5.0, detect_types=int or 0, isolation_level
(DEFERRED default), cached_statements=int or 128, check_same_thread=False,
uri=True); then "pragma database_list" (a DatabaseError is Failed("Harlequin
could not connect to your SQLite database.", "{error}\\n\\nThe file at {path}
does not look like a SQLite database. If it is a DuckDB database, try:
harlequin -a duckdb {path}")); attach further paths "attach database '{uri}' as
{alias}" (alias: the path stem, "memory" for :memory:). Extensions:
enable_load_extension(True) then load_extension(path) each (Failed("SQLite
couldn't load your extension.", message)). Init script (default ~/.sqliterc,
unless no_init) as DuckDb, except lines that are exactly "/" or "go" also end
a SQL chunk, ".open PATH" becomes "attach 'PATH' as STEM;" (no argument:
"attach '';"), ".load FILE [ENTRY]" becomes "select load_extension('FILE'[,
'ENTRY']);", and failures are Failed("SQLite could not execute your
initialization script.", ...). The connection starts with autocommit True.
Transaction modes ["Auto", "Manual"], starting at Auto; Manual can commit and
roll back.
Postgres: at most one conn_str (a libpq conninfo or postgresql:// URI); more is
InvalidOption("Harlequin could not initialize the selected adapter.", "Cannot
provide multiple connection strings to the Postgres adapter. {tuple}"). Build
conninfo with psycopg.conninfo.make_conninfo(dsn, **options that are set) and
open psycopg.Connection with autocommit=True. When read_only, execute "set
session characteristics as transaction read only;" and require
current_setting('default_transaction_read_only') == 'on', else
Failed("Harlequin could not open a read-only connection to Postgres.", "The
server did not accept a read-only session, so writes would not be
prevented."). Connection errors are Failed("Harlequin could not connect to
your Postgres database.", message). Transaction modes ["Auto", "Manual"]
starting at Auto; Manual can commit and roll back.
MySql: conn_str must be empty, else InvalidOption("Harlequin could not
initialize the selected adapter.", "Cannot provide a DSN to the MySQL adapter.
Got:\\n{tuple}"). mysql.connector.connect(host, port=int, unix_socket, database,
user, password (password1), password2, password3, connection_timeout=int,
ssl_ca, ssl_cert, ssl_key, ssl_disabled, openid_token_file,
allow_local_infile=enable_cleartext_plugin, autocommit=True) with the options
that are set; when read_only execute "set session transaction read only".
Errors: Failed("Harlequin could not connect to your MySQL database.",
message). No transaction mode.
Odbc: exactly one conn_str, else InvalidOption("Harlequin could not
initialize the ODBC adapter.", "The ODBC adapter expects exactly one
connection string. It received:\\n{tuple}"); pyodbc.connect(conn_str,
autocommit=True). Errors: Failed("Harlequin could not connect to your ODBC
data source.", message). No transaction mode.
BigQuery: google.cloud.bigquery.Client(project=project, location=location)
with Application Default Credentials; conn_str is ignored. Errors:
Failed("Harlequin could not connect to BigQuery.", message).
Trino: trino.dbapi.connect(host, port=int, user, catalog, schema); with
require_auth "password", auth=BasicAuthentication(user, password),
http_scheme "https" and verify=sslcert or False; with "google", refreshed
google.auth default credentials as JWTAuthentication(token), https and
verify=True. conn_str is ignored. Errors: Failed("Harlequin could not connect
to Trino.", message).
Databricks: databricks.sql.connect(server_hostname, http_path, and
access_token or username/password, or auth_type, or OAuth M2M when
client-id and client-secret are both set: fetch a token with urllib.request,
POST "grant_type=client_credentials&scope=all-apis" to
https://{server_hostname}/oidc/v1/token with HTTP Basic client-id:client-secret,
and pass the reply's JSON access_token as access_token (databricks-sdk is not
a dependency: its databricks/__init__.py collides with the connector's, so
import only databricks.sql); only one of them is InvalidOption("Harlequin could not initialize
the selected adapter.", "To use OAuth M2M you must supply both --client-id and
--client-secret CLI arguments.")). Unless no_init, run the init script
(default ~/.databricksrc) split on ";" and report "Executed {n} command(s) from
{path}"; failures Failed("Databricks errored while executing your
initialization script.", message).
Adbc: exactly one conn_str, else InvalidOption("Harlequin could not
initialize the ADBC adapter.", "The ADBC adapter expects exactly one connection
string. It received:\\n{tuple}"); neither driver-type nor driver-path is
InvalidOption(same title, "The ADBC adapter expects either at least a driver
type or a driver path and neither was provided."). db-kwargs-str "k=v;k2=v2"
becomes a dict. With driver-path: adbc_driver_manager.dbapi.connect(driver=
path, db_kwargs={**kwargs, "uri": conn_str}); else
adbc_driver_<type>.dbapi.connect(conn_str, db_kwargs=kwargs) for the lock-
selected driver packages adbc_driver_flightsql, adbc_driver_postgresql,
adbc_driver_snowflake, adbc_driver_sqlite and duckdb (whose ADBC driver is
duckdb's own adbc_driver_duckdb). Errors: Failed("Harlequin could not connect
via ADBC.", message).
Cassandra: cassandra.cluster.Cluster([host], port=int, protocol_version=int
when set, auth_provider=PlainTextAuthProvider(user, password) when user is
set).connect(keyspace); default consistency level consistency-level. Transaction
modes are the consistency level names cut to 10 characters ("ANY", "ONE",
"TWO", "THREE", "QUORUM", "ALL", "LOCAL_QUOR", "EACH_QUORU", "SERIAL",
"LOCAL_SERI", "LOCAL_ONE"), starting at the configured level, none with
commit or rollback. Errors: Failed("Harlequin could not connect to your
Cassandra cluster.", message).
NebulaGraph: nebula3 ConnectionPool with Config().init([(host, port)]) then
get_session(user, password). Errors: Failed("Harlequin could not connect to
NebulaGraph.", message).
Chdb: combine nonblank conn_str items with uri and path; more than one is
InvalidOption("Harlequin could not initialize the selected adapter.", "Pass
only one of a positional database path, --path, or --uri."); none, "",
":memory:", "chdb://:memory:" and "chdb::memory:" mean "chdb://"; values with
"://" or starting with "chdb:", "file:" or "local:" pass through; other paths
become "file:" + the resolved POSIX path. Connect with the chDB ADBC driver
(adbc_driver_chdb.dbapi.connect(uri); never import the chdb package itself,
whose chdb/__init__.py two installed distributions own, with
conn_kwargs={"adbc.connection.readonly": "true"} when read_only). Errors:
Failed("Harlequin could not connect to chDB.", message)."""
    request = _cott_normalize_f32_abi(request, ConnectionRequest, path="$.request")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/connect.py", "38c61e506e5e88345b19d55107b61f5090b55688f2698f0bdcbb20f3cb4a81a4", "connect", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.connect")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.connect"
        if _error.span is None:
            _error.span = {"end_byte":31191,"end_column":1,"end_line":508,"start_byte":20119,"start_column":1,"start_line":354}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.connect", phase="implementation-call", span={"end_byte":31191,"end_column":1,"end_line":508,"start_byte":20119,"start_column":1,"start_line":354}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.connect", phase="implementation-call", span={"end_byte":31191,"end_column":1,"end_line":508,"start_byte":20119,"start_column":1,"start_line":354}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Connection, ConnectionError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.adapters.connect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (ConnectionError_ReadOnlyUnsupported, ConnectionError_InvalidOption, ConnectionError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.adapters.connect", phase="error", span={"end_byte":31191,"end_column":1,"end_line":508,"start_byte":20119,"start_column":1,"start_line":354}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.adapters.connect", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.adapters.connect", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is ConnectionError_ReadOnlyUnsupported:
            _cott_contract_condition(True, "real.harlequin.adapters.connect", "error:2")
        if type(_result) is Err and type(_result.error) is ConnectionError_InvalidOption:
            _cott_contract_condition(True, "real.harlequin.adapters.connect", "error:3")
        if type(_result) is Err and type(_result.error) is ConnectionError_Failed:
            _cott_contract_condition(True, "real.harlequin.adapters.connect", "error:4")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                connection = _cott_match_value.value
                return (_cott_contract_condition(((((connection).adapter == (request).adapter) and ((connection).read_only == (request).read_only))), "real.harlequin.adapters.connect", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.adapters.connect", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.connect", clause="ensures:1", phase="ensures", span={"end_byte":31004,"end_column":123,"end_line":500,"start_byte":30886,"start_column":5,"start_line":500}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Connection, ConnectionError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def execute_statements(connection: Connection, statements: CottList[str], limit: Option[U64], continue_on_error: bool) -> CottList[ExecutedStatement]:
    """Run statements in order on the connection's retained driver, without
fetching result rows, the way Harlequin executes before it fetches. Each
statement produces one ExecutedStatement (index is its position):
- a statement that returns a result set keeps its driver cursor/relation in
  cursor, and columns lists its column names (duplicates kept as the driver
  reports them) with the adapter's short type labels;
- a statement the database refuses has failure (title below, the driver's
  error text) and, unless continue_on_error, no later statement runs (the
  result ends with the failed statement);
- DDL/DML without a result set has neither.
limit, when Some(n), is applied as the hard fetch limit n + 1 (one probe row)
where the driver needs it at execution (DuckDB relation.limit(n+1); chDB's
bounded-read settings); other adapters apply it in fetch_result.
Executing cursors are appended to the session's "active" list while they run
so cancel_queries can reach them. A cancelled statement is a failure with title
"Query canceled" and message "The query was canceled.".
Per adapter: DuckDb conn.sql(statement) (None means no result set), failure
title "DuckDB raised an error when compiling or running your query:";
Sqlite conn.execute; in Manual mode a "begin;" is issued first when not in a
transaction (and a user BEGIN is then a no-op without error); failure title
"SQLite raised an error when compiling or running your query:"; Postgres
psycopg cursor.execute (in Manual mode BEGIN first when idle), title
"Postgres raised an error when compiling or running your query:"; MySql
cursor(buffered=False).execute, title "MySQL raised an error when compiling or
running your query:"; Odbc cursor.execute, title "ODBC raised an error when
compiling or running your query:"; BigQuery client.query(statement) job
(result read in fetch), title "BigQuery raised an error when compiling or
running your query:"; Trino, Databricks, Adbc DBAPI cursor.execute with the
same title pattern naming the adapter; Cassandra session.execute with the
current consistency level, title "Cassandra raised an error:"; NebulaGraph
session.execute with a checked is_succeeded(), title "NebulaGraph raised an
error:"; Chdb one statement per ADBC cursor.execute, title "chDB raised an
error when compiling or running your query:".
Short type labels: DuckDb from relation dtypes: SQLNULL "\\\\n", BOOLEAN "t/f",
TINYINT/SMALLINT/INTEGER "#", UTINYINT/USMALLINT/UINTEGER "u#", BIGINT "##",
UBIGINT "u##", HUGEINT "###", UUID "uid", FLOAT/DOUBLE/DECIMAL/REAL "#.#",
DATE "d", TIMESTAMP* "ts", TIME "t", TIME_TZ/TIMESTAMP_TZ/TIMESTAMP WITH TIME
ZONE "ttz", VARCHAR "s", BLOB "0b", BIT "010", INTERVAL "|-|", STRUCT "{}", MAP
"{m}", else "?" (the base type before "(" or "["; a list type "X[]" is "[X]");
Sqlite from the Python type of the first row's value: str "s", float "#.#",
int "##", anything else "?"; other adapters map their driver type codes the
same way where they can (integers "#", floats and decimals "#.#", text "s",
booleans "t/f", dates "d", timestamps "ts", binary "0b", otherwise "?")."""
    connection = _cott_normalize_f32_abi(connection, Connection, path="$.connection")
    statements = _cott_normalize_f32_abi(statements, CottList[str], path="$.statements")
    limit = _cott_normalize_f32_abi(limit, Option[U64], path="$.limit")
    continue_on_error = _cott_normalize_f32_abi(continue_on_error, bool, path="$.continue_on_error")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/execute_statements.py", "72fe61e9197ced2a0a898806fd3d8d1770295c1d8040bceaab7ae40f57a4e599", "execute_statements", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.execute_statements")
        _result = _implementation(connection, statements, limit, continue_on_error)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.execute_statements"
        if _error.span is None:
            _error.span = {"end_byte":35041,"end_column":1,"end_line":571,"start_byte":31508,"start_column":1,"start_line":515}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.execute_statements", phase="implementation-call", span={"end_byte":35041,"end_column":1,"end_line":571,"start_byte":31508,"start_column":1,"start_line":515}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.execute_statements", phase="implementation-call", span={"end_byte":35041,"end_column":1,"end_line":571,"start_byte":31508,"start_column":1,"start_line":515}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[ExecutedStatement], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) <= len(statements))), "real.harlequin.adapters.execute_statements", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.execute_statements", clause="ensures:1", phase="ensures", span={"end_byte":34985,"end_column":41,"end_line":567,"start_byte":34949,"start_column":5,"start_line":567}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[ExecutedStatement], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def fetch_result(connection: Connection, executed: ExecutedStatement, limit: Option[U64], viewer_max_rows: Option[U64]) -> Result[ResultSet, QueryError]:
    """Fetch the rows of one executed statement into a ResultSet whose data is a
pyarrow.Table, as Harlequin fetches after execution. executed.cursor must be
Some; otherwise Err(QueryError.Failed("Nothing to fetch", "The statement did not
return a result set.")). With limit Some(n) at most n + 1 rows are read; when
n + 1 arrived the extra probe row is dropped and truncated is true. With
Nothing every row is read. fetched_row_count is the rows kept; row_count is
that capped by viewer_max_rows when Some. columns are executed.columns with
duplicate names made unique (a, a0, a1, ...), matching the table's column
names. A result with no rows is an empty table that still has the columns.
Arrow conversion: DuckDb relation.arrow() / to_arrow_table(); Adbc and Chdb
fetch_arrow_table(); other adapters build the table from the Python rows with
pyarrow (columns of mixed Python types fall back to strings; Decimal, dates,
times, UUID and bytes keep their natural Arrow types). elapsed_ms is the fetch
time. A driver error is Err(QueryError.Failed(title, message)) with the adapter's
fetch title, e.g. "DuckDB raised an error when running your query:" or "SQLite
raised an error when fetching results for your query:"; a cancelled fetch is
Err(QueryError.Failed("Query canceled", "The query was canceled.")). The cursor is
closed afterwards and removed from the session's "active" list."""
    connection = _cott_normalize_f32_abi(connection, Connection, path="$.connection")
    executed = _cott_normalize_f32_abi(executed, ExecutedStatement, path="$.executed")
    limit = _cott_normalize_f32_abi(limit, Option[U64], path="$.limit")
    viewer_max_rows = _cott_normalize_f32_abi(viewer_max_rows, Option[U64], path="$.viewer_max_rows")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/fetch_result.py", "6e57eaa3d09761eead34e6c12f29d96710d5e59436fb09a7ad9a2e96b77a415c", "fetch_result", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.fetch_result")
        _result = _implementation(connection, executed, limit, viewer_max_rows)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.fetch_result"
        if _error.span is None:
            _error.span = {"end_byte":36871,"end_column":1,"end_line":604,"start_byte":35041,"start_column":1,"start_line":571}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.fetch_result", phase="implementation-call", span={"end_byte":36871,"end_column":1,"end_line":604,"start_byte":35041,"start_column":1,"start_line":571}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.fetch_result", phase="implementation-call", span={"end_byte":36871,"end_column":1,"end_line":604,"start_byte":35041,"start_column":1,"start_line":571}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[ResultSet, QueryError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.adapters.fetch_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (QueryError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.adapters.fetch_result", phase="error", span={"end_byte":36871,"end_column":1,"end_line":604,"start_byte":35041,"start_column":1,"start_line":571}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.adapters.fetch_result", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.adapters.fetch_result", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is QueryError_Failed:
            _cott_contract_condition(True, "real.harlequin.adapters.fetch_result", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                fetched = _cott_match_value.value
                return (_cott_contract_condition(((((fetched).statement == (executed).sql) and (len((fetched).columns) == len((executed).columns)))), "real.harlequin.adapters.fetch_result", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.adapters.fetch_result", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.fetch_result", clause="ensures:1", phase="ensures", span={"end_byte":36802,"end_column":118,"end_line":598,"start_byte":36689,"start_column":5,"start_line":598}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ResultSet, QueryError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def cancel_queries(connection: Connection) -> Result[Unit, QueryError]:
    """Interrupt whatever the connection is executing, without taking the session
lock (another thread holds it while a query runs). DuckDb conn.interrupt();
Sqlite conn.interrupt(); Postgres conn.cancel_safe(); MySql open a second
connection with the same options and issue "KILL QUERY {id}" for the busy
connection id; Databricks cancel the active cursors (cursor.cancel()); Chdb
adbc_cancel() on the active cursors, falling back to the connection. Adapters
whose descriptor does not implement cancel return Err(QueryError.Failed("Harlequin
could not cancel your queries.", "The {name} adapter does not support
canceling queries.")). A driver error is Err(QueryError.Failed("Harlequin could not
cancel your queries.", message))."""
    connection = _cott_normalize_f32_abi(connection, Connection, path="$.connection")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/cancel_queries.py", "28ed62e2833d481fd53b9e506ac39bbf9e2c6561c1d1b8c627f91a17fa644bdb", "cancel_queries", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.cancel_queries")
        _result = _implementation(connection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.cancel_queries"
        if _error.span is None:
            _error.span = {"end_byte":37837,"end_column":1,"end_line":624,"start_byte":36871,"start_column":1,"start_line":604}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.cancel_queries", phase="implementation-call", span={"end_byte":37837,"end_column":1,"end_line":624,"start_byte":36871,"start_column":1,"start_line":604}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.cancel_queries", phase="implementation-call", span={"end_byte":37837,"end_column":1,"end_line":624,"start_byte":36871,"start_column":1,"start_line":604}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Unit, QueryError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.adapters.cancel_queries", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (QueryError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.adapters.cancel_queries", phase="error", span={"end_byte":37837,"end_column":1,"end_line":624,"start_byte":36871,"start_column":1,"start_line":604}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.adapters.cancel_queries", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.adapters.cancel_queries", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is QueryError_Failed:
            _cott_contract_condition(True, "real.harlequin.adapters.cancel_queries", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                done = _cott_match_value.value
                return (_cott_contract_condition(((done == UNIT)), "real.harlequin.adapters.cancel_queries", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.adapters.cancel_queries", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.cancel_queries", clause="ensures:1", phase="ensures", span={"end_byte":37768,"end_column":42,"end_line":618,"start_byte":37731,"start_column":5,"start_line":618}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, QueryError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def load_catalog(connection: Connection) -> Result[CottList[CatalogEntry], QueryError]:
    """The Databases tree's top levels, as a catalog (see
real.harlequin.catalog.normalize_catalog) whose deeper levels are loaded later
by load_catalog_children. Identifiers are quoted with double quotes (a " inside
doubled) except for MySQL, Databricks, BigQuery and chDB, which use backticks.
Entries at a level that has children are expandable; loaded is true only when
the children are included. Levels and type labels per adapter (siblings
sorted by label unless noted):
DuckDb: databases from "pragma show_databases" (type "db", kind Database,
id/qualified_identifier/query_name "\\"db\\""), each loaded with its schemas
(information_schema.schemata, excluding pg_catalog and information_schema;
"sch", Schema, "\\"db\\".\\"schema\\"", query_name the same), schemas not
loaded. Relations come from load_catalog_children.
Sqlite: databases from "pragma database_list" ("db"), not loaded.
Postgres: databases from pg_database (not templates; "db"), the connected one
loaded with its schemas ("sch"); schemas on the current search_path loaded
with their relations.
MySql: databases from information_schema.schemata excluding sys,
information_schema, performance_schema and mysql ("db"), not loaded.
Odbc: catalogs ("db") → schemas ("sch") from cursor.tables() metadata, schemas
not loaded, driver order.
BigQuery: datasets of the project ("ds"), with their tables and columns from
one INFORMATION_SCHEMA query in the location (default US), all loaded.
Trino: catalogs from SHOW CATALOGS except jmx, memory and system ("c"; only
the configured catalog when set), not loaded.
Databricks: catalogs ("catalog"), with schemas ("s"), tables (the raw
TABLE_TYPE as type label) and columns (raw type strings) from
system.information_schema (legacy metastores through connector metadata calls
unless skip-legacy-indexing), all loaded.
Adbc: adbc_get_objects() read into catalogs ("db", excluding template0 and
template1), schemas ("s"), relations ("v" for VIEW else "t") and columns, all
loaded.
Cassandra: keyspaces ("ks") with tables ("t"), views ("v") and columns (CQL
type names) from cluster metadata, all loaded.
NebulaGraph: spaces ("space") with tags ("tag") and edges ("edge") and their
fields (raw types) from SHOW SPACES / SHOW TAGS / SHOW EDGES / DESC, all
loaded.
Chdb: databases ("db", excluding system, INFORMATION_SCHEMA and
information_schema unless show-system), not loaded.
Driver errors are Err(QueryError.Failed("Harlequin could not load the data
catalog.", message))."""
    connection = _cott_normalize_f32_abi(connection, Connection, path="$.connection")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/load_catalog.py", "9091a2466cce98fc5e597a2e4afcfaa6f13d77fd61451e6b5eb83c680ddddf74", "load_catalog", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.load_catalog")
        _result = _implementation(connection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.load_catalog"
        if _error.span is None:
            _error.span = {"end_byte":40682,"end_column":1,"end_line":674,"start_byte":37837,"start_column":1,"start_line":624}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.load_catalog", phase="implementation-call", span={"end_byte":40682,"end_column":1,"end_line":674,"start_byte":37837,"start_column":1,"start_line":624}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.load_catalog", phase="implementation-call", span={"end_byte":40682,"end_column":1,"end_line":674,"start_byte":37837,"start_column":1,"start_line":624}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[CottList[CatalogEntry], QueryError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.adapters.load_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (QueryError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.adapters.load_catalog", phase="error", span={"end_byte":40682,"end_column":1,"end_line":674,"start_byte":37837,"start_column":1,"start_line":624}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.adapters.load_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.adapters.load_catalog", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is QueryError_Failed:
            _cott_contract_condition(True, "real.harlequin.adapters.load_catalog", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                entries = _cott_match_value.value
                return (_cott_contract_condition((True), "real.harlequin.adapters.load_catalog", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.adapters.load_catalog", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.load_catalog", clause="ensures:1", phase="ensures", span={"end_byte":40613,"end_column":39,"end_line":668,"start_byte":40579,"start_column":5,"start_line":668}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogEntry], QueryError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def load_catalog_children(connection: Connection, parent: CatalogEntry) -> Result[CottList[CatalogEntry], QueryError]:
    """The direct children of one unloaded catalog entry (with their own children
when the adapter loads them together), each naming parent.id as parent.
DuckDb: a schema's relations from information_schema.tables ordered by name
("t" BASE TABLE, "tmp" LOCAL TEMPORARY, "v" VIEW, "?" otherwise; query_name
"\\"schema\\".\\"relation\\"", qualified "\\"db\\".\\"schema\\".\\"relation\\"");
a relation's columns from information_schema.columns ordered by name (label
the column name, type label mapped from data_type as in execute_statements,
query_name "\\"column\\"", kind Column, not expandable).
Sqlite: a database's tables and views from "select type, name from
\\"{db}\\".sqlite_schema" ("t"/"v"; query_name "\\"db\\".\\"relation\\"");
a relation's columns from "pragma {db}.table_info('{relation}')" (TEXT "s",
INTEGER "##", REAL and NUMERIC "#.#", BLOB "b", "" when undeclared, else "?").
Postgres: schemas, relations ("t" table, "v" view, "tmp" temporary, "f"
foreign, "mv" materialized view) and columns (compact type labels) of the
connected database; other databases have no loadable children.
MySql: a database's tables ("t") and views ("v"), then a relation's columns
(type label from DATA_TYPE).
Odbc: a schema's relations ("t", "v", "st" system table, "tmp"), then columns
(ODBC type names). Trino: a catalog's schemas ("s", excluding
information_schema, only the configured one when set), a schema's relations
("t" when table_type ends with TABLE else "v"), a relation's columns. Chdb: a
database's relations ("v" view, "mv" materialized view, "dic" dictionary, else
"t"), a relation's columns ordered by position (ClickHouse type names).
An entry of an adapter that loads everything up front has no children to load
(Ok([])). Driver errors are Err(QueryError.Failed("Catalog Error", message))."""
    connection = _cott_normalize_f32_abi(connection, Connection, path="$.connection")
    parent = _cott_normalize_f32_abi(parent, CatalogEntry, path="$.parent")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/load_catalog_children.py", "8f3f6a2a6e3076d7d953f591ba0af62dbf463cdb4066999f25f29e664ab8928c", "load_catalog_children", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.load_catalog_children")
        _result = _implementation(connection, parent)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.load_catalog_children"
        if _error.span is None:
            _error.span = {"end_byte":42820,"end_column":1,"end_line":712,"start_byte":40682,"start_column":1,"start_line":674}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.load_catalog_children", phase="implementation-call", span={"end_byte":42820,"end_column":1,"end_line":712,"start_byte":40682,"start_column":1,"start_line":674}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.load_catalog_children", phase="implementation-call", span={"end_byte":42820,"end_column":1,"end_line":712,"start_byte":40682,"start_column":1,"start_line":674}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[CottList[CatalogEntry], QueryError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.adapters.load_catalog_children", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (QueryError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.adapters.load_catalog_children", phase="error", span={"end_byte":42820,"end_column":1,"end_line":712,"start_byte":40682,"start_column":1,"start_line":674}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.adapters.load_catalog_children", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.adapters.load_catalog_children", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is QueryError_Failed:
            _cott_contract_condition(True, "real.harlequin.adapters.load_catalog_children", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                children = _cott_match_value.value
                return (_cott_contract_condition((True), "real.harlequin.adapters.load_catalog_children", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.adapters.load_catalog_children", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.load_catalog_children", clause="ensures:1", phase="ensures", span={"end_byte":42751,"end_column":40,"end_line":706,"start_byte":42716,"start_column":5,"start_line":706}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogEntry], QueryError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def search_catalog(connection: Connection, term: str) -> Result[CottList[CatalogEntry], QueryError]:
    """Every catalog item whose label contains term, case-insensitively, at every
level, for adapters that implement catalog search, returned as a normalized
catalog including each match's ancestors (an ancestor that does not itself
match is still included so paths are complete). The term is escaped for
"\\\\", "%" and "_" and matched with LIKE/ILIKE '%term%' ESCAPE '\\\\'.
DuckDb searches non-internal databases, their schemas (excluding pg_catalog and
information_schema), relations and columns with one UNION ALL query ordered so
ancestors precede descendants; Sqlite searches databases, relations and
columns (pragma_database_list, sqlite_schema, pragma_table_info); Postgres
databases, schemas, relations and columns of the connected database; MySql
non-system databases, relations and columns; Chdb databases, relations and
columns with positionCaseInsensitive and at most catalog-search-limit
matches per level. Other adapters are Err(QueryError.Failed("Harlequin could not
search the catalog.", "The {name} adapter does not support catalog
search.")). Driver errors: Err(QueryError.Failed("{Display} raised an error
searching the catalog:", message))."""
    connection = _cott_normalize_f32_abi(connection, Connection, path="$.connection")
    term = _cott_normalize_f32_abi(term, str, path="$.term")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/search_catalog.py", "9cfd02c0d1fce19723cc2e6cac552bf4091f687060905e6371c0aa88111d5807", "search_catalog", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.search_catalog")
        _result = _implementation(connection, term)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.search_catalog"
        if _error.span is None:
            _error.span = {"end_byte":44258,"end_column":1,"end_line":738,"start_byte":42820,"start_column":1,"start_line":712}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.search_catalog", phase="implementation-call", span={"end_byte":44258,"end_column":1,"end_line":738,"start_byte":42820,"start_column":1,"start_line":712}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.search_catalog", phase="implementation-call", span={"end_byte":44258,"end_column":1,"end_line":738,"start_byte":42820,"start_column":1,"start_line":712}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[CottList[CatalogEntry], QueryError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.adapters.search_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (QueryError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.adapters.search_catalog", phase="error", span={"end_byte":44258,"end_column":1,"end_line":738,"start_byte":42820,"start_column":1,"start_line":712}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.adapters.search_catalog", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.adapters.search_catalog", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is QueryError_Failed:
            _cott_contract_condition(True, "real.harlequin.adapters.search_catalog", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                found = _cott_match_value.value
                return (_cott_contract_condition((True), "real.harlequin.adapters.search_catalog", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.adapters.search_catalog", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.search_catalog", clause="ensures:1", phase="ensures", span={"end_byte":44189,"end_column":37,"end_line":732,"start_byte":44157,"start_column":5,"start_line":732}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogEntry], QueryError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def adapter_completions(connection: Connection) -> Result[Opaque[Literal["harlequin.completions"]], QueryError]:
    """The adapter's own completion candidates as one CompletionSet (its payload is a Python tuple of real.harlequin.catalog_types.Completion
values in candidate order: build it with cott_runtime.Opaque(tag="harlequin.completions",
value=tuple(...)) and read it with cast(tuple[Completion, ...], handle.unwrap())
after checking handle.tag == "harlequin.completions"), value
equal to label unless noted:
DuckDb, in order: distinct duckdb_keywords() as "kw" (priority 100 when
reserved, else 1000); distinct duckdb_functions() except database 'temp' as
"pragma"/"macro"/"agg"/"fn"/"fn->T" for pragma/macro/aggregate/scalar/table
functions, priority 1000, context the schema name unless it is "system";
duckdb_settings() as "set" priority 2000; system types from duckdb_types() and
custom types (with schema context) as "type" priority 1000.
Sqlite: SQLite's keywords as "kw" priority 100, its PRAGMA names as "pragma"
priority 1000, then "select distinct name, case when type = 'w' then 'agg'
else 'fn' end from pragma_function_list order by name" priority 1000.
Postgres: pg_get_keywords() ("kw", 100 when catcode is 'R' else 1000);
distinct routine names from information_schema.routines (skipping names of 37+
characters or starting with "_", "pg_" or "binary_upgrade_"; "agg" when
routine_type is null else "fn"; context the schema unless pg_catalog; 1000);
pg_settings names ("set", 2000); sorted by label.
MySql: information_schema.KEYWORDS ("kw", 100 when RESERVED else 1000) and the
built-in function names in mysql.help_topic when readable ("fn", 1000).
BigQuery: the google.cloud.bigquery.enums.StandardSqlTypeNames names ("type",
1000), BigQuery's reserved keywords ("kw", 100), and GoogleSQL built-in
scalar and aggregate function names ("fn"/"agg", 1000).
Trino: the reserved keywords of Trino's SQL grammar ("kw", 100) and SHOW
FUNCTIONS names ("fn", 1000). Databricks: Databricks SQL reserved keywords and
SHOW FUNCTIONS names ("kw"/"fn", 1000). Cassandra: CQL keywords ("kw", 100 for
reserved else 1000), sorted. NebulaGraph: nGQL reserved words ("kw", 100) and
functions ("fn", 1000). Chdb exactly: numbers, numbers_mt, file, s3, url (fn,
900), remote, cluster (fn, 850), mergeTreeIndex, toDateTime64,
toStartOfInterval, quantile, quantiles, argMax, argMin, arrayJoin (fn, 800),
PREWHERE, FINAL, SETTINGS, FORMAT, ENGINE, MergeTree (kw, 800). Odbc and Adbc
have none.
A driver error is Err(QueryError.Failed("Harlequin could not load completions from
your adapter.", message))."""
    connection = _cott_normalize_f32_abi(connection, Connection, path="$.connection")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/adapter_completions.py", "0cdba6956e1e94e7af0cff46f484eae456b873d50c92be68b85efc490988ca24", "adapter_completions", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.adapter_completions")
        _result = _implementation(connection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.adapter_completions"
        if _error.span is None:
            _error.span = {"end_byte":47100,"end_column":1,"end_line":783,"start_byte":44258,"start_column":1,"start_line":738}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.adapter_completions", phase="implementation-call", span={"end_byte":47100,"end_column":1,"end_line":783,"start_byte":44258,"start_column":1,"start_line":738}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.adapter_completions", phase="implementation-call", span={"end_byte":47100,"end_column":1,"end_line":783,"start_byte":44258,"start_column":1,"start_line":738}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Opaque[Literal["harlequin.completions"]], QueryError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.adapters.adapter_completions", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (QueryError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.adapters.adapter_completions", phase="error", span={"end_byte":47100,"end_column":1,"end_line":783,"start_byte":44258,"start_column":1,"start_line":738}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.adapters.adapter_completions", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.adapters.adapter_completions", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is QueryError_Failed:
            _cott_contract_condition(True, "real.harlequin.adapters.adapter_completions", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                candidates = _cott_match_value.value
                return (_cott_contract_condition((True), "real.harlequin.adapters.adapter_completions", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.adapters.adapter_completions", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.adapter_completions", clause="ensures:1", phase="ensures", span={"end_byte":47031,"end_column":42,"end_line":777,"start_byte":46994,"start_column":5,"start_line":777}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Opaque[Literal["harlequin.completions"]], QueryError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def validate_sql(connection: Connection, text: str) -> bool:
    """Whether text is a complete statement the adapter can parse, for the Run
Selection caption. DuckDb: "select json_serialize_sql('{text with ' doubled}')"
parses, and the JSON result has no "error" of error_type "parser" (DDL, which
json_serialize_sql does not support, counts as valid). Every other adapter
cannot validate and returns true. Errors return false."""
    connection = _cott_normalize_f32_abi(connection, Connection, path="$.connection")
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/validate_sql.py", "b726cd6b415ec69130426a93d408f69c99daeb089874e791f867037bc96b5f9d", "validate_sql", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.validate_sql")
        _result = _implementation(connection, text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.validate_sql"
        if _error.span is None:
            _error.span = {"end_byte":47590,"end_column":1,"end_line":794,"start_byte":47100,"start_column":1,"start_line":783}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.validate_sql", phase="implementation-call", span={"end_byte":47590,"end_column":1,"end_line":794,"start_byte":47100,"start_column":1,"start_line":783}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.validate_sql", phase="implementation-call", span={"end_byte":47590,"end_column":1,"end_line":794,"start_byte":47100,"start_column":1,"start_line":783}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, bool, path="$.return")
    _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def toggle_transaction_mode(connection: Connection) -> Result[Connection, QueryError]:
    """Move to the adapter's next transaction mode (cycling) and return the
connection with the new transaction_mode. Sqlite and Postgres: Auto <-> Manual;
entering Auto commits an open transaction and sets autocommit true, entering
Manual sets autocommit false (the next statement begins a transaction).
Cassandra: the next consistency level. Adapters without modes return the
connection unchanged. Errors: Err(QueryError.Failed("Harlequin could not change the
transaction mode.", message))."""
    connection = _cott_normalize_f32_abi(connection, Connection, path="$.connection")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/toggle_transaction_mode.py", "bfcb0c2407b127ab7de4a8fb0e32191a8a337ae5af53ee11628b642b3318f645", "toggle_transaction_mode", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.toggle_transaction_mode")
        _result = _implementation(connection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.toggle_transaction_mode"
        if _error.span is None:
            _error.span = {"end_byte":48408,"end_column":1,"end_line":811,"start_byte":47590,"start_column":1,"start_line":794}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.toggle_transaction_mode", phase="implementation-call", span={"end_byte":48408,"end_column":1,"end_line":811,"start_byte":47590,"start_column":1,"start_line":794}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.toggle_transaction_mode", phase="implementation-call", span={"end_byte":48408,"end_column":1,"end_line":811,"start_byte":47590,"start_column":1,"start_line":794}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Connection, QueryError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.adapters.toggle_transaction_mode", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (QueryError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.adapters.toggle_transaction_mode", phase="error", span={"end_byte":48408,"end_column":1,"end_line":811,"start_byte":47590,"start_column":1,"start_line":794}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.adapters.toggle_transaction_mode", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.adapters.toggle_transaction_mode", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is QueryError_Failed:
            _cott_contract_condition(True, "real.harlequin.adapters.toggle_transaction_mode", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                updated = _cott_match_value.value
                return (_cott_contract_condition(((((updated).adapter == (connection).adapter) and ((updated).connection_id == (connection).connection_id))), "real.harlequin.adapters.toggle_transaction_mode", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.adapters.toggle_transaction_mode", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.toggle_transaction_mode", clause="ensures:1", phase="ensures", span={"end_byte":48338,"end_column":128,"end_line":805,"start_byte":48215,"start_column":5,"start_line":805}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Connection, QueryError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def commit_transaction(connection: Connection) -> Result[Unit, QueryError]:
    """Commit the open transaction when the current mode can commit (Manual on
Sqlite and Postgres); otherwise do nothing. Errors: Err(QueryError.Failed("Harlequin
could not commit the transaction.", message))."""
    connection = _cott_normalize_f32_abi(connection, Connection, path="$.connection")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/commit_transaction.py", "5cceabf9b7cd5e78f0e328b3189451e3b9edd7e9589fcbe03a44c22f5e9931b7", "commit_transaction", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.commit_transaction")
        _result = _implementation(connection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.commit_transaction"
        if _error.span is None:
            _error.span = {"end_byte":48831,"end_column":1,"end_line":824,"start_byte":48408,"start_column":1,"start_line":811}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.commit_transaction", phase="implementation-call", span={"end_byte":48831,"end_column":1,"end_line":824,"start_byte":48408,"start_column":1,"start_line":811}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.commit_transaction", phase="implementation-call", span={"end_byte":48831,"end_column":1,"end_line":824,"start_byte":48408,"start_column":1,"start_line":811}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Unit, QueryError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.adapters.commit_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (QueryError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.adapters.commit_transaction", phase="error", span={"end_byte":48831,"end_column":1,"end_line":824,"start_byte":48408,"start_column":1,"start_line":811}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.adapters.commit_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.adapters.commit_transaction", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is QueryError_Failed:
            _cott_contract_condition(True, "real.harlequin.adapters.commit_transaction", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                done = _cott_match_value.value
                return (_cott_contract_condition(((done == UNIT)), "real.harlequin.adapters.commit_transaction", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.adapters.commit_transaction", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.commit_transaction", clause="ensures:1", phase="ensures", span={"end_byte":48761,"end_column":42,"end_line":818,"start_byte":48724,"start_column":5,"start_line":818}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, QueryError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def rollback_transaction(connection: Connection) -> Result[Unit, QueryError]:
    """Roll back the open transaction when the current mode can roll back (Manual on
Sqlite and Postgres); otherwise do nothing. Errors: Err(QueryError.Failed("Harlequin
could not roll back the transaction.", message))."""
    connection = _cott_normalize_f32_abi(connection, Connection, path="$.connection")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/rollback_transaction.py", "ed1e4f86c2f6306939e0faf8e69af7415072d66f9f5609ffc25c683bd1ecc2fb", "rollback_transaction", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.rollback_transaction")
        _result = _implementation(connection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.rollback_transaction"
        if _error.span is None:
            _error.span = {"end_byte":49265,"end_column":1,"end_line":837,"start_byte":48831,"start_column":1,"start_line":824}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.rollback_transaction", phase="implementation-call", span={"end_byte":49265,"end_column":1,"end_line":837,"start_byte":48831,"start_column":1,"start_line":824}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.rollback_transaction", phase="implementation-call", span={"end_byte":49265,"end_column":1,"end_line":837,"start_byte":48831,"start_column":1,"start_line":824}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Unit, QueryError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.adapters.rollback_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (QueryError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.adapters.rollback_transaction", phase="error", span={"end_byte":49265,"end_column":1,"end_line":837,"start_byte":48831,"start_column":1,"start_line":824}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.adapters.rollback_transaction", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.adapters.rollback_transaction", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is QueryError_Failed:
            _cott_contract_condition(True, "real.harlequin.adapters.rollback_transaction", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                done = _cott_match_value.value
                return (_cott_contract_condition(((done == UNIT)), "real.harlequin.adapters.rollback_transaction", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.adapters.rollback_transaction", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.rollback_transaction", clause="ensures:1", phase="ensures", span={"end_byte":49195,"end_column":42,"end_line":831,"start_byte":49158,"start_column":5,"start_line":831}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, QueryError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def run_scalar_query(connection: Connection, sql: str) -> Result[Option[str], QueryError]:
    """Execute sql (used by catalog interactions such as Show DDL and Use) and return
the first column of the first row as text (str of the value), Nothing when
there is no row or no result set. Errors: Err(QueryError.Failed("Data Catalog
Interaction Error", message))."""
    connection = _cott_normalize_f32_abi(connection, Connection, path="$.connection")
    sql = _cott_normalize_f32_abi(sql, str, path="$.sql")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/run_scalar_query.py", "26da61fbdc99d9ec0800a45d579ff7f12bb011918cabb922c2ed44b79ca66262", "run_scalar_query", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.run_scalar_query")
        _result = _implementation(connection, sql)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.run_scalar_query"
        if _error.span is None:
            _error.span = {"end_byte":49776,"end_column":1,"end_line":851,"start_byte":49265,"start_column":1,"start_line":837}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.run_scalar_query", phase="implementation-call", span={"end_byte":49776,"end_column":1,"end_line":851,"start_byte":49265,"start_column":1,"start_line":837}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.run_scalar_query", phase="implementation-call", span={"end_byte":49776,"end_column":1,"end_line":851,"start_byte":49265,"start_column":1,"start_line":837}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Option[str], QueryError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.adapters.run_scalar_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (QueryError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.adapters.run_scalar_query", phase="error", span={"end_byte":49776,"end_column":1,"end_line":851,"start_byte":49265,"start_column":1,"start_line":837}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.adapters.run_scalar_query", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.adapters.run_scalar_query", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is QueryError_Failed:
            _cott_contract_condition(True, "real.harlequin.adapters.run_scalar_query", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                value = _cott_match_value.value
                return (_cott_contract_condition((True), "real.harlequin.adapters.run_scalar_query", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.adapters.run_scalar_query", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.run_scalar_query", clause="ensures:1", phase="ensures", span={"end_byte":49691,"end_column":37,"end_line":845,"start_byte":49659,"start_column":5,"start_line":845}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Option[str], QueryError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def close_connection(connection: Connection) -> Result[Unit, QueryError]:
    """Close the session: mark it closed, then close every registered SDK resource
(an open transaction is rolled back by the driver). Closing twice is
harmless. Errors: Err(QueryError.Failed("Harlequin could not close the
connection.", message))."""
    connection = _cott_normalize_f32_abi(connection, Connection, path="$.connection")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/close_connection.py", "add573241dbfc194b0d467c43fe98133eb07fcc1d13002b8c4e39545cc368df8", "close_connection", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.close_connection")
        _result = _implementation(connection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.close_connection"
        if _error.span is None:
            _error.span = {"end_byte":50238,"end_column":1,"end_line":865,"start_byte":49776,"start_column":1,"start_line":851}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.close_connection", phase="implementation-call", span={"end_byte":50238,"end_column":1,"end_line":865,"start_byte":49776,"start_column":1,"start_line":851}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.close_connection", phase="implementation-call", span={"end_byte":50238,"end_column":1,"end_line":865,"start_byte":49776,"start_column":1,"start_line":851}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Unit, QueryError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.adapters.close_connection", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (QueryError_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.adapters.close_connection", phase="error", span={"end_byte":50238,"end_column":1,"end_line":865,"start_byte":49776,"start_column":1,"start_line":851}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.adapters.close_connection", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.adapters.close_connection", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is QueryError_Failed:
            _cott_contract_condition(True, "real.harlequin.adapters.close_connection", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                done = _cott_match_value.value
                return (_cott_contract_condition(((done == UNIT)), "real.harlequin.adapters.close_connection", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.adapters.close_connection", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.adapters.close_connection", clause="ensures:1", phase="ensures", span={"end_byte":50168,"end_column":42,"end_line":859,"start_byte":50131,"start_column":5,"start_line":859}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Unit, QueryError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def catalog_interactions(adapter: AdapterKind, entry: CatalogEntry) -> CottList[str]:
    """The adapter's context-menu interactions for a database catalog entry, in
order (the menu adds "Insert Name at Cursor" before them).
DuckDb: Database: "Switch Editor Context (Use)", "Export Database"; Schema:
"Switch Editor Context (Use)", "Drop Schema"; Table and TemporaryTable:
"Insert Columns at Cursor", "Preview Data", "Describe", "Summarize", "Show
DDL", "Drop Table"; View: the same four then "Show DDL", "Drop View".
Sqlite: Table: "Insert Columns at Cursor", "Preview Data", "Describe", "Show
DDL", "Drop Table"; View: the same four then "Drop View".
Postgres: Table: "Insert Columns at Cursor", "Preview Data", "Describe
Relation (\\\\d+)", "Describe Indexes", "Describe Constraints", "Drop Table";
View: the first three, "Show View Definition", "Drop View"; Schema: "Set Search
Path", "List Relations (\\\\d+)", "List Indexes (\\\\di+)", "Drop Schema";
Database: "List Relations (\\\\d+)", "List Indexes (\\\\di+)", "Drop Database".
MySql: Table: "Insert Columns at Cursor", "Preview Data", "Drop Table"; View:
the first two, "Drop View"; Database: "Set Editor Context (USE)", "Drop
Database". Odbc: Table: "Insert Columns at Cursor", "Preview Data", "Drop
Table"; View: the first two, "Drop View"; Database: "Use Database", "Drop
Database". Other adapters and other kinds: none."""
    adapter = _cott_normalize_f32_abi(adapter, AdapterKind, path="$.adapter")
    entry = _cott_normalize_f32_abi(entry, CatalogEntry, path="$.entry")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/catalog_interactions.py", "48b15efbb9178aa8484cf5d9908e858c90356e9feee9c61cef50af0727ec794a", "catalog_interactions", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.catalog_interactions")
        _result = _implementation(adapter, entry)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.catalog_interactions"
        if _error.span is None:
            _error.span = {"end_byte":51709,"end_column":1,"end_line":889,"start_byte":50238,"start_column":1,"start_line":865}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.catalog_interactions", phase="implementation-call", span={"end_byte":51709,"end_column":1,"end_line":889,"start_byte":50238,"start_column":1,"start_line":865}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.catalog_interactions", phase="implementation-call", span={"end_byte":51709,"end_column":1,"end_line":889,"start_byte":50238,"start_column":1,"start_line":865}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def plan_interaction(adapter: AdapterKind, entry: CatalogEntry, label: str, children: CottList[CatalogEntry]) -> Option[InteractionPlan]:
    """What choosing a context-menu item does. "Insert Name at Cursor" is
InsertText(entry.query_name) for every adapter. Otherwise (Nothing for a label
catalog_interactions does not list):
"Insert Columns at Cursor": InsertChildNames(entry.id) (the caller loads the
children when needed and inserts their query_name values joined by ",\\n").
"Preview Data": NewBuffer("select *\\nfrom {qualified_identifier}\\nlimit 100")
(MySql "select * from {qi} limit 100"; Odbc "select * from {qi}").
"Describe": NewBuffer("describe {qi}") (DuckDb) or "pragma table_info({qi})"
(Sqlite). "Summarize": NewBuffer("summarize {qi}").
"Export Database": NewBuffer("use {qi};\\nexport database './target_directory';").
"Show DDL": NewBufferFromQuery with DuckDb "select sql from duckdb_tables()
where database_name = '{db}' and schema_name = '{schema}' and table_name =
'{label}' limit 1" (duckdb_views() and view_name for views) or Sqlite "select
sql from sqlite_schema where tbl_name = '{label}' limit 1", failure "Could not
load DDL for {label}".
"Switch Editor Context (Use)", "Set Editor Context (USE)", "Use Database":
Execute("use {qi}", Nothing, "Editor context switched to {label}", "Could not
switch context", false). "Set Search Path": Execute("set search_path to
{qi}", Nothing, "Editor context switched to {label}", "Could not switch
context", false).
"Drop Table"/"Drop View": Execute("drop table {qi}" / "drop view {qi}",
Some("Really drop {table|view} {label}?"), "Dropped {table|view} {label}",
"Could not drop {table|view} {label}", true). "Drop Schema": Execute("drop
schema {qi} cascade", Some("Really drop schema {label} and everything in
it?") when children is nonempty else Nothing, "Dropped schema {label}",
"Could not drop schema {label}", true). "Drop Database": Execute("drop
database {qi}", confirm like Drop Schema, "Dropped database {label}", "Could
not drop database {label}", true).
Postgres list/describe items are NewBuffer with the catalog query psql uses
for \\\\d+, \\\\di+, indexes and constraints of the relation or schema;
"Show View Definition" is NewBufferFromQuery("select
pg_get_viewdef('{qi}'::regclass, true)", ...)."""
    adapter = _cott_normalize_f32_abi(adapter, AdapterKind, path="$.adapter")
    entry = _cott_normalize_f32_abi(entry, CatalogEntry, path="$.entry")
    label = _cott_normalize_f32_abi(label, str, path="$.label")
    children = _cott_normalize_f32_abi(children, CottList[CatalogEntry], path="$.children")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/adapters/plan_interaction.py", "16206e8895f1842ed32a0a4338f290376fa1e5ad74780c5067a0cc482ae42019", "plan_interaction", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.adapters.plan_interaction")
        _result = _implementation(adapter, entry, label, children)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.adapters.plan_interaction"
        if _error.span is None:
            _error.span = {"end_byte":54156,"end_column":1,"end_line":931,"start_byte":51709,"start_column":1,"start_line":889}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.adapters.plan_interaction", phase="implementation-call", span={"end_byte":54156,"end_column":1,"end_line":931,"start_byte":51709,"start_column":1,"start_line":889}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.adapters.plan_interaction", phase="implementation-call", span={"end_byte":54156,"end_column":1,"end_line":931,"start_byte":51709,"start_column":1,"start_line":889}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Option[InteractionPlan], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Option[InteractionPlan], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["AdapterDescriptor", "AdapterKind", "AdapterKind_Adbc", "AdapterKind_BigQuery", "AdapterKind_Cassandra", "AdapterKind_Chdb", "AdapterKind_Databricks", "AdapterKind_DuckDb", "AdapterKind_MySql", "AdapterKind_NebulaGraph", "AdapterKind_Odbc", "AdapterKind_Postgres", "AdapterKind_Sqlite", "AdapterKind_Trino", "AdapterOption", "AdapterSetting", "Connection", "ConnectionError", "ConnectionError_Failed", "ConnectionError_InvalidOption", "ConnectionError_ReadOnlyUnsupported", "ConnectionRequest", "ExecutedStatement", "InteractionPlan", "InteractionPlan_Execute", "InteractionPlan_InsertChildNames", "InteractionPlan_InsertText", "InteractionPlan_NewBuffer", "InteractionPlan_NewBufferFromQuery", "OptionKind", "OptionKind_Choice", "OptionKind_FilePath", "OptionKind_Flag", "OptionKind_Repeated", "OptionKind_Text", "PendingResult", "QueryError", "QueryError_Failed", "QueryFailure", "SessionHandle", "SettingValue", "SettingValue_Flag", "SettingValue_Text", "SettingValue_Values", "TransactionMode", "adapter_completions", "adapter_descriptors", "adapter_options", "cancel_queries", "catalog_interactions", "close_connection", "commit_transaction", "connect", "execute_statements", "fetch_result", "find_adapter", "load_catalog", "load_catalog_children", "plan_interaction", "rollback_transaction", "run_scalar_query", "search_catalog", "toggle_transaction_mode", "validate_sql"]
