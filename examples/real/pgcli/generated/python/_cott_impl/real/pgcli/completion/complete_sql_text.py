import json
import math
import re
from typing import Any, Final, cast

from cott_runtime import Opaque, Some
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document

from real.pgcli.completion import suggest_sql_completions
from real.pgcli.completion_types import CompletionList, CompletionRequest, FunctionUsage_Call, FunctionUsage_From, FunctionUsage_Signature, FunctionUsage_Special, PGLITERALS_JSON, Suggestion_Alias, Suggestion_Column, Suggestion_Database, Suggestion_Datatype, Suggestion_FromClauseItem, Suggestion_Function, Suggestion_Join, Suggestion_JoinCondition, Suggestion_Keyword, Suggestion_NamedQuery, Suggestion_Schema, Suggestion_Special, Suggestion_Table, Suggestion_TableFormat, Suggestion_View

_MOST: Final[str] = "([^\\.():,\\s]+)$"
_TYPE_NAMES: Final[str] = "keyword|function|view|table|datatype|database|schema|column|table alias|join|name join|fk join|table format"


def _opt(value: Any) -> Any:
    if isinstance(value, Some):
        return cast(Some[Any], value).value
    return None


def _last_word(text: str, pattern: str) -> str:
    if not text or text[-1].isspace():
        return ""
    m = re.search(pattern, text)
    return m.group(0) if m else ""


def _escape(ctx: dict[str, Any], name: str) -> str:
    if name and (not re.match("^[_a-z][_a-z0-9\\$]*$", name) or name.upper() in ctx["reserved"] or name.upper() in ctx["funcset"]):
        return '"' + name + '"'
    return name


def _unescape(name: str) -> str:
    if name and name[0] == '"' and name[-1] == '"':
        return name[1:-1]
    return name


def _case(ctx: dict[str, Any], word: str) -> str:
    return cast(str, ctx["casemap"].get(word, word))


def _alias_of(tbl: str, amap: dict[str, str]) -> str:
    if tbl in amap:
        return amap[tbl]
    upper = "".join(c for c in tbl if c.isupper())
    if upper:
        return upper
    return "".join(c for i, c in enumerate(tbl) if c != "_" and (i == 0 or tbl[i - 1] == "_"))


def _ref(t: tuple[Any, ...]) -> str:
    name = cast(str, t[1])
    alias = t[2]
    if alias:
        return cast(str, alias)
    if name.islower() or name.startswith('"'):
        return name
    return '"' + name + '"'


def _norm(r: str) -> str:
    return r if r.startswith('"') else '"' + r.lower() + '"'


def _conv(t: Any) -> tuple[Any, ...]:
    return (_opt(t.schema), str(t.name), _opt(t.alias_name), bool(t.is_function))


def _parse_defaults(text: str) -> list[str]:
    if not text:
        return []
    result: list[str] = []
    current = ""
    quote: str | None = None
    for ch in text:
        if current == "" and ch == " ":
            continue
        if ch in "\"'":
            if quote is not None and ch == quote:
                quote = None
            elif quote is None:
                quote = ch
            current += ch
        elif ch == "," and quote is None:
            result.append(current)
            current = ""
        else:
            current += ch
    result.append(current)
    return result


def _arglist(f: Any, usage: str, casemap: dict[str, str]) -> str:
    names: list[str] = f[2] if f[2] else []
    types: list[str] = f[3] if f[3] else []
    modes: list[str] = f[4] if f[4] else []
    args: list[tuple[str, str]] = []
    if names:
        ms = modes if modes else ["i"] * len(names)
        ts = types if types else ["None"] * len(names)
        args = [(n, t) for n, t, m in zip(names, ts, ms) if m in ("i", "b", "v")]
    n = len(args)
    defaults = _parse_defaults(f[10] if f[10] is not None else "")
    d = len(defaults)
    if usage == "call":
        if n < 2 or "v" in modes:
            return "()"
        width = max(len(a[0]) for a in args) if n > 2 else 0
        parts: list[str] = []
        for k, arg in enumerate(args):
            dflt = re.sub("::[\\w\\.]+(\\[\\])?$", "", defaults[k - n + d]) if k + d >= n else ""
            parts.append(casemap.get(arg[0], arg[0]).ljust(width) + " := " + dflt)
        if n > 2:
            return "(" + ",".join("\n    " + p for p in parts if p) + "\n)"
        return "(" + ", ".join(p for p in parts if p) + ")"
    if usage == "display":
        parts = [casemap.get(a[0], a[0]) for a in args]
    else:
        parts = [casemap.get(a[0], a[0]) + " " + a[1] for a in args]
    return "(" + ", ".join(p for p in parts if p) + ")"


