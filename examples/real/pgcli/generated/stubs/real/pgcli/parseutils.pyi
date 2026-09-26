from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.pgcli.parseutils_types import CteDefinition as CteDefinition, CteExtraction as CteExtraction, CteTable as CteTable, IsolatedQuery as IsolatedQuery, PreviousKeyword as PreviousKeyword, TableReference as TableReference, WordBoundary as WordBoundary, WordBoundary_AllPunctuations as WordBoundary_AllPunctuations, WordBoundary_AlphanumUnderscore as WordBoundary_AlphanumUnderscore, WordBoundary_ManyPunctuations as WordBoundary_ManyPunctuations, WordBoundary_MostPunctuations as WordBoundary_MostPunctuations
"""Upstream parseutils.utils.last_word: the word that ends the text. Return ""
when text is empty or its last character is whitespace (Python
str.isspace). Otherwise search text with the regular expression selected by
boundary (see WordBoundary, Python re semantics) and return the matched
text, or "" when there is no match. Examples: "abc def" gives "def";
"abc def;" gives "" with AlphanumUnderscore; "bac $def" gives "def" with
AlphanumUnderscore and "$def" with MostPunctuations; "bac::def" gives "def"
with MostPunctuations; "\\"foo*bar" gives "\\"foo*bar" with
MostPunctuations."""
def last_word(text: str, boundary: WordBoundary) -> str: ...

"""Upstream TableReference.ref: the name under which a statement refers to the
table. When table.alias_name is Some(alias) with a nonempty alias, return
the alias. Otherwise return table.name when it is lower case (Python
str.islower(): it has at least one cased character and no upper-case one)
or starts with a double quote, and otherwise the name wrapped in double
quotes ("\\"" + name + "\\""). Example: name "Users" without alias gives
"\\"Users\\"", name "users" gives "users", name "123" gives "\\"123\\""."""
def table_reference_ref(table: TableReference) -> str: ...

"""Upstream parseutils.tables.extract_tables: the relations and functions the
first statement of sql reads from, in statement order. It is built on the
lock-selected sqlparse; first assign None to
sqlparse.engine.grouping.MAX_GROUPING_DEPTH and
sqlparse.engine.grouping.MAX_GROUPING_TOKENS (upstream removes both grouping
limits at import). The sqlparse classes named below are sqlparse.sql
Identifier, IdentifierList, Function, TokenList and the token types are
sqlparse.tokens Keyword, Keyword.DML (named DML) and Punctuation.

1. statements = sqlparse.parse(sql). When it yields no statement, or the
   first statement S has no first token (S.token_first() is None, e.g. for
   whitespace-only sql), return an empty list.
2. insert_stmt = S.token_first().value.lower() == "insert".
3. Walk the token stream produced by from_part(S, stop_at_punctuation =
   insert_stmt), a generator over the direct children of a token list:
   keep a flag prefix_seen = false and for each child item in order:
   - if prefix_seen: if item is a subselect (item.is_group and one of its
     direct children has ttype exactly DML and value.upper() in SELECT,
     INSERT, UPDATE, CREATE, DELETE), yield everything from_part(item,
     stop_at_punctuation) yields; else if stop_at_punctuation and
     item.ttype is exactly Punctuation, stop this generator (an enclosing
     generator continues); else if item.ttype is exactly Keyword (the bare
     Keyword type, not a subtype) and item.value.upper() is not "FROM" and
     does not end with "JOIN", set prefix_seen = false; else yield item
     (this also yields whitespace and every other token);
   - else if item.ttype is exactly Keyword or exactly DML: set prefix_seen =
     true when item.value.upper() is COPY, FROM, INTO, UPDATE or TABLE or
     ends with "JOIN";
   - else if item is an IdentifierList: when one of its get_identifiers()
     has ttype exactly Keyword and value.upper() == "FROM", set
     prefix_seen = true (this catches "SELECT a, FROM abc").
4. allow_functions = not insert_stmt (sqlparse reads "insert into foo (a,
   b)" as a call of foo). For each yielded item:
   - IdentifierList: for each identifier of get_identifiers(): skip it when
     it is not a TokenList (a plain token has no name methods); take
     schema = identifier.get_parent_name(), name =
     identifier.get_real_name(), is_function = allow_functions and one of
     identifier.tokens is a Function; when name is nonempty produce
     TableReference(schema, name, alias_name =
     identifier.get_alias(), is_function) with these raw values (no case or quote normalization
     in this branch).
   - Identifier: produce the normalized triple of the rules below with
     is_function = allow_functions and one of item.tokens is a Function.
   - Function: produce the normalized triple but with schema Nothing and
     is_function = allow_functions.
   - anything else is ignored.
   Normalized triple (schema, name, alias) of an item: name =
   item.get_real_name(), schema = item.get_parent_name(), alias =
   item.get_alias(). When name is empty or None: schema = None, name =
   item.get_name(), alias = alias or name. schema_quoted = schema is
   nonempty and item.value starts with "\\"". A nonempty schema that is not
   schema_quoted is lower-cased. quote_count = number of "\\"" characters in
   item.value; name_quoted = quote_count > 2 or (quote_count > 0 and not
   schema_quoted). alias_quoted = alias is nonempty and item.value ends
   with "\\"". When alias_quoted, or (name_quoted and alias is empty and
   name.islower()), alias becomes "\\"" + (alias or name) + "\\"". Then when
   name is nonempty, not name_quoted and not name.islower(): alias becomes
   name if alias is empty, and name becomes name.lower().
5. Drop references whose name is empty or None and return the rest in
   order. Python None maps to Option.Nothing.

Examples: "select * from abc" gives (Nothing, "abc", Nothing, false);
"select * from abc.\\"def\\"" gives (Some "abc", "def", Some "\\"def\\"",
false); "select * from \\"Abc\\" a" gives (Nothing, "Abc", Some "a", false);
"insert into abc (id, name) values (1, \\"def\\")" gives (Nothing, "abc", Some
"abc", false); "SELECT * FROM foo.bar(x) baz" gives (Some "foo", "bar", Some
"baz", true)."""
def extract_tables(sql: str) -> CottList[TableReference]: ...

