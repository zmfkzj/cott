import json
import math
import os
import tempfile
from typing import Any, Final, cast

import boto3
from botocore.exceptions import ClientError
import cott_runtime
from cott_runtime import CottContractViolation, Err, Ok, Result, U64

from real.harlequin.core_types import Cell, Cell_Integer, Cell_Null, Cell_Real, Cell_Text, FileLocation_Local, FileReference, QueryResult, SavedFile
from real.harlequin.render_types import ExportFormat, ExportFormat_Csv, ExportFormat_Json, ExportFormat_Markdown, ExportFormat_Tsv, ExportRequest, RenderError, RenderError_DestinationDenied, RenderError_ExportFailed, RenderError_UnsupportedCell

_INACTIVE: Final[str] = "fixture adapters are inactive"
_NON_FINITE: Final[str] = "non-finite float cannot be exported"
_WRITE_FAILED: Final[str] = "export write failed"

def _cell_text(cell: Cell) -> str:
    if isinstance(cell, Cell_Null):
        return ""
    elif isinstance(cell, Cell_Integer):
        return str(cell.value)
    elif isinstance(cell, Cell_Real):
        return repr(cell.value)
    elif isinstance(cell, Cell_Text):
        return cell.value
    else:
        return bytes(cell.value).hex()

def _csv_field(text: str) -> str:
    if any(ch in text for ch in (",", '"', "\r", "\n")):
        return '"' + text.replace('"', '""') + '"'
    return text

def _tsv_field(text: str) -> str:
    return text.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")

def _md_field(text: str) -> str:
    return text.replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")

def _cell_json(cell: Cell) -> Result[object, RenderError]:
    if isinstance(cell, Cell_Null):
        return Ok(value=None)
    elif isinstance(cell, Cell_Integer):
        return Ok(value=cell.value)
    elif isinstance(cell, Cell_Real):
        if not math.isfinite(cell.value):
            return Err(error=RenderError_UnsupportedCell(message=_NON_FINITE))
        return Ok(value=cell.value)
    elif isinstance(cell, Cell_Text):
        return Ok(value=cell.value)
    else:
        return Ok(value=bytes(cell.value).hex())

def _cell_sql(cell: Cell) -> Result[str, RenderError]:
    if isinstance(cell, Cell_Null):
        return Ok(value="NULL")
    elif isinstance(cell, Cell_Integer):
        return Ok(value=str(cell.value))
    elif isinstance(cell, Cell_Real):
        if not math.isfinite(cell.value):
            return Err(error=RenderError_UnsupportedCell(message=_NON_FINITE))
        return Ok(value=repr(cell.value))
    elif isinstance(cell, Cell_Text):
        return Ok(value="'" + cell.value.replace("'", "''") + "'")
    else:
        return Ok(value="X'" + bytes(cell.value).hex() + "'")

def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def _lines(lines: list[str]) -> str:
    return "".join(line + "\n" for line in lines)

