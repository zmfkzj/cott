from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.pgcli.connection_types import ConnectError, ConnectError_AliasMissing, ConnectError_Failed, ConnectError_ServiceMissing, ConnectTarget, ConnectTarget_Alias, ConnectTarget_Conninfo, ConnectTarget_Params, ConnectTarget_Service, ConnectTarget_Uri, ConnectionHandle, ConnectionParam, ConnectionSpec, Executor, OpenRequest, ReconnectRequest, SshTunnelTarget, TargetRequest, TransactionStatus, TransactionStatus_Active, TransactionStatus_Idle, TransactionStatus_InError, TransactionStatus_InTransaction, TransactionStatus_Unknown, TunnelHandle
from real.pgcli.config_types import ConfigEntry

def select_connect_target(request: TargetRequest) -> Result[ConnectTarget, ConnectError]:
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
    request = _cott_validate_abi(request, TargetRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/select_connect_target.py", "5aa89cbab81d63a442d38e92dbed1b35e34aaf4869954bcde30de341f9b500e9", "select_connect_target", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.select_connect_target")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.select_connect_target"
        if _error.span is None:
            _error.span = {"end_byte":6596,"end_column":1,"end_line":190,"start_byte":5059,"start_column":1,"start_line":161}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.select_connect_target", phase="implementation-call", span={"end_byte":6596,"end_column":1,"end_line":190,"start_byte":5059,"start_column":1,"start_line":161}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.select_connect_target", phase="implementation-call", span={"end_byte":6596,"end_column":1,"end_line":190,"start_byte":5059,"start_column":1,"start_line":161}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectTarget, ConnectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.connection.select_connect_target", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectError_AliasMissing,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.connection.select_connect_target", phase="error", span={"end_byte":6596,"end_column":1,"end_line":190,"start_byte":5059,"start_column":1,"start_line":161}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.connection.select_connect_target", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.connection.select_connect_target", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectError_AliasMissing:
        _cott_contract_condition(True, "real.pgcli.connection.select_connect_target", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and type(_cott_match_value.value) is ConnectTarget_Alias and True and True:
            name = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[0].name)
            return (_cott_contract_condition(((name == (request).dsn_alias)), "real.pgcli.connection.select_connect_target", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.connection.select_connect_target", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.select_connect_target", clause="ensures:1", phase="ensures", span={"end_byte":6541,"end_column":81,"end_line":184,"start_byte":6465,"start_column":5,"start_line":184}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectTarget, ConnectError], path="$.return", validator=_cott_validate_abi)
    return _result

