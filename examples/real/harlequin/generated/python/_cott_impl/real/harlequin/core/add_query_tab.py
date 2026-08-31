from cott_runtime import CottList, Some
from real.harlequin.core_types import IdeSession, QueryTab


def add_query_tab(session: IdeSession, tab: QueryTab) -> IdeSession:
    return IdeSession(
        connection=session.connection,
        tabs=CottList(values=[*session.tabs, tab]),
        active_tab_id=Some(value=tab.id),
        history=session.history,
    )
