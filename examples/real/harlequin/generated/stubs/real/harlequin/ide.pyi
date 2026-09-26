from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.ide_types import ConfirmModal as ConfirmModal, ConfirmOutcome as ConfirmOutcome, ConfirmOutcome_No as ConfirmOutcome_No, ConfirmOutcome_Stay as ConfirmOutcome_Stay, ConfirmOutcome_Yes as ConfirmOutcome_Yes, ConfirmStep as ConfirmStep, ContextMenu as ContextMenu, ContextMenuOutcome as ContextMenuOutcome, ContextMenuOutcome_Choose as ContextMenuOutcome_Choose, ContextMenuOutcome_Close as ContextMenuOutcome_Close, ContextMenuOutcome_Stay as ContextMenuOutcome_Stay, ContextMenuStep as ContextMenuStep, DebugSection as DebugSection, InputModal as InputModal, InputOutcome as InputOutcome, InputOutcome_Cancel as InputOutcome_Cancel, InputOutcome_Complete as InputOutcome_Complete, InputOutcome_Stay as InputOutcome_Stay, InputOutcome_Submit as InputOutcome_Submit, InputPurpose as InputPurpose, InputPurpose_Find as InputPurpose_Find, InputPurpose_GoToLine as InputPurpose_GoToLine, InputPurpose_OpenFile as InputPurpose_OpenFile, InputPurpose_SaveFile as InputPurpose_SaveFile, InputStep as InputStep, LayoutState as LayoutState, Notification as Notification, Pane as Pane, Pane_Catalog as Pane_Catalog, Pane_Editor as Pane_Editor, Pane_Results as Pane_Results, Pane_RunBar as Pane_RunBar, RunBar as RunBar, RunBarStep as RunBarStep, Severity as Severity, Severity_Error as Severity_Error, Severity_Information as Severity_Information, Severity_Warning as Severity_Warning, TextModal as TextModal, TextModalOutcome as TextModalOutcome, TextModalOutcome_Close as TextModalOutcome_Close, TextModalOutcome_Copy as TextModalOutcome_Copy, TextModalOutcome_Stay as TextModalOutcome_Stay, TextModalStep as TextModalStep
from real.harlequin.adapters_types import TransactionMode
from real.harlequin.catalog_types import CatalogEntry
from real.harlequin.keymap_types import FooterHint
from real.harlequin.style_types import StyledLine
"""The layout at startup: focus Editor, sidebar shown, not full screen."""
def initial_layout() -> LayoutState: ...

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
def layout_action(layout: LayoutState, action: str) -> LayoutState: ...

"""The panes shown, in Tab order. Normally Catalog (unless sidebar_hidden),
Editor, RunBar, Results. In full screen: Editor and RunBar when focus is
Editor or RunBar, else Results only."""
def visible_panes(layout: LayoutState) -> CottList[Pane]: ...

"""The Run Query Bar at startup: with a configured limit the checkbox is checked
and limit_text is its decimal text; otherwise unchecked with limit_text
"500". limit_cursor is at the end of limit_text; not running."""
def new_run_bar(limit: Option[U64]) -> RunBar: ...

"""A key while the Run Query Bar has focus. "space" toggles the Limit checkbox
(a checked box requires a valid limit_text, otherwise it stays unchecked).
Digits insert at limit_cursor; "backspace"/"delete" edit; "left"/"right"/
"home"/"end" move the caret; after an edit the checkbox becomes checked when
limit_text is a nonempty whole number >= 0 and unchecked otherwise. "enter"
submits (submit true) when limit_text is valid and nonempty. Other keys do
nothing. submit is false unless stated."""
def run_bar_key(bar: RunBar, key: str, text: str) -> RunBarStep: ...

"""The hard row limit a run uses: Some(int(limit_text)) when the checkbox is
checked and limit_text is a whole number >= 0, else Nothing."""
def effective_limit(bar: RunBar) -> Option[U64]: ...

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
def render_run_bar(bar: RunBar, transaction: Option[TransactionMode], can_cancel: bool, run_label: str, runnable: bool, focused: bool, width: U16) -> StyledLine: ...

"""The Run button caption: "Run Selection" when selection (the selected editor
text) is not blank and valid (the adapter accepted it, or cannot validate),
else "Run Query"."""
def run_label(selection: str, valid: bool) -> str: ...

"""A tab strip: each label as " {label} " styled "class:hq.tab.active" for the
active index and "class:hq.tab" otherwise, separated by nothing, cut at
the terminal's 16-bit column width and padded with spaces to that width."""
def render_tab_bar(labels: CottList[str], active: U64, width: U16) -> StyledLine: ...

