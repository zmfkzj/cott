import sqlite3
from collections.abc import Iterable
from contextlib import closing
from typing import cast

from cott_runtime import CottList, Nothing, Ok, Result, Some
from real.harlequin.catalog_types import CatalogColumn
from real.harlequin.core_types import DatabaseTarget, DatabaseTarget_File, DatabaseTarget_Memory, SqlClientError


def catalog_columns(database: DatabaseTarget, relation: str) -> Result[CottList[CatalogColumn], SqlClientError]:
    match database:
        case DatabaseTarget_Memory():
            connection = sqlite3.connect(":memory:")
        case DatabaseTarget_File() as target:
            connection = sqlite3.connect(target.path)

    with closing(connection):
        connection.execute("PRAGMA query_only = ON").close()
        cursor = connection.execute(
            'SELECT cid, name, type, "notnull", dflt_value, pk FROM pragma_table_info(?, \'main\') ORDER BY cid LIMIT 65535',
            (relation,),
        )
        with closing(cursor):
            rows = cast(Iterable[tuple[int, str, str, int, str | None, int]], cursor)
            columns = CottList(
                values=tuple(
                    CatalogColumn(
                        relation=relation,
                        ordinal=ordinal,
                        name=name,
                        declared_type=declared_type,
                        not_null=not_null != 0,
                        default_sql=Nothing() if default_sql is None else Some(value=default_sql),
                        primary_key_position=primary_key_position,
                    )
                    for ordinal, name, declared_type, not_null, default_sql, primary_key_position in rows
                )
            )

    return Ok(value=columns)
