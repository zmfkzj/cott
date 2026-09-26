import re
from typing import Any, cast

import sqlparse
import sqlparse.engine.grouping
import sqlparse.sql
import sqlparse.tokens

from cott_runtime import CottList, Nothing, Option, Some
from real.pgcli.completion_types import FunctionUsage_Call, FunctionUsage_Signature, FunctionUsage_Special, Suggestion, Suggestion_Alias, Suggestion_Column, Suggestion_Database, Suggestion_Datatype, Suggestion_FromClauseItem, Suggestion_Function, Suggestion_Join, Suggestion_JoinCondition, Suggestion_Keyword, Suggestion_NamedQuery, Suggestion_Path, Suggestion_Schema, Suggestion_Special, Suggestion_Table, Suggestion_TableFormat, Suggestion_View
from real.pgcli.parseutils import extract_tables, find_previous_keyword, isolate_query_ctes, last_word, table_reference_ref
from real.pgcli.parseutils_types import CteTable, TableReference, WordBoundary_AllPunctuations, WordBoundary_ManyPunctuations


def _opt(value: str | None) -> Option[str]:
    return Some(value=value) if value is not None else Nothing()


def _parse(text: str) -> Any:
    return cast(Any, sqlparse).parse(text)


def _is(token: Any, name: str) -> bool:
    if name == "Identifier":
        return isinstance(token, sqlparse.sql.Identifier)
    if name == "Comparison":
        return isinstance(token, sqlparse.sql.Comparison)
    if name == "Where":
        return isinstance(token, sqlparse.sql.Where)
    if name == "TokenList":
        return isinstance(token, sqlparse.sql.TokenList)
    return False


def _keyword(last: str | None) -> Suggestion:
    return Suggestion_Keyword(last_token=_opt(last))


def _schema() -> Suggestion:
    return Suggestion_Schema(quoted=False)


def _column(refs: list[TableReference], require_last: bool, local_tables: list[CteTable], qualifiable: bool, context: str | None) -> Suggestion:
    return Suggestion_Column(table_refs=CottList(values=refs), require_last_table=require_last, local_tables=CottList(values=local_tables), qualifiable=qualifiable, context=_opt(context))


def _table(schema: str | None) -> Suggestion:
    return Suggestion_Table(schema=_opt(schema), table_refs=CottList(values=[]), local_tables=CottList(values=[]))


def _view(schema: str | None) -> Suggestion:
    return Suggestion_View(schema=_opt(schema), table_refs=CottList(values=[]))


def _function(schema: str | None, usage: str) -> Suggestion:
    if usage == "signature":
        return Suggestion_Function(schema=_opt(schema), table_refs=CottList(values=[]), usage=FunctionUsage_Signature())
    if usage == "special":
        return Suggestion_Function(schema=_opt(schema), table_refs=CottList(values=[]), usage=FunctionUsage_Special())
    return Suggestion_Function(schema=_opt(schema), table_refs=CottList(values=[]), usage=FunctionUsage_Call())


def _str_or_none(value: Any) -> str | None:
    return None if value is None else str(value)


def _partial_identifier(word: str) -> Any:
    p: Any = _parse(word)[0]
    if len(p.tokens) == 1 and _is(p.tokens[0], "Identifier"):
        return p.tokens[0]
    toks: Any = sqlparse.tokens
    if p.token_next_by(m=(toks.Error, '"'))[1] is not None:
        return _partial_identifier(word + '"')
    return None


def _split(full: str, before: str, parsed: Any) -> tuple[str, str, Any]:
    if not parsed:
        return (full, before, None)
    statement: Any = parsed[0]
    if len(parsed) > 1:
        current = len(before)
        start = 0
        end = 0
        for s in parsed:
            start, end = end, end + len(str(s))
            statement = s
            if end >= current:
                before = full[start:current]
                full = full[start:]
                break
    if statement.get_type() in ("CREATE", "CREATE OR REPLACE"):
        first: Any = statement.token_first()
        if first is not None:
            nxt: Any = statement.token_next(statement.token_index(first))[1]
            if nxt is not None and str(nxt.value).upper() == "FUNCTION":
                match = re.search(r"(\$.*?\$)([\s\S]*?)\1", full, re.M)
                if match is not None and match.start(2) <= len(before) < match.end(2):
                    body_before = before[match.start(2):]
                    return _split(full[match.start(2):match.end(2)], body_before, _parse(body_before))
    return (full, before, statement)