"""The footer: for each hint " {key}" styled "class:hq.footer.key" followed by
" {description} " styled "class:hq.footer.description", cut at the terminal's
16-bit column width and padded with spaces styled "class:hq.footer"."""
def render_footer(hints: CottList[FooterHint], width: U16) -> StyledLine: ...

"""A notification shown for 5 seconds (10 seconds for Error), as Harlequin's
toasts: expires_at_ms is now_ms + 5000 or + 10000, saturated at the U64
maximum 18446744073709551615. Saturation preserves the timestamp's ABI
when the caller supplies a monotonic clock reading near its upper bound."""
def notify(title: Option[str], message: str, severity: Severity, now_ms: U64) -> Notification: ...

"""The unexpired notifications (expires_at_ms > now_ms), newest last, each as
its title line (when Some, bold via class:hq.dialog.title) and its message
lines, every line prefixed with "▌ " and styled "class:hq.notification" (or
"class:hq.notification.error" for Error, "class:hq.warning" prefix for
Warning), wrapped at width - 2 cells, with a blank line between
notifications. At most the last 3 notifications are shown."""
def render_notifications(notifications: CottList[Notification], now_ms: U64, width: U64) -> CottList[StyledLine]: ...

"""A copyable text dialog showing body (split into lines on LF), scrolled to
the top, whose copy_text is body. It closes on any key other than scroll
keys and "c"."""
def text_modal(title: str, header: str, body: str, footer: str, copy_notice: str) -> TextModal: ...

"""The View Cell dialog: title column (or "Cell Contents" when column is ""),
header "", body value, footer "Arrows/PgUp/PgDn scroll. Click text or press c
to copy. Any other key closes.", copy notice "Cell value copied to
clipboard."."""
def cell_modal(column: str, value: str) -> TextModal: ...

"""An error dialog (Query Error, Export Data Error, Catalog Error, ...): the
given title and header, body message, footer "Arrows/PgUp/PgDn scroll. Click
text or press c to copy. Any other key closes.", copy notice "Error copied to
clipboard."."""
def error_modal(title: str, header: str, message: str) -> TextModal: ...

"""The help screen (F1): title "Harlequin Help", header "Welcome to Harlequin!
This screen contains a small subset of the online docs, available at
https://harlequin.sh/docs/getting-started", body = the key reference lines
(key_lines, from real.harlequin.keymap.help_lines), a blank line, then the
lines of help_markdown(); footer "Scroll with arrows. Press any other key to
continue."; not copyable; closes on any non-scroll key."""
def help_modal(key_lines: CottList[str]) -> TextModal: ...

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
def help_markdown() -> str: ...

"""The debug screen (F12): title "Debug Information", header "Details about the
current Harlequin session, environment, and adapter.", body: for each section
a line "## {title}", its body lines and a blank line; footer "Tab/Shift Tab to
move focus, Enter to expand/collapse, Esc to close."; copyable (copy_text is
the body, notice "Copied to clipboard."); closes only on "escape"."""
def debug_modal(sections: CottList[DebugSection]) -> TextModal: ...

"""A key in a text dialog: "up"/"down" scroll one line, "pageup"/"pagedown" by
max(visible_lines - 1, 1), "home"/"end" to the top/bottom, clamped so the
last page stays full (scroll <= max(lines.len - visible_lines, 0)); these
Stay. "c" when copyable is Copy(copy_text, copy_notice). "escape" is Close.
Any other key is Close when close_on_any_key, else Stay."""
def text_modal_key(modal: TextModal, key: str, visible_lines: U64) -> TextModalStep: ...

"""Draw a text dialog of width x height cells: line 1 the title
(class:hq.dialog.title), then the header wrapped at width
(class:hq.dialog) when not "", then available body lines from scroll
(class:hq.text, cut at width), then the footer (class:hq.muted). Return
at most height actual-content lines; never pad the body with blank rows
to reach height. The terminal widget paints unused space. In particular,
when no header is present the result has at most the title, the existing
body lines and the footer, independent of height."""
def render_text_modal(modal: TextModal, width: U64, height: U64) -> CottList[StyledLine]: ...

"""A key in a Yes/No dialog: "left"/"right"/"tab"/"shift+tab" toggle
yes_selected (Stay); "enter" answers the highlighted button; "y" is Yes; "n"
and "escape" are No; other keys Stay."""
def confirm_key(modal: ConfirmModal, key: str) -> ConfirmStep: ...

