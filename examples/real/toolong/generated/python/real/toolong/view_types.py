from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.toolong.keys_types import KeyEvent, TextInput
from real.toolong.model_types import Rect, TabPlan, TimeUnit

"""Which widget has keyboard focus: the tab strip, the log lines of the active
tab, its line panel, or one of its find dialog widgets (the find input, the
"Case sensitive" checkbox, the "Regex" checkbox)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Focus_Tabs:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Focus_Lines:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Focus_Panel:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Focus_FindInput:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Focus_FindCase:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Focus_FindRegex:
    pass

Focus: TypeAlias = Union[Focus_Tabs, Focus_Lines, Focus_Panel, Focus_FindInput, Focus_FindCase, Focus_FindRegex]

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

"""A toast notification, shown until the viewer clock reaches expires_ms."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Notification:
    __hash__ = None
    title: str
    message: str
    severity: Severity
    expires_ms: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "title", _cott_validate_abi(self.title, str, path="$.title"))
        if not _cott_validated_construction():
            object.__setattr__(self, "message", _cott_validate_abi(self.message, str, path="$.message"))
        if not _cott_validated_construction():
            object.__setattr__(self, "severity", _cott_validate_abi(self.severity, Severity, path="$.severity"))
        if not _cott_validated_construction():
            object.__setattr__(self, "expires_ms", _cott_validate_abi(self.expires_ms, U64, path="$.expires_ms"))

"""A modal screen over the log view: none, the help screen scrolled by scroll
rows, or the go-to-line input."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Modal_Closed:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Modal_Help:
    __hash__ = None
    scroll: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Modal_Goto:
    __hash__ = None
    input: TextInput

Modal: TypeAlias = Union[Modal_Closed, Modal_Help, Modal_Goto]

"""The state of one tab (Toolong's LogView with its LogLines, LinePanel,
FindDialog, InfoOverlay and LogFooter).