def connection_spec_from_uri(uri: str) -> Result[ConnectionSpec, ConnectError]:
    """PGCli.connect_uri: parse uri with psycopg.conninfo.conninfo_to_dict (URI or
key=value form) and map its parameters: dbname -> database, host, user, port
and password -> password; every other parameter goes to extra in the parsed
order. dsn is "". Values are converted with str(). A parse failure is
Failed(message: str(error))."""
    uri = _cott_validate_abi(uri, str, path="$.uri")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/connection_spec_from_uri.py", "a3c2ec0200e056b849d62492d9d156bb685f7853ea4e0c33c302abae36b97750", "connection_spec_from_uri", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.connection_spec_from_uri")
        _result = _implementation(uri)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.connection_spec_from_uri"
        if _error.span is None:
            _error.span = {"end_byte":7138,"end_column":1,"end_line":205,"start_byte":6596,"start_column":1,"start_line":190}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.connection_spec_from_uri", phase="implementation-call", span={"end_byte":7138,"end_column":1,"end_line":205,"start_byte":6596,"start_column":1,"start_line":190}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.connection_spec_from_uri", phase="implementation-call", span={"end_byte":7138,"end_column":1,"end_line":205,"start_byte":6596,"start_column":1,"start_line":190}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ConnectionSpec, ConnectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.connection.connection_spec_from_uri", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.connection.connection_spec_from_uri", phase="error", span={"end_byte":7138,"end_column":1,"end_line":205,"start_byte":6596,"start_column":1,"start_line":190}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.connection.connection_spec_from_uri", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.connection.connection_spec_from_uri", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectError_Failed:
        _cott_contract_condition(True, "real.pgcli.connection.connection_spec_from_uri", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            spec = _cott_match_value.value
            return (_cott_contract_condition((((spec).dsn == "")), "real.pgcli.connection.connection_spec_from_uri", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.connection.connection_spec_from_uri", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.connection_spec_from_uri", clause="ensures:1", phase="ensures", span={"end_byte":7089,"end_column":46,"end_line":199,"start_byte":7048,"start_column":5,"start_line":199}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ConnectionSpec, ConnectError], path="$.return", validator=_cott_validate_abi)
    return _result

def parse_pg_service(text: str, service: str) -> Result[Option[CottList[ConnectionParam]], ConnectError]:
    """parse_service_info on already-read text: skip_initial_comment drops every
line before the first line matching the regex "\\s*\\[" (the start of the
first section; all lines when there is none), then the remaining text is
parsed with the lock-selected configobj (ConfigObj(lines), default
options). Return Some(the keys and values of the section named service in
file order) or Nothing when there is no such section. A configobj
ParseError is Failed(message: str(error)) where the reported line number
counts the skipped lines too."""
    text = _cott_validate_abi(text, str, path="$.text")
    service = _cott_validate_abi(service, str, path="$.service")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/parse_pg_service.py", "16d027e34baba1a9bc6ab71988232c599f7b79fa68ed148982168f367be5ffb4", "parse_pg_service", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.parse_pg_service")
        _result = _implementation(text, service)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.parse_pg_service"
        if _error.span is None:
            _error.span = {"end_byte":7949,"end_column":1,"end_line":223,"start_byte":7138,"start_column":1,"start_line":205}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.parse_pg_service", phase="implementation-call", span={"end_byte":7949,"end_column":1,"end_line":223,"start_byte":7138,"start_column":1,"start_line":205}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.parse_pg_service", phase="implementation-call", span={"end_byte":7949,"end_column":1,"end_line":223,"start_byte":7138,"start_column":1,"start_line":205}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Option[CottList[ConnectionParam]], ConnectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.connection.parse_pg_service", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.connection.parse_pg_service", phase="error", span={"end_byte":7949,"end_column":1,"end_line":223,"start_byte":7138,"start_column":1,"start_line":205}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.connection.parse_pg_service", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.connection.parse_pg_service", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectError_Failed:
        _cott_contract_condition(True, "real.pgcli.connection.parse_pg_service", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and type(_cott_match_value.value) is Some and True:
            params = _cott_match_value.value.value
            return (_cott_contract_condition((((service != "") and (len(params) >= 0))), "real.pgcli.connection.parse_pg_service", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.connection.parse_pg_service", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.parse_pg_service", clause="ensures:1", phase="ensures", span={"end_byte":7900,"end_column":80,"end_line":217,"start_byte":7825,"start_column":5,"start_line":217}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Option[CottList[ConnectionParam]], ConnectError], path="$.return", validator=_cott_validate_abi)
    return _result

def lookup_pg_service(service: str, service_file: str, sysconfdir: str, home: str) -> Result[Option[CottList[ConnectionParam]], ConnectError]:
    """connect_service's lookup: the service file is service_file ($PGSERVICEFILE)
when nonempty, else sysconfdir + "/.pg_service.conf" when sysconfdir
($PGSYSCONFDIR) is nonempty, else home + "/.pg_service.conf". When the file
does not exist the result is ServiceMissing(service, file: that path);
otherwise read it as text (newline="" semantics) and apply
parse_pg_service(text, service); Nothing becomes ServiceMissing(service,
file). Read failures are Failed(message: str(error))."""
    service = _cott_validate_abi(service, str, path="$.service")
    service_file = _cott_validate_abi(service_file, str, path="$.service_file")
    sysconfdir = _cott_validate_abi(sysconfdir, str, path="$.sysconfdir")
    home = _cott_validate_abi(home, str, path="$.home")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/lookup_pg_service.py", "049e413496bee2a432f3d1f122a81ca969f4740b10ee4992353f4bfc0dc6f1a3", "lookup_pg_service", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.lookup_pg_service")
        _result = _implementation(service, service_file, sysconfdir, home)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.lookup_pg_service"
        if _error.span is None:
            _error.span = {"end_byte":8808,"end_column":1,"end_line":246,"start_byte":7949,"start_column":1,"start_line":223}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.lookup_pg_service", phase="implementation-call", span={"end_byte":8808,"end_column":1,"end_line":246,"start_byte":7949,"start_column":1,"start_line":223}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.lookup_pg_service", phase="implementation-call", span={"end_byte":8808,"end_column":1,"end_line":246,"start_byte":7949,"start_column":1,"start_line":223}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Option[CottList[ConnectionParam]], ConnectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.connection.lookup_pg_service", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectError_ServiceMissing, ConnectError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.connection.lookup_pg_service", phase="error", span={"end_byte":8808,"end_column":1,"end_line":246,"start_byte":7949,"start_column":1,"start_line":223}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.connection.lookup_pg_service", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.connection.lookup_pg_service", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectError_ServiceMissing:
        _cott_contract_condition(True, "real.pgcli.connection.lookup_pg_service", "error:2")
    if type(_result) is Err and type(_result.error) is ConnectError_Failed:
        _cott_contract_condition(True, "real.pgcli.connection.lookup_pg_service", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and type(_cott_match_value.value) is Some and True:
            params = _cott_match_value.value.value
            return (_cott_contract_condition((((service != "") and (len(params) >= 0))), "real.pgcli.connection.lookup_pg_service", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.connection.lookup_pg_service", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.lookup_pg_service", clause="ensures:1", phase="ensures", span={"end_byte":8712,"end_column":80,"end_line":239,"start_byte":8637,"start_column":5,"start_line":239}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Option[CottList[ConnectionParam]], ConnectError], path="$.return", validator=_cott_validate_abi)
    return _result

def choose_connect_timeout(explicit: Option[I64], dsn: str, extra: CottList[ConnectionParam], pgconnect_timeout: str, default: I64) -> Option[I64]:
    """get_connect_timeout: explicit when Some; otherwise Nothing when extra
contains a connect_timeout parameter, or dsn is nonempty and
conninfo_to_dict(dsn) has connect_timeout, or pgconnect_timeout is
nonempty; otherwise Some(default). An unparsable dsn counts as having no
connect_timeout."""
    explicit = _cott_validate_abi(explicit, Option[I64], path="$.explicit")
    dsn = _cott_validate_abi(dsn, str, path="$.dsn")
    extra = _cott_validate_abi(extra, CottList[ConnectionParam], path="$.extra")
    pgconnect_timeout = _cott_validate_abi(pgconnect_timeout, str, path="$.pgconnect_timeout")
    default = _cott_validate_abi(default, I64, path="$.default")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/choose_connect_timeout.py", "e499f32cae0da61287d1d62b5c7bc1ac5880124cc796b135a8caa6e9a484c4e1", "choose_connect_timeout", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.choose_connect_timeout")
        _result = _implementation(explicit, dsn, extra, pgconnect_timeout, default)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.choose_connect_timeout"
        if _error.span is None:
            _error.span = {"end_byte":9386,"end_column":1,"end_line":265,"start_byte":8808,"start_column":1,"start_line":246}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.choose_connect_timeout", phase="implementation-call", span={"end_byte":9386,"end_column":1,"end_line":265,"start_byte":8808,"start_column":1,"start_line":246}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.choose_connect_timeout", phase="implementation-call", span={"end_byte":9386,"end_column":1,"end_line":265,"start_byte":8808,"start_column":1,"start_line":246}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[I64], path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = explicit
        if type(_cott_match_value) is Some and True:
            return (_cott_contract_condition(((_result == explicit)), "real.pgcli.connection.choose_connect_timeout", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.connection.choose_connect_timeout", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.choose_connect_timeout", clause="ensures:1", phase="ensures", span={"end_byte":9368,"end_column":66,"end_line":261,"start_byte":9307,"start_column":5,"start_line":261}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[I64], path="$.return", validator=_cott_validate_abi)
    return _result

def find_ssh_tunnel_url(explicit: Option[str], dsn_alias: Option[str], host: str, dsn_tunnels: CottList[ConfigEntry], host_tunnels: CottList[ConfigEntry]) -> Option[str]:
    """The tunnel selection of PGCli.connect: explicit when Some. Otherwise, when
dsn_alias is Some(alias), the value of the first dsn_tunnels entry whose
name, used as a Python regular expression, re.search-matches alias. Otherwise
the value of the first host_tunnels entry whose name re.search-matches host.
Otherwise Nothing. A result without "://" gets "ssh://" prepended."""
    explicit = _cott_validate_abi(explicit, Option[str], path="$.explicit")
    dsn_alias = _cott_validate_abi(dsn_alias, Option[str], path="$.dsn_alias")
    host = _cott_validate_abi(host, str, path="$.host")
    dsn_tunnels = _cott_validate_abi(dsn_tunnels, CottList[ConfigEntry], path="$.dsn_tunnels")
    host_tunnels = _cott_validate_abi(host_tunnels, CottList[ConfigEntry], path="$.host_tunnels")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/find_ssh_tunnel_url.py", "da1f28e18cc785f75bb6ad1bfdb87db3763fe9bd60bfdee2374ec38ded2ed20c", "find_ssh_tunnel_url", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.find_ssh_tunnel_url")
        _result = _implementation(explicit, dsn_alias, host, dsn_tunnels, host_tunnels)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.find_ssh_tunnel_url"
        if _error.span is None:
            _error.span = {"end_byte":10088,"end_column":1,"end_line":284,"start_byte":9386,"start_column":1,"start_line":265}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.find_ssh_tunnel_url", phase="implementation-call", span={"end_byte":10088,"end_column":1,"end_line":284,"start_byte":9386,"start_column":1,"start_line":265}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.find_ssh_tunnel_url", phase="implementation-call", span={"end_byte":10088,"end_column":1,"end_line":284,"start_byte":9386,"start_column":1,"start_line":265}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[str], path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            url = _cott_match_value.value
            return (_cott_contract_condition((("://" in url)), "real.pgcli.connection.find_ssh_tunnel_url", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.connection.find_ssh_tunnel_url", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.find_ssh_tunnel_url", clause="ensures:1", phase="ensures", span={"end_byte":10070,"end_column":53,"end_line":280,"start_byte":10022,"start_column":5,"start_line":280}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[str], path="$.return", validator=_cott_validate_abi)
    return _result

def parse_ssh_tunnel_url(url: str) -> SshTunnelTarget:
    """urllib.parse.urlparse(url) of an "ssh://..." URL: host is its hostname
("" when absent), port its port or 22, username and password its
username and password when present."""
    url = _cott_validate_abi(url, str, path="$.url")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/parse_ssh_tunnel_url.py", "8e031a4099f678f3d97cb5d3fba035abdad55facf4f992a42fab2f24e0d4a58e", "parse_ssh_tunnel_url", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.parse_ssh_tunnel_url")
        _result = _implementation(url)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.parse_ssh_tunnel_url"
        if _error.span is None:
            _error.span = {"end_byte":10394,"end_column":1,"end_line":295,"start_byte":10088,"start_column":1,"start_line":284}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.parse_ssh_tunnel_url", phase="implementation-call", span={"end_byte":10394,"end_column":1,"end_line":295,"start_byte":10088,"start_column":1,"start_line":284}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.parse_ssh_tunnel_url", phase="implementation-call", span={"end_byte":10394,"end_column":1,"end_line":295,"start_byte":10088,"start_column":1,"start_line":284}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SshTunnelTarget, path="$.return")
    if not (_cott_contract_condition((((_result).port > 0)), "real.pgcli.connection.parse_ssh_tunnel_url", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.parse_ssh_tunnel_url", clause="ensures:1", phase="ensures", span={"end_byte":10376,"end_column":30,"end_line":291,"start_byte":10351,"start_column":5,"start_line":291}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, SshTunnelTarget, path="$.return", validator=_cott_validate_abi)
    return _result

def open_executor(request: OpenRequest) -> Result[Executor, ConnectError]:
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
    request = _cott_validate_abi(request, OpenRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/open_executor.py", "66b3abe0fa983bab9a227c95b8b48ee79eb4146d7b3edbcf3a31060a44185ab9", "open_executor", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.open_executor")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.open_executor"
        if _error.span is None:
            _error.span = {"end_byte":15052,"end_column":1,"end_line":366,"start_byte":10394,"start_column":1,"start_line":295}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.open_executor", phase="implementation-call", span={"end_byte":15052,"end_column":1,"end_line":366,"start_byte":10394,"start_column":1,"start_line":295}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.open_executor", phase="implementation-call", span={"end_byte":15052,"end_column":1,"end_line":366,"start_byte":10394,"start_column":1,"start_line":295}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Executor, ConnectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.connection.open_executor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.connection.open_executor", phase="error", span={"end_byte":15052,"end_column":1,"end_line":366,"start_byte":10394,"start_column":1,"start_line":295}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.connection.open_executor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.connection.open_executor", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectError_Failed:
        _cott_contract_condition(True, "real.pgcli.connection.open_executor", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            executor = _cott_match_value.value
            return (_cott_contract_condition(((((executor).dbname != "") or (executor).virtual_database)), "real.pgcli.connection.open_executor", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.connection.open_executor", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.open_executor", clause="ensures:1", phase="ensures", span={"end_byte":14958,"end_column":86,"end_line":360,"start_byte":14877,"start_column":5,"start_line":360}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Executor, ConnectError], path="$.return", validator=_cott_validate_abi)
    return _result

def reconnect_executor(executor: Executor, request: ReconnectRequest) -> Result[Executor, ConnectError]:
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
    executor = _cott_validate_abi(executor, Executor, path="$.executor")
    request = _cott_validate_abi(request, ReconnectRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/reconnect_executor.py", "d93300d28d5d0efcf2f795d4189ddfe4ad3b28cbb6fe51471d0ad395a0cb3195", "reconnect_executor", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.reconnect_executor")
        _result = _implementation(executor, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.reconnect_executor"
        if _error.span is None:
            _error.span = {"end_byte":16257,"end_column":1,"end_line":391,"start_byte":15052,"start_column":1,"start_line":366}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.reconnect_executor", phase="implementation-call", span={"end_byte":16257,"end_column":1,"end_line":391,"start_byte":15052,"start_column":1,"start_line":366}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.reconnect_executor", phase="implementation-call", span={"end_byte":16257,"end_column":1,"end_line":391,"start_byte":15052,"start_column":1,"start_line":366}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Executor, ConnectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.connection.reconnect_executor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.connection.reconnect_executor", phase="error", span={"end_byte":16257,"end_column":1,"end_line":391,"start_byte":15052,"start_column":1,"start_line":366}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.connection.reconnect_executor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.connection.reconnect_executor", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectError_Failed:
        _cott_contract_condition(True, "real.pgcli.connection.reconnect_executor", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            reconnected = _cott_match_value.value
            return (_cott_contract_condition((((((request).database == "") or ((reconnected).dbname == (request).database)) or (reconnected).virtual_database)), "real.pgcli.connection.reconnect_executor", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.connection.reconnect_executor", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.reconnect_executor", clause="ensures:1", phase="ensures", span={"end_byte":16186,"end_column":137,"end_line":385,"start_byte":16054,"start_column":5,"start_line":385}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Executor, ConnectError], path="$.return", validator=_cott_validate_abi)
    return _result

def copy_executor(executor: Executor) -> Result[Executor, ConnectError]:
    """PGExecute.copy: open a second, independent session from executor.params
with the same post-connect steps as real.pgcli.connection.reconnect_executor
but without a notification handler, sharing the tunnel. The original
session is untouched. A failure is Failed(message: str(error))."""
    executor = _cott_validate_abi(executor, Executor, path="$.executor")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/copy_executor.py", "2f8caec4e58c39a024709fadad7bcd2158d92b54da20eefffd5209ecf0ecbc70", "copy_executor", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.copy_executor")
        _result = _implementation(executor)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.copy_executor"
        if _error.span is None:
            _error.span = {"end_byte":16784,"end_column":1,"end_line":405,"start_byte":16257,"start_column":1,"start_line":391}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.copy_executor", phase="implementation-call", span={"end_byte":16784,"end_column":1,"end_line":405,"start_byte":16257,"start_column":1,"start_line":391}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.copy_executor", phase="implementation-call", span={"end_byte":16784,"end_column":1,"end_line":405,"start_byte":16257,"start_column":1,"start_line":391}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Executor, ConnectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.connection.copy_executor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.connection.copy_executor", phase="error", span={"end_byte":16784,"end_column":1,"end_line":405,"start_byte":16257,"start_column":1,"start_line":391}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.connection.copy_executor", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.connection.copy_executor", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectError_Failed:
        _cott_contract_condition(True, "real.pgcli.connection.copy_executor", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            copied = _cott_match_value.value
            return (_cott_contract_condition((((copied).params == (executor).params)), "real.pgcli.connection.copy_executor", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.connection.copy_executor", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.copy_executor", clause="ensures:1", phase="ensures", span={"end_byte":16713,"end_column":66,"end_line":399,"start_byte":16652,"start_column":5,"start_line":399}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Executor, ConnectError], path="$.return", validator=_cott_validate_abi)
    return _result

def close_executor(executor: Executor) -> Unit:
    """Close the session's psycopg connection, ignoring errors. The tunnel is not
stopped here (upstream stops it at interpreter exit)."""
    executor = _cott_validate_abi(executor, Executor, path="$.executor")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/close_executor.py", "40c5d3533e96383dfe82302ef11eed62bce34682f4ec5bfdacb10ed6a5a71794", "close_executor", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.close_executor")
        _result = _implementation(executor)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.close_executor"
        if _error.span is None:
            _error.span = {"end_byte":17012,"end_column":1,"end_line":413,"start_byte":16784,"start_column":1,"start_line":405}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.close_executor", phase="implementation-call", span={"end_byte":17012,"end_column":1,"end_line":413,"start_byte":16784,"start_column":1,"start_line":405}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.close_executor", phase="implementation-call", span={"end_byte":17012,"end_column":1,"end_line":413,"start_byte":16784,"start_column":1,"start_line":405}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Unit, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Unit, path="$.return", validator=_cott_validate_abi)
    return _result

def stop_executor_tunnel(executor: Executor) -> Unit:
    """Stop the SSH forwarder when executor.tunnel is Some, ignoring errors
(upstream's atexit ssh_tunnel.stop)."""
    executor = _cott_validate_abi(executor, Executor, path="$.executor")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/stop_executor_tunnel.py", "86d14994141655734035f6e0e62771cb96479f06c180373e645f617877cacbc2", "stop_executor_tunnel", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.stop_executor_tunnel")
        _result = _implementation(executor)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.stop_executor_tunnel"
        if _error.span is None:
            _error.span = {"end_byte":17223,"end_column":1,"end_line":421,"start_byte":17012,"start_column":1,"start_line":413}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.stop_executor_tunnel", phase="implementation-call", span={"end_byte":17223,"end_column":1,"end_line":421,"start_byte":17012,"start_column":1,"start_line":413}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.stop_executor_tunnel", phase="implementation-call", span={"end_byte":17223,"end_column":1,"end_line":421,"start_byte":17012,"start_column":1,"start_line":413}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Unit, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Unit, path="$.return", validator=_cott_validate_abi)
    return _result

def executor_transaction_status(executor: Executor) -> TransactionStatus:
    """Map connection.info.transaction_status (psycopg.pq.TransactionStatus IDLE,
ACTIVE, INTRANS, INERROR, UNKNOWN) to the enum. Reading it never contacts the
server. A closed connection reports Unknown."""
    executor = _cott_validate_abi(executor, Executor, path="$.executor")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/executor_transaction_status.py", "6b6daff7ab767fdeb79dcebeec6d98ff60c196ea3d0633159700796634625941", "executor_transaction_status", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.executor_transaction_status")
        _result = _implementation(executor)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.executor_transaction_status"
        if _error.span is None:
            _error.span = {"end_byte":17556,"end_column":1,"end_line":430,"start_byte":17223,"start_column":1,"start_line":421}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.executor_transaction_status", phase="implementation-call", span={"end_byte":17556,"end_column":1,"end_line":430,"start_byte":17223,"start_column":1,"start_line":421}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.executor_transaction_status", phase="implementation-call", span={"end_byte":17556,"end_column":1,"end_line":430,"start_byte":17223,"start_column":1,"start_line":421}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, TransactionStatus, path="$.return")
    _result = _cott_wrap_async_protocol(_result, TransactionStatus, path="$.return", validator=_cott_validate_abi)
    return _result

