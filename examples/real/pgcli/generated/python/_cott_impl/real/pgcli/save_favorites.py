import json
import os
import secrets
import stat
from typing import Final

import cott_runtime
from cott_runtime import CottList, Err, Ok, Result, UNIT, Unit
from real.pgcli_types import ClientError, ClientError_FavoriteFailed, Favorite, FavoriteStore

_MAX_BYTES: Final[int] = 16777216
_WHITE_SPACE: Final[str] = "\t\n\x0b\x0c\r \x85\xa0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000"
_INACTIVE: Final[str] = "fixture adapters are inactive"


def _failure(name: str) -> Err[ClientError]:
    return Err(error=ClientError_FavoriteFailed(name=name))


def _is_blank(name: str) -> bool:
    for ch in name:
        if ch not in _WHITE_SPACE:
            return False
    return True


def _bad_name(favorites: CottList[Favorite]) -> str | None:
    seen: set[str] = set()
    for fav in favorites:
        name = fav.name
        if _is_blank(name) or name in seen:
            return name
        seen.add(name)
    return None


def _encode(favorites: CottList[Favorite]) -> bytes | None:
    items: list[dict[str, object]] = []
    for fav in favorites:
        tags: list[str] = []
        for tag in fav.tags:
            tags.append(tag)
        items.append({"name": fav.name, "sql": fav.sql, "tags": tags})
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


def _close(fd: int) -> bool:
    try:
        os.close(fd)
    except OSError:
        return False
    return True


def _sync(fd: int) -> bool:
    try:
        os.fsync(fd)
    except OSError:
        return False
    return True


def _write_file(tmp: str, data: bytes) -> bool:
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    except OSError:
        return False
    ok = True
    try:
        os.fchmod(fd, 0o600)
        view = memoryview(data)
        while view:
            n = os.write(fd, view)
            if n <= 0:
                ok = False
                break
            view = view[n:]
        if ok:
            os.fsync(fd)
    except OSError:
        ok = False
    if not _close(fd):
        ok = False
    if not ok:
        _discard(tmp)
    return ok


def _rollback(path: str, backup: str, had_previous: bool) -> bool:
    ok = True
    try:
        if had_previous:
            os.replace(backup, path)
        else:
            os.unlink(path)
    except OSError:
        ok = False
    try:
        dfd = os.open(os.path.dirname(path) or ".", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        if not _sync(dfd):
            ok = False
        if not _close(dfd):
            ok = False
    except OSError:
        ok = False
    return ok


def _write_atomic(path: str, data: bytes) -> bool:
    parent = os.path.dirname(path) or "."
    if not _leaf_ok(path) or not os.path.isdir(parent):
        return False
    stem = os.path.join(parent, "." + os.path.basename(path) + "." + secrets.token_hex(8))
    tmp = stem + ".tmp"
    backup = stem + ".bak"
    try:
        dfd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    except OSError:
        return False
    ok = _write_file(tmp, data)
    had_previous = False
    if ok and not _leaf_ok(path):
        _discard(tmp)
        ok = False
    if ok:
        try:
            had_previous = os.path.lexists(path)
            if had_previous:
                os.link(path, backup, follow_symlinks=False)
        except OSError:
            _discard(tmp)
            ok = False
    if ok:
        try:
            os.replace(tmp, path)
        except OSError:
            _discard(tmp)
            _discard(backup)
            ok = False
    synced = True
    if ok and not _sync(dfd):
        synced = False
    if not _close(dfd):
        synced = False
    if ok and not synced:
        rollback_ok = _rollback(path, backup, had_previous)
        if rollback_ok:
            _discard(backup)
        ok = False
    elif ok:
        _discard(backup)
    return ok


def save_favorites(store: FavoriteStore, favorites: CottList[Favorite]) -> Result[Unit, ClientError]:
    bad = _bad_name(favorites)
    if bad is not None:
        return _failure(bad)
    if len(favorites) > store.max_entries:
        return _failure("")
    data = _encode(favorites)
    if data is None:
        return _failure("")
    try:
        cott_runtime._cott_fixture_replace(store.path, data)
        return Ok(value=UNIT)
    except cott_runtime.CottContractViolation as exc:
        if exc.message != _INACTIVE:
            return _failure("")
    except Exception:
        return _failure("")
    path = os.fspath(store.path)
    if path == "" or os.path.basename(path) == "":
        return _failure("")
    try:
        if not _write_atomic(path, data):
            return _failure("")
    except (OSError, ValueError, TypeError, MemoryError):
        return _failure("")
    return Ok(value=UNIT)
