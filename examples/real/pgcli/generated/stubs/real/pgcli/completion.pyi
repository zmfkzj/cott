from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.pgcli.completion_types import AliasMapError as AliasMapError, AliasMapError_InvalidMapFile as AliasMapError_InvalidMapFile, ArgumentListUsage as ArgumentListUsage, ArgumentListUsage_Call as ArgumentListUsage_Call, ArgumentListUsage_CallDisplay as ArgumentListUsage_CallDisplay, ArgumentListUsage_Signature as ArgumentListUsage_Signature, CASING_QUERY as CASING_QUERY, COLUMNS_QUERY as COLUMNS_QUERY, COLUMNS_QUERY_LEGACY as COLUMNS_QUERY_LEGACY, ColumnMetadata as ColumnMetadata, CompleterSettings as CompleterSettings, CompletionCatalog as CompletionCatalog, CompletionItem as CompletionItem, CompletionList as CompletionList, CompletionMetadata as CompletionMetadata, CompletionRequest as CompletionRequest, DATABASES_QUERY as DATABASES_QUERY, DATATYPES_QUERY as DATATYPES_QUERY, DATATYPES_QUERY_LEGACY as DATATYPES_QUERY_LEGACY, DatatypeMetadata as DatatypeMetadata, FOREIGN_KEYS_QUERY as FOREIGN_KEYS_QUERY, FUNCTIONS_QUERY_LEGACY as FUNCTIONS_QUERY_LEGACY, FUNCTIONS_QUERY_V11 as FUNCTIONS_QUERY_V11, FUNCTIONS_QUERY_V84 as FUNCTIONS_QUERY_V84, FUNCTIONS_QUERY_V9 as FUNCTIONS_QUERY_V9, ForeignKeyMetadata as ForeignKeyMetadata, FunctionMetadata as FunctionMetadata, FunctionUsage as FunctionUsage, FunctionUsage_Call as FunctionUsage_Call, FunctionUsage_From as FunctionUsage_From, FunctionUsage_Signature as FunctionUsage_Signature, FunctionUsage_Special as FunctionUsage_Special, MetadataRefreshError as MetadataRefreshError, MetadataRefreshError_CasingFileFailed as MetadataRefreshError_CasingFileFailed, MetadataRefreshError_QueryFailed as MetadataRefreshError_QueryFailed, MetadataRefreshError_VirtualDatabase as MetadataRefreshError_VirtualDatabase, MetadataRefreshRequest as MetadataRefreshRequest, PGLITERALS_JSON as PGLITERALS_JSON, Prevalence as Prevalence, PrevalenceHandle as PrevalenceHandle, RELATIONS_QUERY as RELATIONS_QUERY, RelationMetadata as RelationMetadata, SCHEMATA_QUERY as SCHEMATA_QUERY, SEARCH_PATH_FALLBACK_QUERY as SEARCH_PATH_FALLBACK_QUERY, SEARCH_PATH_QUERY as SEARCH_PATH_QUERY, SpecialCommandInfo as SpecialCommandInfo, Suggestion as Suggestion, Suggestion_Alias as Suggestion_Alias, Suggestion_Column as Suggestion_Column, Suggestion_Database as Suggestion_Database, Suggestion_Datatype as Suggestion_Datatype, Suggestion_FromClauseItem as Suggestion_FromClauseItem, Suggestion_Function as Suggestion_Function, Suggestion_Join as Suggestion_Join, Suggestion_JoinCondition as Suggestion_JoinCondition, Suggestion_Keyword as Suggestion_Keyword, Suggestion_NamedQuery as Suggestion_NamedQuery, Suggestion_Path as Suggestion_Path, Suggestion_Schema as Suggestion_Schema, Suggestion_Special as Suggestion_Special, Suggestion_Table as Suggestion_Table, Suggestion_TableFormat as Suggestion_TableFormat, Suggestion_View as Suggestion_View
from real.pgcli.connection_types import Executor
from real.pgcli.parseutils_types import CteTable, TableReference
"""Upstream PGCompleter.escape_name: quote a catalog name for insertion into
SQL. Return '"' + name + '"' when name is nonempty and at least one holds:
re.match(r"^[_a-z][_a-z0-9\\$]*$", name) fails (Python re semantics, so a
single trailing newline still matches); name.upper() is one of the
"reserved" words of PGLITERALS_JSON; name.upper() is one of its
"functions" names. Otherwise return name unchanged. Examples: "users" and
"custom_fun" stay unchanged; "Users" gives '"Users"', "select" gives
'"select"' (reserved), "count" gives '"count"' (built-in function) and
"a b" gives '"a b"'."""
def escape_identifier_name(name: str) -> str: ...

"""Upstream pgcompleter.generate_alias. When alias_map contains table_name as
a key, return its value. Otherwise return the upper-case characters of
table_name (per character Python str.isupper) in order; when there are
none, return the characters c at positions i where c is not "_" and
either i == 0 or table_name[i - 1] == "_". Examples: "users" gives "u",
"Users" gives "U", '"Users"' gives "U", "user_emails" gives "ue",
"set_returning_func" gives "srf", "_custom_fun" gives "cf" and
"OrderItems" gives "OI"."""
def generate_table_alias(table_name: str, alias_map: FrozenMap[str, str]) -> str: ...

"""Upstream PGCompleter.case with the casing words of the catalog
(catalog.value["casing"], see CompletionCatalog): build the map from
w.lower() to w for every casing word w in order (a later word with the
same lower-cased form replaces an earlier one) and return the entry whose
key equals word exactly, or word unchanged when there is none. Only a word
that is already lower case can match. Example: with casing ["Users",
"ID"], "users" gives "Users", "id" gives "ID" and "Id" stays "Id"."""
def apply_identifier_casing(catalog: Opaque[Literal["pgcli.completion-catalog"]], word: str) -> str: ...