def _match(s: str, text: str, pat: str, strict: bool) -> tuple[Any, ...] | None:
    low = s.lower()
    if strict:
        return (-math.inf, 0) if low.startswith(text) else None
    if low[: len(text) + 1] in (text, text + " "):
        return (math.inf, -1)
    m = re.search(pat, _unescape(low))
    if m:
        return (-len(m.group()), -m.start())
    return None


def _find(ctx: dict[str, Any], text: str, collection: Any, strict: bool, meta: str | None) -> list[tuple[Any, Any]]:
    if not collection:
        return []
    type_names = _TYPE_NAMES.split("|")
    type_priority = type_names.index(meta) if meta in type_names else -1
    text = _last_word(text, _MOST).lower()
    text_len = len(text)
    if text.startswith('"'):
        text = text[1:]
    pat = "(" + ".*?".join(re.escape(ch) for ch in text) + ")"
    counts = cast(dict[str, int], ctx["kwcounts"] if strict else ctx["namecounts"])
    result: list[tuple[Any, Any]] = []
    for item in collection:
        if isinstance(item, str):
            comp = item
            dmeta = meta
            prio = 0
            prio2 = 0
            display = item
            sort_key = _match(item, text, pat, strict)
        else:
            comp, prio, cmeta, synonyms, prio2, display = item
            dmeta = cmeta if cmeta is not None else meta
            keys = [k for k in (_match(x, text, pat, strict) for x in synonyms) if k is not None]
            sort_key = max(keys) if keys else None
        if sort_key is None:
            continue
        if dmeta and len(dmeta) > 50:
            dmeta = dmeta[:47] + "..."
        lexical = tuple(0 if ch in " _" else -ord(ch) for ch in _unescape(comp.lower())) + (1,) + tuple(comp)
        cased = _case(ctx, comp)
        shown = _case(ctx, display)
        count = counts.get(cased, 0)
        result.append((Completion(cased, start_position=-text_len, display=shown, display_meta=dmeta), (sort_key, type_priority, prio, count, prio2, lexical)))
    return result


def _schemas_of(ctx: dict[str, Any], m: dict[str, Any], schema: str | None) -> list[str]:
    if schema:
        s = _escape(ctx, schema)
        return [s] if s in m else []
    if ctx["spf"]:
        return list(ctx["sp"])
    return list(m.keys())


def _shown(ctx: dict[str, Any], sch: str, schema: str | None) -> str | None:
    return None if schema or sch in ctx["sp"] else sch


def _objects(ctx: dict[str, Any], m: dict[str, Any], schema: str | None) -> list[tuple[str, str | None]]:
    return [(name, _shown(ctx, sch, schema)) for sch in _schemas_of(ctx, m, schema) if sch in m for name in m[sch]]


def _alias_for(ctx: dict[str, Any], tbl: str, refs: list[tuple[Any, ...]]) -> str:
    tbl = _case(ctx, tbl)
    taken = {_norm(_ref(t)) for t in refs}
    if ctx["gen"]:
        tbl = _alias_of(_unescape(tbl), ctx["amap"])
    if _norm(tbl) not in taken:
        return tbl
    i = 2
    while True:
        alias = '"' + tbl[1:-1] + str(i) + '"' if tbl.startswith('"') else tbl + str(i)
        if _norm(alias) not in taken:
            return alias
        i += 1


