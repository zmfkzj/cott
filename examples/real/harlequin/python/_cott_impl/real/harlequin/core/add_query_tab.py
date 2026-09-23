from cott_runtime import CottList
from real.harlequin.core_types import IdeSession, QueryTab


def add_query_tab(session: IdeSession, tab: QueryTab) -> IdeSession:
    tabs: list[QueryTab] = [existing for existing in session.tabs]
    tabs.append(tab)
    return IdeSession(connection=session.connection, tabs=CottList(values=tabs), active_tab_id=session.active_tab_id, history=session.history)
