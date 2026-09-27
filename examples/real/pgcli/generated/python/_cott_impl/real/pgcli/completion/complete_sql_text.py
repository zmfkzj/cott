import json
import math
import re
from collections.abc import Iterable
from typing import Any, cast

from cott_runtime import FrozenMap, Nothing, Opaque, Option, Some
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document

from real.pgcli.completion import suggest_sql_completions
from real.pgcli.completion_types import (
    CompletionList,
    CompletionRequest,
    FunctionUsage,
    FunctionUsage_From,
    FunctionUsage_Signature,
    FunctionUsage_Special,
    PGLITERALS_JSON,
    Suggestion,
    Suggestion_Alias,
    Suggestion_Column,
    Suggestion_Database,
    Suggestion_Datatype,
    Suggestion_FromClauseItem,
    Suggestion_Function,
    Suggestion_Join,
    Suggestion_JoinCondition,
    Suggestion_Keyword,
    Suggestion_NamedQuery,
    Suggestion_Schema,
    Suggestion_Special,
    Suggestion_Table,
    Suggestion_TableFormat,
    Suggestion_View,
)
from real.pgcli.parseutils import last_word, parse_function_defaults, table_reference_ref
from real.pgcli.parseutils_types import CteTable, TableReference, WordBoundary_MostPunctuations


