from real.harlequin.core_types import QueryResult


def render_table(result: QueryResult) -> str:
    lines: list[str] = []
    if len(result.columns) > 0:
        lines.append(" | ".join(result.columns))
    for row in result.rows:
        lines.append(" | ".join(str(value) for value in row.values))
    return "\n".join(lines)
