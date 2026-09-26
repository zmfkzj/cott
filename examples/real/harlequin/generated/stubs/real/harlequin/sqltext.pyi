from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.sqltext_types import FormatError as FormatError, FormatError_Unformattable as FormatError_Unformattable, REDACTED as REDACTED, TextEdit as TextEdit, TextRange as TextRange
"""Split a SQL script into its statements, in order, the way Harlequin's editor
and hsql both split one. A separator is a ";" that is not inside:
a single-quoted string '...' (a doubled '' continues it; a backslash does not
escape), a double-quoted identifier "..." (doubled "" continues it), a
backtick identifier `...`, a line comment from -- to the end of the line, a
block comment /* ... */ (not nested: the first */ closes it), or a dollar-quoted body
$tag$ ... $tag$, where tag is empty or an identifier ([A-Za-z_][A-Za-z0-9_]*)
and the body ends only at the same $tag$ spelling (a different $other$ is
body content). An unterminated quote, comment or dollar body runs to the end
of the text and hides every later ";".
Each statement is the text from just after the previous separator (or the
start) through its own ";" inclusive, or to the end of the text for the last
piece, with surrounding whitespace (str.strip()) removed. It keeps its
trailing ";". Pieces that are empty after stripping are dropped, so blank
lines produce no statement; a piece that is only ";" (from repeated
separators) is kept as the statement ";", as in Harlequin. Text without any
nonblank piece returns an empty list. Comments are statement content: a
piece holding only a comment is a statement."""
def split_statements(text: str) -> CottList[str]: ...

"""The character offsets just past each separator ";" of text, in ascending
order, using exactly the separator rules of split_statements."""
def separator_offsets(text: str) -> CottList[U64]: ...

"""The queries the Run Query action submits, exactly as Harlequin's code editor
chooses them. selection is the editor selection normalized so start <= end
(a bare cursor has start == end).
1. If text.strip() is empty, return [].
2. If text contains no ";" at all, or separator_offsets(text) is empty,
   return [text] (the whole buffer, unstripped).
3. Otherwise build the query list: boundaries are 0, every separator offset
   and len(text); for each consecutive pair (query_start, query_end) the
   query is text[query_start:query_end].strip(); keep only nonempty ones,
   remembering each kept query's (query_start, query_end).
4. If no query was kept, return [].
5. The queries whose range overlaps the selection, meaning
   query_start < selection.end and query_end > selection.start, in order,
   when there is at least one (a bare cursor overlaps only a query it sits
   strictly inside).
6. Otherwise the first kept query whose query_end >= selection.start.
7. Otherwise (the cursor is in trailing whitespace after the last query) the
   last kept query.
Queries keep their trailing ";"."""
def selected_queries(text: str, selection: TextRange) -> CottList[str]: ...

"""Toggle SQL line comments on the lines the selection touches (Ctrl+/ in
Harlequin's editor). Lines are split on "\\n". The touched lines run from the
line holding selection.start to the line holding selection.end; when the
selection is nonempty and selection.end is exactly at the start of a line,
that last line is not touched. Blank lines (only spaces and tabs) are
ignored when deciding and are never changed.
If every touched nonblank line, after its leading spaces and tabs, starts
with "--", uncomment: remove "-- " when the text after the indentation starts
with "-- ", otherwise remove "--". Otherwise comment: let indent be the
smallest leading-whitespace width among the touched nonblank lines and insert
"-- " at that column of each touched nonblank line. If there is no touched
nonblank line, the text is unchanged.
The returned anchor and cursor are selection.start and selection.end moved
by the net number of characters inserted at or before them and removed
before them (an offset inside a removed marker moves to the marker's start).
text is otherwise unchanged, including the presence or absence of a final
newline. A TextRange is an editor selection into text, so its end must not
exceed the number of Unicode scalar values in text."""
def toggle_comment(text: str, selection: TextRange) -> TextEdit: ...

"""Format text with shandy-sqlfmt exactly like Harlequin's Format Query action:
sqlfmt.api.format_string(text, sqlfmt.mode.Mode()) with the default mode
(line length 88, lowercase keywords). Text that is already formatted comes
back unchanged. Any sqlfmt error (for example unbalanced brackets or an
unterminated string) is Unformattable(message) with the error's message."""
def format_sql(text: str) -> Result[str, FormatError]: ...

"""The range of the completion prefix ending at cursor: the longest run of
characters immediately before cursor that are letters, digits, "_", "$", ".",
or double quotes. The range ends at cursor (clamped to len(text))."""
def word_at_cursor(text: str, cursor: U64) -> TextRange: ...

"""Mask the credentials in one connection string, leaving the rest readable:
1. URI passwords: the password in scheme://user:password@host, matched by
   the regular expression ://[^/?#@\\s]*?:([^/?#@\\s]+)@ (group 1).
2. DSN pairs: a key containing (case-insensitively) one of password, passwd,
   pwd, secret, token, api[_-]?key, access[_-]?key, private[_-]?key, possibly
   with surrounding [\\w.\\-] characters, then "=" with optional spaces, then a
   value in single quotes, double quotes, or bare up to "&", ";" or
   whitespace; the value (without its quotes) is the secret.
Each secret span is replaced, by position, with REDACTED; a span that
overlaps one already replaced (scanning from the end of the text) is skipped
so quotes are never eaten."""
def redact_connection_string(connection: str) -> str: ...

"""Mask credentials inside one SQL statement before it is logged or shown in the
query history: first replace every element of secrets that is at least 4
characters long with REDACTED (longest first), then mask, by position, the
spans redact_connection_string masks and every quoted literal that follows a
credential-like name: [\\w.]*(<secret name alternatives>|key[_-]?id)[\\w.]*
then an optional "=" with optional spaces, then '...'; the text between the
quotes is masked."""
def redact_sql(sql: str, secrets: CottList[str]) -> str: ...

"""Replace every element of secrets that is at least 4 characters long, longest
first, with REDACTED wherever it appears in text. Shorter secrets are left
alone so short values do not mangle prose."""
def redact_text(text: str, secrets: CottList[str]) -> str: ...

"""The "did you mean" suggestions Harlequin draws from difflib.get_close_matches
(cutoff 0.6), computed here without difflib. The similarity of word and a
candidate is 2*M/(len(word)+len(candidate)) (1.0 when both are empty),
where M is the total length of the matching blocks: find the longest common
contiguous substring (on ties the one starting earliest in word, then
earliest in candidate), add its length, and repeat on the parts left of it
and right of it. Candidates with similarity >= 0.6 are returned best first,
equal similarities ordered by the candidate string descending, at most
limit of them."""
def close_matches(word: str, candidates: CottList[str], limit: U64) -> CottList[str]: ...

__all__ = ["FormatError", "FormatError_Unformattable", "REDACTED", "TextEdit", "TextRange", "close_matches", "format_sql", "redact_connection_string", "redact_sql", "redact_text", "selected_queries", "separator_offsets", "split_statements", "toggle_comment", "word_at_cursor"]
