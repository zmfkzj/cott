import sys
from typing import Final, Never

from cott_runtime import CottList, Err, Some
from real.harlequin.core import connect, disconnect, execute_statements, parse_cli
from real.harlequin.core_types import AdapterKind, AdapterKind_DuckDb, Cell, Cell_Integer, Cell_Null, Cell_Real, Cell_Text, CliError, CliError_InvalidAdapter, CliError_MissingOptionValue, CliError_UnknownOption, ConnectionError, ConnectionError_AdapterUnavailable, ConnectionError_AuthenticationFailed, ConnectionError_InvalidEndpoint, ConnectionRequest, QueryResult, Setting, SqlClientError, SqlClientError_EmptySql, SqlClientError_ExecutionFailed, SqlClientError_ReadOnlyViolation, SqlClientError_ResultLimitExceeded, SqlClientError_SqliteFailure, SqlClientError_UnsupportedValue, SqlClientError_UnterminatedSql

_PROMPT: Final[str] = "sql> "
_QUIT: Final[str] = ".quit"
_DEFAULT_ENDPOINT: Final[str] = ":memory:"
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
        return "0x" + cell.value.hex()


def _print_result(result: QueryResult) -> None:
    columns: list[str] = []
    for column in result.columns:
        columns.append(_escape(column))
    if columns:
        print("\t".join(columns))
        for row in result.rows:
            print("\t".join(_cell_text(cell) for cell in row.values))
    else:
        print(f"affected rows: {result.affected_rows}" if result.affected_rows >= 0 else "ok")


def _cli_error_text(error: CliError) -> str:
    if isinstance(error, CliError_UnknownOption):
        return "unknown option: " + error.argument
    if isinstance(error, CliError_MissingOptionValue):
        return "missing value for " + error.option
    if isinstance(error, CliError_InvalidAdapter):
        return "invalid adapter: " + error.value
    else:
        return "conflicting connection inputs"


def _connection_error_text(error: ConnectionError) -> str:
    if isinstance(error, ConnectionError_AdapterUnavailable):
        return "adapter unavailable"
    if isinstance(error, ConnectionError_InvalidEndpoint):
        return "invalid endpoint or settings"
    if isinstance(error, ConnectionError_AuthenticationFailed):
        return "authentication failed: " + error.message
    else:
        return "connection failed: " + error.message


def _sql_error_text(error: SqlClientError) -> str:
    if isinstance(error, SqlClientError_EmptySql):
        return "empty SQL"
    if isinstance(error, SqlClientError_UnterminatedSql):
        return "unterminated SQL: missing " + error.delimiter
    if isinstance(error, SqlClientError_ReadOnlyViolation):
        return "read-only violation: " + error.statement
    if isinstance(error, SqlClientError_SqliteFailure):
        return "sqlite failure: " + error.message
    if isinstance(error, SqlClientError_UnsupportedValue):
        return "unsupported value: " + error.type_name
    if isinstance(error, SqlClientError_ExecutionFailed):
        return "execution failed: " + error.message
    if isinstance(error, SqlClientError_ResultLimitExceeded):
        return f"result exceeds {error.limit} rows"
    else:
        return "cancelled"


def run(arguments: CottList[str]) -> Never:
    parsed = parse_cli(arguments)
    if isinstance(parsed, Err):
        print(_cli_error_text(parsed.error), file=sys.stderr)
        raise SystemExit(2)
    options = parsed.value
    adapter: AdapterKind = options.adapter.value if isinstance(options.adapter, Some) else AdapterKind_DuckDb()
    endpoint: str = options.connection.value if isinstance(options.connection, Some) else _DEFAULT_ENDPOINT
    settings: list[Setting] = []
    opened = connect(ConnectionRequest(adapter=adapter, endpoint=endpoint, settings=CottList(values=settings), read_only=options.read_only))
    if isinstance(opened, Err):
        print(_connection_error_text(opened.error), file=sys.stderr)
        raise SystemExit(1)
    connection = opened.value
    status = 0
    try:
        while True:
            try:
                line = input(_PROMPT)
            except EOFError:
                break
            except KeyboardInterrupt:
                print()
                continue
            text = line.strip()
            if text == _QUIT:
                break
            if not text:
                continue
            outcome = execute_statements(connection, line, _MAX_ROWS)
            if isinstance(outcome, Err):
                print(_sql_error_text(outcome.error), file=sys.stderr)
                continue
            for result in outcome.value.results:
                _print_result(result)
    finally:
        closed = disconnect(connection)
        if isinstance(closed, Err):
            print(_connection_error_text(closed.error), file=sys.stderr)
            status = 1
    raise SystemExit(status)
