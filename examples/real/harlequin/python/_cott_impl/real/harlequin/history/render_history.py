from typing import Final

from cott_runtime import I64, U64, CottList, Some
from wcwidth import wcwidth

from real.harlequin.history import history_label, history_preview
from real.harlequin.history_types import HistoryFocus_List, HistoryFocus_Program, HistoryFocus_Search, HistoryScreen, QueryRecord, QueryStatus, QueryStatus_Error, QueryStatus_Ok
from real.harlequin.style_types import StyledLine, StyledSpan

_PREVIEW_LINES: Final[int] = 8
_FOOTER: Final[str] = "Enter: Select  Ctrl+F: Filter  Esc: Cancel"


def _cut(spans: list[tuple[str, str]], width: int) -> StyledLine:
    out: list[StyledSpan] = []
    used = 0
    for style, text in spans:
        kept: list[str] = []
        for ch in text:
            w = max(wcwidth(ch), 0)
            if used + w > width:
                break
            used += w
            kept.append(ch)
        if kept:
            out.append(StyledSpan(style=style, text="".join(kept)))
        if len(kept) < len(text):
            break
    return StyledLine(spans=CottList(values=out))


def _status_name(status: QueryStatus) -> str:
    if isinstance(status, QueryStatus_Ok):
        return "ok"
    if isinstance(status, QueryStatus_Error):
        return "error"
    return "canceled"


def _with_cursor(style: str, focused: bool) -> str:
    if not focused:
        return style
    return (style + " class:hq.cursor").strip()


def _block(record: QueryRecord, selected: bool, timezone_offset_minutes: int) -> list[list[tuple[str, str]]]:
    label_style = "class:hq.text" if isinstance(record.status, QueryStatus_Ok) else "class:hq.error"
    sel = " class:hq.selection" if selected else ""
    lines: list[list[tuple[str, str]]] = [[(label_style + sel, history_label(record, timezone_offset_minutes))]]
    for line in history_preview(record.sql):
        lines.append([("class:hq.muted" + sel, "  " + line)])
    return lines


def _block_height(record: QueryRecord) -> int:
    return 1 + len(history_preview(record.sql))


def render_history(screen: HistoryScreen, records: CottList[QueryRecord], width: U64, height: U64, timezone_offset_minutes: I64) -> CottList[StyledLine]:
    recs: list[QueryRecord] = [r for r in records]
    count = len(recs)
    if count == 0:
        subtitle = "No matching queries"
    elif count == 1:
        subtitle = "1 query"
    else:
        subtitle = f"{count} queries"
    rows: list[list[tuple[str, str]]] = [[("class:hq.dialog.title", "Query History"), ("class:hq.muted", " — " + subtitle)]]

    if screen.filters_visible:
        flt = screen.filter
        focus = screen.focus
        search = flt.search
        search_style = "class:hq.muted" if search == "" else ""
        search_text = search if search != "" else "Filter by query text"
        program = flt.program
        program_text = program.value if isinstance(program, Some) else "Any program"
        status = flt.status
        status_text = _status_name(status.value) if isinstance(status, Some) else "Any outcome"
        on_search = isinstance(focus, HistoryFocus_Search)
        on_program = isinstance(focus, HistoryFocus_Program)
        on_outcome = not on_search and not on_program and not isinstance(focus, HistoryFocus_List)
        rows.append([
            ("", "Search: "),
            (_with_cursor(search_style, on_search), search_text),
            ("", "  Program: "),
            (_with_cursor("", on_program), program_text),
            ("", "  Outcome: "),
            (_with_cursor("", on_outcome), status_text),
        ])

    area = max(height - len(rows) - 1, 0)
    preview_h = min(_PREVIEW_LINES, area)
    list_h = area - preview_h

    if count > 0:
        selected = min(screen.selected, count - 1)
        first = min(screen.first_row, selected)
        heights = [_block_height(recs[i]) for i in range(first, selected + 1)]
        total = sum(heights)
        idx = 0
        while first < selected and total > list_h:
            total -= heights[idx]
            idx += 1
            first += 1
        used = 0
        i = first
        while i < count and used < list_h:
            for line in _block(recs[i], i == selected, timezone_offset_minutes):
                if used >= list_h:
                    break
                rows.append(line)
                used += 1
            i += 1

    preview: list[list[tuple[str, str]]] = [[("class:hq.title", "Highlighted Query Preview")]]
    if count > 0:
        for line in recs[min(screen.selected, count - 1)].sql.splitlines():
            if len(preview) >= preview_h:
                break
            preview.append([("", line)])
    rows.extend(preview[:preview_h])

    rows.append([("class:hq.footer", _FOOTER)])
    return CottList(values=[_cut(r, width) for r in rows[:height]])
