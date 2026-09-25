import sys
from pathlib import Path
from typing import Final, Never

from cott_runtime import CottList, Err, Nothing, Some
from real.harlequin.core import connect, disconnect, execute_statements, load_configuration, load_query_file, parse_cli, resolve_profile
from real.harlequin.core_types import Cell, Cell_Integer, Cell_Null, Cell_Real, Cell_Text, CliError, CliError_InvalidAdapter, CliError_MissingOptionValue, CliError_UnknownOption, Configuration, ConfigurationError, ConfigurationError_Invalid, ConfigurationError_Missing, ConfigurationError_ProfileDuplicate, ConnectionError, ConnectionError_AdapterUnavailable, ConnectionError_AuthenticationFailed, ConnectionError_Failed, ConnectionError_InvalidEndpoint, ConnectionError_LeaseRejected, ConnectionProfile, FileError, FileError_InvalidEncoding, FileError_NotFound, FileError_PermissionDenied, FileLocation_Local, FileReference, QueryBatch, QueryResult, SqlClientError, SqlClientError_EmptySql, SqlClientError_ExecutionFailed, SqlClientError_ReadOnlyViolation, SqlClientError_ResultLimitExceeded, SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue, SqlClientError_UnterminatedSql

_PROMPT: Final[str] = "sql> "
_QUIT: Final[str] = ".quit"
_CONFIG_FILE: Final[str] = ".harlequin.toml"
_MAX_ROWS: Final[int] = 1000


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")


def _cell_text(cell: Cell) -> str:
    if isinstance(cell, Cell_Null):
        return "NULL"
    if isinstance(cell, Cell_Integer):
        return str(cell.value)
    if isinstance(cell, Cell_Real):
        return repr(cell.value)
    if isinstance(cell, Cell_Text):
        return _escape(cell.value)
    else:
        return "0x" + bytes(cell.value).hex()


def _print_result(result: QueryResult) -> None:
    columns: list[str] = []
    for column in result.columns:
        columns.append(_escape(column))
    if columns:
        print("\t".join(columns))
        for row in result.rows:
            fields: list[str] = []
            for cell in row.values:
                fields.append(_cell_text(cell))
            print("\t".join(fields))
    elif result.affected_rows < 0:
        print("OK")
    else:
        print(f"OK, {result.affected_rows} rows affected")


def _print_batch(batch: QueryBatch) -> None:
    for result in batch.results:
        _print_result(result)


def _report(text: str) -> None:
    sys.stdout.flush()
    print("harlequin: " + text, file=sys.stderr)
    sys.stderr.flush()


def _cli_error_text(error: CliError) -> str:
    if isinstance(error, CliError_UnknownOption):
        return "unknown option: " + _escape(error.argument)
    if isinstance(error, CliError_MissingOptionValue):
        return "missing value for option: " + _escape(error.option)
    if isinstance(error, CliError_InvalidAdapter):
        return "invalid adapter: " + _escape(error.value)
    else:
        return "conflicting connection inputs"


def _configuration_error_text(error: ConfigurationError) -> str:
    if isinstance(error, ConfigurationError_Missing):
        return "configuration file missing: " + _escape(str(error.path))
    if isinstance(error, ConfigurationError_Invalid):
        return "invalid configuration: " + _escape(str(error.path)) + ": " + _escape(error.message)
    if isinstance(error, ConfigurationError_ProfileDuplicate):
        return "duplicate profile: " + _escape(error.name)
    else:
        return "profile not found: " + _escape(error.name)


def _connection_error_text(error: ConnectionError) -> str:
    if isinstance(error, ConnectionError_AdapterUnavailable):
        return "adapter unavailable"
    if isinstance(error, ConnectionError_InvalidEndpoint):
        return "invalid endpoint or settings"
    if isinstance(error, ConnectionError_AuthenticationFailed):
        return "authentication failed"
    if isinstance(error, ConnectionError_Failed):
        return "connection failed"
    if isinstance(error, ConnectionError_LeaseRejected):
        return "transaction lease rejected"
    else:
        return "transactions unsupported"


def _file_error_text(error: FileError) -> str:
    if isinstance(error, FileError_NotFound):
        return "query file not found"
    if isinstance(error, FileError_PermissionDenied):
        return "query file permission denied"
    if isinstance(error, FileError_InvalidEncoding):
        return "query file is not valid UTF-8"
    else:
        return "query file transfer failed"


def _sql_error_text(error: SqlClientError) -> str:
    if isinstance(error, SqlClientError_EmptySql):
        return "empty SQL"
    if isinstance(error, SqlClientError_UnterminatedSql):
        return "unterminated SQL: missing " + _escape(error.delimiter)
    if isinstance(error, SqlClientError_ReadOnlyViolation):
        return "read-only violation: " + _escape(error.statement)
    if isinstance(error, SqlClientError_SqliteFailure):
        return "sqlite failure"
    if isinstance(error, SqlClientError_UnsupportedValue):
        return "unsupported value: " + _escape(error.type_name)
    if isinstance(error, SqlClientError_ExecutionFailed):
        return "execution failed: " + _escape(error.statement)
    if isinstance(error, SqlClientError_ResultLimitExceeded):
        return f"result exceeds {error.limit} rows"
    else:
        return "cancelled"


def _empty_configuration() -> Configuration:
    profiles: list[ConnectionProfile] = []
    return Configuration(profiles=CottList(values=profiles), default_profile=Nothing(), theme="harlequin", keymap="default")


def run(arguments: CottList[str]) -> Never:
    parsed = parse_cli(arguments)
    if isinstance(parsed, Err):
        _report(_cli_error_text(parsed.error))
        raise SystemExit(2)
    options = parsed.value
    if options.no_config:
        configuration = _empty_configuration()
    else:
        loaded = load_configuration(Path(_CONFIG_FILE))
        if isinstance(loaded, Err):
            if isinstance(loaded.error, ConfigurationError_Missing):
                configuration = _empty_configuration()
            else:
                _report(_configuration_error_text(loaded.error))
                raise SystemExit(2)
        else:
            configuration = loaded.value
    resolved = resolve_profile(configuration, options)
    if isinstance(resolved, Err):
        _report(_configuration_error_text(resolved.error))
        raise SystemExit(2)
    opened = connect(resolved.value)
    if isinstance(opened, Err):
        _report(_connection_error_text(opened.error))
        raise SystemExit(1)
    connection = opened.value
    status = 0
    try:
        query_file = options.query_file
        if isinstance(query_file, Some):
            source = load_query_file(FileReference(location=FileLocation_Local(path=query_file.value), writable=False))
            if isinstance(source, Err):
                _report(_file_error_text(source.error))
                status = 1
            else:
                outcome = execute_statements(connection, source.value.source, _MAX_ROWS)
                if isinstance(outcome, Err):
                    _report(_sql_error_text(outcome.error))
                    status = 1
                else:
                    _print_batch(outcome.value)
        else:
            while True:
                sys.stdout.write(_PROMPT)
                sys.stdout.flush()
                line = sys.stdin.readline()
                if line == "":
                    break
                text = line.strip()
                if text == _QUIT:
                    break
                if not text:
                    continue
                outcome = execute_statements(connection, line, _MAX_ROWS)
                if isinstance(outcome, Err):
                    _report(_sql_error_text(outcome.error))
                    continue
                _print_batch(outcome.value)
    finally:
        closed = disconnect(connection)
        if isinstance(closed, Err):
            _report(_connection_error_text(closed.error))
            if status == 0:
                status = 1
    sys.stdout.flush()
    raise SystemExit(status)