def _cand(ctx: dict[str, Any], name: str, schema: str | None, f: Any, aliased: bool, refs: list[tuple[Any, ...]], arg: str | None) -> tuple[Any, ...]:
    c = _case(ctx, name)
    synonyms = (c, _alias_of(c, ctx["amap"]))
    tail = " " + _alias_for(ctx, c, refs) if aliased else ""
    head = _case(ctx, schema) + "." if schema else ""
    casemap = cast(dict[str, str], ctx["casemap"])
    if arg == "call":
        suffix = _arglist(f, "call", casemap)
        dsuffix = _arglist(f, "display", casemap)
    elif arg == "signature":
        suffix = _arglist(f, "signature", casemap)
        dsuffix = suffix
    else:
        suffix = ""
        dsuffix = ""
    return (head + c + suffix + tail, 0, None, synonyms, 0 if schema else 1, head + c + dsuffix + tail)


def _fields(f: Any) -> list[list[Any]]:
    rt = cast(str, f[5]).strip()
    if rt.lower() == "void":
        return []
    modes: list[str] = f[4] if f[4] else []
    if not modes:
        return [[f[1], rt, False, None, []]]
    names: list[str] = f[2] if f[2] else []
    types: list[str] = f[3] if f[3] else ["None"] * len(modes)
    return [[n, t, False, None, []] for n, t, m in zip(names, types, modes) if m in ("o", "b", "t")]


def _scoped(ctx: dict[str, Any], refs: list[tuple[Any, ...]], local_tables: list[tuple[str, list[str]]]) -> dict[tuple[Any, ...], list[Any]]:
    cols: dict[tuple[Any, ...], list[Any]] = {}
    ctes: dict[str, list[str]] = {}
    for name, columns in local_tables:
        ctes[_norm(name)] = columns
    used: set[str] = set()
    for t in refs:
        schema, name, alias, isf = t
        if schema is None and _norm(name) in ctes:
            nk = _norm(name)
            recs: list[list[Any]] = [] if nk in used else [[c, None, False, None, []] for c in ctes[nk]]
            used.add(nk)
            cols.setdefault((None, name, "CTE", alias == "functions"), []).extend(recs)
            continue
        for sch in [schema] if schema else ctx["sp"]:
            rel = _escape(ctx, name)
            s = _escape(ctx, sch)
            if isf:
                for f in ctx["F"].get(s, {}).get(rel, []):
                    cols.setdefault((s, rel, alias, True), []).extend(_fields(f))
            else:
                for m in (ctx["T"], ctx["V"]):
                    found = m.get(s, {}).get(rel)
                    if found:
                        cols.setdefault((s, rel, alias, False), []).extend(found.values())
                        break
    return cols


def _qualify(ctx: dict[str, Any], col: str, r: str, qualify: bool) -> str:
    return r + "." + _case(ctx, col) if qualify else _case(ctx, col)


def _keep_insert(col: list[Any]) -> bool:
    if not col[2]:
        return True
    return not (re.match("^now\\(\\)$", col[3]) or re.match("^nextval\\(", col[3]))


