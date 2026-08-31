from real.harlequin.core_types import QueryTab


def open_query_tab(id: str, title: str, source: str) -> QueryTab:
    return QueryTab(id=id, title=title, source=source, cursor=0, dirty=False)
