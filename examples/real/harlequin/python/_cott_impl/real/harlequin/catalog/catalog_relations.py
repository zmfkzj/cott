import sqlite3
from pathlib import Path
from typing import Final

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some
from real.harlequin.catalog_types import CatalogRelation, RelationKind_Table, RelationKind_View
from real.harlequin.core_types import DatabaseTarget, DatabaseTarget_File, SqlClientError, SqlClientError_SqliteFailure

_MAX_RELATIONS: Final[int] = 100000


def catalog_relations(database: DatabaseTarget) -> Result[CottList[CatalogRelation], SqlClientError]:
    try:
        if isinstance(database, DatabaseTarget_File):
            uri = Path(database.path).resolve().as_uri() + "?mode=ro"
            connection = sqlite3.connect(uri, uri=True)
        else:
            connection = sqlite3.connect(":memory:")
        try:
            rows = connection.execute(
                "SELECT name, type, sql FROM sqlite_schema WHERE type IN ('table', 'view') LIMIT ?",
                (_MAX_RELATIONS,),
            ).fetchall()
        finally:
            connection.close()
    except (sqlite3.Error, OSError, ValueError) as error:
        return Err(error=SqlClientError_SqliteFailure(message=str(error)))
    return Ok(value=CottList(values=[
        CatalogRelation(
            name=name,
            kind=RelationKind_Table() if kind == "table" else RelationKind_View(),
            sql=Nothing() if sql is None else Some(value=sql),
        )
        for name, kind, sql in rows
    ]))
