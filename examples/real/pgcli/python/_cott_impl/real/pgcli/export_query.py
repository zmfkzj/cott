import csv
import html
import io
import json
import os
import secrets

import psycopg
from psycopg.conninfo import make_conninfo
from cott_runtime import Err, Ok, Result, Some
from real.pgcli_types import ClientError, ClientError_ExportFailed, ClientError_QueryFailed, ConnectionPlan, ExportRequest, TableFormat, TableFormat_Aligned, TableFormat_Csv, TableFormat_Html, TableFormat_Json, TableFormat_JsonLines, TableFormat_Latex, TableFormat_Markdown, TableFormat_Tsv, TransferResult


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _json_value(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def _render_delimited(columns: list[str], rows: list[tuple[object, ...]], delimiter: str, header: bool) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n")
    if header:
        writer.writerow(columns)
    for row in rows:
        writer.writerow([_text(value) for value in row])
    return buffer.getvalue()


def _render_json(columns: list[str], rows: list[tuple[object, ...]]) -> str:
    records = [{name: _json_value(value) for name, value in zip(columns, row)} for row in rows]
    return json.dumps(records, ensure_ascii=False, indent=2) + "\n"


def _render_json_lines(columns: list[str], rows: list[tuple[object, ...]]) -> str:
    return "".join(json.dumps({name: _json_value(value) for name, value in zip(columns, row)}, ensure_ascii=False) + "\n" for row in rows)


def _render_html(columns: list[str], rows: list[tuple[object, ...]], header: bool) -> str:
    parts = ["<table>\n"]
    if header:
        parts.append("<thead><tr>" + "".join("<th>" + html.escape(name) + "</th>" for name in columns) + "</tr></thead>\n")
    parts.append("<tbody>\n")
    for row in rows:
        parts.append("<tr>" + "".join("<td>" + html.escape(_text(value)) + "</td>" for value in row) + "</tr>\n")
    parts.append("</tbody>\n</table>\n")
    return "".join(parts)


def _latex_escape(value: str) -> str:
    replacements = {"\\": "\\textbackslash{}", "&": "\\&", "%": "\\%", "$": "\\$", "#": "\\#", "_": "\\_", "{": "\\{", "}": "\\}", "~": "\\textasciitilde{}", "^": "\\textasciicircum{}"}
    return "".join(replacements.get(char, char) for char in value)


def _render_latex(columns: list[str], rows: list[tuple[object, ...]], header: bool) -> str:
    parts = ["\\begin{tabular}{" + "l" * len(columns) + "}\n", "\\hline\n"]
    if header:
        parts.append(" & ".join(_latex_escape(name) for name in columns) + " \\\\\n\\hline\n")
    for row in rows:
        parts.append(" & ".join(_latex_escape(_text(value)) for value in row) + " \\\\\n")
    parts.append("\\hline\n\\end{tabular}\n")
    return "".join(parts)


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _render_markdown(columns: list[str], rows: list[tuple[object, ...]]) -> str:
    parts = ["| " + " | ".join(_markdown_cell(name) for name in columns) + " |\n", "|" + "|".join("---" for _ in columns) + "|\n"]
    for row in rows:
        parts.append("| " + " | ".join(_markdown_cell(_text(value)) for value in row) + " |\n")
    return "".join(parts)


def _render_aligned(columns: list[str], rows: list[tuple[object, ...]], header: bool) -> str:
    cells = [[_text(value) for value in row] for row in rows]
    widths = [len(name) if header else 0 for name in columns]
    for row_cells in cells:
        for index, cell in enumerate(row_cells):
            widths[index] = max(widths[index], len(cell))
    parts: list[str] = []
    if header:
        parts.append(" | ".join(name.ljust(widths[index]) for index, name in enumerate(columns)).rstrip() + "\n")
        parts.append("-+-".join("-" * width for width in widths) + "\n")
    for row_cells in cells:
        parts.append(" | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row_cells)).rstrip() + "\n")
    return "".join(parts)


def _render_vertical(columns: list[str], rows: list[tuple[object, ...]]) -> str:
    width = max((len(name) for name in columns), default=0)
    parts: list[str] = []
    for number, row in enumerate(rows, start=1):
        parts.append("-[ RECORD " + str(number) + " ]\n")
        for name, value in zip(columns, row):
            parts.append(name.ljust(width) + " | " + _text(value) + "\n")
    return "".join(parts)


def _render(fmt: TableFormat, columns: list[str], rows: list[tuple[object, ...]], delimiter: str, header: bool) -> str:
    if isinstance(fmt, TableFormat_Aligned):
        return _render_aligned(columns, rows, header)
    if isinstance(fmt, TableFormat_Csv):
        return _render_delimited(columns, rows, delimiter if len(delimiter) == 1 else ",", header)
    if isinstance(fmt, TableFormat_Tsv):
        return _render_delimited(columns, rows, "\t", header)
    if isinstance(fmt, TableFormat_Json):
        return _render_json(columns, rows)
    if isinstance(fmt, TableFormat_JsonLines):
        return _render_json_lines(columns, rows)
    if isinstance(fmt, TableFormat_Html):
        return _render_html(columns, rows, header)
    if isinstance(fmt, TableFormat_Latex):
        return _render_latex(columns, rows, header)
    if isinstance(fmt, TableFormat_Markdown):
        return _render_markdown(columns, rows)
    return _render_vertical(columns, rows)


def _query_message(error: psycopg.Error) -> str:
    primary = error.diag.message_primary
    if primary:
        return primary
    return "query failed"


def _remove_quietly(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        return None
    return None


def export_query(plan: ConnectionPlan, request: ExportRequest) -> Result[TransferResult, ClientError]:
    if isinstance(plan.ssh, Some):
        return Err(error=ClientError_QueryFailed(message="SSH tunnelled connections are not supported for export"))
    tls = plan.tls
    options: dict[str, str] = {}
    if tls.mode:
        options["sslmode"] = tls.mode
    if os.fspath(tls.root_certificate):
        options["sslrootcert"] = os.fspath(tls.root_certificate)
    if os.fspath(tls.certificate):
        options["sslcert"] = os.fspath(tls.certificate)
    if os.fspath(tls.private_key):
        options["sslkey"] = os.fspath(tls.private_key)
    columns: list[str] = []
    rows: list[tuple[object, ...]] = []
    try:
        conninfo = make_conninfo(plan.dsn, **options)
        with psycopg.connect(conninfo, autocommit=False) as connection:
            connection.read_only = True
            with connection.cursor() as cursor:
                cursor.execute(request.sql.encode("utf-8"))
                description = cursor.description
                if description is not None:
                    columns = [column.name for column in description]
                    if request.max_rows > 0:
                        rows = list(cursor.fetchmany(request.max_rows))
            connection.rollback()
    except psycopg.Error as error:
        return Err(error=ClientError_QueryFailed(message=_query_message(error)))
    content = _render(request.format, columns, rows, request.delimiter, request.header)
    target = os.fspath(request.target)
    temporary = target + ".partial-" + secrets.token_hex(16)
    try:
        with open(temporary, "x", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(temporary, target)
    except OSError as error:
        if not isinstance(error, FileExistsError):
            _remove_quietly(temporary)
        return Err(error=ClientError_ExportFailed(path=request.target, message=error.strerror or "export failed"))
    return Ok(value=TransferResult(rows=len(rows), path=request.target))
