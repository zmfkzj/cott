from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import cast
from cott_runtime import CottList


from real.harlequin.catalog import (
    CatalogColumn,
    CatalogMatch,
    CatalogRelation,
    catalog_columns,
    catalog_relations,
    search_catalog,
)
from real.harlequin.core import (
    DatabaseTarget,
    DatabaseTarget_File,
    DatabaseTarget_Memory,
    QueryResult,
    execute_sql,
)
from real.harlequin.render import (
    render_catalog_columns,
    render_catalog_matches,
    render_catalog_relations,
    render_table,
)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Headless SQLite terminal client")
    command.add_argument("--database", type=Path)
    command.add_argument("--read-only", action="store_true")
    actions = command.add_subparsers(dest="action", required=True)

    query = actions.add_parser("query")
    query.add_argument("sql")

    catalog = actions.add_parser("catalog")
    catalog_actions = catalog.add_subparsers(dest="catalog_action", required=True)
    catalog_actions.add_parser("relations")
    columns = catalog_actions.add_parser("columns")
    columns.add_argument("relation")

    search = actions.add_parser("search")
    search.add_argument("term")
    return command


def database_target(path: Path | None) -> DatabaseTarget:
    if path is None:
        return DatabaseTarget_Memory()
    return DatabaseTarget_File(path=path)


def unwrap(result: object) -> tuple[object | None, object | None]:
    if type(result).__name__ == "Ok":
        return getattr(result, "value"), None
    return None, getattr(result, "error", result)


def report(result: object) -> tuple[object | None, int]:
    value, error = unwrap(result)
    if error is None:
        return value, 0
    print(f"error: {type(error).__name__}: {error!r}", file=sys.stderr)
    return None, 1


def main() -> int:
    args = parser().parse_args()
    database = database_target(args.database)

    if args.action == "query":
        value, status = report(execute_sql(database, args.sql, args.read_only))
        if status:
            return status
        for index, result in enumerate(cast(list[QueryResult], value)):
            if index:
                print()
            print(render_table(result))
        return 0

    if args.action == "catalog":
        if args.catalog_action == "relations":
            value, status = report(catalog_relations(database))
            if status:
                return status
            print(render_catalog_relations(CottList(values=tuple(cast(list[CatalogRelation], value)))))
            return 0
        value, status = report(catalog_columns(database, args.relation))
        if status:
            return status
        print(render_catalog_columns(CottList(values=tuple(cast(list[CatalogColumn], value)))))
        return 0

    value, status = report(search_catalog(database, args.term))
    if status:
        return status
    print(render_catalog_matches(CottList(values=tuple(cast(list[CatalogMatch], value)))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
