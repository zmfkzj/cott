from cott_runtime import CottList, Some
from real.harlequin.core_types import IdeSession, QueryTab


def add_query_tab(session: IdeSession, tab: QueryTab) -> IdeSession:
    tabs: list[QueryTab] = []
    replaced = False
    for existing in session.tabs:
        if existing.id == tab.id:
            tabs.append(tab)
            replaced = True
        else:
            tabs.append(existing)
    if not replaced:
        tabs.append(tab)
    return IdeSession(connection_id=session.connection_id, tabs=CottList(values=tabs), active_tab_id=Some(value=tab.id), history=session.history)
