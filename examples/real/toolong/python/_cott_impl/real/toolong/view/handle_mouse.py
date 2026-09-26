import dataclasses

from rich.cells import cell_len

from cott_runtime import CottList, Nothing, Some
from real.toolong.view import apply_action, footer_keys, viewer_layout
from real.toolong.model_types import Rect
from real.toolong.view_types import Focus_FindCase, Focus_FindInput, Focus_FindRegex, Focus_Lines, Focus_Panel, Focus_Tabs, Modal_Goto, Modal_Help, MouseEvent, MouseKind_Click, MouseKind_WheelUp, TabView, ViewerAction_Goto, ViewerAction_HelpDown, ViewerAction_HelpUp, ViewerAction_OpenLink, ViewerAction_Tail, ViewerAction_ToggleCase, ViewerAction_ToggleRegex, ViewerState, ViewerUpdate


def _inside(rect: Rect, x: int, y: int) -> bool:
    return rect.x <= x < rect.x + rect.width and rect.y <= y < rect.y + rect.height


def _unchanged(viewer: ViewerState) -> ViewerUpdate:
    return ViewerUpdate(viewer=viewer, requests=CottList(values=[]))


def _with_tab(viewer: ViewerState, tab: TabView) -> ViewerState:
    tabs = [t for t in viewer.tabs]
    tabs[viewer.active] = tab
    return dataclasses.replace(viewer, tabs=CottList(values=tabs))


def _tail_off(tab: TabView) -> TabView:
    if tab.tail:
        return dataclasses.replace(tab, tail=False, pending_lines=0)
    return tab


def _help_mouse(viewer: ViewerState, event: MouseEvent) -> ViewerUpdate:
    kind = event.kind
    if not isinstance(kind, MouseKind_Click):
        if isinstance(kind, MouseKind_WheelUp):
            first = apply_action(viewer, ViewerAction_HelpUp())
            second = apply_action(first.viewer, ViewerAction_HelpUp())
        else:
            first = apply_action(viewer, ViewerAction_HelpDown())
            second = apply_action(first.viewer, ViewerAction_HelpDown())
        return ViewerUpdate(viewer=second.viewer, requests=CottList(values=[r for r in first.requests] + [r for r in second.requests]))
    if viewer.height == 0 or event.y != viewer.height - 1:
        return _unchanged(viewer)
    links = [
        ("A", "Author", "https://www.willmcgugan.com"),
        ("T", "Textual", "https://www.textualize.io/"),
        ("R", "Repository", "https://github.com/Textualize/toolong"),
        ("L", "Logmerger", "https://github.com/ptmcg/logmerger"),
    ]
    column = 0
    for key, label, url in links:
        width = cell_len(" " + key + " ") + cell_len(" " + label + " ")
        if column <= event.x < column + width:
            return apply_action(viewer, ViewerAction_OpenLink(url=url))
        column += width
    return _unchanged(viewer)


def handle_mouse(viewer: ViewerState, event: MouseEvent, meta: str) -> ViewerUpdate:
    modal = viewer.modal
    if isinstance(modal, Modal_Help):
        return _help_mouse(viewer, event)
    if isinstance(modal, Modal_Goto):
        return _unchanged(viewer)
    x = event.x
    y = event.y
    click = isinstance(event.kind, MouseKind_Click)
    layout = viewer_layout(viewer)
    width = viewer.width
    footer = layout.footer
    if footer.height > 0 and y == footer.y:
        if not click:
            return _unchanged(viewer)
        column = 0
        for key in footer_keys(viewer):
            key_width = cell_len(key.display) + 1 + cell_len(key.description) + 1
            if column <= x < column + key_width:
                return apply_action(viewer, key.action)
            column += key_width
        if x >= width - (cell_len(meta) + 2):
            return apply_action(viewer, ViewerAction_Goto())
        return _unchanged(viewer)
    tabs = [t for t in viewer.tabs]
    if len(tabs) == 0:
        return _unchanged(viewer)
    tab = tabs[viewer.active]
    if not tab.tail and tab.pending_lines > 0 and footer.y >= 1 and y == footer.y - 1:
        label = " +" + format(tab.pending_lines, ",") + " lines "
        label_width = cell_len(label)
        box = layout.lines_box
        start = box.x + (box.width - label_width) // 2
        if click and start <= x < start + label_width:
            return apply_action(viewer, ViewerAction_Tail())
    tab_rect = layout.tabs
    if isinstance(tab_rect, Some) and y == tab_rect.value.y + 1:
        column = 1
        for index, other in enumerate(tabs):
            label_width = cell_len(" " + other.title + " ")
            if click and column <= x < column + label_width:
                return _unchanged(dataclasses.replace(viewer, active=index, focus=Focus_Tabs()))
            column += label_width + 1
    find = layout.find
    if isinstance(find, Some) and find.value.y + 1 <= y <= find.value.y + 3:
        if not click:
            return _unchanged(viewer)
        if x < width - 35:
            value = tab.find_input.value
            cursor = min(len(value), max(0, x - 3))
            updated = _with_tab(viewer, dataclasses.replace(tab, find_input=dataclasses.replace(tab.find_input, cursor=cursor)))
            return _unchanged(dataclasses.replace(updated, focus=Focus_FindInput()))
        if x < width - 13:
            return apply_action(dataclasses.replace(viewer, focus=Focus_FindCase()), ViewerAction_ToggleCase())
        if x < width:
            return apply_action(dataclasses.replace(viewer, focus=Focus_FindRegex()), ViewerAction_ToggleRegex())
        return _unchanged(viewer)
    text = layout.text
    if _inside(layout.lines_box, x, y):
        if click:
            if text.y <= y < text.y + text.height and not tab.loading:
                line = tab.scroll_y + (y - text.y)
                old = tab.pointer
                if isinstance(old, Some):
                    same = old.value == line
                else:
                    same = False
                show_panel = (not tab.show_panel) if same else tab.show_panel
                if tab.line_count == 0:
                    pointer = Nothing()
                    show_panel = False
                else:
                    pointer = Some(value=min(line, tab.line_count - 1))
                new_tab = dataclasses.replace(tab, show_panel=show_panel, pointer=pointer)
                if pointer != old:
                    new_tab = dataclasses.replace(new_tab, panel_scroll_x=0, panel_scroll_y=0)
                tab = _tail_off(new_tab)
            updated = _with_tab(viewer, tab)
            return _unchanged(dataclasses.replace(updated, focus=Focus_Lines()))
        max_y = max(0, tab.line_count - text.height)
        delta = -2 if isinstance(event.kind, MouseKind_WheelUp) else 2
        scroll = min(max_y, max(0, tab.scroll_y + delta))
        return _unchanged(_with_tab(viewer, _tail_off(dataclasses.replace(tab, scroll_y=scroll))))
    panel = layout.panel
    if isinstance(panel, Some) and _inside(panel.value, x, y):
        if click:
            return _unchanged(dataclasses.replace(viewer, focus=Focus_Panel()))
        max_rows = max(0, tab.panel_lines - max(0, panel.value.height - 2))
        delta = -2 if isinstance(event.kind, MouseKind_WheelUp) else 2
        scroll = min(max_rows, max(0, tab.panel_scroll_y + delta))
        return _unchanged(_with_tab(viewer, dataclasses.replace(tab, panel_scroll_y=scroll)))
    return _unchanged(viewer)
