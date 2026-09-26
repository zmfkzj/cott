from collections.abc import Iterator
from typing import cast

import sqlparse
import sqlparse.sql
import sqlparse.tokens
from cott_runtime import I64


def should_limit_rows(sql: str, rowcount: I64, row_limit: I64, explain_mode: bool) -> bool:
    if explain_mode:
        return False
    words = sql.split()
    if not words or words[0].lower() != "select":
        return False
    for statement in sqlparse.parse(sql):
        for token in cast(Iterator[sqlparse.sql.Token], statement.flatten()):
            if token.match(sqlparse.tokens.Keyword, "LIMIT"):
                return False
    return row_limit != 0 and rowcount > row_limit
