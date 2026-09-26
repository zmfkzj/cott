from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.toolong.text_types import COMBINED_LOG_PATTERN, COMMON_LOG_PATTERN, CompletionTarget, LOG_HIGHLIGHT_PATTERN, LineMatch, SEARCH_SPLIT_PATTERN, SearchWord
from real.toolong.model_types import FindQuery, LineFormat, ParsedLine, StyledSpan, StyledText

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def decode_ansi(line: str) -> StyledText:
    """Exactly rich 13.7.0 Text.from_ansi(line) with its default arguments,
converted to a StyledText: text is the rich Text's plain text and spans are
its spans in order, each rich Style converted to a style code (see
real.toolong.model.StyledSpan). A rich color of type default converts to
the COLOR "default", a standard, 8-bit or Windows color to the COLOR of
TermColor.Indexed with its palette number, and a truecolor color to the
COLOR of TermColor.Rgb. bold, dim, italic, underline and reverse appear
(as the name, or "no" + the name) when the rich style sets them (true or
false); every other rich attribute (blink, strike, links, ...) is
dropped. A span whose converted code is empty is still kept.

Consequences of rich's behavior that must hold: SGR escape sequences
(ESC [ ... m) style the text and are removed; other recognized escape
sequences are removed without styling; the line separators recognized by
str.splitlines (including a lone CR) split the text into lines that are
joined back with LF."""
    line = _cott_normalize_f32_abi(line, str, path="$.line")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/text/decode_ansi.py", "90da6bfdb1527de5f4deb8776d5a37761672bed74ff0ee332b2371f025d2d8c9", "decode_ansi", expected_project_name="toolong", expected_cott_symbol="real.toolong.text.decode_ansi")
        _result = _implementation(line)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.text.decode_ansi"
        if _error.span is None:
            _error.span = {"end_byte":3694,"end_column":1,"end_line":73,"start_byte":2447,"start_column":1,"start_line":49}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.text.decode_ansi", phase="implementation-call", span={"end_byte":3694,"end_column":1,"end_line":73,"start_byte":2447,"start_column":1,"start_line":49}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.text.decode_ansi", phase="implementation-call", span={"end_byte":3694,"end_column":1,"end_line":73,"start_byte":2447,"start_column":1,"start_line":49}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, StyledText, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((not ((not ("\u001b" in line)) and (not ("\r" in line)))) or (len((_result).spans) == 0))), "real.toolong.text.decode_ansi", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.decode_ansi", clause="ensures:1", phase="ensures", span={"end_byte":3676,"end_column":97,"end_line":69,"start_byte":3584,"start_column":5,"start_line":69}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, StyledText, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def highlight_repr(text: StyledText) -> StyledText:
    """Toolong's LogHighlighter applied to a copy of text. When text.text is 10000
or more code points long the text is returned unchanged. Otherwise, for
every match of re.finditer(LOG_HIGHLIGHT_PATTERN, text.text), in match
order, and for every named group of the pattern in the order the groups
appear in the pattern, append a span over the group's match when the group
matched a non-empty string, with the rich 13.7.0 default theme style
"repr.<group name>" as a style code:

ipv4, ipv6, eui48, eui64: "fg:ansibrightgreen bold"
uuid: "fg:ansibrightyellow nobold"
bool_true: "fg:ansibrightgreen italic"
bool_false: "fg:ansibrightred italic"
none: "fg:ansimagenta italic"
number: "fg:ansicyan bold noitalic"
str: "fg:ansigreen nobold noitalic"
path: "fg:ansimagenta"

Existing spans are kept before the new ones."""
    text = _cott_normalize_f32_abi(text, StyledText, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/text/highlight_repr.py", "55c67c0454dedc5873be9a468f967acee39ba7a39d69734f888744d2c17a47ca", "highlight_repr", expected_project_name="toolong", expected_cott_symbol="real.toolong.text.highlight_repr")
        _result = _implementation(text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.text.highlight_repr"
        if _error.span is None:
            _error.span = {"end_byte":4747,"end_column":1,"end_line":100,"start_byte":3694,"start_column":1,"start_line":73}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.text.highlight_repr", phase="implementation-call", span={"end_byte":4747,"end_column":1,"end_line":100,"start_byte":3694,"start_column":1,"start_line":73}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.text.highlight_repr", phase="implementation-call", span={"end_byte":4747,"end_column":1,"end_line":100,"start_byte":3694,"start_column":1,"start_line":73}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, StyledText, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).text == (text).text)), "real.toolong.text.highlight_repr", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.highlight_repr", clause="ensures:1", phase="ensures", span={"end_byte":4682,"end_column":37,"end_line":95,"start_byte":4650,"start_column":5,"start_line":95}, expected="true", actual="false")
        if not (_cott_contract_condition(((len((_result).spans) >= len((text).spans))), "real.toolong.text.highlight_repr", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.highlight_repr", clause="ensures:2", phase="ensures", span={"end_byte":4729,"end_column":47,"end_line":96,"start_byte":4687,"start_column":5,"start_line":96}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, StyledText, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def highlight_json(text: StyledText) -> StyledText:
    """rich 13.7.0 JSONHighlighter applied to a copy of text: its combined brace,
boolean, null, number and string pattern with style prefix "json." (named
groups handled like real.toolong.text.highlight_repr), followed by its key
pass that appends a "json.key" span over every JSON string (matched by the
highlighter's JSON_STR pattern) whose next non-whitespace character (space,
LF, CR or TAB are skipped) is ":". The rich default theme styles as style
codes:

brace: "bold"
bool_true: "fg:ansibrightgreen italic"
bool_false: "fg:ansibrightred italic"
null: "fg:ansimagenta italic"
number: "fg:ansicyan bold noitalic"
str: "fg:ansigreen nobold noitalic"
key: "fg:ansiblue bold"

Existing spans are kept before the new ones; there is no length limit."""
    text = _cott_normalize_f32_abi(text, StyledText, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/text/highlight_json.py", "eafd6545f4866b8a851aca6d76c2c70cd4f14fb87871d46061e9c9f328503594", "highlight_json", expected_project_name="toolong", expected_cott_symbol="real.toolong.text.highlight_json")
        _result = _implementation(text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.text.highlight_json"
        if _error.span is None:
            _error.span = {"end_byte":5734,"end_column":1,"end_line":126,"start_byte":4747,"start_column":1,"start_line":100}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.text.highlight_json", phase="implementation-call", span={"end_byte":5734,"end_column":1,"end_line":126,"start_byte":4747,"start_column":1,"start_line":100}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.text.highlight_json", phase="implementation-call", span={"end_byte":5734,"end_column":1,"end_line":126,"start_byte":4747,"start_column":1,"start_line":100}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, StyledText, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).text == (text).text)), "real.toolong.text.highlight_json", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.highlight_json", clause="ensures:1", phase="ensures", span={"end_byte":5669,"end_column":37,"end_line":121,"start_byte":5637,"start_column":5,"start_line":121}, expected="true", actual="false")
        if not (_cott_contract_condition(((len((_result).spans) >= len((text).spans))), "real.toolong.text.highlight_json", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.highlight_json", clause="ensures:2", phase="ensures", span={"end_byte":5716,"end_column":47,"end_line":122,"start_byte":5674,"start_column":5,"start_line":122}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, StyledText, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def default_line_formats() -> CottList[LineFormat]:
    """The format parser's initial order: Json, CommonLog, CombinedLog, Plain."""
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/text/default_line_formats.py", "5e93cab294f4d0ae98f507b07f9bbe2c95b2bcbf6dc8de8fc1c5d641b42befa6", "default_line_formats", expected_project_name="toolong", expected_cott_symbol="real.toolong.text.default_line_formats")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.text.default_line_formats"
        if _error.span is None:
            _error.span = {"end_byte":5923,"end_column":1,"end_line":135,"start_byte":5734,"start_column":1,"start_line":126}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.text.default_line_formats", phase="implementation-call", span={"end_byte":5923,"end_column":1,"end_line":135,"start_byte":5734,"start_column":1,"start_line":126}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.text.default_line_formats", phase="implementation-call", span={"end_byte":5923,"end_column":1,"end_line":135,"start_byte":5734,"start_column":1,"start_line":126}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[LineFormat], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) == 4)), "real.toolong.text.default_line_formats", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.default_line_formats", clause="ensures:1", phase="ensures", span={"end_byte":5905,"end_column":28,"end_line":131,"start_byte":5882,"start_column":5,"start_line":131}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[LineFormat], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def parse_line(line: str, order: CottList[LineFormat]) -> ParsedLine:
    """Toolong's FormatParser.parse. When line is longer than 10000 code points
only its first 10000 code points are used. Try the formats in the given
order; the first format that accepts the line wins and moves to the front
of the returned order (the order is unchanged when it is already first).

Json: the line with Python str.strip() applied; rejected when that is
empty or json.loads rejects it. Its text is decode_ansi(stripped line)
and, when that has no spans, highlight_json of it. The ParsedLine line is
the stripped line.

CommonLog / CombinedLog: accepted when re.fullmatch(COMMON_LOG_PATTERN,
line) / re.fullmatch(COMBINED_LOG_PATTERN, line) matches. Its text is
decode_ansi(line) and, when that has no spans, highlight_repr of it. Then,
when the match's status group is non-empty, append a span over every
non-overlapping occurrence (re.finditer of re.escape) of " " + status + " "
in the text, styled "fg:ansired bold" when status starts with "4" and
"fg:ansimagenta" otherwise. Then append a span styled "fg:ansiyellow
bold" over every occurrence of the alternation
GET|POST|PUT|HEAD|POST|DELETE|OPTIONS|PATCH (case sensitive,
anywhere in the text). The ParsedLine line is the line.

Plain: always accepts. Its text is decode_ansi(line) and, when that has no
spans, highlight_repr of it. The ParsedLine line is the line.

When no format in order accepts the line (always the case when order is
empty) the result is format Plain, line "", an empty text and order
unchanged. Call real.toolong.text.decode_ansi,
real.toolong.text.highlight_repr and real.toolong.text.highlight_json for
those steps."""
    line = _cott_normalize_f32_abi(line, str, path="$.line")
    order = _cott_normalize_f32_abi(order, CottList[LineFormat], path="$.order")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/text/parse_line.py", "fd437a550a56e363ae6f5532d5f8ba0dd5f28b037e9fbcb0381b5f0ae38eb467", "parse_line", expected_project_name="toolong", expected_cott_symbol="real.toolong.text.parse_line")
        _result = _implementation(line, order)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.text.parse_line"
        if _error.span is None:
            _error.span = {"end_byte":7790,"end_column":1,"end_line":172,"start_byte":5923,"start_column":1,"start_line":135}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.text.parse_line", phase="implementation-call", span={"end_byte":7790,"end_column":1,"end_line":172,"start_byte":5923,"start_column":1,"start_line":135}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.text.parse_line", phase="implementation-call", span={"end_byte":7790,"end_column":1,"end_line":172,"start_byte":5923,"start_column":1,"start_line":135}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, ParsedLine, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len((_result).order) == len(order))), "real.toolong.text.parse_line", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.parse_line", clause="ensures:1", phase="ensures", span={"end_byte":7772,"end_column":42,"end_line":168,"start_byte":7735,"start_column":5,"start_line":168}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, ParsedLine, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def abbreviate_text(text: StyledText, limit: U64) -> StyledText:
    """When text.text has more than limit code points, keep its first limit code
points followed by "…" (U+2026): spans are clipped to [0, limit), spans
left empty are dropped and the ellipsis is unstyled. Otherwise return text
unchanged."""
    text = _cott_normalize_f32_abi(text, StyledText, path="$.text")
    limit = _cott_normalize_f32_abi(limit, U64, path="$.limit")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/text/abbreviate_text.py", "92b583ea67340355729e8fd079718047dc39b78119908b6d6cabf00da17b8fd7", "abbreviate_text", expected_project_name="toolong", expected_cott_symbol="real.toolong.text.abbreviate_text")
        _result = _implementation(text, limit)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.text.abbreviate_text"
        if _error.span is None:
            _error.span = {"end_byte":8265,"end_column":1,"end_line":185,"start_byte":7790,"start_column":1,"start_line":172}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.text.abbreviate_text", phase="implementation-call", span={"end_byte":8265,"end_column":1,"end_line":185,"start_byte":7790,"start_column":1,"start_line":172}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.text.abbreviate_text", phase="implementation-call", span={"end_byte":8265,"end_column":1,"end_line":185,"start_byte":7790,"start_column":1,"start_line":172}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, StyledText, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((not (len((text).text) <= limit)) or (_result == text))), "real.toolong.text.abbreviate_text", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.abbreviate_text", clause="ensures:1", phase="ensures", span={"end_byte":8179,"end_column":55,"end_line":180,"start_byte":8129,"start_column":5,"start_line":180}, expected="true", actual="false")
        if not (_cott_contract_condition((((not (len((text).text) > limit)) or (len((_result).text) == (limit + 1)))), "real.toolong.text.abbreviate_text", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.abbreviate_text", clause="ensures:2", phase="ensures", span={"end_byte":8247,"end_column":68,"end_line":181,"start_byte":8184,"start_column":5,"start_line":181}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, StyledText, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def highlight_find(text: StyledText, query: FindQuery) -> StyledText:
    """Toolong's find highlighting of one displayed line. The match style code is
"fg:#000000 bg:#fea62b".

Regex queries: when query.text is not a valid Python regular expression
the text is returned unchanged. Otherwise every match of
re.finditer(query.text, text.text) (flag re.IGNORECASE unless
case_sensitive) with a non-empty span gets an appended match-style span.

Plain queries: every non-overlapping occurrence of query.text (re.escape;
re.IGNORECASE unless case_sensitive) gets an appended match-style span.

When nothing matched, append instead one span styled "dim" over the whole
text (no span when the text is empty). Existing spans are kept
first. An empty query.text leaves the text unchanged."""
    text = _cott_normalize_f32_abi(text, StyledText, path="$.text")
    query = _cott_normalize_f32_abi(query, FindQuery, path="$.query")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/text/highlight_find.py", "b88be0eba4c27e5459d7e4c1d0bf9149ce6dc371c79487a54d2ff0a344d7175e", "highlight_find", expected_project_name="toolong", expected_cott_symbol="real.toolong.text.highlight_find")
        _result = _implementation(text, query)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.text.highlight_find"
        if _error.span is None:
            _error.span = {"end_byte":9218,"end_column":1,"end_line":208,"start_byte":8265,"start_column":1,"start_line":185}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.text.highlight_find", phase="implementation-call", span={"end_byte":9218,"end_column":1,"end_line":208,"start_byte":8265,"start_column":1,"start_line":185}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.text.highlight_find", phase="implementation-call", span={"end_byte":9218,"end_column":1,"end_line":208,"start_byte":8265,"start_column":1,"start_line":185}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, StyledText, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).text == (text).text)), "real.toolong.text.highlight_find", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.highlight_find", clause="ensures:1", phase="ensures", span={"end_byte":9151,"end_column":37,"end_line":203,"start_byte":9119,"start_column":5,"start_line":203}, expected="true", actual="false")
        if not (_cott_contract_condition((((not ((query).text == "")) or (_result == text))), "real.toolong.text.highlight_find", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.highlight_find", clause="ensures:2", phase="ensures", span={"end_byte":9200,"end_column":49,"end_line":204,"start_byte":9156,"start_column":5,"start_line":204}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, StyledText, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def line_matches(line: str, query: FindQuery) -> LineMatch:
    """Toolong's check_match for find navigation over a raw line. An empty line
matches. Regex queries use re.match(query.text, line) (anchored at the
start of line; re.IGNORECASE unless case_sensitive); when query.text is not
a valid regular expression the line matches and invalid_regex is true.
Plain queries match when query.text is a substring of line, comparing
str.lower() of both unless case_sensitive. invalid_regex is false except
for the invalid-regex case."""
    line = _cott_normalize_f32_abi(line, str, path="$.line")
    query = _cott_normalize_f32_abi(query, FindQuery, path="$.query")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/text/line_matches.py", "7e38d16d0a628b67be035dcf9446eedf9c15b86fbaf20965b56fee9aa5b0ec60", "line_matches", expected_project_name="toolong", expected_cott_symbol="real.toolong.text.line_matches")
        _result = _implementation(line, query)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.text.line_matches"
        if _error.span is None:
            _error.span = {"end_byte":10024,"end_column":1,"end_line":225,"start_byte":9218,"start_column":1,"start_line":208}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.text.line_matches", phase="implementation-call", span={"end_byte":10024,"end_column":1,"end_line":225,"start_byte":9218,"start_column":1,"start_line":208}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.text.line_matches", phase="implementation-call", span={"end_byte":10024,"end_column":1,"end_line":225,"start_byte":9218,"start_column":1,"start_line":208}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, LineMatch, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((not (line == "")) or (_result).matched)), "real.toolong.text.line_matches", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.line_matches", clause="ensures:1", phase="ensures", span={"end_byte":9830,"end_column":43,"end_line":219,"start_byte":9792,"start_column":5,"start_line":219}, expected="true", actual="false")
        if not (_cott_contract_condition((((not (not (query).regex)) or (not (_result).invalid_regex))), "real.toolong.text.line_matches", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.line_matches", clause="ensures:2", phase="ensures", span={"end_byte":9888,"end_column":58,"end_line":220,"start_byte":9835,"start_column":5,"start_line":220}, expected="true", actual="false")
        if not (_cott_contract_condition((((not (((not (query).regex) and (query).case_sensitive) and (line != ""))) or ((_result).matched == ((query).text in line)))), "real.toolong.text.line_matches", "ensures:3")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.line_matches", clause="ensures:3", phase="ensures", span={"end_byte":10006,"end_column":118,"end_line":221,"start_byte":9893,"start_column":5,"start_line":221}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, LineMatch, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def pretty_json(line: str) -> Option[StyledText]:
    """The line panel's JSON view. When json.loads(line) succeeds, return the
text of rich 13.7.0 JSON.from_data(value) with its defaults (indent 2,
ensure_ascii false, keys in document order): the json.dumps text,
highlighted as real.toolong.text.highlight_json does (call it). Lines of
the result are separated by LF. Nothing when json.loads fails."""
    line = _cott_normalize_f32_abi(line, str, path="$.line")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/text/pretty_json.py", "b7155f321348e9bdef59fd618c1e6dd553e5cab594b1d23839fa5ee181c8ffc0", "pretty_json", expected_project_name="toolong", expected_cott_symbol="real.toolong.text.pretty_json")
        _result = _implementation(line)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.text.pretty_json"
        if _error.span is None:
            _error.span = {"end_byte":10474,"end_column":1,"end_line":236,"start_byte":10024,"start_column":1,"start_line":225}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.text.pretty_json", phase="implementation-call", span={"end_byte":10474,"end_column":1,"end_line":236,"start_byte":10024,"start_column":1,"start_line":225}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.text.pretty_json", phase="implementation-call", span={"end_byte":10474,"end_column":1,"end_line":236,"start_byte":10024,"start_column":1,"start_line":225}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Option[StyledText], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Option[StyledText], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def wrap_text(text: StyledText, width: U16) -> CottList[StyledText]:
    """Word-wrap styled text as a Textual label does: exactly rich 13.7.0
Text.wrap(console, width) with default justify and overflow ("fold") and
tab size 8. The text is split at LF; each line is broken before words that
would exceed width cells, words longer than width are folded, trailing
whitespace beyond width is removed, and an empty line stays one empty
line. Each resulting line keeps its styles with spans relative to the
line. A width of 0 is treated as 1."""
    text = _cott_normalize_f32_abi(text, StyledText, path="$.text")
    width = _cott_normalize_f32_abi(width, U16, path="$.width")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/text/wrap_text.py", "6cd8180892fb8277020fa1538b6589400a7997b6fc1010520332d7ab4af56440", "wrap_text", expected_project_name="toolong", expected_cott_symbol="real.toolong.text.wrap_text")
        _result = _implementation(text, width)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.text.wrap_text"
        if _error.span is None:
            _error.span = {"end_byte":11094,"end_column":1,"end_line":251,"start_byte":10474,"start_column":1,"start_line":236}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.text.wrap_text", phase="implementation-call", span={"end_byte":11094,"end_column":1,"end_line":251,"start_byte":10474,"start_column":1,"start_line":236}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.text.wrap_text", phase="implementation-call", span={"end_byte":11094,"end_column":1,"end_line":251,"start_byte":10474,"start_column":1,"start_line":236}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[StyledText], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) >= 1)), "real.toolong.text.wrap_text", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.wrap_text", clause="ensures:1", phase="ensures", span={"end_byte":11076,"end_column":28,"end_line":247,"start_byte":11053,"start_column":5,"start_line":247}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[StyledText], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def search_words(plain: str) -> CottList[SearchWord]:
    """The find-suggestion words of one rendered line, in Toolong's order: for
every piece of re.split(SEARCH_SPLIT_PATTERN, plain) that is longer than one
code point, and for every offset from 1 up to and excluding len(piece) - 1,
one SearchWord with prefix piece[:offset] and word piece."""
    plain = _cott_normalize_f32_abi(plain, str, path="$.plain")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/text/search_words.py", "e25af6d82496e712b9cd6359931263420871257a0b11a7dee7fbebee0817e134", "search_words", expected_project_name="toolong", expected_cott_symbol="real.toolong.text.search_words")
        _result = _implementation(plain)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.text.search_words"
        if _error.span is None:
            _error.span = {"end_byte":11479,"end_column":1,"end_line":261,"start_byte":11094,"start_column":1,"start_line":251}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.text.search_words", phase="implementation-call", span={"end_byte":11479,"end_column":1,"end_line":261,"start_byte":11094,"start_column":1,"start_line":251}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.text.search_words", phase="implementation-call", span={"end_byte":11479,"end_column":1,"end_line":261,"start_byte":11094,"start_column":1,"start_line":251}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[SearchWord], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[SearchWord], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def completion_target(value: str) -> Option[CompletionTarget]:
    """What a find suggestion completes: word is the last piece of
re.split(SEARCH_SPLIT_PATTERN, value) and start is value without that last
word (value[:len(value) - len(word)]). Nothing when word is empty."""
    value = _cott_normalize_f32_abi(value, str, path="$.value")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/text/completion_target.py", "8e220f5f5e5bd79b949a9af0be5ee905ee54299ae788ba99faab1aace8b77d86", "completion_target", expected_project_name="toolong", expected_cott_symbol="real.toolong.text.completion_target")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.text.completion_target"
        if _error.span is None:
            _error.span = {"end_byte":11846,"end_column":1,"end_line":272,"start_byte":11479,"start_column":1,"start_line":261}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.text.completion_target", phase="implementation-call", span={"end_byte":11846,"end_column":1,"end_line":272,"start_byte":11479,"start_column":1,"start_line":261}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.text.completion_target", phase="implementation-call", span={"end_byte":11846,"end_column":1,"end_line":272,"start_byte":11479,"start_column":1,"start_line":261}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Option[CompletionTarget], path="$.return")
    if _cott_test_context:
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Some and True:
                target = _cott_match_value.value
                return (_cott_contract_condition((((target).word != "")), "real.toolong.text.completion_target", "ensures:1"))
            _cott_contract_condition((False), "real.toolong.text.completion_target", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.text.completion_target", clause="ensures:1", phase="ensures", span={"end_byte":11828,"end_column":53,"end_line":268,"start_byte":11780,"start_column":5,"start_line":268}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[CompletionTarget], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["COMBINED_LOG_PATTERN", "COMMON_LOG_PATTERN", "CompletionTarget", "LOG_HIGHLIGHT_PATTERN", "LineMatch", "SEARCH_SPLIT_PATTERN", "SearchWord", "abbreviate_text", "completion_target", "decode_ansi", "default_line_formats", "highlight_find", "highlight_json", "highlight_repr", "line_matches", "parse_line", "pretty_json", "search_words", "wrap_text"]
