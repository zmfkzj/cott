import os
import sys
from typing import Final, Never

from cott_runtime import CottList, Err, Nothing
from real.pgcli import parse_arguments, resolve_connection_plan, run_interactive
from real.pgcli_types import (
    CliCommand_Help,
    ClientError,
    ClientError_CatalogFailed,
    ClientError_ConnectionFailed,
    ClientError_EditorFailed,
    ClientError_ExportFailed,
    ClientError_FavoriteFailed,
    ClientError_HistoryFailed,
    ClientError_ImportFailed,
    ClientError_InvalidArguments,
    ClientError_InvalidCommand,
    ClientError_InvalidSql,
    ClientError_NotificationFailed,
    ClientError_PagerFailed,
    ClientError_QueryFailed,
    ClientError_TerminalFailed,
    ClientError_TransactionFailed,
    ClientError_TunnelUnsupported,
    EnvironmentInputs,
    InteractiveRequest,
    SessionOptions,
    TableFormat_Aligned,
    TransactionMode_AutoCommit,
)

_USAGE: Final[str] = "usage: pgcli-cott [DSN] [-h HOST | --host HOST] [-p PORT | --port PORT]\n                  [-U USER | --username USER] [-d DBNAME | --dbname DBNAME]\n                  [-c COMMAND | --command COMMAND] [--help]\n"
_CONNECTION_INVALID: Final[str] = "pgcli-cott: invalid connection settings\n"


def _error_category(error: ClientError) -> str:
    if isinstance(error, ClientError_InvalidArguments):
        return "invalid arguments"
    if isinstance(error, ClientError_InvalidCommand):
        return "invalid command"
    if isinstance(error, ClientError_InvalidSql):
        return "invalid sql"
    if isinstance(error, ClientError_ConnectionFailed):
        return "connection failed"
    if isinstance(error, ClientError_TunnelUnsupported):
        return "ssh tunnel unsupported"
    if isinstance(error, ClientError_CatalogFailed):
        return "catalog refresh failed"
    if isinstance(error, ClientError_QueryFailed):
        return "query failed"
    if isinstance(error, ClientError_TransactionFailed):
        return "transaction failed"
    if isinstance(error, ClientError_ImportFailed):
        return "import failed"
    if isinstance(error, ClientError_ExportFailed):
        return "export failed"
    if isinstance(error, ClientError_HistoryFailed):
        return "history failed"
    if isinstance(error, ClientError_FavoriteFailed):
        return "favorite failed"
    if isinstance(error, ClientError_EditorFailed):
        return "editor failed"
    if isinstance(error, ClientError_PagerFailed):
        return "pager failed"
    if isinstance(error, ClientError_NotificationFailed):
        return "notification failed"
    if isinstance(error, ClientError_TerminalFailed):
        return "terminal failed"
    return "unsupported format"


def run(arguments: CottList[str]) -> Never:
    try:
        argv: list[str] = [a for a in arguments]
        environment = EnvironmentInputs(
            host=os.environ.get("PGHOST", ""),
            port=os.environ.get("PGPORT", ""),
            user=os.environ.get("PGUSER", ""),
            password=os.environ.get("PGPASSWORD", ""),
            database=os.environ.get("PGDATABASE", ""),
        )
        parsed = parse_arguments(CottList(values=argv), environment)
        if isinstance(parsed, Err):
            error = parsed.error
            message = error.message if isinstance(error, ClientError_InvalidArguments) else "invalid arguments"
            sys.stderr.write(_USAGE)
            sys.stderr.write("pgcli-cott: " + message + "\n")
            sys.stderr.flush()
            sys.exit(2)
        command = parsed.value
        if isinstance(command, CliCommand_Help):
            sys.stdout.write(_USAGE)
            sys.stdout.flush()
            sys.exit(0)
        planned = resolve_connection_plan(command.connection, Nothing())
        if isinstance(planned, Err):
            sys.stderr.write(_CONNECTION_INVALID)
            sys.stderr.flush()
            sys.exit(2)
        options = SessionOptions(
            connection=planned.value,
            catalog_limit=1000,
            max_rows=1000,
            history=Nothing(),
            favorites=Nothing(),
            format=TableFormat_Aligned(),
            timing=False,
            pager=False,
            multiline=False,
            transaction=TransactionMode_AutoCommit(),
        )
        outcome = run_interactive(InteractiveRequest(options=options, initial_sql=command.initial_sql, mode=command.mode))
        if isinstance(outcome, Err):
            sys.stderr.write("pgcli-cott: " + _error_category(outcome.error) + "\n")
            sys.stderr.flush()
            sys.exit(1)
        sys.exit(0 if outcome.value.failures == 0 else 1)
    except KeyboardInterrupt:
        sys.exit(130)
