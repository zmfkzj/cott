from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.harlequin.adapters_types import TransactionMode
from real.harlequin.catalog_types import CatalogEntry
from real.harlequin.keymap_types import FooterHint
from real.harlequin.style_types import StyledLine

"""The focusable regions of the IDE, in Tab order: the Data Catalog sidebar, the
Query Editor, the Run Query Bar's limit input, and the Results Viewer."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Pane_Catalog:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Pane_Editor:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Pane_RunBar:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Pane_Results:
    pass

Pane: TypeAlias = Union[Pane_Catalog, Pane_Editor, Pane_RunBar, Pane_Results]

"""Which pane has focus and how the screen is divided. sidebar_hidden hides the
Data Catalog (Ctrl+B / F9); full_screen shows only the focused Editor or
Results Viewer (F10) without changing sidebar_hidden."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LayoutState:
    __hash__ = None
    focus: Pane
    sidebar_hidden: bool
    full_screen: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "focus", _cott_validate_abi(self.focus, Pane, path="$.focus"))
        if not _cott_validated_construction():
            object.__setattr__(self, "sidebar_hidden", _cott_validate_abi(self.sidebar_hidden, bool, path="$.sidebar_hidden"))
        if not _cott_validated_construction():
            object.__setattr__(self, "full_screen", _cott_validate_abi(self.full_screen, bool, path="$.full_screen"))

"""The Run Query Bar: the Limit checkbox and its integer input (limit_text,
caret limit_cursor), and whether a query is running."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RunBar:
    __hash__ = None
    limit_enabled: bool
    limit_text: str
    limit_cursor: U64
    running: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "limit_enabled", _cott_validate_abi(self.limit_enabled, bool, path="$.limit_enabled"))
        if not _cott_validated_construction():
            object.__setattr__(self, "limit_text", _cott_validate_abi(self.limit_text, str, path="$.limit_text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "limit_cursor", _cott_validate_abi(self.limit_cursor, U64, path="$.limit_cursor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "running", _cott_validate_abi(self.running, bool, path="$.running"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RunBarStep:
    __hash__ = None
    bar: RunBar
    submit: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "bar", _cott_validate_abi(self.bar, RunBar, path="$.bar"))
        if not _cott_validated_construction():
            object.__setattr__(self, "submit", _cott_validate_abi(self.submit, bool, path="$.submit"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Severity_Information:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Severity_Warning:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Severity_Error:
    pass

Severity: TypeAlias = Union[Severity_Information, Severity_Warning, Severity_Error]

"""A toast notification. expires_at_ms is the monotonic time (ms) after which it
disappears."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Notification:
    __hash__ = None
    title: Option[str]
    message: str
    severity: Severity
    expires_at_ms: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "title", _cott_validate_abi(self.title, Option[str], path="$.title"))
        if not _cott_validated_construction():
            object.__setattr__(self, "message", _cott_validate_abi(self.message, str, path="$.message"))
        if not _cott_validated_construction():
            object.__setattr__(self, "severity", _cott_validate_abi(self.severity, Severity, path="$.severity"))
        if not _cott_validated_construction():
            object.__setattr__(self, "expires_at_ms", _cott_validate_abi(self.expires_at_ms, U64, path="$.expires_at_ms"))