def _find_prev(sql: str, n_skip: int) -> tuple[Any, str]:
    found = find_previous_keyword(sql, n_skip)
    if not isinstance(found.keyword, Some):
        return (None, found.text)
    target = len(found.text)
    consumed = 0
    for token in _parse(sql)[0].flatten():
        consumed += len(str(token.value))
        if consumed == target:
            return (token, found.text)
    return (None, found.text)


def _reduce(cells: list[str], n_skip: int) -> Any:
    token, text = _find_prev(cells[0], n_skip)
    cells[0] = text
    return token


def _tables(cells: list[str], full_text: str, statement: Any, scope: str) -> list[TableReference]:
    refs = list(extract_tables(full_text if scope == "full" else cells[0]))
    if scope == "insert":
        return refs[:1]
    if str(statement.token_first().value).lower() == "insert":
        return refs[1:]
    return refs


def _identifier_schema(identifier: Any) -> str | None:
    if identifier is None:
        return None
    parent = _str_or_none(identifier.get_parent_name())
    if not parent:
        return None
    return parent if str(identifier.value).startswith('"') else parent.lower()


def _parent(identifier: Any) -> str | None:
    if identifier is None:
        return None
    parent = _str_or_none(identifier.get_parent_name())
    return parent if parent else None


def _identifies(ident: str, table: TableReference) -> bool:
    alias = table.alias_name
    if isinstance(alias, Some) and ident == alias.value:
        return True
    if ident == table.name:
        return True
    schema = table.schema
    return isinstance(schema, Some) and bool(schema.value) and ident == schema.value + "." + table.name


def _last_child_value(statement: Any) -> str:
    if statement is None:
        return ""
    token: Any = statement.token_prev(len(statement.tokens))[1]
    return str(token.value).lower() if token is not None else ""


def _expression(cells: list[str], full_text: str, statement: Any, identifier: Any, local_tables: list[CteTable], value: str) -> list[Suggestion]:
    parent = _parent(identifier)
    if parent is not None:
        refs = [table for table in _tables(cells, full_text, statement, "full") if _identifies(parent, table)]
        return [_column(refs, False, local_tables, False, None), _table(parent), _view(parent), _function(parent, "call")]
    return [_column(_tables(cells, full_text, statement, "full"), False, local_tables, True, None), _function(None, "call"), _keyword(value.upper())]


def _special(text: str) -> list[Suggestion]:
    text = text.lstrip()
    head, _, rest = text.partition(" ")
    cmd = head.strip().replace("+", "")
    arg = rest.strip()
    if cmd == text:
        return [Suggestion_Special()]
    if cmd in ("\\c", "\\connect"):
        return [Suggestion_Database()]
    if cmd == "\\T":
        return [Suggestion_TableFormat()]
    if cmd == "\\dn":
        return [_schema()]
    schema: str | None = None
    if arg:
        token: Any = _parse(arg)[0].tokens[0]
        if _is(token, "TokenList"):
            schema = _str_or_none(token.get_parent_name())
    if cmd == "\\d":
        return [_table(schema), _view(schema)] if schema else [_schema(), _table(None), _view(None)]
    if cmd in ("\\dT", "\\df", "\\sf", "\\dt", "\\dv"):
        scoped = schema if schema else None
        if cmd == "\\dT":
            item: Suggestion = Suggestion_Datatype(schema=_opt(scoped))
        elif cmd == "\\dt":
            item = _table(scoped)
        elif cmd == "\\dv":
            item = _view(scoped)
        else:
            item = _function(scoped, "special")
        return [item] if schema else [_schema(), item]
    if cmd in ("\\n", "\\ns", "\\nd", "\\nq"):
        return [Suggestion_NamedQuery()]
    return [_keyword(None), Suggestion_Special()]


