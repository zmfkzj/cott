import sqlite3
from pathlib import Path

from cott_runtime import CottList, Err, Nothing, Ok, Option, Result, Some
from real.harlequin.catalog_types import CatalogRelation, RelationKind_Table, RelationKind_View
from real.harlequin.core_types import DatabaseTarget, DatabaseTarget_File, SqlClientError, SqlClientError_SqliteFailure


def catalog_relations(database: DatabaseTarget) -> Result[CottList[CatalogRelation], SqlClientError]:
    try:
        if isinstance(database, DatabaseTarget_File):
            uri = Path(database.path).resolve().as_uri() + "?mode=ro"
            connection = sqlite3.connect(uri, uri=True)
        else:
            connection = sqlite3.connect(":memory:")
        try:
            rows: list[tuple[object, object, object]] = connection.execute(
                "SELECT name, type, sql FROM main.sqlite_schema WHERE type IN ('table', 'view')"
            ).fetchall()
        finally:
            connection.close()
    except sqlite3.Error as error:
        return Err(error=SqlClientError_SqliteFailure(message=str(error)))
    relations: list[CatalogRelation] = []
    for name, kind, sql in rows:
        if not isinstance(name, str) or name.startswith("sqlite_"):
            continue
        stored: Option[str] = Some(value=sql) if isinstance(sql, str) else Nothing()
        relations.append(
            CatalogRelation(
                name=name,
                kind=RelationKind_Table() if kind == "table" else RelationKind_View(),
                sql=stored,
            )
        )
    relations.sort(key=lambda relation: relation.name)
    return Ok(value=CottList(values=relations))