def _m_column(ctx: dict[str, Any], s: Any) -> list[tuple[Any, Any]]:
    refs = [_conv(t) for t in s.table_refs]
    local_tables = [(str(c.name), [str(x) for x in c.columns]) for c in s.local_tables]
    word = cast(str, ctx["word"])
    qualify = False
    if s.qualifiable:
        qc = ctx["qc"]
        if qc == "always":
            qualify = True
        elif qc == "never":
            qualify = False
        elif qc == "if_more_than_one_table":
            qualify = len(refs) > 1
        else:
            return []
    cols = _scoped(ctx, refs, local_tables)
    if s.require_last_table:
        if not refs:
            return []
        last = _ref(refs[-1])
        other = {c[0] for k, cs in cols.items() if _ref(k) != last for c in cs}
        cols = {k: [c for c in cs if c[0] in other] for k, cs in cols.items() if _ref(k) == last}
    lastword = _last_word(word, _MOST)
    if lastword == "*":
        if _opt(s.context) == "insert":
            cols = {k: [c for c in cs if _keep_insert(c)] for k, cs in cols.items()}
        if ctx["order"] == "alphabetic":
            cols = {k: sorted(cs, key=lambda c: cast(str, c[0])) for k, cs in cols.items()}
        if lastword != word and len(refs) == 1 and word[-len(lastword) - 1] == ".":
            sep = ", " + word[:-1]
            text = sep.join(_case(ctx, _qualify(ctx, c[0], _ref(k), qualify)) for k, cs in cols.items() for c in cs)
        else:
            text = ", ".join(_qualify(ctx, c[0], _ref(k), qualify) for k, cs in cols.items() for c in cs)
        return [(Completion(text, start_position=-1, display="*", display_meta="columns"), (1, 1, 1))]
    cands: list[tuple[Any, ...]] = []
    for k, cs in cols.items():
        for c in cs:
            q = _qualify(ctx, c[0], _ref(k), qualify)
            cands.append((q, 0, "column", (c[0], _alias_of(_case(ctx, c[0]), ctx["amap"])), 0, q))
    return _find(ctx, word, cands, False, "column")


def _m_join(ctx: dict[str, Any], s: Any) -> list[tuple[Any, Any]]:
    refs = [_conv(t) for t in s.table_refs]
    schema = _opt(s.schema)
    cols = _scoped(ctx, refs, [])
    qualified = {_norm(_ref(t)): t[0] for t in refs}
    order = {_norm(_ref(t)): i for i, t in enumerate(refs)}
    taken = set(qualified)
    keys = list(cols)
    others = {(k[0], k[1]) for k in keys[:-1]}
    cands: list[tuple[Any, ...]] = []
    for k, cs in cols.items():
        for r in cs:
            for fk in r[4]:
                right = (k[0], k[1], r[0])
                child = (fk[3], fk[4], fk[5])
                parent = (fk[0], fk[1], fk[2])
                left = child if parent == right else parent
                if schema and left[0] != schema:
                    continue
                lt = _case(ctx, left[1])
                lc = _case(ctx, left[2])
                rr = _ref(k)
                rc = _case(ctx, right[2])
                if ctx["gen"] or _norm(left[1]) in taken:
                    a = _alias_for(ctx, left[1], refs)
                    join = lt + " " + a + " ON " + a + "." + lc + " = " + rr + "." + rc
                else:
                    join = lt + " ON " + lt + "." + lc + " = " + rr + "." + rc
                al = _alias_of(lt, ctx["amap"])
                synonyms = (join, al + " ON " + al + "." + lc + " = " + rr + "." + rc)
                if not schema and ((qualified[_norm(rr)] and left[0] == right[0]) or left[0] not in (right[0], "public")):
                    join = left[0] + "." + join
                prio = order[_norm(rr)] * 2 + (0 if (left[0], left[1]) in others else 1)
                cands.append((join, prio, "join", synonyms, 0, join))
    return _find(ctx, ctx["word"], cands, False, "join")


def _add_cond(ctx: dict[str, Any], conds: list[tuple[Any, ...]], found: set[str], prefix: str, lcol: str, rcol: str, rref: str, prio: int, meta: str, order: dict[str, int]) -> None:
    cond = prefix + _case(ctx, lcol) + " = " + rref + "." + _case(ctx, rcol)
    if cond in found:
        return
    found.add(cond)
    conds.append((cond, prio + order[rref], meta, (cond,), 0, cond))