def _strings(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [item for item in cast(list[object], raw) if isinstance(item, str)]


def _literals() -> tuple[dict[str, list[str]], list[str], list[str], set[str]]:
    parsed = cast(object, json.loads(PGLITERALS_JSON))
    if not isinstance(parsed, dict):
        return {}, [], [], set()
    data = cast(dict[object, object], parsed)
    tree: dict[str, list[str]] = {}
    raw_tree = data.get("keywords")
    if isinstance(raw_tree, dict):
        for key, value in cast(dict[object, object], raw_tree).items():
            if isinstance(key, str):
                tree[key] = _strings(value)
    return tree, _strings(data.get("functions")), _strings(data.get("datatypes")), set(_strings(data.get("reserved")))


def _text_option(value: Option[str]) -> str | None:
    if isinstance(value, Some):
        return value.value
    return None


def _table_option(value: Option[TableReference]) -> TableReference | None:
    if isinstance(value, Some):
        return value.value
    return None


def _option(value: str | None) -> Option[str]:
    if value is not None:
        return Some(value=value)
    return Nothing()


def _escape(ctx: dict[str, Any], name: str) -> str:
    if name and (not re.match(r"^[_a-z][_a-z0-9\$]*$", name) or name.upper() in ctx["reserved"] or name.upper() in ctx["funcset"]):
        return '"' + name + '"'
    return name


def _unescape(name: str) -> str:
    if name and name.startswith('"') and name.endswith('"'):
        return name[1:-1]
    return name


def _case(ctx: dict[str, Any], word: str) -> str:
    return cast(str, ctx["casemap"].get(word, word))


def _alias_of(table_name: str, alias_map: FrozenMap[str, str]) -> str:
    if table_name in alias_map:
        return alias_map[table_name]
    uppercase = "".join(char for char in table_name if char.isupper())
    if uppercase:
        return uppercase
    return "".join(char for index, char in enumerate(table_name) if char != "_" and (index == 0 or table_name[index - 1] == "_"))


def _conv(table: TableReference) -> tuple[str | None, str, str | None, bool]:
    return _text_option(table.schema), table.name, _text_option(table.alias_name), table.is_function


def _ref(table: tuple[str | None, str, str | None, bool]) -> str:
    return table_reference_ref(TableReference(schema=_option(table[0]), name=table[1], alias_name=_option(table[2]), is_function=table[3]))


def _norm(ref: str) -> str:
    return ref if ref.startswith('"') else '"' + ref.lower() + '"'


def _arglist(function: tuple[Any, ...], usage: str, casemap: dict[str, str]) -> str:
    names: list[str] = function[2] or []
    modes: list[str] = function[4] or []
    types: list[str] = function[3] or []
    args: list[tuple[str, str]] = []
    if names:
        actual_modes = modes if modes else ["i"] * len(names)
        actual_types = types if types else ["None"] * len(names)
        args = [(name, datatype) for name, datatype, mode in zip(names, actual_types, actual_modes) if mode in ("i", "b", "v")]
    n = len(args)
    if usage == "call":
        if n < 2 or "v" in modes:
            return "()"
        defaults = parse_function_defaults(function[10] if function[10] is not None else "")
        d = len(defaults)
        width = max(len(name) for name, _datatype in args) if n > 2 else 0
        parts: list[str] = []
        for k, (name, _datatype) in enumerate(args):
            default = re.sub(r"::[\w\.]+(\[\])?$", "", defaults[k - n + d]) if k + d >= n else ""
            parts.append(casemap.get(name, name).ljust(width) + " := " + default)
        if n > 2:
            return "(" + ",".join("\n    " + part for part in parts if part) + "\n)"
        return "(" + ", ".join(part for part in parts if part) + ")"
    if usage == "display":
        parts = [casemap.get(name, name) for name, _datatype in args]
    else:
        parts = [casemap.get(name, name) + " " + datatype for name, datatype in args]
    return "(" + ", ".join(part for part in parts if part) + ")"


def _match(synonym: str, text: str, pattern: str, strict: bool) -> tuple[float, int] | None:
    lowered = synonym.lower()
    if strict:
        return (-math.inf, 0) if lowered.startswith(text) else None
    if lowered[: len(text) + 1] in (text, text + " "):
        return math.inf, -1
    found = re.search(pattern, _unescape(lowered))
    if found is None:
        return None
    return -len(found.group()), -found.start()


def _find(ctx: dict[str, Any], text: str, collection: Iterable[str | tuple[Any, ...]], strict: bool, meta: str | None) -> list[tuple[Completion, tuple[Any, ...]]]:
    type_names = ("keyword", "function", "view", "table", "datatype", "database", "schema", "column", "table alias", "join", "name join", "fk join", "table format")
    type_priority = type_names.index(meta) if meta in type_names else -1
    text = last_word(text, WordBoundary_MostPunctuations()).lower()
    text_len = len(text)
    if text.startswith('"'):
        text = text[1:]
    pattern = "(" + ".*?".join(re.escape(char) for char in text) + ")" if not strict else ""
    counts: dict[str, int] = ctx["kwcounts"] if strict else ctx["namecounts"]
    result: list[tuple[Completion, tuple[Any, ...]]] = []
    for candidate in collection:
        if isinstance(candidate, str):
            completion = candidate
            display = candidate
            display_meta = meta
            priority = 0
            priority2 = 0
            sort_key = _match(candidate, text, pattern, strict)
        else:
            completion, priority, own_meta, synonyms, priority2, display = candidate
            display_meta = own_meta if own_meta is not None else meta
            keys = [key for synonym in synonyms if (key := _match(synonym, text, pattern, strict)) is not None]
            sort_key = max(keys) if keys else None
        if sort_key is None:
            continue
        if display_meta is not None and len(display_meta) > 50:
            display_meta = display_meta[:47] + "..."
        lexical = tuple(0 if char in " _" else -ord(char) for char in _unescape(completion.lower())) + (1,) + tuple(completion)
        inserted = _case(ctx, completion)
        shown = _case(ctx, display)
        count = counts.get(inserted, 0)
        result.append((Completion(inserted, start_position=-text_len, display=shown, display_meta=display_meta), (sort_key, type_priority, priority, count, priority2, lexical)))
    return result


def _schemas_of(ctx: dict[str, Any], objects: dict[str, Any], schema: str | None) -> Iterable[str]:
    if schema:
        escaped = _escape(ctx, schema)
        return [escaped] if escaped in objects else []
    if ctx["spf"]:
        return cast(list[str], ctx["sp"])
    return objects.keys()


def _shown(ctx: dict[str, Any], schema: str, qualifier: str | None) -> str | None:
    return None if qualifier or schema in ctx["sp"] else schema


def _objects(ctx: dict[str, Any], objects: dict[str, Any], schema: str | None) -> list[tuple[str, str | None]]:
    return [(name, _shown(ctx, sch, schema)) for sch in _schemas_of(ctx, objects, schema) if sch in objects for name in objects[sch]]


def _alias_for(ctx: dict[str, Any], table: str, refs: list[tuple[str | None, str, str | None, bool]]) -> str:
    table = _case(ctx, table)
    taken = {_norm(_ref(ref)) for ref in refs}
    if ctx["gen"]:
        table = _alias_of(_unescape(table), ctx["amap"])
    if _norm(table) not in taken:
        return table
    index = 2
    while True:
        alias = '"' + table[1:-1] + str(index) + '"' if table.startswith('"') else table + str(index)
        if _norm(alias) not in taken:
            return alias
        index += 1


def _candidate(ctx: dict[str, Any], name: str, schema: str | None, function: tuple[Any, ...] | None, aliased: bool, refs: list[tuple[str | None, str, str | None, bool]], arg: str | None) -> tuple[Any, ...]:
    cased = _case(ctx, name)
    synonyms = (cased, _alias_of(cased, ctx["amap"]))
    tail = " " + _alias_for(ctx, cased, refs) if aliased else ""
    head = _case(ctx, schema) + "." if schema else ""
    if function is not None and arg == "call":
        suffix = _arglist(function, "call", ctx["casemap"])
        display_suffix = _arglist(function, "display", ctx["casemap"])
    elif function is not None and arg == "signature":
        suffix = _arglist(function, "signature", ctx["casemap"])
        display_suffix = suffix
    else:
        suffix = ""
        display_suffix = ""
    return head + cased + suffix + tail, 0, None, synonyms, 0 if schema else 1, head + cased + display_suffix + tail


def _fields(function: tuple[Any, ...]) -> list[list[Any]]:
    return_type: str = function[5].strip()
    if return_type.lower() == "void":
        return []
    modes: list[str] = function[4] or []
    if not modes:
        return [[function[1], return_type, False, None, []]]
    names: list[str] = function[2] or []
    types: list[str] = function[3] or ["None"] * len(modes)
    return [[name, datatype, False, None, []] for name, datatype, mode in zip(names, types, modes) if mode in ("o", "b", "t")]


def _scoped(ctx: dict[str, Any], refs: list[tuple[str | None, str, str | None, bool]], local_tables: Iterable[CteTable]) -> dict[tuple[str | None, str, str | None, bool], list[list[Any]]]:
    result: dict[tuple[str | None, str, str | None, bool], list[list[Any]]] = {}
    ctes = {_norm(table.name): table for table in local_tables}
    used: set[str] = set()
    for schema, name, alias, is_function in refs:
        normalized = _norm(name)
        if schema is None and normalized in ctes:
            columns: list[list[Any]] = [] if normalized in used else [[column, None, False, None, []] for column in ctes[normalized].columns]
            used.add(normalized)
            result.setdefault((None, name, "CTE", alias == "functions"), []).extend(columns)
            continue
        for sch in [schema] if schema else ctx["sp"]:
            relation = _escape(ctx, name)
            escaped_schema = _escape(ctx, sch)
            if is_function:
                for function in ctx["F"].get(escaped_schema, {}).get(relation, []):
                    result.setdefault((escaped_schema, relation, alias, True), []).extend(_fields(function))
            else:
                for objects in (ctx["T"], ctx["V"]):
                    found = objects.get(escaped_schema, {}).get(relation)
                    if found:
                        result.setdefault((escaped_schema, relation, alias, False), []).extend(found.values())
                        break
    return result


def _qualified_column(ctx: dict[str, Any], column: str, ref: str, qualify: bool) -> str:
    return ref + "." + _case(ctx, column) if qualify else _case(ctx, column)


def _keep_insert(column: list[Any]) -> bool:
    if not column[2] or column[3] is None:
        return True
    return not (re.match(r"^now\(\)$", column[3]) or re.match(r"^nextval\(", column[3]))


def _column(ctx: dict[str, Any], suggestion: Suggestion_Column) -> list[tuple[Completion, tuple[Any, ...]]]:
    refs = [_conv(ref) for ref in suggestion.table_refs]
    word: str = ctx["word"]
    qualify = False
    if suggestion.qualifiable:
        setting = ctx["qc"]
        if setting == "always":
            qualify = True
        elif setting == "if_more_than_one_table":
            qualify = len(refs) > 1
        elif setting != "never":
            return []
    columns = _scoped(ctx, refs, suggestion.local_tables)
    if suggestion.require_last_table:
        if not refs:
            return []
        last = _ref(refs[-1])
        other = {column[0] for key, cols in columns.items() if _ref(key) != last for column in cols}
        columns = {key: [column for column in cols if column[0] in other] for key, cols in columns.items() if _ref(key) == last}
    lastword = last_word(word, WordBoundary_MostPunctuations())
    if lastword == "*":
        if _text_option(suggestion.context) == "insert":
            columns = {key: [column for column in cols if _keep_insert(column)] for key, cols in columns.items()}
        if ctx["order"] == "alphabetic":
            columns = {key: sorted(cols, key=lambda column: column[0]) for key, cols in columns.items()}
        if lastword != word and len(refs) == 1 and word[-len(lastword) - 1] == ".":
            separator = ", " + word[:-1]
            text = separator.join(_case(ctx, _qualified_column(ctx, column[0], _ref(key), qualify)) for key, cols in columns.items() for column in cols)
        else:
            text = ", ".join(_qualified_column(ctx, column[0], _ref(key), qualify) for key, cols in columns.items() for column in cols)
        return [(Completion(text, start_position=-1, display="*", display_meta="columns"), (1, 1, 1))]
    candidates: list[tuple[Any, ...]] = []
    for key, cols in columns.items():
        ref = _ref(key)
        for column in cols:
            name: str = column[0]
            completion = _qualified_column(ctx, name, ref, qualify)
            candidates.append((completion, 0, "column", (name, _alias_of(_case(ctx, name), ctx["amap"])), 0, completion))
    return _find(ctx, word, candidates, False, "column")


def _join(ctx: dict[str, Any], suggestion: Suggestion_Join) -> list[tuple[Completion, tuple[Any, ...]]]:
    refs = [_conv(table) for table in suggestion.table_refs]
    schema = _text_option(suggestion.schema)
    columns = _scoped(ctx, refs, [])
    qualified = {_norm(_ref(table)): table[0] for table in refs}
    order = {_norm(_ref(table)): index for index, table in enumerate(refs)}
    taken = set(qualified)
    others = {(key[0], key[1]) for key in list(columns)[:-1]}
    candidates: list[tuple[Any, ...]] = []
    for key, cols in columns.items():
        right_ref = _ref(key)
        for column in cols:
            for fk in column[4]:
                right = key[0], key[1], column[0]
                child = fk[3], fk[4], fk[5]
                parent = fk[0], fk[1], fk[2]
                left = child if parent == right else parent
                if schema and left[0] != schema:
                    continue
                table_name = _case(ctx, left[1])
                left_column = _case(ctx, left[2])
                right_column = _case(ctx, right[2])
                if ctx["gen"] or _norm(left[1]) in taken:
                    alias = _alias_for(ctx, left[1], refs)
                    join = table_name + " " + alias + " ON " + alias + "." + left_column + " = " + right_ref + "." + right_column
                else:
                    join = table_name + " ON " + table_name + "." + left_column + " = " + right_ref + "." + right_column
                short = _alias_of(table_name, ctx["amap"])
                synonyms = (join, short + " ON " + short + "." + left_column + " = " + right_ref + "." + right_column)
                if not schema and ((qualified[_norm(right_ref)] and left[0] == right[0]) or left[0] not in (right[0], "public")):
                    join = left[0] + "." + join
                priority = order[_norm(right_ref)] * 2 + (0 if (left[0], left[1]) in others else 1)
                candidates.append((join, priority, "join", synonyms, 0, join))
    return _find(ctx, ctx["word"], candidates, False, "join")


def _add_condition(ctx: dict[str, Any], candidates: list[tuple[Any, ...]], seen: set[str], prefix: str, left: str, right: str, right_ref: str, priority: int, meta: str, order: dict[str, int]) -> None:
    condition = prefix + _case(ctx, left) + " = " + right_ref + "." + _case(ctx, right)
    if condition not in seen:
        seen.add(condition)
        candidates.append((condition, priority + order[right_ref], meta, (condition,), 0, condition))


def _join_condition(ctx: dict[str, Any], suggestion: Suggestion_JoinCondition) -> list[tuple[Completion, tuple[Any, ...]]]:
    refs = [_conv(table) for table in suggestion.table_refs]
    if not refs:
        return []
    columns = _scoped(ctx, refs, [])
    parent = _table_option(suggestion.parent)
    left_ref = _ref(_conv(parent)) if parent is not None else _ref(refs[-1])
    matching = [(key, cols) for key, cols in columns.items() if _ref(key) == left_ref]
    if not matching:
        return []
    left_key, left_cols = matching[-1]
    prefix = "" if parent is not None else _ref(left_key) + "."
    order = {_ref(table): index for index, table in enumerate(refs)}
    candidates: list[tuple[Any, ...]] = []
    seen: set[str] = set()
    other_columns: dict[tuple[str | None, str, str], list[tuple[str | None, str, str | None, bool]]] = {}
    for key, cols in columns.items():
        if _ref(key) != left_ref:
            for column in cols:
                other_columns.setdefault((key[0], key[1], column[0]), []).append(key)
    for column in left_cols:
        for fk in column[4]:
            current = left_key[0], left_key[1], column[0]
            child = fk[3], fk[4], fk[5]
            parent_key = fk[0], fk[1], fk[2]
            left, right = (child, parent_key) if current == child else (parent_key, child)
            for key in other_columns.get(right, []):
                _add_condition(ctx, candidates, seen, prefix, left[2], right[2], _ref(key), 2000, "fk join", order)
    by_name: dict[tuple[str, str | None], list[tuple[str | None, str, str | None, bool]]] = {}
    for key, cols in columns.items():
        for column in cols:
            by_name.setdefault((column[0], column[1]), []).append(key)
    for column in left_cols:
        for key in by_name.get((column[0], column[1]), []):
            if _ref(key) != _ref(left_key):
                priority = 1000 if column[1] in ("integer", "bigint", "smallint") else 0
                _add_condition(ctx, candidates, seen, prefix, column[0], column[0], _ref(key), priority, "name join", order)
    return _find(ctx, ctx["word"], candidates, False, "join")


def _function(ctx: dict[str, Any], schema: str | None, refs: list[tuple[str | None, str, str | None, bool]], usage: FunctionUsage, aliased: bool) -> list[tuple[Completion, tuple[Any, ...]]]:
    is_from = isinstance(usage, FunctionUsage_From)
    if not is_from:
        aliased = False
    if isinstance(usage, FunctionUsage_Signature):
        arg: str | None = "signature"
        is_call = False
    elif isinstance(usage, FunctionUsage_Special):
        arg = None
        is_call = False
    elif is_from:
        arg = "call"
        is_call = False
    else:
        arg = "call"
        is_call = True
    functions: dict[str, dict[str, list[tuple[Any, ...]]]] = ctx["F"]
    seen: set[tuple[Any, ...]] = set()
    candidates: list[tuple[Any, ...]] = []
    for sch in _schemas_of(ctx, functions, schema):
        if sch not in functions:
            continue
        for name, rows in functions[sch].items():
            for function in rows:
                if is_from:
                    keep = not function[6] and not function[7] and not function[9] and (function[0] == "public" or function[0] in ctx["sp"] or function[0] == schema)
                else:
                    keep = not function[9] and (function[0] == "public" or function[0] == schema)
                if keep:
                    candidate = _candidate(ctx, name, _shown(ctx, sch, schema), function, aliased, refs, arg)
                    if candidate not in seen:
                        seen.add(candidate)
                        candidates.append(candidate)
    result = _find(ctx, ctx["word"], candidates, False, "function")
    if not schema and is_call:
        result.extend(_find(ctx, ctx["word"], ctx["builtin_funcs"], True, "function"))
    return result


def _table(ctx: dict[str, Any], schema: str | None, refs: list[tuple[str | None, str, str | None, bool]], local_names: Iterable[str], aliased: bool, view: bool) -> list[tuple[Completion, tuple[Any, ...]]]:
    word: str = ctx["word"]
    objects = _objects(ctx, ctx["V"] if view else ctx["T"], schema) + [(name, None) for name in local_names]
    if not schema and not word.startswith("pg_"):
        objects = [entry for entry in objects if not entry[0].startswith("pg_")]
    candidates = [_candidate(ctx, name, sch, None, aliased, refs, None) for name, sch in objects]
    return _find(ctx, word, candidates, False, "view" if view else "table")


def _keyword(ctx: dict[str, Any], last_token: str | None) -> list[tuple[Completion, tuple[Any, ...]]]:
    tree: dict[str, list[str]] = ctx["tree"]
    words = list(tree)
    if last_token is not None and tree.get(last_token):
        words = tree[last_token]
    casing: str = ctx["kwcase"].lower()
    if casing not in ("upper", "lower", "auto"):
        casing = "upper"
    word: str = ctx["word"]
    if casing == "auto":
        casing = "lower" if word and word[-1].islower() else "upper"
    return _find(ctx, word, [value.upper() if casing == "upper" else value.lower() for value in words], True, "keyword")


def _run(ctx: dict[str, Any], suggestion: Suggestion, request: CompletionRequest) -> list[tuple[Completion, tuple[Any, ...]]]:
    word: str = ctx["word"]
    if isinstance(suggestion, Suggestion_Column):
        return _column(ctx, suggestion)
    if isinstance(suggestion, Suggestion_Join):
        return _join(ctx, suggestion)
    if isinstance(suggestion, Suggestion_JoinCondition):
        return _join_condition(ctx, suggestion)
    if isinstance(suggestion, Suggestion_Function):
        return _function(ctx, _text_option(suggestion.schema), [_conv(table) for table in suggestion.table_refs], suggestion.usage, False)
    if isinstance(suggestion, Suggestion_Schema):
        names = list(ctx["T"])
        if not word.startswith("pg_"):
            names = [name for name in names if not name.startswith("pg_")]
        if suggestion.quoted:
            names = ["'" + _unescape(name) + "'" for name in names]
        return _find(ctx, word, names, False, "schema")
    if isinstance(suggestion, Suggestion_FromClauseItem):
        schema = _text_option(suggestion.schema)
        refs = [_conv(table) for table in suggestion.table_refs]
        aliased: bool = ctx["gen"]
        return (_table(ctx, schema, refs, (local.name for local in suggestion.local_tables), aliased, False)
                + _table(ctx, schema, refs, [], aliased, True)
                + _function(ctx, schema, refs, FunctionUsage_From(), aliased))
    if isinstance(suggestion, Suggestion_Table):
        return _table(ctx, _text_option(suggestion.schema), [_conv(table) for table in suggestion.table_refs], (local.name for local in suggestion.local_tables), False, False)
    if isinstance(suggestion, Suggestion_View):
        return _table(ctx, _text_option(suggestion.schema), [_conv(table) for table in suggestion.table_refs], [], False, True)
    if isinstance(suggestion, Suggestion_Alias):
        return _find(ctx, word, suggestion.aliases, False, "table alias")
    if isinstance(suggestion, Suggestion_Database):
        return _find(ctx, word, ctx["C"]["databases"], False, "database")
    if isinstance(suggestion, Suggestion_Keyword):
        return _keyword(ctx, _text_option(suggestion.last_token))
    if isinstance(suggestion, Suggestion_Special):
        commands = [(command.command, 0, command.description, (command.command,), 0, command.command) for command in request.special_commands]
        return _find(ctx, word, commands, True, None)
    if isinstance(suggestion, Suggestion_Datatype):
        schema = _text_option(suggestion.schema)
        candidates = [_candidate(ctx, name, sch, None, False, [], None) for name, sch in _objects(ctx, ctx["D"], schema)]
        result = _find(ctx, word, candidates, False, "datatype")
        if not schema:
            result.extend(_find(ctx, word, ctx["builtin_types"], True, "datatype"))
        return result
    if isinstance(suggestion, Suggestion_NamedQuery):
        return _find(ctx, word, request.named_queries, False, "named query")
    if isinstance(suggestion, Suggestion_TableFormat):
        return _find(ctx, word, request.table_formats, False, "table format")
    return []


def _fill_relations(ctx: dict[str, Any], objects: dict[str, dict[str, dict[str, list[Any]]]], rows: list[Any]) -> None:
    for schema, name, _columns in rows:
        escaped_schema = _escape(ctx, schema)
        if escaped_schema in objects:
            objects[escaped_schema][_escape(ctx, name)] = {}
    for schema, name, columns in rows:
        for column, datatype, has_default, default in columns:
            escaped = _escape(ctx, column)
            objects.setdefault(_escape(ctx, schema), {}).setdefault(_escape(ctx, name), {})[escaped] = [escaped, datatype, has_default, default, []]


def _complete(request: CompletionRequest) -> list[Completion]:
    tree, builtin_functions, builtin_types, reserved = _literals()
    all_keywords = [value for key, following in tree.items() for value in (key, *following)]
    raw_catalog = request.catalog.unwrap()
    raw_prevalence = request.prevalence.unwrap()
    if not isinstance(raw_catalog, dict) or not isinstance(raw_prevalence, dict):
        return []
    catalog = cast(dict[str, Any], raw_catalog)
    prevalence = cast(dict[str, Any], raw_prevalence)
    before = request.text[:request.cursor]
    word = Document(request.text, request.cursor).get_word_before_cursor(WORD=True)
    casemap = {name.lower(): name for name in catalog["casing"]}
    settings = request.settings
    ctx: dict[str, Any] = {
        "reserved": reserved,
        "funcset": set(builtin_functions),
        "casemap": casemap,
        "amap": settings.alias_map,
        "gen": settings.generate_aliases,
        "spf": settings.search_path_filter,
        "qc": settings.qualify_columns,
        "order": settings.asterisk_column_order,
        "kwcase": settings.keyword_casing,
        "kwcounts": prevalence["keywords"],
        "namecounts": prevalence["names"],
        "word": word,
        "tree": tree,
        "builtin_funcs": builtin_functions,
        "builtin_types": builtin_types,
        "C": catalog,
    }
    ctx["sp"] = [_escape(ctx, schema) for schema in catalog["search_path"]]
    tables: dict[str, dict[str, dict[str, list[Any]]]] = {}
    views: dict[str, dict[str, dict[str, list[Any]]]] = {}
    functions: dict[str, dict[str, list[tuple[Any, ...]]]] = {}
    datatypes: dict[str, dict[str, bool]] = {}
    for schema in catalog["schemata"]:
        escaped = _escape(ctx, schema)
        tables[escaped] = {}
        views[escaped] = {}
        functions[escaped] = {}
        datatypes[escaped] = {}
    _fill_relations(ctx, tables, catalog["tables"])
    _fill_relations(ctx, views, catalog["views"])
    for foreign_key in catalog["foreign_keys"]:
        escaped_key = tuple(_escape(ctx, name) for name in foreign_key)
        try:
            child = tables[escaped_key[3]][escaped_key[4]][escaped_key[5]]
            parent = tables[escaped_key[0]][escaped_key[1]][escaped_key[2]]
        except KeyError:
            continue
        child[4].append(escaped_key)
        parent[4].append(escaped_key)
    for schema, name in catalog["datatypes"]:
        escaped_schema = _escape(ctx, schema)
        if escaped_schema in datatypes:
            datatypes[escaped_schema][_escape(ctx, name)] = True
    for function in catalog["functions"]:
        escaped_schema = _escape(ctx, function[0])
        if escaped_schema in functions:
            functions[escaped_schema].setdefault(_escape(ctx, function[1]), []).append(function)
    ctx["T"] = tables
    ctx["V"] = views
    ctx["F"] = functions
    ctx["D"] = datatypes
    if not request.smart_completion:
        words = set(all_keywords) | set(builtin_functions)
        words.update(_escape(ctx, schema) for schema in catalog["schemata"])
        for kind in ("tables", "views"):
            for schema, name, columns in catalog[kind]:
                words.add(_escape(ctx, schema))
                words.add(_escape(ctx, name))
                words.update(_escape(ctx, column[0]) for column in columns)
        for schema, name in catalog["datatypes"]:
            words.add(_escape(ctx, schema))
            words.add(_escape(ctx, name))
        for function in catalog["functions"]:
            words.add(_escape(ctx, function[0]))
            words.add(_escape(ctx, function[1]))
        return sorted((completion for completion, _priority in _find(ctx, word, words, True, None)), key=lambda completion: completion.text)
    pairs: list[tuple[Completion, tuple[Any, ...]]] = []
    for suggestion in suggest_sql_completions(request.text, before):
        pairs.extend(_run(ctx, suggestion, request))
    return [completion for completion, _priority in sorted(pairs, key=lambda pair: pair[1], reverse=True)]


def complete_sql_text(request: CompletionRequest) -> CompletionList:
    try:
        completions = _complete(request)
    except Exception:
        completions = []
    return Opaque(tag="pgcli.completions", value=completions)
