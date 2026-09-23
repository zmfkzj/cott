import csv
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

from cott_runtime import Err, Ok, Result, Some
from real.pgcli_types import ClientError, ClientError_ImportFailed, ClientError_QueryFailed, ConnectionPlan, ImportRequest, TransferResult


def _path_text(value: Path) -> str:
    text = str(value)
    return "" if text in ("", ".") else text


def _conninfo(plan: ConnectionPlan) -> str:
    options: dict[str, str] = {}
    settings = plan.settings
    for key, value in (("host", settings.host), ("port", settings.port), ("user", settings.user), ("password", settings.password), ("dbname", settings.database), ("sslmode", plan.tls.mode)):
        if value:
            options[key] = value
    for key, path in (("sslrootcert", plan.tls.root_certificate), ("sslcert", plan.tls.certificate), ("sslkey", plan.tls.private_key)):
        text = _path_text(path)
        if text:
            options[key] = text
    return make_conninfo(plan.dsn, **options)


def _db_message(error: psycopg.Error) -> str:
    primary = error.diag.message_primary
    return primary if primary else "database operation failed"


def import_delimited(plan: ConnectionPlan, request: ImportRequest) -> Result[TransferResult, ClientError]:
    source = request.source
    if len(request.delimiter) != 1:
        return Err(error=ClientError_ImportFailed(path=source, message="delimiter must be a single character"))
    if isinstance(plan.ssh, Some):
        return Err(error=ClientError_QueryFailed(message="SSH tunnelled connections are not supported for import"))
    parts = request.table.split(".")
    if not request.table or any(not part for part in parts):
        return Err(error=ClientError_ImportFailed(path=source, message="invalid table name"))
    rows: list[list[str | None]] = []
    try:
        with open(source, newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle, delimiter=request.delimiter)
            first = True
            for record in reader:
                if first and request.header:
                    first = False
                    continue
                first = False
                if len(rows) >= request.max_rows:
                    return Err(error=ClientError_ImportFailed(path=source, message="row count exceeds max_rows"))
                rows.append([None if field == request.null_text else field for field in record])
    except OSError:
        return Err(error=ClientError_ImportFailed(path=source, message="cannot read source file"))
    except UnicodeDecodeError:
        return Err(error=ClientError_ImportFailed(path=source, message="source file is not valid UTF-8"))
    except csv.Error:
        return Err(error=ClientError_ImportFailed(path=source, message="malformed delimited data"))
    statement = sql.SQL("COPY {} FROM STDIN").format(sql.Identifier(*parts))
    try:
        conninfo = _conninfo(plan)
        with psycopg.connect(conninfo, autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    with cursor.copy(statement) as copy:
                        for row in rows:
                            copy.write_row(row)
                connection.commit()
            except psycopg.Error:
                connection.rollback()
                raise
    except psycopg.Error as error:
        return Err(error=ClientError_QueryFailed(message=_db_message(error)))
    return Ok(value=TransferResult(rows=len(rows), path=source))
