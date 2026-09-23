import sqlite3
from pathlib import Path
from typing import Final

from cott_runtime import CottList, Err, Ok, Result, U32
from real.harlequin.catalog_types import CatalogMatch, CatalogMatchKind_Column, CatalogMatchKind_Relation
from real.harlequin.core_types import DatabaseTarget, DatabaseTarget_File, SqlClientError, SqlClientError_SqliteFailure

_MAX_MATCHES: Final[int] = 1000


def _connect(database: DatabaseTarget) -> sqlite3.Connection:
    if isinstance(database, DatabaseTarget_File):
        uri = Path(database.path).resolve().as_uri() + "?mode=ro"
        return sqlite3.connect(uri, uri=True)
    return sqlite3.connect(":memory:")


def _quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def search_catalog(database: DatabaseTarget, term: str) -> Result[CottList[CatalogMatch], SqlClientError]:
    needle = term.casefold()
    matches: list[CatalogMatch] = []
    try:
        connection = _connect(database)
        try:
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite\\_%' ESCAPE '\\' ORDER BY name"
            ).fetchall()
            for (relation,) in rows:
                if len(matches) >= _MAX_MATCHES:
                    break
                relation_name = str(relation)
                if needle in relation_name.casefold():
                    matches.append(CatalogMatch(kind=CatalogMatchKind_Relation(), relation=relation_name, name=relation_name, ordinal=0))
                columns = connection.execute("PRAGMA table_info(" + _quote_identifier(relation_name) + ")").fetchall()
                for column in columns:
                    if len(matches) >= _MAX_MATCHES:
                        break
                    column_name = str(column[1])
                    if needle in column_name.casefold():
                        ordinal: U32 = int(column[0])
                        matches.append(CatalogMatch(kind=CatalogMatchKind_Column(), relation=relation_name, name=column_name, ordinal=ordinal))
        finally:
            connection.close()
    except sqlite3.Error as error:
        return Err(error=SqlClientError_SqliteFailure(message=str(error)))
    return Ok(value=CottList(values=matches))
