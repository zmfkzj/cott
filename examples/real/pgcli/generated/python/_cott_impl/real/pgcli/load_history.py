import errno
import json
import os
import stat
from pathlib import Path
from typing import Final, cast

import cott_runtime
from cott_runtime import CottContractViolation, CottList, Err, Ok, Result
from real.pgcli_types import ClientError, ClientError_HistoryFailed, HistoryEntry, HistoryPolicy

_MAX_BYTES: Final[int] = 16777216
_U64_MAX: Final[int] = 18446744073709551615
_CHUNK_BYTES: Final[int] = 65536
_INACTIVE_FIXTURES: Final[str] = "fixture adapters are inactive"
_MESSAGE_UNREADABLE: Final[str] = "history file unreadable"
_MESSAGE_TOO_LARGE: Final[str] = "history file too large"
_MESSAGE_UTF8: Final[str] = "history file is not valid UTF-8"
_MESSAGE_JSON: Final[str] = "history file is not valid JSON"
_MESSAGE_ROOT: Final[str] = "history root is not an array"
_MESSAGE_ENTRY: Final[str] = "history entry is invalid"


def _failure(path: Path, message: str) -> Err[ClientError]:
    return Err(error=ClientError_HistoryFailed(path=path, message=message))


def _read_host(path: Path) -> bytes | None:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        return None
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError(errno.EINVAL, "not a regular file")
        chunks: list[bytes] = []
        size = 0
        while True:
            chunk = os.read(descriptor, _CHUNK_BYTES)
            if not chunk:
                break
            size += len(chunk)
            if size > _MAX_BYTES:
                raise OSError(errno.EFBIG, "history file too large")
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _parse_entry(item: object) -> HistoryEntry | None:
    if not isinstance(item, dict):
        return None
    fields = cast(dict[object, object], item)
    if set(fields) != {"sql", "executed_at_ms", "database", "success"}:
        return None
    sql = fields["sql"]
    executed_at_ms = fields["executed_at_ms"]
    database = fields["database"]
    success = fields["success"]
    if type(sql) is not str or type(database) is not str or type(success) is not bool:
        return None
    if type(executed_at_ms) is not int or executed_at_ms < 0 or executed_at_ms > _U64_MAX:
        return None
    return HistoryEntry(sql=sql, executed_at_ms=executed_at_ms, database=database, success=success)


def _normalize(entries: list[HistoryEntry], policy: HistoryPolicy) -> list[HistoryEntry]:
    normalized = entries
    if policy.unique:
        last_positions: dict[tuple[str, str], int] = {}
        for index, entry in enumerate(normalized):
            last_positions[(entry.database, entry.sql)] = index
        normalized = [entry for index, entry in enumerate(normalized) if last_positions[(entry.database, entry.sql)] == index]
    if policy.max_entries == 0:
        return []
    if len(normalized) > policy.max_entries:
        normalized = normalized[len(normalized) - policy.max_entries:]
    return normalized


def load_history(policy: HistoryPolicy) -> Result[CottList[HistoryEntry], ClientError]:
    path = policy.path
    data: bytes | None
    try:
        data = cott_runtime._cott_fixture_read(path)
    except CottContractViolation as error:
        if error.message == _INACTIVE_FIXTURES:
            try:
                data = _read_host(path)
            except OSError as host_error:
                message = _MESSAGE_TOO_LARGE if host_error.errno == errno.EFBIG else _MESSAGE_UNREADABLE
                return _failure(path, message)
        elif isinstance(error.__cause__, FileNotFoundError):
            return Ok(value=CottList(values=[]))
        else:
            return _failure(path, _MESSAGE_UNREADABLE)
    except FileNotFoundError:
        return Ok(value=CottList(values=[]))
    except OSError:
        return _failure(path, _MESSAGE_UNREADABLE)
    if data is None:
        return Ok(value=CottList(values=[]))
    if len(data) > _MAX_BYTES:
        return _failure(path, _MESSAGE_TOO_LARGE)
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return _failure(path, _MESSAGE_UTF8)
    try:
        decoded: object = json.loads(text)
    except (ValueError, RecursionError):
        return _failure(path, _MESSAGE_JSON)
    if not isinstance(decoded, list):
        return _failure(path, _MESSAGE_ROOT)
    entries: list[HistoryEntry] = []
    for item in cast(list[object], decoded):
        entry = _parse_entry(item)
        if entry is None:
            return _failure(path, _MESSAGE_ENTRY)
        entries.append(entry)
    return Ok(value=CottList(values=_normalize(entries, policy)))