title: the tab label. file_names: the final path component of each file.
merged: several files merged into one view. can_tail: false for a merged
view. tail: the view follows the end of the file. scroll_x/scroll_y: scroll
offsets in cells/lines. pointer: the pointer line (pointer mode) if any.
line_numbers: the line-number gutter is shown. show_panel: the line panel is
shown; panel_scroll_x/panel_scroll_y: its scroll offsets; panel_lines and
panel_width: the size of its content as last reported. show_find: the find
dialog is shown; find_input: its text input; case_sensitive and regex: its
checkboxes. break_count: lines known to the index (single file: number of
breaks; merged: number of merged lines). line_count: lines currently
displayed. content_width: the widest rendered line so far in cells.
pending_lines: the "+N lines" count of new lines while not tailing (0 hides
it). loading: the loading indicator is shown. scan_running: the initial
scan (or merge) is still running and escape cancels it. scan_tint: the
lines are dimmed because the scan has not completed. scan_message and
scan_progress: the scan progress box message ("" hides it) and completion
from 0.0 to 1.0."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TabView:
    __hash__ = None
    title: str
    file_names: CottList[str]
    merged: bool
    can_tail: bool
    tail: bool
    scroll_x: U64
    scroll_y: U64
    pointer: Option[U64]
    line_numbers: bool
    show_panel: bool
    panel_scroll_x: U64
    panel_scroll_y: U64
    panel_lines: U64
    panel_width: U64
    show_find: bool
    find_input: TextInput
    case_sensitive: bool
    regex: bool
    break_count: U64
    line_count: U64
    content_width: U64
    pending_lines: U64
    loading: bool
    scan_running: bool
    scan_tint: bool
    scan_message: str
    scan_progress: F64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "title", _cott_validate_abi(self.title, str, path="$.title"))
        if not _cott_validated_construction():
            object.__setattr__(self, "file_names", _cott_validate_abi(self.file_names, CottList[str], path="$.file_names"))
        if not _cott_validated_construction():
            object.__setattr__(self, "merged", _cott_validate_abi(self.merged, bool, path="$.merged"))
        if not _cott_validated_construction():
            object.__setattr__(self, "can_tail", _cott_validate_abi(self.can_tail, bool, path="$.can_tail"))
        if not _cott_validated_construction():
            object.__setattr__(self, "tail", _cott_validate_abi(self.tail, bool, path="$.tail"))
        if not _cott_validated_construction():
            object.__setattr__(self, "scroll_x", _cott_validate_abi(self.scroll_x, U64, path="$.scroll_x"))
        if not _cott_validated_construction():
            object.__setattr__(self, "scroll_y", _cott_validate_abi(self.scroll_y, U64, path="$.scroll_y"))
        if not _cott_validated_construction():
            object.__setattr__(self, "pointer", _cott_validate_abi(self.pointer, Option[U64], path="$.pointer"))
        if not _cott_validated_construction():
            object.__setattr__(self, "line_numbers", _cott_validate_abi(self.line_numbers, bool, path="$.line_numbers"))
        if not _cott_validated_construction():
            object.__setattr__(self, "show_panel", _cott_validate_abi(self.show_panel, bool, path="$.show_panel"))
        if not _cott_validated_construction():
            object.__setattr__(self, "panel_scroll_x", _cott_validate_abi(self.panel_scroll_x, U64, path="$.panel_scroll_x"))
        if not _cott_validated_construction():
            object.__setattr__(self, "panel_scroll_y", _cott_validate_abi(self.panel_scroll_y, U64, path="$.panel_scroll_y"))
        if not _cott_validated_construction():
            object.__setattr__(self, "panel_lines", _cott_validate_abi(self.panel_lines, U64, path="$.panel_lines"))
        if not _cott_validated_construction():
            object.__setattr__(self, "panel_width", _cott_validate_abi(self.panel_width, U64, path="$.panel_width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "show_find", _cott_validate_abi(self.show_find, bool, path="$.show_find"))
        if not _cott_validated_construction():
            object.__setattr__(self, "find_input", _cott_validate_abi(self.find_input, TextInput, path="$.find_input"))
        if not _cott_validated_construction():
            object.__setattr__(self, "case_sensitive", _cott_validate_abi(self.case_sensitive, bool, path="$.case_sensitive"))
        if not _cott_validated_construction():
            object.__setattr__(self, "regex", _cott_validate_abi(self.regex, bool, path="$.regex"))
        if not _cott_validated_construction():
            object.__setattr__(self, "break_count", _cott_validate_abi(self.break_count, U64, path="$.break_count"))
        if not _cott_validated_construction():
            object.__setattr__(self, "line_count", _cott_validate_abi(self.line_count, U64, path="$.line_count"))
        if not _cott_validated_construction():
            object.__setattr__(self, "content_width", _cott_validate_abi(self.content_width, U64, path="$.content_width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "pending_lines", _cott_validate_abi(self.pending_lines, U64, path="$.pending_lines"))
        if not _cott_validated_construction():
            object.__setattr__(self, "loading", _cott_validate_abi(self.loading, bool, path="$.loading"))
        if not _cott_validated_construction():
            object.__setattr__(self, "scan_running", _cott_validate_abi(self.scan_running, bool, path="$.scan_running"))
        if not _cott_validated_construction():
            object.__setattr__(self, "scan_tint", _cott_validate_abi(self.scan_tint, bool, path="$.scan_tint"))
        if not _cott_validated_construction():
            object.__setattr__(self, "scan_message", _cott_validate_abi(self.scan_message, str, path="$.scan_message"))
        if not _cott_validated_construction():
            object.__setattr__(self, "scan_progress", _cott_validate_abi(self.scan_progress, F64, path="$.scan_progress"))

"""The whole viewer: its tabs, the active tab, the focused widget, the open
modal, the notifications, the current find suggestion for the active tab's
find input ("" for none), the terminal size and the viewer clock."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerState:
    __hash__ = None
    tabs: CottList[TabView]
    active: U32
    focus: Focus
    modal: Modal
    notifications: CottList[Notification]
    suggestion: str
    width: U16
    height: U16
    now_ms: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "tabs", _cott_validate_abi(self.tabs, CottList[TabView], path="$.tabs"))
        if not _cott_validated_construction():
            object.__setattr__(self, "active", _cott_validate_abi(self.active, U32, path="$.active"))
        if not _cott_validated_construction():
            object.__setattr__(self, "focus", _cott_validate_abi(self.focus, Focus, path="$.focus"))
        if not _cott_validated_construction():
            object.__setattr__(self, "modal", _cott_validate_abi(self.modal, Modal, path="$.modal"))
        if not _cott_validated_construction():
            object.__setattr__(self, "notifications", _cott_validate_abi(self.notifications, CottList[Notification], path="$.notifications"))
        if not _cott_validated_construction():
            object.__setattr__(self, "suggestion", _cott_validate_abi(self.suggestion, str, path="$.suggestion"))
        if not _cott_validated_construction():
            object.__setattr__(self, "width", _cott_validate_abi(self.width, U16, path="$.width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "height", _cott_validate_abi(self.height, U16, path="$.height"))
        if not _cott_validated_construction():
            object.__setattr__(self, "now_ms", _cott_validate_abi(self.now_ms, U64, path="$.now_ms"))

"""The screen regions of the active tab. tabs: the three-row tab strip (only
with more than one tab). find: the four-row find dialog (only when shown).
lines_box: the bordered log lines widget. text: the area inside its border
where lines are drawn (excluding the two-column vertical scrollbar and the
one-row horizontal scrollbar). panel: the line panel (only when shown).
footer: the last row. gutter: the width of the pointer/line-number gutter at
the left of text."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerLayout:
    __hash__ = None
    tabs: Option[Rect]
    find: Option[Rect]
    lines_box: Rect
    text: Rect
    panel: Option[Rect]
    footer: Rect
    gutter: U16

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "tabs", _cott_validate_abi(self.tabs, Option[Rect], path="$.tabs"))
        if not _cott_validated_construction():
            object.__setattr__(self, "find", _cott_validate_abi(self.find, Option[Rect], path="$.find"))
        if not _cott_validated_construction():
            object.__setattr__(self, "lines_box", _cott_validate_abi(self.lines_box, Rect, path="$.lines_box"))
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, Rect, path="$.text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "panel", _cott_validate_abi(self.panel, Option[Rect], path="$.panel"))
        if not _cott_validated_construction():
            object.__setattr__(self, "footer", _cott_validate_abi(self.footer, Rect, path="$.footer"))
        if not _cott_validated_construction():
            object.__setattr__(self, "gutter", _cott_validate_abi(self.gutter, U16, path="$.gutter"))

"""A Textual action, triggered by a key binding or a click on a footer key."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_Quit:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_Help:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_FocusNext:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_FocusPrevious:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_PreviousTab:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_NextTab:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_ScrollUp:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_ScrollDown:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_ScrollLeft:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_ScrollRight:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_ScrollHome:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_ScrollEnd:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_PageUp:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_PageDown:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_Select:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_Dismiss:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_Navigate:
    __hash__ = None
    steps: I32
    unit: TimeUnit

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_ToggleTail:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_ToggleLineNumbers:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_ShowFind:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_Goto:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_DismissFind:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_PointerDown:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_PointerUp:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_ToggleCase:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_ToggleRegex:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_PanelUp:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_PanelDown:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_PanelLeft:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_PanelRight:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_PanelHome:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_PanelEnd:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_PanelPageUp:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_PanelPageDown:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_HelpUp:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_HelpDown:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_HelpHome:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_HelpEnd:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_HelpPageUp:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_HelpPageDown:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_CloseHelp:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_OpenLink:
    __hash__ = None
    url: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_CloseGoto:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerAction_Tail:
    pass

ViewerAction: TypeAlias = Union[ViewerAction_Quit, ViewerAction_Help, ViewerAction_FocusNext, ViewerAction_FocusPrevious, ViewerAction_PreviousTab, ViewerAction_NextTab, ViewerAction_ScrollUp, ViewerAction_ScrollDown, ViewerAction_ScrollLeft, ViewerAction_ScrollRight, ViewerAction_ScrollHome, ViewerAction_ScrollEnd, ViewerAction_PageUp, ViewerAction_PageDown, ViewerAction_Select, ViewerAction_Dismiss, ViewerAction_Navigate, ViewerAction_ToggleTail, ViewerAction_ToggleLineNumbers, ViewerAction_ShowFind, ViewerAction_Goto, ViewerAction_DismissFind, ViewerAction_PointerDown, ViewerAction_PointerUp, ViewerAction_ToggleCase, ViewerAction_ToggleRegex, ViewerAction_PanelUp, ViewerAction_PanelDown, ViewerAction_PanelLeft, ViewerAction_PanelRight, ViewerAction_PanelHome, ViewerAction_PanelEnd, ViewerAction_PanelPageUp, ViewerAction_PanelPageDown, ViewerAction_HelpUp, ViewerAction_HelpDown, ViewerAction_HelpHome, ViewerAction_HelpEnd, ViewerAction_HelpPageUp, ViewerAction_HelpPageDown, ViewerAction_CloseHelp, ViewerAction_OpenLink, ViewerAction_CloseGoto, ViewerAction_Tail]

"""Work the viewer asks its driver to do: ring the bell, quit, search for the
next find match from line start in direction, jump by time from from_line,
cancel a tab's initial scan, open a URL in the web browser, or compute the
find suggestion for value."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerRequest_Bell:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerRequest_Quit:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerRequest_FindNext:
    __hash__ = None
    tab: U32
    start: I64
    direction: I8

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerRequest_Navigate:
    __hash__ = None
    tab: U32
    from_line: U64
    steps: I32
    unit: TimeUnit

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerRequest_CancelScan:
    __hash__ = None
    tab: U32

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerRequest_OpenLink:
    __hash__ = None
    url: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerRequest_Suggest:
    __hash__ = None
    tab: U32
    value: str

ViewerRequest: TypeAlias = Union[ViewerRequest_Bell, ViewerRequest_Quit, ViewerRequest_FindNext, ViewerRequest_Navigate, ViewerRequest_CancelScan, ViewerRequest_OpenLink, ViewerRequest_Suggest]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerUpdate:
    __hash__ = None
    viewer: ViewerState
    requests: CottList[ViewerRequest]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "viewer", _cott_validate_abi(self.viewer, ViewerState, path="$.viewer"))
        if not _cott_validated_construction():
            object.__setattr__(self, "requests", _cott_validate_abi(self.requests, CottList[ViewerRequest], path="$.requests"))

"""Something the driver observed: the clock, a terminal resize, a notification
to show, scan progress, a scan batch (count is the total number of breaks
now), the end of a scan (count is the total number of breaks, or of merged
lines for a merged tab), new lines read while tailing (break totals before
and after), a failure to open a single file, a tab's loading finished, the
widest rendered line, the line panel content size, a find suggestion for a
find input value, a find search result and a time navigation result."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerEvent_Tick:
    __hash__ = None
    now_ms: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerEvent_Resize:
    __hash__ = None
    width: U16
    height: U16

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerEvent_Notify:
    __hash__ = None
    title: str
    message: str
    severity: Severity

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerEvent_Progress:
    __hash__ = None
    tab: U32
    message: str
    progress: F64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerEvent_Breaks:
    __hash__ = None
    tab: U32
    count: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerEvent_Complete:
    __hash__ = None
    tab: U32
    count: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerEvent_Tailed:
    __hash__ = None
    tab: U32
    before: U64
    after: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerEvent_OpenFailed:
    __hash__ = None
    tab: U32
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerEvent_Loaded:
    __hash__ = None
    tab: U32

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerEvent_Widths:
    __hash__ = None
    tab: U32
    width: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerEvent_PanelSize:
    __hash__ = None
    tab: U32
    lines: U64
    width: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerEvent_Suggestion:
    __hash__ = None
    value: str
    suggestion: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerEvent_Found:
    __hash__ = None
    tab: U32
    line: Option[U64]
    invalid_regex: bool

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerEvent_Jumped:
    __hash__ = None
    tab: U32
    line: Option[U64]

ViewerEvent: TypeAlias = Union[ViewerEvent_Tick, ViewerEvent_Resize, ViewerEvent_Notify, ViewerEvent_Progress, ViewerEvent_Breaks, ViewerEvent_Complete, ViewerEvent_Tailed, ViewerEvent_OpenFailed, ViewerEvent_Loaded, ViewerEvent_Widths, ViewerEvent_PanelSize, ViewerEvent_Suggestion, ViewerEvent_Found, ViewerEvent_Jumped]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MouseKind_Click:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MouseKind_WheelUp:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MouseKind_WheelDown:
    pass

MouseKind: TypeAlias = Union[MouseKind_Click, MouseKind_WheelUp, MouseKind_WheelDown]

"""A mouse event at terminal cell (x, y)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MouseEvent:
    __hash__ = None
    x: U16
    y: U16
    kind: MouseKind

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "x", _cott_validate_abi(self.x, U16, path="$.x"))
        if not _cott_validated_construction():
            object.__setattr__(self, "y", _cott_validate_abi(self.y, U16, path="$.y"))
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, MouseKind, path="$.kind"))

