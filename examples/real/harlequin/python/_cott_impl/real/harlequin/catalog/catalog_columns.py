import sqlite3
from pathlib import Path

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some
from real.harlequin.catalog_types import CatalogColumn
from real.harlequin.core_types import DatabaseTarget, DatabaseTarget_File, SqlClientError, SqlClientError_SqliteFailure


def _connect(database: DatabaseTarget) -> sqlite3.Connection:
    if isinstance(database, DatabaseTarget_File):
        uri = Path(database.path).resolve().as_uri() + "?mode=ro"
        return sqlite3.connect(uri, uri=True)
    return sqlite3.connect(":memory:")


def catalog_columns(database: DatabaseTarget, relation: str) -> Result[CottList[CatalogColumn], SqlClientError]:
    try:
        connection = _connect(database)
        try:
            rows = connection.execute(
                "SELECT cid, name, type, \"notnull\", dflt_value, pk FROM pragma_table_info(?) ORDER BY cid",
                (relation,),
            ).fetchall()
        finally:
            connection.close()
    except sqlite3.Error as error:
        return Err(error=SqlClientError_SqliteFailure(message=str(error)))
    columns: list[CatalogColumn] = [
        CatalogColumn(
            relation=relation,
            ordinal=int(cid),
            name=str(name),
            declared_type=str(declared_type) if declared_type is not None else "",
            not_null=bool(not_null),
            default_sql=Some(value=str(default_sql)) if default_sql is not None else Nothing(),
            primary_key_position=int(pk),
        )
        for cid, name, declared_type, not_null, default_sql, pk in rows
    ]
    return Ok(value=CottList(values=columns))
