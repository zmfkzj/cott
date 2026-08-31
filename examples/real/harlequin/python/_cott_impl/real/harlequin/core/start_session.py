from cott_runtime import CottList, Nothing, U64
from real.harlequin.core_types import Connection, IdeSession, QueryHistory


def start_session(connection: Connection, history_capacity: U64) -> IdeSession:
    return IdeSession(
        connection=connection,
        tabs=CottList(values=[]),
        active_tab_id=Nothing(),
        history=QueryHistory(entries=CottList(values=[]), capacity=history_capacity),
    )
