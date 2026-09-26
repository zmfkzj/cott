from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.pgcli.connection_types import ConnectError as ConnectError, ConnectError_AliasMissing as ConnectError_AliasMissing, ConnectError_Failed as ConnectError_Failed, ConnectError_ServiceMissing as ConnectError_ServiceMissing, ConnectTarget as ConnectTarget, ConnectTarget_Alias as ConnectTarget_Alias, ConnectTarget_Conninfo as ConnectTarget_Conninfo, ConnectTarget_Params as ConnectTarget_Params, ConnectTarget_Service as ConnectTarget_Service, ConnectTarget_Uri as ConnectTarget_Uri, ConnectionHandle as ConnectionHandle, ConnectionParam as ConnectionParam, ConnectionSpec as ConnectionSpec, Executor as Executor, OpenRequest as OpenRequest, ReconnectRequest as ReconnectRequest, SshTunnelTarget as SshTunnelTarget, TargetRequest as TargetRequest, TransactionStatus as TransactionStatus, TransactionStatus_Active as TransactionStatus_Active, TransactionStatus_Idle as TransactionStatus_Idle, TransactionStatus_InError as TransactionStatus_InError, TransactionStatus_InTransaction as TransactionStatus_InTransaction, TransactionStatus_Unknown as TransactionStatus_Unknown, TunnelHandle as TunnelHandle
from real.pgcli.config_types import ConfigEntry
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
def select_connect_target(request: TargetRequest) -> Result[ConnectTarget, ConnectError]: ...

"""PGCli.connect_uri: parse uri with psycopg.conninfo.conninfo_to_dict (URI or
key=value form) and map its parameters: dbname -> database, host, user, port
and password -> password; every other parameter goes to extra in the parsed
order. dsn is "". Values are converted with str(). A parse failure is
Failed(message: str(error))."""
def connection_spec_from_uri(uri: str) -> Result[ConnectionSpec, ConnectError]: ...

"""parse_service_info on already-read text: skip_initial_comment drops every
line before the first line matching the regex "\\s*\\[" (the start of the
first section; all lines when there is none), then the remaining text is
parsed with the lock-selected configobj (ConfigObj(lines), default
options). Return Some(the keys and values of the section named service in
file order) or Nothing when there is no such section. A configobj
ParseError is Failed(message: str(error)) where the reported line number
counts the skipped lines too."""
def parse_pg_service(text: str, service: str) -> Result[Option[CottList[ConnectionParam]], ConnectError]: ...

"""connect_service's lookup: the service file is service_file ($PGSERVICEFILE)
when nonempty, else sysconfdir + "/.pg_service.conf" when sysconfdir
($PGSYSCONFDIR) is nonempty, else home + "/.pg_service.conf". When the file
does not exist the result is ServiceMissing(service, file: that path);
otherwise read it as text (newline="" semantics) and apply
parse_pg_service(text, service); Nothing becomes ServiceMissing(service,
file). Read failures are Failed(message: str(error))."""
def lookup_pg_service(service: str, service_file: str, sysconfdir: str, home: str) -> Result[Option[CottList[ConnectionParam]], ConnectError]: ...

"""get_connect_timeout: explicit when Some; otherwise Nothing when extra
contains a connect_timeout parameter, or dsn is nonempty and
conninfo_to_dict(dsn) has connect_timeout, or pgconnect_timeout is
nonempty; otherwise Some(default). An unparsable dsn counts as having no
connect_timeout."""
def choose_connect_timeout(explicit: Option[I64], dsn: str, extra: CottList[ConnectionParam], pgconnect_timeout: str, default: I64) -> Option[I64]: ...

"""The tunnel selection of PGCli.connect: explicit when Some. Otherwise, when
dsn_alias is Some(alias), the value of the first dsn_tunnels entry whose
name, used as a Python regular expression, re.search-matches alias. Otherwise
the value of the first host_tunnels entry whose name re.search-matches host.
Otherwise Nothing. A result without "://" gets "ssh://" prepended."""
def find_ssh_tunnel_url(explicit: Option[str], dsn_alias: Option[str], host: str, dsn_tunnels: CottList[ConfigEntry], host_tunnels: CottList[ConfigEntry]) -> Option[str]: ...

"""urllib.parse.urlparse(url) of an "ssh://..." URL: host is its hostname
("" when absent), port its port or 22, username and password its
username and password when present."""
def parse_ssh_tunnel_url(url: str) -> SshTunnelTarget: ...

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
def open_executor(request: OpenRequest) -> Result[Executor, ConnectError]: ...

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
def reconnect_executor(executor: Executor, request: ReconnectRequest) -> Result[Executor, ConnectError]: ...

"""PGExecute.copy: open a second, independent session from executor.params
with the same post-connect steps as real.pgcli.connection.reconnect_executor
but without a notification handler, sharing the tunnel. The original
session is untouched. A failure is Failed(message: str(error))."""
def copy_executor(executor: Executor) -> Result[Executor, ConnectError]: ...

"""Close the session's psycopg connection, ignoring errors. The tunnel is not
stopped here (upstream stops it at interpreter exit)."""
def close_executor(executor: Executor) -> Unit: ...

"""Stop the SSH forwarder when executor.tunnel is Some, ignoring errors
(upstream's atexit ssh_tunnel.stop)."""
def stop_executor_tunnel(executor: Executor) -> Unit: ...

"""Map connection.info.transaction_status (psycopg.pq.TransactionStatus IDLE,
ACTIVE, INTRANS, INERROR, UNKNOWN) to the enum. Reading it never contacts the
server. A closed connection reports Unknown."""
def executor_transaction_status(executor: Executor) -> TransactionStatus: ...

"""PGExecute.transaction_indicator: "?" for Unknown, "!" for InError, "*" for
Active or InTransaction, "" for Idle."""
def transaction_indicator(status: TransactionStatus) -> str: ...

"""PGExecute.short_host: an IP address (ipaddress.ip_address accepts it) is
returned unchanged; otherwise take the part before the first "," and then
the part before the first "."."""
def short_host_name(host: str) -> str: ...

"""PGExecute.search_path: SELECT * FROM unnest(current_schemas(true)) and
return the first column of every row; on psycopg.ProgrammingError fall back
to SELECT * FROM current_schemas(true) and return the array in its first
row. Other failures are Failed(message: str(error))."""
def read_search_path(executor: Executor) -> Result[CottList[str], ConnectError]: ...

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
def apply_local_timezone(executor: Executor) -> Unit: ...

__all__ = ["ConnectError", "ConnectError_AliasMissing", "ConnectError_Failed", "ConnectError_ServiceMissing", "ConnectTarget", "ConnectTarget_Alias", "ConnectTarget_Conninfo", "ConnectTarget_Params", "ConnectTarget_Service", "ConnectTarget_Uri", "ConnectionHandle", "ConnectionParam", "ConnectionSpec", "Executor", "OpenRequest", "ReconnectRequest", "SshTunnelTarget", "TargetRequest", "TransactionStatus", "TransactionStatus_Active", "TransactionStatus_Idle", "TransactionStatus_InError", "TransactionStatus_InTransaction", "TransactionStatus_Unknown", "TunnelHandle", "apply_local_timezone", "choose_connect_timeout", "close_executor", "connection_spec_from_uri", "copy_executor", "executor_transaction_status", "find_ssh_tunnel_url", "lookup_pg_service", "open_executor", "parse_pg_service", "parse_ssh_tunnel_url", "read_search_path", "reconnect_executor", "select_connect_target", "short_host_name", "stop_executor_tunnel", "transaction_indicator"]