"""A scrollable read-only text dialog: the View Cell dialog, error dialogs
(Query Error, Export Data Error, ...), the help screen and the debug screen.
lines is the full body; scroll is the first body line shown; copyable says
whether "c" copies copy_text; copy_notice is the notification text after a
copy; close_on_any_key says whether keys other than scroll keys (and "c" when
copyable) close it."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TextModal:
    __hash__ = None
    title: str
    header: str
    lines: CottList[str]
    footer: str
    scroll: U64
    copyable: bool
    copy_text: str
    copy_notice: str
    close_on_any_key: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "title", _cott_validate_abi(self.title, str, path="$.title"))
        if not _cott_validated_construction():
            object.__setattr__(self, "header", _cott_validate_abi(self.header, str, path="$.header"))
        if not _cott_validated_construction():
            object.__setattr__(self, "lines", _cott_validate_abi(self.lines, CottList[str], path="$.lines"))
        if not _cott_validated_construction():
            object.__setattr__(self, "footer", _cott_validate_abi(self.footer, str, path="$.footer"))
        if not _cott_validated_construction():
            object.__setattr__(self, "scroll", _cott_validate_abi(self.scroll, U64, path="$.scroll"))
        if not _cott_validated_construction():
            object.__setattr__(self, "copyable", _cott_validate_abi(self.copyable, bool, path="$.copyable"))
        if not _cott_validated_construction():
            object.__setattr__(self, "copy_text", _cott_validate_abi(self.copy_text, str, path="$.copy_text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "copy_notice", _cott_validate_abi(self.copy_notice, str, path="$.copy_notice"))
        if not _cott_validated_construction():
            object.__setattr__(self, "close_on_any_key", _cott_validate_abi(self.close_on_any_key, bool, path="$.close_on_any_key"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TextModalOutcome_Stay:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TextModalOutcome_Close:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TextModalOutcome_Copy:
    __hash__ = None
    text: str
    notice: str

TextModalOutcome: TypeAlias = Union[TextModalOutcome_Stay, TextModalOutcome_Close, TextModalOutcome_Copy]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TextModalStep:
    __hash__ = None
    modal: TextModal
    outcome: TextModalOutcome

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "modal", _cott_validate_abi(self.modal, TextModal, path="$.modal"))
        if not _cott_validated_construction():
            object.__setattr__(self, "outcome", _cott_validate_abi(self.outcome, TextModalOutcome, path="$.outcome"))

"""A Yes/No confirmation (for example before a catalog interaction drops a
table). yes_selected is the highlighted button."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfirmModal:
    __hash__ = None
    prompt: str
    yes_selected: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "prompt", _cott_validate_abi(self.prompt, str, path="$.prompt"))
        if not _cott_validated_construction():
            object.__setattr__(self, "yes_selected", _cott_validate_abi(self.yes_selected, bool, path="$.yes_selected"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfirmOutcome_Stay:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfirmOutcome_Yes:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfirmOutcome_No:
    pass

ConfirmOutcome: TypeAlias = Union[ConfirmOutcome_Stay, ConfirmOutcome_Yes, ConfirmOutcome_No]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfirmStep:
    __hash__ = None
    modal: ConfirmModal
    outcome: ConfirmOutcome

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "modal", _cott_validate_abi(self.modal, ConfirmModal, path="$.modal"))
        if not _cott_validated_construction():
            object.__setattr__(self, "outcome", _cott_validate_abi(self.outcome, ConfirmOutcome, path="$.outcome"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputPurpose_Find:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputPurpose_GoToLine:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputPurpose_OpenFile:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputPurpose_SaveFile:
    pass

InputPurpose: TypeAlias = Union[InputPurpose_Find, InputPurpose_GoToLine, InputPurpose_OpenFile, InputPurpose_SaveFile]

"""A one-line input dialog used for Find (Ctrl+F), Go To Line (Ctrl+G), Open
Query (Ctrl+O) and Save Query (Ctrl+S). completions are the candidates offered
by the last Tab (path purposes), shown under the input."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputModal:
    __hash__ = None
    purpose: InputPurpose
    title: str
    placeholder: str
    value: str
    cursor: U64
    message: str
    completions: CottList[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "purpose", _cott_validate_abi(self.purpose, InputPurpose, path="$.purpose"))
        if not _cott_validated_construction():
            object.__setattr__(self, "title", _cott_validate_abi(self.title, str, path="$.title"))
        if not _cott_validated_construction():
            object.__setattr__(self, "placeholder", _cott_validate_abi(self.placeholder, str, path="$.placeholder"))
        if not _cott_validated_construction():
            object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))
        if not _cott_validated_construction():
            object.__setattr__(self, "cursor", _cott_validate_abi(self.cursor, U64, path="$.cursor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "message", _cott_validate_abi(self.message, str, path="$.message"))
        if not _cott_validated_construction():
            object.__setattr__(self, "completions", _cott_validate_abi(self.completions, CottList[str], path="$.completions"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputOutcome_Stay:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputOutcome_Cancel:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputOutcome_Submit:
    __hash__ = None
    value: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputOutcome_Complete:
    __hash__ = None
    value: str

InputOutcome: TypeAlias = Union[InputOutcome_Stay, InputOutcome_Cancel, InputOutcome_Submit, InputOutcome_Complete]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputStep:
    __hash__ = None
    modal: InputModal
    outcome: InputOutcome

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "modal", _cott_validate_abi(self.modal, InputModal, path="$.modal"))
        if not _cott_validated_construction():
            object.__setattr__(self, "outcome", _cott_validate_abi(self.outcome, InputOutcome, path="$.outcome"))

"""The Data Catalog context menu (".") for one entry: Insert Name at Cursor
followed by the adapter's interactions for the entry."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ContextMenu:
    __hash__ = None
    entry: CatalogEntry
    items: CottList[str]
    selected: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "entry", _cott_validate_abi(self.entry, CatalogEntry, path="$.entry"))
        if not _cott_validated_construction():
            object.__setattr__(self, "items", _cott_validate_abi(self.items, CottList[str], path="$.items"))
        if not _cott_validated_construction():
            object.__setattr__(self, "selected", _cott_validate_abi(self.selected, U64, path="$.selected"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ContextMenuOutcome_Stay:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ContextMenuOutcome_Close:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ContextMenuOutcome_Choose:
    __hash__ = None
    label: str

ContextMenuOutcome: TypeAlias = Union[ContextMenuOutcome_Stay, ContextMenuOutcome_Close, ContextMenuOutcome_Choose]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ContextMenuStep:
    __hash__ = None
    menu: ContextMenu
    outcome: ContextMenuOutcome

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "menu", _cott_validate_abi(self.menu, ContextMenu, path="$.menu"))
        if not _cott_validated_construction():
            object.__setattr__(self, "outcome", _cott_validate_abi(self.outcome, ContextMenuOutcome, path="$.outcome"))

"""One line of the debug screen's content: a section heading (level 1 or 2) or
a body line."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DebugSection:
    __hash__ = None
    title: str
    body: CottList[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "title", _cott_validate_abi(self.title, str, path="$.title"))
        if not _cott_validated_construction():
            object.__setattr__(self, "body", _cott_validate_abi(self.body, CottList[str], path="$.body"))

"""The layout at startup: focus Editor, sidebar shown, not full screen."""
"""Apply a layout action, as Harlequin's app actions do:
"toggle_sidebar": flip sidebar_hidden; hiding it while the catalog has focus
moves focus to Editor. "toggle_full_screen": flip full_screen; entering full
screen while the catalog or run bar has focus moves focus to Editor.
"focus_query_editor", "focus_results_viewer": focus that pane (leaving full
screen when full screen shows the other pane). "focus_data_catalog": show the
sidebar, leave full screen and focus Catalog. "focus_next" /
"focus_previous": move to the next/previous pane in Tab order among the
visible ones (Catalog only when the sidebar is shown and not full screen;
in full screen only the full-screen pane, plus RunBar when that pane is the
Editor), wrapping. Any other action returns layout unchanged."""
"""The panes shown, in Tab order. Normally Catalog (unless sidebar_hidden),
Editor, RunBar, Results. In full screen: Editor and RunBar when focus is
Editor or RunBar, else Results only."""
"""The Run Query Bar at startup: with a configured limit the checkbox is checked
and limit_text is its decimal text; otherwise unchecked with limit_text
"500". limit_cursor is at the end of limit_text; not running."""
"""A key while the Run Query Bar has focus. "space" toggles the Limit checkbox
(a checked box requires a valid limit_text, otherwise it stays unchecked).
Digits insert at limit_cursor; "backspace"/"delete" edit; "left"/"right"/
"home"/"end" move the caret; after an edit the checkbox becomes checked when
limit_text is a nonempty whole number >= 0 and unchecked otherwise. "enter"
submits (submit true) when limit_text is valid and nonempty. Other keys do
nothing. submit is false unless stated."""
"""The hard row limit a run uses: Some(int(limit_text)) when the checkbox is
checked and limit_text is a whole number >= 0, else Nothing."""
"""The one-line Run Query Bar. Left: when transaction is Some, "[Tx: {label}]"
then " [🡅]" when can_commit and " [⮌]" when can_rollback, then a space. Then
"[x] Limit " or "[ ] Limit " followed by the limit_text padded to 7 cells
(style "class:hq.input", with " class:hq.cursor" when focused), right-aligned
at the end: "[ Cancel Query ]" (class:hq.button.focused) when bar.running
and can_cancel, "[ Running... ]" (class:hq.loading) when running otherwise,
else "[ {run_label} ]" (class:hq.button, or class:hq.muted when not
runnable). Other text uses class:hq.status. width is the terminal's
16-bit column count (POSIX winsize.ws_col); the line is exactly width cells
(padded with spaces, or cut)."""
"""The Run button caption: "Run Selection" when selection (the selected editor
text) is not blank and valid (the adapter accepted it, or cannot validate),
else "Run Query"."""
"""A tab strip: each label as " {label} " styled "class:hq.tab.active" for the
active index and "class:hq.tab" otherwise, separated by nothing, cut at
the terminal's 16-bit column width and padded with spaces to that width."""
"""The footer: for each hint " {key}" styled "class:hq.footer.key" followed by
" {description} " styled "class:hq.footer.description", cut at the terminal's
16-bit column width and padded with spaces styled "class:hq.footer"."""
"""A notification shown for 5 seconds (10 seconds for Error), as Harlequin's
toasts: expires_at_ms is now_ms + 5000 or + 10000, saturated at the U64
maximum 18446744073709551615. Saturation preserves the timestamp's ABI
when the caller supplies a monotonic clock reading near its upper bound."""
"""The unexpired notifications (expires_at_ms > now_ms), newest last, each as
its title line (when Some, bold via class:hq.dialog.title) and its message
lines, every line prefixed with "▌ " and styled "class:hq.notification" (or
"class:hq.notification.error" for Error, "class:hq.warning" prefix for
Warning), wrapped at width - 2 cells, with a blank line between
notifications. At most the last 3 notifications are shown."""
"""A copyable text dialog showing body (split into lines on LF), scrolled to
the top, whose copy_text is body. It closes on any key other than scroll
keys and "c"."""
"""The View Cell dialog: title column (or "Cell Contents" when column is ""),
header "", body value, footer "Arrows/PgUp/PgDn scroll. Click text or press c
to copy. Any other key closes.", copy notice "Cell value copied to
clipboard."."""
"""An error dialog (Query Error, Export Data Error, Catalog Error, ...): the
given title and header, body message, footer "Arrows/PgUp/PgDn scroll. Click
text or press c to copy. Any other key closes.", copy notice "Error copied to
clipboard."."""
"""The help screen (F1): title "Harlequin Help", header "Welcome to Harlequin!
This screen contains a small subset of the online docs, available at
https://harlequin.sh/docs/getting-started", body = the key reference lines
(key_lines, from real.harlequin.keymap.help_lines), a blank line, then the
lines of help_markdown(); footer "Scroll with arrows. Press any other key to
continue."; not copyable; closes on any non-scroll key."""
"""Harlequin's bundled help text (help_screen.md of Harlequin 2.15.0), exactly
these sections in order, as Markdown: "### Using Harlequin with DuckDB"
(default adapter; `harlequin "path/to/duck.db" "another_duck.db"`; no
arguments for in-memory; see the Troubleshooting page
https://harlequin.sh/docs/troubleshooting/duckdb-version-mismatch to control
the DuckDB version), "### Using Harlequin with SQLite and Other Adapters"
(`harlequin -a sqlite "path/to/sqlite.db" "another_sqlite.db"`, `harlequin -a
sqlite` for in-memory, other adapters listed at
https://harlequin.sh/docs/adapters), "### Getting Help" (`harlequin --help`,
https://harlequin.sh/docs/troubleshooting/index, GitHub Issues
https://github.com/tconbeer/harlequin/issues for bugs, GitHub Discussions
https://github.com/tconbeer/harlequin/discussions for other issues), "###
Viewing Files" (`--show-files`/`-f` with an absolute path example
`harlequin --show-files /path/to/my/data` and `harlequin -f .`; remote
objects: https://harlequin.sh/docs/files/remote), "### Using Config Files"
(https://harlequin.sh/docs/config-file), "### Changing Key Bindings"
(keymaps from plug-ins or TOML config files,
https://harlequin.sh/docs/keymaps) and "### Managing Transactions"
(transaction modes, https://harlequin.sh/docs/transactions), each with the
upstream paragraphs and fenced bash examples."""
"""The debug screen (F12): title "Debug Information", header "Details about the
current Harlequin session, environment, and adapter.", body: for each section
a line "## {title}", its body lines and a blank line; footer "Tab/Shift Tab to
move focus, Enter to expand/collapse, Esc to close."; copyable (copy_text is
the body, notice "Copied to clipboard."); closes only on "escape"."""
"""A key in a text dialog: "up"/"down" scroll one line, "pageup"/"pagedown" by
max(visible_lines - 1, 1), "home"/"end" to the top/bottom, clamped so the
last page stays full (scroll <= max(lines.len - visible_lines, 0)); these
Stay. "c" when copyable is Copy(copy_text, copy_notice). "escape" is Close.
Any other key is Close when close_on_any_key, else Stay."""
"""Draw a text dialog of width x height cells: line 1 the title
(class:hq.dialog.title), then the header wrapped at width
(class:hq.dialog) when not "", then available body lines from scroll
(class:hq.text, cut at width), then the footer (class:hq.muted). Return
at most height actual-content lines; never pad the body with blank rows
to reach height. The terminal widget paints unused space. In particular,
when no header is present the result has at most the title, the existing
body lines and the footer, independent of height."""
"""A key in a Yes/No dialog: "left"/"right"/"tab"/"shift+tab" toggle
yes_selected (Stay); "enter" answers the highlighted button; "y" is Yes; "n"
and "escape" are No; other keys Stay."""
"""The prompt wrapped at width (class:hq.dialog), a blank line, then the buttons
"[ No ]" and "[ Yes ]" separated by two spaces, the highlighted one styled
class:hq.button.focused and the other class:hq.button."""
"""An input dialog: Find has title "Find" and placeholder "Search text";
GoToLine "Go To Line" and "Line number"; OpenFile "Open Query" and
"/path/to/file.sql (tab autocompletes, enter opens, esc cancels)"; SaveFile
"Save Query" and "/path/to/file.sql (tab autocompletes, enter saves, esc
cancels)". value is the initial text with the caret at its end; message ""
and no completions."""
"""A key in an input dialog. Printable text inserts at cursor;
"backspace"/"delete" edit; "left"/"right"/"home"/"end" move the caret (all
clear message and completions, Stay). "escape" is Cancel. "tab" for OpenFile
and SaveFile is Complete(value) (the caller supplies completions with
apply_completions); for other purposes Stay. "enter": an empty value sets
message "Please enter a value." (Stay); for GoToLine a value that is not a
whole number >= 1 sets message "Please enter a line number." (Stay);
otherwise Submit(value)."""
"""After a Tab in a path input: with exactly one completion, value becomes it
and the caret moves to its end; with several, value becomes their longest
common prefix when that is longer than value, and completions lists them;
with none, message becomes "No matching files." ."""
"""The title (class:hq.dialog.title), the input line showing value (or the
placeholder in class:hq.muted when empty) with the caret cell styled
class:hq.cursor, the message (class:hq.error) when not "", then up to 8
completions (class:hq.muted), cut at width."""
"""The context menu for entry: items "Insert Name at Cursor" followed by
interactions (from real.harlequin.adapters.catalog_interactions), selected 0."""
""""up"/"down" move the highlight (clamped); "enter" is Choose(items[selected]);
"escape" (and "full_stop") is Close; other keys Stay."""
"""At most 10 item lines, scrolled so selected is visible, each " {item} " padded
to the terminal's 16-bit column width (class:hq.dialog, plus
" class:hq.cursor" on the highlighted item)."""
__all__ = ["ConfirmModal", "ConfirmOutcome", "ConfirmOutcome_No", "ConfirmOutcome_Stay", "ConfirmOutcome_Yes", "ConfirmStep", "ContextMenu", "ContextMenuOutcome", "ContextMenuOutcome_Choose", "ContextMenuOutcome_Close", "ContextMenuOutcome_Stay", "ContextMenuStep", "DebugSection", "InputModal", "InputOutcome", "InputOutcome_Cancel", "InputOutcome_Complete", "InputOutcome_Stay", "InputOutcome_Submit", "InputPurpose", "InputPurpose_Find", "InputPurpose_GoToLine", "InputPurpose_OpenFile", "InputPurpose_SaveFile", "InputStep", "LayoutState", "Notification", "Pane", "Pane_Catalog", "Pane_Editor", "Pane_Results", "Pane_RunBar", "RunBar", "RunBarStep", "Severity", "Severity_Error", "Severity_Information", "Severity_Warning", "TextModal", "TextModalOutcome", "TextModalOutcome_Close", "TextModalOutcome_Copy", "TextModalOutcome_Stay", "TextModalStep"]
