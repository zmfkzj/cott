from collections.abc import Iterable
from typing import cast

import sqlparse
import sqlparse.engine.grouping
import sqlparse.sql
import sqlparse.tokens


def is_open_quote(sql: str) -> bool:
    sqlparse.engine.grouping.MAX_GROUPING_DEPTH = None
    sqlparse.engine.grouping.MAX_GROUPING_TOKENS = None
    for statement in sqlparse.parse(sql):
        for token in cast(Iterable[object], statement.flatten()):
            if isinstance(token, sqlparse.sql.Token) and token.match(sqlparse.tokens.Error, ("'", "$")):
                return True
    return False
