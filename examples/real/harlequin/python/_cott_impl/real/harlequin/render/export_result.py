import csv
import io
import json
import math
from pathlib import Path
from typing import Any, Final, cast

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from cott_runtime import UNIT, Err, Ok, Result, Unit

from real.harlequin.core_types import Cell, Cell_Blob, Cell_Integer, Cell_Real, Cell_Text, FileLocation_Local, QueryResult
from real.harlequin.render_types import ExportFormat, ExportFormat_Csv, ExportFormat_Json, ExportFormat_Markdown, ExportFormat_Tsv, ExportRequest, RenderError, RenderError_DestinationDenied, RenderError_ExportFailed

_SQL_TABLE: Final[str] = "result"


def _cell_text(cell: Cell) -> str:
    if isinstance(cell, Cell_Integer):
        return str(cell.value)
    if isinstance(cell, Cell_Real):
        return repr(cell.value)
    if isinstance(cell, Cell_Text):
        return cell.value
    if isinstance(cell, Cell_Blob):
        return bytes(cell.value).hex()
    return ""


def _cell_json(cell: Cell) -> object:
    if isinstance(cell, Cell_Integer):
        return cell.value
    if isinstance(cell, Cell_Real):
        return cell.value if math.isfinite(cell.value) else None
    if isinstance(cell, Cell_Text):
        return cell.value
    if isinstance(cell, Cell_Blob):
        return bytes(cell.value).hex()
    return None


def _cell_sql(cell: Cell) -> str:
    if isinstance(cell, Cell_Integer):
        return str(cell.value)
    if isinstance(cell, Cell_Real):
        return repr(cell.value) if math.isfinite(cell.value) else "NULL"
    if isinstance(cell, Cell_Text):
        return "'" + cell.value.replace("'", "''") + "'"
    if isinstance(cell, Cell_Blob):
        return "X'" + bytes(cell.value).hex() + "'"
    return "NULL"


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _md_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>")


def _serialize(result: QueryResult, fmt: ExportFormat) -> str:
    columns: list[str] = [c for c in result.columns]
    if isinstance(fmt, ExportFormat_Csv) or isinstance(fmt, ExportFormat_Tsv):
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter="\t" if isinstance(fmt, ExportFormat_Tsv) else ",", lineterminator="\n")
        writer.writerow(columns)
        for row in result.rows:
            writer.writerow([_cell_text(cell) for cell in row.values])
        return buffer.getvalue()
    if isinstance(fmt, ExportFormat_Json):
        records: list[dict[str, object]] = []
        for row in result.rows:
            values = [_cell_json(cell) for cell in row.values]
            records.append({name: value for name, value in zip(columns, values)})
        return json.dumps(records, ensure_ascii=False, indent=2) + "\n"
    if isinstance(fmt, ExportFormat_Markdown):
        lines = ["| " + " | ".join(_md_escape(c) for c in columns) + " |", "|" + "|".join(" --- " for _ in columns) + "|"]
        for row in result.rows:
            lines.append("| " + " | ".join(_md_escape(_cell_text(cell)) for cell in row.values) + " |")
        return "\n".join(lines) + "\n"
    column_list = ", ".join(_quote_ident(c) for c in columns)
    statements: list[str] = []
    for row in result.rows:
        sql_values = ", ".join(_cell_sql(cell) for cell in row.values)
        statements.append(f"INSERT INTO {_quote_ident(_SQL_TABLE)} ({column_list}) VALUES ({sql_values});")
    return "\n".join(statements) + ("\n" if statements else "")


def export_result(request: ExportRequest) -> Result[Unit, RenderError]:
    destination = request.destination
    if not destination.writable:
        return Err(error=RenderError_DestinationDenied(destination=destination))
    payload = _serialize(request.result, request.format).encode("utf-8")
    location = destination.location
    if isinstance(location, FileLocation_Local):
        try:
            Path(location.path).write_bytes(payload)
        except OSError as exc:
            return Err(error=RenderError_ExportFailed(destination=destination, message=f"local write failed: {exc.strerror or 'I/O error'}"))
        return Ok(value=UNIT)
    try:
        sdk: Any = boto3
        client: Any = sdk.client("s3")
        client.put_object(Bucket=location.bucket, Key=location.key, Body=payload)
    except ClientError as exc:
        response: Any = exc.response
        error_info: Any = response.get("Error", {})
        code = str(cast(object, error_info.get("Code", "unknown")))
        return Err(error=RenderError_ExportFailed(destination=destination, message=f"S3 upload failed: {code}"))
    except BotoCoreError:
        return Err(error=RenderError_ExportFailed(destination=destination, message="S3 upload failed: client error"))
    return Ok(value=UNIT)
