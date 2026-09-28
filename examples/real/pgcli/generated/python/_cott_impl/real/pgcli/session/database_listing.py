from typing import cast

import psycopg
from cott_runtime import CottContractViolation, CottList, Err, FrozenMap, Ok, Opaque, Result, Some, _cott_fixture_database

from real.pgcli.connection_types import Executor
from real.pgcli.output import format_output
from real.pgcli.output_types import OutputSettings, ResultSet
from real.pgcli.session_types import EvaluateError, EvaluateError_Failed


def database_listing(executor: Executor) -> Result[str, EvaluateError]:
    try:
        raw_connection = executor.connection.unwrap()
        if not isinstance(raw_connection, psycopg.Connection):
            raise TypeError("executor connection must be a psycopg connection")
        connection = cast(psycopg.Connection[tuple[object, ...]], raw_connection)
        try:
            _cott_fixture_database("read")
        except CottContractViolation as violation:
            if violation.message != "fixture adapters are inactive":
                raise
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT d.datname as "Name", pg_catalog.pg_get_userbyid(d.datdba) as "Owner", '
                'pg_catalog.pg_encoding_to_char(d.encoding) as "Encoding", d.datcollate as "Collate", '
                'd.datctype as "Ctype", pg_catalog.array_to_string(d.datacl, E\'\\n\') AS "Access privileges" '
                'FROM pg_catalog.pg_database d ORDER BY 1'
            )
            description = cursor.description or []
            columns = [column.name for column in description]
            type_names: list[str] = []
            for column in description:
                type_info = cursor.adapters.types.get(column.type_code)
                type_names.append(type_info.name if type_info is not None else "")
            rows = cursor.fetchall()
            result_set = ResultSet(
                columns=CottList(values=columns),
                type_names=CottList(values=type_names),
                rows=Opaque(tag="pgcli.result-rows", value=rows),
                rowcount=cursor.rowcount,
            )
            status = cursor.statusmessage or ""
        settings = OutputSettings(
            table_format="ascii",
            column_date_formats=FrozenMap(values={}),
            max_field_width=Some(value=500),
        )
        formatted = format_output(
            Some(value="List of databases"), Some(value=result_set), Some(value=status), settings, False
        )
        if isinstance(formatted, Err):
            return Err[EvaluateError](error=EvaluateError_Failed(message=formatted.error.message))
        return Ok(value=formatted.value.text)
    except Exception as error:
        return Err[EvaluateError](error=EvaluateError_Failed(message=str(error)))
