import sqlite3
from typing import Final
from pathlib import Path

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some
from real.harlequin.catalog_types import CatalogColumn
from real.harlequin.core_types import DatabaseTarget, DatabaseTarget_Memory, SqlClientError, SqlClientError_SqliteFailure

_NO_SUCH_RELATION: Final[str] = "no such relation"


def catalog_columns(database: DatabaseTarget, relation: str) -> Result[CottList[CatalogColumn], SqlClientError]:
    if isinstance(database, DatabaseTarget_Memory):
        return Err(error=SqlClientError_SqliteFailure(message=_NO_SUCH_RELATION))
    try:
        uri = Path(database.path).resolve().as_uri() + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        try:
            rows: list[tuple[object, ...]] = connection.execute(
                "SELECT cid, name, type, \"notnull\", dflt_value, pk FROM pragma_table_info(?, 'main') ORDER BY cid",
                (relation,),
            ).fetchall()
        finally:
            connection.close()
    except sqlite3.Error as error:
        return Err(error=SqlClientError_SqliteFailure(message=str(error)))
    if len(rows) == 0:
        return Err(error=SqlClientError_SqliteFailure(message=_NO_SUCH_RELATION))
    columns: list[CatalogColumn] = []
    for cid, name, declared_type, not_null, default_sql, pk in rows:
        columns.append(
            CatalogColumn(
                relation=relation,
                ordinal=int(str(cid)) + 1,
                name=str(name),
                declared_type=str(declared_type) if declared_type is not None else "",
                not_null=bool(not_null),
                default_sql=Some(value=str(default_sql)) if default_sql is not None else Nothing(),
                primary_key_position=int(str(pk)),
            )
        )
    return Ok(value=CottList(values=columns))
