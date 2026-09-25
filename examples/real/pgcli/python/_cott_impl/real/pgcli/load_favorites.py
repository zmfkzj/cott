import json
import os
import stat
from pathlib import Path
from typing import Final, cast

import cott_runtime
from cott_runtime import CottContractViolation, CottList, Err, Ok, Result
from real.pgcli_types import ClientError, ClientError_FavoriteFailed, Favorite, FavoriteStore

_MAX_BYTES: Final[int] = 16777216
_WHITE_SPACE: Final[str] = "\t\n\x0b\x0c\r \x85\xa0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000"
_INACTIVE: Final[str] = "fixture adapters are inactive"


def _fail(name: str) -> Result[CottList[Favorite], ClientError]:
    return Err(error=ClientError_FavoriteFailed(name=name))


def _host_read(path: Path) -> bytes | None:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return None
    except (OSError, ValueError, TypeError):
        raise OSError("host file metadata check failed")
    if not stat.S_ISREG(metadata.st_mode):
        raise OSError("favorites path is not a regular file")
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except (OSError, ValueError, TypeError):
        raise OSError("host file open failed")
    close_failed = False
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError("favorites path is not a regular file")
        chunks: list[bytes] = []
        total = 0
        while total <= _MAX_BYTES:
            chunk = os.read(descriptor, min(1048576, _MAX_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        return b"".join(chunks)
    finally:
        try:
            os.close(descriptor)
        except OSError:
            close_failed = True
    if close_failed:
        raise OSError("host file close failed")


def _is_blank(name: str) -> bool:
    return all(character in _WHITE_SPACE for character in name)


def _entry(row: object) -> Favorite | None:
    if not isinstance(row, tuple):
        return None
    pairs = cast(tuple[object, ...], row)
    fields: dict[str, object] = {}
    for pair in pairs:
        if not isinstance(pair, tuple):
            return None
        pair_tuple = cast(tuple[object, ...], pair)
        if len(pair_tuple) != 2:
            return None
        key = pair_tuple[0]
        value = pair_tuple[1]
        if not isinstance(key, str) or key in fields:
            return None
        fields[key] = value
    if set(fields) != {"name", "sql", "tags"}:
        return None
    name = fields["name"]
    sql = fields["sql"]
    tags = fields["tags"]
    if not isinstance(name, str) or not isinstance(sql, str) or not isinstance(tags, list):
        return None
    tag_values: list[str] = []
    for tag in cast(list[object], tags):
        if not isinstance(tag, str):
            return None
        tag_values.append(tag)
    return Favorite(name=name, sql=sql, tags=CottList(values=tag_values))


def load_favorites(store: FavoriteStore) -> Result[CottList[Favorite], ClientError]:
    data: bytes | None
    try:
        data = cott_runtime._cott_fixture_read(store.path)
    except CottContractViolation as violation:
        if isinstance(violation.__cause__, FileNotFoundError):
            data = None
        elif violation.message != _INACTIVE:
            return _fail("")
        else:
            try:
                data = _host_read(store.path)
            except (OSError, ValueError, TypeError, MemoryError):
                return _fail("")
    except Exception:
        return _fail("")
    if data is None:
        return Ok(value=CottList(values=[]))
    if len(data) > _MAX_BYTES:
        return _fail("")
    try:
        document: object = json.loads(data.decode("utf-8"), object_pairs_hook=tuple, parse_constant=int)
    except (UnicodeDecodeError, ValueError, RecursionError):
        return _fail("")
    if not isinstance(document, list):
        return _fail("")
    seen: set[str] = set()
    favorites: list[Favorite] = []
    for row in cast(list[object], document):
        favorite = _entry(row)
        if favorite is None:
            return _fail("")
        if _is_blank(favorite.name) or favorite.name in seen:
            return _fail(favorite.name)
        seen.add(favorite.name)
        favorites.append(favorite)
    if len(favorites) > store.max_entries:
        return _fail("")
    return Ok(value=CottList(values=favorites))