"""Upstream PGCompleter._arg_list with the default argument styles (pgcli never
changes them): the parenthesized argument list appended to a function
name. case(w) is the rule of apply_identifier_casing with the given casing
words: {c.lower(): c for c in casing}.get(w, w).

Input arguments (upstream FunctionMetadata.args): none when
function.arg_names is Nothing or empty. Otherwise names =
function.arg_names; modes = function.arg_modes when present and nonempty,
else "i" for every name; types = function.arg_types when present and
nonempty, else the text "None" for every argument. Walk names, types and
modes together (stopping at the shortest) and keep the (name, type)
pairs whose mode is "i", "b" or "v"; let n be their count. defaults =
real.pgcli.parseutils.parse_function_defaults(function.arg_defaults, ""
when Nothing) and d its length; kept argument k (0-based) has a default
when k + d >= n, namely defaults[k - n + d].

Formatting per usage, where an argument that formats to "" is skipped:
- Call: "()" when n < 2 or any mode of function.arg_modes is "v".
  Otherwise each argument is NAME + " := " + DEFAULT, where DEFAULT is ""
  without a default and otherwise the default text with one trailing
  type cast removed (re.sub(r"::[\\w\\.]+(\\[\\])?$", "", text)). When n > 2
  the list is multiline: NAME is case(name) left-justified with spaces to
  the length of the longest kept raw name, and the result is "(" +
  ",".join("\\n    " + argument ...) + "\\n)". When n == 2, NAME is
  case(name) and the result is "(" + ", ".join(arguments) + ")".
- CallDisplay: "(" + ", ".join(case(name) ...) + ")".
- Signature: "(" + ", ".join(case(name) + " " + type ...) + ")".
Examples: arguments x, y of type integer with modes b, b give "(x := , y
:= )" for Call, "(x, y)" for CallDisplay and "(x integer, y integer)" for
Signature; no arguments give "()" in every usage."""
def function_argument_list(function: FunctionMetadata, usage: ArgumentListUsage, casing: CottList[str]) -> str: ...

"""Build a CompletionCatalog from Cott metadata: Opaque(tag=
"pgcli.completion-catalog", value=D) with D laid out as documented on
CompletionCatalog: "schemata", "databases", "search_path" and "casing"
are lists of the same texts; "tables" and "views" hold (r.schema, r.name,
[(c.name, c.datatype, c.has_default, c.default value or None) for each
column]) per relation; "functions" holds the 11 FunctionMetadata fields
per function with Some(list) as a list (empty lists kept) and Nothing as
None; "datatypes" holds (schema, name); "foreign_keys" holds the six
ForeignKeyMetadata fields in order. Every list keeps the input order."""
def completion_catalog_from(metadata: CompletionMetadata) -> Opaque[Literal["pgcli.completion-catalog"]]: ...

"""A new CompletionCatalog whose dict is a shallow copy of catalog.value with
only "search_path" replaced by list(search_path) in order."""
def catalog_with_search_path(catalog: Opaque[Literal["pgcli.completion-catalog"]], search_path: CottList[str]) -> Opaque[Literal["pgcli.completion-catalog"]]: ...

"""A CompletionCatalog with no metadata: every key documented on
CompletionCatalog maps to a new empty list (the state before the first
refresh completes)."""
def empty_completion_catalog() -> Opaque[Literal["pgcli.completion-catalog"]]: ...

"""A new PrevalenceHandle whose dict is {"keywords": dict(keyword_counts),
"names": dict(name_counts)} (plain int values). An empty pair of maps is
the state of a new upstream PrevalenceCounter."""
def prevalence_from(keyword_counts: FrozenMap[str, U64], name_counts: FrozenMap[str, U64]) -> Opaque[Literal["pgcli.prevalence"]]: ...

"""The counts held by prevalence as a Prevalence value: keyword_counts from
prevalence.value["keywords"] and name_counts from
prevalence.value["names"], same keys and counts (for inspection of small
counters)."""
def prevalence_counts(prevalence: Opaque[Literal["pgcli.prevalence"]]) -> Prevalence: ...

"""Upstream PrevalenceCounter.clear_names: a new PrevalenceHandle with a copy
of the keyword counts and no name counts."""
def clear_prevalence_names(prevalence: Opaque[Literal["pgcli.prevalence"]]) -> Opaque[Literal["pgcli.prevalence"]]: ...

"""The first limit completions of completions.value (all of them when there
are fewer), in order, as CompletionItem(text = c.text, start_position =
c.start_position, display = c.display_text, display_meta =
c.display_meta_text) of each prompt_toolkit Completion c."""
def completion_items(completions: Opaque[Literal["pgcli.completions"]], limit: U64) -> CottList[CompletionItem]: ...

"""A compact rendering of the first limit completions of completions.value
(all of them when there are fewer), in order: for each prompt_toolkit
Completion c the text c.text + " | " + str(c.start_position) + " | " +
c.display_text + " | " + c.display_meta_text."""
def completion_lines(completions: Opaque[Literal["pgcli.completions"]], limit: U64) -> CottList[str]: ...

