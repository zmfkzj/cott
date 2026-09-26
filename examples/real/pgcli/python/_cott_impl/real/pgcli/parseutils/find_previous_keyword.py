from collections.abc import Iterable
from typing import Final, cast

import sqlparse
import sqlparse.engine.grouping
from sqlparse.sql import Token

from cott_runtime import Nothing, Some, U64
from real.pgcli.parseutils_types import PreviousKeyword

_LOGICAL_OPERATORS: Final[str] = "AND OR NOT BETWEEN"


def find_previous_keyword(sql: str, n_skip: U64) -> PreviousKeyword:
    if not sql.strip():
        return PreviousKeyword(keyword=Nothing(), text="")
    sqlparse.engine.grouping.MAX_GROUPING_DEPTH = None
    sqlparse.engine.grouping.MAX_GROUPING_TOKENS = None
    raw = cast(Iterable[object], sqlparse.parse(sql)[0].flatten())
    flattened: list[Token] = [item for item in raw if isinstance(item, Token)]
    values: list[str] = [str(cast(object, item.value)) for item in flattened]
    candidates = flattened[: len(flattened) - n_skip]
    logical = _LOGICAL_OPERATORS.split()
    for index in range(len(candidates) - 1, -1, -1):
        token = candidates[index]
        value = values[index]
        is_keyword = bool(cast(object, token.is_keyword))
        if value == "(" or (is_keyword and value.upper() not in logical):
            return PreviousKeyword(keyword=Some(value=value), text="".join(values[: index + 1]))
    return PreviousKeyword(keyword=Nothing(), text="")
