from typing import Any, Final, cast

import wcwidth
from cott_runtime import Some

from real.harlequin.hsql_types import LayoutOptions
from real.harlequin.results_types import ResultSet

_BOLD: Final[str] = "\u001b[1m"
_DIM: Final[str] = "\u001b[2m"
_RESET: Final[str] = "\u001b[0m"


def _width(text: str) -> int:
    if text.isascii():
        return len(text)
    total = 0
    for ch in text:
        w = wcwidth.wcwidth(ch)
        total += w if w > 0 else 0
    return total


def _cell_width(text: str) -> int:
    return max((_width(line) for line in text.split("\n")), default=0)


def _style(text: str, code: str, on: bool) -> str:
    if not on or text == "":
        return text
    return code + text + _RESET


def _footer(shown: int, total: int, truncated: bool) -> str:
    if truncated:
        return f"({shown} of >{total} rows)"
    if shown < total:
        return f"({shown} of {total} rows)"
    return "(1 row)" if shown == 1 else f"({shown} rows)"


def _extract(result_set: ResultSet, cap: int | None, null_text: str) -> tuple[list[str], list[list[tuple[str, bool]]], int]:
    handle = result_set.data
    if handle.tag != "harlequin.arrow_table":
        raise ValueError("result data is not an Arrow table")
    table: Any = handle.unwrap()
    names = [str(n) for n in cast(list[object], table.column_names)]
    total = int(cast(int, table.num_rows))
    shown = total if cap is None else min(cap, total)
    columns: list[list[object]] = []
    for index in range(len(names)):
        values = cast(object, table.column(index).slice(0, shown).to_pylist())
        columns.append(cast(list[object], values))
    rows: list[list[tuple[str, bool]]] = []
    for r in range(shown):
        row: list[tuple[str, bool]] = []
        for col in columns:
            value = col[r]
            if value is None:
                row.append((null_text, True))
            else:
                raw = repr(value) if isinstance(value, (float, bytes)) else str(value)
                row.append((raw.replace("\r\n", "\n"), False))
        rows.append(row)
    return names, rows, total


def _table(names: list[str], rows: list[list[tuple[str, bool]]], options: LayoutOptions) -> list[str]:
    color = options.color
    out: list[str] = []
    if not options.aligned:
        if options.header:
            out.append("|".join(_style(n, _BOLD, color) for n in names))
        for row in rows:
            out.append("|".join(_style(t, _DIM, color and isnull) for t, isnull in row))
        return out
    widths = [_cell_width(n) if options.header else 0 for n in names]
    for row in rows:
        for i, (text, _isnull) in enumerate(row):
            widths[i] = max(widths[i], _cell_width(text))
    last = len(names) - 1
    if options.header:
        parts: list[str] = []
        for i, n in enumerate(names):
            styled = _style(n, _BOLD, color)
            parts.append(styled if i == last else styled + " " * (widths[i] - _width(n)))
        out.append(" " + " | ".join(parts))
        out.append("-" + "-+-".join("-" * w for w in widths))
    for row in rows:
        split = [text.split("\n") for text, _isnull in row]
        height = max((len(s) for s in split), default=1)
        for k in range(height):
            line = " "
            for i, lines in enumerate(split):
                piece = lines[k] if k < len(lines) else ""
                more = k + 1 < len(lines)
                styled = _style(piece, _DIM, color and row[i][1])
                if i == last:
                    line += (styled + " " * (widths[i] - _width(piece)) + "+") if more else styled
                else:
                    line += styled + " " * (widths[i] - _width(piece)) + ("+| " if more else " | ")
            out.append(line)
    return out


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", "<br>")


def _markdown(names: list[str], rows: list[list[tuple[str, bool]]], options: LayoutOptions) -> list[str]:
    color = options.color
    esc_names = [_md_escape(n) for n in names]
    esc_rows = [[(_md_escape(t), isnull) for t, isnull in row] for row in rows]
    widths = [max(3, _width(n)) for n in esc_names]
    for row in esc_rows:
        for i, (text, _isnull) in enumerate(row):
            widths[i] = max(widths[i], _width(text))
    out: list[str] = []
    if options.header:
        out.append("| " + " | ".join(_style(n, _BOLD, color) + " " * (widths[i] - _width(n)) for i, n in enumerate(esc_names)) + " |")
        out.append("| " + " | ".join("-" * w for w in widths) + " |")
    for row in esc_rows:
        out.append("| " + " | ".join(_style(t, _DIM, color and isnull) + " " * (widths[i] - _width(t)) for i, (t, isnull) in enumerate(row)) + " |")
    return out


def _vertical(names: list[str], rows: list[list[tuple[str, bool]]], options: LayoutOptions) -> list[str]:
    color = options.color
    out: list[str] = []
    if not options.aligned:
        for number, row in enumerate(rows, start=1):
            if options.header:
                out.append(f"-[ RECORD {number} ]")
            elif number > 1:
                out.append("")
            for i, (text, isnull) in enumerate(row):
                out.append(_style(names[i], _BOLD, color) + "|" + _style(text, _DIM, color and isnull))
        return out
    name_width = max((_cell_width(n) for n in names), default=0)
    value_width = 0
    for row in rows:
        for text, _isnull in row:
            value_width = max(value_width, _cell_width(text))
    widest = name_width + 3 + value_width
    for number, row in enumerate(rows, start=1):
        if options.header:
            title = f"-[ RECORD {number} ]"
            out.append(title + "-" * max(0, widest - len(title)))
        elif number > 1:
            out.append("")
        for i, (text, isnull) in enumerate(row):
            label = _style(names[i], _BOLD, color) + " " * (name_width - _width(names[i]))
            lines = text.split("\n")
            out.append(label + " | " + _style(lines[0], _DIM, color and isnull))
            for extra in lines[1:]:
                out.append(" " * name_width + " | " + extra)
    return out


def layout_text(result_set: ResultSet, layout: str, options: LayoutOptions) -> str:
    kind = layout.strip().lower()
    if kind == "md":
        kind = "markdown"
    if kind not in ("table", "markdown", "vertical"):
        raise ValueError(f"unknown layout: {layout}")
    null_opt = options.null_string
    null_text = null_opt.value if isinstance(null_opt, Some) else "NULL"
    cap_opt = options.max_rows
    cap: int | None = int(cap_opt.value) if isinstance(cap_opt, Some) else None
    names, rows, available = _extract(result_set, cap, null_text)
    if kind == "table":
        lines = _table(names, rows, options)
    elif kind == "markdown":
        lines = _markdown(names, rows, options)
    else:
        lines = _vertical(names, rows, options)
    if options.footer:
        fetched = int(result_set.fetched_row_count)
        text = _footer(len(rows), max(available, fetched), result_set.truncated)
        if kind == "markdown":
            lines.append("")
            lines.append(f"*{text}*")
        else:
            lines.append(text)
    return "".join(line + "\n" for line in lines)