"""Upstream packages/sqlcompletion.suggest_type: decide which kinds of objects
can complete the word at the cursor. full_text is the whole buffer and
text_before_cursor the text before the cursor. The result lists
Suggestion values in upstream order. It uses the lock-selected sqlparse:
first assign None to sqlparse.engine.grouping.MAX_GROUPING_DEPTH and
MAX_GROUPING_TOKENS. sqlparse names: sqlparse.sql Comparison, Identifier,
Where, TokenList; sqlparse.tokens Error, DML (Keyword.DML). Upstream
tuples map to lists; Python None maps to Nothing. Defaults when a variant
is written with fewer fields below: Column(require_last_table false,
local_tables [], qualifiable false, context Nothing), Table(table_refs [],
local_tables []), View(table_refs []), Function(table_refs [], usage
Call), Keyword(last_token Nothing), Schema(quoted false). If any step
raises an exception (upstream either catches TypeError and AttributeError
or lets the error escape so prompt_toolkit shows nothing), the result is
[].

A. When full_text starts with "\\i " return [Path].

B. Statement state (upstream SqlStatement):
1. word = real.pgcli.parseutils.last_word(text_before_cursor,
   ManyPunctuations), computed on the original text_before_cursor.
2. When re.match(r"^\\s*\\\\ns\\s+[A-z0-9\\-_]+\\s+", t) matches a text t, t
   becomes re.sub of that pattern with "" (removes a leading "\\ns name "
   save-named-query prefix). Apply this to full_text and to
   text_before_cursor.
3. iso = real.pgcli.parseutils.isolate_query_ctes(full_text,
   text_before_cursor); Nothing gives []. full_text and
   text_before_cursor become iso's texts; local_tables = iso.local_tables.
4. identifier = None. When word is nonempty, does not end with "(" and
   does not start with "\\": text_before_cursor =
   text_before_cursor[:-len(word)] and identifier =
   partial_identifier(word). parsed = sqlparse.parse(text_before_cursor).
   partial_identifier(w): p = sqlparse.parse(w)[0]; when p has exactly one
   direct child and it is an Identifier return it; else when
   p.token_next_by(m=(Error, '"'))[1] is not None (an unmatched double
   quote) return partial_identifier(w + '"'); else None.
5. (full_text, text_before_cursor, statement) = split(full_text,
   text_before_cursor, parsed), where split(f, t, parsed):
   - more than one statement: current = len(t); start = end = 0; for each
     statement s in order: start, end = end, end + len(str(s)); when end
     >= current: t = f[start:current], f = f[start:], stop. statement is
     the last s visited.
   - exactly one: statement = parsed[0]. None at all: return (f, t, None).
   - When statement.get_type() is "CREATE" or "CREATE OR REPLACE" and
     first = statement.token_first() exists and
     statement.token_next(statement.token_index(first))[1] is a token
     whose value.upper() == "FUNCTION": m = re.search(
     r"(\\$.*?\\$)([\\s\\S]*?)\\1", f, re.M); when m exists and m.start(2) <=
     len(t) < m.end(2) (cursor inside the dollar-quoted body) return
     split(f[m.start(2):m.end(2)], t[m.start(2):],
     sqlparse.parse(t[m.start(2):])).
   - return (f, t, statement).
6. last_token = statement.token_prev(len(statement.tokens))[1] (the last
   non-whitespace child; comments count), or "" when statement is None
   or that is None.

C. When statement is not None and statement.token_first() exists and its
value starts with "\\": return special(text_before_cursor + word), using
the text_before_cursor of B5.

D. Otherwise return by_token(last_token).

Helpers over the state (text_before_cursor is mutable state):
- reduce(n): (tok, text) = the found token and truncated text of
  real.pgcli.parseutils.find_previous_keyword(text_before_cursor, n)
  (the same algorithm, keeping the sqlparse token itself);
  text_before_cursor = text; return tok (None when not found).
- tables(scope): refs = real.pgcli.parseutils.extract_tables(full_text
  when scope is full, else text_before_cursor); scope insert keeps only
  refs[:1]; otherwise when statement.token_first().value.lower() ==
  "insert" drop refs[0].
- identifier_schema(): p = identifier.get_parent_name() when identifier
  is not None; None when empty or absent; lower-cased unless
  identifier.value starts with '"'.
- parent(): identifier.get_parent_name() when identifier is not None,
  treating "" as absent.
- identifies(id, t): id == t.alias_name value, or id == t.name, or t.schema
  is a nonempty s with id == s + "." + t.name.
- last_child_value(): statement.token_prev(len(statement.tokens))[1]
  .value.lower() (false when statement is None or has no tokens).
  allow_join_condition: it is "on", "and" or "or". allow_join: it ends
  with "join" and is neither "cross join" nor "natural join".
- expression(v): with parent() present as P: refs = [t for t in
  tables(full) if identifies(P, t)]; return [Column(refs, local_tables =
  local_tables), Table(Some(P)), View(Some(P)), Function(Some(P))].
  Without: [Column(tables(full), local_tables = local_tables,
  qualifiable = true), Function(Nothing), Keyword(Some(v.upper()))].

special(text) (upstream suggest_special): text = text.lstrip(); cmd =
the part before the first " " stripped with every "+" removed and arg =
the part after it stripped (pgspecial.main.parse_special_command).
- cmd == text: [Special]. cmd "\\c" or "\\connect": [Database]. "\\T":
  [TableFormat]. "\\dn": [Schema].
- schema = None; when arg is nonempty, x = sqlparse.parse(arg)[0]
  .tokens[0] and schema = x.get_parent_name() when x is a TokenList.
- cmd == "\\d": schema ? [Table(schema), View(schema)] : [Schema,
  Table(Nothing), View(Nothing)].
- cmd "\\dT" (Datatype), "\\df" or "\\sf" (Function with usage Special),
  "\\dt" (Table), "\\dv" (View): with schema [X(schema)], else [Schema,
  X(Nothing)].
- cmd "\\n", "\\ns", "\\nd" or "\\nq": [NamedQuery]. Else [Keyword, Special].

by_token(token) (upstream suggest_based_on_last_token). token is a text
("" at the top level, "where" or "type" in internal calls) or a sqlparse
token. token_v: text.lower() for a text; for a Comparison
token.tokens[-1].value.lower(); for a Where return by_token(reduce(0)) (a None token gives []);
for an Identifier: k = the find_previous_keyword token of
text_before_cursor (n_skip 0, state unchanged); when k is "(" return
by_token("type"), else [Keyword]; otherwise token.value.lower(). Then
the first matching rule wins:
1. token == "": [Keyword, Special].
2. token_v ends with "(": p = sqlparse.parse(text_before_cursor)[0].
   a. When p.tokens is nonempty and p.tokens[-1] is a Where: cols =
      by_token("where"); w = p.tokens[-1]; q = w.token_prev(len(w.tokens)
      - 1)[1]; when q is a Comparison q = q.tokens[-1]; return [Keyword]
      when q.value.lower() == "exists", else cols.
   b. prev = p.token_prev(len(p.tokens) - 1)[1]. When prev has a
      nonempty value and prev.value.lower().split(" ")[-1] == "using":
      return [Column(tables(before), require_last_table = true,
      local_tables = local_tables)].
   c. Else when p.token_first().value.lower() == "select" and
      real.pgcli.parseutils.last_word(text_before_cursor, AllPunctuations)
      starts with "(": return [Keyword].
   d. pp = p.token_prev(p.token_index(prev))[1] when prev exists; when
      pp exists and pp.normalized == "INTO": return
      [Column(tables(insert), context = Some("insert"))].
   e. return expression(token_v).
3. "set": when sqlparse.parse(text_before_cursor)[0].token_first()
   .value.upper() == "SET" return [Keyword(Some("SET"))]; else
   [Column(tables(full), local_tables = local_tables)].
4. "select", "where", "having", "group by", "order by", "distinct":
   expression(token_v).
5. "as": [].
6. (token_v ends with "join" and token.is_keyword) or token_v in "copy",
   "from", "update", "into", "describe", "truncate": s =
   identifier_schema(); refs = real.pgcli.parseutils.extract_tables(
   text_before_cursor); is_join = the first alternative. Result: Schema
   first when s is None; then FromClauseItem(s, refs, local_tables) for
   "from" or a join, Table(s) for "truncate", else Table(s), View(s);
   then Join(tables(before), s) when is_join and allow_join.
7. "function": s = identifier_schema(); prev =
   statement.token_prev(statement.token_index(token))[1]; [] when token
   is not a direct child of statement (token_index raises ValueError),
   prev is None, or prev.value.lower() is not "drop", "alter", "create"
   or "create or replace"; otherwise Schema first when s is None, then
   Function(s, usage = Signature).
8. "table" or "view": s = identifier_schema(); s ? [Table(s)] or
   [View(s)] : [Schema, Table(Nothing)] or [Schema, View(Nothing)].
9. "column": [Column(tables(full))].
10. "on": refs = tables(before); with parent() present as P: f = [t in
    refs if identifies(P, t)]; [Column(f, local_tables = local_tables),
    Table(Some(P)), View(Some(P)), Function(Some(P))] followed by
    JoinCondition(refs, Some(f[-1])) when f is nonempty and
    allow_join_condition. Without: aliases =
    [real.pgcli.parseutils.table_reference_ref(t) for t in refs];
    [Alias(aliases), JoinCondition(refs, Nothing)] when
    allow_join_condition, else [Alias(aliases)].
11. "c", "use", "database", "template": [Database].
12. "schema": k = reduce(2); [Schema(quoted = k exists and
    k.value.lower() == "set")].
13. token_v ends with "," or is "=", "and", "or": k = reduce(0);
    by_token(k) when k exists, else [].
14. token_v == "::", or token_v == "type" and datatype_keyword(token): s =
    identifier_schema(); [Datatype(s), Table(s)] plus Schema when s is
    None. datatype_keyword: true for a text; false when not
    token.is_keyword; else k = the find_previous_keyword token of
    text_before_cursor.rstrip() with n_skip 1 (state unchanged); false
    when none, else k.ttype is not sqlparse.tokens.Keyword.DML.
15. "alter", "create", "drop": [Keyword(Some(token_v.upper()))].
16. "to": [Schema].
17. token.is_keyword: k = reduce(1); by_token(k) when k exists, else
    [Keyword(Some(token_v.upper()))].
18. otherwise [Keyword]."""
def suggest_sql_completions(full_text: str, text_before_cursor: str) -> CottList[Suggestion]: ...

