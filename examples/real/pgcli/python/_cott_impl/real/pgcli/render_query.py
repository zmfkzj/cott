from cott_runtime import CottList
from real.pgcli_types import RenderLayout, RenderLayout_Horizontal, RenderLayout_Vertical, RenderRequest, RenderedQuery


def _layout(vertical: bool) -> RenderLayout:
    if vertical:
        return RenderLayout_Vertical()
    return RenderLayout_Horizontal()


def _row_cells(row: CottList[str], count: int) -> list[str]:
    cells: list[str] = []
    for cell in row:
        cells.append(cell)
    while len(cells) < count:
        cells.append("")
    return cells


def _render_vertical(columns: list[str], rows: list[list[str]]) -> str:
    label_width = max((len(c) for c in columns), default=0)
    lines: list[str] = []
    for index, row in enumerate(rows):
        lines.append(f"-[ RECORD {index + 1} ]" + "-" * max(0, label_width))
        for name, value in zip(columns, row):
            lines.append(f"{name.ljust(label_width)} | {value}")
    return "\n".join(lines)


def _render_horizontal(columns: list[str], rows: list[list[str]]) -> str:
    widths = [len(c) for c in columns]
    for row in rows:
        for i in range(len(columns)):
            widths[i] = max(widths[i], len(row[i]))
    header = " | ".join(c.ljust(w) for c, w in zip(columns, widths))
    separator = "-+-".join("-" * w for w in widths)
    body = [" | ".join(v.ljust(w) for v, w in zip(row[: len(columns)], widths)) for row in rows]
    return "\n".join([header, separator, *body])


def render_query(request: RenderRequest) -> RenderedQuery:
    columns: list[str] = []
    for column in request.columns:
        columns.append(column)
    rows: list[list[str]] = []
    for row in request.rows:
        rows.append(_row_cells(row, len(columns)))
    if request.vertical:
        text = _render_vertical(columns, rows)
    else:
        text = _render_horizontal(columns, rows)
    return RenderedQuery(text=text, layout=_layout(request.vertical), width=request.terminal_width)
