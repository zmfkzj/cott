from dataclasses import replace

from cott_runtime import CottList, Nothing, Some, U64
from real.harlequin.history_types import HistoryFilter, HistoryFocus, HistoryFocus_List, HistoryFocus_Outcome, HistoryFocus_Program, HistoryFocus_Search, HistoryOutcome, HistoryOutcome_Close, HistoryOutcome_Reload, HistoryOutcome_Select, HistoryOutcome_Stay, HistoryScreen, HistoryStep, QueryRecord, QueryStatus_Canceled, QueryStatus_Error, QueryStatus_Ok


def _focus_index(focus: HistoryFocus) -> int:
    if isinstance(focus, HistoryFocus_Search):
        return 0
    if isinstance(focus, HistoryFocus_Program):
        return 1
    if isinstance(focus, HistoryFocus_Outcome):
        return 2
    return 3


def _focus_at(index: int) -> HistoryFocus:
    wrapped = index % 4
    if wrapped == 0:
        return HistoryFocus_Search()
    if wrapped == 1:
        return HistoryFocus_Program()
    if wrapped == 2:
        return HistoryFocus_Outcome()
    return HistoryFocus_List()


def _clamp(value: int, count: int) -> U64:
    if count <= 0 or value < 0:
        return 0
    return min(value, count - 1)


def _finish(screen: HistoryScreen, count: int, outcome: HistoryOutcome) -> HistoryStep:
    if isinstance(outcome, HistoryOutcome_Reload):
        final = replace(screen, filter=outcome.filter, selected=0, first_row=0)
    else:
        final = replace(screen, selected=_clamp(screen.selected, count))
    return HistoryStep(screen=final, outcome=outcome)


def _reload(screen: HistoryScreen, count: int, flt: HistoryFilter) -> HistoryStep:
    return _finish(screen, count, HistoryOutcome_Reload(filter=flt))


def _cleared_filter(flt: HistoryFilter) -> HistoryFilter:
    return replace(flt, search="", program=Nothing(), status=Nothing())


def _has_criteria(flt: HistoryFilter) -> bool:
    return flt.search != "" or isinstance(flt.program, Some) or isinstance(flt.status, Some)


def _set_search(screen: HistoryScreen, count: int, search: str, cursor: int) -> HistoryStep:
    moved = replace(screen, search_cursor=cursor)
    if search == screen.filter.search:
        return _finish(moved, count, HistoryOutcome_Stay())
    return _reload(moved, count, replace(screen.filter, search=search))


def history_key(screen: HistoryScreen, records: CottList[QueryRecord], key: str, text: str) -> HistoryStep:
    items: list[QueryRecord] = [record for record in records]
    count = len(items)
    flt = screen.filter
    focus = screen.focus
    stay = HistoryOutcome_Stay()
    printable = len(text) == 1 and text.isprintable()

    if key == "escape":
        if screen.filters_visible:
            if isinstance(focus, HistoryFocus_Search) and flt.search != "":
                return _reload(replace(screen, search_cursor=0), count, replace(flt, search=""))
            hidden = replace(screen, filters_visible=False, focus=HistoryFocus_List(), search_cursor=0)
            return _reload(hidden, count, _cleared_filter(flt))
        return _finish(screen, count, HistoryOutcome_Close())

    if key == "ctrl+f":
        if not screen.filters_visible:
            return _finish(replace(screen, filters_visible=True, focus=HistoryFocus_Search()), count, stay)
        hidden = replace(screen, filters_visible=False, focus=HistoryFocus_List(), search_cursor=0)
        if _has_criteria(flt):
            return _reload(hidden, count, _cleared_filter(flt))
        return _finish(hidden, count, stay)

    if key == "enter":
        if isinstance(focus, HistoryFocus_List):
            if count > 0:
                return _finish(screen, count, HistoryOutcome_Select(sql=items[_clamp(screen.selected, count)].sql))
            return _finish(screen, count, stay)
        if isinstance(focus, HistoryFocus_Search):
            return _finish(replace(screen, focus=HistoryFocus_List()), count, stay)
        if isinstance(focus, HistoryFocus_Program):
            program = flt.program
            if isinstance(program, Some):
                next_program: Some[str] | Nothing = Some(value="hsql") if program.value == "harlequin" else Nothing()
            else:
                next_program = Some(value="harlequin")
            return _reload(screen, count, replace(flt, program=next_program))
        status = flt.status
        if isinstance(status, Some):
            current = status.value
            if isinstance(current, QueryStatus_Ok):
                next_status: Some[QueryStatus_Ok | QueryStatus_Error | QueryStatus_Canceled] | Nothing = Some(value=QueryStatus_Error())
            elif isinstance(current, QueryStatus_Error):
                next_status = Some(value=QueryStatus_Canceled())
            else:
                next_status = Nothing()
        else:
            next_status = Some(value=QueryStatus_Ok())
        return _reload(screen, count, replace(flt, status=next_status))

    if key in ("tab", "shift+tab"):
        if screen.filters_visible:
            step = 1 if key == "tab" else -1
            return _finish(replace(screen, focus=_focus_at(_focus_index(focus) + step)), count, stay)
        return _finish(screen, count, stay)

    if isinstance(focus, HistoryFocus_List):
        selected = screen.selected
        if key == "up":
            return _finish(replace(screen, selected=_clamp(selected - 1, count)), count, stay)
        if key == "down":
            return _finish(replace(screen, selected=_clamp(selected + 1, count)), count, stay)
        if key == "pageup":
            return _finish(replace(screen, selected=_clamp(selected - 10, count)), count, stay)
        if key == "pagedown":
            return _finish(replace(screen, selected=_clamp(selected + 10, count)), count, stay)
        if key == "home":
            return _finish(replace(screen, selected=0), count, stay)
        if key == "end":
            return _finish(replace(screen, selected=_clamp(count - 1, count)), count, stay)
        if printable and text.strip() != "":
            search = flt.search + text
            shown = replace(screen, filters_visible=True, focus=HistoryFocus_Search(), search_cursor=len(search))
            return _reload(shown, count, replace(flt, search=search))
        return _finish(screen, count, stay)

    if isinstance(focus, HistoryFocus_Search):
        search = flt.search
        cursor = min(max(screen.search_cursor, 0), len(search))
        if key == "backspace":
            if cursor == 0:
                return _finish(replace(screen, search_cursor=cursor), count, stay)
            return _set_search(screen, count, search[: cursor - 1] + search[cursor:], cursor - 1)
        if key == "delete":
            if cursor >= len(search):
                return _finish(replace(screen, search_cursor=cursor), count, stay)
            return _set_search(screen, count, search[:cursor] + search[cursor + 1 :], cursor)
        if key == "left":
            return _finish(replace(screen, search_cursor=max(cursor - 1, 0)), count, stay)
        if key == "right":
            return _finish(replace(screen, search_cursor=min(cursor + 1, len(search))), count, stay)
        if key == "home":
            return _finish(replace(screen, search_cursor=0), count, stay)
        if key == "end":
            return _finish(replace(screen, search_cursor=len(search)), count, stay)
        if printable:
            return _set_search(screen, count, search[:cursor] + text + search[cursor:], cursor + 1)

    return _finish(screen, count, stay)
