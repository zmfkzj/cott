import errno
import json
import os
import stat
from typing import Final, cast

from cott_runtime import CottList, Err, Ok, Result
from real.pgcli_types import ClientError, ClientError_FavoriteFailed, Favorite, FavoriteStore

_MAX_BYTES: Final[int] = 16777216


def _read_bytes(path: str) -> bytes | None:
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(st.st_mode) or st.st_size > _MAX_BYTES:
        raise OSError(errno.EINVAL, "invalid file")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        fst = os.fstat(fd)
        if not stat.S_ISREG(fst.st_mode) or fst.st_size > _MAX_BYTES:
            raise OSError(errno.EINVAL, "invalid file")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            total += len(chunk)
            if total > _MAX_BYTES:
                raise OSError(errno.EFBIG, "file too large")
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def _has_duplicate_keys(node: object) -> bool:
    if isinstance(node, list):
        for item in cast(list[object], node):
            if _has_duplicate_keys(item):
                return True
        return False
    if isinstance(node, tuple):
        keys: set[object] = set()
        for pair in cast(tuple[object, ...], node):
            key, value = cast(tuple[object, object], pair)
            if key in keys or _has_duplicate_keys(value):
                return True
            keys.add(key)
    return False


def _parse_row(row: object) -> Favorite | None:
    if not isinstance(row, dict):
        return None
    fields = cast(dict[object, object], row)
    if set(fields.keys()) != {"name", "sql", "tags"}:
        return None
    name = fields["name"]
    sql = fields["sql"]
    tags = fields["tags"]
    if not isinstance(name, str) or not name or not isinstance(sql, str) or not isinstance(tags, list):
        return None
    tag_values: list[str] = []
    for tag in cast(list[object], tags):
        if not isinstance(tag, str):
            return None
        tag_values.append(tag)
    return Favorite(name=name, sql=sql, tags=CottList(values=tag_values))


def _parse(data: bytes, max_entries: int) -> list[Favorite] | None:
    try:
        text = data.decode("utf-8", errors="strict")
        doc: object = json.loads(text)
        pairs_doc: object = json.loads(text, object_pairs_hook=tuple)
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None
    if _has_duplicate_keys(pairs_doc):
        return None
    if not isinstance(doc, list):
        return None
    rows = cast(list[object], doc)
    if len(rows) > max_entries:
        return None
    seen: set[str] = set()
    out: list[Favorite] = []
    for row in rows:
        favorite = _parse_row(row)
        if favorite is None or favorite.name in seen:
            return None
        seen.add(favorite.name)
        out.append(favorite)
    return out


def load_favorites(store: FavoriteStore) -> Result[CottList[Favorite], ClientError]:
    failure = ClientError_FavoriteFailed(name=str(store.path))
    try:
        data = _read_bytes(os.fspath(store.path))
    except OSError:
        return Err(error=failure)
    if data is None:
        return Ok(value=CottList(values=[]))
    favorites = _parse(data, store.max_entries)
    if favorites is None:
        return Err(error=failure)
    return Ok(value=CottList(values=favorites))