"""Upstream PGCompleter.get_completions (pgcompleter.py) on a completer
loaded with request.catalog, returning the completions in display order as
a CompletionList.

A. Definitions.
- LITERALS = json.loads(PGLITERALS_JSON); KEYWORD_TREE its "keywords"
  object (key order kept), BUILTIN_FUNCTIONS its "functions" list,
  BUILTIN_DATATYPES its "datatypes" list; ALL_KEYWORDS = every key of
  KEYWORD_TREE plus every entry of its lists.
- before = request.text[:request.cursor]. word =
  prompt_toolkit.document.Document(request.text,
  request.cursor).get_word_before_cursor(WORD=True): "" when before is
  empty or ends with whitespace, else the maximal run of non-whitespace
  characters ending at the cursor.
- C = request.catalog.value (layout documented on CompletionCatalog) and
  P = request.prevalence.value (layout documented on PrevalenceHandle).
- escape(n) follows escape_identifier_name; unescape(n) = n[1:-1] when n
  is nonempty, starts with '"' and ends with '"', else n. case(w) follows
  apply_identifier_casing with the casing words C["casing"].
  alias_of(n) = generate_table_alias(n, request.settings.alias_map).
  ref(t) = real.pgcli.parseutils.table_reference_ref(t). norm(r) = r when
  r starts with '"', else '"' + r.lower() + '"'. arglist(f, u) follows
  function_argument_list for the function row f with casing C["casing"].
Implement these rules privately (catalog-sized data must never be passed
to a Cott facade); only suggest_sql_completions and the small
real.pgcli.parseutils helpers may be called as facades.

B. Completer state (upstream extend_* calls; all keys escaped).
- search_path = [escape(s) for s in C["search_path"]].
- Four ordered maps TABLES, VIEWS, FUNCTIONS, DATATYPES from schema to an
  ordered map; each starts with an empty entry for escape(s) of every s
  in C["schemata"] in order.
- For each row (schema, name, columns) of C["tables"] in order: when
  escape(schema) is a key of TABLES, set TABLES[escape(schema)]
  [escape(name)] to a new empty ordered column map (a relation in an
  unknown schema is ignored). Then for each row in order and each column
  (col, datatype, has_default, default) of its columns in order:
  TABLES.setdefault(escape(schema), {}).setdefault(escape(name), {})
  [escape(col)] = a column record (name escape(col), datatype,
  has_default, default, fks = []). The same two passes fill VIEWS from
  C["views"].
- For each row of C["foreign_keys"]: escape its six names; child =
  TABLES[child_schema][child_table][child_column], parent =
  TABLES[parent_schema][parent_table][parent_column] (skip the row when a
  lookup fails); append the escaped 6-tuple to child.fks and then to
  parent.fks.
- For each (schema, name) of C["datatypes"]: DATATYPES[escape(schema)]
  [escape(name)] = present (unknown schema ignored).
- For each function row f of C["functions"]: append f to
  FUNCTIONS[escape(f.schema_name)][escape(f.func_name)] (unknown schema
  ignored; name keys keep first-insertion order). Field names of f below
  are the FunctionMetadata names of the tuple positions; an empty list
  counts as None and return_type is used stripped.
- WORDS (plain-mode vocabulary) = the set of ALL_KEYWORDS,
  BUILTIN_FUNCTIONS and the escaped names of every schema, relation,
  column, function and datatype of C. Databases are not included.

C. find_matches(text, collection, mode, meta) returns (item, priority)
pairs; mode is fuzzy (default) or strict, meta a text or None.
1. Empty collection gives []. type_priority = the index of meta in
   ["keyword", "function", "view", "table", "datatype", "database",
   "schema", "column", "table alias", "join", "name join", "fk join",
   "table format"], or -1 when meta is not in that list.
2. text = real.pgcli.parseutils.last_word(text, MostPunctuations)
   .lower(); text_len = len(text); then when text starts with '"' drop
   that character (text_len keeps the length before dropping).
3. match(s): fuzzy: when s.lower()[:len(text) + 1] equals text or text +
   " " return (inf, -1); else m = re.search("(" + ".*?".join(re.escape(ch)
   for ch in text) + ")", unescape(s.lower())); a match gives
   (-len(m.group()), -m.start()), else no match. strict: when
   s.lower() starts with text return (-inf, 0), else no match.
4. For each element of collection in order. A candidate has completion,
   prio (0), meta (None), synonyms ([completion]), prio2 (0) and display
   (completion); its display_meta is its meta when not None, else the
   meta argument; its sort_key is the largest match(syn) over synonyms
   that match; none matching skips it. A plain text s is a candidate
   with completion s and display_meta meta, sort_key = match(s). Then:
   display_meta longer than 50 characters becomes display_meta[:47] +
   "..."; lexical = tuple(0 if ch in " _" else -ord(ch) for ch in
   unescape(completion.lower())) + (1,) + tuple(completion) using the
   uncased completion; item = case(completion); display = case(display);
   count = P["names"].get(item, 0) in fuzzy mode and
   P["keywords"].get(item, 0) in strict mode; priority = (sort_key,
   type_priority, prio, count, prio2, lexical); output
   Completion(item, start_position=-text_len, display=display,
   display_meta=display_meta).

D. Objects.
- schemas_of(M, schema): with a nonempty schema: [escape(schema)] when it
  is a key of M, else []; without: search_path when
  settings.search_path_filter else all keys of M in order (schemas that
  are not keys of M are skipped when walking).
- shown(sch, schema) = None when schema is nonempty or sch is in
  search_path, else sch.
- objects(M, schema) = [(name, shown(sch, schema)) for sch in
  schemas_of(M, schema) for name in M[sch]].
- functions_of(schema, keep) = [(name, shown(sch, schema), f) for sch in
  schemas_of(FUNCTIONS, schema) for name, fs in FUNCTIONS[sch] for f in
  fs if keep(f)].
- alias_for(tbl, refs) (upstream alias): tbl = case(tbl); taken =
  {norm(ref(t)) for t in refs}; when settings.generate_aliases tbl =
  alias_of(unescape(tbl)); when norm(tbl) is not taken return tbl; else
  try tbl + str(i) (or '"' + tbl[1:-1] + str(i) + '"' when tbl starts
  with '"') for i = 2, 3, ... and return the first whose norm is not
  taken.
- candidate(name, schema, f, aliased, refs, arg) (upstream _make_cand):
  c = case(name); synonyms [c, alias_of(c)]; tail = " " +
  alias_for(c, refs) when aliased else ""; head = case(schema) + "."
  when schema else ""; suffix = arglist(f, Call) and display suffix
  arglist(f, CallDisplay) when arg is Call; both arglist(f, Signature)
  when arg is Signature; both "" without arg. Candidate completion head
  + c + suffix + tail, display head + c + display suffix + tail, prio 0,
  prio2 0 when schema else 1.
- scoped(refs, locals) (upstream populate_scoped_cols): an ordered map
  from key (schema, name, alias, is_function) to a column list; add(key,
  cols) appends to the key's list, creating it at the end. ctes = {norm(
  t.name): t for t in locals} (a later duplicate wins); a local table's
  columns are handed out only on its first use within the request
  (upstream stores a one-shot generator), later uses add no columns.
  For each t in refs: when t.schema is absent and norm(t.name) is in
  ctes: add((None, t.name, "CTE", t.alias_name == Some("functions")),
  its columns as records with datatype None, no default and no fks)
  and continue (upstream passes its arguments shifted, so the key's
  alias is the literal "CTE"). Otherwise for each sch in [t.schema]
  when nonempty else search_path: rel = escape(t.name), s = escape(sch)
  (search_path entries are escaped a second time). When t.is_function:
  for each f in FUNCTIONS.get(s, {}).get(rel, []): add((s, rel,
  t.alias_name, true), fields(f)), where fields(f) is [] when
  f.return_type.lower() == "void", [record(f.func_name,
  f.return_type)] when f has no arg_modes, else a record(name, type)
  for each name, type, mode of arg_names, arg types ("None" when
  absent) and arg_modes with mode "o", "b" or "t". Otherwise for M in
  (TABLES, VIEWS): cols = M.get(s, {}).get(rel); when cols is nonempty
  add((s, rel, t.alias_name, false), its records in order) and stop.
  The ref of a key is ref(TableReference(schema, name, alias, is_function)).

E. Matchers (each returns a list of (item, priority)).
- Column(refs, require_last_table, locals, qualifiable, context):
  qualify = false unless qualifiable, else by settings.qualify_columns:
  "always" true, "never" false, "if_more_than_one_table" len(refs) > 1;
  another value makes the whole result [] (upstream KeyError). q(col,
  r) = r + "." + case(col) when qualify, else case(col). cols =
  scoped(refs, locals). When require_last_table: last =
  ref(refs[-1]) (no refs makes the result []); other = {c.name for keys
  whose ref != last}; keep only keys whose ref == last with their
  columns whose name is in other. lastword =
  real.pgcli.parseutils.last_word(word, MostPunctuations). When lastword
  == "*": for context Some("insert") drop columns that have a default
  matching re.match(r"^now\\(\\)$") or re.match(r"^nextval\\("); when
  settings.asterisk_column_order == "alphabetic" sort each key's columns
  by name; when lastword != word and len(refs) == 1 and
  word[-len(lastword) - 1] == ".", text = (", " + word[:-1]).join(
  case(q(c.name, ref(key)))), else text = ", ".join(q(c.name,
  ref(key))), both over every key and column in order; return the single
  Completion(text, start_position=-1, display="*", display_meta=
  "columns") with priority (1, 1, 1).
  Otherwise find_matches(word, [candidate completion q(c.name,
  ref(key)), meta "column", synonyms [c.name, alias_of(case(c.name))]
  for every key and column], fuzzy, "column").
- Join(refs, schema): cols = scoped(refs, []); qualified = {norm(ref(t)):
  t.schema}, order = {norm(ref(t)): position}, taken = {norm(ref(t))}
  over refs; others = {(key schema, key name) for every key of cols but
  the last}. For each key R, column r of R and fk of r.fks in order:
  right = (R.schema, R.name, r.name); child and parent the fk's triples;
  left = child when parent == right, else parent. Skip when schema is
  nonempty and left schema != schema. When settings.generate_aliases or
  norm(left table) is taken: a = alias_for(left table, refs); join =
  case(left table) + " " + a + " ON " + a + "." + case(left column) +
  " = " + ref(R) + "." + case(right column); else join = case(left
  table) + " ON " + case(left table) + "." + case(left column) + " = " +
  ref(R) + "." + case(right column). synonyms = [join, the second form
  with alias_of(case(left table)) in place of the table]. When schema is
  empty and ((qualified[norm(ref(R))] is nonempty and left schema ==
  right schema) or left schema not in (right schema, "public")), prefix
  join with left schema + ".". prio = order[norm(ref(R))] * 2 + (0 when
  (left schema, left table) is in others else 1). Candidate(join, prio,
  meta "join", synonyms). Return find_matches(word, candidates, fuzzy,
  "join").
- JoinCondition(refs, parent): cols = scoped(refs, []); lref =
  ref(parent value) when parent is Some, else ref(refs[-1]); (L, lcols)
  = the last key whose ref == lref with its columns; no refs or no such
  key gives []. order = {ref(t): position in refs}. add(lcol, rcol,
  rref, prio, meta): cond = ("" when parent is Some else ref(L) + ".") +
  case(lcol) + " = " + rref + "." + case(rcol); skip a cond already
  produced; else Candidate(cond, prio + order[rref], meta). First,
  coldict maps (key schema, key name, column name) to the keys (in order)
  for every key whose ref != lref; for each column c of lcols and fk of
  c.fks: left = (L.schema, L.name, c.name); when left == the fk child
  triple then (left, right) = (child, parent) else (parent, child); for
  each key K in coldict[right]: add(left column, right column, ref(K),
  2000, "fk join"). Then with col_table mapping (column name, datatype)
  to keys over every key and column: for each c of lcols and each key K
  in col_table[(c.name, c.datatype)] whose ref != ref(L): add(c.name,
  c.name, ref(K), 1000 when c.datatype is "integer", "bigint" or
  "smallint" else 0, "name join"). Return find_matches(word, conds,
  fuzzy, "join").
- Function(schema, refs, usage), aliased (default false): usage From
  keeps f when not aggregate, not window, not extension and (schema_name
  == "public" or schema_name in search_path or schema_name == schema);
  other usages set aliased false and keep f when not extension and
  (schema_name == "public" or schema_name == schema). arg = Signature for
  Signature, none for Special, else Call. cands = the distinct
  candidate(name, shown schema, f, aliased, refs, arg) for
  functions_of(schema, keep), first occurrence kept. Result
  find_matches(word, cands, fuzzy, "function"), followed when schema is
  absent and usage is Call by find_matches(word, BUILTIN_FUNCTIONS,
  strict, "function").
- Schema(quoted): names = keys of TABLES; unless word starts with "pg_"
  drop names starting with "pg_"; quoted maps n to "'" + unescape(n) +
  "'"; find_matches(word, names, fuzzy, "schema").
- FromClauseItem(schema, refs, locals): Table(schema, refs, locals) +
  View(schema, refs) + Function(schema, refs, From), each aliased =
  settings.generate_aliases.
- Table(schema, refs, locals), aliased (default false): objs =
  objects(TABLES, schema) + [(t.name, None) for t in locals]; when schema
  is absent and word does not start with "pg_" drop names starting with
  "pg_"; find_matches(word, [candidate(name, shown, None, aliased, refs,
  none)], fuzzy, "table").
- View(schema, refs), aliased (default false): the same over
  objects(VIEWS, schema) with meta "view".
- Alias(aliases): find_matches(word, aliases, fuzzy, "table alias").
- Database: find_matches(word, C["databases"], fuzzy, "database").
- Keyword(last_token): words = KEYWORD_TREE's keys, or KEYWORD_TREE[
  last_token] when that list exists and is nonempty. casing =
  settings.keyword_casing.lower(), "upper" when not upper, lower or auto;
  auto means lower when word is nonempty and word[-1].islower(), else
  upper. Upper- or lower-case every word; find_matches(word, words,
  strict, "keyword").
- Special: candidates (command, prio 0, meta description) of
  request.special_commands in order; find_matches(word, them, strict,
  None).
- Datatype(schema): find_matches(word, [candidate(name, shown, None,
  false, [], none) for objects(DATATYPES, schema)], fuzzy, "datatype"),
  followed when schema is absent by find_matches(word,
  BUILTIN_DATATYPES, strict, "datatype").
- NamedQuery: find_matches(word, request.named_queries, fuzzy, "named
  query"). TableFormat: find_matches(word, request.table_formats, fuzzy,
  "table format"). Path: [] (the REPL completes paths itself with
  prompt_toolkit PathCompleter).

F. Result. When request.smart_completion is false: find_matches(word,
WORDS, strict, None) completions sorted by text. Otherwise run the
matcher of every Suggestion of suggest_sql_completions(request.text,
before) in order, concatenate their pairs and stable-sort them by
priority, highest first (Python sorted(pairs, key=priority,
reverse=True)). Return Opaque(tag="pgcli.completions", value=the list of
completions). Comparing the (1, 1, 1) priority with another priority, or
any other exception, gives an empty list (upstream crashes)."""
def complete_sql_text(request: CompletionRequest) -> Opaque[Literal["pgcli.completions"]]: ...

