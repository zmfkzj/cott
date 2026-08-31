from cott_runtime import Err, Ok, Result, Some
from real.harlequin.core_types import IdeSession, SessionError, SessionError_TabMissing


def activate_query_tab(session: IdeSession, tab_id: str) -> Result[IdeSession, SessionError]:
    for tab in session.tabs:
        if tab.id == tab_id:
            return Ok(
                value=IdeSession(
                    connection=session.connection,
                    tabs=session.tabs,
                    active_tab_id=Some(value=tab_id),
                    history=session.history,
                )
            )

    return Err(error=SessionError_TabMissing(tab_id=tab_id))
