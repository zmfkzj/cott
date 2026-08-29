from __future__ import annotations

import argparse
import dataclasses
import getpass
import os
import shutil
import sys
from typing import TypeVar


from cott_runtime import CottList, Err, Ok, Result

from real.pgcli import (
    ColumnCatalog,
    CompletionRequest,
    ConnectionInputs,
    EnvironmentInputs,
    PromptAction_PromptPassword,
    execute_query,
    RenderRequest,
    TableCatalog,
    complete_sql,
    prompt_policy,
    render_query,
    resolve_connection,
)


class CliError(Exception):
    pass


T = TypeVar("T")
E = TypeVar("E")


def _unwrap(result: Result[T, E]) -> T:
    if isinstance(result, Ok):
        return result.value
    if isinstance(result, Err):
        raise CliError(str(result.error))
    raise AssertionError("unreachable")


def _environment() -> EnvironmentInputs:
    return EnvironmentInputs(
        host=os.environ.get("PGHOST", ""),
        port=os.environ.get("PGPORT", ""),
        user=os.environ.get("PGUSER", ""),
        password=os.environ.get("PGPASSWORD", ""),
        database=os.environ.get("PGDATABASE", ""),
    )


def _catalog(specifications: list[str]) -> CottList[TableCatalog]:
    tables: list[TableCatalog] = []
    for specification in specifications:
        table, _, columns = specification.partition(":")
        schema, name = table.rsplit(".", 1) if "." in table else ("public", table)
        tables.append(
            TableCatalog(
                schema=schema,
                name=name,
                columns=CottList(values=tuple(ColumnCatalog(name=column) for column in columns.split(",") if column)),
            )
        )
    return CottList(values=tuple(tables))


def _complete(args: argparse.Namespace) -> int:
    result = complete_sql(
        CompletionRequest(
            source=args.source,
            cursor=len(args.source) if args.cursor is None else args.cursor,
            catalog=_catalog(args.table),
        )
    )
    print("\n".join(result.candidates))
    return 0


def _query(args: argparse.Namespace) -> int:
    settings = _unwrap(
        resolve_connection(
            ConnectionInputs(
                host=args.host or "",
                port=args.port or "",
                user=args.user or "",
                password=args.password or "",
                database=args.database or "",
            ),
            _environment(),
        )
    )
    action = _unwrap(prompt_policy(args.no_password, settings.password))
    if isinstance(action, PromptAction_PromptPassword):
        settings = dataclasses.replace(settings, password=getpass.getpass("Password: "))
    result = _unwrap(execute_query(settings, args.sql))
    rendered = render_query(
        RenderRequest(
            columns=result.columns,
            rows=result.rows,
            terminal_width=args.width,
            vertical=args.vertical,
        )
    )
    print(rendered.text)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bounded clean-room pgcli adapter")
    commands = parser.add_subparsers(dest="mode", required=True)

    complete = commands.add_parser("complete")
    complete.add_argument("source")
    complete.add_argument("--cursor", type=int)
    complete.add_argument("--table", action="append", default=[], metavar="[SCHEMA.]TABLE:COLUMN,...")
    complete.set_defaults(handler=_complete)

    query = commands.add_parser("query")
    query.add_argument("--sql", required=True)
    query.add_argument("--host")
    query.add_argument("--port")
    query.add_argument("--user")
    query.add_argument("--password")
    query.add_argument("--database")
    query.add_argument("--no-password", action="store_true")
    query.add_argument("--vertical", action="store_true")
    query.add_argument("--width", type=int, default=shutil.get_terminal_size(fallback=(80, 24)).columns)
    query.set_defaults(handler=_query)
    return parser


def main() -> int:
    try:
        args = _parser().parse_args()
        return args.handler(args)
    except CliError as error:
        print(f"pgcli: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
