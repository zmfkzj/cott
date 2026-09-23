import time
from typing import Final, LiteralString

import psycopg
from psycopg.conninfo import make_conninfo
from cott_runtime import CottList, Err, Ok, Result, Some, U64

from real.pgcli_types import Catalog, CatalogRefreshRequest, ClientError, ClientError_CatalogFailed, ColumnCatalog, ConnectionPlan, RelationCatalog, RoutineCatalog

_MAX_SQL_LIMIT: Final[int] = 9223372036854775807


def _catalog_failed(message: str) -> Result[Catalog, ClientError]:
    return Err(error=ClientError_CatalogFailed(message=message))


def _conninfo(plan: ConnectionPlan) -> str:
    kwargs: dict[str, str] = {}
    settings = plan.settings
    if settings.host != "":
        kwargs["host"] = settings.host
    if settings.port != "":
        kwargs["port"] = settings.port
    if settings.user != "":
        kwargs["user"] = settings.user
    if settings.password != "":
        kwargs["password"] = settings.password
    if settings.database != "":
        kwargs["dbname"] = settings.database
    tls = plan.tls
    if tls.mode != "":
        kwargs["sslmode"] = tls.mode
    root_certificate = str(tls.root_certificate)
    if root_certificate not in ("", "."):
        kwargs["sslrootcert"] = root_certificate
    certificate = str(tls.certificate)
    if certificate not in ("", "."):
        kwargs["sslcert"] = certificate
    private_key = str(tls.private_key)
    if private_key not in ("", "."):
        kwargs["sslkey"] = private_key
    return make_conninfo(plan.dsn, **kwargs)


def _names(cursor: psycopg.Cursor[tuple[object, ...]], sql: LiteralString, params: dict[str, object]) -> CottList[str]:
    cursor.execute(sql, params)
    return CottList(values=[str(row[0]) for row in cursor.fetchall()])


def refresh_catalog(request: CatalogRefreshRequest) -> Result[Catalog, ClientError]:
    plan = request.connection
    if isinstance(plan.ssh, Some):
        return _catalog_failed("catalog refresh over an SSH tunnel is not supported by this client")
    limit: U64 = request.limit
    params: dict[str, object] = {"include_system": request.include_system, "limit": min(limit, _MAX_SQL_LIMIT)}
    try:
        conninfo = _conninfo(plan)
        with psycopg.connect(conninfo, autocommit=True) as connection:
            connection.read_only = True
            with connection.cursor() as cursor:
                databases = _names(cursor, "SELECT datname FROM pg_catalog.pg_database WHERE (%(include_system)s OR NOT datistemplate) ORDER BY datname LIMIT %(limit)s", params)
                schemas = _names(cursor, "SELECT n.nspname FROM pg_catalog.pg_namespace n WHERE (%(include_system)s OR (n.nspname NOT IN ('pg_catalog', 'information_schema') AND n.nspname NOT LIKE 'pg\\_toast%%' AND n.nspname NOT LIKE 'pg\\_temp\\_%%')) ORDER BY n.nspname LIMIT %(limit)s", params)
                cursor.execute("SELECT c.oid, n.nspname, c.relname, CASE c.relkind WHEN 'r' THEN 'table' WHEN 'p' THEN 'table' WHEN 'v' THEN 'view' WHEN 'm' THEN 'materialized_view' WHEN 'f' THEN 'foreign_table' END FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind IN ('r', 'p', 'v', 'm', 'f') AND (%(include_system)s OR (n.nspname NOT IN ('pg_catalog', 'information_schema') AND n.nspname NOT LIKE 'pg\\_toast%%' AND n.nspname NOT LIKE 'pg\\_temp\\_%%')) ORDER BY n.nspname, c.relname LIMIT %(limit)s", params)
                relation_rows = cursor.fetchall()
                oids: list[int] = [int(str(row[0])) for row in relation_rows]
                columns_by_oid: dict[int, list[ColumnCatalog]] = {oid: [] for oid in oids}
                if oids:
                    cursor.execute("SELECT a.attrelid, a.attname FROM pg_catalog.pg_attribute a WHERE a.attrelid = ANY(%(oids)s) AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attrelid, a.attnum", {"oids": oids})
                    for column_row in cursor.fetchall():
                        columns_by_oid[int(str(column_row[0]))].append(ColumnCatalog(name=str(column_row[1])))
                relations = CottList(values=[RelationCatalog(schema=str(row[1]), name=str(row[2]), kind=str(row[3]), columns=CottList(values=columns_by_oid[int(str(row[0]))])) for row in relation_rows])
                cursor.execute("SELECT n.nspname, p.proname, pg_catalog.pg_get_function_arguments(p.oid), pg_catalog.pg_get_function_result(p.oid) FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace WHERE (%(include_system)s OR (n.nspname NOT IN ('pg_catalog', 'information_schema') AND n.nspname NOT LIKE 'pg\\_toast%%' AND n.nspname NOT LIKE 'pg\\_temp\\_%%')) ORDER BY n.nspname, p.proname, p.oid LIMIT %(limit)s", params)
                routines = CottList(values=[RoutineCatalog(schema=str(row[0]), name=str(row[1]), arguments=str(row[2]), result_type=str(row[3])) for row in cursor.fetchall()])
                roles = _names(cursor, "SELECT rolname FROM pg_catalog.pg_roles WHERE (%(include_system)s OR rolname NOT LIKE 'pg\\_%%') ORDER BY rolname LIMIT %(limit)s", params)
                extensions = _names(cursor, "SELECT extname FROM pg_catalog.pg_extension ORDER BY extname LIMIT %(limit)s", params)
                publications = _names(cursor, "SELECT pubname FROM pg_catalog.pg_publication ORDER BY pubname LIMIT %(limit)s", params)
                subscriptions = _names(cursor, "SELECT s.subname FROM pg_catalog.pg_subscription s JOIN pg_catalog.pg_database d ON d.oid = s.subdbid WHERE d.datname = pg_catalog.current_database() ORDER BY s.subname LIMIT %(limit)s", params)
    except psycopg.Error as error:
        sqlstate = error.sqlstate
        if sqlstate is None:
            return _catalog_failed("catalog refresh failed")
        return _catalog_failed("catalog refresh failed (SQLSTATE " + sqlstate + ")")
    refreshed_at_ms: U64 = time.time_ns() // 1_000_000
    return Ok(value=Catalog(databases=databases, schemas=schemas, relations=relations, routines=routines, roles=roles, extensions=extensions, publications=publications, subscriptions=subscriptions, refreshed_at_ms=refreshed_at_ms, limit=limit))
