import time
from typing import Final, LiteralString

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from cott_runtime import CottList, Err, Ok, Result, Some, U64

from real.pgcli_types import Catalog, CatalogRefreshRequest, ClientError, ClientError_CatalogFailed, ClientError_TunnelUnsupported, ColumnCatalog, ConnectionPlan, RelationCatalog, RoutineCatalog, TlsMode, TlsMode_Allow, TlsMode_Disable, TlsMode_Prefer, TlsMode_Require, TlsMode_VerifyCa, TlsMode_VerifyFull

_MAX_SQL_LIMIT: Final[int] = 9223372036854775807
_CONNECT_TIMEOUT: Final[int] = 10


def _catalog_failed(message: str) -> Result[Catalog, ClientError]:
    return Err(error=ClientError_CatalogFailed(message=message))


def _sslmode(mode: TlsMode) -> str:
    if isinstance(mode, TlsMode_Disable):
        return "disable"
    if isinstance(mode, TlsMode_Allow):
        return "allow"
    if isinstance(mode, TlsMode_Prefer):
        return "prefer"
    if isinstance(mode, TlsMode_Require):
        return "require"
    if isinstance(mode, TlsMode_VerifyCa):
        return "verify-ca"
    if isinstance(mode, TlsMode_VerifyFull):
        return "verify-full"
    return ""


def _sslmode_rank(mode: str) -> int:
    order = ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
    if mode in order:
        return order.index(mode)
    return 0


def _conninfo(plan: ConnectionPlan) -> str:
    settings = plan.settings
    host = settings.host if settings.host != "" else None
    port = settings.port if settings.port != "" else None
    user = settings.user if settings.user != "" else None
    password = settings.password if settings.password != "" else None
    dbname = settings.database if settings.database != "" else None
    tls = plan.tls
    mode = _sslmode(tls.mode)
    sslmode = mode if mode != "" else None
    if sslmode is not None:
        try:
            parsed = conninfo_to_dict(plan.dsn)
            existing = parsed.get("sslmode")
            if isinstance(existing, str) and _sslmode_rank(existing) > _sslmode_rank(sslmode):
                sslmode = None
        except Exception:
            sslmode = sslmode
    root = tls.root_certificate
    sslrootcert = str(root.value) if isinstance(root, Some) else None
    client = tls.client
    sslcert: str | None = None
    sslkey: str | None = None
    if isinstance(client, Some):
        sslcert = str(client.value.certificate)
        sslkey = str(client.value.private_key)
    return make_conninfo(plan.dsn, host=host, port=port, user=user, password=password, dbname=dbname, sslmode=sslmode, sslrootcert=sslrootcert, sslcert=sslcert, sslkey=sslkey, connect_timeout=_CONNECT_TIMEOUT)


def _names(cursor: psycopg.Cursor[tuple[object, ...]], sql: LiteralString, params: dict[str, object]) -> CottList[str]:
    cursor.execute(sql, params)
    return CottList(values=[str(row[0]) for row in cursor.fetchall()])


def refresh_catalog(request: CatalogRefreshRequest) -> Result[Catalog, ClientError]:
    plan = request.connection
    if isinstance(plan.ssh, Some):
        return Err(error=ClientError_TunnelUnsupported())
    limit: U64 = request.limit
    params: dict[str, object] = {"include_system": request.include_system, "limit": min(limit, _MAX_SQL_LIMIT)}
    try:
        conninfo = _conninfo(plan)
        with psycopg.connect(conninfo, autocommit=False, connect_timeout=_CONNECT_TIMEOUT) as connection:
            connection.read_only = True
            with connection.cursor() as cursor:
                databases = _names(cursor, "SELECT datname FROM pg_catalog.pg_database WHERE (%(include_system)s OR NOT datistemplate) ORDER BY datname LIMIT %(limit)s", params)
                schemas = _names(cursor, "SELECT n.nspname FROM pg_catalog.pg_namespace n WHERE (%(include_system)s OR (n.nspname NOT IN ('pg_catalog', 'information_schema') AND n.nspname NOT LIKE 'pg\\_toast%%' AND n.nspname NOT LIKE 'pg\\_temp%%')) ORDER BY n.nspname LIMIT %(limit)s", params)
                cursor.execute("SELECT c.oid::bigint, n.nspname, c.relname, CASE c.relkind WHEN 'r' THEN 'table' WHEN 'p' THEN 'partitioned table' WHEN 'v' THEN 'view' WHEN 'm' THEN 'materialized view' WHEN 'S' THEN 'sequence' WHEN 'f' THEN 'foreign table' END FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f') AND (%(include_system)s OR (n.nspname NOT IN ('pg_catalog', 'information_schema') AND n.nspname NOT LIKE 'pg\\_toast%%' AND n.nspname NOT LIKE 'pg\\_temp%%')) ORDER BY n.nspname, c.relname LIMIT %(limit)s", params)
                relation_rows = cursor.fetchall()
                oids: list[int] = [int(str(row[0])) for row in relation_rows]
                columns_by_oid: dict[int, list[ColumnCatalog]] = {oid: [] for oid in oids}
                if oids:
                    cursor.execute("SELECT a.attrelid::bigint, a.attname FROM pg_catalog.pg_attribute a WHERE a.attrelid = ANY(%(oids)s::oid[]) AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attrelid, a.attnum", {"oids": oids})
                    for column_row in cursor.fetchall():
                        columns_by_oid[int(str(column_row[0]))].append(ColumnCatalog(name=str(column_row[1])))
                relations = CottList(values=[RelationCatalog(schema=str(row[1]), name=str(row[2]), kind=str(row[3]), columns=CottList(values=columns_by_oid[int(str(row[0]))])) for row in relation_rows])
                cursor.execute("SELECT n.nspname, p.proname, pg_catalog.pg_get_function_identity_arguments(p.oid), COALESCE(pg_catalog.pg_get_function_result(p.oid), '') FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace WHERE (%(include_system)s OR (n.nspname NOT IN ('pg_catalog', 'information_schema') AND n.nspname NOT LIKE 'pg\\_toast%%' AND n.nspname NOT LIKE 'pg\\_temp%%')) ORDER BY n.nspname, p.proname, p.oid LIMIT %(limit)s", params)
                routines = CottList(values=[RoutineCatalog(schema=str(row[0]), name=str(row[1]), arguments=str(row[2]), result_type=str(row[3])) for row in cursor.fetchall()])
                roles = _names(cursor, "SELECT rolname FROM pg_catalog.pg_roles ORDER BY rolname LIMIT %(limit)s", params)
                extensions = _names(cursor, "SELECT extname FROM pg_catalog.pg_extension ORDER BY extname LIMIT %(limit)s", params)
                publications = _names(cursor, "SELECT pubname FROM pg_catalog.pg_publication ORDER BY pubname LIMIT %(limit)s", params)
                subscriptions = _names(cursor, "SELECT subname FROM pg_catalog.pg_subscription ORDER BY subname LIMIT %(limit)s", params)
            connection.rollback()
    except Exception:
        return _catalog_failed("catalog refresh failed")
    refreshed_at_ms: U64 = time.time_ns() // 1_000_000
    return Ok(value=Catalog(databases=databases, schemas=schemas, relations=relations, routines=routines, roles=roles, extensions=extensions, publications=publications, subscriptions=subscriptions, refreshed_at_ms=refreshed_at_ms, limit=limit))
