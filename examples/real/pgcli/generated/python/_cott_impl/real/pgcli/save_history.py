import json
import os
import secrets
import stat
from typing import Final

import cott_runtime
from cott_runtime import UNIT, CottContractViolation, CottList, Err, Ok, Result, Unit
from real.pgcli_types import ClientError, ClientError_HistoryFailed, HistoryEntry, HistoryPolicy

_MAX_BYTES: Final[int] = 16777216
_U64_MAX: Final[int] = 18446744073709551615
_MSG_SERIALIZE: Final[str] = "history serialization failed"
_MSG_TOO_LARGE: Final[str] = "history too large"
_MSG_NOT_REGULAR: Final[str] = "history path is not a regular file"
_MSG_IO: Final[str] = "history write failed"
_INACTIVE: Final[str] = "fixture adapters are inactive"


def _fail(policy: HistoryPolicy, message: str) -> Result[Unit, ClientError]:
    return Err(error=ClientError_HistoryFailed(path=policy.path, message=message))


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
        sql: object = entry.sql
        database: object = entry.database
        ts: object = entry.executed_at_ms
        success: object = entry.success
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
        return


def _host_replace(policy: HistoryPolicy, data: bytes) -> Result[Unit, ClientError]:
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
    backup_path = os.path.join(parent, "." + name + ".bak-" + secrets.token_hex(8))
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        fd = os.open(tmp_path, flags, 0o600)
    except (OSError, ValueError):
        return _fail(policy, _MSG_IO)
    written_all = False
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
        written_all = True
    except OSError:
        return _fail(policy, _MSG_IO)
    finally:
        try:
            os.close(fd)
        except OSError:
            written_all = False
        if not written_all:
            _discard(tmp_path)
    if _leaf_status(target) is not None:
        _discard(tmp_path)
        return _fail(policy, _MSG_NOT_REGULAR)
    has_backup = False
    try:
        os.link(target, backup_path)
        has_backup = True
    except FileNotFoundError:
        has_backup = False
    except OSError:
        _discard(tmp_path)
        return _fail(policy, _MSG_IO)
    try:
        os.replace(tmp_path, target)
    except OSError:
        _discard(tmp_path)
        if has_backup:
            _discard(backup_path)
        return _fail(policy, _MSG_IO)
    dir_error = False
    try:
        dir_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            try:
                os.close(dir_fd)
            except OSError:
                dir_error = True
    except OSError:
        dir_error = True
    if dir_error:
        if has_backup:
            try:
                os.replace(backup_path, target)
            except OSError:
                return _fail(policy, _MSG_IO)
        else:
            _discard(target)
        return _fail(policy, _MSG_IO)
    if has_backup:
        _discard(backup_path)
    return Ok(value=UNIT)


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
        cott_runtime._cott_fixture_replace(policy.path, data)
    except CottContractViolation as exc:
        if exc.message == _INACTIVE:
            return _host_replace(policy, data)
        return _fail(policy, _MSG_IO)
    except Exception:
        return _fail(policy, _MSG_IO)
    return Ok(value=UNIT)
