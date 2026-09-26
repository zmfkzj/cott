from typing import Final

from cott_runtime import CottList, Nothing, Some

from real.harlequin.adapters_types import AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_Postgres, AdapterKind_Sqlite, AdapterKind_Trino, AdapterOption, OptionKind, OptionKind_Choice, OptionKind_FilePath, OptionKind_Flag, OptionKind_Repeated, OptionKind_Text

_INIT_DESC: Final[str] = "The path to an initialization script. On startup, Harlequin will execute the commands in the script against the attached database."
_NO_INIT_DESC: Final[str] = "Start Harlequin without executing the initialization script."


def _kind(spec: str) -> OptionKind:
    if spec == "text":
        return OptionKind_Text()
    if spec == "flag":
        return OptionKind_Flag()
    if spec == "repeated":
        return OptionKind_Repeated()
    if spec == "path":
        return OptionKind_FilePath()
    return OptionKind_Choice(choices=CottList(values=spec.split(",")))


def _opt(name: str, shorts: str, spec: str, default: str, label: str, description: str, secret: bool) -> AdapterOption:
    return AdapterOption(
        name=name,
        short_decls=CottList(values=shorts.split()),
        kind=_kind(spec),
        label=label,
        description=description,
        default=Some(value=default) if default else Nothing(),
        secret=secret,
    )


