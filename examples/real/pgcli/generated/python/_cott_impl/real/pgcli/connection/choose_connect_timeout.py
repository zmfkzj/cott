import psycopg
from psycopg.conninfo import conninfo_to_dict

from cott_runtime import I64, CottList, Nothing, Option, Some
from real.pgcli.connection_types import ConnectionParam


def _dsn_has_timeout(dsn: str) -> bool:
    if not dsn:
        return False
    try:
        parsed = conninfo_to_dict(dsn)
    except psycopg.ProgrammingError:
        return False
    return "connect_timeout" in parsed


def choose_connect_timeout(explicit: Option[I64], dsn: str, extra: CottList[ConnectionParam], pgconnect_timeout: str, default: I64) -> Option[I64]:
    if isinstance(explicit, Some):
        return explicit
    for param in extra:
        if param.name == "connect_timeout":
            return Nothing()
    if _dsn_has_timeout(dsn) or pgconnect_timeout:
        return Nothing()
    return Some(value=default)
