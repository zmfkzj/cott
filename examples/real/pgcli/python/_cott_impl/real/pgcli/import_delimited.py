import csv
import io
import os
from pathlib import Path

import cott_runtime
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from cott_runtime import Err, Ok, Result, Some
from real.pgcli_types import ClientError, ClientError_ConnectionFailed, ClientError_ImportFailed, ClientError_QueryFailed, ClientError_TunnelUnsupported, ConnectionPlan, ImportRequest, TlsMode, TlsMode_Allow, TlsMode_Disable, TlsMode_Prefer, TlsMode_Require, TlsMode_VerifyCa, TlsMode_VerifyFull, TransferResult


def _ssl_rank(mode: str) -> int:
    order = ("disable", "allow", "prefer", "require", "verify-ca", "verify-full")
    return order.index(mode) if mode in order else -1


def _import_error(source: Path, message: str) -> Err[ClientError]:
    return Err(error=ClientError_ImportFailed(path=source, message=message))


def _mode_text(mode: TlsMode) -> str:
    if isinstance(mode, TlsMode_Disable):
        return "disable"
    if isinstance(mode, TlsMode_Allow):
        return "allow"
    if isinstance(mode, TlsMode_Prefer):
        return "prefer"
    if isinstance(mode, TlsMode_Require):
        return "require"
    if isinstance(mode, TlsMode_VerifyCa):
        return "verify-ca"
    if isinstance(mode, TlsMode_VerifyFull):
        return "verify-full"
    return ""


def _conninfo(plan: ConnectionPlan) -> str:
    existing = conninfo_to_dict(plan.dsn)
    options: dict[str, str] = {}
    options["connect_timeout"] = "10"
    settings = plan.settings
    for key, value in (("host", settings.host), ("port", settings.port), ("user", settings.user), ("password", settings.password), ("dbname", settings.database)):
        if value:
            options[key] = value
    mode = _mode_text(plan.tls.mode)
    if mode:
        current = existing.get("sslmode")
        current_text = current if isinstance(current, str) else ""
        if current_text == "" or 0 <= _ssl_rank(current_text) <= _ssl_rank(mode):
            options["sslmode"] = mode
    root = plan.tls.root_certificate
    if isinstance(root, Some):
        options["sslrootcert"] = os.fspath(root.value)
    client = plan.tls.client
    if isinstance(client, Some):
        options["sslcert"] = os.fspath(client.value.certificate)
        options["sslkey"] = os.fspath(client.value.private_key)
    return make_conninfo(plan.dsn, **options)


def _read_source(source: Path) -> str | None:
    try:
        data = cott_runtime._cott_fixture_read(source)
    except cott_runtime.CottContractViolation as violation:
        if violation.message != "fixture adapters are inactive":
            return None
        try:
            with open(source, "rb") as handle:
                data = handle.read()
        except OSError:
            return None
    except Exception:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _query_error(error: psycopg.Error) -> Err[ClientError]:
    state = error.diag.sqlstate
    primary = error.diag.message_primary
    if state and primary:
        return Err(error=ClientError_QueryFailed(message=f"{state}: {primary}"))
    if primary:
        return Err(error=ClientError_QueryFailed(message=primary))
    return Err(error=ClientError_QueryFailed(message="database operation failed"))


def import_delimited(plan: ConnectionPlan, request: ImportRequest) -> Result[TransferResult, ClientError]:
    source = request.source
    if len(request.delimiter) != 1:
        return _import_error(source, "delimiter must be a single character")
    if request.table == "":
        return _import_error(source, "invalid table name")
    if isinstance(plan.ssh, Some):
        return Err(error=ClientError_TunnelUnsupported())
    parts = request.table.split(".")
    if len(parts) > 2 or any(not part for part in parts):
        return _import_error(source, "invalid table name")
    text = _read_source(source)
    if text is None:
        return _import_error(source, "cannot read source file")
    rows: list[list[str | None]] = []
    try:
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=request.delimiter, quotechar='"', doublequote=True, strict=True)
        first = True
        for record in reader:
            if first and request.header:
                first = False
                continue
            first = False
            if len(rows) >= request.max_rows:
                return _import_error(source, "row count exceeds max_rows")
            rows.append([None if field == request.null_text else field for field in record])
    except (csv.Error, TypeError, ValueError):
        return _import_error(source, "malformed delimited data")
    try:
        conninfo = _conninfo(plan)
    except (psycopg.Error, TypeError, ValueError):
        return Err(error=ClientError_ConnectionFailed(message="invalid connection parameters"))
    try:
        connection = psycopg.connect(conninfo, autocommit=False, connect_timeout=10)
    except (psycopg.Error, TypeError, ValueError):
        return Err(error=ClientError_ConnectionFailed(message="could not connect to server"))
    statement = sql.SQL("COPY {} FROM STDIN").format(sql.Identifier(*parts))
    try:
        with connection:
            with connection.cursor() as cursor:
                with cursor.copy(statement) as copy:
                    for row in rows:
                        copy.write_row(row)
    except psycopg.Error as error:
        return _query_error(error)
    finally:
        connection.close()
    return Ok(value=TransferResult(rows=len(rows), path=source))
