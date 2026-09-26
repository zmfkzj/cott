from typing import LiteralString, cast

import psycopg
from psycopg import sql
from cott_runtime import Err, Ok, Result

from real.pgcli.connection_types import Executor
from real.pgcli.session_types import EvaluateError, EvaluateError_Failed


def _failed(message: str) -> Result[str, EvaluateError]:
    return Err(error=EvaluateError_Failed(message=message))


def view_definition_sql(executor: Executor, spec: str) -> Result[str, EvaluateError]:
    conn = cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())
    query: LiteralString = (
        "WITH v AS (SELECT %s::pg_catalog.regclass::pg_catalog.oid AS v_oid) "
        "SELECT nspname, relname, relkind, pg_catalog.pg_get_viewdef(c.oid, true), "
        "array_remove(array_remove(c.reloptions,'check_option=local'), 'check_option=cascaded') AS reloptions, "
        "CASE WHEN 'check_option=local' = ANY (c.reloptions) THEN 'LOCAL'::text "
        "WHEN 'check_option=cascaded' = ANY (c.reloptions) THEN 'CASCADED'::text ELSE NULL END AS checkoption "
        "FROM pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_namespace n ON (c.relnamespace = n.oid) "
        "JOIN v ON (c.oid = v.v_oid)"
    )
    not_found = "View " + spec + " does not exist."
    try:
        with conn.cursor() as cur:
            try:
                cur.execute(query, (spec,))
            except psycopg.ProgrammingError:
                return _failed(not_found)
            row = cur.fetchone()
        if row is None:
            return _failed(not_found)
        nspname = str(row[0])
        relname = str(row[1])
        relkind = str(row[2])
        viewdef = cast(LiteralString, str(row[3]))
        if relkind == "m":
            template: LiteralString = "CREATE OR REPLACE MATERIALIZED VIEW {name} AS \n{stmt}"
        else:
            template = "CREATE OR REPLACE VIEW {name} AS \n{stmt}"
        composed = sql.SQL(template).format(name=sql.Identifier(nspname, relname), stmt=sql.SQL(viewdef))
        return Ok(value=composed.as_string(conn))
    except Exception as error:
        return _failed(str(error))
