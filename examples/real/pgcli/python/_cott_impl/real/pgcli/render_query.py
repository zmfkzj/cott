from real.pgcli_types import RenderLayout_Vertical, RenderRequest, RenderedQuery


def _normalize_rows(request: RenderRequest, count: int) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in request.rows:
        cells: list[str] = []
        for cell in row:
            if len(cells) == count:
                break
            cells.append(cell)
        while len(cells) < count:
            cells.append("")
        rows.append(cells)
    return rows


def _render_horizontal(columns: list[str], rows: list[list[str]]) -> list[str]:
    widths = [len(c) for c in columns]
    for row in rows:
        for i, cell in enumerate(row):
            if len(cell) > widths[i]:
                widths[i] = len(cell)
    lines = [" | ".join(c.ljust(w) for c, w in zip(columns, widths))]
    lines.append("-+-".join("-" * w for w in widths))
    for row in rows:
        lines.append(" | ".join(v.ljust(w) for v, w in zip(row, widths)))
    return lines


def _render_vertical(columns: list[str], rows: list[list[str]]) -> list[str]:
    label_width = max(len(c) for c in columns)
    lines: list[str] = []
    for index, row in enumerate(rows):
        lines.append(f"-[ RECORD {index + 1} ]")
        for name, value in zip(columns, row):
            lines.append(f"{name.ljust(label_width)} | {value}")
    return lines


def render_query(request: RenderRequest) -> RenderedQuery:
    columns: list[str] = []
    for column in request.columns:
        columns.append(column)
    if not columns:
        return RenderedQuery(text="", layout=request.layout, width=0)
    rows = _normalize_rows(request, len(columns))
    if isinstance(request.layout, RenderLayout_Vertical):
        lines = _render_vertical(columns, rows)
    else:
        lines = _render_horizontal(columns, rows)
    stripped = [line.rstrip(" ") for line in lines]
    width = min(max((len(line) for line in stripped), default=0), 65535)
    return RenderedQuery(text="\n".join(stripped), layout=request.layout, width=width)