def _serialize(result: QueryResult, fmt: ExportFormat) -> Result[str, RenderError]:
    columns: list[str] = [c for c in result.columns]
    if isinstance(fmt, ExportFormat_Json):
        rows: list[list[object]] = []
        for row in result.rows:
            values: list[object] = []
            for cell in row.values:
                converted = _cell_json(cell)
                if isinstance(converted, Err):
                    return Err(error=converted.error)
                values.append(converted.value)
            rows.append(values)
        text = json.dumps({"columns": columns, "rows": rows}, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        return Ok(value=text + "\n")
    if not columns:
        return Ok(value="")
    if isinstance(fmt, ExportFormat_Csv):
        lines = [",".join(_csv_field(c) for c in columns)]
        for row in result.rows:
            lines.append(",".join(_csv_field(_cell_text(cell)) for cell in row.values))
        return Ok(value=_lines(lines))
    elif isinstance(fmt, ExportFormat_Tsv):
        lines = ["\t".join(_tsv_field(c) for c in columns)]
        for row in result.rows:
            lines.append("\t".join(_tsv_field(_cell_text(cell)) for cell in row.values))
        return Ok(value=_lines(lines))
    elif isinstance(fmt, ExportFormat_Markdown):
        lines = ["| " + " | ".join(_md_field(c) for c in columns) + " |", "| --- |" + " --- |" * (len(columns) - 1)]
        for row in result.rows:
            lines.append("| " + " | ".join(_md_field(_cell_text(cell)) for cell in row.values) + " |")
        return Ok(value=_lines(lines))
    else:
        column_list = ", ".join(_quote_ident(c) for c in columns)
        statements: list[str] = []
        for row in result.rows:
            parts: list[str] = []
            for cell in row.values:
                converted_sql = _cell_sql(cell)
                if isinstance(converted_sql, Err):
                    return Err(error=converted_sql.error)
                parts.append(converted_sql.value)
            statements.append('INSERT INTO "result" (' + column_list + ") VALUES (" + ", ".join(parts) + ");")
        return Ok(value=_lines(statements))

def _discard(temp_path: str) -> None:
    try:
        os.unlink(temp_path)
    except OSError:
        return None

def _host_replace(path: str, data: bytes) -> None:
    folder = os.path.split(os.path.abspath(path))[0]
    fd, temp_path = tempfile.mkstemp("", ".cott-save-", folder)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except BaseException:
        _discard(temp_path)
        raise

def _write_local(destination: FileReference, path: str, data: bytes) -> Result[None, RenderError]:
    try:
        cott_runtime._cott_fixture_replace(path, data)
    except CottContractViolation as exc:
        if exc.message != _INACTIVE:
            if isinstance(exc.__cause__, PermissionError):
                return Err(error=RenderError_DestinationDenied(destination=destination))
            return Err(error=RenderError_ExportFailed(destination=destination, message=_WRITE_FAILED))
        try:
            _host_replace(path, data)
        except PermissionError:
            return Err(error=RenderError_DestinationDenied(destination=destination))
        except OSError:
            return Err(error=RenderError_ExportFailed(destination=destination, message=_WRITE_FAILED))
        except Exception:
            return Err(error=RenderError_ExportFailed(destination=destination, message=_WRITE_FAILED))
    except PermissionError:
        return Err(error=RenderError_DestinationDenied(destination=destination))
    except Exception:
        return Err(error=RenderError_ExportFailed(destination=destination, message=_WRITE_FAILED))
    return Ok(value=None)

def _write_s3(destination: FileReference, bucket: str, key: str, data: bytes) -> Result[None, RenderError]:
    try:
        sdk: Any = boto3
        client: Any = sdk.client("s3")
        client.put_object(Bucket=bucket, Key=key, Body=data)
    except ClientError as exc:
        error_info = cast(object, exc.response.get("Error", {}))
        code = ""
        if isinstance(error_info, dict):
            info = cast(dict[str, object], error_info)
            raw_code = info.get("Code")
            if isinstance(raw_code, str):
                code = raw_code
        if code in ("AccessDenied", "403", "Forbidden", "AllAccessDisabled", "InvalidAccessKeyId", "SignatureDoesNotMatch"):
            return Err(error=RenderError_DestinationDenied(destination=destination))
        return Err(error=RenderError_ExportFailed(destination=destination, message=_WRITE_FAILED))
    except Exception:
        return Err(error=RenderError_ExportFailed(destination=destination, message=_WRITE_FAILED))
    return Ok(value=None)

def export_result(request: ExportRequest) -> Result[SavedFile, RenderError]:
    destination = request.destination
    if not destination.writable:
        return Err(error=RenderError_DestinationDenied(destination=destination))
    serialized = _serialize(request.result, request.format)
    if isinstance(serialized, Err):
        return Err(error=serialized.error)
    data = serialized.value.encode("utf-8")
    location = destination.location
    if isinstance(location, FileLocation_Local):
        written = _write_local(destination, os.fspath(location.path), data)
    else:
        written = _write_s3(destination, location.bucket, location.key, data)
    if isinstance(written, Err):
        return Err(error=written.error)
    size: U64 = len(data)
    return Ok(value=SavedFile(reference=destination, bytes_written=size))
