import contextlib
import csv
import io
import os
import secrets
import stat
from pathlib import Path
from typing import Final

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo

import cott_runtime
from cott_runtime import CottContractViolation, Err, Ok, Result, Some
from real.pgcli_types import ClientError, ClientError_ConnectionFailed, ClientError_ExportFailed, ClientError_QueryFailed, ClientError_TunnelUnsupported, ClientError_UnsupportedFormat, ConnectionPlan, ExportRequest, TableFormat, TableFormat_Aligned, TableFormat_Csv, TableFormat_Html, TableFormat_Json, TableFormat_JsonLines, TableFormat_Latex, TableFormat_Markdown, TableFormat_Tsv, TlsMode, TlsMode_Allow, TlsMode_Default, TlsMode_Disable, TlsMode_Prefer, TlsMode_Require, TlsMode_VerifyCa, TransferResult

_INACTIVE: Final[str] = "fixture adapters are inactive"
_SSL_MODES: Final[str] = "disable allow prefer require verify-ca verify-full"


def _format_name(fmt: TableFormat) -> str:
    if isinstance(fmt, TableFormat_Aligned):
        return "aligned"
    if isinstance(fmt, TableFormat_Csv):
        return "csv"
    if isinstance(fmt, TableFormat_Tsv):
        return "tsv"
    if isinstance(fmt, TableFormat_Json):
        return "json"
    if isinstance(fmt, TableFormat_JsonLines):
        return "jsonl"
    if isinstance(fmt, TableFormat_Html):
        return "html"
    if isinstance(fmt, TableFormat_Latex):
        return "latex"
    if isinstance(fmt, TableFormat_Markdown):
        return "markdown"
    return "vertical"


def _mode_name(mode: TlsMode) -> str | None:
    if isinstance(mode, TlsMode_Default):
        return None
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
    return "verify-full"


def _mode_rank(mode: str) -> int:
    names = _SSL_MODES.split(" ")
    if mode in names:
        return names.index(mode)
    return len(names)


def _conninfo(plan: ConnectionPlan) -> str:
    parsed = conninfo_to_dict(plan.dsn)
    overrides: dict[str, str] = {}
    settings = plan.settings
    for key, value in (("host", settings.host), ("port", settings.port), ("user", settings.user), ("password", settings.password), ("dbname", settings.database)):
        if value:
            overrides[key] = value
    requested = _mode_name(plan.tls.mode)
    if requested is not None:
        existing = parsed.get("sslmode")
        if isinstance(existing, str) and _mode_rank(existing) > _mode_rank(requested):
            requested = existing
        overrides["sslmode"] = requested
    root = plan.tls.root_certificate
    if isinstance(root, Some):
        overrides["sslrootcert"] = os.fspath(root.value)
    client = plan.tls.client
    if isinstance(client, Some):
        overrides["sslcert"] = os.fspath(client.value.certificate)
        overrides["sslkey"] = os.fspath(client.value.private_key)
    overrides["connect_timeout"] = "10"
    return make_conninfo(plan.dsn, **overrides)


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "t" if value else "f"
    if isinstance(value, (bytes, bytearray)):
        return "\\x" + bytes(value).hex()
    return str(value)


def _export_failed(target: Path, message: str) -> Err[ClientError]:
    return Err(error=ClientError_ExportFailed(path=target, message=message))


def _query_failed(error: psycopg.Error) -> Err[ClientError]:
    diag = error.diag
    state = diag.sqlstate
    primary = diag.message_primary
    if state and primary:
        return Err(error=ClientError_QueryFailed(message=state + ": " + primary))
    if state:
        return Err(error=ClientError_QueryFailed(message=state))
    return Err(error=ClientError_QueryFailed(message="query failed"))


def _discard(directory: int, name: str) -> None:
    with contextlib.suppress(OSError):
        os.unlink(name, dir_fd=directory)


def _is_regular(directory: int, name: str) -> bool:
    return stat.S_ISREG(os.lstat(name, dir_fd=directory).st_mode)


