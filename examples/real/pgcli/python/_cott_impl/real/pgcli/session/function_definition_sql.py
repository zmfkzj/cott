from typing import cast

import psycopg
from cott_runtime import Err, Ok, Result

from real.pgcli.connection_types import Executor
from real.pgcli.session_types import EvaluateError, EvaluateError_Failed


def function_definition_sql(executor: Executor, spec: str) -> Result[str, EvaluateError]:
    connection = cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "WITH f AS (SELECT %s::pg_catalog.regproc::pg_catalog.oid AS f_oid) SELECT pg_catalog.pg_get_functiondef(f.f_oid) FROM f",
                (spec,),
            )
            row = cursor.fetchone()
    except psycopg.ProgrammingError:
        return Err[EvaluateError](error=EvaluateError_Failed(message="Function " + spec + " does not exist."))
    if row is None:
        return Err[EvaluateError](error=EvaluateError_Failed(message="Function " + spec + " does not exist."))
    return Ok(value=str(row[0]))
