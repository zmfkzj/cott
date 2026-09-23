import json
import os
import secrets
import stat
from typing import Final

from cott_runtime import CottList, Err, Ok, Result, UNIT, Unit
from real.pgcli_types import ClientError, ClientError_FavoriteFailed, Favorite, FavoriteStore

_MAX_BYTES: Final[int] = 16777216


def _failure(store: FavoriteStore) -> Err[ClientError]:
    return Err(error=ClientError_FavoriteFailed(name=str(store.path)))


def _encode(store: FavoriteStore, favorites: CottList[Favorite]) -> bytes | None:
    items: list[dict[str, object]] = []
    seen: set[str] = set()
    for fav in favorites:
        name = fav.name
        if name == "" or name in seen:
            return None
        seen.add(name)
        tags: list[str] = []
        for tag in fav.tags:
            tags.append(tag)
        items.append({"name": name, "sql": fav.sql, "tags": tags})
    if len(items) > store.max_entries:
        return None
    try:
        data = (json.dumps(items, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError):
        return None
    if len(data) > _MAX_BYTES:
        return None
    return data


def _leaf_ok(path: str) -> bool:
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return stat.S_ISREG(st.st_mode)


def _discard(tmp: str) -> None:
    try:
        os.unlink(tmp)
    except OSError:
        return


def _write_atomic(path: str, data: bytes) -> bool:
    parent = os.path.dirname(path) or "."
    if not _leaf_ok(path) or not os.path.isdir(parent):
        return False
    tmp = os.path.join(parent, "." + os.path.basename(path) + "." + secrets.token_hex(8) + ".tmp")
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    except OSError:
        return False
    committed = False
    try:
        try:
            os.fchmod(fd, 0o600)
            view = memoryview(data)
            while view:
                n = os.write(fd, view)
                view = view[n:]
            os.fsync(fd)
        finally:
            os.close(fd)
        if not _leaf_ok(path):
            return False
        os.replace(tmp, path)
        committed = True
        dfd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
        return True
    except OSError:
        return False
    finally:
        if not committed:
            _discard(tmp)


def save_favorites(store: FavoriteStore, favorites: CottList[Favorite]) -> Result[Unit, ClientError]:
    path = os.fspath(store.path)
    if path == "" or os.path.basename(path) == "":
        return _failure(store)
    try:
        data = _encode(store, favorites)
        if data is None:
            return _failure(store)
        if not _write_atomic(path, data):
            return _failure(store)
    except (OSError, ValueError, TypeError, RecursionError, MemoryError):
        return _failure(store)
    return Ok(value=UNIT)
