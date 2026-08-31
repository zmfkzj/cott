from real.harlequin.core_types import QueryResult


def render_vertical(result: QueryResult) -> str:
    lines: list[str] = []
    for row_number, row in enumerate(result.rows, start=1):
        lines.append(f"Row {row_number}")
        for column, value in zip(result.columns, row.values):
            lines.append(f"{column}: {value}")
    return "\n".join(lines)