"""The prompt wrapped at width (class:hq.dialog), a blank line, then the buttons
"[ No ]" and "[ Yes ]" separated by two spaces, the highlighted one styled
class:hq.button.focused and the other class:hq.button."""
def render_confirm(modal: ConfirmModal, width: U64) -> CottList[StyledLine]: ...

"""An input dialog: Find has title "Find" and placeholder "Search text";
GoToLine "Go To Line" and "Line number"; OpenFile "Open Query" and
"/path/to/file.sql (tab autocompletes, enter opens, esc cancels)"; SaveFile
"Save Query" and "/path/to/file.sql (tab autocompletes, enter saves, esc
cancels)". value is the initial text with the caret at its end; message ""
and no completions."""
def input_modal(purpose: InputPurpose, value: str) -> InputModal: ...

"""A key in an input dialog. Printable text inserts at cursor;
"backspace"/"delete" edit; "left"/"right"/"home"/"end" move the caret (all
clear message and completions, Stay). "escape" is Cancel. "tab" for OpenFile
and SaveFile is Complete(value) (the caller supplies completions with
apply_completions); for other purposes Stay. "enter": an empty value sets
message "Please enter a value." (Stay); for GoToLine a value that is not a
whole number >= 1 sets message "Please enter a line number." (Stay);
otherwise Submit(value)."""
def input_key(modal: InputModal, key: str, text: str) -> InputStep: ...

"""After a Tab in a path input: with exactly one completion, value becomes it
and the caret moves to its end; with several, value becomes their longest
common prefix when that is longer than value, and completions lists them;
with none, message becomes "No matching files." ."""
def apply_completions(modal: InputModal, completions: CottList[str]) -> InputModal: ...

"""The title (class:hq.dialog.title), the input line showing value (or the
placeholder in class:hq.muted when empty) with the caret cell styled
class:hq.cursor, the message (class:hq.error) when not "", then up to 8
completions (class:hq.muted), cut at width."""
def render_input_modal(modal: InputModal, width: U64) -> CottList[StyledLine]: ...

"""The context menu for entry: items "Insert Name at Cursor" followed by
interactions (from real.harlequin.adapters.catalog_interactions), selected 0."""
def context_menu(entry: CatalogEntry, interactions: CottList[str]) -> ContextMenu: ...

""""up"/"down" move the highlight (clamped); "enter" is Choose(items[selected]);
"escape" (and "full_stop") is Close; other keys Stay."""
def context_menu_key(menu: ContextMenu, key: str) -> ContextMenuStep: ...

"""At most 10 item lines, scrolled so selected is visible, each " {item} " padded
to the terminal's 16-bit column width (class:hq.dialog, plus
" class:hq.cursor" on the highlighted item)."""
def render_context_menu(menu: ContextMenu, width: U16) -> CottList[StyledLine]: ...

__all__ = ["ConfirmModal", "ConfirmOutcome", "ConfirmOutcome_No", "ConfirmOutcome_Stay", "ConfirmOutcome_Yes", "ConfirmStep", "ContextMenu", "ContextMenuOutcome", "ContextMenuOutcome_Choose", "ContextMenuOutcome_Close", "ContextMenuOutcome_Stay", "ContextMenuStep", "DebugSection", "InputModal", "InputOutcome", "InputOutcome_Cancel", "InputOutcome_Complete", "InputOutcome_Stay", "InputOutcome_Submit", "InputPurpose", "InputPurpose_Find", "InputPurpose_GoToLine", "InputPurpose_OpenFile", "InputPurpose_SaveFile", "InputStep", "LayoutState", "Notification", "Pane", "Pane_Catalog", "Pane_Editor", "Pane_Results", "Pane_RunBar", "RunBar", "RunBarStep", "Severity", "Severity_Error", "Severity_Information", "Severity_Warning", "TextModal", "TextModalOutcome", "TextModalOutcome_Close", "TextModalOutcome_Copy", "TextModalOutcome_Stay", "TextModalStep", "apply_completions", "cell_modal", "confirm_key", "context_menu", "context_menu_key", "debug_modal", "effective_limit", "error_modal", "help_markdown", "help_modal", "initial_layout", "input_key", "input_modal", "layout_action", "new_run_bar", "notify", "render_confirm", "render_context_menu", "render_footer", "render_input_modal", "render_notifications", "render_run_bar", "render_tab_bar", "render_text_modal", "run_bar_key", "run_label", "text_modal", "text_modal_key", "visible_panes"]
