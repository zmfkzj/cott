from typing import Final

from cott_runtime import CottList
from real.harlequin.catalog_types import CatalogSnapshot, CompletionRequest, CompletionResult

_KEYWORDS: Final[str] = "SELECT FROM WHERE GROUP BY ORDER HAVING LIMIT JOIN LEFT INNER ON AS AND OR NOT NULL INSERT INTO VALUES UPDATE SET DELETE CREATE TABLE VIEW DROP WITH DISTINCT UNION"


def _is_ident_char(ch: str) -> bool:
    return ch.isascii() and (ch.isalnum() or ch == "_")


def _ascii_lower(text: str) -> str:
    return "".join(chr(ord(ch) + 32) if "A" <= ch <= "Z" else ch for ch in text)


def complete_sql(request: CompletionRequest, snapshot: CatalogSnapshot) -> CompletionResult:
    source = request.source
    cursor = request.cursor
    start = cursor
    while start > 0 and _is_ident_char(source[start - 1]):
        start -= 1
    prefix = _ascii_lower(source[start:cursor])
    candidates: list[str] = []
    limit = request.maximum_candidates
    if prefix and limit > 0:
        pool: list[str] = []
        if request.scope == snapshot.scope:
            for relation in snapshot.relations:
                pool.append(relation.name)
        pool.extend(_KEYWORDS.split(" "))
        for name in pool:
            if len(candidates) >= limit:
                break
            if _ascii_lower(name).startswith(prefix) and name not in candidates:
                candidates.append(name)
    return CompletionResult(
        candidates=CottList(values=candidates),
        replace_start=start,
        replace_end=cursor,
    )
