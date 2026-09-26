from collections.abc import Iterable, Iterator
from typing import cast

import sqlparse
import sqlparse.engine.grouping
from sqlparse.sql import Function, Identifier, IdentifierList, Token, TokenList

from cott_runtime import CottList, Nothing, Some
from real.pgcli.parseutils_types import TableReference


def _opt(value: str | None) -> Some[str] | Nothing:
    return Some(value=value) if value is not None else Nothing()


def _str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _ttype(item: Token) -> str:
    ttype = cast(object, item.ttype)
    return "" if ttype is None else str(ttype)


def _value(item: Token) -> str:
    return _str(cast(object, item.value)) or ""


def _children(item: TokenList) -> list[Token]:
    return [child for child in cast(Iterable[object], item.tokens) if isinstance(child, Token)]


def _identifiers(item: IdentifierList) -> list[Token]:
    return [child for child in cast(Iterable[object], item.get_identifiers()) if isinstance(child, Token)]


def _is_subselect(item: Token) -> bool:
    if not bool(cast(object, item.is_group)) or not isinstance(item, TokenList):
        return False
    for child in _children(item):
        if _ttype(child) == "Token.Keyword.DML" and _value(child).upper() in ("SELECT", "INSERT", "UPDATE", "CREATE", "DELETE"):
            return True
    return False


def _from_part(parsed: TokenList, stop_at_punctuation: bool) -> Iterator[Token]:
    prefix_seen = False
    for item in _children(parsed):
        ttype = _ttype(item)
        upper = _value(item).upper()
        if prefix_seen:
            if isinstance(item, TokenList) and _is_subselect(item):
                yield from _from_part(item, stop_at_punctuation)
            elif stop_at_punctuation and ttype == "Token.Punctuation":
                return
            elif ttype == "Token.Keyword" and upper != "FROM" and not upper.endswith("JOIN"):
                prefix_seen = False
            else:
                yield item
        elif ttype in ("Token.Keyword", "Token.Keyword.DML"):
            if upper in ("COPY", "FROM", "INTO", "UPDATE", "TABLE") or upper.endswith("JOIN"):
                prefix_seen = True
        elif isinstance(item, IdentifierList):
            for identifier in _identifiers(item):
                if _ttype(identifier) == "Token.Keyword" and _value(identifier).upper() == "FROM":
                    prefix_seen = True
                    break


def _has_function(item: TokenList) -> bool:
    return any(isinstance(child, Function) for child in _children(item))


def _normalized(item: TokenList) -> tuple[str | None, str | None, str | None]:
    name = _str(cast(object, item.get_real_name()))
    schema = _str(cast(object, item.get_parent_name()))
    alias = _str(cast(object, item.get_alias()))
    if not name:
        schema = None
        name = _str(cast(object, item.get_name()))
        alias = alias or name
    value = _value(item)
    schema_quoted = bool(schema) and value.startswith('"')
    if schema and not schema_quoted:
        schema = schema.lower()
    quote_count = value.count('"')
    name_quoted = quote_count > 2 or (quote_count > 0 and not schema_quoted)
    alias_quoted = bool(alias) and value.endswith('"')
    if alias_quoted or (name_quoted and not alias and name is not None and name.islower()):
        alias = '"' + (alias or name or "") + '"'
    if name and not name_quoted and not name.islower():
        if not alias:
            alias = name
        name = name.lower()
    return schema, name, alias


def extract_tables(sql: str) -> CottList[TableReference]:
    sqlparse.engine.grouping.MAX_GROUPING_DEPTH = None
    sqlparse.engine.grouping.MAX_GROUPING_TOKENS = None
    statements = [s for s in cast(Iterable[object], sqlparse.parse(sql)) if isinstance(s, TokenList)]
    result: list[TableReference] = []
    if not statements:
        return CottList(values=result)
    statement = statements[0]
    first = cast(object, statement.token_first())
    if not isinstance(first, Token):
        return CottList(values=result)
    insert_stmt = _value(first).lower() == "insert"
    allow_functions = not insert_stmt
    for item in _from_part(statement, insert_stmt):
        if isinstance(item, IdentifierList):
            for identifier in _identifiers(item):
                if not isinstance(identifier, TokenList):
                    continue
                name = _str(cast(object, identifier.get_real_name()))
                if name:
                    result.append(TableReference(schema=_opt(_str(cast(object, identifier.get_parent_name()))), name=name, alias_name=_opt(_str(cast(object, identifier.get_alias()))), is_function=allow_functions and _has_function(identifier)))
        elif isinstance(item, Identifier):
            schema, name, alias = _normalized(item)
            if name:
                result.append(TableReference(schema=_opt(schema), name=name, alias_name=_opt(alias), is_function=allow_functions and _has_function(item)))
        elif isinstance(item, Function):
            _schema, name, alias = _normalized(item)
            if name:
                result.append(TableReference(schema=Nothing(), name=name, alias_name=_opt(alias), is_function=allow_functions))
    return CottList(values=result)