def _rows(kind: AdapterKind) -> list[tuple[str, str, str, str, str, str]]:
    if isinstance(kind, AdapterKind_DuckDb):
        return [
            ("init-path", "-i -init", "path", "", "Init Path", _INIT_DESC),
            ("no-init", "", "flag", "", "No Init", _NO_INIT_DESC),
            ("allow-unsigned-extensions", "-u -unsigned", "flag", "", "Allow Unsigned Extensions", "Allow loading unsigned extensions"),
            ("extension", "-e", "repeated", "", "Extension", "Install and load the named DuckDB extension when starting Harlequin. To install multiple extensions, repeat this option."),
            ("force-install-extensions", "", "flag", "", "Force Install Extensions", "Force install all extensions passed with -e."),
            ("custom-extension-repo", "", "text", "", "Custom Extension Repo", "A value to pass to DuckDB's custom_extension_repository variable. Will be set before installing any extensions that are passed using -e."),
            ("md_token", "", "text", "", "Md Token", "MotherDuck Token. Pass your MotherDuck service token in this option, or set the `motherduck_token` environment variable."),
            ("md_saas", "", "flag", "", "Md Saas", "Run MotherDuck in SaaS mode (no local privileges)."),
        ]
    if isinstance(kind, AdapterKind_Sqlite):
        return [
            ("init-path", "-i -init", "path", "", "Init Path", _INIT_DESC),
            ("no-init", "", "flag", "", "No Init", _NO_INIT_DESC),
            ("mode", "-mode -m", "ro,rw,rwc,memory", "rwc", "Mode", "The mode parameter may be set to either 'ro', 'rw', 'rwc', or 'memory'."),
            ("lock-timeout", "", "text", "", "Lock Timeout", "How many seconds the connection should wait before raising an OperationalError when a table is locked. Default five seconds."),
            ("detect-types", "", "text", "", "Detect Types", "Control whether and how data types not natively supported by SQLite are looked up (PARSE_DECLTYPES | PARSE_COLNAMES as an int). By default (0), type detection is disabled."),
            ("cached-statements", "", "text", "", "Cached Statements", "The number of statements that sqlite3 should internally cache for this connection. By default, 128 statements."),
            ("extension", "-e", "repeated", "", "Extension", "Load the SQLite extension from the passed path when starting Harlequin. To install multiple extensions, repeat this option."),
        ]
    if isinstance(kind, AdapterKind_Postgres):
        return [
            ("host", "-h", "text", "localhost", "Host", "Specifies the host name of the machine on which the server is running."),
            ("port", "-p", "text", "5432", "Port", "Port number to connect to at the server host."),
            ("dbname", "-d", "text", "postgres", "Database", "The database name to use when connecting with the Postgres server."),
            ("user", "-u --username -U", "text", "", "User", "PostgreSQL user name to connect as."),
            ("password", "", "text", "", "Password", "Password to be used if the server demands password authentication."),
            ("passfile", "", "path", "", "Passfile", "Specifies the name of the file used to store passwords."),
            ("require_auth", "", "password,md5,gss,sspi,scram-sha-256,none", "", "Require Auth", "Specifies the authentication method that the client requires from the server."),
            ("channel_binding", "", "require,prefer,disable", "", "Channel Binding", "This option controls the client's use of channel binding."),
            ("connect_timeout", "", "text", "", "Connect Timeout", "Maximum time to wait while connecting, in seconds (write as a decimal integer)."),
            ("sslmode", "", "disable,allow,prefer,require,verify-ca,verify-full", "prefer", "SSL Mode", "Determines whether or with what priority a secure SSL TCP/IP connection will be negotiated with the server."),
            ("sslcert", "", "path", "~/.postgresql/postgresql.crt", "SSL Cert", "Specifies the file name of the client SSL certificate."),
            ("sslkey", "", "text", "", "SSL Key", "Specifies the location for the secret key used for the client certificate."),
        ]
    if isinstance(kind, AdapterKind_MySql):
        return [
            ("host", "-h", "text", "localhost", "Host", "The host name or IP address of the MySQL server."),
            ("port", "-p", "text", "3306", "Port", "The TCP/IP port of the MySQL server. Must be an integer."),
            ("unix_socket", "", "text", "", "Unix Socket", "The location of the Unix socket file."),
            ("database", "-d -db", "text", "postgres", "Database", "The database (schema) name to use when connecting with the MySQL server."),
            ("user", "-u --username -U", "text", "", "User", "The user name used to authenticate with the MySQL server."),
            ("password", "--password1", "text", "", "Password", "The password to authenticate the user with the MySQL server."),
            ("password2", "", "text", "", "Password 2", "For Multi-Factor Authentication (MFA); password for the second authentication factor."),
            ("password3", "", "text", "", "Password 3", "For Multi-Factor Authentication (MFA); password for the third authentication factor."),
            ("connection_timeout", "--connect_timeout", "text", "", "Connection Timeout", "Timeout for the TCP and Unix socket connections. Must be an integer."),
            ("ssl-ca", "", "path", "", "SSL CA", "File containing the SSL certificate authority."),
            ("ssl-cert", "--sslcert", "path", "", "SSL Cert", "File containing the SSL certificate file."),
            ("ssl-disabled", "", "flag", "", "SSL Disabled", "True disables SSL/TLS usage."),
            ("ssl-key", "--sslkey", "path", "", "SSL Key", "File containing the SSL key."),
            ("openid-token-file", "--oid", "path", "", "OpenID Token File", "File containing the OpenID Connect token."),
            ("pool-size", "-n", "text", "5", "Pool Size", "The number of connections to open in the pool. Must be an integer."),
            ("enable-cleartext-plugin", "", "flag", "", "Enable Cleartext Plugin", "Enables the mysql_clear_password plugin."),
        ]
    if isinstance(kind, AdapterKind_Odbc):
        return []
    if isinstance(kind, AdapterKind_BigQuery):
        return [
            ("project", "-p", "text", "", "Project", "The GCP project ID to use when connecting to BigQuery."),
            ("location", "-l", "text", "", "Location", "The GCP location (region) to use for queries and catalog."),
        ]
    if isinstance(kind, AdapterKind_Trino):
        return [
            ("host", "-h", "text", "localhost", "Host", "Specifies the host name of the machine on which the server is running."),
            ("port", "-p", "text", "8080", "Port", "Port number to connect to at the server host."),
            ("user", "-u --username -U", "text", "trino", "User", "Trino user name to connect as."),
            ("password", "", "text", "", "Password", "Password to be used if the server demands password authentication."),
            ("require_auth", "", "password,google,none", "", "Require Auth", "Specifies the authentication method that the client requires from the server."),
            ("sslcert", "", "path", "", "SSL Cert", "Specifies the file name of the client SSL certificate."),
            ("schema", "", "text", "", "Schema", "Specifies the schema to browse."),
            ("catalog", "", "text", "", "Catalog", "Specifies the catalog to browse."),
        ]
    if isinstance(kind, AdapterKind_Databricks):
        return [
            ("server-hostname", "", "text", "", "Server Hostname", "The Server Hostname value for your cluster or SQL warehouse."),
            ("http-path", "", "text", "", "HTTP Path", "The HTTP Path value for your cluster or SQL warehouse."),
            ("access-token", "", "text", "", "Access Token", "Your Databricks personal access token."),
            ("username", "", "text", "", "Username", "Your Databricks username (basic auth)."),
            ("password", "", "text", "", "Password", "Your Databricks password (basic auth)."),
            ("auth-type", "", "databricks-oauth,azure-oauth", "", "Auth Type", "The OAuth U2M flow to use."),
            ("skip-legacy-indexing", "", "flag", "", "Skip Legacy Indexing", "Do not index legacy (non Unity Catalog) metastores for the Data Catalog."),
            ("client-id", "", "text", "", "Client ID", "The OAuth M2M client id."),
            ("client-secret", "", "text", "", "Client Secret", "The OAuth M2M client secret."),
            ("init-path", "-i -init", "path", "", "Init Path", "The path to an initialization script (default ~/.databricksrc)."),
            ("no-init", "", "flag", "", "No Init", _NO_INIT_DESC),
        ]
    if isinstance(kind, AdapterKind_Adbc):
        return [
            ("driver-type", "", "flightsql,postgresql,snowflake,sqlite,duckdb", "", "Driver Type", "The ADBC driver package to use (adbc_driver_<type>)."),
            ("driver-path", "", "path", "", "Driver Path", "The path to an ADBC driver shared library to load with the driver manager."),
            ("db-kwargs-str", "", "text", "", "Database Kwargs", "Driver options as semicolon-separated key=value pairs."),
        ]
    if isinstance(kind, AdapterKind_Cassandra):
        return [
            ("host", "-h", "text", "localhost", "Host", "The contact point of the Cassandra cluster."),
            ("port", "-p", "text", "9042", "Port", "The native protocol port. Must be an integer."),
            ("keyspace", "-k", "text", "", "Keyspace", "The keyspace to use."),
            ("user", "-u --username", "text", "", "User", "The user name for plain-text authentication."),
            ("password", "", "text", "", "Password", "The password for plain-text authentication."),
            ("protocol-version", "-P", "text", "", "Protocol Version", "The native protocol version. Must be an integer."),
            ("consistency-level", "-C", "ANY,ONE,TWO,THREE,QUORUM,ALL,LOCAL_QUORUM,EACH_QUORUM,SERIAL,LOCAL_SERIAL,LOCAL_ONE", "LOCAL_ONE", "Consistency Level", "The default consistency level of queries."),
        ]
    if isinstance(kind, AdapterKind_NebulaGraph):
        return [
            ("host", "-h", "text", "localhost", "Host", "The host of the NebulaGraph graphd service."),
            ("port", "-p", "text", "9669", "Port", "The port of the graphd service."),
            ("user", "-u", "text", "root", "User", "The user name."),
            ("password", "-pw", "text", "nebula", "Password", "The password."),
        ]
    return [
        ("uri", "", "text", "", "URI", "A chDB connection URI."),
        ("path", "-p", "path", "", "Path", "A directory holding a persistent chDB database."),
        ("show-system", "", "flag", "", "Show System", "Show the system, INFORMATION_SCHEMA and information_schema databases in the Data Catalog."),
        ("catalog-search-limit", "", "text", "200", "Catalog Search Limit", "The maximum number of catalog search matches per level. Must be an integer of at least 1."),
    ]


def adapter_options(kind: AdapterKind) -> CottList[AdapterOption]:
    duckdb = isinstance(kind, AdapterKind_DuckDb)
    return CottList(values=[_opt(name, shorts, spec, default, label, desc, duckdb and name == "md_token") for (name, shorts, spec, default, label, desc) in _rows(kind)])