"""A key shown in a footer: the binding key, how it is displayed, its
description and the action it runs when clicked."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FooterKey:
    __hash__ = None
    key: str
    display: str
    description: str
    action: ViewerAction

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "key", _cott_validate_abi(self.key, str, path="$.key"))
        if not _cott_validated_construction():
            object.__setattr__(self, "display", _cott_validate_abi(self.display, str, path="$.display"))
        if not _cott_validated_construction():
            object.__setattr__(self, "description", _cott_validate_abi(self.description, str, path="$.description"))
        if not _cott_validated_construction():
            object.__setattr__(self, "action", _cott_validate_abi(self.action, ViewerAction, path="$.action"))

"""The viewer before any file is read. One TabView per plan, in order:
title from the plan; file_names the final path component of each plan
path; merged from the plan; can_tail is not merged; tail false; all
scrolls 0; pointer Nothing; line_numbers, show_panel, show_find,
case_sensitive and regex false; panel_lines, panel_width, break_count,
line_count, content_width and pending_lines 0; find_input empty with
cursor 0; loading, scan_running and scan_tint true; scan_message "";
scan_progress 0.0. active 0; focus Lines (the visible tab's lines; upstream
1.4.0 initially focuses the last tab's hidden lines, which this
reimplementation does not reproduce); modal Closed; no notifications;
suggestion ""; the given size; now_ms 0."""
"""The Textual layout of the active tab (W = width, H = height; every
subtraction below saturates at 0). footer is Rect(0, H - 1, W, 1) (height
0 when H is 0). With more than one tab, tabs is Rect(0, 0, W, 3) and the
body starts at row 3, else at row 0 and tabs is Nothing. When the active
tab shows its find dialog, find is Rect(0, top, W, 4) and the body starts
4 rows lower. The body is the rows from its start to H - 1 (exclusive).
When the active tab shows its panel, panel is Rect(W - W // 2, top, W // 2,
body height) and lines_box is Rect(0, top, W - W // 2, body height);
otherwise panel is Nothing and lines_box spans the full width. text is
Rect(lines_box.x + 1, lines_box.y + 1, lines_box.width - 4,
lines_box.height - 3). gutter is, when line_numbers is on, the number of
decimal digits of scroll_y + text.height + 1 plus one, and 0 otherwise,
plus 3 when the pointer is set. With no tabs every rectangle except the
footer is empty and gutter is 0."""
"""The keys of the footer bar.

With the help modal open: A "Author" OpenLink("https://www.willmcgugan.com"),
T "Textual" OpenLink("https://www.textualize.io/"), R "Repository"
OpenLink("https://github.com/Textualize/toolong"), L "Logmerger"
OpenLink("https://github.com/ptmcg/logmerger"), with key "a", "t", "r",
"l" and display "A", "T", "R", "L".

Otherwise (also under the go-to modal) Toolong's LogFooter keys for the
focused widget: first f1 "Help" (key "f1", display "f1", action Help).
When focus is not Tabs, then: ctrl+t "^t" "Tail" ToggleTail only when the
active tab can_tail; ctrl+l "^l" "Line nos." ToggleLineNumbers; ctrl+f
"^f" "Find" ShowFind unless focus is FindInput; ctrl+g "^g" "Go to" Goto.
When focus is FindInput, FindCase or FindRegex, then also down "↓" "Next"
PointerDown and up "↑" "Previous" PointerUp."""
"""Run one action. "The view" is the active tab; page is text.height and
gutter is from real.toolong.view.viewer_layout(viewer); max_scroll_y is
line_count - page and max_scroll_x is content_width plus the gutter (only
when the pointer is set or line numbers are on) minus text.width, both
saturating at 0. Scroll offsets are always clamped to [0, max]. Setting
the pointer clamps it to [0, line_count - 1] (Nothing when line_count is
0). Centering the pointer sets scroll_y to pointer - page // 2, clamped.
Whenever the pointer becomes Nothing, show_panel becomes false; whenever
the pointer changes, both panel scrolls reset to 0.
"Tail on" (only when tail was false): tail true; for a single-file view
line_count becomes max(1, break_count); scroll_y becomes max_scroll_y;
pointer Nothing; pending_lines 0. "Tail off" (only when tail was true):
tail false; pending_lines 0. Hiding the find dialog sets show_find false,
the pointer Nothing and focus Lines. Showing it sets show_find true and
focus FindInput. A panel hide while focus is Panel moves focus to Lines.
A notification is appended with expires_ms = now_ms + 5000. Requests are
returned in the order they arise.

Quit: request Quit. Help: modal Help(0). Goto: modal Goto with value the
decimal pointer + 1 (or scroll_y + 1) and cursor at its end. CloseHelp and
CloseGoto: modal Closed. OpenLink(url): notification title "Link", message
"Opening " + url, Information, then request OpenLink(url). Help scroll
actions (HelpUp/Down by 1, HelpPageUp/PageDown by the help content height,
HelpHome/End) change the Help modal scroll within [0, max], where the help
box is Rect(8, 4, W - 16, H - 9), its content is (box width - 4) cells
wide and (box height - 2) rows tall, and max is the number of lines of
real.toolong.help.help_title(content width) plus the number of StyledText
values in the tuple wrapped by real.toolong.help.help_markdown(content
width), minus the content height.

FocusNext/FocusPrevious cycle through the focus chain: Tabs (only with
more than one tab), Lines, Panel (only when show_panel), then FindInput,
FindCase, FindRegex (only when show_find); from a focus not in the chain
they go to its first/last element. PreviousTab/NextTab change active by
-1/+1 modulo the number of tabs.

ScrollUp: without pointer scroll_y - 1, with pointer advance(-1); then
tail off. ScrollDown: without pointer scroll_y + 1, with pointer
advance(+1). ScrollLeft/ScrollRight: scroll_x -1/+1. ScrollHome: pointer
(when set) becomes 0, scroll_y 0, tail off. ScrollEnd: pointer (when set)
becomes line_count; then if scroll_y already equals max_scroll_y tail on,
else scroll_y = max_scroll_y and tail off. PageDown/PageUp: without
pointer scroll_y +/- page; with pointer, pointer +/- page then center;
tail off. Select: without pointer, pointer = scroll_y; with pointer,
toggle show_panel. Dismiss: when scan_running, request CancelScan(active)
and add a Warning notification "Stopped scanning. Some lines may not be
available." (empty title); otherwise hide the find dialog if shown, else
hide the panel if shown, else set the pointer to Nothing.

advance(direction): with show_find, start = pointer + direction, or
without pointer scroll_y (direction +1) / scroll_y + page - 1 (direction
-1), and request FindNext(active, start, direction). Without show_find the
pointer moves to that same start line when it lies within [0,
line_count - 1]; otherwise it is set to the old pointer, or to scroll_y
when the old pointer is Nothing or 0; then, unless the pointer was Nothing
before, center it when it lies outside rows [scroll_y, scroll_y + page -
1].

Navigate(steps, unit): request Navigate(active, pointer or scroll_y,
steps, unit). ToggleTail: when can_tail is false add an Error notification
titled "Tail" with message "Can't tail merged files"; otherwise tail on or
off. ToggleLineNumbers: flip line_numbers. ShowFind: unless the find
dialog is shown and focus is FindInput, show it. DismissFind: hide the
find dialog. PointerDown/PointerUp: advance(+1)/advance(-1). ToggleCase /
ToggleRegex: flip case_sensitive / regex. Panel actions scroll the panel:
Up/Down by 1 row, Left/Right by 1 cell, PageUp/PageDown by the panel
content height (panel height - 2), Home/End to 0 / the end, clamped with
max rows panel_lines - (panel height - 2) and max columns panel_width -
(panel width - 6). Tail: tail on. With no tabs, only Quit, Help,
CloseHelp, OpenLink and the help scroll actions have an effect."""
"""Route one key press with Textual's precedence and run the resulting
action with real.toolong.view.apply_action (or edit an input with
real.toolong.keys.edit_input). Keys with no effect return the state
unchanged and no requests.

ctrl+c always runs Quit.

Help modal: escape CloseHelp; a/t/r/l OpenLink of the Author, Textual,
Repository and Logmerger URLs listed in real.toolong.view.footer_keys;
up HelpUp, down HelpDown, pageup HelpPageUp, pagedown HelpPageDown, home
HelpHome, end HelpEnd.

Go-to modal: offer the key to its input (integer_only, no suggestion).
When the input handled the key: store the new input; request Bell when the
edit rang the bell; when the value changed, parse it with Python int():
success sets the pointer of the active tab to value - 1 (clamped) and
centers it, failure sets the pointer to Nothing. Otherwise escape runs
CloseGoto.

No modal, by focus:
Lines: escape Dismiss; up and k ScrollUp; down and j ScrollDown; left
ScrollLeft; right ScrollRight; home ScrollHome; end ScrollEnd; pageup
PageUp; pagedown PageDown; enter Select; m Navigate(1, Minute), M
Navigate(-1, Minute), h Navigate(1, Hour), H Navigate(-1, Hour), d
Navigate(1, Day), D Navigate(-1, Day).
Panel: up PanelUp, down PanelDown, left PanelLeft, right PanelRight, home
PanelHome, end PanelEnd, pageup PanelPageUp, pagedown PanelPageDown.
Tabs: left PreviousTab, right NextTab.
FindInput: first offer the key to the input (suggestion is the state's
suggestion, not integer_only). When handled: store it; request Bell when
it rang; when the value changed, clear the suggestion, set the pointer to
Nothing when the new value is empty and request Suggest(active, value)
when it is not; when submitted, toggle show_panel.
FindCase / FindRegex: enter and space ToggleCase / ToggleRegex.
Then, for FindInput, FindCase and FindRegex: escape DismissFind; down and j
PointerDown; up and k PointerUp.
Then, for every focus except Tabs: ctrl+t ToggleTail; ctrl+l
ToggleLineNumbers; ctrl+f and slash ShowFind; ctrl+g Goto.
Then, for every focus: f1 Help; tab FocusNext; shift+tab FocusPrevious.
A key is used by the first rule above that matches it."""
"""Apply an observation, with the conventions of
real.toolong.view.apply_action (clamping, pointer, tail on/off,
notifications); tab indexes out of range are ignored.

Tick(now_ms): set now_ms and drop notifications whose expires_ms <= now_ms.
Resize: set the size and clamp every tab's scrolls with the new layout.
Notify: append the notification. Progress: set scan_message and
scan_progress. Breaks(count): break_count = count, loading false, and for
a single-file tab line_count = max(1, count). Complete(count): break_count
= count; line_count = max(1, count) for a single file and count for a
merged tab; loading, scan_running and scan_tint false; scan_message "";
then tail on. Tailed(before, after): when tail is off, pending_lines =
before - line_count + 1 (saturating at 0); loading false; break_count =
after; when tail is on or before is 0, line_count = max(1, after); when
tail is on, scroll_y = max_scroll_y. OpenFailed(message): an Error
notification with that message and empty title; loading and scan_running
false (scan_tint stays). Loaded: loading false. Widths(width):
content_width = max(content_width, width). PanelSize(lines, width): store
them and clamp the panel scrolls. Suggestion(value, suggestion): when value
equals the active tab's find input value, the state's suggestion becomes
suggestion. Found(line, invalid_regex): first, when invalid_regex, an Error
notification "Regex is invalid!"; then with Some(line) set the pointer to
line and center it; with Nothing request Bell and, when the pointer is set
and outside rows [scroll_y, scroll_y + page - 1], center it.
Jumped(line): Nothing requests Bell; Some(line) sets the pointer and
centers it."""
"""Route a mouse event using real.toolong.view.viewer_layout; meta is the
footer meta text currently shown. Cell widths are rich cell widths.

Help modal: WheelUp/WheelDown scroll the help 2 rows up/down (clamped as
HelpUp/HelpDown are); a Click on the last row inside " A " + " Author ",
" T " + " Textual ", " R " + " Repository ", " L " + " Logmerger " laid out
left to right from column 0 runs that key's OpenLink. Go-to modal: nothing.

No modal, checked in this order:
Footer row: a Click inside a footer key (real.toolong.view.footer_keys,
laid out from column 0, each len(display) + 1 + len(description) + 1
cells wide) runs its action; a Click in the last len(meta) + 2 columns
runs Goto.
New-lines overlay (shown when the active tab is not tailing and
pending_lines > 0): the label " +N lines " (N with thousands separators)
starting at column lines_box.x + (lines_box.width - label width) // 2 on
the row above the footer; a Click on it runs Tail.
Tab strip row 1: tab i's label " " + title + " " starts at column 1 for
the first tab and one column after the previous label; a Click on it makes
it active and focuses Tabs.
Find dialog rows find.y + 1 to find.y + 3: a Click in columns [0, W - 35)
focuses FindInput with the cursor at min(len(value), max(0, x - 3)); in
[W - 35, W - 13) focuses FindCase and runs ToggleCase; in [W - 13, W)
focuses FindRegex and runs ToggleRegex.
Lines box: a Click focuses Lines; when it is on a text row and loading is
false, line = scroll_y + (y - text.y): when line equals the pointer toggle
show_panel, then set the pointer to line and turn tail off. WheelUp /
WheelDown on the box scroll 2 lines up / down and turn tail off.
Panel: a Click focuses Panel; wheels scroll it 2 rows.
Anything else has no effect."""
__all__ = ["Focus", "Focus_FindCase", "Focus_FindInput", "Focus_FindRegex", "Focus_Lines", "Focus_Panel", "Focus_Tabs", "FooterKey", "Modal", "Modal_Closed", "Modal_Goto", "Modal_Help", "MouseEvent", "MouseKind", "MouseKind_Click", "MouseKind_WheelDown", "MouseKind_WheelUp", "Notification", "Severity", "Severity_Error", "Severity_Information", "Severity_Warning", "TabView", "ViewerAction", "ViewerAction_CloseGoto", "ViewerAction_CloseHelp", "ViewerAction_Dismiss", "ViewerAction_DismissFind", "ViewerAction_FocusNext", "ViewerAction_FocusPrevious", "ViewerAction_Goto", "ViewerAction_Help", "ViewerAction_HelpDown", "ViewerAction_HelpEnd", "ViewerAction_HelpHome", "ViewerAction_HelpPageDown", "ViewerAction_HelpPageUp", "ViewerAction_HelpUp", "ViewerAction_Navigate", "ViewerAction_NextTab", "ViewerAction_OpenLink", "ViewerAction_PageDown", "ViewerAction_PageUp", "ViewerAction_PanelDown", "ViewerAction_PanelEnd", "ViewerAction_PanelHome", "ViewerAction_PanelLeft", "ViewerAction_PanelPageDown", "ViewerAction_PanelPageUp", "ViewerAction_PanelRight", "ViewerAction_PanelUp", "ViewerAction_PointerDown", "ViewerAction_PointerUp", "ViewerAction_PreviousTab", "ViewerAction_Quit", "ViewerAction_ScrollDown", "ViewerAction_ScrollEnd", "ViewerAction_ScrollHome", "ViewerAction_ScrollLeft", "ViewerAction_ScrollRight", "ViewerAction_ScrollUp", "ViewerAction_Select", "ViewerAction_ShowFind", "ViewerAction_Tail", "ViewerAction_ToggleCase", "ViewerAction_ToggleLineNumbers", "ViewerAction_ToggleRegex", "ViewerAction_ToggleTail", "ViewerEvent", "ViewerEvent_Breaks", "ViewerEvent_Complete", "ViewerEvent_Found", "ViewerEvent_Jumped", "ViewerEvent_Loaded", "ViewerEvent_Notify", "ViewerEvent_OpenFailed", "ViewerEvent_PanelSize", "ViewerEvent_Progress", "ViewerEvent_Resize", "ViewerEvent_Suggestion", "ViewerEvent_Tailed", "ViewerEvent_Tick", "ViewerEvent_Widths", "ViewerLayout", "ViewerRequest", "ViewerRequest_Bell", "ViewerRequest_CancelScan", "ViewerRequest_FindNext", "ViewerRequest_Navigate", "ViewerRequest_OpenLink", "ViewerRequest_Quit", "ViewerRequest_Suggest", "ViewerState", "ViewerUpdate"]
