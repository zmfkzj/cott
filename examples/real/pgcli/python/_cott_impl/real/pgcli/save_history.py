import json
import os
import secrets
import stat
from typing import Final

from cott_runtime import UNIT, CottList, Err, Ok, Result, Unit
from real.pgcli_types import ClientError, ClientError_HistoryFailed, HistoryEntry, HistoryPolicy

_MAX_BYTES: Final[int] = 16777216
_U64_MAX: Final[int] = 18446744073709551615
_MSG_SERIALIZE: Final[str] = "history serialization failed"
_MSG_TOO_LARGE: Final[str] = "history too large"
_MSG_NOT_REGULAR: Final[str] = "history path is not a regular file"
_MSG_IO: Final[str] = "history write failed"


def _normalize(policy: HistoryPolicy, entries: CottList[HistoryEntry]) -> list[HistoryEntry]:
    items: list[HistoryEntry] = [entry for entry in entries]
    if policy.unique:
        last_index: dict[tuple[str, str], int] = {}
        for index, entry in enumerate(items):
            last_index[(entry.database, entry.sql)] = index
        items = [entry for index, entry in enumerate(items) if last_index[(entry.database, entry.sql)] == index]
    capacity = policy.max_entries
    if capacity <= 0:
        return []
    if len(items) > capacity:
        items = items[len(items) - capacity :]
    return items


def _serialize(items: list[HistoryEntry]) -> bytes | None:
    records: list[dict[str, object]] = []
    for entry in items:
        sql = entry.sql
        database = entry.database
        ts = entry.executed_at_ms
        success = entry.success
        if type(sql) is not str or type(database) is not str or type(success) is not bool:
            return None
        if type(ts) is not int or ts < 0 or ts > _U64_MAX:
            return None
        records.append({"sql": sql, "executed_at_ms": ts, "database": database, "success": success})
    try:
        text = json.dumps(records, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n"
        return text.encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        return None


def _fail(policy: HistoryPolicy, message: str) -> Result[Unit, ClientError]:
    return Err(error=ClientError_HistoryFailed(path=policy.path, message=message))


def _leaf_status(target: str) -> str | None:
    try:
        info = os.lstat(target)
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        return _MSG_IO
    if not stat.S_ISREG(info.st_mode):
        return _MSG_NOT_REGULAR
    return None


def _discard(tmp_path: str) -> None:
    try:
        os.unlink(tmp_path)
    except OSError:
        return None
    return None


def save_history(policy: HistoryPolicy, entries: CottList[HistoryEntry]) -> Result[Unit, ClientError]:
    try:
        data = _serialize(_normalize(policy, entries))
    except (TypeError, ValueError, AttributeError, KeyError, OverflowError):
        return _fail(policy, _MSG_SERIALIZE)
    if data is None:
        return _fail(policy, _MSG_SERIALIZE)
    if len(data) > _MAX_BYTES:
        return _fail(policy, _MSG_TOO_LARGE)
    try:
        target = os.path.abspath(os.fspath(policy.path))
    except (TypeError, ValueError):
        return _fail(policy, _MSG_IO)
    parent = os.path.dirname(target)
    name = os.path.basename(target)
    leaf_error = _leaf_status(target)
    if leaf_error is not None:
        return _fail(policy, leaf_error)
    tmp_path = os.path.join(parent, "." + name + ".tmp-" + secrets.token_hex(8))
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        fd = os.open(tmp_path, flags, 0o600)
    except (OSError, ValueError):
        return _fail(policy, _MSG_IO)
    committed = False
    try:
        try:
            os.fchmod(fd, 0o600)
            view = memoryview(data)
            written = 0
            while written < len(data):
                count = os.write(fd, view[written:])
                if count <= 0:
                    raise OSError("short write")
                written += count
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp_path, target)
        committed = True
    except OSError:
        return _fail(policy, _MSG_IO)
    finally:
        if not committed:
            _discard(tmp_path)
    try:
        dir_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        return _fail(policy, _MSG_IO)
    return Ok(value=UNIT)
