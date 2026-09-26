from typing import Any, cast

import sqlparse
import sqlparse.engine.grouping
import sqlparse.sql
import sqlparse.tokens
from cott_runtime import CottList, Nothing, Option, Some
from real.pgcli.parseutils_types import CteDefinition, CteExtraction


def _token_start_pos(tokens: Any, i: int) -> int:
    return sum(len(str(token)) for token in tokens[:i])


def _append_name(names: list[str], item: Any) -> None:
    name = cast(object, item.get_name())
    if isinstance(name, str):
        names.append(name)


def _column_names(parsed: Any) -> list[str]:
    idx, tok = parsed.token_next_by(t=sqlparse.tokens.DML)
    tok_val = tok.value.lower() if tok is not None else None
    if tok_val in ("insert", "update", "delete"):
        idx, tok = parsed.token_next_by(idx, (sqlparse.tokens.Keyword, "returning"))
    elif tok_val != "select":
        return []
    idx, tok = parsed.token_next(idx, skip_ws=True, skip_cm=True)
    names: list[str] = []
    found = cast(object, tok)
    if isinstance(found, sqlparse.sql.Identifier):
        _append_name(names, cast(Any, found))
    elif isinstance(found, sqlparse.sql.IdentifierList):
        group: Any = found
        for item in group.get_identifiers():
            if isinstance(cast(object, item), sqlparse.sql.Identifier):
                _append_name(names, item)
    return names


def _cte_from_token(token: Any, pos0: int) -> CteDefinition | None:
    name = token.get_real_name()
    if not name:
        return None
    idx, parens = token.token_next_by(sqlparse.sql.Parenthesis)
    if parens is None:
        return None
    start = pos0 + _token_start_pos(token.tokens, idx)
    stop = start + len(str(parens))
    return CteDefinition(name=str(name), columns=CottList(values=_column_names(parens)), start=start, stop=stop)


def _extract(sql: str) -> CteExtraction:
    grouping: Any = sqlparse.engine.grouping
    grouping.MAX_GROUPING_DEPTH = None
    grouping.MAX_GROUPING_TOKENS = None
    if not sql:
        return CteExtraction(ctes=CottList(values=[]), remainder="")
    parsed: Any = sqlparse.parse(sql)[0]
    idx, token = parsed.token_next(-1, skip_ws=True, skip_cm=True)
    if token is None or token.ttype != sqlparse.tokens.CTE:
        return CteExtraction(ctes=CottList(values=[]), remainder=sql)
    idx, token = parsed.token_next(idx)
    if token is None:
        return CteExtraction(ctes=CottList(values=[]), remainder="")
    start_pos = _token_start_pos(parsed.tokens, idx)
    ctes: list[CteDefinition] = []
    found = cast(object, token)
    if isinstance(found, sqlparse.sql.IdentifierList):
        identifiers: Any = found
        for item in identifiers.get_identifiers():
            cte = _cte_from_token(item, start_pos + _token_start_pos(identifiers.tokens, identifiers.token_index(item)))
            if cte is not None:
                ctes.append(cte)
    elif isinstance(found, sqlparse.sql.Identifier):
        cte = _cte_from_token(token, start_pos)
        if cte is not None:
            ctes.append(cte)
    remainder = "".join(str(item) for item in parsed.tokens[parsed.token_index(token) + 1:])
    return CteExtraction(ctes=CottList(values=ctes), remainder=remainder)


def extract_ctes(sql: str) -> Option[CteExtraction]:
    try:
        return Some(value=_extract(sql))
    except (TypeError, AttributeError):
        return Nothing()
