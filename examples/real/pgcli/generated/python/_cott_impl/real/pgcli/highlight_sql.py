from real.pgcli_types import HighlightRequest, HighlightedSql


def highlight_sql(request: HighlightRequest) -> HighlightedSql:
    return HighlightedSql(text=request.source, contains_error=False)