"""Upstream PrevalenceCounter.update (keywords_only false) and
update_keywords (keywords_only true): return a new PrevalenceHandle whose
dicts are copies of prevalence.value's with the usage counts of text
added (a key is only added when its count grows; the input is never
mutated).
- Keywords: for each key K of the "keywords" object of PGLITERALS_JSON in
  order, compile "\\b" + K with every whitespace run replaced by \\s+ +
  "\\b" (K itself is not escaped) with re.MULTILINE | re.IGNORECASE, and
  add the number of re.finditer matches in text to the "keywords" count
  of K.
- Names, only when keywords_only is false: for each statement of
  sqlparse.parse(text) (lock-selected sqlparse; assign None to
  sqlparse.engine.grouping.MAX_GROUPING_DEPTH and MAX_GROUPING_TOKENS
  first) and each leaf token of statement.flatten() whose ttype is in
  sqlparse.tokens.Name (Name or a subtype), add 1 to the "names" count of
  token.value."""
def update_prevalence(prevalence: Opaque[Literal["pgcli.prevalence"]], text: str, keywords_only: bool) -> Opaque[Literal["pgcli.prevalence"]]: ...

"""Upstream pgcompleter.load_alias_map_file, used for [main] alias_map_file
(upstream reloads it whenever a completer is created). Read path as text
and parse it with json.load; return the object as a map from table name
to alias. A missing file gives InvalidMapFile("Cannot read alias_map_file
- " + str(path) + " does not exist"). Text that is not valid JSON, JSON
that is not an object, or an object with a non-string value gives
InvalidMapFile("Cannot read alias_map_file - " + str(path) + " is not
valid json"). Any other OSError gives InvalidMapFile("Cannot read
alias_map_file - " + str(path) + ": " + the error's strerror)."""
def load_alias_map(path: Path) -> Result[FrozenMap[str, str], AliasMapError]: ...

