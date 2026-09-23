import csv
import html
import io
import json
from typing import Final

from cott_runtime import U16
from real.pgcli_types import FormatRequest, FormattedQuery, RenderLayout, RenderLayout_Horizontal, RenderLayout_Vertical, RenderedQuery, TableFormat, TableFormat_Aligned, TableFormat_Csv, TableFormat_Html, TableFormat_Json, TableFormat_JsonLines, TableFormat_Latex, TableFormat_Markdown, TableFormat_Tsv

_U16_MAX: Final[int] = 65535


def _clip(value: str, limit: int) -> str:
    if limit <= 0 or len(value) <= limit:
        return value
    if limit == 1:
        return value[:1]
    return value[: limit - 1] + "…"


def _row_line(cells: list[str], widths: list[int]) -> str:
    padded = [(cells[i] if i < len(cells) else "").ljust(w) for i, w in enumerate(widths)]
    return "| " + " | ".join(padded) + " |"


def _aligned(columns: list[str], rows: list[list[str]]) -> str:
    widths = [len(c) for c in columns]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths) and len(cell) > widths[i]:
                widths[i] = len(cell)
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    out = [sep, _row_line(columns, widths), sep]
    out.extend(_row_line(r, widths) for r in rows)
    out.append(sep)
    return "\n".join(out)


def _vertical(columns: list[str], rows: list[list[str]]) -> str:
    label = max((len(c) for c in columns), default=0)
    out: list[str] = []
    for n, row in enumerate(rows, start=1):
        out.append(f"-[ RECORD {n} ]" + "-" * max(label, 1))
        for i, col in enumerate(columns):
            cell = row[i] if i < len(row) else ""
            out.append(f"{col.ljust(label)} | {cell}")
    return "\n".join(out)


def _delimited(columns: list[str], rows: list[list[str]], delimiter: str) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=delimiter, lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(rows)
    return buf.getvalue().rstrip("\n")


def _records(columns: list[str], rows: list[list[str]]) -> list[dict[str, str]]:
    return [{col: (row[i] if i < len(row) else "") for i, col in enumerate(columns)} for row in rows]


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|")


def _latex_cell(value: str) -> str:
    out = value.replace("\\", "\\textbackslash{}")
    for ch in "&%$#_{}":
        out = out.replace(ch, "\\" + ch)
    return out


def format_query(request: FormatRequest) -> FormattedQuery:
    limit = int(request.max_column_width)
    columns: list[str] = [_clip(str(c), limit) for c in request.query.columns]
    kept: list[list[str]] = []
    for row in request.query.rows:
        if len(kept) >= request.max_rows:
            break
        kept.append([_clip(str(cell), limit) for cell in row])

    fmt: TableFormat = request.format
    layout: RenderLayout = RenderLayout_Horizontal()
    if isinstance(fmt, TableFormat_Aligned):
        text = _aligned(columns, kept)
        if max((len(l) for l in text.split("\n")), default=0) > request.terminal_width:
            text = _vertical(columns, kept)
            layout = RenderLayout_Vertical()
    elif isinstance(fmt, TableFormat_Csv):
        text = _delimited(columns, kept, ",")
    elif isinstance(fmt, TableFormat_Tsv):
        text = _delimited(columns, kept, "\t")
    elif isinstance(fmt, TableFormat_Json):
        text = json.dumps(_records(columns, kept), ensure_ascii=False, indent=2)
    elif isinstance(fmt, TableFormat_JsonLines):
        text = "\n".join(json.dumps(r, ensure_ascii=False) for r in _records(columns, kept))
    elif isinstance(fmt, TableFormat_Html):
        head = "".join(f"<th>{html.escape(c)}</th>" for c in columns)
        body = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>" for r in kept)
        text = f"<table>\n<thead><tr>{head}</tr></thead>\n<tbody>{body}</tbody>\n</table>"
    elif isinstance(fmt, TableFormat_Latex):
        spec = "l" * len(columns)
        lines = [f"\\begin{{tabular}}{{{spec}}}", " & ".join(_latex_cell(c) for c in columns) + " \\\\", "\\hline"]
        lines.extend(" & ".join(_latex_cell(c) for c in r) + " \\\\" for r in kept)
        lines.append("\\end{tabular}")
        text = "\n".join(lines)
    elif isinstance(fmt, TableFormat_Markdown):
        lines = ["| " + " | ".join(_markdown_cell(c) for c in columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
        lines.extend("| " + " | ".join(_markdown_cell(c) for c in r) + " |" for r in kept)
        text = "\n".join(lines)
    else:
        text = _vertical(columns, kept)
        layout = RenderLayout_Vertical()

    measured = max((len(l) for l in text.split("\n")), default=0)
    width: U16 = min(measured, _U16_MAX)
    rendered = RenderedQuery(text=text, layout=layout, width=width)
    return FormattedQuery(rendered=rendered, truncated_rows=len(kept))
