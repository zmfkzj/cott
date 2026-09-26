from typing import cast

import sqlparse
import sqlparse.engine.grouping
import sqlparse.sql
import sqlparse.tokens
from cott_runtime import CottList


def _is_unconditional_update(query: str) -> bool:
    statements = sqlparse.parse(query)
    if not statements:
        return False
    statement = statements[0]
    first = cast(object, statement.token_first(skip_cm=True))
    if not isinstance(first, sqlparse.sql.Token):
        return False
    ttype = cast(object, first.ttype)
    if ttype is not sqlparse.tokens.DML or str(cast(object, first.value)).upper() != "UPDATE":
        return False
    children = cast(object, statement.tokens)
    if isinstance(children, list):
        for child in cast(list[object], children):
            if isinstance(child, sqlparse.sql.Where):
                return False
    return True


def is_destructive(queries: str, keywords: CottList[str]) -> bool:
    sqlparse.engine.grouping.MAX_GROUPING_DEPTH = None
    sqlparse.engine.grouping.MAX_GROUPING_TOKENS = None
    lowered: set[str] = set()
    check_update = False
    for keyword in keywords:
        lowered.add(keyword.lower())
        if keyword == "unconditional_update":
            check_update = True
    for query in sqlparse.split(queries):
        if not query:
            continue
        formatted = str(sqlparse.format(query.lower(), strip_comments=True)).strip()
        if check_update and _is_unconditional_update(query):
            return True
        if formatted and formatted.split()[0] in lowered:
            return True
    return False
