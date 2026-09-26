from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.toolong.view_types import Focus as Focus, Focus_FindCase as Focus_FindCase, Focus_FindInput as Focus_FindInput, Focus_FindRegex as Focus_FindRegex, Focus_Lines as Focus_Lines, Focus_Panel as Focus_Panel, Focus_Tabs as Focus_Tabs, FooterKey as FooterKey, Modal as Modal, Modal_Closed as Modal_Closed, Modal_Goto as Modal_Goto, Modal_Help as Modal_Help, MouseEvent as MouseEvent, MouseKind as MouseKind, MouseKind_Click as MouseKind_Click, MouseKind_WheelDown as MouseKind_WheelDown, MouseKind_WheelUp as MouseKind_WheelUp, Notification as Notification, Severity as Severity, Severity_Error as Severity_Error, Severity_Information as Severity_Information, Severity_Warning as Severity_Warning, TabView as TabView, ViewerAction as ViewerAction, ViewerAction_CloseGoto as ViewerAction_CloseGoto, ViewerAction_CloseHelp as ViewerAction_CloseHelp, ViewerAction_Dismiss as ViewerAction_Dismiss, ViewerAction_DismissFind as ViewerAction_DismissFind, ViewerAction_FocusNext as ViewerAction_FocusNext, ViewerAction_FocusPrevious as ViewerAction_FocusPrevious, ViewerAction_Goto as ViewerAction_Goto, ViewerAction_Help as ViewerAction_Help, ViewerAction_HelpDown as ViewerAction_HelpDown, ViewerAction_HelpEnd as ViewerAction_HelpEnd, ViewerAction_HelpHome as ViewerAction_HelpHome, ViewerAction_HelpPageDown as ViewerAction_HelpPageDown, ViewerAction_HelpPageUp as ViewerAction_HelpPageUp, ViewerAction_HelpUp as ViewerAction_HelpUp, ViewerAction_Navigate as ViewerAction_Navigate, ViewerAction_NextTab as ViewerAction_NextTab, ViewerAction_OpenLink as ViewerAction_OpenLink, ViewerAction_PageDown as ViewerAction_PageDown, ViewerAction_PageUp as ViewerAction_PageUp, ViewerAction_PanelDown as ViewerAction_PanelDown, ViewerAction_PanelEnd as ViewerAction_PanelEnd, ViewerAction_PanelHome as ViewerAction_PanelHome, ViewerAction_PanelLeft as ViewerAction_PanelLeft, ViewerAction_PanelPageDown as ViewerAction_PanelPageDown, ViewerAction_PanelPageUp as ViewerAction_PanelPageUp, ViewerAction_PanelRight as ViewerAction_PanelRight, ViewerAction_PanelUp as ViewerAction_PanelUp, ViewerAction_PointerDown as ViewerAction_PointerDown, ViewerAction_PointerUp as ViewerAction_PointerUp, ViewerAction_PreviousTab as ViewerAction_PreviousTab, ViewerAction_Quit as ViewerAction_Quit, ViewerAction_ScrollDown as ViewerAction_ScrollDown, ViewerAction_ScrollEnd as ViewerAction_ScrollEnd, ViewerAction_ScrollHome as ViewerAction_ScrollHome, ViewerAction_ScrollLeft as ViewerAction_ScrollLeft, ViewerAction_ScrollRight as ViewerAction_ScrollRight, ViewerAction_ScrollUp as ViewerAction_ScrollUp, ViewerAction_Select as ViewerAction_Select, ViewerAction_ShowFind as ViewerAction_ShowFind, ViewerAction_Tail as ViewerAction_Tail, ViewerAction_ToggleCase as ViewerAction_ToggleCase, ViewerAction_ToggleLineNumbers as ViewerAction_ToggleLineNumbers, ViewerAction_ToggleRegex as ViewerAction_ToggleRegex, ViewerAction_ToggleTail as ViewerAction_ToggleTail, ViewerEvent as ViewerEvent, ViewerEvent_Breaks as ViewerEvent_Breaks, ViewerEvent_Complete as ViewerEvent_Complete, ViewerEvent_Found as ViewerEvent_Found, ViewerEvent_Jumped as ViewerEvent_Jumped, ViewerEvent_Loaded as ViewerEvent_Loaded, ViewerEvent_Notify as ViewerEvent_Notify, ViewerEvent_OpenFailed as ViewerEvent_OpenFailed, ViewerEvent_PanelSize as ViewerEvent_PanelSize, ViewerEvent_Progress as ViewerEvent_Progress, ViewerEvent_Resize as ViewerEvent_Resize, ViewerEvent_Suggestion as ViewerEvent_Suggestion, ViewerEvent_Tailed as ViewerEvent_Tailed, ViewerEvent_Tick as ViewerEvent_Tick, ViewerEvent_Widths as ViewerEvent_Widths, ViewerLayout as ViewerLayout, ViewerRequest as ViewerRequest, ViewerRequest_Bell as ViewerRequest_Bell, ViewerRequest_CancelScan as ViewerRequest_CancelScan, ViewerRequest_FindNext as ViewerRequest_FindNext, ViewerRequest_Navigate as ViewerRequest_Navigate, ViewerRequest_OpenLink as ViewerRequest_OpenLink, ViewerRequest_Quit as ViewerRequest_Quit, ViewerRequest_Suggest as ViewerRequest_Suggest, ViewerState as ViewerState, ViewerUpdate as ViewerUpdate
from real.toolong.keys_types import KeyEvent, TextInput
from real.toolong.model_types import Rect, TabPlan, TimeUnit
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
def initial_viewer(plans: CottList[TabPlan], width: U16, height: U16) -> ViewerState: ...

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
def viewer_layout(viewer: ViewerState) -> ViewerLayout: ...

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
def footer_keys(viewer: ViewerState) -> CottList[FooterKey]: ...

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
def apply_action(viewer: ViewerState, action: ViewerAction) -> ViewerUpdate: ...

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
def handle_key(viewer: ViewerState, key: KeyEvent) -> ViewerUpdate: ...

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
def apply_event(viewer: ViewerState, event: ViewerEvent) -> ViewerUpdate: ...

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
def handle_mouse(viewer: ViewerState, event: MouseEvent, meta: str) -> ViewerUpdate: ...

