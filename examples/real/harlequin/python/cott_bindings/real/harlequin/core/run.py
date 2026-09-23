import sys
from typing import Never

from cott_runtime import CottList, Err, Some
from real.harlequin.core import connect, disconnect, execute_statements, parse_cli
from real.harlequin.core_types import (
    AdapterKind_DuckDb,
    Cell,
    Cell_Integer,
    Cell_Null,
    Cell_Real,
    Cell_Text,
    ConnectionRequest,
)


def _cell_text(cell: Cell) -> str:
    if isinstance(cell, Cell_Null):
        return "NULL"
    if isinstance(cell, Cell_Integer | Cell_Real | Cell_Text):
        return str(cell.value)
    return cell.value.hex()


def run(arguments: CottList[str]) -> Never:
    parsed = parse_cli(arguments)
    if isinstance(parsed, Err):
        sys.exit(str(parsed.error))
    options = parsed.value
    adapter = options.adapter.value if isinstance(options.adapter, Some) else AdapterKind_DuckDb()
    endpoint = options.connection.value if isinstance(options.connection, Some) else ":memory:"
    connected = connect(
        ConnectionRequest(
            adapter=adapter,
            endpoint=endpoint,
            settings=CottList(values=()),
            read_only=options.read_only,
        )
    )
    if isinstance(connected, Err):
        sys.exit(str(connected.error))
    status = 0
    try:
        while True:
            try:
                sql = input("sql> ")
            except EOFError:
                break
            if sql.strip() == ".quit":
                break
            if not sql.strip():
                continue
            outcome = execute_statements(connected.value, sql, 100000)
            if isinstance(outcome, Err):
                status = 1
                print(outcome.error, file=sys.stderr)
                continue
            for result in outcome.value.results:
                if len(result.columns) > 0:
                    print("\t".join(result.columns))
                for row in result.rows:
                    print("\t".join(_cell_text(cell) for cell in row.values))
                if len(result.columns) == 0:
                    print(f"{result.affected_rows} rows affected")
    finally:
        closed = disconnect(connected.value)
        if isinstance(closed, Err):
            print("connection cleanup failed", file=sys.stderr)
            status = 1
    sys.exit(status)
