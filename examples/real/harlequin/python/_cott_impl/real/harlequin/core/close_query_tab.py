from cott_runtime import CottList, Err, Nothing, Ok, Option, Result, Some
from real.harlequin.core_types import IdeSession, QueryTab, SessionError, SessionError_TabMissing


def close_query_tab(session: IdeSession, tab_id: str) -> Result[IdeSession, SessionError]:
    remaining: list[QueryTab] = []
    closed_index: int = -1
    index: int = 0
    for tab in session.tabs:
        if closed_index < 0 and tab.id == tab_id:
            closed_index = index
        else:
            remaining.append(tab)
        index += 1
    if closed_index < 0:
        return Err(error=SessionError_TabMissing(tab_id=tab_id))
    active: Option[str] = session.active_tab_id
    if isinstance(active, Some) and active.value == tab_id:
        if len(remaining) == 0:
            active = Nothing()
        elif closed_index < len(remaining):
            active = Some(value=remaining[closed_index].id)
        else:
            active = Some(value=remaining[-1].id)
    return Ok(value=IdeSession(connection=session.connection, tabs=CottList(values=remaining), active_tab_id=active, history=session.history))
