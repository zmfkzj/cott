import csv
import json
from io import StringIO
from pathlib import Path

import boto3
from cott_runtime import Err, Ok, Result, UNIT, Unit
from real.harlequin.core_types import FileLocation_Local, FileLocation_S3
from real.harlequin.render_types import (
    ExportFormat_Csv,
    ExportFormat_Json,
    ExportFormat_Markdown,
    ExportFormat_Sql,
    ExportFormat_Tsv,
    ExportRequest,
    RenderError,
    RenderError_DestinationDenied,
)


def export_result(request: ExportRequest) -> Result[Unit, RenderError]:
    if not request.destination.writable:
        return Err(error=RenderError_DestinationDenied(destination=request.destination))

    rows = [[str(value) for value in row.values] for row in request.result.rows]
    match request.format:
        case ExportFormat_Csv():
            output = StringIO(newline="")
            csv.writer(output, lineterminator="\n").writerows(rows)
            content = output.getvalue()
        case ExportFormat_Tsv():
            output = StringIO(newline="")
            csv.writer(output, delimiter="\t", lineterminator="\n").writerows(rows)
            content = output.getvalue()
        case ExportFormat_Json():
            content = json.dumps(rows)
        case ExportFormat_Markdown():
            content = "\n".join("| " + " | ".join(row) + " |" for row in rows)
        case ExportFormat_Sql():
            content = "\n".join(
                "INSERT INTO result VALUES ("
                + ", ".join("'" + value.replace("'", "''") + "'" for value in row)
                + ");"
                for row in rows
            )

    match request.destination.location:
        case FileLocation_Local(path=path):
            Path(path).write_text(content, encoding="utf-8")
        case FileLocation_S3(bucket=bucket, key=key):
            boto3.client("s3").put_object(Bucket=bucket, Key=key, Body=content.encode("utf-8"))

    return Ok(value=UNIT)
