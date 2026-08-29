from cott_runtime import CottList, U64
from frogmouth.model_types import (
    BrowserState,
    StateAction,
    StateAction_AddHistory,
    StateAction_ClearHistory,
    StateAction_RemoveHistory,
    StateAction_ToggleBookmark,
)
from frogmouth.persistence import add_history, remove_history, toggle_bookmark


def update_state(current: BrowserState, action: StateAction, history_limit: U64) -> BrowserState:
    match action:
        case StateAction_AddHistory(location=location):
            return BrowserState(
                history=add_history(current.history, location, history_limit),
                bookmarks=current.bookmarks,
            )
        case StateAction_ToggleBookmark(location=location):
            return BrowserState(
                history=current.history,
                bookmarks=toggle_bookmark(current.bookmarks, location),
            )
        case StateAction_RemoveHistory(location=location):
            return BrowserState(
                history=remove_history(current.history, location),
                bookmarks=current.bookmarks,
            )
        case StateAction_ClearHistory():
            empty_history: CottList[str] = CottList(values=())
            return BrowserState(history=empty_history, bookmarks=current.bookmarks)
