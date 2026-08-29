import sqlite3
from collections.abc import Iterable
from contextlib import closing
from typing import cast

from cott_runtime import CottList, Nothing, Ok, Result, Some
from real.harlequin.catalog_types import CatalogRelation, RelationKind_Table, RelationKind_View
from real.harlequin.core_types import DatabaseTarget, DatabaseTarget_File, DatabaseTarget_Memory, SqlClientError


def catalog_relations(database: DatabaseTarget) -> Result[CottList[CatalogRelation], SqlClientError]:
    match database:
        case DatabaseTarget_Memory():
            connection = sqlite3.connect(":memory:")
        case DatabaseTarget_File() as target:
            connection = sqlite3.connect(target.path)

    with closing(connection):
        connection.execute("PRAGMA query_only = ON").close()
        cursor = connection.execute(
            "SELECT name, type, sql FROM main.sqlite_master "
            "WHERE type IN ('table', 'view') AND substr(name, 1, 7) <> 'sqlite_' "
            "ORDER BY name LIMIT 100000"
        )
        with closing(cursor):
            rows = cast(Iterable[tuple[str, str, str | None]], cursor)
            relations = CottList(
                values=tuple(
                    CatalogRelation(
                        name=name,
                        kind=RelationKind_Table() if relation_type == "table" else RelationKind_View(),
                        sql=Nothing() if sql is None else Some(value=sql),
                    )
                    for name, relation_type, sql in rows
                )
            )

    return Ok(value=relations)
