from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.toolong.keys_types import TextInput
from real.toolong.model_types import Rect, ScreenRow, StyledRun, StyledText, TermColor
from real.toolong.view_types import Focus, FooterKey, Notification, TabView, ViewerLayout, ViewerState

"""The named colors of Toolong's default Textual dark theme."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_Surface:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_Background:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_Text:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_Muted:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_Accent:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_AccentDark:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_Panel:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_Primary:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_Warning:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_Success:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_Error:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_LineNumber:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_TailBackground:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_Track:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_Thumb:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_Underline:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_Black:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_SuccessDark:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_WarningDark:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeColor_ErrorDark:
    pass

ThemeColor: TypeAlias = Union[ThemeColor_Surface, ThemeColor_Background, ThemeColor_Text, ThemeColor_Muted, ThemeColor_Accent, ThemeColor_AccentDark, ThemeColor_Panel, ThemeColor_Primary, ThemeColor_Warning, ThemeColor_Success, ThemeColor_Error, ThemeColor_LineNumber, ThemeColor_TailBackground, ThemeColor_Track, ThemeColor_Thumb, ThemeColor_Underline, ThemeColor_Black, ThemeColor_SuccessDark, ThemeColor_WarningDark, ThemeColor_ErrorDark]

"""A terminal cursor position."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cursor:
    __hash__ = None
    x: U16
    y: U16

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "x", _cott_validate_abi(self.x, U16, path="$.x"))
        if not _cott_validated_construction():
            object.__setattr__(self, "y", _cott_validate_abi(self.y, U16, path="$.y"))

"""Rows to draw with their top-left corner at (x, y)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PlacedRows:
    __hash__ = None
    x: U16
    y: U16
    rows: CottList[ScreenRow]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "x", _cott_validate_abi(self.x, U16, path="$.x"))
        if not _cott_validated_construction():
            object.__setattr__(self, "y", _cott_validate_abi(self.y, U16, path="$.y"))
        if not _cott_validated_construction():
            object.__setattr__(self, "rows", _cott_validate_abi(self.rows, CottList[ScreenRow], path="$.rows"))

"""The rendered find dialog rows and the text cursor when its input has focus."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FindDialogView:
    __hash__ = None
    rows: CottList[ScreenRow]
    cursor: Option[Cursor]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "rows", _cott_validate_abi(self.rows, CottList[ScreenRow], path="$.rows"))
        if not _cott_validated_construction():
            object.__setattr__(self, "cursor", _cott_validate_abi(self.cursor, Option[Cursor], path="$.cursor"))

"""What the driver read for one frame: the parsed, abbreviated texts of the
active tab's visible lines (the lines scroll_y, scroll_y + 1, ... that exist,
at most one per text row), the line panel's content lines, and the footer
meta text. lines and panel are each Opaque(tag="styled_lines", value=tuple
of StyledText values): a screenful of highlighted lines exceeds the
1024-node ABI traversal limit, which is enforced even when a struct is
constructed, so never collect them into a List or a Cott struct field typed
as a list. Build them with cott_runtime.Opaque(tag="styled_lines",
value=tuple(texts)) and read them as typing.cast(tuple[StyledText, ...],
handle.unwrap()) without per-element checks."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FrameContent:
    __hash__ = None
    lines: Opaque[Literal["styled_lines"]]
    panel: Opaque[Literal["styled_lines"]]
    meta: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "lines", _cott_validate_abi(self.lines, Opaque[Literal["styled_lines"]], path="$.lines"))
        if not _cott_validated_construction():
            object.__setattr__(self, "panel", _cott_validate_abi(self.panel, Opaque[Literal["styled_lines"]], path="$.panel"))
        if not _cott_validated_construction():
            object.__setattr__(self, "meta", _cott_validate_abi(self.meta, str, path="$.meta"))

"""A complete frame: exactly height rows of exactly width cells, and where to
show the terminal cursor (Nothing hides it). The screen rows are an opaque
tuple of ScreenRow values: validating an entire terminal frame recursively at
the facade would exceed the bounded ABI traversal budget. Build
Opaque["screen_rows"] values with cott_runtime.Opaque(tag="screen_rows",
value=tuple(rows)) and read them as typing.cast(tuple[ScreenRow, ...],
handle.unwrap()) without per-element checks."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Frame:
    __hash__ = None
    rows: Opaque[Literal["screen_rows"]]
    cursor: Option[Cursor]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "rows", _cott_validate_abi(self.rows, Opaque[Literal["screen_rows"]], path="$.rows"))
        if not _cott_validated_construction():
            object.__setattr__(self, "cursor", _cott_validate_abi(self.cursor, Option[Cursor], path="$.cursor"))

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
"""Draw rows over base with their top-left corner at column x, row y. Row i of
rows replaces the cells of base row y + i starting at column x, clipped to
the base row's width; rows beyond the last base row are dropped. A
double-width character in base that is partly overwritten becomes a space
for its surviving cell, in its style. The result rows are normalized
(adjacent equal styles merged, no empty runs) and keep their widths."""
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
"""Color names (Surface, Text, Accent, ...) are ThemeColor members whose
values come from real.toolong.screen.theme_color.

Toolong's LogFooter row, width cells, background Surface. From column 0,
each key is its display drawn reversed (foreground Surface on background
Warning) followed by " " + description + " " in Warning. At the right end:
" " + meta + " " in Success; when tail_badge is true it is preceded by " "
and " TAIL " (Success, bold, background TailBackground). The right part
is drawn over the keys when they overlap; the rest is blank."""
"""Color names (Surface, Text, Accent, ...) are ThemeColor members whose
values come from real.toolong.screen.theme_color.

Textual's Footer row for the help screen, width cells, background Accent,
foreground Text: from column 0 each key is " " + display + " " bold on
AccentDark followed by " " + description + " "; the rest is blank."""
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
"""Color names (Surface, Text, Accent, ...) are ThemeColor members whose
values come from real.toolong.screen.theme_color.

The go-to-line input: a 16-cell by 3-row tall-bordered Accent input (see
real.toolong.screen.render_find_dialog) at x = width - 19 and y = height -
6 (saturating at 0), background Surface, showing the value (or the
placeholder "Enter line number" in Muted, cut to the text area) with the
same padding and scrolling as the find input."""
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
__all__ = ["Cursor", "FindDialogView", "Frame", "FrameContent", "PlacedRows", "ThemeColor", "ThemeColor_Accent", "ThemeColor_AccentDark", "ThemeColor_Background", "ThemeColor_Black", "ThemeColor_Error", "ThemeColor_ErrorDark", "ThemeColor_LineNumber", "ThemeColor_Muted", "ThemeColor_Panel", "ThemeColor_Primary", "ThemeColor_Success", "ThemeColor_SuccessDark", "ThemeColor_Surface", "ThemeColor_TailBackground", "ThemeColor_Text", "ThemeColor_Thumb", "ThemeColor_Track", "ThemeColor_Underline", "ThemeColor_Warning", "ThemeColor_WarningDark"]