def _install(directory: int, name: str, temporary: str, backup: str | None) -> str | None:
    # A hard link keeps the previous target reachable until the new entry is
    # durable, so a directory fsync failure can restore the original state.
    if backup is not None:
        os.link(name, backup, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
        if not _is_regular(directory, backup):
            _discard(directory, backup)
            _discard(directory, temporary)
            return "target is not a regular file"
    os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
    try:
        os.fsync(directory)
    except OSError:
        with contextlib.suppress(OSError):
            if backup is None:
                os.unlink(name, dir_fd=directory)
            else:
                os.replace(backup, name, src_dir_fd=directory, dst_dir_fd=directory)
            os.fsync(directory)
        return "cannot sync target directory"
    if backup is not None:
        _discard(directory, backup)
        with contextlib.suppress(OSError):
            os.fsync(directory)
    return None


def _replace_host(target: Path, data: bytes) -> str | None:
    path = os.fspath(target)
    name = os.path.basename(path)
    if not name:
        return "target is not a regular file"
    parent = os.path.dirname(path) or "."
    try:
        directory = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    except OSError:
        return "cannot open target directory"
    try:
        exists = True
        try:
            if not _is_regular(directory, name):
                return "target is not a regular file"
        except FileNotFoundError:
            exists = False
        except OSError:
            return "cannot inspect target"
        token = secrets.token_hex(16)
        temporary = "." + name + ".tmp-" + token
        backup = "." + name + ".old-" + token if exists else None
        try:
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=directory)
        except OSError:
            return "cannot create temporary file"
        try:
            try:
                os.fchmod(descriptor, 0o600)
                view = memoryview(data)
                while view:
                    written = os.write(descriptor, view)
                    view = view[written:]
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except OSError:
            _discard(directory, temporary)
            return "cannot write target"
        try:
            return _install(directory, name, temporary, backup)
        except OSError:
            _discard(directory, temporary)
            if backup is not None:
                _discard(directory, backup)
            return "cannot write target"
    finally:
        os.close(directory)


def export_query(plan: ConnectionPlan, request: ExportRequest) -> Result[TransferResult, ClientError]:
    fmt = request.format
    if isinstance(fmt, TableFormat_Csv):
        if len(request.delimiter) != 1:
            return _export_failed(request.target, "invalid delimiter")
        delimiter = request.delimiter
    elif isinstance(fmt, TableFormat_Tsv):
        delimiter = "\t"
    else:
        return Err(error=ClientError_UnsupportedFormat(value=_format_name(fmt)))
    if isinstance(plan.ssh, Some):
        return Err(error=ClientError_TunnelUnsupported())
    try:
        conninfo = _conninfo(plan)
    except psycopg.Error:
        return Err(error=ClientError_ConnectionFailed(message="invalid connection parameters"))
    try:
        connection = psycopg.connect(conninfo, autocommit=False, connect_timeout=10)
    except psycopg.Error:
        return Err(error=ClientError_ConnectionFailed(message="connection failed"))
    columns: list[str] = []
    rows: list[tuple[object, ...]] = []
    try:
        with connection:
            connection.read_only = True
            with connection.cursor() as cursor:
                cursor.execute(request.sql.encode("utf-8"))
                description = cursor.description
                if description is not None:
                    columns = [column.name for column in description]
                    rows = list(cursor.fetchmany(request.max_rows + 1))
            connection.rollback()
    except psycopg.OperationalError as error:
        if connection.broken:
            return Err(error=ClientError_ConnectionFailed(message="connection lost"))
        return _query_failed(error)
    except psycopg.Error as error:
        return _query_failed(error)
    if len(rows) > request.max_rows:
        return _export_failed(request.target, "row limit exceeded")
    buffer = io.StringIO()
    try:
        writer = csv.writer(buffer, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        if request.header:
            writer.writerow(columns)
        for row in rows:
            writer.writerow([_text(value) for value in row])
    except csv.Error:
        return _export_failed(request.target, "cannot encode rows")
    try:
        data = buffer.getvalue().encode("utf-8")
    except UnicodeEncodeError:
        return _export_failed(request.target, "cannot encode rows")
    try:
        cott_runtime._cott_fixture_replace(request.target, data)
    except CottContractViolation as violation:
        if violation.message != _INACTIVE:
            return _export_failed(request.target, "cannot write target")
        failure = _replace_host(request.target, data)
        if failure is not None:
            return _export_failed(request.target, failure)
    except Exception:
        return _export_failed(request.target, "cannot write target")
    return Ok(value=TransferResult(rows=len(rows), path=request.target))
