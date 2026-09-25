from cott_runtime import U64, CottList, Nothing
from real.harlequin.core_types import Connection, IdeSession, QueryHistory


def start_session(connection: Connection, history_capacity: U64) -> IdeSession:
    return IdeSession(connection_id=connection.id, tabs=CottList(values=[]), active_tab_id=Nothing(), history=QueryHistory(entries=CottList(values=[]), capacity=history_capacity))
