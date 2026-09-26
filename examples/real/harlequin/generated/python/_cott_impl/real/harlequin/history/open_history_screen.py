from cott_runtime import Nothing, Some

from real.harlequin.history_types import HistoryFilter, HistoryFocus_List, HistoryScreen


def open_history_screen(connection: str) -> HistoryScreen:
    return HistoryScreen(
        filter=HistoryFilter(connection=Some(value=connection), search="", program=Nothing(), status=Nothing()),
        filters_visible=False,
        focus=HistoryFocus_List(),
        search_cursor=0,
        selected=0,
        first_row=0,
    )