def _datatype_keyword(cells: list[str], token: Any) -> bool:
    if isinstance(token, str):
        return True
    if not token.is_keyword:
        return False
    keyword, _ = _find_prev(cells[0].rstrip(), 1)
    if keyword is None:
        return False
    toks: Any = sqlparse.tokens
    return keyword.ttype is not toks.DML


def _by_token(cells: list[str], full_text: str, statement: Any, identifier: Any, local_tables: list[CteTable], token: Any) -> list[Suggestion]:
    is_text = isinstance(token, str)
    if is_text:
        value = str(token).lower()
    elif _is(token, "Comparison"):
        value = str(token.tokens[-1].value).lower()
    elif _is(token, "Where"):
        keyword = _reduce(cells, 0)
        if keyword is None:
            return []
        return _by_token(cells, full_text, statement, identifier, local_tables, keyword)
    elif _is(token, "Identifier"):
        keyword, _ = _find_prev(cells[0], 0)
        if keyword is not None and str(keyword.value) == "(":
            return _by_token(cells, full_text, statement, identifier, local_tables, "type")
        return [_keyword(None)]
    else:
        value = str(token.value).lower()
    is_keyword = not is_text and bool(token.is_keyword)

    if is_text and token == "":
        return [_keyword(None), Suggestion_Special()]
    if value.endswith("("):
        parsed: Any = _parse(cells[0])[0]
        if parsed.tokens and _is(parsed.tokens[-1], "Where"):
            cols = _by_token(cells, full_text, statement, identifier, local_tables, "where")
            where: Any = parsed.tokens[-1]
            prior: Any = where.token_prev(len(where.tokens) - 1)[1]
            if _is(prior, "Comparison"):
                prior = prior.tokens[-1]
            return [_keyword(None)] if str(prior.value).lower() == "exists" else cols
        prev: Any = parsed.token_prev(len(parsed.tokens) - 1)[1]
        if prev is not None and prev.value and str(prev.value).lower().split(" ")[-1] == "using":
            return [_column(_tables(cells, full_text, statement, "before"), True, local_tables, False, None)]
        if str(parsed.token_first().value).lower() == "select" and last_word(cells[0], WordBoundary_AllPunctuations()).startswith("("):
            return [_keyword(None)]
        if prev is not None:
            pp: Any = parsed.token_prev(parsed.token_index(prev))[1]
            if pp is not None and pp.normalized == "INTO":
                return [_column(_tables(cells, full_text, statement, "insert"), False, [], False, "insert")]
        return _expression(cells, full_text, statement, identifier, local_tables, value)
    if value == "set":
        if str(_parse(cells[0])[0].token_first().value).upper() == "SET":
            return [_keyword("SET")]
        return [_column(_tables(cells, full_text, statement, "full"), False, local_tables, False, None)]
    if value in ("select", "where", "having", "group by", "order by", "distinct"):
        return _expression(cells, full_text, statement, identifier, local_tables, value)
    if value == "as":
        return []
    is_join = value.endswith("join") and is_keyword
    if is_join or value in ("copy", "from", "update", "into", "describe", "truncate"):
        schema = _identifier_schema(identifier)
        refs = list(extract_tables(cells[0]))
        out: list[Suggestion] = []
        if schema is None:
            out.append(_schema())
        if value == "from" or is_join:
            out.append(Suggestion_FromClauseItem(schema=_opt(schema), table_refs=CottList(values=refs), local_tables=CottList(values=local_tables)))
        elif value == "truncate":
            out.append(_table(schema))
        else:
            out.extend([_table(schema), _view(schema)])
        last = _last_child_value(statement)
        if is_join and last.endswith("join") and last not in ("cross join", "natural join"):
            out.append(Suggestion_Join(table_refs=CottList(values=_tables(cells, full_text, statement, "before")), schema=_opt(schema)))
        return out
    if value == "function":
        schema = _identifier_schema(identifier)
        if is_text:
            return []
        try:
            index: int = int(statement.token_index(token))
        except ValueError:
            return []
        previous: Any = statement.token_prev(index)[1]
        if previous is None or str(previous.value).lower() not in ("drop", "alter", "create", "create or replace"):
            return []
        function = _function(schema, "signature")
        return [_schema(), function] if schema is None else [function]
    if value in ("table", "view"):
        schema = _identifier_schema(identifier)
        item = _table(schema) if value == "table" else _view(schema)
        return [item] if schema is not None else [_schema(), item]
    if value == "column":
        return [_column(_tables(cells, full_text, statement, "full"), False, [], False, None)]
    if value == "on":
        refs = _tables(cells, full_text, statement, "before")
        parent = _parent(identifier)
        allow_join_condition = _last_child_value(statement) in ("on", "and", "or")
        if parent is not None:
            matching = [table for table in refs if _identifies(parent, table)]
            out = [_column(matching, False, local_tables, False, None), _table(parent), _view(parent), _function(parent, "call")]
            if matching and allow_join_condition:
                out.append(Suggestion_JoinCondition(table_refs=CottList(values=refs), parent=Some(value=matching[-1])))
            return out
        aliases = [table_reference_ref(table) for table in refs]
        alias_item = Suggestion_Alias(aliases=CottList(values=aliases))
        if allow_join_condition:
            return [alias_item, Suggestion_JoinCondition(table_refs=CottList(values=refs), parent=Nothing())]
        return [alias_item]
    if value in ("c", "use", "database", "template"):
        return [Suggestion_Database()]
    if value == "schema":
        keyword = _reduce(cells, 2)
        return [Suggestion_Schema(quoted=keyword is not None and str(keyword.value).lower() == "set")]
    if value.endswith(",") or value in ("=", "and", "or"):
        keyword = _reduce(cells, 0)
        if keyword is None:
            return []
        return _by_token(cells, full_text, statement, identifier, local_tables, keyword)
    if value == "::" or (value == "type" and _datatype_keyword(cells, token)):
        schema = _identifier_schema(identifier)
        out = [Suggestion_Datatype(schema=_opt(schema)), _table(schema)]
        if schema is None:
            out.append(_schema())
        return out
    if value in ("alter", "create", "drop"):
        return [_keyword(value.upper())]
    if value == "to":
        return [_schema()]
    if is_keyword:
        keyword = _reduce(cells, 1)
        if keyword is None:
            return [_keyword(value.upper())]
        return _by_token(cells, full_text, statement, identifier, local_tables, keyword)
    return [_keyword(None)]