"""Upstream completion_refresher refreshers (schemata, tables, views, types,
databases, casing, functions) with the PGExecute metadata queries, run on
executor.connection, the caller's autocommit psycopg connection (the
single-connection path): never close, commit or roll it back.
- When executor.virtual_database is true return Err(VirtualDatabase)
  without querying.
- V = executor.connection.info.server_version (psycopg integer, e.g.
  160004). Each query runs on a new cursor (with conn.cursor() as cur)
  with psycopg %s parameters; a psycopg.Error that is not the handled
  search_path failure gives Err(QueryFailed(str(error))).
Steps, in order:
1. search_path: SEARCH_PATH_QUERY, first column of every row; when it
   raises psycopg.ProgrammingError run SEARCH_PATH_FALLBACK_QUERY and take
   fetchone()[0] (a list of schema names).
2. schemata: SCHEMATA_QUERY, first column of every row.
3. tables: RELATIONS_QUERY with parameters [["r", "p", "f"]] gives
   (schema, name) rows, each becoming a (schema, name, []) relation tuple
   in row order. Columns: COLUMNS_QUERY when V >= 80400, else
   COLUMNS_QUERY_LEGACY, with the same parameters, rows (schema, table,
   column, type name, has_default, default): append (column, type name,
   has_default is True (NULL is False), default str or None) to the
   column list of the relation with that schema and name; a row whose
   relation was not listed creates a new relation tuple appended at the
   end. Foreign keys: FOREIGN_KEYS_QUERY when V >= 90000 (rows parent
   schema, parent table, parent column, child schema, child table, child
   column, kept as 6-tuples), none otherwise.
4. views: the same relation and column queries with parameters
   [["v", "m"]].
5. datatypes: DATATYPES_QUERY when V > 90000, else DATATYPES_QUERY_LEGACY;
   (schema, name) tuples.
6. databases: DATABASES_QUERY, first column of every row.
7. casing: [] when request.casing_file is Nothing. Otherwise with path =
   its value: when request.generate_casing_file and os.path.isfile(path)
   is false, run CASING_QUERY and write "\\n".join(first column of every
   row) to path in text mode (created or truncated, no final newline).
   Then when os.path.isfile(path), casing = [line.strip() for every line
   of the file read in text mode] (blank lines give ""), else []. An
   OSError gives Err(CasingFileFailed(path, str(error))).
8. functions: FUNCTIONS_QUERY_V11 when V >= 110000, FUNCTIONS_QUERY_V9
   when V > 90000, FUNCTIONS_QUERY_V84 when V >= 80400, else
   FUNCTIONS_QUERY_LEGACY. Each row (schema_name, func_name, arg names,
   arg types, arg modes, return type, is_aggregate, is_window,
   is_set_returning, is_extension, arg_defaults) becomes an 11-tuple with
   each array a list of str or None when NULL, the return type stripped
   of surrounding whitespace, NULL booleans False and arg_defaults a str
   or None.
Build the catalog dict directly from these rows (never through Cott
structs, which cannot hold a real catalog) with the layout documented on
CompletionCatalog and return Ok(Opaque(tag="pgcli.completion-catalog",
value=that dict)); every list keeps row order."""
def refresh_completion_metadata(executor: Executor, request: MetadataRefreshRequest) -> Result[Opaque[Literal["pgcli.completion-catalog"]], MetadataRefreshError]: ...

