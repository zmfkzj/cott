from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.harlequin.sqltext_types import FormatError, FormatError_Unformattable, REDACTED, TextEdit, TextRange

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def split_statements(text: str) -> CottList[str]:
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
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/sqltext/split_statements.py", "57443cb468892e9075d1f0a2b96513e2cf1f4d5dc62f94308f321d25b820bea5", "split_statements", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.sqltext.split_statements")
        _result = _implementation(text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.sqltext.split_statements"
        if _error.span is None:
            _error.span = {"end_byte":2002,"end_column":1,"end_line":50,"start_byte":569,"start_column":1,"start_line":26}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.sqltext.split_statements", phase="implementation-call", span={"end_byte":2002,"end_column":1,"end_line":50,"start_byte":569,"start_column":1,"start_line":26}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.sqltext.split_statements", phase="implementation-call", span={"end_byte":2002,"end_column":1,"end_line":50,"start_byte":569,"start_column":1,"start_line":26}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def separator_offsets(text: str) -> CottList[U64]:
    """The character offsets just past each separator ";" of text, in ascending
order, using exactly the separator rules of split_statements."""
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/sqltext/separator_offsets.py", "ebd91daac401a91dc1267c23b044224d79cfd4c82e5fce3a217ea3b446a3a415", "separator_offsets", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.sqltext.separator_offsets")
        _result = _implementation(text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.sqltext.separator_offsets"
        if _error.span is None:
            _error.span = {"end_byte":2264,"end_column":1,"end_line":60,"start_byte":2002,"start_column":1,"start_line":50}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.sqltext.separator_offsets", phase="implementation-call", span={"end_byte":2264,"end_column":1,"end_line":60,"start_byte":2002,"start_column":1,"start_line":50}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.sqltext.separator_offsets", phase="implementation-call", span={"end_byte":2264,"end_column":1,"end_line":60,"start_byte":2002,"start_column":1,"start_line":50}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[U64], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) <= len(text))), "real.harlequin.sqltext.separator_offsets", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.sqltext.separator_offsets", clause="ensures:1", phase="ensures", span={"end_byte":2246,"end_column":35,"end_line":56,"start_byte":2216,"start_column":5,"start_line":56}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[U64], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def selected_queries(text: str, selection: TextRange) -> CottList[str]:
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
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    selection = _cott_normalize_f32_abi(selection, TextRange, path="$.selection")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/sqltext/selected_queries.py", "1e00f571dc00eb8b8bd98bae2f693649c6fd242e24e90be30e3fcf4a95fd78f4", "selected_queries", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.sqltext.selected_queries")
        _result = _implementation(text, selection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.sqltext.selected_queries"
        if _error.span is None:
            _error.span = {"end_byte":3584,"end_column":1,"end_line":87,"start_byte":2264,"start_column":1,"start_line":60}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.sqltext.selected_queries", phase="implementation-call", span={"end_byte":3584,"end_column":1,"end_line":87,"start_byte":2264,"start_column":1,"start_line":60}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.sqltext.selected_queries", phase="implementation-call", span={"end_byte":3584,"end_column":1,"end_line":87,"start_byte":2264,"start_column":1,"start_line":60}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[str], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((not (len(text) == 0)) or (len(_result) == 0))), "real.harlequin.sqltext.selected_queries", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.sqltext.selected_queries", clause="ensures:1", phase="ensures", span={"end_byte":3566,"end_column":45,"end_line":83,"start_byte":3526,"start_column":5,"start_line":83}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def toggle_comment(text: str, selection: TextRange) -> TextEdit:
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
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    selection = _cott_normalize_f32_abi(selection, TextRange, path="$.selection")
    if _cott_test_context:
        if not (_cott_contract_condition((((selection).end <= len(text))), "real.harlequin.sqltext.toggle_comment", "requires:1")):
            raise CottContractViolation("requires clause failed", symbol="real.harlequin.sqltext.toggle_comment", clause="requires:1", phase="requires", span={"end_byte":5029,"end_column":39,"end_line":109,"start_byte":4995,"start_column":5,"start_line":109}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/sqltext/toggle_comment.py", "5a0f3320d26b39e7e56d17a7cd79685c6132bbe3f5d0f3a5246eefb091c1a212", "toggle_comment", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.sqltext.toggle_comment")
        _result = _implementation(text, selection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.sqltext.toggle_comment"
        if _error.span is None:
            _error.span = {"end_byte":5047,"end_column":1,"end_line":113,"start_byte":3584,"start_column":1,"start_line":87}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.sqltext.toggle_comment", phase="implementation-call", span={"end_byte":5047,"end_column":1,"end_line":113,"start_byte":3584,"start_column":1,"start_line":87}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.sqltext.toggle_comment", phase="implementation-call", span={"end_byte":5047,"end_column":1,"end_line":113,"start_byte":3584,"start_column":1,"start_line":87}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TextEdit, path="$.return")
    _result = _cott_wrap_async_protocol(_result, TextEdit, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def format_sql(text: str) -> Result[str, FormatError]:
    """Format text with shandy-sqlfmt exactly like Harlequin's Format Query action:
sqlfmt.api.format_string(text, sqlfmt.mode.Mode()) with the default mode
(line length 88, lowercase keywords). Text that is already formatted comes
back unchanged. Any sqlfmt error (for example unbalanced brackets or an
unterminated string) is Unformattable(message) with the error's message."""
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/sqltext/format_sql.py", "955db1ba0c9b7e2dc89331c19b8691b712f79abae8d1560dd5c1a9b4ee98de52", "format_sql", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.sqltext.format_sql")
        _result = _implementation(text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.sqltext.format_sql"
        if _error.span is None:
            _error.span = {"end_byte":5621,"end_column":1,"end_line":128,"start_byte":5047,"start_column":1,"start_line":113}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.sqltext.format_sql", phase="implementation-call", span={"end_byte":5621,"end_column":1,"end_line":128,"start_byte":5047,"start_column":1,"start_line":113}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.sqltext.format_sql", phase="implementation-call", span={"end_byte":5621,"end_column":1,"end_line":128,"start_byte":5047,"start_column":1,"start_line":113}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[str, FormatError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.sqltext.format_sql", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (FormatError_Unformattable,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.sqltext.format_sql", phase="error", span={"end_byte":5621,"end_column":1,"end_line":128,"start_byte":5047,"start_column":1,"start_line":113}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.sqltext.format_sql", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.sqltext.format_sql", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is FormatError_Unformattable:
            _cott_contract_condition(True, "real.harlequin.sqltext.format_sql", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                formatted = _cott_match_value.value
                return (_cott_contract_condition(((len(formatted) >= 0)), "real.harlequin.sqltext.format_sql", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.sqltext.format_sql", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.sqltext.format_sql", clause="ensures:1", phase="ensures", span={"end_byte":5566,"end_column":55,"end_line":122,"start_byte":5516,"start_column":5,"start_line":122}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, FormatError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def word_at_cursor(text: str, cursor: U64) -> TextRange:
    """The range of the completion prefix ending at cursor: the longest run of
characters immediately before cursor that are letters, digits, "_", "$", ".",
or double quotes. The range ends at cursor (clamped to len(text))."""
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    cursor = _cott_normalize_f32_abi(cursor, U64, path="$.cursor")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/sqltext/word_at_cursor.py", "00ac9c0ad921d9a353970e1b927035a87a547b15987b35c9e5dca3d6ccf11a64", "word_at_cursor", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.sqltext.word_at_cursor")
        _result = _implementation(text, cursor)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.sqltext.word_at_cursor"
        if _error.span is None:
            _error.span = {"end_byte":5979,"end_column":1,"end_line":139,"start_byte":5621,"start_column":1,"start_line":128}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.sqltext.word_at_cursor", phase="implementation-call", span={"end_byte":5979,"end_column":1,"end_line":139,"start_byte":5621,"start_column":1,"start_line":128}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.sqltext.word_at_cursor", phase="implementation-call", span={"end_byte":5979,"end_column":1,"end_line":139,"start_byte":5621,"start_column":1,"start_line":128}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TextRange, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).end <= len(text))), "real.harlequin.sqltext.word_at_cursor", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.sqltext.word_at_cursor", clause="ensures:1", phase="ensures", span={"end_byte":5961,"end_column":35,"end_line":135,"start_byte":5931,"start_column":5,"start_line":135}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TextRange, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def redact_connection_string(connection: str) -> str:
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
    connection = _cott_normalize_f32_abi(connection, str, path="$.connection")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/sqltext/redact_connection_string.py", "d7df6081f4c704fe1e4441e54af6d022d2aa2d4c8f44a3255e6eed4f4e46336a", "redact_connection_string", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.sqltext.redact_connection_string")
        _result = _implementation(connection)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.sqltext.redact_connection_string"
        if _error.span is None:
            _error.span = {"end_byte":6897,"end_column":1,"end_line":158,"start_byte":6013,"start_column":1,"start_line":141}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.sqltext.redact_connection_string", phase="implementation-call", span={"end_byte":6897,"end_column":1,"end_line":158,"start_byte":6013,"start_column":1,"start_line":141}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.sqltext.redact_connection_string", phase="implementation-call", span={"end_byte":6897,"end_column":1,"end_line":158,"start_byte":6013,"start_column":1,"start_line":141}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def redact_sql(sql: str, secrets: CottList[str]) -> str:
    """Mask credentials inside one SQL statement before it is logged or shown in the
query history: first replace every element of secrets that is at least 4
characters long with REDACTED (longest first), then mask, by position, the
spans redact_connection_string masks and every quoted literal that follows a
credential-like name: [\\w.]*(<secret name alternatives>|key[_-]?id)[\\w.]*
then an optional "=" with optional spaces, then '...'; the text between the
quotes is masked."""
    sql = _cott_normalize_f32_abi(sql, str, path="$.sql")
    secrets = _cott_normalize_f32_abi(secrets, CottList[str], path="$.secrets")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/sqltext/redact_sql.py", "8f73a08be8215df7a98f96984aa0855edf2dabd8db52813104a4dd1931394d64", "redact_sql", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.sqltext.redact_sql")
        _result = _implementation(sql, secrets)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.sqltext.redact_sql"
        if _error.span is None:
            _error.span = {"end_byte":7485,"end_column":1,"end_line":171,"start_byte":6897,"start_column":1,"start_line":158}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.sqltext.redact_sql", phase="implementation-call", span={"end_byte":7485,"end_column":1,"end_line":171,"start_byte":6897,"start_column":1,"start_line":158}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.sqltext.redact_sql", phase="implementation-call", span={"end_byte":7485,"end_column":1,"end_line":171,"start_byte":6897,"start_column":1,"start_line":158}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def redact_text(text: str, secrets: CottList[str]) -> str:
    """Replace every element of secrets that is at least 4 characters long, longest
first, with REDACTED wherever it appears in text. Shorter secrets are left
alone so short values do not mangle prose."""
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    secrets = _cott_normalize_f32_abi(secrets, CottList[str], path="$.secrets")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/sqltext/redact_text.py", "b09db6b427741d924a7c390720d4eddb526f9ad4bebf827e21bf066e1df31dfd", "redact_text", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.sqltext.redact_text")
        _result = _implementation(text, secrets)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.sqltext.redact_text"
        if _error.span is None:
            _error.span = {"end_byte":7783,"end_column":1,"end_line":180,"start_byte":7485,"start_column":1,"start_line":171}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.sqltext.redact_text", phase="implementation-call", span={"end_byte":7783,"end_column":1,"end_line":180,"start_byte":7485,"start_column":1,"start_line":171}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.sqltext.redact_text", phase="implementation-call", span={"end_byte":7783,"end_column":1,"end_line":180,"start_byte":7485,"start_column":1,"start_line":171}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def close_matches(word: str, candidates: CottList[str], limit: U64) -> CottList[str]:
    """The "did you mean" suggestions Harlequin draws from difflib.get_close_matches
(cutoff 0.6), computed here without difflib. The similarity of word and a
candidate is 2*M/(len(word)+len(candidate)) (1.0 when both are empty),
where M is the total length of the matching blocks: find the longest common
contiguous substring (on ties the one starting earliest in word, then
earliest in candidate), add its length, and repeat on the parts left of it
and right of it. Candidates with similarity >= 0.6 are returned best first,
equal similarities ordered by the candidate string descending, at most
limit of them."""
    word = _cott_normalize_f32_abi(word, str, path="$.word")
    candidates = _cott_normalize_f32_abi(candidates, CottList[str], path="$.candidates")
    limit = _cott_normalize_f32_abi(limit, U64, path="$.limit")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/sqltext/close_matches.py", "c47a0c41a5e093ea934cc302b0396ace823a7d7341e3c981db99b0e90e962209", "close_matches", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.sqltext.close_matches")
        _result = _implementation(word, candidates, limit)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.sqltext.close_matches"
        if _error.span is None:
            _error.span = {"end_byte":8572,"end_column":1,"end_line":197,"start_byte":7783,"start_column":1,"start_line":180}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.sqltext.close_matches", phase="implementation-call", span={"end_byte":8572,"end_column":1,"end_line":197,"start_byte":7783,"start_column":1,"start_line":180}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.sqltext.close_matches", phase="implementation-call", span={"end_byte":8572,"end_column":1,"end_line":197,"start_byte":7783,"start_column":1,"start_line":180}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[str], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) <= limit)), "real.harlequin.sqltext.close_matches", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.sqltext.close_matches", clause="ensures:1", phase="ensures", span={"end_byte":8554,"end_column":32,"end_line":193,"start_byte":8527,"start_column":5,"start_line":193}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["FormatError", "FormatError_Unformattable", "REDACTED", "TextEdit", "TextRange", "close_matches", "format_sql", "redact_connection_string", "redact_sql", "redact_text", "selected_queries", "separator_offsets", "split_statements", "toggle_comment", "word_at_cursor"]
