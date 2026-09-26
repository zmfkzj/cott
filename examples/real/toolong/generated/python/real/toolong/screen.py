from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.toolong.screen_types import Cursor, FindDialogView, Frame, FrameContent, PlacedRows, ThemeColor, ThemeColor_Accent, ThemeColor_AccentDark, ThemeColor_Background, ThemeColor_Black, ThemeColor_Error, ThemeColor_ErrorDark, ThemeColor_LineNumber, ThemeColor_Muted, ThemeColor_Panel, ThemeColor_Primary, ThemeColor_Success, ThemeColor_SuccessDark, ThemeColor_Surface, ThemeColor_TailBackground, ThemeColor_Text, ThemeColor_Thumb, ThemeColor_Track, ThemeColor_Underline, ThemeColor_Warning, ThemeColor_WarningDark
from real.toolong.keys_types import TextInput
from real.toolong.model_types import Rect, ScreenRow, StyledRun, StyledText, TermColor
from real.toolong.view_types import Focus, FooterKey, Notification, TabView, ViewerLayout, ViewerState

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def theme_color(color: ThemeColor) -> TermColor:
    """The RGB value (TermColor.Rgb) of each theme color: Surface (30, 30, 30),
Background (18, 18, 18), Text (225, 225, 225), Muted (115, 115, 115),
Accent (1, 120, 212), AccentDark (0, 83, 170), Panel (36, 41, 47), Primary
(0, 69, 120), Warning (254, 166, 43), Success (78, 191, 113), Error (185,
60, 91), LineNumber (186, 125, 39), TailBackground (37, 54, 42), Track (20,
25, 31), Thumb (35, 86, 139), Underline (51, 51, 51), Black (0, 0, 0),
SuccessDark (54, 170, 94), WarningDark (231, 146, 13), ErrorDark (163, 37,
73). Screen renderers write theme colors into cell codes (see
real.toolong.model.StyledRun) as "#" + lowercase hex, e.g. Text on
Surface is "fg:#e1e1e1 bg:#1e1e1e"."""
    color = _cott_normalize_f32_abi(color, ThemeColor, path="$.color")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/screen/theme_color.py", "16449768337c2f9f2c0890111f5fd5dc9aca26015b11eec8538011228935eb9b", "theme_color", expected_project_name="toolong", expected_cott_symbol="real.toolong.screen.theme_color")
        _result = _implementation(color)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.screen.theme_color"
        if _error.span is None:
            _error.span = {"end_byte":3362,"end_column":1,"end_line":114,"start_byte":2558,"start_column":1,"start_line":98}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.screen.theme_color", phase="implementation-call", span={"end_byte":3362,"end_column":1,"end_line":114,"start_byte":2558,"start_column":1,"start_line":98}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.screen.theme_color", phase="implementation-call", span={"end_byte":3362,"end_column":1,"end_line":114,"start_byte":2558,"start_column":1,"start_line":98}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TermColor, path="$.return")
    _result = _cott_wrap_async_protocol(_result, TermColor, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def text_runs(text: StyledText, base: str, offset: U64, width: U16, fill: str) -> CottList[StyledRun]:
    """Draw styled text into exactly width cells, starting at cell offset of the
text (horizontal scrolling). base and fill are cell codes (see
real.toolong.model.StyledRun). Each code point's style is base with the
style codes of the spans that cover it applied in list order: a "fg:" /
"bg:" token sets that color (the COLOR "default" meaning base's color),
an attribute name sets the attribute and "no" + the name clears it. The
resulting cell code lists fg, bg and the attributes that are on, in the
canonical token order. Each code point takes
rich.cells.get_character_cell_size(code point) cells; zero-width code
points are not drawn. Of the text's cells, those in [offset, offset +
width) are drawn; a double-width character cut by either edge shows as one
space in its style for its visible cell. Cells left after the text are
spaces in fill. Adjacent cells with equal cell codes form one run; there
are no empty runs; width 0 gives no runs."""
    text = _cott_normalize_f32_abi(text, StyledText, path="$.text")
    base = _cott_normalize_f32_abi(base, str, path="$.base")
    offset = _cott_normalize_f32_abi(offset, U64, path="$.offset")
    width = _cott_normalize_f32_abi(width, U16, path="$.width")
    fill = _cott_normalize_f32_abi(fill, str, path="$.fill")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/screen/text_runs.py", "02b8ab1369bf8b7da7aad4090cbe9ce889cd42984d06b634378a6925cfe39542", "text_runs", expected_project_name="toolong", expected_cott_symbol="real.toolong.screen.text_runs")
        _result = _implementation(text, base, offset, width, fill)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.screen.text_runs"
        if _error.span is None:
            _error.span = {"end_byte":4496,"end_column":1,"end_line":134,"start_byte":3362,"start_column":1,"start_line":114}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.screen.text_runs", phase="implementation-call", span={"end_byte":4496,"end_column":1,"end_line":134,"start_byte":3362,"start_column":1,"start_line":114}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.screen.text_runs", phase="implementation-call", span={"end_byte":4496,"end_column":1,"end_line":134,"start_byte":3362,"start_column":1,"start_line":114}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[StyledRun], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[StyledRun], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def paste_rows(base: CottList[ScreenRow], x: U16, y: U16, rows: CottList[ScreenRow]) -> CottList[ScreenRow]:
    """Draw rows over base with their top-left corner at column x, row y. Row i of
rows replaces the cells of base row y + i starting at column x, clipped to
the base row's width; rows beyond the last base row are dropped. A
double-width character in base that is partly overwritten becomes a space
for its surviving cell, in its style. The result rows are normalized
(adjacent equal styles merged, no empty runs) and keep their widths."""
    base = _cott_normalize_f32_abi(base, CottList[ScreenRow], path="$.base")
    x = _cott_normalize_f32_abi(x, U16, path="$.x")
    y = _cott_normalize_f32_abi(y, U16, path="$.y")
    rows = _cott_normalize_f32_abi(rows, CottList[ScreenRow], path="$.rows")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/screen/paste_rows.py", "20d2dd6d35bb487f65a93607b938c8b746b533450c6c1db95176f0c01a30858c", "paste_rows", expected_project_name="toolong", expected_cott_symbol="real.toolong.screen.paste_rows")
        _result = _implementation(base, x, y, rows)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.screen.paste_rows"
        if _error.span is None:
            _error.span = {"end_byte":5119,"end_column":1,"end_line":148,"start_byte":4496,"start_column":1,"start_line":134}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.screen.paste_rows", phase="implementation-call", span={"end_byte":5119,"end_column":1,"end_line":148,"start_byte":4496,"start_column":1,"start_line":134}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.screen.paste_rows", phase="implementation-call", span={"end_byte":5119,"end_column":1,"end_line":148,"start_byte":4496,"start_column":1,"start_line":134}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[ScreenRow], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) == len(base))), "real.toolong.screen.paste_rows", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.screen.paste_rows", clause="ensures:1", phase="ensures", span={"end_byte":5101,"end_column":35,"end_line":144,"start_byte":5071,"start_column":5,"start_line":144}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[ScreenRow], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_tabs(titles: CottList[str], active: U32, width: U16, focused: bool) -> CottList[ScreenRow]:
    """Color names (Surface, Text, Accent, ...) are ThemeColor members whose
values come from real.toolong.screen.theme_color.

The three-row tab strip, each row width cells, background Surface. Row 0
is blank. Row 1 has one blank cell, then for each tab " " + title + " "
with one blank cell between tabs; the active tab's label is Text and
bold, the others Muted; the rest is blank. Row 2 is "━" in every cell with
foreground Underline, except that the cells under the active tab's title
(not its padding) are "━" in Accent when focused and Panel otherwise, the
cell just left of them is "╸" and the cell just right of them is "╺"
(both Underline). Everything is clipped to width; blank cells are spaces
with foreground Text."""
    titles = _cott_normalize_f32_abi(titles, CottList[str], path="$.titles")
    active = _cott_normalize_f32_abi(active, U32, path="$.active")
    width = _cott_normalize_f32_abi(width, U16, path="$.width")
    focused = _cott_normalize_f32_abi(focused, bool, path="$.focused")
    if _cott_test_context:
        if not (_cott_contract_condition(((width <= 4096)), "real.toolong.screen.render_tabs", "requires:1")):
            raise CottContractViolation("requires clause failed", symbol="real.toolong.screen.render_tabs", clause="requires:1", phase="requires", span={"end_byte":6037,"end_column":27,"end_line":164,"start_byte":6015,"start_column":5,"start_line":164}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/screen/render_tabs.py", "432512fadf22c39013aee04a1c53a4df24b4569305a3ef41e20b532fd2ad3c78", "render_tabs", expected_project_name="toolong", expected_cott_symbol="real.toolong.screen.render_tabs")
        _result = _implementation(titles, active, width, focused)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.screen.render_tabs"
        if _error.span is None:
            _error.span = {"end_byte":6084,"end_column":1,"end_line":170,"start_byte":5119,"start_column":1,"start_line":148}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.screen.render_tabs", phase="implementation-call", span={"end_byte":6084,"end_column":1,"end_line":170,"start_byte":5119,"start_column":1,"start_line":148}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.screen.render_tabs", phase="implementation-call", span={"end_byte":6084,"end_column":1,"end_line":170,"start_byte":5119,"start_column":1,"start_line":148}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[ScreenRow], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) == 3)), "real.toolong.screen.render_tabs", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.screen.render_tabs", clause="ensures:2", phase="ensures", span={"end_byte":6066,"end_column":28,"end_line":166,"start_byte":6043,"start_column":5,"start_line":166}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[ScreenRow], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_log_lines(tab: TabView, layout: ViewerLayout, focused: bool, lines: Opaque[Literal["styled_lines"]]) -> Opaque[Literal["screen_rows"]]:
    """Color names (Surface, Text, Accent, ...) are ThemeColor members whose
values come from real.toolong.screen.theme_color.

The log lines widget: layout.lines_box.height rows of lines_box.width
cells (coordinates below are relative to the box). base is foreground
Text on background Surface.

lines is the opaque tuple of StyledText values described on FrameContent
(lines[r] and lines.len below index and measure that tuple). Return an
opaque tuple of ScreenRow values rather than passing the entire densely
styled screen through recursive ABI validation. Assemble the rows with
private helpers only: never pass the box rows (or any other multi-row,
full-width ScreenRow list) through the public
real.toolong.screen.paste_rows facade, because such arguments exceed the
1024-node ABI traversal limit at runtime. Calls to text_runs and
real.toolong.text.highlight_find with one line's text are fine.

Border: when focused, a heavy box ("┏", "━", "┓", "┃", "┗", "┛") in Accent
on Surface; otherwise the border cells are blank base cells.

Text rows r = 0 .. text.height - 1 are drawn at box row 1 + r from box
column 1, text.width cells wide. Line index = scroll_y + r. When loading is
true every text row is blank except row text.height // 2, which shows
"●●●●●" in Accent starting at cell (text.width - 5) // 2. Otherwise rows
with index >= line_count or r >= lines.len are blank. For the other rows,
start from lines[r]; when index equals the pointer append a span with
style code "bg:#004578 bold" (Primary, bold) over the whole text; when show_find is
true and the find input value is non-empty, apply
real.toolong.text.highlight_find with FindQuery(value, regex,
case_sensitive). The row is the gutter (layout.gutter cells) followed by
real.toolong.screen.text_runs(text, base, scroll_x, text.width - gutter,
fill) where fill is base with background Primary on the pointer row and
base otherwise. The gutter, when line numbers are on, starts with the
decimal index + 1 and a space in foreground LineNumber (Warning and bold
on the pointer row), then "👉" on the pointer row or " " otherwise, padded
with base spaces or cut to the gutter width. When scan_tint is true every
cell of the text rows is additionally dim.

Scrollbars: the two columns right of the text rows form the vertical
scrollbar and the row below the text rows (text.width + 2 cells) the
horizontal one; their cells are spaces with background Track. The
vertical thumb exists when line_count > text.height: length max(1,
text.height * text.height // line_count), starting (text.height - length)
* scroll_y // (line_count - text.height) rows down. The horizontal thumb
uses the virtual width content_width plus the gutter (when the pointer is
set or line numbers are on) against text.width the same way with scroll_x.
Thumb cells are spaces with background Thumb.

Scan box: when focused and scan_message is not empty, rows text row 2 to
text row 5 in columns text column 4 to text.width - 5 (only the part inside
the text area) are a box with background Primary: a blank row, the message
centered (foreground Text), a bar centered, a blank row. The bar is min(32,
box width - 4) cells of "━": the first round(scan_progress * bar width) in
Warning, the rest in Underline."""
    tab = _cott_normalize_f32_abi(tab, TabView, path="$.tab")
    layout = _cott_normalize_f32_abi(layout, ViewerLayout, path="$.layout")
    focused = _cott_normalize_f32_abi(focused, bool, path="$.focused")
    lines = _cott_normalize_f32_abi(lines, Opaque[Literal["styled_lines"]], path="$.lines")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/screen/render_log_lines.py", "1f303880a1e287e90d0784a5fc36cd576bdf803dad1db65d6ac41a9ad4c43b85", "render_log_lines", expected_project_name="toolong", expected_cott_symbol="real.toolong.screen.render_log_lines")
        _result = _implementation(tab, layout, focused, lines)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.screen.render_log_lines"
        if _error.span is None:
            _error.span = {"end_byte":9749,"end_column":1,"end_line":235,"start_byte":6084,"start_column":1,"start_line":170}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.screen.render_log_lines", phase="implementation-call", span={"end_byte":9749,"end_column":1,"end_line":235,"start_byte":6084,"start_column":1,"start_line":170}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.screen.render_log_lines", phase="implementation-call", span={"end_byte":9749,"end_column":1,"end_line":235,"start_byte":6084,"start_column":1,"start_line":170}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Opaque[Literal["screen_rows"]], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Opaque[Literal["screen_rows"]], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_find_dialog(tab: TabView, width: U16, focus: Focus, suggestion: str) -> FindDialogView:
    """Color names (Surface, Text, Accent, ...) are ThemeColor members whose
values come from real.toolong.screen.theme_color.

The four-row find dialog, width cells wide, background Surface. Row 0 is
blank. Rows 1 to 3 hold three tall-bordered widgets side by side: the
input in columns [0, width - 35), the "Case sensitive" checkbox in [width -
35, width - 13) and the "Regex" checkbox in [width - 13, width) (a widget
with no room is omitted). A tall border draws, for a widget w cells wide,
"▊" + "▔" * (w - 2) + "▎" on its top row, "▊" + content + "▎" on its middle
row and "▊" + "▁" * (w - 2) + "▎" on its bottom row; the border color is
Accent when the widget has focus, Error for the input when regex is on and
the value is not a valid Python regular expression, and Background
otherwise. Decide validity by calling real.toolong.text.line_matches(" ",
FindQuery(value, true, false)) and reading invalid_regex (the
implementation audit rejects calling re.compile directly).

Input content (w - 2 cells): two blank cells, then the text area (w - 6
cells), then two blank cells. With an empty value the text area shows the
placeholder "Regex" (regex on) or "Find" in Muted. Otherwise it shows the
value in Text scrolled so that the cursor stays visible (first shown code
point: max(0, cursor - (area width - 1))) followed, when the input has
focus and suggestion is longer than the value, by suggestion[len(value):]
in Muted. cursor is the cell of the input's cursor on row 2 when focus is
FindInput and Nothing otherwise.

Checkbox content: " ▐X▌ " + label + " " where label is "Case sensitive"
or "Regex"; "▐" and "▌" are Panel, "X" is Success and bold when the box is
on and Muted when off, and the label is Text, underlined when the checkbox
has focus."""
    tab = _cott_normalize_f32_abi(tab, TabView, path="$.tab")
    width = _cott_normalize_f32_abi(width, U16, path="$.width")
    focus = _cott_normalize_f32_abi(focus, Focus, path="$.focus")
    suggestion = _cott_normalize_f32_abi(suggestion, str, path="$.suggestion")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/screen/render_find_dialog.py", "bb881551c39293491c17cdec577d91159eb912a8ffa55543dcfc984f97210d43", "render_find_dialog", expected_project_name="toolong", expected_cott_symbol="real.toolong.screen.render_find_dialog")
        _result = _implementation(tab, width, focus, suggestion)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.screen.render_find_dialog"
        if _error.span is None:
            _error.span = {"end_byte":11813,"end_column":1,"end_line":272,"start_byte":9749,"start_column":1,"start_line":235}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.screen.render_find_dialog", phase="implementation-call", span={"end_byte":11813,"end_column":1,"end_line":272,"start_byte":9749,"start_column":1,"start_line":235}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.screen.render_find_dialog", phase="implementation-call", span={"end_byte":11813,"end_column":1,"end_line":272,"start_byte":9749,"start_column":1,"start_line":235}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, FindDialogView, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len((_result).rows) == 4)), "real.toolong.screen.render_find_dialog", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.screen.render_find_dialog", clause="ensures:1", phase="ensures", span={"end_byte":11795,"end_column":33,"end_line":268,"start_byte":11767,"start_column":5,"start_line":268}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, FindDialogView, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_panel(lines: CottList[StyledText], rect: Rect, scroll_x: U64, scroll_y: U64, focused: bool) -> CottList[ScreenRow]:
    """Color names (Surface, Text, Accent, ...) are ThemeColor members whose
values come from real.toolong.screen.theme_color.

The line panel: rect.height rows of rect.width cells with background Panel
and foreground Text (base). The border is a heavy Accent box when focused
and blank base cells otherwise. The content area starts at panel column 2
and row 2, is rect.width - 6 cells wide and rect.height - 3 rows tall;
content row i shows lines[scroll_y + i] (blank when missing) through
real.toolong.screen.text_runs with offset scroll_x and base as base and
fill. The two columns left of the right border are a vertical scrollbar
(Track spaces, Thumb as in real.toolong.screen.render_log_lines for
lines.len lines against the content height)."""
    lines = _cott_normalize_f32_abi(lines, CottList[StyledText], path="$.lines")
    rect = _cott_normalize_f32_abi(rect, Rect, path="$.rect")
    scroll_x = _cott_normalize_f32_abi(scroll_x, U64, path="$.scroll_x")
    scroll_y = _cott_normalize_f32_abi(scroll_y, U64, path="$.scroll_y")
    focused = _cott_normalize_f32_abi(focused, bool, path="$.focused")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/screen/render_panel.py", "153b85cfe0db8401856f2cd11c04c0c6f4c960e23d932d748851616b81c36ecd", "render_panel", expected_project_name="toolong", expected_cott_symbol="real.toolong.screen.render_panel")
        _result = _implementation(lines, rect, scroll_x, scroll_y, focused)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.screen.render_panel"
        if _error.span is None:
            _error.span = {"end_byte":12780,"end_column":1,"end_line":296,"start_byte":11813,"start_column":1,"start_line":272}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.screen.render_panel", phase="implementation-call", span={"end_byte":12780,"end_column":1,"end_line":296,"start_byte":11813,"start_column":1,"start_line":272}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.screen.render_panel", phase="implementation-call", span={"end_byte":12780,"end_column":1,"end_line":296,"start_byte":11813,"start_column":1,"start_line":272}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[ScreenRow], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[ScreenRow], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_footer(keys: CottList[FooterKey], width: U16, tail_badge: bool, meta: str) -> ScreenRow:
    """Color names (Surface, Text, Accent, ...) are ThemeColor members whose
values come from real.toolong.screen.theme_color.

Toolong's LogFooter row, width cells, background Surface. From column 0,
each key is its display drawn reversed (foreground Surface on background
Warning) followed by " " + description + " " in Warning. At the right end:
" " + meta + " " in Success; when tail_badge is true it is preceded by " "
and " TAIL " (Success, bold, background TailBackground). The right part
is drawn over the keys when they overlap; the rest is blank."""
    keys = _cott_normalize_f32_abi(keys, CottList[FooterKey], path="$.keys")
    width = _cott_normalize_f32_abi(width, U16, path="$.width")
    tail_badge = _cott_normalize_f32_abi(tail_badge, bool, path="$.tail_badge")
    meta = _cott_normalize_f32_abi(meta, str, path="$.meta")
    if _cott_test_context:
        if not (_cott_contract_condition(((width <= 4096)), "real.toolong.screen.render_footer", "requires:1")):
            raise CottContractViolation("requires clause failed", symbol="real.toolong.screen.render_footer", clause="requires:1", phase="requires", span={"end_byte":13508,"end_column":27,"end_line":309,"start_byte":13486,"start_column":5,"start_line":309}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/screen/render_footer.py", "ffdade96f928a3dcc7a57a4482e4ef14ec7615838b396284838ea36e743dbdda", "render_footer", expected_project_name="toolong", expected_cott_symbol="real.toolong.screen.render_footer")
        _result = _implementation(keys, width, tail_badge, meta)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.screen.render_footer"
        if _error.span is None:
            _error.span = {"end_byte":13526,"end_column":1,"end_line":313,"start_byte":12780,"start_column":1,"start_line":296}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.screen.render_footer", phase="implementation-call", span={"end_byte":13526,"end_column":1,"end_line":313,"start_byte":12780,"start_column":1,"start_line":296}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.screen.render_footer", phase="implementation-call", span={"end_byte":13526,"end_column":1,"end_line":313,"start_byte":12780,"start_column":1,"start_line":296}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, ScreenRow, path="$.return")
    _result = _cott_wrap_async_protocol(_result, ScreenRow, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_help_footer(keys: CottList[FooterKey], width: U16) -> ScreenRow:
    """Color names (Surface, Text, Accent, ...) are ThemeColor members whose
values come from real.toolong.screen.theme_color.

Textual's Footer row for the help screen, width cells, background Accent,
foreground Text: from column 0 each key is " " + display + " " bold on
AccentDark followed by " " + description + " "; the rest is blank."""
    keys = _cott_normalize_f32_abi(keys, CottList[FooterKey], path="$.keys")
    width = _cott_normalize_f32_abi(width, U16, path="$.width")
    if _cott_test_context:
        if not (_cott_contract_condition(((width <= 4096)), "real.toolong.screen.render_help_footer", "requires:1")):
            raise CottContractViolation("requires clause failed", symbol="real.toolong.screen.render_help_footer", clause="requires:1", phase="requires", span={"end_byte":14001,"end_column":27,"end_line":323,"start_byte":13979,"start_column":5,"start_line":323}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/screen/render_help_footer.py", "a203d192459cd8483460257ff545c2339106535d68d2e013161be360d3d6852c", "render_help_footer", expected_project_name="toolong", expected_cott_symbol="real.toolong.screen.render_help_footer")
        _result = _implementation(keys, width)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.screen.render_help_footer"
        if _error.span is None:
            _error.span = {"end_byte":14019,"end_column":1,"end_line":327,"start_byte":13526,"start_column":1,"start_line":313}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.screen.render_help_footer", phase="implementation-call", span={"end_byte":14019,"end_column":1,"end_line":327,"start_byte":13526,"start_column":1,"start_line":313}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.screen.render_help_footer", phase="implementation-call", span={"end_byte":14019,"end_column":1,"end_line":327,"start_byte":13526,"start_column":1,"start_line":313}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, ScreenRow, path="$.return")
    _result = _cott_wrap_async_protocol(_result, ScreenRow, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_help(lines: CottList[StyledText], box: Rect, scroll: U64) -> CottList[ScreenRow]:
    """Color names (Surface, Text, Accent, ...) are ThemeColor members whose
values come from real.toolong.screen.theme_color.

The help screen box: box.height rows of box.width cells with foreground
Text on Surface. A heavy Accent border whose top edge shows " Help "
starting at column 2 and whose bottom edge shows " ESCAPE to dismiss "
ending at column box.width - 3 (titles in Text). The content area is box
columns 1 to box.width - 4 and rows 1 to box.height - 2; content row i
shows lines[scroll + i] through real.toolong.screen.text_runs (offset 0).
The two columns left of the right border are a vertical scrollbar for
lines.len lines, as in real.toolong.screen.render_log_lines."""
    lines = _cott_normalize_f32_abi(lines, CottList[StyledText], path="$.lines")
    box = _cott_normalize_f32_abi(box, Rect, path="$.box")
    scroll = _cott_normalize_f32_abi(scroll, U64, path="$.scroll")
    if _cott_test_context:
        if not (_cott_contract_condition(((((box).width <= 4096) and ((box).height <= 4096))), "real.toolong.screen.render_help", "requires:1")):
            raise CottContractViolation("requires clause failed", symbol="real.toolong.screen.render_help", clause="requires:1", phase="requires", span={"end_byte":14903,"end_column":54,"end_line":342,"start_byte":14854,"start_column":5,"start_line":342}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/screen/render_help.py", "b0f2993d8f9f0f65c979b89ce9ae150cbbdaee960ab421980d052318d915e43b", "render_help", expected_project_name="toolong", expected_cott_symbol="real.toolong.screen.render_help")
        _result = _implementation(lines, box, scroll)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.screen.render_help"
        if _error.span is None:
            _error.span = {"end_byte":14921,"end_column":1,"end_line":346,"start_byte":14019,"start_column":1,"start_line":327}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.screen.render_help", phase="implementation-call", span={"end_byte":14921,"end_column":1,"end_line":346,"start_byte":14019,"start_column":1,"start_line":327}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.screen.render_help", phase="implementation-call", span={"end_byte":14921,"end_column":1,"end_line":346,"start_byte":14019,"start_column":1,"start_line":327}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[ScreenRow], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[ScreenRow], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_goto(input: TextInput, width: U16, height: U16) -> PlacedRows:
    """Color names (Surface, Text, Accent, ...) are ThemeColor members whose
values come from real.toolong.screen.theme_color.

The go-to-line input: a 16-cell by 3-row tall-bordered Accent input (see
real.toolong.screen.render_find_dialog) at x = width - 19 and y = height -
6 (saturating at 0), background Surface, showing the value (or the
placeholder "Enter line number" in Muted, cut to the text area) with the
same padding and scrolling as the find input."""
    input = _cott_normalize_f32_abi(input, TextInput, path="$.input")
    width = _cott_normalize_f32_abi(width, U16, path="$.width")
    height = _cott_normalize_f32_abi(height, U16, path="$.height")
    if _cott_test_context:
        if not (_cott_contract_condition((((width <= 4096) and (height <= 4096))), "real.toolong.screen.render_goto", "requires:1")):
            raise CottContractViolation("requires clause failed", symbol="real.toolong.screen.render_goto", clause="requires:1", phase="requires", span={"end_byte":15547,"end_column":46,"end_line":358,"start_byte":15506,"start_column":5,"start_line":358}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/screen/render_goto.py", "9e1003a05f4aa5244a596be33c151f2a7ac61a31332a458e38ecf27321b65729", "render_goto", expected_project_name="toolong", expected_cott_symbol="real.toolong.screen.render_goto")
        _result = _implementation(input, width, height)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.screen.render_goto"
        if _error.span is None:
            _error.span = {"end_byte":15599,"end_column":1,"end_line":364,"start_byte":14921,"start_column":1,"start_line":346}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.screen.render_goto", phase="implementation-call", span={"end_byte":15599,"end_column":1,"end_line":364,"start_byte":14921,"start_column":1,"start_line":346}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.screen.render_goto", phase="implementation-call", span={"end_byte":15599,"end_column":1,"end_line":364,"start_byte":14921,"start_column":1,"start_line":346}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, PlacedRows, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len((_result).rows) == 3)), "real.toolong.screen.render_goto", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.screen.render_goto", clause="ensures:2", phase="ensures", span={"end_byte":15581,"end_column":33,"end_line":360,"start_byte":15553,"start_column":5,"start_line":360}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, PlacedRows, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_notifications(notifications: CottList[Notification], width: U16, height: U16) -> CottList[PlacedRows]:
    """Color names (Surface, Text, Accent, ...) are ThemeColor members whose
values come from real.toolong.screen.theme_color.

Textual toasts, bottom-right. A toast is t = min(60, width // 2) cells
wide with background Panel: its first column is "▌" in the severity color
(Success for Information, Warning, Error), its last column a blank, and
between them a one-cell padding on each side around the content, which is
t - 4 cells wide. Content lines: the title (when non-empty) bold in
SuccessDark / WarningDark / ErrorDark, then the message word-wrapped with
real.toolong.text.wrap_text in Text. A toast has a blank padding row above
and below its content. The newest (last) notification is lowest, its last
row on row height - 2 and its left edge at column width - 1 - t; each
earlier one sits above the next with one row between them. Toasts whose
top would be above row 0 are omitted. The list is ordered from the oldest
shown to the newest."""
    notifications = _cott_normalize_f32_abi(notifications, CottList[Notification], path="$.notifications")
    width = _cott_normalize_f32_abi(width, U16, path="$.width")
    height = _cott_normalize_f32_abi(height, U16, path="$.height")
    if _cott_test_context:
        if not (_cott_contract_condition((((width <= 4096) and (height <= 4096))), "real.toolong.screen.render_notifications", "requires:1")):
            raise CottContractViolation("requires clause failed", symbol="real.toolong.screen.render_notifications", clause="requires:1", phase="requires", span={"end_byte":16787,"end_column":46,"end_line":387,"start_byte":16746,"start_column":5,"start_line":387}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/screen/render_notifications.py", "2bc8bdc42f64a38e1a21f9964081f14470c3ebacdce15ae4fe993f42fa628498", "render_notifications", expected_project_name="toolong", expected_cott_symbol="real.toolong.screen.render_notifications")
        _result = _implementation(notifications, width, height)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.screen.render_notifications"
        if _error.span is None:
            _error.span = {"end_byte":16805,"end_column":1,"end_line":391,"start_byte":15599,"start_column":1,"start_line":364}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.screen.render_notifications", phase="implementation-call", span={"end_byte":16805,"end_column":1,"end_line":391,"start_byte":15599,"start_column":1,"start_line":364}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.screen.render_notifications", phase="implementation-call", span={"end_byte":16805,"end_column":1,"end_line":391,"start_byte":15599,"start_column":1,"start_line":364}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[PlacedRows], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[PlacedRows], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def compose_screen(viewer: ViewerState, content: FrameContent) -> Frame:
    """Color names (Surface, Text, Accent, ...) are ThemeColor members whose
values come from real.toolong.screen.theme_color.

The whole frame, height rows of width cells, built from blank base cells
using real.toolong.view.viewer_layout and real.toolong.view.footer_keys.
Compose the intermediate frame with a private row-paste helper, not by
round-tripping full-width rows through the public paste_rows facade: dense
screen rows exceed the ABI traversal budget. Wrap the completed tuple of
ScreenRow values as Opaque["screen_rows"].

1. With more than one tab, the tab strip (render_tabs with the titles, the
active index and focus Tabs) at row 0.
2. For the active tab: the find dialog (when shown) at its rectangle; the
log lines (render_log_lines with focus Lines and content.lines); the panel
(when shown) with content.panel and focus Panel; when the tab is not
tailing and pending_lines > 0, the label " +N lines " (N with thousands
separators) bold Success on Panel starting at column lines_box.x +
(lines_box.width - label width) // 2 on the row above the footer.
3. The footer row: render_footer(keys, width, tail and can_tail,
content.meta).
4. Help modal: every cell so far becomes dim; the help box
Rect(8, 4, width - 16, height - 9) (saturating) is drawn with the lines of
real.toolong.help.help_title(content width) followed by the StyledText
values of the tuple wrapped by real.toolong.help.help_markdown(content
width), content width being the box width - 4, and the footer row is
replaced by render_help_footer. Go-to
modal: every cell so far becomes dim and render_goto is drawn.
5. The notifications on top.
The cursor is the go-to input's cursor under the go-to modal, the find
input's cursor when no modal is open and focus is FindInput with the find
dialog shown, and Nothing otherwise. With no tabs, only the footer and
modals are drawn."""
    viewer = _cott_normalize_f32_abi(viewer, ViewerState, path="$.viewer")
    content = _cott_normalize_f32_abi(content, FrameContent, path="$.content")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/screen/compose_screen.py", "d9001817a62b51bb1d462a452f3bc8c594630575ecbe8e080c216132ea008985", "compose_screen", expected_project_name="toolong", expected_cott_symbol="real.toolong.screen.compose_screen")
        _result = _implementation(viewer, content)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.screen.compose_screen"
        if _error.span is None:
            _error.span = {"end_byte":18898,"end_column":1,"end_line":429,"start_byte":16805,"start_column":1,"start_line":391}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.screen.compose_screen", phase="implementation-call", span={"end_byte":18898,"end_column":1,"end_line":429,"start_byte":16805,"start_column":1,"start_line":391}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.screen.compose_screen", phase="implementation-call", span={"end_byte":18898,"end_column":1,"end_line":429,"start_byte":16805,"start_column":1,"start_line":391}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Frame, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Frame, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["Cursor", "FindDialogView", "Frame", "FrameContent", "PlacedRows", "ThemeColor", "ThemeColor_Accent", "ThemeColor_AccentDark", "ThemeColor_Background", "ThemeColor_Black", "ThemeColor_Error", "ThemeColor_ErrorDark", "ThemeColor_LineNumber", "ThemeColor_Muted", "ThemeColor_Panel", "ThemeColor_Primary", "ThemeColor_Success", "ThemeColor_SuccessDark", "ThemeColor_Surface", "ThemeColor_TailBackground", "ThemeColor_Text", "ThemeColor_Thumb", "ThemeColor_Track", "ThemeColor_Underline", "ThemeColor_Warning", "ThemeColor_WarningDark", "compose_screen", "paste_rows", "render_find_dialog", "render_footer", "render_goto", "render_help", "render_help_footer", "render_log_lines", "render_notifications", "render_panel", "render_tabs", "text_runs", "theme_color"]
