from cott_runtime import U64
from real.harlequin.core_types import QueryTab


def edit_query_tab(tab: QueryTab, source: str, cursor: U64) -> QueryTab:
    return QueryTab(
        id=tab.id,
        title=tab.title,
        source=source,
        cursor=min(cursor, len(source)),
        dirty=True,
    )