def _m_join_condition(ctx: dict[str, Any], s: Any) -> list[tuple[Any, Any]]:
    refs = [_conv(t) for t in s.table_refs]
    cols = _scoped(ctx, refs, [])
    parent = _opt(s.parent)
    if not refs:
        return []
    lref = _ref(_conv(parent)) if parent is not None else _ref(refs[-1])
    matches = [(k, cs) for k, cs in cols.items() if _ref(k) == lref]
    if not matches:
        return []
    big_l, lcols = matches[-1]
    prefix = "" if parent is not None else _ref(big_l) + "."
    order = {_ref(t): i for i, t in enumerate(refs)}
    conds: list[tuple[Any, ...]] = []
    found: set[str] = set()
    coldict: dict[tuple[Any, ...], list[tuple[Any, ...]]] = {}
    for k, cs in cols.items():
        if _ref(k) != lref:
            for c in cs:
                coldict.setdefault((k[0], k[1], c[0]), []).append(k)
    for c in lcols:
        for fk in c[4]:
            left = (big_l[0], big_l[1], c[0])
            child = (fk[3], fk[4], fk[5])
            par = (fk[0], fk[1], fk[2])
            if left == child:
                lft, rgt = child, par
            else:
                lft, rgt = par, child
            for kk in coldict.get(rgt, []):
                _add_cond(ctx, conds, found, prefix, lft[2], rgt[2], _ref(kk), 2000, "fk join", order)
    col_table: dict[tuple[Any, ...], list[tuple[Any, ...]]] = {}
    for k, cs in cols.items():
        for c in cs:
            col_table.setdefault((c[0], c[1]), []).append(k)
    for c in lcols:
        for kk in col_table.get((c[0], c[1]), []):
            if _ref(kk) != _ref(big_l):
                prio = 1000 if c[1] in ("integer", "bigint", "smallint") else 0
                _add_cond(ctx, conds, found, prefix, c[0], c[0], _ref(kk), prio, "name join", order)
    return _find(ctx, ctx["word"], conds, False, "join")


def _m_function(ctx: dict[str, Any], schema: str | None, refs: list[tuple[Any, ...]], usage: Any, aliased: bool) -> list[tuple[Any, Any]]:
    is_from = isinstance(usage, FunctionUsage_From)
    if not is_from:
        aliased = False
    if isinstance(usage, FunctionUsage_Signature):
        arg: str | None = "signature"
    elif isinstance(usage, FunctionUsage_Special):
        arg = None
    else:
        arg = "call"
    funcs = cast(dict[str, dict[str, list[Any]]], ctx["F"])
    seen: set[tuple[Any, ...]] = set()
    cands: list[tuple[Any, ...]] = []
    for sch in _schemas_of(ctx, funcs, schema):
        if sch not in funcs:
            continue
        for name, fs in funcs[sch].items():
            for f in fs:
                if is_from:
                    keep = not f[6] and not f[7] and not f[9] and (f[0] == "public" or f[0] in ctx["sp"] or f[0] == schema)
                else:
                    keep = not f[9] and (f[0] == "public" or f[0] == schema)
                if not keep:
                    continue
                cand = _cand(ctx, name, _shown(ctx, sch, schema), f, aliased, refs, arg)
                if cand not in seen:
                    seen.add(cand)
                    cands.append(cand)
    result = _find(ctx, ctx["word"], cands, False, "function")
    if not schema and isinstance(usage, FunctionUsage_Call):
        result.extend(_find(ctx, ctx["word"], ctx["builtin_funcs"], True, "function"))
    return result


def _m_table(ctx: dict[str, Any], schema: str | None, refs: list[tuple[Any, ...]], local_names: list[str], aliased: bool, view: bool) -> list[tuple[Any, Any]]:
    word = cast(str, ctx["word"])
    objs = _objects(ctx, ctx["V"] if view else ctx["T"], schema) + [(n, None) for n in local_names]
    if not schema and not word.startswith("pg_"):
        objs = [o for o in objs if not o[0].startswith("pg_")]
    cands = [_cand(ctx, n, sh, None, aliased, refs, None) for n, sh in objs]
    return _find(ctx, word, cands, False, "view" if view else "table")


