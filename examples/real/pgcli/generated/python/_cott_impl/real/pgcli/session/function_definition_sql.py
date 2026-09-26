from typing import cast

import psycopg
from cott_runtime import Err, Ok, Result

from real.pgcli.connection_types import Executor
from real.pgcli.session_types import EvaluateError, EvaluateError_Failed


def function_definition_sql(executor: Executor, spec: str) -> Result[str, EvaluateError]:
    conn = cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())
    missing: Result[str, EvaluateError] = Err(error=EvaluateError_Failed(message="Function " + spec + " does not exist."))
    try:
        with conn.cursor() as cur:
            cur.execute(
                "WITH f AS (SELECT %s::pg_catalog.regproc::pg_catalog.oid AS f_oid) SELECT pg_catalog.pg_get_functiondef(f.f_oid) FROM f",
                (spec,),
            )
            row = cur.fetchone()
    except psycopg.ProgrammingError:
        return missing
    if row is None:
        return missing
    return Ok(value=str(row[0]))
