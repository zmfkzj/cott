from typing import cast

import cott_runtime
import psycopg

from real.pgcli.connection_types import Executor


def ping_database(executor: Executor) -> bool:
    try:
        connection = cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())
        try:
            cott_runtime._cott_fixture_database("read")
        except cott_runtime.CottContractViolation as error:
            if error.message != "fixture adapters are inactive":
                raise
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception:
        return False