def _m_keyword(ctx: dict[str, Any], last_token: str | None) -> list[tuple[Any, Any]]:
    tree = cast(dict[str, list[str]], ctx["tree"])
    word = cast(str, ctx["word"])
    words = list(tree.keys())
    if last_token is not None:
        nxt = tree.get(last_token)
        if nxt:
            words = list(nxt)
    casing = str(ctx["kwcase"]).lower()
    if casing not in ("upper", "lower", "auto"):
        casing = "upper"
    if casing == "auto":
        casing = "lower" if word and word[-1].islower() else "upper"
    words = [w.upper() if casing == "upper" else w.lower() for w in words]
    return _find(ctx, word, words, True, "keyword")


def _run(ctx: dict[str, Any], s: Any, request: CompletionRequest) -> list[tuple[Any, Any]]:
    word = cast(str, ctx["word"])
    if isinstance(s, Suggestion_Column):
        return _m_column(ctx, s)
    if isinstance(s, Suggestion_Join):
        return _m_join(ctx, s)
    if isinstance(s, Suggestion_JoinCondition):
        return _m_join_condition(ctx, s)
    if isinstance(s, Suggestion_Function):
        return _m_function(ctx, _opt(s.schema), [_conv(t) for t in s.table_refs], s.usage, False)
    if isinstance(s, Suggestion_Schema):
        names = list(ctx["T"].keys())
        if not word.startswith("pg_"):
            names = [n for n in names if not n.startswith("pg_")]
        if s.quoted:
            names = ["'" + _unescape(n) + "'" for n in names]
        return _find(ctx, word, names, False, "schema")
    if isinstance(s, Suggestion_FromClauseItem):
        schema = _opt(s.schema)
        refs = [_conv(t) for t in s.table_refs]
        gen = bool(ctx["gen"])
        locals_ = [str(c.name) for c in s.local_tables]
        return _m_table(ctx, schema, refs, locals_, gen, False) + _m_table(ctx, schema, refs, [], gen, True) + _m_function(ctx, schema, refs, FunctionUsage_From(), gen)
    if isinstance(s, Suggestion_Table):
        return _m_table(ctx, _opt(s.schema), [_conv(t) for t in s.table_refs], [str(c.name) for c in s.local_tables], False, False)
    if isinstance(s, Suggestion_View):
        return _m_table(ctx, _opt(s.schema), [_conv(t) for t in s.table_refs], [], False, True)
    if isinstance(s, Suggestion_Alias):
        return _find(ctx, word, [str(a) for a in s.aliases], False, "table alias")
    if isinstance(s, Suggestion_Database):
        return _find(ctx, word, ctx["C"]["databases"], False, "database")
    if isinstance(s, Suggestion_Keyword):
        return _m_keyword(ctx, _opt(s.last_token))
    if isinstance(s, Suggestion_Special):
        cmds = [(str(c.command), 0, str(c.description), (str(c.command),), 0, str(c.command)) for c in request.special_commands]
        return _find(ctx, word, cmds, True, None)
    if isinstance(s, Suggestion_Datatype):
        schema = _opt(s.schema)
        cands = [_cand(ctx, n, sh, None, False, [], None) for n, sh in _objects(ctx, ctx["D"], schema)]
        result = _find(ctx, word, cands, False, "datatype")
        if not schema:
            result.extend(_find(ctx, word, ctx["builtin_types"], True, "datatype"))
        return result
    if isinstance(s, Suggestion_NamedQuery):
        return _find(ctx, word, [str(n) for n in request.named_queries], False, "named query")
    if isinstance(s, Suggestion_TableFormat):
        return _find(ctx, word, [str(n) for n in request.table_formats], False, "table format")
    return []


def _fill_relations(ctx: dict[str, Any], m: dict[str, dict[str, dict[str, Any]]], rows: list[Any]) -> None:
    for schema, name, _cols in rows:
        s = _escape(ctx, schema)
        if s in m:
            m[s][_escape(ctx, name)] = {}
    for schema, name, cols in rows:
        for col, datatype, has_default, default in cols:
            ec = _escape(ctx, col)
            m.setdefault(_escape(ctx, schema), {}).setdefault(_escape(ctx, name), {})[ec] = [ec, datatype, has_default, default, []]