__all__ = ["AliasMapError", "AliasMapError_InvalidMapFile", "ArgumentListUsage", "ArgumentListUsage_Call", "ArgumentListUsage_CallDisplay", "ArgumentListUsage_Signature", "CASING_QUERY", "COLUMNS_QUERY", "COLUMNS_QUERY_LEGACY", "ColumnMetadata", "CompleterSettings", "CompletionCatalog", "CompletionItem", "CompletionList", "CompletionMetadata", "CompletionRequest", "DATABASES_QUERY", "DATATYPES_QUERY", "DATATYPES_QUERY_LEGACY", "DatatypeMetadata", "FOREIGN_KEYS_QUERY", "FUNCTIONS_QUERY_LEGACY", "FUNCTIONS_QUERY_V11", "FUNCTIONS_QUERY_V84", "FUNCTIONS_QUERY_V9", "ForeignKeyMetadata", "FunctionMetadata", "FunctionUsage", "FunctionUsage_Call", "FunctionUsage_From", "FunctionUsage_Signature", "FunctionUsage_Special", "MetadataRefreshError", "MetadataRefreshError_CasingFileFailed", "MetadataRefreshError_QueryFailed", "MetadataRefreshError_VirtualDatabase", "MetadataRefreshRequest", "PGLITERALS_JSON", "Prevalence", "PrevalenceHandle", "RELATIONS_QUERY", "RelationMetadata", "SCHEMATA_QUERY", "SEARCH_PATH_FALLBACK_QUERY", "SEARCH_PATH_QUERY", "SpecialCommandInfo", "Suggestion", "Suggestion_Alias", "Suggestion_Column", "Suggestion_Database", "Suggestion_Datatype", "Suggestion_FromClauseItem", "Suggestion_Function", "Suggestion_Join", "Suggestion_JoinCondition", "Suggestion_Keyword", "Suggestion_NamedQuery", "Suggestion_Path", "Suggestion_Schema", "Suggestion_Special", "Suggestion_Table", "Suggestion_TableFormat", "Suggestion_View", "apply_identifier_casing", "catalog_with_search_path", "clear_prevalence_names", "complete_sql_text", "completion_catalog_from", "completion_items", "completion_lines", "empty_completion_catalog", "escape_identifier_name", "function_argument_list", "generate_table_alias", "load_alias_map", "prevalence_counts", "prevalence_from", "refresh_completion_metadata", "suggest_sql_completions", "update_prevalence"]
