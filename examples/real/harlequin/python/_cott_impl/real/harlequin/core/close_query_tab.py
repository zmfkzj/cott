from cott_runtime import CottList, Err, Nothing, Ok, Result, Some
from real.harlequin.core_types import IdeSession, SessionError, SessionError_TabMissing


def close_query_tab(session: IdeSession, tab_id: str) -> Result[IdeSession, SessionError]:
    remaining_tabs = CottList(values=[tab for tab in session.tabs if tab.id != tab_id])
    if len(remaining_tabs) == len(session.tabs):
        return Err(error=SessionError_TabMissing(tab_id=tab_id))

    active_tab_id = session.active_tab_id
    if isinstance(active_tab_id, Some) and active_tab_id.value == tab_id:
        if len(remaining_tabs) == 0:
            active_tab_id = Nothing()
        else:
            active_tab_id = Some(value=remaining_tabs[0].id)

    return Ok(
        value=IdeSession(
            connection=session.connection,
            tabs=remaining_tabs,
            active_tab_id=active_tab_id,
            history=session.history,
        )
    )