"""Upstream parseutils.ctes.extract_ctes, built on the lock-selected sqlparse
(first assign None to sqlparse.engine.grouping.MAX_GROUPING_DEPTH and
MAX_GROUPING_TOKENS). Nothing means upstream raised TypeError or
AttributeError (the callers then give up); implement the steps literally
with the same sqlparse calls so that the same inputs fail.

When sql is "" return Some(ctes: [], remainder: ""). Otherwise p =
sqlparse.parse(sql)[0] and token_start_pos(tokens, i) = the sum of
len(str(t)) over tokens[:i] (code points).
1. idx, tok = p.token_next(-1, skip_ws=True, skip_cm=True). Unless tok is
   not None and tok.ttype == sqlparse.tokens.CTE (the WITH keyword),
   return Some(ctes: [], remainder: sql).
2. idx, tok = p.token_next(idx) (default skipping: whitespace only). When
   tok is None return Some(ctes: [], remainder: ""). start_pos =
   token_start_pos(p.tokens, idx).
3. If tok is a sqlparse.sql.IdentifierList: for each t of
   tok.get_identifiers(): cte = cte_from_token(t, start_pos +
   token_start_pos(tok.tokens, tok.token_index(t))); append it unless it
   is None. Else if tok is a sqlparse.sql.Identifier: append
   cte_from_token(tok, start_pos) unless None. (Anything else, e.g. the
   RECURSIVE keyword, declares nothing.)
4. remainder = "".join(str(x) for x in p.tokens[p.token_index(tok) + 1:]).

cte_from_token(t, pos0): name = t.get_real_name() (a plain token without
that method raises AttributeError, so the whole result is Nothing); when
name is empty return None. idx, parens = t.token_next_by(
sqlparse.sql.Parenthesis) (instance search over t's direct children);
when parens is None return None. start = pos0 + token_start_pos(t.tokens,
idx); stop = start + len(str(parens)); columns = column_names(parens).

column_names(parsed): idx, tok = parsed.token_next_by(t=
sqlparse.tokens.DML); tok_val = tok.value.lower() when tok exists. When
tok_val is insert, update or delete: idx, tok = parsed.token_next_by(idx,
(sqlparse.tokens.Keyword, "returning")) with idx passed positionally as
the first (instance-class) argument exactly as upstream does, which
raises TypeError whenever idx is not 0, so a data-modifying CTE body in
parentheses makes the result Nothing. Otherwise when tok_val is not
select, return no columns. Then idx, tok = parsed.token_next(idx,
skip_ws=True, skip_cm=True); the columns are t.get_name() for t = tok when
tok is a sqlparse.sql.Identifier, or for each t of tok.get_identifiers()
that is an Identifier when tok is an IdentifierList; otherwise none.

Example: "WITH a AS (SELECT abc FROM xxx) SELECT * FROM a" gives
ctes [CteDefinition("a", ["abc"], 10, 31)] and remainder " SELECT * FROM a"."""
def extract_ctes(sql: str) -> Option[CteExtraction]: ...

"""Upstream parseutils.ctes.isolate_query_ctes: simplify a query for
completion by turning its CTEs into local tables. Offsets count code
points.

- When full_text is empty or whitespace only, return Some(full_text,
  text_before_cursor, []).
- extraction = extract_ctes(full_text); Nothing gives Nothing. When it has
  no CTE return Some(full_text, text_before_cursor, []).
- current = the length of text_before_cursor. Walk the CTEs in order with
  an accumulating list of local tables: when cte.start < current <
  cte.stop the cursor is inside that CTE body, so return Some(full_text[
  cte.start:cte.stop], full_text[cte.start:current], the CTEs before it as
  CteTable(name, columns)). Otherwise append CteTable(cte.name,
  cte.columns) and continue.
- After the last CTE (cursor in the main body) return Some(
  full_text[last.stop:], text_before_cursor[last.stop:current], all CTEs
  as CteTable) using Python slice semantics."""
def isolate_query_ctes(full_text: str, text_before_cursor: str) -> Option[IsolatedQuery]: ...

