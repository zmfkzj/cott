import errno
import json
import os
import stat
from typing import Final, cast

from cott_runtime import CottList, Err, Ok, Result
from real.pgcli_types import ClientError, ClientError_HistoryFailed, HistoryEntry, HistoryPolicy

_MAX_BYTES: Final[int] = 16777216
_U64_MAX: Final[int] = 18446744073709551615
_CHUNK: Final[int] = 65536


def _read_bounded(path: str) -> bytes | None:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        return None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError(errno.EINVAL, "not a regular file")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, _CHUNK)
            if not chunk:
                break
            total += len(chunk)
            if total > _MAX_BYTES:
                raise OSError(errno.EFBIG, "too large")
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def _parse_entry(item: object) -> HistoryEntry | None:
    if not isinstance(item, dict):
        return None
    obj = cast(dict[object, object], item)
    if set(obj.keys()) != {"sql", "executed_at_ms", "database", "success"}:
        return None
    sql = obj["sql"]
    ts = obj["executed_at_ms"]
    database = obj["database"]
    success = obj["success"]
    if not isinstance(sql, str) or type(sql) is not str:
        return None
    if not isinstance(database, str) or type(database) is not str:
        return None
    if not isinstance(success, bool):
        return None
    if isinstance(ts, bool) or not isinstance(ts, int) or type(ts) is not int:
        return None
    if ts < 0 or ts > _U64_MAX:
        return None
    return HistoryEntry(sql=sql, executed_at_ms=ts, database=database, success=success)


def load_history(policy: HistoryPolicy) -> Result[CottList[HistoryEntry], ClientError]:
    path = policy.path
    try:
        data = _read_bounded(os.fspath(path))
    except OSError as exc:
        message = "history file too large" if exc.errno == errno.EFBIG else "history file unreadable"
        return Err(error=ClientError_HistoryFailed(path=path, message=message))
    if data is None:
        return Ok(value=CottList(values=[]))
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return Err(error=ClientError_HistoryFailed(path=path, message="history file is not valid UTF-8"))
    try:
        root: object = json.loads(text)
    except (ValueError, RecursionError):
        return Err(error=ClientError_HistoryFailed(path=path, message="history file is not valid JSON"))
    if not isinstance(root, list):
        return Err(error=ClientError_HistoryFailed(path=path, message="history root is not an array"))
    items = cast(list[object], root)
    entries: list[HistoryEntry] = []
    for item in items:
        entry = _parse_entry(item)
        if entry is None:
            return Err(error=ClientError_HistoryFailed(path=path, message="history entry is invalid"))
        entries.append(entry)
    if policy.unique:
        last_index: dict[tuple[str, str], int] = {}
        for index, entry in enumerate(entries):
            last_index[(entry.database, entry.sql)] = index
        entries = [entry for index, entry in enumerate(entries) if last_index[(entry.database, entry.sql)] == index]
    capacity = policy.max_entries
    if capacity == 0:
        return Ok(value=CottList(values=[]))
    if len(entries) > capacity:
        entries = entries[len(entries) - capacity:]
    return Ok(value=CottList(values=entries))