def transaction_indicator(status: TransactionStatus) -> str:
    """PGExecute.transaction_indicator: "?" for Unknown, "!" for InError, "*" for
Active or InTransaction, "" for Idle."""
    status = _cott_validate_abi(status, TransactionStatus, path="$.status")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/transaction_indicator.py", "6b9b81936ac9aeec12cca7cba263df18257e635e2065fe3b50454dd264817ac3", "transaction_indicator", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.transaction_indicator")
        _result = _implementation(status)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.transaction_indicator"
        if _error.span is None:
            _error.span = {"end_byte":18007,"end_column":1,"end_line":445,"start_byte":17556,"start_column":1,"start_line":430}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.transaction_indicator", phase="implementation-call", span={"end_byte":18007,"end_column":1,"end_line":445,"start_byte":17556,"start_column":1,"start_line":430}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.transaction_indicator", phase="implementation-call", span={"end_byte":18007,"end_column":1,"end_line":445,"start_byte":17556,"start_column":1,"start_line":430}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = status
        if type(_cott_match_value) is TransactionStatus_Idle:
            return (_cott_contract_condition(((_result == "")), "real.pgcli.connection.transaction_indicator", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.connection.transaction_indicator", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.transaction_indicator", clause="ensures:1", phase="ensures", span={"end_byte":17820,"end_column":37,"end_line":437,"start_byte":17792,"start_column":9,"start_line":437}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = status
        if type(_cott_match_value) is TransactionStatus_Active:
            return (_cott_contract_condition(((_result == "*")), "real.pgcli.connection.transaction_indicator", "ensures:2"))
        _cott_contract_condition((False), "real.pgcli.connection.transaction_indicator", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.transaction_indicator", clause="ensures:2", phase="ensures", span={"end_byte":17860,"end_column":40,"end_line":438,"start_byte":17829,"start_column":9,"start_line":438}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = status
        if type(_cott_match_value) is TransactionStatus_InTransaction:
            return (_cott_contract_condition(((_result == "*")), "real.pgcli.connection.transaction_indicator", "ensures:3"))
        _cott_contract_condition((False), "real.pgcli.connection.transaction_indicator", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.transaction_indicator", clause="ensures:3", phase="ensures", span={"end_byte":17907,"end_column":47,"end_line":439,"start_byte":17869,"start_column":9,"start_line":439}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = status
        if type(_cott_match_value) is TransactionStatus_InError:
            return (_cott_contract_condition(((_result == "!")), "real.pgcli.connection.transaction_indicator", "ensures:4"))
        _cott_contract_condition((False), "real.pgcli.connection.transaction_indicator", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.transaction_indicator", clause="ensures:4", phase="ensures", span={"end_byte":17948,"end_column":41,"end_line":440,"start_byte":17916,"start_column":9,"start_line":440}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = status
        if type(_cott_match_value) is TransactionStatus_Unknown:
            return (_cott_contract_condition(((_result == "?")), "real.pgcli.connection.transaction_indicator", "ensures:5"))
        _cott_contract_condition((False), "real.pgcli.connection.transaction_indicator", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.transaction_indicator", clause="ensures:5", phase="ensures", span={"end_byte":17989,"end_column":41,"end_line":441,"start_byte":17957,"start_column":9,"start_line":441}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def short_host_name(host: str) -> str:
    """PGExecute.short_host: an IP address (ipaddress.ip_address accepts it) is
returned unchanged; otherwise take the part before the first "," and then
the part before the first "."."""
    host = _cott_validate_abi(host, str, path="$.host")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/short_host_name.py", "118fbc53b5f709c966f8ba8ad5ba71e24bd7dadba3dd06e5052b7c2d3266a9b6", "short_host_name", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.short_host_name")
        _result = _implementation(host)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.short_host_name"
        if _error.span is None:
            _error.span = {"end_byte":18336,"end_column":1,"end_line":456,"start_byte":18007,"start_column":1,"start_line":445}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.short_host_name", phase="implementation-call", span={"end_byte":18336,"end_column":1,"end_line":456,"start_byte":18007,"start_column":1,"start_line":445}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.short_host_name", phase="implementation-call", span={"end_byte":18336,"end_column":1,"end_line":456,"start_byte":18007,"start_column":1,"start_line":445}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not (_cott_contract_condition(((("%" in host) or (not ("," in _result)))), "real.pgcli.connection.short_host_name", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.short_host_name", clause="ensures:1", phase="ensures", span={"end_byte":18318,"end_column":63,"end_line":452,"start_byte":18260,"start_column":5,"start_line":452}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def read_search_path(executor: Executor) -> Result[CottList[str], ConnectError]:
    """PGExecute.search_path: SELECT * FROM unnest(current_schemas(true)) and
return the first column of every row; on psycopg.ProgrammingError fall back
to SELECT * FROM current_schemas(true) and return the array in its first
row. Other failures are Failed(message: str(error))."""
    executor = _cott_validate_abi(executor, Executor, path="$.executor")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/read_search_path.py", "10ccacaf8a9f15e03dc83ddeb1188ab7ed0c87fd5001a1fde0e7da6d80e1e633", "read_search_path", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.read_search_path")
        _result = _implementation(executor)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.read_search_path"
        if _error.span is None:
            _error.span = {"end_byte":18828,"end_column":1,"end_line":470,"start_byte":18336,"start_column":1,"start_line":456}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.read_search_path", phase="implementation-call", span={"end_byte":18828,"end_column":1,"end_line":470,"start_byte":18336,"start_column":1,"start_line":456}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.read_search_path", phase="implementation-call", span={"end_byte":18828,"end_column":1,"end_line":470,"start_byte":18336,"start_column":1,"start_line":456}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], ConnectError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.connection.read_search_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConnectError_Failed,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.connection.read_search_path", phase="error", span={"end_byte":18828,"end_column":1,"end_line":470,"start_byte":18336,"start_column":1,"start_line":456}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.connection.read_search_path", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.connection.read_search_path", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConnectError_Failed:
        _cott_contract_condition(True, "real.pgcli.connection.read_search_path", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            path = _cott_match_value.value
            return (_cott_contract_condition(((len(path) >= 0)), "real.pgcli.connection.read_search_path", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.connection.read_search_path", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.connection.read_search_path", clause="ensures:1", phase="ensures", span={"end_byte":18766,"end_column":45,"end_line":464,"start_byte":18726,"start_column":5,"start_line":464}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], ConnectError], path="$.return", validator=_cott_validate_abi)
    return _result

def apply_local_timezone(executor: Executor) -> Unit:
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
    executor = _cott_validate_abi(executor, Executor, path="$.executor")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/connection/apply_local_timezone.py", "51ab6605adddaa53ca58fb9d330e68323f12e97ae390c199adca437e72fc6c9c", "apply_local_timezone", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.connection.apply_local_timezone")
        _result = _implementation(executor)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.connection.apply_local_timezone"
        if _error.span is None:
            _error.span = {"end_byte":20203,"end_column":1,"end_line":493,"start_byte":18828,"start_column":1,"start_line":470}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.connection.apply_local_timezone", phase="implementation-call", span={"end_byte":20203,"end_column":1,"end_line":493,"start_byte":18828,"start_column":1,"start_line":470}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.connection.apply_local_timezone", phase="implementation-call", span={"end_byte":20203,"end_column":1,"end_line":493,"start_byte":18828,"start_column":1,"start_line":470}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Unit, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Unit, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["ConnectError", "ConnectError_AliasMissing", "ConnectError_Failed", "ConnectError_ServiceMissing", "ConnectTarget", "ConnectTarget_Alias", "ConnectTarget_Conninfo", "ConnectTarget_Params", "ConnectTarget_Service", "ConnectTarget_Uri", "ConnectionHandle", "ConnectionParam", "ConnectionSpec", "Executor", "OpenRequest", "ReconnectRequest", "SshTunnelTarget", "TargetRequest", "TransactionStatus", "TransactionStatus_Active", "TransactionStatus_Idle", "TransactionStatus_InError", "TransactionStatus_InTransaction", "TransactionStatus_Unknown", "TunnelHandle", "apply_local_timezone", "choose_connect_timeout", "close_executor", "connection_spec_from_uri", "copy_executor", "executor_transaction_status", "find_ssh_tunnel_url", "lookup_pg_service", "open_executor", "parse_pg_service", "parse_ssh_tunnel_url", "read_search_path", "reconnect_executor", "select_connect_target", "short_host_name", "stop_executor_tunnel", "transaction_indicator"]
