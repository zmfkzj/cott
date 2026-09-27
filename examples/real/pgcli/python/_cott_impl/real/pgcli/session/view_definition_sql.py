from typing import LiteralString, cast

import psycopg
from psycopg import sql

from cott_runtime import Err, Ok, Result
from real.pgcli.connection_types import Executor
from real.pgcli.session_types import EvaluateError, EvaluateError_Failed


def view_definition_sql(executor: Executor, spec: str) -> Result[str, EvaluateError]:
    connection = cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())
    query: LiteralString = (
        "WITH v AS (SELECT %s::pg_catalog.regclass::pg_catalog.oid AS v_oid) "
        "SELECT nspname, relname, relkind, pg_catalog.pg_get_viewdef(c.oid, true), "
        "array_remove(array_remove(c.reloptions,'check_option=local'), 'check_option=cascaded') AS reloptions, "
        "CASE WHEN 'check_option=local' = ANY (c.reloptions) THEN 'LOCAL'::text "
        "WHEN 'check_option=cascaded' = ANY (c.reloptions) THEN 'CASCADED'::text ELSE NULL END AS checkoption "
        "FROM pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_namespace n ON (c.relnamespace = n.oid) "
        "JOIN v ON (c.oid = v.v_oid)"
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (spec,))
            row = cursor.fetchone()
        if row is None:
            return Err(error=EvaluateError_Failed(message=f"View {spec} does not exist."))
        if row[2] == "m":
            template: LiteralString = "CREATE OR REPLACE MATERIALIZED VIEW {name} AS \n{stmt}"
        else:
            template = "CREATE OR REPLACE VIEW {name} AS \n{stmt}"
        definition = cast(LiteralString, str(row[3]))
        statement = sql.SQL(template).format(
            name=sql.Identifier(str(row[0]), str(row[1])),
            stmt=sql.SQL(definition),
        )
        return Ok(value=statement.as_string(connection))
    except psycopg.ProgrammingError:
        return Err(error=EvaluateError_Failed(message=f"View {spec} does not exist."))
    except Exception as error:
        return Err(error=EvaluateError_Failed(message=str(error)))
