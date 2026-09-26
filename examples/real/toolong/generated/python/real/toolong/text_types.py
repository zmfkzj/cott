from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.toolong.model_types import FindQuery, LineFormat, ParsedLine, StyledSpan, StyledText

"""Toolong's LogHighlighter pattern: the alternation of its named-group regular
expressions, applied with style prefix "repr."."""
LOG_HIGHLIGHT_PATTERN: Final[str] = "(?P<ipv4>[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3})|(?P<ipv6>([A-Fa-f0-9]{1,4}::?){1,7}[A-Fa-f0-9]{1,4})|(?P<eui64>(?:[0-9A-Fa-f]{1,2}-){7}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{1,2}:){7}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{4}\\.){3}[0-9A-Fa-f]{4})|(?P<eui48>(?:[0-9A-Fa-f]{1,2}-){5}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{1,2}:){5}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{4}\\.){2}[0-9A-Fa-f]{4})|(?P<uuid>[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})|\\b(?P<bool_true>True)\\b|\\b(?P<bool_false>False)\\b|\\b(?P<none>None)\\b|(?P<number>(?<!\\w)\\-?[0-9]+\\.?[0-9]*(e[-+]?\\d+?)?\\b|0x[0-9a-fA-F]*)|(?<![\\\\\\w])(?P<str>b?'''.*?(?<!\\\\)'''|b?'.*?(?<!\\\\)'|b?\\\"\\\"\\\".*?(?<!\\\\)\\\"\\\"\\\"|b?\\\".*?(?<!\\\\)\\\")|(?P<path>\\[.*?\\])"

"""Toolong's CommonLogFormat regular expression (matched with re.fullmatch)."""
COMMON_LOG_PATTERN: Final[str] = "(?P<ip>.*?) (?P<remote_log_name>.*?) (?P<userid>.*?) (?P<date>\\[.*?(?= ).*?\\]) \"(?P<request_method>.*?) (?P<path>.*?)(?P<request_version> HTTP\\/.*)?\" (?P<status>.*?) (?P<length>.*?) \"(?P<referrer>.*?)\""

"""Toolong's CombinedLogFormat regular expression (matched with re.fullmatch)."""
COMBINED_LOG_PATTERN: Final[str] = "(?P<ip>.*?) (?P<remote_log_name>.*?) (?P<userid>.*?) \\[(?P<date>.*?)(?= ) (?P<timezone>.*?)\\] \"(?P<request_method>.*?) (?P<path>.*?)(?P<request_version> HTTP\\/.*)?\" (?P<status>.*?) (?P<length>.*?) \"(?P<referrer>.*?)\" \"(?P<user_agent>.*?)\" (?P<session_id>.*?) (?P<generation_time_micro>.*?) (?P<virtual_host>.*)"

"""The regular expression Toolong splits rendered lines and find input with to
find words for find suggestions."""
SEARCH_SPLIT_PATTERN: Final[str] = "[\\s/\\[\\]\\(\\)\\\"\\/]"

"""A word seen in a rendered line and one of its prefixes, for find suggestions."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SearchWord:
    __hash__ = None
    prefix: str
    word: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "prefix", _cott_validate_abi(self.prefix, str, path="$.prefix"))
        if not _cott_validated_construction():
            object.__setattr__(self, "word", _cott_validate_abi(self.word, str, path="$.word"))

"""The part of a find input value that a suggestion completes: the text before
the last word and the last word."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CompletionTarget:
    __hash__ = None
    start: str
    word: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "start", _cott_validate_abi(self.start, str, path="$.start"))
        if not _cott_validated_construction():
            object.__setattr__(self, "word", _cott_validate_abi(self.word, str, path="$.word"))

"""The outcome of testing one raw line against the find query."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LineMatch:
    __hash__ = None
    matched: bool
    invalid_regex: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "matched", _cott_validate_abi(self.matched, bool, path="$.matched"))
        if not _cott_validated_construction():
            object.__setattr__(self, "invalid_regex", _cott_validate_abi(self.invalid_regex, bool, path="$.invalid_regex"))

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
"""The format parser's initial order: Json, CommonLog, CombinedLog, Plain."""
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
"""When text.text has more than limit code points, keep its first limit code
points followed by "…" (U+2026): spans are clipped to [0, limit), spans
left empty are dropped and the ellipsis is unstyled. Otherwise return text
unchanged."""
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
"""Toolong's check_match for find navigation over a raw line. An empty line
matches. Regex queries use re.match(query.text, line) (anchored at the
start of line; re.IGNORECASE unless case_sensitive); when query.text is not
a valid regular expression the line matches and invalid_regex is true.
Plain queries match when query.text is a substring of line, comparing
str.lower() of both unless case_sensitive. invalid_regex is false except
for the invalid-regex case."""
"""The line panel's JSON view. When json.loads(line) succeeds, return the
text of rich 13.7.0 JSON.from_data(value) with its defaults (indent 2,
ensure_ascii false, keys in document order): the json.dumps text,
highlighted as real.toolong.text.highlight_json does (call it). Lines of
the result are separated by LF. Nothing when json.loads fails."""
"""Word-wrap styled text as a Textual label does: exactly rich 13.7.0
Text.wrap(console, width) with default justify and overflow ("fold") and
tab size 8. The text is split at LF; each line is broken before words that
would exceed width cells, words longer than width are folded, trailing
whitespace beyond width is removed, and an empty line stays one empty
line. Each resulting line keeps its styles with spans relative to the
line. A width of 0 is treated as 1."""
"""The find-suggestion words of one rendered line, in Toolong's order: for
every piece of re.split(SEARCH_SPLIT_PATTERN, plain) that is longer than one
code point, and for every offset from 1 up to and excluding len(piece) - 1,
one SearchWord with prefix piece[:offset] and word piece."""
"""What a find suggestion completes: word is the last piece of
re.split(SEARCH_SPLIT_PATTERN, value) and start is value without that last
word (value[:len(value) - len(word)]). Nothing when word is empty."""
__all__ = ["COMBINED_LOG_PATTERN", "COMMON_LOG_PATTERN", "CompletionTarget", "LOG_HIGHLIGHT_PATTERN", "LineMatch", "SEARCH_SPLIT_PATTERN", "SearchWord"]