def _suggest(full_text: str, text_before_cursor: str) -> list[Suggestion]:
    grouping: Any = sqlparse.engine.grouping
    grouping.MAX_GROUPING_DEPTH = None
    grouping.MAX_GROUPING_TOKENS = None
    if full_text.startswith("\\i "):
        return [Suggestion_Path()]
    word = last_word(text_before_cursor, WordBoundary_ManyPunctuations())
    save_prefix = r"^\s*\\ns\s+[A-z0-9\-_]+\s+"
    if re.match(save_prefix, full_text):
        full_text = re.sub(save_prefix, "", full_text)
    if re.match(save_prefix, text_before_cursor):
        text_before_cursor = re.sub(save_prefix, "", text_before_cursor)
    isolated = isolate_query_ctes(full_text, text_before_cursor)
    if not isinstance(isolated, Some):
        return []
    query = isolated.value
    full_text = query.full_text
    text_before_cursor = query.text_before_cursor
    local_tables = list(query.local_tables)
    identifier: Any = None
    if word and not word.endswith("(") and not word.startswith("\\"):
        text_before_cursor = text_before_cursor[:-len(word)]
        identifier = _partial_identifier(word)
    parsed: Any = _parse(text_before_cursor)
    full_text, text_before_cursor, statement = _split(full_text, text_before_cursor, parsed)
    if statement is None:
        return _by_token([text_before_cursor], full_text, statement, identifier, local_tables, "")
    first: Any = statement.token_first()
    if first is not None and str(first.value).startswith("\\"):
        return _special(text_before_cursor + word)
    last: Any = statement.token_prev(len(statement.tokens))[1]
    token: Any = last if last is not None else ""
    return _by_token([text_before_cursor], full_text, statement, identifier, local_tables, token)


def suggest_sql_completions(full_text: str, text_before_cursor: str) -> CottList[Suggestion]:
    try:
        return CottList(values=_suggest(full_text, text_before_cursor))
    except Exception:
        return CottList(values=[])
