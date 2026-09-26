from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.pgcli.config_types import ConfigEntry

"""A live psycopg 3 connection (psycopg.Connection[tuple[object, ...]]) opened
with autocommit on."""
ConnectionHandle: TypeAlias = Opaque[Literal["pgcli.connection"]]

"""A started sshtunnel.SSHTunnelForwarder that forwards a local loopback port to
the database host."""
TunnelHandle: TypeAlias = Opaque[Literal["pgcli.ssh-tunnel"]]

"""One libpq connection parameter. name is a libpq keyword such as dbname, user,
password, host, hostaddr, port, dsn (a whole connection string) or
application_name."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionParam:
    __hash__ = None
    name: str
    value: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))

"""PGExecute: one open database session. params are the merged connection
parameters the session was opened with, in first-insertion order, used to
reconnect and to open a copy. dbname, user, host and port are the values libpq
reports for the open connection (host falls back to "pgbouncer" for a pgbouncer
virtual database and otherwise to the server's first unix_socket_directories
entry when libpq reports none). pid is the backend process id, superuser is
whether the is_superuser parameter status is "on" or "1", server_version is the
server_version parameter status ("" when absent) and virtual_database is true
for a pgbouncer admin database, detected by a protocol violation on SELECT 1."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Executor:
    __hash__ = None
    connection: Opaque[Literal["pgcli.connection"]]
    tunnel: Option[Opaque[Literal["pgcli.ssh-tunnel"]]]
    params: CottList[ConnectionParam]
    dbname: str
    user: str
    host: str
    port: str
    pid: I64
    superuser: bool
    server_version: str
    virtual_database: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "connection", _cott_validate_abi(self.connection, Opaque[Literal["pgcli.connection"]], path="$.connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "tunnel", _cott_validate_abi(self.tunnel, Option[Opaque[Literal["pgcli.ssh-tunnel"]]], path="$.tunnel"))
        if not _cott_validated_construction():
            object.__setattr__(self, "params", _cott_validate_abi(self.params, CottList[ConnectionParam], path="$.params"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dbname", _cott_validate_abi(self.dbname, str, path="$.dbname"))
        if not _cott_validated_construction():
            object.__setattr__(self, "user", _cott_validate_abi(self.user, str, path="$.user"))
        if not _cott_validated_construction():
            object.__setattr__(self, "host", _cott_validate_abi(self.host, str, path="$.host"))
        if not _cott_validated_construction():
            object.__setattr__(self, "port", _cott_validate_abi(self.port, str, path="$.port"))
        if not _cott_validated_construction():
            object.__setattr__(self, "pid", _cott_validate_abi(self.pid, I64, path="$.pid"))
        if not _cott_validated_construction():
            object.__setattr__(self, "superuser", _cott_validate_abi(self.superuser, bool, path="$.superuser"))
        if not _cott_validated_construction():
            object.__setattr__(self, "server_version", _cott_validate_abi(self.server_version, str, path="$.server_version"))
        if not _cott_validated_construction():
            object.__setattr__(self, "virtual_database", _cott_validate_abi(self.virtual_database, bool, path="$.virtual_database"))

"""Connection failures. message is the text upstream pgcli prints in red on
standard error before exiting 1 or keeping the previous connection: str() of
the psycopg/sshtunnel/OS exception, or the fixed texts named by each fn."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectError_Failed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectError_AliasMissing:
    __hash__ = None
    name: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectError_ServiceMissing:
    __hash__ = None
    service: str
    file: str

ConnectError: TypeAlias = Union[ConnectError_Failed, ConnectError_AliasMissing, ConnectError_ServiceMissing]

"""The arguments of PGCli.connect(database, host, user, port, passwd, dsn,
**kwargs). "" means not given. extra holds the remaining libpq keyword
arguments in order (for example sslmode from a URI)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionSpec:
    __hash__ = None
    database: str
    host: str
    user: str
    port: str
    password: str
    dsn: str
    extra: CottList[ConnectionParam]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "database", _cott_validate_abi(self.database, str, path="$.database"))
        if not _cott_validated_construction():
            object.__setattr__(self, "host", _cott_validate_abi(self.host, str, path="$.host"))
        if not _cott_validated_construction():
            object.__setattr__(self, "user", _cott_validate_abi(self.user, str, path="$.user"))
        if not _cott_validated_construction():
            object.__setattr__(self, "port", _cott_validate_abi(self.port, str, path="$.port"))
        if not _cott_validated_construction():
            object.__setattr__(self, "password", _cott_validate_abi(self.password, str, path="$.password"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dsn", _cott_validate_abi(self.dsn, str, path="$.dsn"))
        if not _cott_validated_construction():
            object.__setattr__(self, "extra", _cott_validate_abi(self.extra, CottList[ConnectionParam], path="$.extra"))

"""How the command line selects the connection (the branch order of upstream
cli())."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectTarget_Alias:
    __hash__ = None
    name: str
    uri: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectTarget_Uri:
    __hash__ = None
    uri: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectTarget_Conninfo:
    __hash__ = None
    dsn: str
    user: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectTarget_Service:
    __hash__ = None
    service: str
    user: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectTarget_Params:
    __hash__ = None
    database: str
    host: str
    user: str
    port: str

ConnectTarget: TypeAlias = Union[ConnectTarget_Alias, ConnectTarget_Uri, ConnectTarget_Conninfo, ConnectTarget_Service, ConnectTarget_Params]

"""The command-line and environment inputs of target selection. dbname_option is
-d/--dbname, dbname_argument the first positional argument (or $PGDATABASE),
username_option is -U/--username/-u/--user, username_argument the second
positional argument (or $PGUSER), host is -h/--host (or $PGHOST, default ""),
port is -p/--port as decimal text (or $PGPORT, default "5432"), pgservice is
$PGSERVICE when set, list_or_ping is -l/--list or --ping, dsn_alias is -D/--dsn
(or $DSN, default "") and alias_dsn is the [alias_dsn] section."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TargetRequest:
    __hash__ = None
    dbname_option: Option[str]
    dbname_argument: Option[str]
    username_option: Option[str]
    username_argument: Option[str]
    host: str
    port: str
    pgservice: Option[str]
    list_or_ping: bool
    dsn_alias: str
    alias_dsn: CottList[ConfigEntry]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "dbname_option", _cott_validate_abi(self.dbname_option, Option[str], path="$.dbname_option"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dbname_argument", _cott_validate_abi(self.dbname_argument, Option[str], path="$.dbname_argument"))
        if not _cott_validated_construction():
            object.__setattr__(self, "username_option", _cott_validate_abi(self.username_option, Option[str], path="$.username_option"))
        if not _cott_validated_construction():
            object.__setattr__(self, "username_argument", _cott_validate_abi(self.username_argument, Option[str], path="$.username_argument"))
        if not _cott_validated_construction():
            object.__setattr__(self, "host", _cott_validate_abi(self.host, str, path="$.host"))
        if not _cott_validated_construction():
            object.__setattr__(self, "port", _cott_validate_abi(self.port, str, path="$.port"))
        if not _cott_validated_construction():
            object.__setattr__(self, "pgservice", _cott_validate_abi(self.pgservice, Option[str], path="$.pgservice"))
        if not _cott_validated_construction():
            object.__setattr__(self, "list_or_ping", _cott_validate_abi(self.list_or_ping, bool, path="$.list_or_ping"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dsn_alias", _cott_validate_abi(self.dsn_alias, str, path="$.dsn_alias"))
        if not _cott_validated_construction():
            object.__setattr__(self, "alias_dsn", _cott_validate_abi(self.alias_dsn, CottList[ConfigEntry], path="$.alias_dsn"))

"""An SSH jump host parsed from a tunnel URL: port defaults to 22, username and
password are Nothing when the URL has none."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SshTunnelTarget:
    __hash__ = None
    host: str
    port: I64
    username: Option[str]
    password: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "host", _cott_validate_abi(self.host, str, path="$.host"))
        if not _cott_validated_construction():
            object.__setattr__(self, "port", _cott_validate_abi(self.port, I64, path="$.port"))
        if not _cott_validated_construction():
            object.__setattr__(self, "username", _cott_validate_abi(self.username, Option[str], path="$.username"))
        if not _cott_validated_construction():
            object.__setattr__(self, "password", _cott_validate_abi(self.password, Option[str], path="$.password"))

"""Everything PGCli.connect needs besides the spec. force_password_prompt is
-W/--password, never_password_prompt is -w/--no-password, keyring_enabled is
[main] keyring, explicit_timeout is --timeout, default_timeout is [main]
connect_timeout, pgpassword and pgconnect_timeout are the environment values
("" when unset), dsn_alias is the -D alias in use, explicit_tunnel is
--ssh-tunnel, dsn_tunnels is [dsn ssh tunnels] and host_tunnels is
[ssh tunnels]."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OpenRequest:
    __hash__ = None
    spec: ConnectionSpec
    application_name: str
    force_password_prompt: bool
    never_password_prompt: bool
    keyring_enabled: bool
    explicit_timeout: Option[I64]
    default_timeout: I64
    pgpassword: str
    pgconnect_timeout: str
    dsn_alias: Option[str]
    explicit_tunnel: Option[str]
    dsn_tunnels: CottList[ConfigEntry]
    host_tunnels: CottList[ConfigEntry]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "spec", _cott_validate_abi(self.spec, ConnectionSpec, path="$.spec"))
        if not _cott_validated_construction():
            object.__setattr__(self, "application_name", _cott_validate_abi(self.application_name, str, path="$.application_name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "force_password_prompt", _cott_validate_abi(self.force_password_prompt, bool, path="$.force_password_prompt"))
        if not _cott_validated_construction():
            object.__setattr__(self, "never_password_prompt", _cott_validate_abi(self.never_password_prompt, bool, path="$.never_password_prompt"))
        if not _cott_validated_construction():
            object.__setattr__(self, "keyring_enabled", _cott_validate_abi(self.keyring_enabled, bool, path="$.keyring_enabled"))
        if not _cott_validated_construction():
            object.__setattr__(self, "explicit_timeout", _cott_validate_abi(self.explicit_timeout, Option[I64], path="$.explicit_timeout"))
        if not _cott_validated_construction():
            object.__setattr__(self, "default_timeout", _cott_validate_abi(self.default_timeout, I64, path="$.default_timeout"))
        if not _cott_validated_construction():
            object.__setattr__(self, "pgpassword", _cott_validate_abi(self.pgpassword, str, path="$.pgpassword"))
        if not _cott_validated_construction():
            object.__setattr__(self, "pgconnect_timeout", _cott_validate_abi(self.pgconnect_timeout, str, path="$.pgconnect_timeout"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dsn_alias", _cott_validate_abi(self.dsn_alias, Option[str], path="$.dsn_alias"))
        if not _cott_validated_construction():
            object.__setattr__(self, "explicit_tunnel", _cott_validate_abi(self.explicit_tunnel, Option[str], path="$.explicit_tunnel"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dsn_tunnels", _cott_validate_abi(self.dsn_tunnels, CottList[ConfigEntry], path="$.dsn_tunnels"))
        if not _cott_validated_construction():
            object.__setattr__(self, "host_tunnels", _cott_validate_abi(self.host_tunnels, CottList[ConfigEntry], path="$.host_tunnels"))

"""Parameters for PGExecute.connect on an existing session: "" leaves the
current value. Used by \\c (database, user, host, port) and by reconnects
(all "")."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ReconnectRequest:
    __hash__ = None
    database: str
    user: str
    host: str
    port: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "database", _cott_validate_abi(self.database, str, path="$.database"))
        if not _cott_validated_construction():
            object.__setattr__(self, "user", _cott_validate_abi(self.user, str, path="$.user"))
        if not _cott_validated_construction():
            object.__setattr__(self, "host", _cott_validate_abi(self.host, str, path="$.host"))
        if not _cott_validated_construction():
            object.__setattr__(self, "port", _cott_validate_abi(self.port, str, path="$.port"))

"""The libpq transaction status of the session connection: Idle, Active (a
command in progress), InTransaction, InError (failed transaction block) or
Unknown (connection bad or closed)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionStatus_Idle:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionStatus_Active:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionStatus_InTransaction:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionStatus_InError:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransactionStatus_Unknown:
    pass

TransactionStatus: TypeAlias = Union[TransactionStatus_Idle, TransactionStatus_Active, TransactionStatus_InTransaction, TransactionStatus_InError, TransactionStatus_Unknown]

"""The target selection of upstream cli(), in this order:
username = username_argument; when both dbname_option and dbname_argument
are Some, username = dbname_argument (psql style: the positional database
becomes the user). database = dbname_option, else dbname_argument, else "".
user = username_option, else username, else "".
service: when database starts with "service=", the rest after those 8
characters; otherwise pgservice when Some; otherwise none.
is_conn_string = database contains "://", or database contains "=" and
there is no service.
When list_or_ping: an empty database becomes "postgres"; a connection
string whose parsed parameters (psycopg.conninfo.conninfo_to_dict) have no
nonempty dbname becomes psycopg.conninfo.make_conninfo(database,
dbname="postgres"); a connection string that fails to parse is kept.
Then: dsn_alias != "" selects Alias(name: dsn_alias, uri: the value of the
first alias_dsn entry named dsn_alias), or AliasMissing(name: dsn_alias)
when there is none; else database containing "://" selects Uri(database);
else database containing "=" with no service selects Conninfo(database,
user); else a service selects Service(service, user); else
Params(database, host, user, port)."""
"""PGCli.connect_uri: parse uri with psycopg.conninfo.conninfo_to_dict (URI or
key=value form) and map its parameters: dbname -> database, host, user, port
and password -> password; every other parameter goes to extra in the parsed
order. dsn is "". Values are converted with str(). A parse failure is
Failed(message: str(error))."""
"""parse_service_info on already-read text: skip_initial_comment drops every
line before the first line matching the regex "\\s*\\[" (the start of the
first section; all lines when there is none), then the remaining text is
parsed with the lock-selected configobj (ConfigObj(lines), default
options). Return Some(the keys and values of the section named service in
file order) or Nothing when there is no such section. A configobj
ParseError is Failed(message: str(error)) where the reported line number
counts the skipped lines too."""
"""connect_service's lookup: the service file is service_file ($PGSERVICEFILE)
when nonempty, else sysconfdir + "/.pg_service.conf" when sysconfdir
($PGSYSCONFDIR) is nonempty, else home + "/.pg_service.conf". When the file
does not exist the result is ServiceMissing(service, file: that path);
otherwise read it as text (newline="" semantics) and apply
parse_pg_service(text, service); Nothing becomes ServiceMissing(service,
file). Read failures are Failed(message: str(error))."""
"""get_connect_timeout: explicit when Some; otherwise Nothing when extra
contains a connect_timeout parameter, or dsn is nonempty and
conninfo_to_dict(dsn) has connect_timeout, or pgconnect_timeout is
nonempty; otherwise Some(default). An unparsable dsn counts as having no
connect_timeout."""
"""The tunnel selection of PGCli.connect: explicit when Some. Otherwise, when
dsn_alias is Some(alias), the value of the first dsn_tunnels entry whose
name, used as a Python regular expression, re.search-matches alias. Otherwise
the value of the first host_tunnels entry whose name re.search-matches host.
Otherwise Nothing. A result without "://" gets "ssh://" prepended."""
"""urllib.parse.urlparse(url) of an "ssh://..." URL: host is its hostname
("" when absent), port its port or 22, username and password its
username and password when present."""
"""PGCli.connect followed by PGExecute.__init__/connect, on the host:
1. user = spec.user, or getpass.getuser() when "". database = spec.database,
or user when "". kwargs = spec.extra plus application_name (added only when
extra has none).
2. timeout = real.pgcli.connection.choose_connect_timeout(explicit_timeout,
spec.dsn, kwargs, pgconnect_timeout, default_timeout); when Some(t) set
kwargs connect_timeout = str(t).
3. passwd = spec.password. Unless force_password_prompt, an empty passwd is
replaced by pgpassword, except when spec.dsn is nonempty and its parsed
parameters contain password. When force_password_prompt and passwd is
empty, prompt with click.prompt("Password for " + user, hide_input=True,
show_default=False, type=str).
4. key = user + "@" + host + "@" + port (the spec values; port "" stays "").
When passwd is empty and keyring_enabled, passwd = keyring.get_password(
"pgcli", key) or ""; any exception prints, in red on standard error with
click.secho, the text "Load your password from keyring returned:\\n" + str(e)
+ "\\nTo remove this message do one of the following:\\n- prepare keyring as
described at: https://keyring.readthedocs.io/en/stable/\\n- uninstall keyring:
pip uninstall keyring\\n- disable keyring in our configuration: add keyring =
False to [main]" and continues with "".
5. When spec.dsn is nonempty, host and port become the dsn's host and port
parameters when present.
6. Tunnel: url = real.pgcli.connection.find_ssh_tunnel_url(explicit_tunnel,
dsn_alias, host, dsn_tunnels, host_tunnels). When Some, parse it with
real.pgcli.connection.parse_ssh_tunnel_url and start
sshtunnel.SSHTunnelForwarder(local_bind_address=("127.0.0.1",),
remote_bind_address=(host, int(port or 5432)), ssh_address_or_host=(tunnel
host, tunnel port), logger=logging.getLogger("pgcli.main"), plus
ssh_username / ssh_password when present); keep the pgcli logger's handler
list unchanged across the start. A failure is Failed(message: str(error)).
Then connect through it: port = the forwarder's first local bind port;
with a dsn, dsn = make_conninfo(dsn, host=host, hostaddr="127.0.0.1",
port=port), otherwise kwargs hostaddr = "127.0.0.1". The original host is
kept for .pgpass and TLS verification.
7. PGExecute connect: params start from dbname=database, user, password=
passwd, host, port, dsn then kwargs, keeping only nonempty values; with a
dsn only dsn, password, hostaddr and connect_timeout are kept and a password
is folded into the dsn with make_conninfo(dsn, password=...). The conninfo
is make_conninfo(dsn, **others) with a dsn, else make_conninfo(**params).
psycopg.connect(conninfo), then autocommit = True; register a notification
handler that prints with click.secho(fg="green") 'Notification received on
channel "<channel>" (PID <pid>):\\n<payload>'. dbname, user, host and port
come from connection.info.get_parameters() (else from params). virtual
database detection runs SELECT 1 and treats psycopg.errors.ProtocolViolation
as a pgbouncer virtual database. An empty host becomes "pgbouncer" for a
virtual database, else the first value of SELECT setting FROM pg_settings
WHERE name = 'unix_socket_directories' ("" when no row). pid is
info.backend_pid, superuser is parameter_status("is_superuser") in ("on",
"1"), server_version is parameter_status("server_version") or "". Unless
virtual, register psycopg.types.string.TextLoader for date, time, timestamp,
timestamptz, bytea, json and jsonb so those values arrive as text.
8. When the first attempt raises psycopg.OperationalError or InterfaceError
whose first argument contains "no password supplied" or "password
authentication failed", and never_password_prompt is false, prompt as in
step 3 and retry once with the answer; other errors are not retried.
9. After success, when passwd is nonempty and keyring_enabled, store it with
keyring.set_password("pgcli", key, passwd); a failure prints the same
message as step 4 with "Set password in keyring returned:".
Any failure is Failed(message: str(error)); the caller prints it in red on
standard error and exits 1. Executor.params are the kept params,
Executor.tunnel holds the started forwarder."""
"""PGExecute.connect on an open session (called without a dsn argument): start
from executor.params, overlay the nonempty request values as dbname, user,
host and port (the dsn-only filtering of open_executor step 7 applies to a
dsn argument and does not happen here), then build the conninfo like
real.pgcli.connection.open_executor step 7: with a stored dsn,
make_conninfo(dsn, **every other param), so the overlaid values override
the dsn's own; otherwise make_conninfo(**params). Open a new
connection with the same post-connect steps (autocommit, notification
handler, parameters, host fallback, pid, superuser, server_version,
typecasters). Only after the new connection succeeds is the old one closed.
The tunnel is kept. A failure is Failed(message: str(error)) and leaves the
old connection open and usable."""
"""PGExecute.copy: open a second, independent session from executor.params
with the same post-connect steps as real.pgcli.connection.reconnect_executor
but without a notification handler, sharing the tunnel. The original
session is untouched. A failure is Failed(message: str(error))."""
"""Close the session's psycopg connection, ignoring errors. The tunnel is not
stopped here (upstream stops it at interpreter exit)."""
"""Stop the SSH forwarder when executor.tunnel is Some, ignoring errors
(upstream's atexit ssh_tunnel.stop)."""
"""Map connection.info.transaction_status (psycopg.pq.TransactionStatus IDLE,
ACTIVE, INTRANS, INERROR, UNKNOWN) to the enum. Reading it never contacts the
server. A closed connection reports Unknown."""
"""PGExecute.transaction_indicator: "?" for Unknown, "!" for InError, "*" for
Active or InTransaction, "" for Idle."""
"""PGExecute.short_host: an IP address (ipaddress.ip_address accepts it) is
returned unchanged; otherwise take the part before the first "," and then
the part before the first "."."""
"""PGExecute.search_path: SELECT * FROM unnest(current_schemas(true)) and
return the first column of every row; on psycopg.ProgrammingError fall back
to SELECT * FROM current_schemas(true) and return the array in its first
row. Other failures are Failed(message: str(error))."""
"""The use_local_timezone step of upstream cli(): server_tz = the first value
of "show time zone". local_tz = tzlocal.get_localzone_name().
When local_tz is None print on standard error, in yellow with click.secho,
"Failed to determine the local time zone", then "No local time zone
configuration found\\n", then "Continuing with the default time zone as
preset by the server (" + server_tz + ")", then, dimmed, "Set
`use_local_timezone = False` in the config to avoid trying to override the
server time zone\\n". When local_tz differs from server_tz print on standard
output in green "Using local time zone <local_tz> (server uses
<server_tz>)", then dimmed "Use `set time zone <TZ>` to override, or set
`use_local_timezone = False` in the config", and execute
psycopg.sql.SQL("set time zone {}").format(psycopg.sql.Identifier(local_tz)).
tzlocal.get_localzone_name() raising zoneinfo's ZoneInfoNotFoundError (a
KeyError subclass: catch it as KeyError, never import zoneinfo, which the
lock does not select) prints the same four stderr lines with
str(error.args[0]) instead of "No local time zone configuration found\\n".
Database errors are ignored after being logged."""
__all__ = ["ConnectError", "ConnectError_AliasMissing", "ConnectError_Failed", "ConnectError_ServiceMissing", "ConnectTarget", "ConnectTarget_Alias", "ConnectTarget_Conninfo", "ConnectTarget_Params", "ConnectTarget_Service", "ConnectTarget_Uri", "ConnectionHandle", "ConnectionParam", "ConnectionSpec", "Executor", "OpenRequest", "ReconnectRequest", "SshTunnelTarget", "TargetRequest", "TransactionStatus", "TransactionStatus_Active", "TransactionStatus_Idle", "TransactionStatus_InError", "TransactionStatus_InTransaction", "TransactionStatus_Unknown", "TunnelHandle"]