def _complete(request: CompletionRequest) -> list[Any]:
    literals = cast(dict[str, Any], json.loads(PGLITERALS_JSON))
    tree = cast(dict[str, list[str]], literals["keywords"])
    builtin_funcs = cast(list[str], literals["functions"])
    builtin_types = cast(list[str], literals["datatypes"])
    all_keywords: list[str] = []
    for key, follow in tree.items():
        all_keywords.append(key)
        all_keywords.extend(follow)
    c = cast(dict[str, Any], request.catalog.unwrap())
    p = cast(dict[str, Any], request.prevalence.unwrap())
    settings = request.settings
    before = request.text[: request.cursor]
    word = Document(request.text, request.cursor).get_word_before_cursor(WORD=True)
    casemap: dict[str, str] = {}
    for w in c["casing"]:
        casemap[w.lower()] = w
    amap: dict[str, str] = {str(k): str(v) for k, v in settings.alias_map.items()}
    ctx: dict[str, Any] = {
        "reserved": set(cast(list[str], literals["reserved"])),
        "funcset": set(builtin_funcs),
        "casemap": casemap,
        "amap": amap,
        "gen": settings.generate_aliases,
        "spf": settings.search_path_filter,
        "qc": settings.qualify_columns,
        "order": settings.asterisk_column_order,
        "kwcase": settings.keyword_casing,
        "kwcounts": p["keywords"],
        "namecounts": p["names"],
        "word": word,
        "tree": tree,
        "builtin_funcs": builtin_funcs,
        "builtin_types": builtin_types,
        "C": c,
    }
    ctx["sp"] = [_escape(ctx, s) for s in c["search_path"]]
    tables: dict[str, dict[str, dict[str, Any]]] = {}
    views: dict[str, dict[str, dict[str, Any]]] = {}
    funcs: dict[str, dict[str, list[Any]]] = {}
    dtypes: dict[str, dict[str, Any]] = {}
    for s in c["schemata"]:
        es = _escape(ctx, s)
        tables[es] = {}
        views[es] = {}
        funcs[es] = {}
        dtypes[es] = {}
    _fill_relations(ctx, tables, c["tables"])
    _fill_relations(ctx, views, c["views"])
    for fk in c["foreign_keys"]:
        e = tuple(_escape(ctx, x) for x in fk)
        try:
            child = tables[e[3]][e[4]][e[5]]
            parent = tables[e[0]][e[1]][e[2]]
        except KeyError:
            continue
        child[4].append(e)
        parent[4].append(e)
    for schema, name in c["datatypes"]:
        es = _escape(ctx, schema)
        if es in dtypes:
            dtypes[es][_escape(ctx, name)] = True
    for f in c["functions"]:
        es = _escape(ctx, f[0])
        if es in funcs:
            funcs[es].setdefault(_escape(ctx, f[1]), []).append(f)
    ctx["T"] = tables
    ctx["V"] = views
    ctx["F"] = funcs
    ctx["D"] = dtypes
    if not request.smart_completion:
        words: set[str] = set(all_keywords) | set(builtin_funcs)
        for m in (tables, views):
            for sch, rels in m.items():
                words.add(sch)
                for rel, cols in rels.items():
                    words.add(rel)
                    words.update(cols.keys())
        for sch, names in funcs.items():
            words.add(sch)
            words.update(names.keys())
        for sch, names in dtypes.items():
            words.add(sch)
            words.update(names.keys())
        found = [pair[0] for pair in _find(ctx, word, words, True, None)]
        return sorted(found, key=lambda comp: cast(Completion, comp).text)
    pairs: list[tuple[Any, Any]] = []
    for suggestion in suggest_sql_completions(request.text, before):
        pairs.extend(_run(ctx, suggestion, request))
    ordered = sorted(pairs, key=lambda pair: pair[1], reverse=True)
    return [pair[0] for pair in ordered]


def complete_sql_text(request: CompletionRequest) -> CompletionList:
    try:
        completions = _complete(request)
    except Exception:
        completions = []
    return Opaque(tag="pgcli.completions", value=completions)
