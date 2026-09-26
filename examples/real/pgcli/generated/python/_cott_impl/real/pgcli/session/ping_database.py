from typing import cast

import psycopg

from real.pgcli.connection_types import Executor


def ping_database(executor: Executor) -> bool:
    try:
        connection = cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception:
        return False