"""Upstream parseutils.utils.find_prev_keyword with the found token reduced to
its text. When sql.strip() is empty return (Nothing, ""). Otherwise take
the flattened leaf tokens of the first statement,
list(sqlparse.parse(sql)[0].flatten()), and cut them to
flattened[:len(flattened) - n_skip] (Python slice semantics: a negative
bound counts from the end). Scanning that list from the end, the first
token whose value is "(" or which is a keyword (token.is_keyword) whose
value.upper() is not AND, OR, NOT or BETWEEN is the result: return
(Some(token.value), the concatenation of the values of the flattened
tokens up to and including it). When none qualifies return (Nothing, "").
Before parsing assign None to sqlparse.engine.grouping.MAX_GROUPING_DEPTH
and MAX_GROUPING_TOKENS. Examples: "select * from foo where bar = 1 and
baz or " gives ("where", "select * from foo where"); "select * from tbl1
inner join tbl2 using (col1, " gives ("(", "select * from tbl1 inner join
tbl2 using (")."""
def find_previous_keyword(sql: str, n_skip: U64) -> PreviousKeyword: ...

"""Upstream parseutils.utils.is_open_quote: true when sql contains an
unclosed quote. Parse sql with the lock-selected sqlparse
(sqlparse.parse; assign None to sqlparse.engine.grouping.MAX_GROUPING_DEPTH
and MAX_GROUPING_TOKENS first) and return true when any leaf token of any
parsed statement (statement.flatten()) matches
token.match(sqlparse.tokens.Error, ("'", "$")), i.e. an unmatched single
quote or dollar sign that the lexer reported as an error token. Examples:
"$$ foo $$" and "foo bar $$ baz $$" are closed; "$$", "foo 'bar baz",
"$a$ foo " and "foo $$ bar $$; foo $$" are open."""
def is_open_quote(sql: str) -> bool: ...

"""Upstream parseutils.is_destructive: whether any statement of queries needs
a destructive-command confirmation for the given keyword list. Uses the
lock-selected sqlparse (assign None to
sqlparse.engine.grouping.MAX_GROUPING_DEPTH and MAX_GROUPING_TOKENS
first). For each query of sqlparse.split(queries) that is nonempty:
- formatted = sqlparse.format(query.lower(), strip_comments=True).strip().
- When keywords contains "unconditional_update" and the query is an
  unconditional update, return true. A query is an unconditional update
  when sqlparse.parse(query) yields a first statement whose first token
  skipping whitespace and comments (token_first(skip_cm=True)) has ttype
  exactly sqlparse.tokens.DML with value.upper() == "UPDATE", and none of
  that statement's direct children (statement.tokens) is a
  sqlparse.sql.Where (a WHERE inside a string, comment or subquery does
  not count).
- When formatted is nonempty and its first whitespace-separated word
  (formatted.split()[0]) equals one of the keywords lower-cased, return
  true.
Otherwise return false. Examples: "update abc set x = 1 where y = 2" is
destructive for ["update"] but not for ["drop", "shutdown", "delete",
"truncate", "alter", "unconditional_update"]; "update t set c =
'nowhere'" is destructive for ["unconditional_update"]."""
def is_destructive(queries: str, keywords: CottList[str]) -> bool: ...

"""Upstream parseutils.parse_destructive_warning: convert the
destructive_warning option into the keyword list used by is_destructive.
values is the option value as a list; a plain string option is passed as
a one-element list. BASE is ["drop", "shutdown", "delete", "truncate",
"alter", "unconditional_update"] and ALL is BASE followed by "update".
- An empty list gives [].
- A single element that contains "," gives that element split on ","
  (Python str.split(","), no trimming and no mapping).
- Otherwise map on the first element: "true" and "all" give ALL,
  "moderate" gives BASE, "false", "off" and "" give [], and any other
  first element gives values unchanged."""
def parse_destructive_warning(values: CottList[str]) -> CottList[str]: ...

"""Upstream parseutils.meta.parse_defaults: split the text of
pg_get_expr(pg_proc.proargdefaults, 0) into one default expression per
argument. An empty text gives []. Otherwise scan the characters with
current = "" and quote = none: a space while current is "" is skipped; a
single or double quote character closes the quote when it equals the
open quote, opens a quote when none is open, and is always appended to
current; a "," outside quotes ends the expression (append current to the
result, reset current to "" and do not append the comma); any other
character is appended. After the scan append current. Example:
"1, 'a,b'::text, NULL" gives ["1", "'a,b'::text", "NULL"]."""
def parse_function_defaults(defaults: str) -> CottList[str]: ...

__all__ = ["CteDefinition", "CteExtraction", "CteTable", "IsolatedQuery", "PreviousKeyword", "TableReference", "WordBoundary", "WordBoundary_AllPunctuations", "WordBoundary_AlphanumUnderscore", "WordBoundary_ManyPunctuations", "WordBoundary_MostPunctuations", "extract_ctes", "extract_tables", "find_previous_keyword", "is_destructive", "is_open_quote", "isolate_query_ctes", "last_word", "parse_destructive_warning", "parse_function_defaults", "table_reference_ref"]
