from typing import cast

import psycopg
from cott_runtime import UNIT, Unit

from real.pgcli.connection_types import Executor


def close_executor(executor: Executor) -> Unit:
    try:
        conn = cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())
        conn.close()
    except Exception:
        return UNIT
    return UNIT