__all__ = ["Focus", "Focus_FindCase", "Focus_FindInput", "Focus_FindRegex", "Focus_Lines", "Focus_Panel", "Focus_Tabs", "FooterKey", "Modal", "Modal_Closed", "Modal_Goto", "Modal_Help", "MouseEvent", "MouseKind", "MouseKind_Click", "MouseKind_WheelDown", "MouseKind_WheelUp", "Notification", "Severity", "Severity_Error", "Severity_Information", "Severity_Warning", "TabView", "ViewerAction", "ViewerAction_CloseGoto", "ViewerAction_CloseHelp", "ViewerAction_Dismiss", "ViewerAction_DismissFind", "ViewerAction_FocusNext", "ViewerAction_FocusPrevious", "ViewerAction_Goto", "ViewerAction_Help", "ViewerAction_HelpDown", "ViewerAction_HelpEnd", "ViewerAction_HelpHome", "ViewerAction_HelpPageDown", "ViewerAction_HelpPageUp", "ViewerAction_HelpUp", "ViewerAction_Navigate", "ViewerAction_NextTab", "ViewerAction_OpenLink", "ViewerAction_PageDown", "ViewerAction_PageUp", "ViewerAction_PanelDown", "ViewerAction_PanelEnd", "ViewerAction_PanelHome", "ViewerAction_PanelLeft", "ViewerAction_PanelPageDown", "ViewerAction_PanelPageUp", "ViewerAction_PanelRight", "ViewerAction_PanelUp", "ViewerAction_PointerDown", "ViewerAction_PointerUp", "ViewerAction_PreviousTab", "ViewerAction_Quit", "ViewerAction_ScrollDown", "ViewerAction_ScrollEnd", "ViewerAction_ScrollHome", "ViewerAction_ScrollLeft", "ViewerAction_ScrollRight", "ViewerAction_ScrollUp", "ViewerAction_Select", "ViewerAction_ShowFind", "ViewerAction_Tail", "ViewerAction_ToggleCase", "ViewerAction_ToggleLineNumbers", "ViewerAction_ToggleRegex", "ViewerAction_ToggleTail", "ViewerEvent", "ViewerEvent_Breaks", "ViewerEvent_Complete", "ViewerEvent_Found", "ViewerEvent_Jumped", "ViewerEvent_Loaded", "ViewerEvent_Notify", "ViewerEvent_OpenFailed", "ViewerEvent_PanelSize", "ViewerEvent_Progress", "ViewerEvent_Resize", "ViewerEvent_Suggestion", "ViewerEvent_Tailed", "ViewerEvent_Tick", "ViewerEvent_Widths", "ViewerLayout", "ViewerRequest", "ViewerRequest_Bell", "ViewerRequest_CancelScan", "ViewerRequest_FindNext", "ViewerRequest_Navigate", "ViewerRequest_OpenLink", "ViewerRequest_Quit", "ViewerRequest_Suggest", "ViewerState", "ViewerUpdate", "apply_action", "apply_event", "footer_keys", "handle_key", "handle_mouse", "initial_viewer", "viewer_layout"]
