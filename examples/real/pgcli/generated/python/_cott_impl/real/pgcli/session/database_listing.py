from typing import cast

import psycopg
from cott_runtime import CottList, Err, FrozenMap, Ok, Opaque, Result, Some

from real.pgcli.connection_types import Executor
from real.pgcli.output import format_output
from real.pgcli.output_types import OutputSettings, ResultSet
from real.pgcli.session_types import EvaluateError, EvaluateError_Failed


def database_listing(executor: Executor) -> Result[str, EvaluateError]:
    try:
        connection = cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT d.datname as "Name", pg_catalog.pg_get_userbyid(d.datdba) as "Owner", '
                'pg_catalog.pg_encoding_to_char(d.encoding) as "Encoding", d.datcollate as "Collate", '
                'd.datctype as "Ctype", pg_catalog.array_to_string(d.datacl, E\'\\n\') AS "Access privileges" '
                "FROM pg_catalog.pg_database d ORDER BY 1"
            )
            description = cursor.description or []
            columns = [str(column.name) for column in description]
            type_names: list[str] = []
            for column in description:
                type_info = cursor.adapters.types.get(column.type_code)
                type_names.append(type_info.name if type_info is not None else "")
            rows: list[tuple[object, ...]] = [tuple(row) for row in cursor.fetchall()]
            rowcount = cursor.rowcount
            status = cursor.statusmessage or ""
        result_set = ResultSet(
            columns=CottList(values=columns),
            type_names=CottList(values=type_names),
            rows=Opaque(tag="pgcli.result-rows", value=rows),
            rowcount=rowcount,
        )
        settings = OutputSettings(
            table_format="ascii",
            column_date_formats=FrozenMap(values={}),
            max_field_width=Some(value=500),
        )
        formatted = format_output(Some(value="List of databases"), Some(value=result_set), Some(value=status), settings, False)
        if isinstance(formatted, Ok):
            return Ok(value=formatted.value.text)
        return Err(error=EvaluateError_Failed(message=formatted.error.message))
    except Exception as error:
        return Err(error=EvaluateError_Failed(message=str(error)))
